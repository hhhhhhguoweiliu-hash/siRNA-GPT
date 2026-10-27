#!/usr/bin/env python3
"""Reproduce AI-preliminary task accuracy and required-slot P/R/F1 from the CSV files.

Run from this directory:
    python metrics_calculation.py

This script does not calculate strict CRISPR-GPT C1 planning metrics.
"""
import csv
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent

def read_csv(name):
    with (HERE / name).open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def ratio(a, b):
    return (a / b) if b else 0.0

def slot_metrics(rows):
    statuses = [r["review_status"] for r in rows]
    correct = statuses.count("CORRECT")
    wrong = statuses.count("WRONG")
    missing = statuses.count("MISSING")
    unjudged = statuses.count("UNJUDGED")
    na = statuses.count("NOT_APPLICABLE")
    tp = correct
    fp = wrong
    fn = wrong + missing
    if unjudged:
        return {"n":len(rows),"correct":correct,"wrong":wrong,"missing":missing,
                "unjudged":unjudged,"not_applicable":na,"TP":tp,"FP":fp,"FN":fn,
                "precision":"","recall":"","f1":"","ready":"NOT_READY"}
    return {"n":len(rows),"correct":correct,"wrong":wrong,"missing":missing,
            "unjudged":unjudged,"not_applicable":na,"TP":tp,"FP":fp,"FN":fn,
            "precision":ratio(tp,tp+fp),"recall":ratio(tp,tp+fn),
            "f1":ratio(2*tp,2*tp+fp+fn),"ready":"AI_PRE_REVIEW_ONLY"}

def main():
    slots = read_csv("slot_reviews.csv")
    tasks = read_csv("task_reviews.csv")
    group_map = {r["answer_id"]:r["group"] for r in read_csv("group_map.csv")}
    task_rows = []
    for t in tasks:
        rr = [s for s in slots if s["answer_id"] == t["answer_id"]]
        m = slot_metrics(rr)
        task_rows.append({
            "answer_id":t["answer_id"],"case_id":t["case_id"],"category":t["category"],
            "group":group_map[t["answer_id"]],"task_verdict":t["task_verdict"],
            "task_pass_indicator":1 if t["task_verdict"]=="PASS" else 0,
            "required_slots_n":m["n"],"correct_slots":m["correct"],"wrong_slots":m["wrong"],
            "missing_slots":m["missing"],"TP":m["TP"],"FP":m["FP"],"FN":m["FN"],
            "precision":m["precision"],"recall":m["recall"],"f1":m["f1"],
            "metric_status":m["ready"]
        })
    print("Per-task rows (case x group):", len(task_rows))
    for group in ("llm","workflow","agent"):
        tr = [r for r in task_rows if r["group"]==group]
        sr = [s for s in slots if s["answer_id"] in {r["answer_id"] for r in tr}]
        m = slot_metrics(sr)
        pass_n = sum(r["task_pass_indicator"] for r in tr)
        macro_p = statistics.mean([float(r["precision"]) for r in tr if r["precision"]!=""])
        macro_r = statistics.mean([float(r["recall"]) for r in tr if r["recall"]!=""])
        macro_f = statistics.mean([float(r["f1"]) for r in tr if r["f1"]!=""])
        print(group, {
            "task_accuracy": f"{pass_n}/{len(tr)}",
            "required_slots":m["n"],"TP":m["TP"],"FP":m["FP"],"FN":m["FN"],
            "micro_precision":m["precision"],"micro_recall":m["recall"],"micro_f1":m["f1"],
            "macro_precision":macro_p,"macro_recall":macro_r,"macro_f1":macro_f
        })
    print("All values are AI-preliminary. Human adjudication is still pending.")
    print("Strict C1 planning metrics remain NOT_READY.")

if __name__ == "__main__":
    main()
