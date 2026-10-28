#!/usr/bin/env python3
"""Regenerate the seven siRNA-GPT evaluation figures from repository CSV sources."""
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
RESEARCH = HERE.parent.parent
SLOT_PATH = RESEARCH / "2026-10-27_ai_simulated_review_audit_v3" / "slot_reviews.csv"
TASK_PATH = RESEARCH / "2026-10-27_ai_simulated_review_audit_v3" / "task_reviews.csv"
SCORE_A_PATH = RESEARCH / "2026-10-27_final_score_review" / "score_rows_by_actual_group.csv"
SCORE_C_PATH = RESEARCH / "2026-10-27_third_expert_review" / "score_rows_by_actual_group.csv"

plt.rcParams["font.family"] = "Arial"
plt.rcParams["font.weight"] = "bold"
plt.rcParams["axes.labelweight"] = "bold"
plt.rcParams["axes.titleweight"] = "bold"
plt.rcParams["figure.dpi"] = 150
plt.rcParams["savefig.dpi"] = 300

GROUPS = ["llm", "workflow", "agent"]
LABELS = {"llm": "Generic LLM", "workflow": "Fixed Workflow", "agent": "Agent"}
COLORS = {"llm": "#1f77b4", "workflow": "#ff7f0e", "agent": "#2ca02c"}
DIMS = ["factual_accuracy", "evidence_support", "requirement_completion", "boundary_handling"]
DIM_LABELS = ["Factual\nAccuracy", "Evidence\nSupport", "Requirement\nCompletion", "Boundary\nHandling"]
OVERRIDES = {"A013": "PASS", "A014": "PASS", "A002": "PASS", "A008": "FAIL"}

slots = pd.read_csv(SLOT_PATH, encoding="utf-8-sig")
tasks = pd.read_csv(TASK_PATH, encoding="utf-8-sig")
score_a = pd.read_csv(SCORE_A_PATH, encoding="utf-8-sig")
score_c = pd.read_csv(SCORE_C_PATH, encoding="utf-8-sig")
tasks["final_verdict"] = tasks.apply(lambda r: OVERRIDES.get(r["answer_id"], r["task_verdict"]), axis=1)

slot_counts = {}
metrics = {}
for g in GROUPS:
    s = slots[slots["group"] == g]["review_status"].value_counts().to_dict()
    c, w, m = s.get("CORRECT", 0), s.get("WRONG", 0), s.get("MISSING", 0)
    p = c / (c + w) if c + w else float("nan")
    r = c / (c + m) if c + m else float("nan")
    f1 = 2 * p * r / (p + r) if p + r else float("nan")
    slot_counts[g] = (c, w, m)
    metrics[g] = (p, r, f1)

def save(fig, name):
    fig.tight_layout()
    fig.savefig(HERE / name, bbox_inches="tight")
    plt.close(fig)

def dimension_plot(df, group_col, sheet, filename):
    means = df.groupby(group_col)[DIMS].mean().reindex(GROUPS)
    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(DIMS))
    width = 0.23
    for i, g in enumerate(GROUPS):
        ax.bar(x + (i - 1) * width, means.loc[g].values, width=width,
               label=LABELS[g], color=COLORS[g])
    ax.set_xticks(x)
    ax.set_xticklabels(DIM_LABELS, fontweight="bold")
    ax.set_ylim(0, 2.1)
    ax.set_ylabel("Mean score (0–2)", fontweight="bold")
    ax.set_title(f"Dimension-wise Mean Scores ({sheet})", fontweight="bold")
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=0.25)
    ax.set_axisbelow(True)
    save(fig, filename)

dimension_plot(score_a, "actual_group", "Score Sheet A", "Figure3_score_sheet_A_dimension_means.png")
dimension_plot(score_c, "group", "Score Sheet C", "Figure3_score_sheet_C_dimension_means.png")

def heatmap(df, group_col, sheet, filename):
    data = df[DIMS].astype(float).to_numpy()
    fig, ax = plt.subplots(figsize=(9, 11))
    im = ax.imshow(data, aspect="auto", vmin=0, vmax=2, cmap="Greys")
    ax.set_xticks(np.arange(4))
    ax.set_xticklabels(["Factual", "Evidence", "Requirement", "Boundary"], fontweight="bold")
    ax.set_yticks(np.arange(len(df)))
    ax.set_yticklabels([f'{r.answer_id} | {r.case_id} | {LABELS[getattr(r, group_col)]}' for r in df.itertuples()], fontsize=8, fontweight="bold")
    ax.set_xlabel("Evaluation dimension", fontweight="bold")
    ax.set_ylabel("Task episode", fontweight="bold")
    ax.set_title(f"Task-level Score Matrix ({sheet})", fontweight="bold")
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            ax.text(j, i, f"{int(data[i, j])}", ha="center", va="center",
                    fontweight="bold", color="white" if data[i, j] >= 1.7 else "black", fontsize=8)
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("Score", fontweight="bold")
    save(fig, filename)

heatmap(score_a, "actual_group", "Score Sheet A", "Figure4_task_dimension_heatmap_score_sheet_A.png")
heatmap(score_c, "group", "Score Sheet C", "FigureS1_task_dimension_heatmap_score_sheet_C.png")

changed_ids = ["A002", "A008", "A013", "A014"]
changed = tasks.set_index("answer_id").loc[changed_ids].reset_index()
fig, ax = plt.subplots(figsize=(7, 4.8))
mat = np.array([[1 if v == "PASS" else 0 for v in row] for row in changed[["task_verdict", "final_verdict"]].values])
from matplotlib.colors import ListedColormap
ax.imshow(mat, aspect="auto", cmap=ListedColormap(["#d62728", "#2ca02c"]), vmin=0, vmax=1)
ax.set_xticks([0, 1])
ax.set_xticklabels(["Before", "After"], fontweight="bold")
ax.set_yticks(np.arange(len(changed)))
ax.set_yticklabels([f'{r.answer_id} ({LABELS[r["group"]]})' for _, r in changed.iterrows()], fontweight="bold")
ax.set_title("Cases with Adjudication-driven Verdict Changes", fontweight="bold")
ax.set_xlabel("Verdict stage", fontweight="bold")
for i in range(len(changed)):
    for j, col in enumerate(["task_verdict", "final_verdict"]):
        ax.text(j, i, changed.iloc[i][col], ha="center", va="center",
                color="white", fontweight="bold")
save(fig, "FigureS2_changed_case_verdicts.png")

final_counts = tasks.groupby("group")["final_verdict"].value_counts().unstack(fill_value=0)
rates = [final_counts.loc[g].get("PASS", 0) / 9 for g in GROUPS]
fig, ax = plt.subplots(figsize=(7, 5))
bars = ax.bar([LABELS[g] for g in GROUPS], rates, color=[COLORS[g] for g in GROUPS])
ax.set_ylim(0, 1.08)
ax.set_ylabel("Task-level PASS rate", fontweight="bold")
ax.set_title("Task-level PASS Rate After Adjudication", fontweight="bold")
ax.grid(axis="y", alpha=0.25)
ax.set_axisbelow(True)
for bar, g, rate in zip(bars, GROUPS, rates):
    ax.text(bar.get_x() + bar.get_width()/2, rate + 0.025,
            f"{rate:.3f} ({int(final_counts.loc[g].get('PASS', 0))}/9)",
            ha="center", fontweight="bold")
save(fig, "FigureM1_accuracy.png")

fig, ax = plt.subplots(figsize=(8.5, 5.2))
x = np.arange(3)
width = 0.23
metric_names = ["Precision", "Recall", "F1 score"]
for i, g in enumerate(GROUPS):
    vals = metrics[g]
    ax.bar(x + (i - 1) * width, vals, width=width, label=LABELS[g], color=COLORS[g])
    for j, val in enumerate(vals):
        ax.text(x[j] + (i - 1) * width, val + 0.015, f"{val:.3f}",
                ha="center", va="bottom", fontsize=8, fontweight="bold", rotation=0)
ax.set_xticks(x)
ax.set_xticklabels(metric_names, fontweight="bold")
ax.set_ylim(0, 1.12)
ax.set_ylabel("Score", fontweight="bold")
ax.set_title("Slot-level Precision, Recall and F1", fontweight="bold")
ax.legend(frameon=False)
ax.grid(axis="y", alpha=0.25)
ax.set_axisbelow(True)
save(fig, "FigureM2_precision_recall_f1.png")

print("Generated seven PNG figures from the repository source CSVs.")
for g in GROUPS:
    c, w, m = slot_counts[g]
    p, r, f1 = metrics[g]
    print(f"{LABELS[g]}: CORRECT={c}, WRONG={w}, MISSING={m}; P={p:.3f}, R={r:.3f}, F1={f1:.3f}")
