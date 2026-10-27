#!/usr/bin/env python3
# Evaluator: ChatGPT | Review date: 2026-10-27 | Audit version: AUDIT_V3_2026-10-27
# Nature: AI-assisted pre-review only; not independent human adjudication.
# Source snapshot before this audit directory was added: ab54de166d77cf2c34ee7d9a5219e8ff3e6d834b
"""Reproduce AI-preliminary task accuracy and required-slot P/R/F1 from the committed CSVs.

Run from this directory:
    python metrics_calculation.py

Rules:
  CORRECT -> TP += 1
  WRONG   -> FP += 1 and FN += 1
  MISSING -> FN += 1
  UNJUDGED is not imputed as zero; if any remain, metrics are NOT_READY.
  NOT_APPLICABLE is excluded from the required-slot denominator.
This does not calculate strict CRISPR-GPT C1 planning metrics.
"""
import csv, json, statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent

def read_csv(name):
    with (HERE / name).open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def metrics(rows):
    st = [r["review_status"] for r in rows]
    c, w, m = st.count("CORRECT"), st.count("WRONG"), st.count("MISSING")
    u, na = st.count("UNJUDGED"), st.count("NOT_APPLICABLE")
    tp, fp, fn = c, w, w + m
    if u:
        return {"n":len(rows),"correct":c,"wrong":w,"missing":m,"unjudged":u,
                "not_applicable":na,"TP":tp,"FP":fp,"FN":fn,
                "precision":None,"recall":None,"f1":None,"status":"NOT_READY"}
    return {"n":len(rows),"correct":c,"wrong":w,"missing":m,"unjudged":u,
            "not_applicable":na,"TP":tp,"FP":fp,"FN":fn,
            "precision":tp/(tp+fp) if tp+fp else 0.0,
            "recall":tp/(tp+fn) if tp+fn else 0.0,
            "f1":2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0.0,
            "status":"AI_PRE_REVIEW_ONLY"}

def main():
    slots = read_csv("slot_reviews.csv")
    tasks = read_csv("task_reviews.csv")
    groups = {r["answer_id"]:r["group"] for r in read_csv("group_map.csv")}
    task_rows = []
    for t in tasks:
        rr = [s for s in slots if s["answer_id"] == t["answer_id"]]
        m = metrics(rr)
        task_rows.append({
            "answer_id":t["answer_id"],"case_id":t["case_id"],"category":t["category"],
            "group":groups[t["answer_id"]],"task_verdict":t["task_verdict"],
            "required_slots_n":m["n"],"correct_slots":m["correct"],"wrong_slots":m["wrong"],
            "missing_slots":m["missing"],"TP":m["TP"],"FP":m["FP"],"FN":m["FN"],
            "precision":m["precision"],"recall":m["recall"],"f1":m["f1"]
        })
    print("PER-TASK METRICS")
    print(json.dumps(task_rows, ensure_ascii=False, indent=2))
    summaries = []
    for group in ("llm","workflow","agent"):
        for cat in ("STANDARD_TASK","RELIABILITY","REQUIREMENT_CHANGE","OVERALL"):
            tr = [r for r in task_rows if r["group"] == group and (cat=="OVERALL" or r["category"]==cat)]
            answer_ids = {r["answer_id"] for r in tr}
            sr = [s for s in slots if s["answer_id"] in answer_ids]
            m = metrics(sr)
            passed = sum(r["task_verdict"]=="PASS" for r in tr)
            def macro(key):
                vals = [r[key] for r in tr if r[key] is not None]
                return statistics.mean(vals) if vals else None
            summaries.append({
                "group":group,"category":cat,"task_accuracy":f"{passed}/{len(tr)}",
                "slot_n":m["n"],"TP":m["TP"],"FP":m["FP"],"FN":m["FN"],
                "micro_precision":m["precision"],"micro_recall":m["recall"],"micro_f1":m["f1"],
                "macro_precision":macro("precision"),"macro_recall":macro("recall"),"macro_f1":macro("f1"),
                "status":"AI_PRE_REVIEW_ONLY"
            })
    print("GROUP/CATEGORY SUMMARY")
    print(json.dumps(summaries, ensure_ascii=False, indent=2))
    print("Planning C1 metrics: NOT_READY; see planning_metrics_status.json.")
    print("Human adjudication: pending; these are not ground-truth expert labels.")

if __name__ == "__main__":
    main()
