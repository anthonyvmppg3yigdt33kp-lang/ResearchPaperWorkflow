# figure-storyline-planning

Use this skill when planning manuscript figures, figure order, panel logic, or
figure-to-claim mapping.

## Minimal Inputs

- `brief/PROJECT_BRIEF.yaml`
- `brief/FIGURE_STORYLINE.md` if present
- `results/current_run.yaml`
- `results/figure_plan.json`
- `results/figure_source_map.yaml` if present
- current manuscript section or figure legend when named

## Do Not

- Do not create or reorder figures without checking claim boundaries.
- Do not treat exploratory support panels as main claims.
- Do not read raw data by default.

## Output

Return a figure storyline with:

- figure purpose;
- panels;
- source files;
- claim strength;
- missing analyses;
- reviewer risk.
