from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from paper_workflow.bioinformatics.method_depersonalizer import (
    assert_no_project_terms,
    find_object_terms,
    find_project_terms,
    parameterization_plan,
)


def test_method_depersonalizer_flags_project_terms_and_plans_parameters():
    text = "DEA <- FindMarkers(obj, ident.1 = 'LUAD', ident.2 = 'LUSC')\nC:/Users/HP/Desktop/project"

    assert {"LUAD", "LUSC"}.issubset(set(find_project_terms(text)))
    assert "DEA" in find_object_terms(text)
    plan = parameterization_plan(
        method_family="seurat_findmarkers_de",
        hardcoded_terms=["LUAD", "LUSC"],
        object_terms=["DEA"],
    )

    assert "group_column" in plan["required_parameters"]
    assert plan["hardcoded_term_policy"]["LUAD"] == "parameter_or_provenance_only"
    assert assert_no_project_terms("group_column <- metadata[['condition']]") == []
