"""Audit method assets for inspectable source, descriptions, and locks."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from paper_workflow.bioinformatics.module_registry import ModuleRegistry


COMMON_WRAPPERS = {
    "single_cell": "code_library/modules/single_cell/common/sc_module_wrapper.R",
    "bulk_rnaseq": "code_library/modules/bulk_rnaseq/common/bulk_module_wrapper.R",
    "spatial": "code_library/modules/spatial/common/spatial_module_wrapper.R",
}


class MethodAssetAuditor:
    """Repository-level method-asset production gate."""

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.registry = ModuleRegistry(self.project_root)

    def run(self) -> dict[str, Any]:
        modules = []
        issues: list[str] = []
        warnings: list[str] = []
        catalog_path = self.project_root / "code_library" / "modules" / "MODULE_SOURCE_CATALOG.md"
        catalog_text = catalog_path.read_text(encoding="utf-8") if catalog_path.exists() else ""

        for module_id, module in sorted(self.registry.modules.items()):
            audit = self.audit_module(module_id, module, catalog_text)
            modules.append(audit)
            issues.extend(audit["issues"])
            warnings.extend(audit["warnings"])

        status = "fail" if issues else ("warn" if warnings else "pass")
        return {
            "schema_version": "method_asset_audit.v1",
            "status": status,
            "module_count": len(modules),
            "issue_count": len(issues),
            "warning_count": len(warnings),
            "catalog_path": str(catalog_path),
            "issues": issues,
            "warnings": warnings,
            "modules": modules,
        }

    def audit_module(self, module_id: str, module: dict[str, Any], catalog_text: str = "") -> dict[str, Any]:
        source_rel = str((module.get("source") or {}).get("path") or "")
        source_path = self.project_root / source_rel
        module_dir = source_path.parent if source_rel else self.project_root
        module_asset_dir = self.project_root / "code_library" / "modules" / str(module.get("modality", "")) / str(module.get("step", ""))
        readme_candidates = [module_dir / "README.md", module_asset_dir / "README.md"]
        readme_path = next((path for path in readme_candidates if path.exists()), readme_candidates[0])
        env_id = str((module.get("environment") or {}).get("env_id", ""))
        maturity = str(module.get("method_maturity", ""))
        validation = str(module.get("validation_status", ""))
        issues: list[str] = []
        warnings: list[str] = []

        source_exists = source_path.exists()
        source_size = source_path.stat().st_size if source_exists else 0
        direct_functions = self.extract_functions(source_path) if source_exists else []
        delegated_sources = self.delegated_sources(module, source_path)
        auditable_scripts = [source_rel] if source_rel else []
        auditable_scripts.extend(delegated_sources)

        if not source_exists:
            issues.append(f"{module_id}: source script missing: {source_rel}")
        elif source_size < 700 and not delegated_sources:
            issues.append(f"{module_id}: source script is too thin and has no auditable delegated wrapper")

        readme_text = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""
        if not readme_path.exists() or len(readme_text.strip()) < 80:
            issues.append(f"{module_id}: README description missing or too short")
        if module_id not in catalog_text:
            issues.append(f"{module_id}: MODULE_SOURCE_CATALOG.md entry missing")

        env_lock = self.environment_lock(env_id)
        if env_id in {"r_bulk_rnaseq", "r_pseudobulk_deseq2"} and not env_lock.get("present"):
            issues.append(f"{module_id}: required environment lock missing for {env_id}")

        lower_maturity = maturity.lower()
        lower_validation = validation.lower()
        if any(token in lower_maturity for token in ["thin_wrapper", "adapter_contract", "pilot"]) or "dry" in lower_validation:
            warnings.append(f"{module_id}: maturity={maturity} validation={validation}; not publication-grade until real-data execution evidence exists")

        return {
            "module_id": module_id,
            "name": module.get("name", ""),
            "modality": module.get("modality", ""),
            "step": module.get("step", ""),
            "language": module.get("language", ""),
            "source_path": source_rel,
            "source_exists": source_exists,
            "source_size_bytes": source_size,
            "auditable_scripts": auditable_scripts,
            "functions": direct_functions,
            "delegated_sources": delegated_sources,
            "readme_path": str(readme_path.relative_to(self.project_root)).replace("\\", "/") if readme_path.exists() else "",
            "description_status": "present" if readme_path.exists() and len(readme_text.strip()) >= 80 else "missing_or_too_short",
            "environment_id": env_id,
            "environment_lock": env_lock,
            "execution_type": (module.get("execution") or {}).get("type", "not_declared"),
            "method_maturity": maturity,
            "validation_status": validation,
            "issues": issues,
            "warnings": warnings,
        }

    def delegated_sources(self, module: dict[str, Any], source_path: Path) -> list[str]:
        delegated = []
        if source_path.exists():
            text = source_path.read_text(encoding="utf-8", errors="replace")
            for match in re.findall(r"source\s*\(\s*['\"]([^'\"]+)['\"]", text):
                candidate = (source_path.parent / match).resolve()
                if candidate.exists():
                    delegated.append(str(candidate.relative_to(self.project_root)).replace("\\", "/"))
        modality = str(module.get("modality", ""))
        common = COMMON_WRAPPERS.get(modality)
        if common and source_path.exists() and (self.project_root / common).exists():
            text = source_path.read_text(encoding="utf-8", errors="replace") if source_path.exists() else ""
            if "common" in text or source_path.stat().st_size < 900:
                delegated.append(common)
        return sorted(set(delegated))

    def environment_lock(self, env_id: str) -> dict[str, Any]:
        env = self.registry_environment(env_id)
        lock_file = str(env.get("lock_file", ""))
        lock_path = self.project_root / lock_file if lock_file and not Path(lock_file).is_absolute() else Path(lock_file)
        return {
            "lock_file": lock_file,
            "present": bool(lock_file) and lock_path.exists(),
        }

    def registry_environment(self, env_id: str) -> dict[str, Any]:
        env_data = self.project_root / "code_library" / "environment_registry.yaml"
        if not env_data.exists():
            return {}
        import yaml

        data = yaml.safe_load(env_data.read_text(encoding="utf-8")) or {}
        envs = data.get("environments", {}) or {}
        return dict(envs.get(env_id, {}) or {})

    @staticmethod
    def extract_functions(path: Path) -> list[str]:
        suffix = path.suffix.lower()
        text = path.read_text(encoding="utf-8", errors="replace")
        if suffix == ".py":
            return sorted(set(re.findall(r"(?m)^\s*def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", text)))
        if suffix == ".r":
            return sorted(set(re.findall(r"(?m)^\s*([A-Za-z.][A-Za-z0-9_.]*)\s*(?:<-|=)\s*function\s*\(", text)))
        return []

    def render_source_catalog(self) -> str:
        audit = self.run()
        lines = [
            "# Method Source Catalog",
            "",
            "This catalog is the clickable source index for `code_library/modules`.",
            "Each entry identifies the script a researcher can inspect, delegated common wrappers, purpose, execution type, maturity, and current publication boundary.",
            "",
        ]
        for item in audit["modules"]:
            module = self.registry.get(item["module_id"])
            purpose = "; ".join(str(v) for v in module.get("biological_question_types", []) or module.get("reviewer_value", []) or ["not_declared"])
            lines.extend(
                [
                    f"## {item['module_id']}",
                    "",
                    f"- Name: {item['name']}",
                    f"- Purpose/use: {purpose}",
                    f"- Modality/step/language: {item['modality']} / {item['step']} / {item['language']}",
                    f"- Primary script: `{item['source_path']}`",
                    f"- Auditable scripts: {', '.join('`' + p + '`' for p in item['auditable_scripts']) or 'not_declared'}",
                    f"- Functions in primary script: {', '.join(item['functions']) if item['functions'] else 'delegated or script-level workflow'}",
                    f"- Execution type: {item['execution_type']}",
                    f"- Environment lock: `{item['environment_lock']['lock_file'] or 'not_declared'}` status={item['environment_lock']['present']}",
                    f"- Maturity/validation: {item['method_maturity']} / {item['validation_status']}",
                    f"- Claim boundary: {module.get('claim_boundary', 'not_declared')}",
                    "",
                ]
            )
        return "\n".join(lines)
