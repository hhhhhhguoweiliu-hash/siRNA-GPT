# Checkpoint accuracy and decision metrics — retrospective revision

## What this analysis measures

This is a retrospective, AI-assisted **fact-and-boundary checkpoint decision**
evaluation of the same 27 delivered answers on nine seen development tasks.
It measures evidence reporting and appropriate rejection of unsupported claims
or prohibited actions. It does not measure biological efficacy, independent
scientific judgment, or performance on an unseen test set.

The source is the previously resolved 405 checkpoint outcomes, including the
user-relayed BCC adjudication. This is a documented recoding of that evidence,
not a new independent review or 405 new expert scores. The four-dimension
human rating workbook and the older task-level PASS labels are not numerical
inputs. All original answers, C/W/M labels, and known defects remain intact.

## Fixed evaluation universe and polarity

All **135 existing checkpoints** are retained for every system: **108 positive
checkpoints and 27 negative checkpoints**. No new test cases, guessed negative
examples, false alternative sequences, or extra TN rows were added.

`data/checkpoint_definitions.csv` gives the full proposition, gold polarity,
original requirement, reference value and evidence basis for every checkpoint.
The 27 negative propositions concern boundary claims or bounded prohibited
events already covered by the original requirements, e.g. treating a model
score as measured knockdown, reusing a score for a changed core, claiming a
vendor-confirmed duplex, or substituting an expression table contrary to the
task. Gold values follow the original task and fixed evidence, not the system's
answer or which system performs best.

Gold 1 means supported/required within the specified task and evidence;
gold 0 means unsupported or prohibited within that scope. In particular,
rejecting an unverified vendor/chemistry claim is not a new experimental
determination that the physical property is false in the real world.

Positive checkpoints retain the original fact, correct value, or complete
delivery requirement. An incompatible supplied value contradicts that positive
proposition. Composite checkpoints keep the pre-existing complete-tuple rule;
partly supplied content stays incomplete. Some checkpoints overlap, so 135
checkpoints are not 135 independent tasks or biological replicates.

This polarity scheme was specified retrospectively after the answers and their
previous review existed. It is **not preregistered**, and its positive/negative
composition affects P/R/F1. Do not present this recoding as a new benchmark or
as a universally preferred class definition.

## Predictions, abstention and TN

An explicit statement or delivered field can express support (`1`) or rejection
(`0`) of a proposition. The original correct/incorrect/insufficient outcomes
are retained as follows; the exact conversion is fully visible in
`data/judgments.csv`:

| Original complete-checkpoint outcome | Gold 1 | Gold 0 |
|---|---|---|
| CORRECT | 1 (TP) | 0 (TN) |
| WRONG | 0 (explicit FN) | 1 (FP) |
| MISSING / incomplete | ABSTAIN | ABSTAIN |

This is a recoding of an existing evidence audit, not a claim that the original
systems were asked to output literal 0/1 labels. Each prediction links to the
original evidence location, original review label, source row and quote hash.

For **semantic** negative propositions, merely failing to mention the issue
does not establish rejection. A previously missing/incomplete boundary
explanation remains ABSTAIN, including the BCC decisions for A002/A006's PASS
interpretation. Missing output is never converted to TN.

For **bounded-event** checkpoints, the observable object is the occurrence of a
specific forbidden action or emitted claim within a complete answer/run. The
entire answer, actual delivered sequence/attachment, or execution record can
establish that the event did not occur. For example, no placeholder date in a
fully available source statement and no new score/scan in a complete tool log
are observed non-events, not unanswered semantic questions. An empty or
unavailable answer/run is not sufficient evidence for TN. A010's follow-up
question did not execute a new score; A023's stopped candidate check was not a
new score/scan. A013's delivered attachments remain usable under scope A.

All 81 negative checkpoint/system combinations have a separate linked review
in `data/negative_evidence_review.csv`; 72 are TN. The original evidence is
immutable at the commit in `source_manifest.json`. Original input echoes remain
subject to the earlier BCC decision; they do not become independent biological
verification or cure a missing interpretation.

## Four headline metrics with missing output retained

The gold labels are binary, but actual output can be **1, 0, or ABSTAIN**.
We therefore publish a **2 × 3 confusion table**, not a fabricated complete
2 × 2 table. Define `A+` and `A−` as abstentions on positive and negative
checkpoints, and `FN_e` as explicit rejection of a true proposition:

| Gold | Support 1 | Reject 0 | ABSTAIN |
|---|---:|---:|---:|
| 1 | TP | FN_e | A+ |
| 0 | FP | TN | A− |

With N = TP + TN + FP + FN_e + A+ + A− = 135 per system:

- **Accuracy = (TP + TN) / N**. Every missing/incomplete item is counted as
  not correct; it is retained in N, never dropped or credited as TN.
- **Precision = TP / (TP + FP)** for the positive class.
- **Recall = TP / (TP + FN_e + A+)** for the positive class.
- **F1 = 2TP / (2TP + FP + FN_e + A+)** for the positive class.

With no abstentions, these reduce to the ordinary binary formulas. With
abstentions, ordinary positive-class FN is FN_e + A+. Overall classification
accuracy still counts exact label matches over all items. The implementation
encodes ABSTAIN as a third prediction label (-1), absent from the gold labels,
and verifies all four values independently with scikit-learn's `accuracy_score`
and `precision_recall_fscore_support(labels=[1])`. It does **not** recode
ABSTAIN as the negative class.

Missing negative items lower overall accuracy and negative-class recall; they
are not positive-class FP unless the system actually supports the false
proposition. This distinction matters and is visible in the 2 × 3 table.

Coverage is (N − A+ − A−) / N and is published alongside the metrics. Answered-
only accuracy is supplementary and explicitly labelled; it must not replace
the full-denominator headline accuracy. Micro values pool the 135 items. Macro
values average the nine task-specific metrics, including per-task F1, so tasks
with more checkpoints do not have extra weight in that view. Both are supplied.

## Relationship to previous figures

The new accuracy is checkpoint accuracy, not the previously plotted task PASS
rate (0/9, 8/9, 9/9). The old content-extraction P/R/F1 used C/(C+W),
C/(C+W+M), and 2C/(2C+2W+M); incorrect content contributed to both FP and FN
under that protocol. Those are a different construct and must not be mixed
with this decision confusion table. Old files remain historical; this directory
provides a complete, consistently recoded four-metric set.

The new accuracy numerically equals C/135 because a previously correct item is
now either TP or TN. That numerical identity follows from retaining the prior
correctness judgments; it is not an extra independent experimental result. The
new positive-class recall uses 108 positive checkpoints and is therefore a
different quantity from the former required-slot recall with denominator 135.

Known defects outside a particular checkpoint remain recorded in
`data/retained_extra_errors_and_scope_notes.json`. A high checkpoint score does
not establish that every sentence of an answer is correct. No significance
tests or confidence intervals treating the checkpoints as independent samples
are reported. New independent evaluation would require a prospectively frozen
question/label scheme and new held-out cases.

## Reproduction and primary method references

Run `python compute_and_verify.py` followed by
`python build_figures.py --font /path/to/Arial-Bold.ttf`.

- https://scikit-learn.org/stable/modules/generated/sklearn.metrics.accuracy_score.html
- https://scikit-learn.org/stable/modules/generated/sklearn.metrics.precision_recall_fscore_support.html
- https://scikit-learn.org/stable/modules/generated/sklearn.metrics.confusion_matrix.html

Method references support the metric definitions and library implementation;
they do not endorse this project's retrospective checkpoint construction.
