# Figure legends

**Figure 1. Accuracy, precision, recall and F1 on the existing development
checkpoints.** Metrics were recalculated from a retrospective polarity recoding
of 135 pre-existing checkpoints per system (108 positive and 27 negative),
using the previously resolved AI-assisted review plus user-relayed BCC
adjudication. Accuracy includes all checkpoints and counts abstentions or
incomplete answers as incorrect. Precision, recall and F1 describe the positive
class, with positive abstentions included among false negatives. Values are
micro-aggregated across nine seen tasks; they are not task PASS rates,
independent expert scores, biological efficacy or unseen-test performance.
Colors were sampled from CRISPR-GPT Figure 3. All text uses verified Arial Bold.

**Figure 2. Correct positive and negative judgments, explicit errors and
abstentions.** Panel a separates correct, explicit incorrect and
missing/incomplete outcomes over all 135 checkpoints. Panel b shows TP and TN
within the correct outcomes; labels give the total TN count. No missing answer
is counted as TN. The 27 negative checkpoints already existed among the 135
requirements; no extra negatives were added.

**Figure 3. Confusion tables retaining abstentions.** Rows indicate binary gold
polarity and columns indicate supported, rejected or absent/incomplete response.
Abstention is a separate prediction outcome. There are 108 positive and 27
negative checkpoints per system. Numbers are item counts; overlapping items
within a task are not independent experimental replicates.

**Supplementary Figure 1. Task-averaged accuracy, precision, recall and F1.**
Each metric is computed separately for each of the nine tasks and then averaged
without weighting by the task's checkpoint count. F1 is the mean of task F1
values, not the harmonic mean of average precision and recall. The same
retrospective protocol, prior review labels, abstention rules and scientific
limitations apply as in Figure 1.
