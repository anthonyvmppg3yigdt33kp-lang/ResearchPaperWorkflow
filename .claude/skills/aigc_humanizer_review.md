---
name: aigc_humanizer_review
description: Review manuscript text for AIGC writing artifacts, produce a responsible AI-writing signal report, and create a conservative humanizer revision pass. Triggers: AIGC review, AI writing detection, humanize manuscript, remove AI traces, AI痕迹检测, 去AI味.
version: "4.0.0"
paper_loop_stages: "15"
agent: aigc_humanizer_reviewer
type: skill
---

# AIGC Humanizer Review Skill

This skill combines `ai-writing-detection` and `humanizer` into a bounded
workflow stage. It is designed for manuscripts that were drafted or polished
with AI assistance and need a final responsible text-hygiene pass.

## Inputs

- `manuscript/manuscript_full.md`, or the available IMRAD files in `manuscript/`
- optional `references/library.bib`
- optional `claims_evidence_table.csv`

## Outputs

- `review/aigc_detection_report.md`
- `review/humanizer_revision_plan.yaml`
- `manuscript/manuscript_humanized.md`

## Procedure

1. Run artifact scan for AI interface residue:
   `turn0search`, `contentReference`, `oaicite`, `utm_source=chatgpt.com`,
   `utm_source=openai`, `<grok_card>`, `[attached_file:]`, `[web:]`, and
   copied assistant phrases.
2. Run style scan for clustered AIGC signals:
   inflated importance language, vague authority phrases, repeated tricolons,
   excessive bold-header lists, excessive em dashes, and AI-favored phrases
   such as "complex and multifaceted" or "intricate interplay".
3. Apply false-positive prevention:
   no high-confidence assessment under 200 words, no single-signal judgment,
   and lower weight for normal academic formality.
4. Generate a conservative humanizer plan:
   remove artifacts, simplify puffery, reduce formulaic structure, and preserve
   citations, numeric results, methods parameters, and figure references.
5. Write the humanized copy as a separate artifact. Never overwrite the source
   manuscript automatically.

## Pass Criteria

- No definitive AI interface artifacts remain.
- Style signal score is below the review threshold or explicitly documented.
- Humanizer report and humanized copy exist before `integrity_check`.

## Fail/Warning Criteria

- HIGH: interface artifacts remain in manuscript text.
- MEDIUM: style signal density exceeds threshold.
- MEDIUM: humanizer trace artifacts are missing.

## Responsible Language

The report must say "signals consistent with AI-assisted drafting" rather than
"this is AI-generated". AI detection is probabilistic and has known false
positive risks, especially for technical, academic, and non-native writing.
