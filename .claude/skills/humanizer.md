---
name: humanizer
version: "4.0.0"
description: Conservative manuscript humanization pass that reduces template tone, repetitive AI-style phrasing, and mechanical transitions while preserving scientific meaning.
owner_agent: aigc_humanizer_reviewer
paper_loop_stages: "15, 18, 20"
---

# Humanizer Skill

Use this skill after an AIGC text hygiene scan identifies passages that need a more natural scholarly voice.

## Principles

- Preserve factual claims, citations, numerical values, statistical tests, figure references, and method names.
- Improve prose rhythm, specificity, and authorial judgment.
- Replace generic boosters with concrete study-specific wording.
- Keep academic restraint: do not make the text more promotional.
- Record every substantive edit in the humanizer revision plan.

## Procedure

1. Read `review/aigc_detection_report.md` and prioritize high-signal sections.
2. Edit sentence-level transitions, repetitive framing, and vague evaluative words.
3. Break formulaic paragraphs into evidence-led argument flow when needed.
4. Leave technical statements unchanged unless the wording itself is the problem.
5. Write the revised manuscript to `manuscript/manuscript_humanized.md`.
6. Write `review/humanizer_revision_plan.yaml` with changed patterns, sections touched, and any manual review notes.

## Safe Replacement Patterns

- Replace "delve into" with "examine" only when the sentence remains accurate.
- Replace "complex and multifaceted" with the specific mechanism or uncertainty described by the data.
- Replace "plays a crucial role" with the measured association or demonstrated function.
- Remove overused contrast templates when a direct sentence is clearer.

## Stop Conditions

Stop and request human review if a passage requires new data interpretation, a changed statistical conclusion, or a modified claim-evidence relationship.
