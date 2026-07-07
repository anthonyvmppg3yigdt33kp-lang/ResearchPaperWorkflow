# research-ppt-briefing

Use this skill for project progress summaries, group-meeting PPTs, journal
briefings, or slide-outline generation.

## Minimal Inputs

- `brief/PROJECT_BRIEF.yaml`
- `brief/STAGE_SUMMARY.md`
- `brief/SLIDE_BRIEF.md`
- `brief/FIGURE_STORYLINE.md`
- `results/current_run.yaml`
- `results/figure_source_map.yaml`

## Do Not

- Do not read raw matrices or rerun analysis.
- Do not use `PROJECT_PROGRESS.md` as the first source unless no brief exists.
- Do not infer completion from deck/report QA alone.

## Output

Return a slide-ready structure with:

- title;
- one-sentence project message;
- evidence slides;
- figure mapping;
- limitations;
- next decisions.
