"""External code-source intake with provenance and figure-style review gates."""

from __future__ import annotations

import hashlib
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


SOURCE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{1,80}$")
SKIP_PARTS = {".git", "__pycache__", ".pytest_cache", "node_modules", ".venv", "renv"}
MAX_RETAINED_BYTES = 1_000_000


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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class SourceImportResult:
    source_id: str
    source_dir: str
    manifest_path: str
    retained_count: int
    status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_dir": self.source_dir,
            "manifest_path": self.manifest_path,
            "retained_count": self.retained_count,
            "status": self.status,
        }


class CodeSourceImporter:
    """Create reviewed intake records without mutating executable registries."""

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.base_dir = self.project_root / "code_library" / "external_sources"
        self.figure_style_registry = self.project_root / "code_library" / "figure_style_registry.yaml"

    def source_dir(self, source_id: str) -> Path:
        self._validate_source_id(source_id)
        return self.base_dir / source_id

    def import_source(
        self,
        *,
        source_id: str,
        github: str = "",
        local: str = "",
        paper_doi: str = "",
        license_text: str = "requires_human_review",
    ) -> SourceImportResult:
        if bool(github) == bool(local):
            raise ValueError("provide exactly one of github or local")
        source_dir = self.source_dir(source_id)
        for subdir in ["original", "adapted", "notes"]:
            (source_dir / subdir).mkdir(parents=True, exist_ok=True)

        retained = []
        if local:
            retained = self._retain_local_files(Path(local), source_dir / "original")
            source_type = "user_upload"
            origin_url = ""
        else:
            (source_dir / "original" / "REMOTE_SOURCE.txt").write_text(
                f"{github}\n",
                encoding="utf-8",
            )
            retained = [self._manifest_entry(source_dir / "original" / "REMOTE_SOURCE.txt", source_dir)]
            source_type = "github_repo"
            origin_url = github

        manifest = {
            "source_id": source_id,
            "source_type": source_type,
            "origin_url": origin_url,
            "paper_doi": paper_doi,
            "license": license_text,
            "imported_at": utc_now(),
            "files_retained": [item["path"] for item in retained],
            "analysis_capabilities": [],
            "figure_style_features": [],
            "allowed_use": [
                "provenance review",
                "manual adaptation into wrappers after tests",
                "figure style inspiration after license review",
            ],
            "forbidden_use": [
                "silent executable module registration",
                "raw data mirroring",
                "claiming license clearance without human review",
            ],
            "adaptation_status": "imported_for_review",
        }
        write_yaml(source_dir / "source_manifest.yaml", manifest)
        write_yaml(
            source_dir / "retained_files_manifest.yaml",
            {
                "source_id": source_id,
                "retained_at": utc_now(),
                "files": retained,
            },
        )
        write_yaml(
            source_dir / "license_review.yaml",
            {
                "source_id": source_id,
                "status": "pending_human_review",
                "license_declared": license_text,
                "registry_update_allowed": False,
                "notes": "Do not register executable modules until license/provenance review and tests pass.",
            },
        )
        return SourceImportResult(
            source_id=source_id,
            source_dir=str(source_dir),
            manifest_path=str(source_dir / "source_manifest.yaml"),
            retained_count=len(retained),
            status="imported_for_review",
        )

    def review_source(self, source_id: str) -> dict[str, Any]:
        source_dir = self.source_dir(source_id)
        manifest = read_yaml(source_dir / "source_manifest.yaml")
        if not manifest:
            raise FileNotFoundError(f"source manifest not found for {source_id}")
        review = read_yaml(source_dir / "license_review.yaml")
        review.update({
            "source_id": source_id,
            "reviewed_at": utc_now(),
            "status": "provenance_recorded_pending_human_license_decision",
            "registry_update_allowed": False,
            "required_next_steps": [
                "human license review",
                "adapted wrapper",
                "tests",
                "module_registry proposal",
            ],
        })
        write_yaml(source_dir / "license_review.yaml", review)
        return review

    def register_figure_style(self, source_id: str, style_id: str = "") -> dict[str, Any]:
        source_dir = self.source_dir(source_id)
        manifest = read_yaml(source_dir / "source_manifest.yaml")
        if not manifest:
            raise FileNotFoundError(f"source manifest not found for {source_id}")
        style_id = style_id or f"{source_id}_figure_style_v1"
        registry = read_yaml(self.figure_style_registry)
        styles = registry.setdefault("styles", {})
        styles[style_id] = {
            "source_id": source_id,
            "plot_types": ["UMAP", "dotplot", "heatmap", "volcano"],
            "layout_rules": "manual extraction required from reviewed source",
            "palette": "requires_human_review",
            "typography": "requires_human_review",
            "panel_labeling": "requires_human_review",
            "compatible_modules": [],
            "reviewer_risk": [
                "style inspiration does not validate scientific claims",
                "license and attribution review required before reuse",
            ],
            "registered_at": utc_now(),
        }
        write_yaml(self.figure_style_registry, registry)
        return {"style_id": style_id, "style": styles[style_id]}

    def list_figure_styles(self) -> dict[str, Any]:
        data = read_yaml(self.figure_style_registry)
        data.setdefault("styles", {})
        return data

    def _retain_local_files(self, source: Path, destination: Path) -> list[dict[str, Any]]:
        source = source.resolve()
        if not source.exists():
            raise FileNotFoundError(f"local source not found: {source}")
        retained: list[dict[str, Any]] = []
        files = [source] if source.is_file() else [p for p in source.rglob("*") if p.is_file()]
        for path in files:
            if any(part in SKIP_PARTS for part in path.parts):
                continue
            if path.stat().st_size > MAX_RETAINED_BYTES:
                continue
            rel = path.name if source.is_file() else str(path.relative_to(source))
            target = destination / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
            retained.append(self._manifest_entry(target, destination.parent))
        return retained

    @staticmethod
    def _manifest_entry(path: Path, base: Path) -> dict[str, Any]:
        return {
            "path": str(path.relative_to(base)).replace("\\", "/"),
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }

    @staticmethod
    def _validate_source_id(source_id: str) -> None:
        if not SOURCE_ID_RE.match(source_id):
            raise ValueError("source_id must be 2-81 characters and contain only letters, numbers, dot, dash, or underscore")
