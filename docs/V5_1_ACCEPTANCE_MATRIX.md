# v5.1 Acceptance Matrix

| Requirement | Acceptance evidence | Release rule |
|---|---|---|
| Natural language reaches TargetTask | Harness tests and equivalent CLI command | Must pass |
| Research question becomes an executable contract | `scientific_assessment.yaml`, `strategy_simulation.yaml`, `figure_plan.yaml`, `target_task.yaml` | Must all exist |
| Researcher sees current state | `RESEARCH_DASHBOARD.md` and dashboard YAML | Must show blockers and next actions |
| Method advice states why and limits | Method knowledge entries include solves, not-for, unit, prerequisites, risks, boundary | Must validate as YAML |
| FindMarkers remains exploratory | Strategy test returns `cell_level_de_exploratory` | Must pass |
| Pseudobulk is not silently substituted | Missing sample mapping creates deferred status | Must pass |
| TargetTask belongs to truth layer | `workflow_contract.yaml` stage bridge and strict contract check | Must pass |
| Subcluster output is scientifically checked | Marker, score, resolution, QC, figure, object, and session checks | Missing critical output must block |
| Resolution choice is not maximum-cluster chasing | Stable plateau policy plus recorded reason | R dry-run and parser checks must pass |
| Intent parameters reach executable code | Graph node parameters and R command record QC, anchor, test, and program values | Must match intent values |
| Real Seurat workflow is reproducible | `validation/pbmc3k_v5_1/validation_summary.yaml` and SHA-256 manifest | Real execution and all gates must pass |
| Runtime and output cost are visible | Per-run node timing, input/output sizes, and TSV ledger | Must exist for every graph run |
| Writing is evidence-bound | `research write` blocks without fail-closed pass | Must pass |
| Tutorial data are not disease evidence | PBMC3K claim boundary and forbidden claims | Must remain explicit |
| No production inflation | module grade audit | Must pass |
| No QA fail-open regression | supervision failure cases | Must pass |
| Local source is actually tested | import path points to current checkout or editable install | Must be recorded |
| GitHub publication is evidence-bound | PR CI, merge commit, tag, and release target align | Required before release |

## Current Capability Boundary

v5.1 can rapidly translate a structured scientific question into a reviewable plan and currently executable TargetTask. It does not guarantee that every recommended method is installed or production-grade. Deferred and planning-only methods remain visible with their blockers, and real analysis still requires explicit approval, data registration, environment validation, module gates, and fail-closed QA.

The accepted PBMC3K run is workflow-test evidence only: 2,638 input cells, 1,372 marker-and-anchor-selected cells, six exploratory subclusters, 2,962 marker rows, 24 program-summary rows, and all workflow/scientific/environment/source-map gates at pass. These metrics do not support disease or clinical inference.
