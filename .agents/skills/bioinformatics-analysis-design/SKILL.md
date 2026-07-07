# bioinformatics-analysis-design

Use this skill before running any bioinformatics analysis. Its purpose is to
convert a biological question into an approved statistical and visualization
plan.

## Minimal Inputs

- `brief/PROJECT_BRIEF.yaml`
- `data/data_inventory.yaml` or equivalent data inventory
- `results/current_run.yaml`
- `config/bioinformatics_method_contract.yaml`
- `config/visualization_contract.yaml`
- user-named scripts or prior manifests

## Required Design Fields

- research question and primary contrast;
- data type and statistical unit;
- covariates and batch/confounder handling;
- primary and secondary methods;
- expected figures and tables;
- validation and sensitivity plan;
- files to read and files to write;
- approval question for the user.

## Do Not

- Do not execute R/Python analysis before approval.
- Do not install packages or download databases in agent phase.
- Do not create a new result directory before a `run_id` is approved.

## Output

Return an analysis design memo plus an explicit `APPROVAL_REQUIRED` section.
