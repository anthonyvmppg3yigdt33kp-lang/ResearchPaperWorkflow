---
name: ai-writing-detection
version: "4.0.0"
description: Responsible AIGC text hygiene scan for manuscript drafts. Flags model-interface artifacts, formulaic structure, and high-density AI-style wording without making authorship accusations.
owner_agent: aigc_humanizer_reviewer
paper_loop_stages: "15, 16, 20"
---

# AI Writing Detection Skill

Use this skill during `aigc_humanizer_review`, `integrity_check`, and `finalize` to triage text hygiene risks before submission.

## Scope

- Detect definitive AI interface residue such as `turn0search`, `contentReference`, `oaicite`, `<grok_card>`, pasted prompt scaffolds, and tool logs.
- Detect high-signal AI-style phrasing when it clusters densely, including vague boosters, inflated symbolism, template transitions, and formulaic "not only...but also" structures.
- Detect formatting patterns that make manuscript prose look generated, such as excessive bolded mini-headings, repetitive three-part lists, and generic limitation paragraphs.
- Avoid claims that a passage "was written by AI." The output is a risk triage and cleanup plan.

## Procedure

1. Read the assembled manuscript or section draft.
2. Scan for definitive artifacts first. Any confirmed artifact is a HIGH gate issue.
3. Score style signals only by density and repetition. Isolated phrases are notes, not findings.
4. Check false positives: methods boilerplate, journal-required statements, translated academic prose, and standard reporting guideline language.
5. Produce `review/aigc_detection_report.md` with evidence, line/section context, severity, and a conservative recommendation.

## Output

The report must include:

- risk level: `low`, `medium`, or `high`
- artifact matches
- phrase and structure signals
- false-positive notes
- sections requiring human revision
- recommended humanizer actions

## Rules

- Preserve scientific claims, citations, numbers, statistical results, and method names.
- Never rewrite evidence while scanning.
- Prefer "AI-style signal" or "text hygiene risk" over accusatory wording.
