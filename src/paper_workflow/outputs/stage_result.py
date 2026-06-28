"""
Unified Stage Result — Standardized output interface for ALL pipeline stages.

Every pipeline stage MUST return a StageResult. This ensures outputs are
traceable, typed, machine-readable, and cross-compatible across the workflow.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional


# Schema version constant
RESULT_SCHEMA_VERSION = "2.0.0"


class StageStatus(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    WARNING = "warning"
    SKIPPED = "skipped"


class ExecutionMode(Enum):
    REAL = "real"
    TEMPLATE = "template"
    PENDING_HARNESS = "pending_harness"
    NEEDS_INPUT = "needs_input"


@dataclass
class ArtifactRecord:
    """Record of a single output artifact produced by a pipeline stage."""
    path: str                                    # relative to paper_dir
    hash_sha256: str = ""
    size_bytes: int = 0
    mime_type: str = "text/plain"
    description: str = ""
    version: str = "1.0"
    source_stage: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path, "hash_sha256": self.hash_sha256,
            "size_bytes": self.size_bytes, "mime_type": self.mime_type,
            "description": self.description, "version": self.version,
            "source_stage": self.source_stage,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ArtifactRecord:
        return cls(
            path=d.get("path", ""), hash_sha256=d.get("hash_sha256", ""),
            size_bytes=d.get("size_bytes", 0), mime_type=d.get("mime_type", "text/plain"),
            description=d.get("description", ""), version=d.get("version", "1.0"),
            source_stage=d.get("source_stage", ""),
        )

    def compute_hash(self, paper_dir: Optional[Path] = None) -> str:
        """Compute SHA-256 hash of the artifact file if it exists."""
        if paper_dir is None:
            return "pending"
        full_path = Path(paper_dir) / self.path
        if not full_path.exists():
            return "missing"
        sha256 = hashlib.sha256()
        with open(full_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
        self.hash_sha256 = sha256.hexdigest()
        self.size_bytes = full_path.stat().st_size
        return self.hash_sha256


@dataclass
class StageResult:
    """Unified output from a single pipeline stage execution.

    This is the STANDARD interface. Every pipeline stage handler MUST
    return a StageResult instance.
    """
    stage_id: str
    status: StageStatus = StageStatus.SUCCESS
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str = ""
    artifacts: list[ArtifactRecord] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    agent_log: list[str] = field(default_factory=list)
    retry_count: int = 0
    checksum: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    execution_mode: str = ExecutionMode.REAL.value
    outputs_verified: bool = False
    required_outputs: list[str] = field(default_factory=list)
    missing_outputs: list[str] = field(default_factory=list)
    quality_gate_results: list[dict[str, Any]] = field(default_factory=list)
    schema_version: str = RESULT_SCHEMA_VERSION

    def complete(self) -> StageResult:
        """Mark the stage as complete and compute the checksum."""
        self.completed_at = datetime.now().isoformat()
        self.checksum = self.compute_checksum()
        return self

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage_id": self.stage_id, "status": self.status.value,
            "started_at": self.started_at, "completed_at": self.completed_at,
            "artifacts": [a.to_dict() for a in self.artifacts],
            "metrics": self.metrics, "warnings": self.warnings,
            "errors": self.errors, "agent_log": self.agent_log,
            "retry_count": self.retry_count, "checksum": self.checksum,
            "metadata": self.metadata, "execution_mode": self.execution_mode,
            "outputs_verified": self.outputs_verified,
            "required_outputs": self.required_outputs,
            "missing_outputs": self.missing_outputs,
            "quality_gate_results": self.quality_gate_results,
            "schema_version": self.schema_version,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> StageResult:
        status_raw = d.get("status", "success")
        if isinstance(status_raw, str):
            status = StageStatus(status_raw)
        else:
            status = StageStatus.SUCCESS
        return cls(
            stage_id=d.get("stage_id", ""), status=status,
            started_at=d.get("started_at", ""), completed_at=d.get("completed_at", ""),
            artifacts=[ArtifactRecord.from_dict(a) for a in d.get("artifacts", [])],
            metrics=d.get("metrics", {}), warnings=d.get("warnings", []),
            errors=d.get("errors", []), agent_log=d.get("agent_log", []),
            retry_count=d.get("retry_count", 0), checksum=d.get("checksum", ""),
            metadata=d.get("metadata", {}),
            execution_mode=d.get("execution_mode", ExecutionMode.REAL.value),
            outputs_verified=bool(d.get("outputs_verified", False)),
            required_outputs=list(d.get("required_outputs", []) or []),
            missing_outputs=list(d.get("missing_outputs", []) or []),
            quality_gate_results=list(d.get("quality_gate_results", []) or []),
            schema_version=d.get("schema_version", RESULT_SCHEMA_VERSION),
        )

    def validate(self) -> tuple[bool, list[str]]:
        """Validate required fields. Returns (is_valid, list_of_issues)."""
        issues = []
        if not self.stage_id:
            issues.append("Missing stage_id")
        if not self.started_at:
            issues.append("Missing started_at")
        if not self.completed_at and self.status != StageStatus.SKIPPED:
            issues.append("Stage not completed (missing completed_at)")
        if self.status == StageStatus.FAILURE and not self.errors:
            issues.append("Stage failed but no errors recorded")
        if self.status == StageStatus.SUCCESS and not self.checksum:
            issues.append("Stage succeeded but no checksum computed")
        return len(issues) == 0, issues

    def compute_checksum(self) -> str:
        """Compute deterministic SHA-256 checksum of the serialized result."""
        payload = json.dumps({
            "stage_id": self.stage_id, "status": self.status.value,
            "started_at": self.started_at, "completed_at": self.completed_at,
            "artifacts": sorted([a.path for a in self.artifacts]),
            "metrics": self.metrics, "errors": sorted(self.errors),
            "retry_count": self.retry_count,
            "execution_mode": self.execution_mode,
            "outputs_verified": self.outputs_verified,
            "required_outputs": sorted(self.required_outputs),
            "missing_outputs": sorted(self.missing_outputs),
        }, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(payload.encode()).hexdigest()[:16]

    def merge(self, other: StageResult) -> StageResult:
        """Merge another StageResult into this one (for combining sub-stages)."""
        self.artifacts.extend(other.artifacts)
        self.metrics.update(other.metrics)
        self.warnings.extend(other.warnings)
        self.errors.extend(other.errors)
        self.agent_log.extend(other.agent_log)
        self.quality_gate_results.extend(other.quality_gate_results)
        self.missing_outputs.extend(other.missing_outputs)
        self.metadata["merged_from"] = self.metadata.get("merged_from", []) + [other.stage_id]
        if other.status == StageStatus.FAILURE and self.status != StageStatus.FAILURE:
            self.status = StageStatus.WARNING
        if other.execution_mode != ExecutionMode.REAL.value:
            self.execution_mode = other.execution_mode
        self.outputs_verified = self.outputs_verified and other.outputs_verified
        self.checksum = self.compute_checksum()
        return self

    def summary(self) -> str:
        """One-line human-readable summary."""
        icon = {"success": "[OK]", "failure": "[FAIL]", "warning": "[WARN]", "skipped": "[SKIP]"}
        art_count = len(self.artifacts)
        err_count = len(self.errors)
        warn_count = len(self.warnings)
        return (
            f"{icon.get(self.status.value, '[?]')} {self.stage_id}: "
            f"{art_count} artifacts, {len(self.metrics)} metrics"
            + (f", {err_count} errors" if err_count else "")
            + (f", {warn_count} warnings" if warn_count else "")
        )

    @classmethod
    def create_success(cls, stage_id: str, artifacts: list[ArtifactRecord] = None,
                       metrics: dict = None, warnings: list[str] = None,
                       agent_log: list[str] = None, execution_mode: str = ExecutionMode.REAL.value,
                       outputs_verified: bool = False, required_outputs: list[str] = None,
                       missing_outputs: list[str] = None,
                       quality_gate_results: list[dict[str, Any]] = None) -> StageResult:
        """Factory method for successful stage results."""
        result = cls(stage_id=stage_id, status=StageStatus.SUCCESS,
                     artifacts=artifacts or [], metrics=metrics or {},
                     warnings=warnings or [], agent_log=agent_log or [],
                     execution_mode=execution_mode, outputs_verified=outputs_verified,
                     required_outputs=required_outputs or [],
                     missing_outputs=missing_outputs or [],
                     quality_gate_results=quality_gate_results or [])
        return result.complete()

    @classmethod
    def create_failure(cls, stage_id: str, errors: list[str],
                       artifacts: list[ArtifactRecord] = None,
                       agent_log: list[str] = None,
                       execution_mode: str = ExecutionMode.REAL.value,
                       outputs_verified: bool = False,
                       required_outputs: list[str] = None,
                       missing_outputs: list[str] = None,
                       quality_gate_results: list[dict[str, Any]] = None) -> StageResult:
        """Factory method for failed stage results."""
        result = cls(stage_id=stage_id, status=StageStatus.FAILURE,
                     errors=errors, artifacts=artifacts or [],
                     agent_log=agent_log or [], execution_mode=execution_mode,
                     outputs_verified=outputs_verified,
                     required_outputs=required_outputs or [],
                     missing_outputs=missing_outputs or [],
                     quality_gate_results=quality_gate_results or [])
        return result.complete()

    @classmethod
    def create_warning(cls, stage_id: str, warnings: list[str],
                       artifacts: list[ArtifactRecord] = None,
                       metrics: dict = None,
                       execution_mode: str = ExecutionMode.REAL.value,
                       outputs_verified: bool = False,
                       required_outputs: list[str] = None,
                       missing_outputs: list[str] = None,
                       quality_gate_results: list[dict[str, Any]] = None) -> StageResult:
        """Factory method for warning-flagged stage results."""
        result = cls(stage_id=stage_id, status=StageStatus.WARNING,
                     warnings=warnings, artifacts=artifacts or [],
                     metrics=metrics or {}, execution_mode=execution_mode,
                     outputs_verified=outputs_verified,
                     required_outputs=required_outputs or [],
                     missing_outputs=missing_outputs or [],
                     quality_gate_results=quality_gate_results or [])
        return result.complete()

    @classmethod
    def create_skipped(cls, stage_id: str, reason: str = "") -> StageResult:
        """Factory method for skipped stages."""
        result = cls(stage_id=stage_id, status=StageStatus.SKIPPED,
                     warnings=[reason] if reason else [])
        return result.complete()
