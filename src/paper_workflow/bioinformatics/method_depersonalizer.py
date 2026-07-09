"""Depersonalization helpers for adapting reviewed literature code.

The goal is conservative: identify project-specific names and turn them into a
parameterization plan. This module does not rewrite third-party source in place.
"""

from __future__ import annotations

import re
from typing import Any


DEFAULT_PROJECT_TERMS = {
    "LUAD",
    "LUSC",
    "NSCLC",
    "Tumour",
    "Tumor",
    "tumour",
    "tumor",
    "BH",
    "Healthy",
    "Background",
}

WINDOWS_PATH_RE = re.compile(r"[A-Za-z]:[\\/][^\s'\"`]+")
TERM_RE = re.compile(r"\b[A-Za-z][A-Za-z0-9_.-]*\b")


def find_project_terms(text: str, extra_terms: list[str] | None = None) -> list[str]:
    """Return disease/project terms that should not enter reusable logic."""
    candidates = set(DEFAULT_PROJECT_TERMS)
    candidates.update(str(term) for term in (extra_terms or []) if str(term))
    found = []
    for term in sorted(candidates, key=str.lower):
        if re.search(rf"(?<![A-Za-z0-9_]){re.escape(term)}(?![A-Za-z0-9_])", text):
            found.append(term)
    found.extend(WINDOWS_PATH_RE.findall(text))
    return sorted(set(found), key=str.lower)


def find_object_terms(text: str) -> list[str]:
    """Find assignment/object names near method calls for human review."""
    names = set()
    for match in re.finditer(r"(?m)^\s*([A-Za-z.][A-Za-z0-9_.]*)\s*(?:<-|=)\s*", text):
        name = match.group(1)
        if name not in {"if", "for", "while", "function"}:
            names.add(name)
    for match in re.finditer(r"\b([A-Za-z.][A-Za-z0-9_.]*)\s*@", text):
        names.add(match.group(1))
    return sorted(names)


def parameterization_plan(
    *,
    method_family: str,
    hardcoded_terms: list[str],
    object_terms: list[str],
) -> dict[str, Any]:
    """Create a structured plan for removing source-project specificity."""
    family = method_family.lower()
    parameters = []
    if "findmarkers" in family or family == "cell_level_de":
        parameters = [
            "seurat_object or seurat_rds",
            "group_column",
            "ident_1",
            "ident_2",
            "subset_column",
            "subset_value",
            "assay",
            "slot",
            "test_use",
            "min_pct",
            "logfc_threshold",
            "only_pos",
        ]
    elif "limma" in family:
        parameters = [
            "count_matrix",
            "sample_metadata",
            "condition_column",
            "sample_id_column",
            "reference",
            "target",
            "model_formula",
        ]
    elif "differential_expression" in family:
        parameters = [
            "differential_expression_tables",
            "contrast_metadata",
            "gene_column",
            "logfc_column",
            "adjusted_p_value_column",
            "expression_percent_tables",
            "output_dir",
            "run_id",
        ]
    elif "percent_expression" in family:
        parameters = [
            "cell_metadata",
            "sample_metadata",
            "group_column",
            "sample_id_column",
            "cell_type_column",
            "percent_column",
            "statistical_test",
            "output_dir",
            "run_id",
        ]
    elif "enrichment" in family or "fgsea" in family:
        parameters = ["ranked_gene_table", "gene_sets", "gene_universe", "database_version", "fdr_threshold"]
    elif "plot" in family or "visual" in family:
        parameters = ["input_object", "feature_list", "group_column", "output_dir", "plot_theme"]
    else:
        parameters = ["input_object", "metadata", "output_dir", "run_id"]

    replacements = {term: "parameter_or_provenance_only" for term in hardcoded_terms}
    object_review = {term: "review_for_generalization" for term in object_terms[:30]}
    return {
        "required_parameters": parameters,
        "hardcoded_term_policy": replacements,
        "object_term_review": object_review,
        "generalization_rule": "Do not copy disease/project/sample labels into reusable function logic.",
        "review_required": True,
    }


def assert_no_project_terms(text: str, terms: list[str] | None = None) -> list[str]:
    """Return project terms found in reusable code text."""
    return find_project_terms(text, extra_terms=terms)
