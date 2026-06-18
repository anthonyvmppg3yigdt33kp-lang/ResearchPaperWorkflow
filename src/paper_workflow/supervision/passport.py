"""
Paper Passport System — Project identity, artifact tracking, and state persistence.

Manages:
- project_passport.yaml: Paper identity and metadata
- artifact_ledger.jsonl: Append-only artifact hash log
- checkpoint_ledger.jsonl: User-approved checkpoints
- integrity_ledger.jsonl: Integrity gate events
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class ArtifactEntry:
    path: str
    hash_sha256: str
    size_bytes: int
    stage: str
    recorded_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "active"

    def to_dict(self) -> dict:
        return {"path": self.path, "hash_sha256": self.hash_sha256,
                "size_bytes": self.size_bytes, "stage": self.stage,
                "recorded_at": self.recorded_at, "status": self.status}


@dataclass
class CheckpointEntry:
    checkpoint_id: str
    stage: str
    decision: str
    notes: str = ""
    recorded_at: str = field(default_factory=lambda: datetime.now().isoformat())
    artifacts_snapshot: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"checkpoint_id": self.checkpoint_id, "stage": self.stage,
                "decision": self.decision, "notes": self.notes,
                "recorded_at": self.recorded_at, "artifacts_snapshot": self.artifacts_snapshot}


@dataclass
class IntegrityEvent:
    event_id: str
    event_type: str
    details: dict = field(default_factory=dict)
    recorded_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {"event_id": self.event_id, "event_type": self.event_type,
                "details": self.details, "recorded_at": self.recorded_at}


class PaperPassport:
    """Paper project passport — identity, artifact tracking, and state persistence."""

    def __init__(self, paper_dir: Path):
        self.paper_dir = Path(paper_dir)
        self.paper_dir.mkdir(parents=True, exist_ok=True)
        self.passport_path = self.paper_dir / "project_passport.yaml"
        self.artifact_ledger_path = self.paper_dir / "artifact_ledger.jsonl"
        self.checkpoint_ledger_path = self.paper_dir / "checkpoint_ledger.jsonl"
        self.integrity_ledger_path = self.paper_dir / "integrity_ledger.jsonl"
        self.passport_data: dict = self._load_yaml(self.passport_path) or {}
        self.artifacts: list[dict] = self._load_jsonl(self.artifact_ledger_path)
        self.checkpoints: list[dict] = self._load_jsonl(self.checkpoint_ledger_path)
        self.integrity_events: list[dict] = self._load_jsonl(self.integrity_ledger_path)

    def initialize(self, idea: str, field: str, target_journal: str = "",
                   paper_type: str = "original_research") -> dict:
        self.passport_data = {
            "paper_id": self._generate_id(idea), "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(), "idea": idea, "field": field,
            "target_journal": target_journal, "paper_type": paper_type,
            "status": "initialized", "pipeline_state": "clean", "stages": {},
            "metadata": {"version": "1.0", "total_stages": 18, "completed_stages": 0},
        }
        self._save_passport()
        return self.passport_data

    def _generate_id(self, idea: str) -> str:
        slug = "_".join(idea.lower().split()[:5])
        slug = "".join(c for c in slug if c.isalnum() or c == "_")
        return f"paper_{slug}_{datetime.now().strftime('%Y%m%d')}"

    def record_artifact(self, artifact_path: str, stage: str, compute_hash: bool = True) -> ArtifactEntry:
        full_path = self.paper_dir / artifact_path
        if compute_hash and full_path.exists():
            file_hash = self._compute_hash(full_path)
            file_size = full_path.stat().st_size
        else:
            file_hash, file_size = "pending", 0
        for existing in self.artifacts:
            if existing["path"] == artifact_path:
                if existing["hash_sha256"] != file_hash:
                    existing["hash_sha256"] = file_hash
                    existing["size_bytes"] = file_size
                    existing["status"] = "modified"
                    existing["recorded_at"] = datetime.now().isoformat()
                    self._save_artifact_ledger()
                    self.record_integrity_event("drift_detected", {"artifact": artifact_path})
                return ArtifactEntry(**existing)
        entry = ArtifactEntry(path=artifact_path, hash_sha256=file_hash, size_bytes=file_size, stage=stage)
        self.artifacts.append(entry.to_dict())
        self._save_artifact_ledger()
        return entry

    def detect_artifact_drift(self) -> list[dict]:
        drifted = []
        for entry in self.artifacts:
            full_path = self.paper_dir / entry["path"]
            if not full_path.exists():
                if entry["status"] != "deleted":
                    drifted.append({"path": entry["path"], "old_hash": entry["hash_sha256"],
                                    "new_hash": "FILE_MISSING", "status": "deleted"})
                continue
            current_hash = self._compute_hash(full_path)
            if current_hash != entry["hash_sha256"]:
                drifted.append({"path": entry["path"], "old_hash": entry["hash_sha256"],
                                "new_hash": current_hash, "status": "modified"})
        return drifted

    def sync_artifact_stale(self, stage_dependency_map: dict[str, list[str]]) -> dict:
        drifted = self.detect_artifact_drift()
        if not drifted:
            return {"stale_stages": [], "stale_count": 0}
        stale_stages = set()
        for drift in drifted:
            for stage_name in stage_dependency_map.get(drift["path"], []):
                stale_stages.add(stage_name)
                self._mark_stage_stale(stage_name)
        self.record_integrity_event("stale_sync", {"drifted_artifacts": [d["path"] for d in drifted],
                                                    "stale_stages": list(stale_stages)})
        self._save_passport()
        return {"stale_stages": list(stale_stages), "stale_count": len(stale_stages)}

    def _mark_stage_stale(self, stage_name: str) -> None:
        self.passport_data.setdefault("stages", {})[stage_name] = {
            "status": "stale", "marked_at": datetime.now().isoformat(),
            "reason": "upstream_artifact_changed"}

    def record_checkpoint(self, stage: str, decision: str, notes: str = "") -> CheckpointEntry:
        cid = f"cp_{stage}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        entry = CheckpointEntry(checkpoint_id=cid, stage=stage, decision=decision, notes=notes)
        self.checkpoints.append(entry.to_dict())
        self._append_jsonl(self.checkpoint_ledger_path, entry.to_dict())
        self.passport_data.setdefault("stages", {})[stage] = {
            "status": decision, "checkpoint_id": cid, "checked_at": entry.recorded_at}
        self._save_passport()
        return entry

    def record_integrity_event(self, event_type: str, details: dict = None) -> IntegrityEvent:
        eid = f"ie_{event_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        entry = IntegrityEvent(event_id=eid, event_type=event_type, details=details or {})
        self.integrity_events.append(entry.to_dict())
        self._append_jsonl(self.integrity_ledger_path, entry.to_dict())
        return entry

    def export_summary(self) -> dict:
        return {
            "paper_id": self.passport_data.get("paper_id", "unknown"),
            "idea": self.passport_data.get("idea", ""),
            "target_journal": self.passport_data.get("target_journal", ""),
            "status": self.passport_data.get("status", "unknown"),
            "total_artifacts": len(self.artifacts), "total_checkpoints": len(self.checkpoints),
            "total_integrity_events": len(self.integrity_events),
            "artifact_summary": {"active": sum(1 for a in self.artifacts if a["status"] == "active"),
                                 "modified": sum(1 for a in self.artifacts if a["status"] == "modified"),
                                 "deleted": sum(1 for a in self.artifacts if a["status"] == "deleted")},
        }

    def _save_passport(self) -> None:
        self.passport_data["updated_at"] = datetime.now().isoformat()
        with open(self.passport_path, "w", encoding="utf-8") as f:
            yaml.dump(self.passport_data, f, allow_unicode=True, default_flow_style=False)

    def _save_artifact_ledger(self) -> None:
        with open(self.artifact_ledger_path, "w", encoding="utf-8") as f:
            for entry in self.artifacts:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def _append_jsonl(self, path: Path, entry: dict) -> None:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    @staticmethod
    def _compute_hash(file_path: Path) -> str:
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    @staticmethod
    def _load_yaml(path: Path) -> Optional[dict]:
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    @staticmethod
    def _load_jsonl(path: Path) -> list[dict]:
        if not path.exists():
            return []
        entries = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return entries
