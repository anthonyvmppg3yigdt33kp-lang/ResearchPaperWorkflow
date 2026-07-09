#!/usr/bin/env python
"""Standardize an imported differential-expression table."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import median


CLAIM_BOUNDARY = (
    "Imported DE table post-processing only; upstream differential model, "
    "replicate unit, contrast design, and FDR provenance must be reviewed before biological claims."
)


GENE_COLUMNS = ["gene", "Gene", "symbol", "Symbol", "gene_symbol", "GeneSymbol", "id"]
LOGFC_COLUMNS = ["avg_log2FC", "log2FoldChange", "logFC", "avg_logFC", "LFC"]
PVALUE_COLUMNS = ["p_val", "pvalue", "P.Value", "PValue", "p"]
FDR_COLUMNS = ["p_val_adj", "padj", "adj.P.Val", "FDR", "qvalue"]


def first_present(row: dict[str, str], candidates: list[str]) -> str:
    for key in candidates:
        if key in row and str(row[key]).strip() != "":
            return key
    return ""


def parse_float(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def standardize_rows(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], dict[str, str]]:
    if not rows:
        return [], {}
    first = rows[0]
    mapping = {
        "gene": first_present(first, GENE_COLUMNS),
        "log2_fold_change": first_present(first, LOGFC_COLUMNS),
        "p_value": first_present(first, PVALUE_COLUMNS),
        "fdr": first_present(first, FDR_COLUMNS),
    }
    standardized = []
    for idx, row in enumerate(rows, start=1):
        gene = row.get(mapping["gene"], f"gene_{idx}") if mapping.get("gene") else f"gene_{idx}"
        logfc_value = parse_float(row.get(mapping["log2_fold_change"], "")) if mapping.get("log2_fold_change") else None
        p_value = parse_float(row.get(mapping["p_value"], "")) if mapping.get("p_value") else None
        fdr = parse_float(row.get(mapping["fdr"], "")) if mapping.get("fdr") else None
        standardized.append({
            "gene": str(gene),
            "log2_fold_change": "" if logfc_value is None else f"{logfc_value:.6g}",
            "p_value": "" if p_value is None else f"{p_value:.6g}",
            "fdr": "" if fdr is None else f"{fdr:.6g}",
            "rank_statistic": "" if logfc_value is None else f"{logfc_value:.6g}",
            "source_row": str(idx),
            "claim_boundary": CLAIM_BOUNDARY,
        })
    standardized.sort(key=lambda item: abs(parse_float(item["rank_statistic"]) or 0.0), reverse=True)
    return standardized, mapping


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def dry_run_rows() -> list[dict[str, str]]:
    return [
        {"gene": "GENE_A", "logFC": "1.5", "P.Value": "0.001", "adj.P.Val": "0.01"},
        {"gene": "GENE_B", "logFC": "-1.2", "P.Value": "0.02", "adj.P.Val": "0.08"},
        {"gene": "GENE_C", "logFC": "0.4", "P.Value": "0.2", "adj.P.Val": "0.5"},
    ]


def run(input_path: Path | None, out_dir: Path, run_id: str, dry_run: bool = False) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = dry_run_rows() if dry_run else read_csv(input_path or Path())
    standardized, mapping = standardize_rows(rows)
    fieldnames = ["gene", "log2_fold_change", "p_value", "fdr", "rank_statistic", "source_row", "claim_boundary"]
    write_csv(out_dir / "tables" / "standardized_de_table.csv", standardized, fieldnames)
    write_csv(out_dir / "tables" / "ranked_gene_statistic.csv", standardized, fieldnames)
    significant = [
        row for row in standardized
        if (parse_float(row["fdr"]) is not None and (parse_float(row["fdr"]) or 1.0) <= 0.05)
    ]
    write_csv(out_dir / "tables" / "significant_genes.csv", significant, fieldnames)
    write_csv(
        out_dir / "qc" / "input_column_mapping.csv",
        [{"standard_column": key, "source_column": value or "not_found"} for key, value in mapping.items()],
        ["standard_column", "source_column"],
    )
    logfc_values = [parse_float(row["log2_fold_change"]) for row in standardized if parse_float(row["log2_fold_change"]) is not None]
    qc = {
        "schema_version": "de_table_quality_summary.v1",
        "run_id": run_id,
        "status": "pass" if standardized and mapping.get("gene") and mapping.get("log2_fold_change") else "needs_fix",
        "input_rows": len(rows),
        "standardized_rows": len(standardized),
        "significant_rows_fdr_0_05": len(significant),
        "median_abs_log2_fold_change": median([abs(v) for v in logfc_values]) if logfc_values else None,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    write_text(out_dir / "qc" / "de_table_quality_summary.csv", "\n".join(f"{k},{v}" for k, v in qc.items()) + "\n")
    write_text(out_dir / "logs" / "sessionInfo.txt", "python stdlib csv post-processing; no upstream DE model executed\n")
    write_text(
        out_dir / "figure_source_map.yaml",
        "schema_version: external_de_table_standardizer_source_map.v1\nfigures: []\n",
    )
    write_text(
        out_dir / "table_source_map.yaml",
        "schema_version: external_de_table_standardizer_source_map.v1\n"
        "tables:\n"
        "  - table_id: standardized_de_table\n"
        "    path: tables/standardized_de_table.csv\n"
        "    source_inputs: imported_de_table\n"
        "    method: DE table column standardization and rank statistic extraction\n"
        "    statistical_unit: source_table_row\n"
        f"    claim_boundary: \"{CLAIM_BOUNDARY}\"\n"
        "  - table_id: ranked_gene_statistic\n"
        "    path: tables/ranked_gene_statistic.csv\n"
        "    source_inputs: tables/standardized_de_table.csv\n"
        "    method: sort by absolute standardized rank statistic\n"
        "    statistical_unit: gene\n"
        f"    claim_boundary: \"{CLAIM_BOUNDARY}\"\n",
    )
    manifest = {
        "schema_version": "external_de_table_standardizer_outputs.v1",
        "run_id": run_id,
        "status": qc["status"],
        "dry_run": dry_run,
        "claim_boundary": CLAIM_BOUNDARY,
        "outputs": [
            "tables/standardized_de_table.csv",
            "tables/ranked_gene_statistic.csv",
            "tables/significant_genes.csv",
            "qc/input_column_mapping.csv",
            "qc/de_table_quality_summary.csv",
            "logs/sessionInfo.txt",
            "figure_source_map.yaml",
            "table_source_map.yaml",
        ],
    }
    write_text(out_dir / "outputs_manifest.yaml", json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    write_text(
        out_dir / "node_manifest.yaml",
        json.dumps({"schema_version": "method_node_manifest.v1", "run_id": run_id, "module_id": "external.lung_master.de_table_standardizer.v1", "status": qc["status"], "dry_run": dry_run, "claim_boundary": CLAIM_BOUNDARY}, indent=2, ensure_ascii=False) + "\n",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input")
    parser.add_argument("--out", required=True)
    parser.add_argument("--run-id", default="external_de_table_standardizer")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not args.dry_run and not args.input:
        parser.error("--input is required unless --dry-run is used")
    run(Path(args.input) if args.input else None, Path(args.out), args.run_id, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
