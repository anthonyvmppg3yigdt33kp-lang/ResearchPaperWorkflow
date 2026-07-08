"""Module usage ledger and improvement proposal workflow."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return data if isinstance(data, dict) else {}


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh, allow_unicode=True, sort_keys=False)


def stable_hash(payload: Any) -> str:
    text = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class ModuleFeedbackManager:
    """Append run feedback and prepare human-reviewed improvement proposals."""

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.ledger_path = self.project_root / "code_library" / "module_usage_ledger.jsonl"
        self.proposal_dir = self.project_root / "code_library" / "module_improvement_proposals"

    def record_run(
        self,
        *,
        paper_id: str,
        run_id: str,
        run_dir: Path,
        adapter_result: dict[str, Any],
        evaluation: dict[str, Any],
    ) -> list[dict[str, Any]]:
        run_dir = Path(run_dir)
        manifest = read_yaml(run_dir / "run_manifest.yaml")
        inputs = read_yaml(run_dir / "inputs_manifest.yaml")
        parameters = read_yaml(run_dir / "parameters.yaml")
        nodes = list(manifest.get("nodes", []) or [])
        if not nodes:
            nodes = [{
                "module_id": manifest.get("analysis_adapter") or adapter_result.get("adapter", "unknown_adapter"),
                "status": manifest.get("status") or adapter_result.get("status", "unknown"),
                "artifacts": manifest.get("outputs_generated", []),
                "warnings": manifest.get("warnings", []),
                "errors": manifest.get("errors", []),
                "environment": {"status": "not_applicable"},
            }]
        records = [
            self._record_for_node(
                paper_id=paper_id,
                run_id=run_id,
                node=node,
                adapter_result=adapter_result,
                evaluation=evaluation,
                inputs=inputs,
                parameters=parameters,
            )
            for node in nodes
        ]
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        with self.ledger_path.open("a", encoding="utf-8") as fh:
            for record in records:
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        return records

    def summarize_module_usage(self, module_id: str) -> dict[str, Any]:
        records = [record for record in self._read_ledger() if record.get("module_id") == module_id]
        statuses: dict[str, int] = {}
        for record in records:
            status = str(record.get("status", "unknown"))
            statuses[status] = statuses.get(status, 0) + 1
        return {
            "module_id": module_id,
            "usage_count": len(records),
            "status_counts": statuses,
            "source_map_valid_count": len([r for r in records if r.get("source_map_valid")]),
            "last_record": records[-1] if records else {},
        }

    def propose_module_improvement(self, run_id: str, paper_id: str = "") -> dict[str, Any]:
        records = [
            record for record in self._read_ledger()
            if record.get("run_id") == run_id and (not paper_id or record.get("paper_id") == paper_id)
        ]
        if not records:
            raise FileNotFoundError(f"no module usage records found for run_id={run_id}")
        proposal_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{run_id}"
        proposal = {
            "proposal_id": proposal_id,
            "created_at": utc_now(),
            "run_id": run_id,
            "paper_id": paper_id or records[0].get("paper_id", ""),
            "status": "proposal_pending_human_review",
            "registry_mutation": "not_performed",
            "records_considered": len(records),
            "modules": sorted({str(record.get("module_id", "")) for record in records}),
            "observed_status_counts": self._status_counts(records),
            "warnings": sorted({warning for record in records for warning in record.get("warnings", [])}),
            "errors": sorted({error for record in records for error in record.get("errors", [])}),
            "recommended_actions": self._recommendations(records),
            "required_next_steps": [
                "human review",
                "adapted code or metadata change",
                "focused tests",
                "explicit module_registry update commit",
            ],
        }
        path = self.proposal_dir / f"{proposal_id}.yaml"
        write_yaml(path, proposal)
        proposal["path"] = str(path)
        return proposal

    def apply_module_improvement(self, proposal: str, approved: bool = False) -> dict[str, Any]:
        if not approved:
            raise PermissionError("apply-module-improvement requires --approved")
        path = Path(proposal)
        if not path.is_absolute():
            candidate = self.proposal_dir / proposal
            path = candidate if candidate.exists() else self.proposal_dir / f"{proposal}.yaml"
        data = read_yaml(path)
        if not data:
            raise FileNotFoundError(f"proposal not found: {proposal}")
        data.update({
            "status": "approved_for_manual_implementation",
            "approved_at": utc_now(),
            "registry_mutation": "not_performed",
            "note": "Approval records intent only; module_registry.yaml must be changed by a separate tested commit.",
        })
        write_yaml(path, data)
        data["path"] = str(path)
        return data

    def _record_for_node(
        self,
        *,
        paper_id: str,
        run_id: str,
        node: dict[str, Any],
        adapter_result: dict[str, Any],
        evaluation: dict[str, Any],
        inputs: dict[str, Any],
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        warnings = list(node.get("warnings", []) or []) + list(adapter_result.get("warnings", []) or [])
        errors = list(node.get("errors", []) or []) + list(adapter_result.get("errors", []) or [])
        environment = node.get("environment", {}) if isinstance(node.get("environment"), dict) else {}
        status = self._normalize_status(
            node_status=str(node.get("status", "")),
            evaluation_status=str(evaluation.get("status", "")),
            errors=errors,
            source_map_valid=bool(evaluation.get("source_map_valid", False)),
        )
        proposal_hint = ""
        if status in {"blocked", "degraded"}:
            proposal_hint = "Run propose-module-improvement after reviewing warnings/errors and source maps."
        artifacts = list(node.get("artifacts", []) or [])
        return {
            "recorded_at": utc_now(),
            "paper_id": paper_id,
            "run_id": run_id,
            "module_id": str(node.get("module_id") or adapter_result.get("adapter", "unknown")),
            "status": status,
            "runtime_seconds": float((adapter_result.get("metrics") or {}).get("runtime_seconds", 0) or 0),
            "inputs_hash": stable_hash({"inputs": inputs, "parameters": parameters}),
            "environment_status": str(environment.get("status", "unknown")),
            "output_count": len(artifacts),
            "source_map_valid": bool(evaluation.get("source_map_valid", False)),
            "warnings": warnings,
            "errors": errors,
            "reviewer_risk_observed": list(node.get("module_reviewer_risk", []) or []),
            "improvement_proposal": proposal_hint,
        }

    @staticmethod
    def _normalize_status(
        *,
        node_status: str,
        evaluation_status: str,
        errors: list[str],
        source_map_valid: bool,
    ) -> str:
        if errors or "blocked" in node_status or evaluation_status == "blocked":
            return "blocked"
        if "degraded" in evaluation_status or not source_map_valid:
            return "degraded"
        return "completed"

    def _read_ledger(self) -> list[dict[str, Any]]:
        if not self.ledger_path.exists():
            return []
        records = []
        with self.ledger_path.open("r", encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(item, dict):
                    records.append(item)
        return records

    @staticmethod
    def _status_counts(records: list[dict[str, Any]]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for record in records:
            status = str(record.get("status", "unknown"))
            counts[status] = counts.get(status, 0) + 1
        return counts

    @staticmethod
    def _recommendations(records: list[dict[str, Any]]) -> list[str]:
        recommendations = []
        if any(not record.get("source_map_valid") for record in records):
            recommendations.append("repair source maps before promoting outputs")
        if any(record.get("errors") for record in records):
            recommendations.append("fix execution errors and add focused regression tests")
        if any(record.get("environment_status") not in {"pass", "not_applicable"} for record in records):
            recommendations.append("review environment registry and lock policy")
        if not recommendations:
            recommendations.append("review run for reusable parameter defaults or documentation updates")
        return recommendations
