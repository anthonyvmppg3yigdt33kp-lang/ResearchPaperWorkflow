"""
Paper Passport System — Project identity, artifact tracking, and state persistence.

v3.0 Upgrades:
- claim_ledger.jsonl: Append-only claim-to-evidence binding log
- evidence_graph.json: Full claim→artifact→code→parameter trace graph
- Manages 5 ledgers (was 4 in v2)

Manages:
- project_passport.yaml: Paper identity and metadata
- artifact_ledger.jsonl: Append-only artifact hash log
- checkpoint_ledger.jsonl: User-approved checkpoints
- integrity_ledger.jsonl: Integrity gate events
- claim_ledger.jsonl: Claim-to-evidence bindings (v3.0 new)
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


@dataclass
class ClaimEntry:
    """v3.0: A single claim with full evidence binding chain."""
    claim_id: str
    claim_text: str
    section: str
    confidence: str = "hypothesis"  # validated/supported/hypothesis/contradicted
    figure_ref: str = ""
    table_ref: str = ""
    artifact_path: str = ""
    artifact_hash: str = ""
    stat_test: str = ""
    stat_value: str = ""
    p_value: str = ""
    effect_size: str = ""
    ci_lower: str = ""
    ci_upper: str = ""
    sample_size: str = ""
    alternative_explanation: str = ""
    code_file: str = ""
    code_line_range: str = ""
    reviewer_challenge_ready: bool = False
    recorded_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "claim_id": self.claim_id, "claim_text": self.claim_text,
            "section": self.section, "confidence": self.confidence,
            "figure_ref": self.figure_ref, "table_ref": self.table_ref,
            "artifact_path": self.artifact_path, "artifact_hash": self.artifact_hash,
            "stat_test": self.stat_test, "stat_value": self.stat_value,
            "p_value": self.p_value, "effect_size": self.effect_size,
            "ci_lower": self.ci_lower, "ci_upper": self.ci_upper,
            "sample_size": self.sample_size,
            "alternative_explanation": self.alternative_explanation,
            "code_file": self.code_file, "code_line_range": self.code_line_range,
            "reviewer_challenge_ready": self.reviewer_challenge_ready,
            "recorded_at": self.recorded_at,
        }

    @property
    def is_bound(self) -> bool:
        """A claim is bound if it has at least an artifact or figure reference."""
        return bool(self.artifact_path or self.figure_ref)

    @property
    def evidence_completeness(self) -> float:
        """Fraction of evidence fields that are populated (0.0-1.0)."""
        fields = [self.artifact_path, self.stat_test, self.p_value, self.effect_size,
                  self.figure_ref, self.alternative_explanation, self.code_file]
        return sum(1 for f in fields if f) / len(fields)


class PaperPassport:
    """Paper project passport — identity, artifact tracking, and state persistence (v3.0).

    v3.0 adds claim ledger (5th ledger) for evidence-centric architecture.
    """

    def __init__(self, paper_dir: Path):
        self.paper_dir = Path(paper_dir)
        self.paper_dir.mkdir(parents=True, exist_ok=True)
        self.passport_path = self.paper_dir / "project_passport.yaml"
        self.artifact_ledger_path = self.paper_dir / "artifact_ledger.jsonl"
        self.checkpoint_ledger_path = self.paper_dir / "checkpoint_ledger.jsonl"
        self.integrity_ledger_path = self.paper_dir / "integrity_ledger.jsonl"
        self.claim_ledger_path = self.paper_dir / "claim_ledger.jsonl"  # v3.0
        self.passport_data: dict = self._load_yaml(self.passport_path) or {}
        self.artifacts: list[dict] = self._load_jsonl(self.artifact_ledger_path)
        self.checkpoints: list[dict] = self._load_jsonl(self.checkpoint_ledger_path)
        self.integrity_events: list[dict] = self._load_jsonl(self.integrity_ledger_path)
        self.claims: list[dict] = self._load_jsonl(self.claim_ledger_path)  # v3.0

    def initialize(self, idea: str, field: str, target_journal: str = "",
                   paper_type: str = "original_research") -> dict:
        self.passport_data = {
            "paper_id": self._generate_id(idea), "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(), "idea": idea, "field": field,
            "target_journal": target_journal, "paper_type": paper_type,
            "status": "initialized", "pipeline_state": "clean", "stages": {},
            "metadata": {"version": "1.0", "total_stages": 19, "completed_stages": 0},
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

    # =========================================================================
    # v3.0: Claim Ledger Methods
    # =========================================================================
    def record_claim(self, claim: ClaimEntry) -> ClaimEntry:
        """Record a manuscript claim with evidence binding (v3.0)."""
        claim_dict = claim.to_dict()
        for existing in self.claims:
            if existing["claim_id"] == claim.claim_id:
                existing.update(claim_dict)
                existing["recorded_at"] = datetime.now().isoformat()
                self._save_claim_ledger()
                return ClaimEntry(**existing)
        self.claims.append(claim_dict)
        self._append_jsonl(self.claim_ledger_path, claim_dict)
        self.passport_data.setdefault("claims", {})["total"] = len(self.claims)
        self._save_passport()
        return claim

    def get_claim(self, claim_id: str) -> Optional[ClaimEntry]:
        """Retrieve a claim by ID."""
        for c in self.claims:
            if c["claim_id"] == claim_id:
                return ClaimEntry(**c)
        return None

    def get_unbound_claims(self) -> list[dict]:
        """Get all claims that lack artifact binding."""
        return [c for c in self.claims if not c.get("artifact_path") and not c.get("figure_ref")]

    def get_weak_claims(self) -> list[dict]:
        """Get claims with weak or contradictory evidence."""
        return [c for c in self.claims
                if c.get("confidence") in ("hypothesis", "contradicted")
                or not c.get("p_value")]

    def get_claims_by_section(self, section: str) -> list[dict]:
        """Get all claims from a specific manuscript section."""
        return [c for c in self.claims if c.get("section") == section]

    def bind_claim_to_artifact(self, claim_id: str, artifact_path: str,
                                artifact_hash: str = "") -> Optional[ClaimEntry]:
        """Bind an existing claim to an artifact."""
        for i, c in enumerate(self.claims):
            if c["claim_id"] == claim_id:
                c["artifact_path"] = artifact_path
                if artifact_hash:
                    c["artifact_hash"] = artifact_hash
                c["recorded_at"] = datetime.now().isoformat()
                self.claims[i] = c
                self._save_claim_ledger()
                return ClaimEntry(**c)
        return None

    def bind_claim_to_statistics(self, claim_id: str, stat_test: str,
                                  stat_value: str, p_value: str,
                                  effect_size: str, ci_lower: str = "",
                                  ci_upper: str = "") -> Optional[ClaimEntry]:
        """Bind a claim to its statistical evidence."""
        for i, c in enumerate(self.claims):
            if c["claim_id"] == claim_id:
                c.update({"stat_test": stat_test, "stat_value": stat_value,
                         "p_value": p_value, "effect_size": effect_size,
                         "ci_lower": ci_lower, "ci_upper": ci_upper,
                         "recorded_at": datetime.now().isoformat()})
                self.claims[i] = c
                self._save_claim_ledger()
                return ClaimEntry(**c)
        return None

    def mark_claim_reviewer_ready(self, claim_id: str) -> bool:
        """Mark a claim as ready for reviewer challenge."""
        for i, c in enumerate(self.claims):
            if c["claim_id"] == claim_id:
                c["reviewer_challenge_ready"] = True
                c["recorded_at"] = datetime.now().isoformat()
                self.claims[i] = c
                self._save_claim_ledger()
                return True
        return False

    def export_evidence_graph(self) -> dict:
        """Export the full evidence graph as a dict (v3.0).

        Returns a structure suitable for evidence_graph.json:
        {
          "paper_id": ...,
          "nodes": {claim nodes, artifact nodes, figure nodes, code nodes},
          "edges": {claim→artifact, claim→figure, artifact→code, ...},
          "summary": {total_claims, bound_claims, unbound_claims, completeness}
        }
        """
        graph = {
            "paper_id": self.passport_data.get("paper_id", "unknown"),
            "generated_at": datetime.now().isoformat(),
            "nodes": {"claims": [], "artifacts": [], "figures": [], "code_files": []},
            "edges": [],
            "summary": {},
        }

        # Add claim nodes
        for c in self.claims:
            claim_node = {
                "id": c["claim_id"], "type": "claim",
                "label": c["claim_text"][:120], "section": c.get("section", ""),
                "confidence": c.get("confidence", "hypothesis"),
            }
            graph["nodes"]["claims"].append(claim_node)

        # Add artifact nodes from artifact ledger
        seen_artifacts = set()
        for a in self.artifacts:
            if a["path"] not in seen_artifacts:
                graph["nodes"]["artifacts"].append({
                    "id": a["path"], "type": "artifact",
                    "hash": a.get("hash_sha256", ""), "stage": a.get("stage", ""),
                    "status": a.get("status", "active"),
                })
                seen_artifacts.add(a["path"])

        # Build edges: claim → artifact, claim → figure, artifact → code
        for c in self.claims:
            cid = c["claim_id"]
            if c.get("artifact_path"):
                graph["edges"].append({"source": cid, "target": c["artifact_path"],
                                      "relationship": "derived_from"})
            if c.get("figure_ref"):
                graph["edges"].append({"source": cid, "target": c["figure_ref"],
                                      "relationship": "visualized_in"})
                if c["figure_ref"] not in [n["id"] for n in graph["nodes"]["figures"]]:
                    graph["nodes"]["figures"].append({"id": c["figure_ref"], "type": "figure"})
            if c.get("code_file"):
                code_id = f"{c['code_file']}:{c.get('code_line_range', '?')}"
                graph["edges"].append({"source": c.get("artifact_path", cid),
                                      "target": code_id, "relationship": "computed_by"})
                if code_id not in [n["id"] for n in graph["nodes"]["code_files"]]:
                    graph["nodes"]["code_files"].append({"id": code_id, "type": "code"})

        # Summary
        bound = sum(1 for c in self.claims if c.get("artifact_path") or c.get("figure_ref"))
        unbound = len(self.claims) - bound
        graph["summary"] = {
            "total_claims": len(self.claims),
            "bound_claims": bound,
            "unbound_claims": unbound,
            "total_artifacts": len(self.artifacts),
            "evidence_completeness": round(bound / max(len(self.claims), 1), 3),
        }
        return graph

    def export_evidence_graph_json(self, output_path: Optional[Path] = None) -> Path:
        """Export the evidence graph as a JSON file."""
        path = output_path or (self.paper_dir / "evidence_graph.json")
        graph = self.export_evidence_graph()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(graph, f, indent=2, ensure_ascii=False)
        return path

    def _save_claim_ledger(self) -> None:
        """Save the claim ledger to disk."""
        with open(self.claim_ledger_path, "w", encoding="utf-8") as f:
            for entry in self.claims:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

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
