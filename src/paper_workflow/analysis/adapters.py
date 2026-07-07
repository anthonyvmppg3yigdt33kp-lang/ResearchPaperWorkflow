"""Bounded analysis adapters.

Adapters create transparent execution packages. Real computation remains
behind explicit approval; dry-run mode is the default for agent-triggered
analysis planning.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any

import yaml

from paper_workflow.analysis.design import AnalysisDesign
from paper_workflow.outputs.result_run_manager import read_yaml, utc_now, write_yaml


@dataclass
class AdapterRunResult:
    """Result from an analysis adapter invocation."""

    status: str
    adapter: str
    run_id: str
    artifacts: list[dict[str, str]]
    metrics: dict[str, Any]
    warnings: list[str]
    errors: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "adapter": self.adapter,
            "run_id": self.run_id,
            "artifacts": self.artifacts,
            "metrics": self.metrics,
            "warnings": self.warnings,
            "errors": self.errors,
        }


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _artifact(path: Path, run_dir: Path, source_stage: str = "run_analysis") -> dict[str, str]:
    paper_dir = run_dir.parents[2]
    suffix = path.suffix.lower()
    mime = "text/plain"
    if suffix in {".yaml", ".yml"}:
        mime = "application/yaml"
    elif suffix == ".md":
        mime = "text/markdown"
    elif suffix == ".csv":
        mime = "text/csv"
    elif suffix == ".svg":
        mime = "image/svg+xml"
    return {
        "path": str(path.relative_to(paper_dir)),
        "mime_type": mime,
        "source_stage": source_stage,
    }


def _resolve_input(path_text: str, paper_dir: Path, run_dir: Path) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    paper_candidate = paper_dir / path
    if paper_candidate.exists():
        return paper_candidate
    return run_dir / path


def _parse_contrast(contrast: str, observed_groups: list[str]) -> tuple[str, str, list[str]]:
    warnings: list[str] = []
    text = contrast.replace(" versus ", " vs ").replace(" VS ", " vs ")
    if " vs " in text:
        left, right = [p.strip() for p in text.split(" vs ", 1)]
    elif len(observed_groups) >= 2:
        left, right = observed_groups[0], observed_groups[1]
        warnings.append(f"primary_contrast was not parseable; using observed groups {left} vs {right}")
    else:
        left, right = "", ""
    return left, right, warnings


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _variance(values: list[float], mean_value: float) -> float:
    if len(values) < 2:
        return 0.0
    return sum((v - mean_value) ** 2 for v in values) / (len(values) - 1)


def _normal_p_from_t(t_stat: float) -> float:
    return max(0.0, min(1.0, math.erfc(abs(t_stat) / math.sqrt(2.0))))


def _bh_fdr(p_values: list[float]) -> list[float]:
    n = len(p_values)
    order = sorted(range(n), key=lambda i: p_values[i])
    adjusted = [1.0] * n
    running = 1.0
    for rank, idx in reversed(list(enumerate(order, start=1))):
        running = min(running, p_values[idx] * n / rank)
        adjusted[idx] = min(1.0, running)
    return adjusted


def _safe_float(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _render_volcano_svg(path: Path, rows: list[dict[str, Any]]) -> None:
    width, height = 720, 520
    plot = rows[:500]
    if not plot:
        _write_text(path, "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"720\" height=\"520\"></svg>\n")
        return
    xs = [float(r["log2_fold_change"]) for r in plot]
    ys = [-math.log10(max(float(r["p_value"]), 1e-300)) for r in plot]
    max_abs_x = max(max(abs(x) for x in xs), 1.0)
    max_y = max(max(ys), 1.0)
    points = []
    for row, x, y in zip(plot, xs, ys):
        px = 70 + ((x + max_abs_x) / (2 * max_abs_x)) * 590
        py = 455 - (y / max_y) * 385
        color = "#b91c1c" if float(row["fdr"]) < 0.05 and abs(x) >= 1 else "#475569"
        points.append(f'<circle cx="{px:.2f}" cy="{py:.2f}" r="3" fill="{color}" opacity="0.78" />')
    _write_text(
        path,
        "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"720\" height=\"520\" viewBox=\"0 0 720 520\">\n"
        "<rect width=\"720\" height=\"520\" fill=\"white\"/>\n"
        "<text x=\"360\" y=\"28\" text-anchor=\"middle\" font-family=\"Arial\" font-size=\"18\">Pilot volcano plot</text>\n"
        "<line x1=\"70\" y1=\"455\" x2=\"660\" y2=\"455\" stroke=\"#111827\"/>\n"
        "<line x1=\"70\" y1=\"70\" x2=\"70\" y2=\"455\" stroke=\"#111827\"/>\n"
        "<text x=\"365\" y=\"500\" text-anchor=\"middle\" font-family=\"Arial\" font-size=\"13\">log2 fold change</text>\n"
        "<text x=\"18\" y=\"260\" transform=\"rotate(-90 18 260)\" text-anchor=\"middle\" font-family=\"Arial\" font-size=\"13\">-log10 p value</text>\n"
        + "\n".join(points)
        + "\n</svg>\n",
    )


def _render_heatmap_svg(path: Path, rows: list[dict[str, Any]]) -> None:
    top = rows[:20]
    cell_w, cell_h = 120, 22
    width = 360
    height = 80 + len(top) * cell_h
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="180" y="25" text-anchor="middle" font-family="Arial" font-size="16">Pilot group-mean heatmap</text>',
        '<text x="145" y="55" text-anchor="middle" font-family="Arial" font-size="12">group A</text>',
        '<text x="265" y="55" text-anchor="middle" font-family="Arial" font-size="12">group B</text>',
    ]
    for i, row in enumerate(top):
        y = 70 + i * cell_h
        a = float(row["mean_log_cpm_group_a"])
        b = float(row["mean_log_cpm_group_b"])
        m = max(abs(a), abs(b), 1.0)
        ca = int(240 - min(160, abs(a) / m * 120))
        cb = int(240 - min(160, abs(b) / m * 120))
        parts.append(f'<text x="10" y="{y + 15}" font-family="Arial" font-size="11">{row["gene"]}</text>')
        parts.append(f'<rect x="90" y="{y}" width="{cell_w}" height="{cell_h - 2}" fill="rgb({ca},220,255)"/>')
        parts.append(f'<rect x="210" y="{y}" width="{cell_w}" height="{cell_h - 2}" fill="rgb(255,{cb},210)"/>')
    parts.append("</svg>")
    _write_text(path, "\n".join(parts) + "\n")


class BulkRNASeqDryRunAdapter:
    """Create a DESeq2-oriented bulk RNA-seq execution package without running R."""

    name = "bulk_rnaseq_deseq2_dry_run"

    def run(self, design: AnalysisDesign, run_dir: Path, execute: bool = False) -> AdapterRunResult:
        start = perf_counter()
        artifacts: list[dict[str, str]] = []
        warnings: list[str] = []
        errors: list[str] = []

        is_valid, issues = design.validate(require_approval=execute)
        if issues:
            warnings.extend(issues)

        if execute:
            errors.append(
                "real execution is not enabled by this adapter yet; rerun after dependency/setup and explicit executor implementation"
            )
            status = "blocked"
        else:
            status = "dry_run_completed"

        blueprint = run_dir / "execution_blueprint.md"
        _write_text(
            blueprint,
            "# Bulk RNA-seq Execution Blueprint\n\n"
            f"- Run ID: `{design.run_id}`\n"
            f"- Adapter: `{self.name}`\n"
            f"- Execution mode: `{'real' if execute else 'dry_run'}`\n"
            f"- Research question: {design.research_question or design.goal}\n"
            f"- Primary contrast: {design.primary_contrast}\n"
            f"- Statistical unit: `{design.statistical_unit}`\n\n"
            "## Planned Method\n\n"
            "1. Validate count matrix and sample metadata.\n"
            "2. Check sample-level grouping, covariates, and batch/confounder plan.\n"
            "3. Run DESeq2 size-factor normalization and negative-binomial GLM.\n"
            "4. Apply multiple-testing correction and effect-size reporting.\n"
            "5. Generate QC, volcano, heatmap, and enrichment-ready tables.\n\n"
            "## Execution Boundary\n\n"
            "This package is a dry run. It does not execute R, install packages, "
            "download gene sets, or create final biological results.\n",
        )
        artifacts.append(_artifact(blueprint, run_dir))

        planned_outputs = [
            {"path": "tables/differential_expression.csv", "status": "planned", "type": "table"},
            {"path": "tables/normalized_counts_summary.csv", "status": "planned", "type": "table"},
            {"path": "figures/volcano_plot.pdf", "status": "planned", "type": "figure"},
            {"path": "figures/deg_heatmap.pdf", "status": "planned", "type": "figure"},
            {"path": "qc/bulk_qc_report.md", "status": "planned", "type": "qc"},
        ]
        write_yaml(
            run_dir / "outputs_manifest.yaml",
            {
                "schema_version": "1.0.0",
                "run_id": design.run_id,
                "execution_mode": "real" if execute else "dry_run",
                "outputs": planned_outputs,
                "updated_at": utc_now(),
            },
        )
        artifacts.append(_artifact(run_dir / "outputs_manifest.yaml", run_dir))

        write_yaml(
            run_dir / "parameters.yaml",
            {
                "schema_version": "1.0.0",
                "run_id": design.run_id,
                "model": {
                    "engine": "DESeq2",
                    "primary_contrast": design.primary_contrast,
                    "covariates": design.covariates,
                    "batch_or_confounder_plan": design.batch_or_confounder_plan,
                    "statistical_unit": design.statistical_unit,
                },
                "normalization_or_preprocessing": design.normalization_or_preprocessing,
                "multiple_testing": "Benjamini-Hochberg FDR",
                "created_at": utc_now(),
            },
        )
        artifacts.append(_artifact(run_dir / "parameters.yaml", run_dir))

        write_yaml(
            run_dir / "inputs_manifest.yaml",
            {
                "schema_version": "1.0.0",
                "run_id": design.run_id,
                "inputs": [{"path": p, "status": "declared"} for p in design.inputs],
                "raw_data_mutation": "forbidden",
                "updated_at": utc_now(),
            },
        )
        artifacts.append(_artifact(run_dir / "inputs_manifest.yaml", run_dir))

        write_yaml(
            run_dir / "qc" / "dry_run_checklist.yaml",
            {
                "schema_version": "1.0.0",
                "run_id": design.run_id,
                "checks": [
                    {"name": "design_present", "passed": True},
                    {"name": "user_approval_for_real_execution", "passed": bool(design.user_approval)},
                    {"name": "package_install_blocked_in_agent_phase", "passed": True},
                    {"name": "output_path_scoped", "passed": True},
                ],
                "contract_status": "ready_for_review" if not errors else "blocked",
            },
        )
        artifacts.append(_artifact(run_dir / "qc" / "dry_run_checklist.yaml", run_dir))

        write_yaml(
            run_dir / "figure_source_map.yaml",
            {
                "schema_version": "1.0.0",
                "status": "pending_execution",
                "figures": [],
                "note": "No final figures exist in dry-run mode.",
            },
        )
        artifacts.append(_artifact(run_dir / "figure_source_map.yaml", run_dir))

        write_yaml(
            run_dir / "table_source_map.yaml",
            {
                "schema_version": "1.0.0",
                "status": "pending_execution",
                "tables": [],
                "note": "No final tables exist in dry-run mode.",
            },
        )
        artifacts.append(_artifact(run_dir / "table_source_map.yaml", run_dir))

        log = run_dir / "logs" / "analysis_executor.log"
        _write_text(
            log,
            f"{utc_now()} adapter={self.name} status={status} execute={execute}\n"
            f"warnings={len(warnings)} errors={len(errors)}\n",
        )
        artifacts.append(_artifact(log, run_dir))

        manifest = read_yaml(run_dir / "run_manifest.yaml")
        manifest.update({
            "schema_version": "1.0.0",
            "run_id": design.run_id,
            "mode": "execution_mode" if execute else "analysis_design_mode",
            "status": status,
            "analysis_adapter": self.name,
            "execution_status": "blocked" if errors else "not_executed",
            "executed_at": utc_now(),
            "dry_run": not execute,
            "outputs_generated": [a["path"] for a in artifacts],
            "warnings": warnings,
            "errors": errors,
            "token_accounting": {
                "status": "not_available",
                "note": "Local CLI/test harness does not expose per-command token usage.",
            },
        })
        write_yaml(run_dir / "run_manifest.yaml", manifest)
        artifacts.append(_artifact(run_dir / "run_manifest.yaml", run_dir))

        metrics = {
            "runtime_seconds": round(perf_counter() - start, 6),
            "planned_output_count": len(planned_outputs),
            "declared_input_count": len(design.inputs),
            "agent_steps_estimate": 1,
            "design_issue_count": len(issues),
        }
        return AdapterRunResult(
            status=status,
            adapter=self.name,
            run_id=design.run_id,
            artifacts=artifacts,
            metrics=metrics,
            warnings=warnings,
            errors=errors,
        )


class BulkRNASeqPythonPilotAdapter:
    """Run a small built-in bulk RNA-seq pilot from CSV inputs.

    This is not a replacement for DESeq2. It is a lightweight execution test
    harness that proves the workflow can read inputs, write scoped outputs,
    generate source maps, and report quality without external dependencies.
    """

    name = "bulk_rnaseq_python_builtin_pilot"

    def run(self, design: AnalysisDesign, run_dir: Path, execute: bool = False) -> AdapterRunResult:
        start = perf_counter()
        artifacts: list[dict[str, str]] = []
        warnings: list[str] = []
        errors: list[str] = []
        paper_dir = run_dir.parents[2]

        if not execute:
            return BulkRNASeqDryRunAdapter().run(design, run_dir, execute=False)

        is_valid, issues = design.validate(require_approval=True)
        warnings.extend(issues)
        if not design.user_approval:
            errors.append("user approval is required for pilot execution")
        if len(design.inputs) < 2:
            errors.append("bulk pilot requires two inputs: count matrix CSV and metadata CSV")

        count_path = _resolve_input(design.inputs[0], paper_dir, run_dir) if design.inputs else Path()
        metadata_path = _resolve_input(design.inputs[1], paper_dir, run_dir) if len(design.inputs) > 1 else Path()
        if count_path and not count_path.exists():
            errors.append(f"count matrix not found: {count_path}")
        if metadata_path and not metadata_path.exists():
            errors.append(f"metadata file not found: {metadata_path}")

        if errors:
            return self._write_blocked(run_dir, design, warnings, errors, start)

        rows, sample_ids = self._read_counts(count_path)
        metadata = self._read_metadata(metadata_path, design.sample_id_column, design.group_column)
        if not rows:
            errors.append("count matrix contains no gene rows")
        if not metadata:
            errors.append("metadata contains no usable sample rows")
        samples = [s for s in sample_ids if s in metadata]
        if len(samples) < 2:
            errors.append("fewer than two count-metadata matched samples")
        if errors:
            return self._write_blocked(run_dir, design, warnings, errors, start)

        group_values = []
        for sample in samples:
            group = metadata[sample][design.group_column]
            if group not in group_values:
                group_values.append(group)
        group_a, group_b, contrast_warnings = _parse_contrast(design.primary_contrast, group_values)
        warnings.extend(contrast_warnings)
        group_a_samples = [s for s in samples if metadata[s][design.group_column] == group_a]
        group_b_samples = [s for s in samples if metadata[s][design.group_column] == group_b]
        if not group_a_samples or not group_b_samples:
            errors.append(f"contrast groups not found in metadata: {group_a} vs {group_b}")
            return self._write_blocked(run_dir, design, warnings, errors, start)

        library_sizes = {
            sample: sum(row["counts"].get(sample, 0.0) for row in rows)
            for sample in samples
        }
        de_rows = self._compute_de(rows, samples, group_a_samples, group_b_samples, library_sizes)
        de_rows.sort(key=lambda row: (float(row["fdr"]), -abs(float(row["log2_fold_change"]))))
        sample_qc = [
            {
                "sample_id": sample,
                "group": metadata[sample][design.group_column],
                "library_size": f"{library_sizes[sample]:.0f}",
                "detected_genes": sum(1 for row in rows if row["counts"].get(sample, 0.0) > 0),
            }
            for sample in samples
        ]

        de_path = run_dir / "tables" / "differential_expression_pilot.csv"
        _write_csv(
            de_path,
            de_rows,
            [
                "gene", "mean_log_cpm_group_a", "mean_log_cpm_group_b",
                "log2_fold_change", "t_statistic", "p_value", "fdr",
            ],
        )
        artifacts.append(_artifact(de_path, run_dir))

        sample_qc_path = run_dir / "qc" / "sample_qc.csv"
        _write_csv(sample_qc_path, sample_qc, ["sample_id", "group", "library_size", "detected_genes"])
        artifacts.append(_artifact(sample_qc_path, run_dir))

        qc_report = run_dir / "qc" / "bulk_pilot_qc_report.md"
        significant = [r for r in de_rows if float(r["fdr"]) < 0.05 and abs(float(r["log2_fold_change"])) >= 1.0]
        _write_text(
            qc_report,
            "# Bulk RNA-seq Pilot QC Report\n\n"
            f"- Run ID: `{design.run_id}`\n"
            f"- Adapter: `{self.name}`\n"
            f"- Count matrix: `{count_path}`\n"
            f"- Metadata: `{metadata_path}`\n"
            f"- Matched samples: {len(samples)}\n"
            f"- Genes tested: {len(de_rows)}\n"
            f"- Contrast: `{group_a}` vs `{group_b}`\n"
            f"- Significant pilot rows (FDR < 0.05 and |log2FC| >= 1): {len(significant)}\n\n"
            "This pilot uses logCPM group means, a Welch-style statistic, and a normal "
            "approximation for p values. It is a workflow execution test, not a "
            "publication-grade DESeq2 result.\n",
        )
        artifacts.append(_artifact(qc_report, run_dir))

        volcano = run_dir / "figures" / "volcano_plot.svg"
        heatmap = run_dir / "figures" / "deg_heatmap.svg"
        _render_volcano_svg(volcano, de_rows)
        _render_heatmap_svg(heatmap, de_rows)
        artifacts.append(_artifact(volcano, run_dir))
        artifacts.append(_artifact(heatmap, run_dir))

        self._write_source_maps(run_dir, design, de_path, sample_qc_path, volcano, heatmap)
        artifacts.append(_artifact(run_dir / "figure_source_map.yaml", run_dir))
        artifacts.append(_artifact(run_dir / "table_source_map.yaml", run_dir))

        outputs = [
            {"path": str(Path(a["path"]).relative_to("results/runs/" + design.run_id)) if a["path"].startswith(f"results/runs/{design.run_id}/") else a["path"], "status": "generated"}
            for a in artifacts
        ]
        write_yaml(
            run_dir / "outputs_manifest.yaml",
            {
                "schema_version": "1.0.0",
                "run_id": design.run_id,
                "execution_mode": "pilot",
                "outputs": outputs,
                "updated_at": utc_now(),
            },
        )
        artifacts.append(_artifact(run_dir / "outputs_manifest.yaml", run_dir))

        write_yaml(
            run_dir / "parameters.yaml",
            {
                "schema_version": "1.0.0",
                "run_id": design.run_id,
                "backend": self.name,
                "primary_contrast": f"{group_a} vs {group_b}",
                "group_column": design.group_column,
                "sample_id_column": design.sample_id_column,
                "statistical_unit": design.statistical_unit,
                "method": "logCPM group means, Welch-style statistic, BH FDR",
                "created_at": utc_now(),
            },
        )
        artifacts.append(_artifact(run_dir / "parameters.yaml", run_dir))

        write_yaml(
            run_dir / "inputs_manifest.yaml",
            {
                "schema_version": "1.0.0",
                "run_id": design.run_id,
                "inputs": [
                    {"path": str(count_path), "role": "count_matrix", "status": "used"},
                    {"path": str(metadata_path), "role": "metadata", "status": "used"},
                ],
                "raw_data_mutation": "none",
                "updated_at": utc_now(),
            },
        )
        artifacts.append(_artifact(run_dir / "inputs_manifest.yaml", run_dir))

        log = run_dir / "logs" / "analysis_executor.log"
        _write_text(
            log,
            f"{utc_now()} adapter={self.name} status=pilot_completed execute={execute}\n"
            f"genes={len(de_rows)} samples={len(samples)} significant={len(significant)}\n",
        )
        artifacts.append(_artifact(log, run_dir))

        metrics = {
            "runtime_seconds": round(perf_counter() - start, 6),
            "genes_tested": len(de_rows),
            "matched_samples": len(samples),
            "group_a": group_a,
            "group_b": group_b,
            "group_a_samples": len(group_a_samples),
            "group_b_samples": len(group_b_samples),
            "significant_rows_fdr_0_05_abs_log2fc_1": len(significant),
            "agent_steps_estimate": 1,
        }
        write_yaml(
            run_dir / "qc" / "pilot_quality_report.yaml",
            {
                "schema_version": "1.0.0",
                "run_id": design.run_id,
                "status": "pilot_completed",
                "metrics": metrics,
                "warnings": warnings,
                "limitations": [
                    "pilot statistics are approximate",
                    "publication-grade DE requires DESeq2/edgeR/limma setup phase",
                    "SVG figures are workflow-quality previews",
                ],
            },
        )
        artifacts.append(_artifact(run_dir / "qc" / "pilot_quality_report.yaml", run_dir))

        manifest = read_yaml(run_dir / "run_manifest.yaml")
        manifest.update({
            "schema_version": "1.0.0",
            "run_id": design.run_id,
            "mode": "execution_mode",
            "status": "pilot_completed",
            "analysis_adapter": self.name,
            "execution_status": "completed",
            "executed_at": utc_now(),
            "dry_run": False,
            "outputs_generated": [a["path"] for a in artifacts],
            "metrics": metrics,
            "warnings": warnings,
            "errors": [],
            "token_accounting": {
                "status": "not_available",
                "note": "Local CLI/test harness does not expose per-command token usage.",
            },
        })
        write_yaml(run_dir / "run_manifest.yaml", manifest)
        artifacts.append(_artifact(run_dir / "run_manifest.yaml", run_dir))

        return AdapterRunResult(
            status="pilot_completed",
            adapter=self.name,
            run_id=design.run_id,
            artifacts=artifacts,
            metrics=metrics,
            warnings=warnings,
            errors=[],
        )

    def _write_blocked(
        self,
        run_dir: Path,
        design: AnalysisDesign,
        warnings: list[str],
        errors: list[str],
        start: float,
    ) -> AdapterRunResult:
        write_yaml(
            run_dir / "run_manifest.yaml",
            {
                "schema_version": "1.0.0",
                "run_id": design.run_id,
                "mode": "execution_mode",
                "status": "blocked",
                "analysis_adapter": self.name,
                "execution_status": "blocked",
                "executed_at": utc_now(),
                "dry_run": False,
                "warnings": warnings,
                "errors": errors,
            },
        )
        write_yaml(
            run_dir / "qc" / "pilot_quality_report.yaml",
            {
                "schema_version": "1.0.0",
                "run_id": design.run_id,
                "status": "blocked",
                "warnings": warnings,
                "errors": errors,
            },
        )
        artifacts = [
            _artifact(run_dir / "run_manifest.yaml", run_dir),
            _artifact(run_dir / "qc" / "pilot_quality_report.yaml", run_dir),
        ]
        return AdapterRunResult(
            status="blocked",
            adapter=self.name,
            run_id=design.run_id,
            artifacts=artifacts,
            metrics={"runtime_seconds": round(perf_counter() - start, 6)},
            warnings=warnings,
            errors=errors,
        )

    @staticmethod
    def _read_counts(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
        with path.open("r", encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            sample_ids = [c for c in (reader.fieldnames or []) if c not in {"gene", "gene_id", "symbol"}]
            rows = []
            for raw in reader:
                gene = raw.get("gene") or raw.get("gene_id") or raw.get("symbol") or ""
                if not gene:
                    continue
                rows.append({
                    "gene": gene,
                    "counts": {sample: _safe_float(raw.get(sample, "0")) for sample in sample_ids},
                })
        return rows, sample_ids

    @staticmethod
    def _read_metadata(path: Path, sample_id_column: str, group_column: str) -> dict[str, dict[str, str]]:
        with path.open("r", encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            metadata: dict[str, dict[str, str]] = {}
            for row in reader:
                sample_id = row.get(sample_id_column, "")
                group = row.get(group_column, "")
                if sample_id and group:
                    metadata[sample_id] = dict(row)
            return metadata

    @staticmethod
    def _compute_de(
        rows: list[dict[str, Any]],
        samples: list[str],
        group_a_samples: list[str],
        group_b_samples: list[str],
        library_sizes: dict[str, float],
    ) -> list[dict[str, Any]]:
        p_values: list[float] = []
        computed: list[dict[str, Any]] = []
        for row in rows:
            log_cpm = {}
            for sample in samples:
                lib = max(library_sizes.get(sample, 0.0), 1.0)
                cpm = row["counts"].get(sample, 0.0) / lib * 1_000_000
                log_cpm[sample] = math.log2(cpm + 1.0)
            a_values = [log_cpm[s] for s in group_a_samples]
            b_values = [log_cpm[s] for s in group_b_samples]
            mean_a = _mean(a_values)
            mean_b = _mean(b_values)
            var_a = _variance(a_values, mean_a)
            var_b = _variance(b_values, mean_b)
            denom = math.sqrt((var_a / max(len(a_values), 1)) + (var_b / max(len(b_values), 1)))
            t_stat = (mean_a - mean_b) / denom if denom else 0.0
            p_value = _normal_p_from_t(t_stat)
            p_values.append(p_value)
            computed.append({
                "gene": row["gene"],
                "mean_log_cpm_group_a": mean_a,
                "mean_log_cpm_group_b": mean_b,
                "log2_fold_change": mean_a - mean_b,
                "t_statistic": t_stat,
                "p_value": p_value,
            })
        fdr_values = _bh_fdr(p_values)
        formatted = []
        for row, fdr in zip(computed, fdr_values):
            formatted.append({
                "gene": row["gene"],
                "mean_log_cpm_group_a": f"{row['mean_log_cpm_group_a']:.6f}",
                "mean_log_cpm_group_b": f"{row['mean_log_cpm_group_b']:.6f}",
                "log2_fold_change": f"{row['log2_fold_change']:.6f}",
                "t_statistic": f"{row['t_statistic']:.6f}",
                "p_value": f"{row['p_value']:.8g}",
                "fdr": f"{fdr:.8g}",
            })
        return formatted

    @staticmethod
    def _write_source_maps(
        run_dir: Path,
        design: AnalysisDesign,
        de_path: Path,
        sample_qc_path: Path,
        volcano: Path,
        heatmap: Path,
    ) -> None:
        write_yaml(
            run_dir / "figure_source_map.yaml",
            {
                "schema_version": "1.0.0",
                "status": "pilot_completed",
                "figures": [
                    {
                        "figure_id": "pilot_volcano",
                        "path": str(volcano.relative_to(run_dir)),
                        "source_data": str(de_path.relative_to(run_dir)),
                        "script": "paper_workflow.analysis.adapters.BulkRNASeqPythonPilotAdapter",
                        "method": "pilot logCPM effect-size and approximate p-value visualization",
                        "statistical_unit": design.statistical_unit,
                        "claim_boundary": "workflow pilot only; not publication-grade DE",
                    },
                    {
                        "figure_id": "pilot_deg_heatmap",
                        "path": str(heatmap.relative_to(run_dir)),
                        "source_data": str(de_path.relative_to(run_dir)),
                        "script": "paper_workflow.analysis.adapters.BulkRNASeqPythonPilotAdapter",
                        "method": "top pilot DE rows by FDR",
                        "statistical_unit": design.statistical_unit,
                        "claim_boundary": "workflow pilot only; not publication-grade heatmap",
                    },
                ],
            },
        )
        write_yaml(
            run_dir / "table_source_map.yaml",
            {
                "schema_version": "1.0.0",
                "status": "pilot_completed",
                "tables": [
                    {
                        "table_id": "pilot_differential_expression",
                        "path": str(de_path.relative_to(run_dir)),
                        "source_inputs": design.inputs,
                        "method": "pilot logCPM Welch-style contrast with BH FDR",
                        "statistical_unit": design.statistical_unit,
                    },
                    {
                        "table_id": "pilot_sample_qc",
                        "path": str(sample_qc_path.relative_to(run_dir)),
                        "source_inputs": design.inputs,
                        "method": "library size and detected gene count",
                        "statistical_unit": "sample",
                    },
                ],
            },
        )


def run_analysis_adapter(
    design: AnalysisDesign,
    run_dir: Path,
    execute: bool = False,
    backend: str | None = None,
) -> AdapterRunResult:
    """Dispatch to the safest available adapter for an analysis design."""
    modality = design.modality.lower().replace("-", "_")
    if modality in {"bulk_rnaseq", "bulk_rna_seq", "rnaseq", "rna_seq"}:
        selected_backend = backend or design.execution_backend
        if execute and selected_backend == "python_builtin_pilot":
            return BulkRNASeqPythonPilotAdapter().run(design, run_dir, execute=True)
        return BulkRNASeqDryRunAdapter().run(design, run_dir, execute=execute)
    return AdapterRunResult(
        status="blocked",
        adapter="unsupported",
        run_id=design.run_id,
        artifacts=[],
        metrics={},
        warnings=[],
        errors=[f"Unsupported modality for bounded adapter: {design.modality}"],
    )
