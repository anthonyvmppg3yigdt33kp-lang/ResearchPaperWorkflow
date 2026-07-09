#!/usr/bin/env python
"""Standalone Python bulk RNA-seq pilot method asset.

This script is intentionally dependency-light. It proves that graph execution
can run Python assets, bind count/metadata inputs, and write scoped source maps.
It is not a substitute for DESeq2, edgeR, or limma.
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a lightweight bulk RNA-seq pilot.")
    parser.add_argument("--counts", required=True, help="CSV count matrix with a gene column and sample columns.")
    parser.add_argument("--metadata", required=True, help="CSV sample metadata.")
    parser.add_argument("--out", required=True, help="Output directory.")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--condition-column", default="condition")
    parser.add_argument("--sample-id-column", default="sample_id")
    parser.add_argument("--reference", default="")
    parser.add_argument("--target", default="")
    return parser.parse_args()


def read_counts(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        sample_ids = [c for c in (reader.fieldnames or []) if c not in {"gene", "gene_id", "symbol"}]
        rows = []
        for raw in reader:
            gene = raw.get("gene") or raw.get("gene_id") or raw.get("symbol") or ""
            if not gene:
                continue
            rows.append({"gene": gene, "counts": {sample: safe_float(raw.get(sample, "0")) for sample in sample_ids}})
        return rows, sample_ids


def read_metadata(path: Path, sample_id_column: str, group_column: str) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        metadata = {}
        for row in reader:
            sample_id = row.get(sample_id_column, "")
            group = row.get(group_column, "")
            if sample_id and group:
                metadata[sample_id] = dict(row)
        return metadata


def safe_float(value: str | None) -> float:
    try:
        return float(value or 0.0)
    except ValueError:
        return 0.0


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def variance(values: list[float], value_mean: float) -> float:
    if len(values) < 2:
        return 0.0
    return sum((value - value_mean) ** 2 for value in values) / (len(values) - 1)


def normal_p_from_t(t_stat: float) -> float:
    return max(0.0, min(1.0, math.erfc(abs(t_stat) / math.sqrt(2.0))))


def bh_fdr(p_values: list[float]) -> list[float]:
    n = len(p_values)
    order = sorted(range(n), key=lambda i: p_values[i])
    adjusted = [1.0] * n
    running = 1.0
    for rank, idx in reversed(list(enumerate(order, start=1))):
        running = min(running, p_values[idx] * n / rank)
        adjusted[idx] = min(1.0, running)
    return adjusted


def select_groups(metadata: dict[str, dict[str, str]], group_column: str, reference: str, target: str) -> tuple[str, str]:
    groups = []
    for row in metadata.values():
        group = row.get(group_column, "")
        if group and group not in groups:
            groups.append(group)
    if reference and target:
        return reference, target
    if len(groups) < 2:
        raise ValueError("metadata must contain at least two groups or explicit --reference/--target")
    return groups[0], groups[1]


def compute_de(
    rows: list[dict[str, Any]],
    samples: list[str],
    group_a_samples: list[str],
    group_b_samples: list[str],
    library_sizes: dict[str, float],
) -> list[dict[str, str]]:
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
        mean_a = mean(a_values)
        mean_b = mean(b_values)
        var_a = variance(a_values, mean_a)
        var_b = variance(b_values, mean_b)
        denom = math.sqrt((var_a / max(len(a_values), 1)) + (var_b / max(len(b_values), 1)))
        t_stat = (mean_a - mean_b) / denom if denom else 0.0
        p_value = normal_p_from_t(t_stat)
        p_values.append(p_value)
        computed.append(
            {
                "gene": row["gene"],
                "mean_log_cpm_group_a": mean_a,
                "mean_log_cpm_group_b": mean_b,
                "log2_fold_change": mean_a - mean_b,
                "t_statistic": t_stat,
                "p_value": p_value,
            }
        )
    fdr_values = bh_fdr(p_values)
    return [
        {
            "gene": row["gene"],
            "mean_log_cpm_group_a": f"{row['mean_log_cpm_group_a']:.6f}",
            "mean_log_cpm_group_b": f"{row['mean_log_cpm_group_b']:.6f}",
            "log2_fold_change": f"{row['log2_fold_change']:.6f}",
            "t_statistic": f"{row['t_statistic']:.6f}",
            "p_value": f"{row['p_value']:.8g}",
            "fdr": f"{fdr:.8g}",
        }
        for row, fdr in zip(computed, fdr_values)
    ]


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def render_volcano(path: Path, rows: list[dict[str, str]]) -> None:
    points = []
    for idx, row in enumerate(rows[:500]):
        x = float(row["log2_fold_change"])
        y = -math.log10(max(float(row["p_value"]), 1e-300))
        px = 360 + max(-280, min(280, x * 55))
        py = 455 - max(0, min(380, y * 45))
        color = "#b91c1c" if float(row["fdr"]) < 0.05 and abs(x) >= 1 else "#475569"
        points.append(f'<circle cx="{px:.2f}" cy="{py:.2f}" r="3" fill="{color}" opacity="0.78"><title>{row["gene"]}</title></circle>')
    write_text(
        path,
        '<svg xmlns="http://www.w3.org/2000/svg" width="720" height="520" viewBox="0 0 720 520">\n'
        '<rect width="720" height="520" fill="white"/>\n'
        '<text x="360" y="30" text-anchor="middle" font-family="Arial" font-size="18">Python pilot volcano plot</text>\n'
        '<line x1="70" y1="455" x2="660" y2="455" stroke="#111827"/>\n'
        '<line x1="360" y1="70" x2="360" y2="455" stroke="#9ca3af" stroke-dasharray="5 5"/>\n'
        + "\n".join(points)
        + "\n</svg>\n",
    )


def render_heatmap(path: Path, rows: list[dict[str, str]]) -> None:
    top = rows[:20]
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="420" height="540" viewBox="0 0 420 540">', '<rect width="100%" height="100%" fill="white"/>']
    parts.append('<text x="210" y="28" text-anchor="middle" font-family="Arial" font-size="16">Top pilot rows</text>')
    for i, row in enumerate(top):
        y = 55 + i * 22
        lfc = float(row["log2_fold_change"])
        color = "#fee2e2" if lfc > 0 else "#dbeafe"
        parts.append(f'<rect x="145" y="{y}" width="210" height="18" fill="{color}"/>')
        parts.append(f'<text x="15" y="{y + 13}" font-family="Arial" font-size="11">{row["gene"]}</text>')
        parts.append(f'<text x="250" y="{y + 13}" font-family="Arial" font-size="11">log2FC {lfc:.2f}</text>')
    parts.append("</svg>")
    write_text(path, "\n".join(parts) + "\n")


def write_source_maps(out_dir: Path, de_path: Path, sample_qc_path: Path, volcano: Path, heatmap: Path) -> None:
    write_text(
        out_dir / "figure_source_map.yaml",
        "schema_version: python_builtin_pilot_source_map.v1\n"
        "figures:\n"
        "  - figure_id: python_pilot_volcano\n"
        f"    path: {volcano.relative_to(out_dir).as_posix()}\n"
        f"    source_data: {de_path.relative_to(out_dir).as_posix()}\n"
        "    script: code_library/modules/bulk_rnaseq/python_builtin_pilot/main.py\n"
        "    method: dependency-light logCPM pilot visualization\n"
        "    statistical_unit: sample\n"
        "    claim_boundary: workflow pilot only; not publication-grade DE\n"
        "  - figure_id: python_pilot_heatmap\n"
        f"    path: {heatmap.relative_to(out_dir).as_posix()}\n"
        f"    source_data: {de_path.relative_to(out_dir).as_posix()}\n"
        "    script: code_library/modules/bulk_rnaseq/python_builtin_pilot/main.py\n"
        "    method: top pilot rows by FDR\n"
        "    statistical_unit: gene\n"
        "    claim_boundary: workflow pilot only; not publication-grade heatmap\n",
    )
    write_text(
        out_dir / "table_source_map.yaml",
        "schema_version: python_builtin_pilot_source_map.v1\n"
        "tables:\n"
        "  - table_id: python_pilot_differential_expression\n"
        f"    path: {de_path.relative_to(out_dir).as_posix()}\n"
        "    method: logCPM group means with approximate p-values and BH FDR\n"
        "    statistical_unit: gene\n"
        "  - table_id: python_pilot_sample_qc\n"
        f"    path: {sample_qc_path.relative_to(out_dir).as_posix()}\n"
        "    method: library size and detected gene count\n"
        "    statistical_unit: sample\n",
    )


def main() -> int:
    args = parse_args()
    counts_path = Path(args.counts)
    metadata_path = Path(args.metadata)
    out_dir = Path(args.out)
    rows, sample_ids = read_counts(counts_path)
    metadata = read_metadata(metadata_path, args.sample_id_column, args.condition_column)
    samples = [sample for sample in sample_ids if sample in metadata]
    if len(samples) < 2:
        raise SystemExit("fewer than two count-metadata matched samples")
    group_a, group_b = select_groups(metadata, args.condition_column, args.reference, args.target)
    group_a_samples = [s for s in samples if metadata[s][args.condition_column] == group_a]
    group_b_samples = [s for s in samples if metadata[s][args.condition_column] == group_b]
    if not group_a_samples or not group_b_samples:
        raise SystemExit(f"contrast groups not found: {group_a} vs {group_b}")
    library_sizes = {sample: sum(row["counts"].get(sample, 0.0) for row in rows) for sample in samples}
    de_rows = compute_de(rows, samples, group_a_samples, group_b_samples, library_sizes)
    de_rows.sort(key=lambda row: (float(row["fdr"]), -abs(float(row["log2_fold_change"]))))
    sample_qc = [
        {
            "sample_id": sample,
            "group": metadata[sample][args.condition_column],
            "library_size": f"{library_sizes[sample]:.0f}",
            "detected_genes": sum(1 for row in rows if row["counts"].get(sample, 0.0) > 0),
        }
        for sample in samples
    ]

    de_path = out_dir / "tables" / "differential_expression_pilot.csv"
    sample_qc_path = out_dir / "qc" / "sample_qc.csv"
    volcano = out_dir / "figures" / "volcano_plot.svg"
    heatmap = out_dir / "figures" / "deg_heatmap.svg"
    write_csv(de_path, de_rows, ["gene", "mean_log_cpm_group_a", "mean_log_cpm_group_b", "log2_fold_change", "t_statistic", "p_value", "fdr"])
    write_csv(sample_qc_path, sample_qc, ["sample_id", "group", "library_size", "detected_genes"])
    render_volcano(volcano, de_rows)
    render_heatmap(heatmap, de_rows)
    write_source_maps(out_dir, de_path, sample_qc_path, volcano, heatmap)
    write_text(
        out_dir / "outputs_manifest.yaml",
        "schema_version: python_builtin_pilot_outputs.v1\n"
        f"run_id: {args.run_id}\n"
        "execution_mode: pilot\n"
        "outputs:\n"
        "  - path: tables/differential_expression_pilot.csv\n"
        "    status: generated\n"
        "  - path: qc/sample_qc.csv\n"
        "    status: generated\n"
        "  - path: figures/volcano_plot.svg\n"
        "    status: generated\n"
        "  - path: figures/deg_heatmap.svg\n"
        "    status: generated\n",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
