"""File-based agent harness bridge for pending skill invocations.

The dispatcher writes pending invocation JSON files when a stage needs an
external skill, human input, or generated artifact set. This module provides a
small verification surface for listing those invocations and marking them as
completed only after their declared outputs exist and are non-placeholder.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class AgentHarness:
    """Manage pending agent/skill invocations for a paper project."""

    PLACEHOLDER_PATTERNS = (
        "[To be defined",
        "[To be generated",
        "[To be selected",
        "[To be determined",
        "[To be written",
        "[Complete manuscript sections",
        "Status: PENDING",
        "status: pending",
        "status: pending_data",
        "reproducibility_status: pending",
        "outputs_generated: []",
        "% No verified references ingested yet",
        "% Bibliography for paper",
    )

    TEXT_SUFFIXES = {".md", ".txt", ".yaml", ".yml", ".json", ".bib", ".csv", ".tsv"}

    def __init__(self, paper_dir: Path):
        self.paper_dir = Path(paper_dir)
        self.invocation_dir = self.paper_dir / "workflow_state" / "pending_invocations"
        self.result_dir = self.paper_dir / "workflow_state" / "harness_results"

    def list_invocations(self, status: str | None = None) -> list[dict[str, Any]]:
        """Return invocation records, optionally filtered by status."""
        if not self.invocation_dir.exists():
            return []
        records: list[dict[str, Any]] = []
        for path in sorted(self.invocation_dir.glob("*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:
                payload = {
                    "stage_id": "",
                    "skill_name": "",
                    "status": "unreadable",
                    "error": f"{type(exc).__name__}: {exc}",
                }
            payload["path"] = str(path)
            payload["name"] = path.name
            if status is None or payload.get("status") == status:
                records.append(payload)
        return records

    def find_invocation(self, invocation: str) -> tuple[Path, dict[str, Any]]:
        """Find an invocation by filename, stem, full path, or stage id."""
        candidate = Path(invocation)
        candidates = []
        if candidate.is_absolute():
            candidates.append(candidate)
        else:
            candidates.append(self.invocation_dir / invocation)
            if candidate.suffix != ".json":
                candidates.append(self.invocation_dir / f"{invocation}.json")

        for path in candidates:
            if path.exists():
                return path, json.loads(path.read_text(encoding="utf-8"))

        matches = [
            Path(record["path"])
            for record in self.list_invocations()
            if record.get("stage_id") == invocation or Path(record.get("path", "")).stem == invocation
        ]
        if matches:
            path = sorted(matches, key=lambda p: p.stat().st_mtime, reverse=True)[0]
            return path, json.loads(path.read_text(encoding="utf-8"))

        raise FileNotFoundError(f"No harness invocation found for: {invocation}")

    def complete_invocation(self, invocation: str, notes: str = "") -> dict[str, Any]:
        """Verify declared outputs and mark an invocation completed or needs_input."""
        path, payload = self.find_invocation(invocation)
        context = payload.get("context", {}) or {}
        required_outputs = self._required_outputs(context)
        output_checks = [self._check_output(rel_path) for rel_path in required_outputs]
        missing_outputs = [c["path"] for c in output_checks if not c["exists"]]
        placeholder_outputs = [c["path"] for c in output_checks if c["placeholder"]]
        empty_outputs = [c["path"] for c in output_checks if c["empty"]]

        outputs_verified = bool(required_outputs) and not (
            missing_outputs or placeholder_outputs or empty_outputs
        )
        status = "completed" if outputs_verified else "needs_input"
        now = datetime.now().isoformat()

        payload.update({
            "status": status,
            "completed_at": now if outputs_verified else "",
            "last_checked_at": now,
            "outputs_verified": outputs_verified,
            "required_outputs": required_outputs,
            "missing_outputs": missing_outputs,
            "placeholder_outputs": placeholder_outputs,
            "empty_outputs": empty_outputs,
            "notes": notes,
        })
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

        result = {
            "stage_id": payload.get("stage_id", ""),
            "skill_name": payload.get("skill_name", ""),
            "invocation": path.name,
            "status": status,
            "checked_at": now,
            "outputs_verified": outputs_verified,
            "required_outputs": required_outputs,
            "missing_outputs": missing_outputs,
            "placeholder_outputs": placeholder_outputs,
            "empty_outputs": empty_outputs,
            "output_checks": output_checks,
            "notes": notes,
        }
        self.result_dir.mkdir(parents=True, exist_ok=True)
        stage = payload.get("stage_id") or path.stem
        result_path = self.result_dir / f"{stage}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        result["result_path"] = str(result_path)
        return result

    def _required_outputs(self, context: dict[str, Any]) -> list[str]:
        outputs = list(context.get("required_outputs", []) or [])
        if not outputs:
            outputs = list(context.get("artifacts", []) or [])
        return [str(p) for p in outputs if str(p).strip()]

    def _check_output(self, rel_path: str) -> dict[str, Any]:
        paths = list(self.paper_dir.glob(rel_path)) if "*" in rel_path else [self.paper_dir / rel_path]
        existing = [p for p in paths if p.exists()]
        if not existing:
            return {
                "path": rel_path,
                "exists": False,
                "empty": False,
                "placeholder": False,
                "size_bytes": 0,
            }

        sizes = [p.stat().st_size for p in existing if p.is_file()]
        empty = not sizes or all(size == 0 for size in sizes)
        placeholder = any(self._is_placeholder(p) for p in existing if p.is_file())
        return {
            "path": rel_path,
            "exists": True,
            "empty": empty,
            "placeholder": placeholder,
            "size_bytes": sum(sizes),
        }

    def _is_placeholder(self, path: Path) -> bool:
        if path.suffix.lower() not in self.TEXT_SUFFIXES:
            return False
        text = path.read_text(encoding="utf-8", errors="ignore")[:20000]
        return any(pattern in text for pattern in self.PLACEHOLDER_PATTERNS)
