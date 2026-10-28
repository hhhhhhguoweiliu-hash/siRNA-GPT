# siRNA-GPT evaluation figures

## Contents

- `Figure3_score_sheet_A_dimension_means.svg`: four-dimension means from score sheet A.
- `Figure3_score_sheet_C_dimension_means.svg`: four-dimension means from score sheet C; kept separate from A.
- `Figure4_task_dimension_heatmap_score_sheet_A.svg`: 27 task episodes by four dimensions, score sheet A.
- `FigureS1_task_dimension_heatmap_score_sheet_C.svg`: 27 task episodes by four dimensions, score sheet C.
- `FigureS2_changed_case_verdicts.svg`: the four task labels changed by the adjudication overlay.
- `FigureM1_accuracy.svg`: task-level PASS rate after adjudication. The plot deliberately labels the quantity as PASS rate, not conventional classification accuracy.
- `FigureM2_precision_recall_f1.svg`: slot-level precision, recall and F1 calculated from the 405 required-slot review records.
- `figure_data.csv`: the plotted means and derived metrics, with counts and formulas.
- `generate_figures.py`: a reproducible Matplotlib script that reads the original CSVs in sibling research folders and writes PNG versions to this folder.

## Metric definitions

Task-level PASS rate is the number of task episodes adjudicated PASS divided by nine tasks in each group. This is an operational pass rate, not conventional classification accuracy against a separate labelled prediction set.

For slot-level metrics, `C` is the number of `CORRECT` required slots, `W` the number of `WRONG` slots, and `M` the number of `MISSING` slots:

- Precision = C / (C + W)
- Recall = C / (C + M)
- F1 = 2 × Precision × Recall / (Precision + Recall)

Counts from the source records:

| Group | Correct | Wrong | Missing | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| Generic LLM | 55 | 12 | 68 | 0.821 | 0.447 | 0.579 |
| Fixed Workflow | 130 | 0 | 5 | 1.000 | 0.963 | 0.981 |
| Agent | 128 | 1 | 6 | 0.992 | 0.955 | 0.973 |

## Font and rendering

All SVG master figures declare `font-family: Arial, Arimo, sans-serif` and `font-weight: 700` (bold). A system with Arial installed will use Arial; the current rendering environment resolves Arial to Arimo, a metric-compatible substitute. The Matplotlib script requests Arial Bold; on Windows with Arial installed it should render with Arial.

## Scope and interpretation

The score sheets are descriptive reviews of the same 27 task episodes and are intentionally not averaged together. The slot-level metrics measure completeness/correctness against the current required-slot rubric; they are not biological efficacy metrics. Task-level PASS rate is based on the final adjudication overlay. The four changed task labels are A002, A008, A013 and A014; the other 23 labels are unchanged.

## Source provenance

All source records below are read-only inputs; this figure directory does not replace them.

- Task review table: `research/2026-10-27_ai_simulated_review_audit_v3/task_reviews.csv` (blob SHA `936f8ae4cf65c363ffb2e417abb65daf76ddc34e`)
- Slot review table: `research/2026-10-27_ai_simulated_review_audit_v3/slot_reviews.csv` (blob SHA `4f2fd1b16d88a4922a6ed426ac65d3cf3d96e080`)
- Score sheet A: `research/2026-10-27_final_score_review/score_rows_by_actual_group.csv` (blob SHA `d8013c609a4479a66943678881d7b0fba1ff63e4`)
- Score sheet C: `research/2026-10-27_third_expert_review/score_rows_by_actual_group.csv` (blob SHA `dc9a0cbf4089295e3446deb08eab8bed60aee510`)

These figures were derived from the records present on the isolated adjudication branch. No source answer, original slot label, or historical score sheet was edited by this figure-generation commit.


## PDF export

After running `python generate_figures.py`, run `python build_pdf.py` to create a seven-page PDF under `dist/`. The PDF preserves each figure's aspect ratio. The plotting script uses Arial Bold when available; otherwise it prefers Arimo Bold as an Arial-compatible substitute.
