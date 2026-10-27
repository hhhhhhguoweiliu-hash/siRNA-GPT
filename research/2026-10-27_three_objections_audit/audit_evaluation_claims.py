"""Read-only audit of original evaluation records. No API calls or quality ratings."""
import argparse, collections, csv, hashlib, json
from pathlib import Path
from zipfile import ZipFile

EXPECTED_RAW_SHA256 = "f443d6f358a3c63f45eeef0906ae968f74f231534eb3c5276207767a14c2b9a3"
def sha(data): return hashlib.sha256(data).hexdigest()
def differences(a,b,path=""):
    if type(a) is not type(b): return [{"path":path,"a":a,"b":b}]
    if isinstance(a,dict):
        return [v for k in sorted(set(a)|set(b)) for v in differences(a.get(k),b.get(k),path+"/"+k)]
    if isinstance(a,list):
        if len(a)!=len(b): return [{"path":path+"/length","a":len(a),"b":len(b)}]
        return [v for i,(x,y) in enumerate(zip(a,b)) for v in differences(x,y,path+"/"+str(i))]
    return [] if a==b else [{"path":path,"a":a,"b":b}]

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--results",type=Path,required=True)
    p.add_argument("--reviewer-zip",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    raw=args.results.read_bytes()
    assert sha(raw)==EXPECTED_RAW_SHA256, "Unexpected raw results; preserve version binding"
    records=json.loads(raw);by={x["answer_id"]:x for x in records}
    assert len(records)==27 and len(by)==27
    rows=[]
    for x in records:
        for q in x["rounds"]:
            model=q.get("raw_model_answer")
            rows.append({"answer_id":x["answer_id"],"case_id":x["case_id"],"group":x["group"],
                "round":q["round"],"answer_source":q["answer_source"],
                "delivered_utf8_bytes":len(q["answer"].encode("utf-8")),
                "raw_model_is_null":model is None,"raw_model_utf8_bytes":len((model or "").encode("utf-8")),
                "raw_equals_delivered":model==q["answer"],"real_model_requests":q.get("real_model_requests"),
                "completed_tools":";".join(q.get("completed_tools",[]))})
    assert len(rows)==33
    zipbytes=args.reviewer_zip.read_bytes()
    with ZipFile(args.reviewer_zip) as z:
        names={}
        for aid in ["A011","A013","A025"]:
            for fn in ["answer.txt","raw_model_answer.txt"]:
                name="answers/"+aid+"/"+fn;b=z.read(name)
                names[name]={"bytes":len(b),"sha256":sha(b)}
        p11=json.loads(z.read("answers/A011/process.json"))
        p25=json.loads(z.read("answers/A025/process.json"))
        same=z.read("answers/A011/answer.txt")==z.read("answers/A025/answer.txt")
        changes=differences(p11,p25)
    a13=by["A013"];q13=a13["rounds"][0];expected=q13["tool_results"]["score_candidates"]["rows"][0]["oligoformer_scaled_score"]
    result={"reviewed_branch_head":"c30473d3168ccf5ce6522722f0cea857c2065037",
        "run_id":"mini_real_20261027_061408",
        "runtime_source_commit":"6c13c5788405e8ecf1aaf77144accd8108701d48",
        "raw_results_commit":"4244ac0d9b9f0b1e01fe46f6871fd664825a4c24",
        "raw_results_sha256":sha(raw),"original_reviewer_zip_sha256":sha(zipbytes),
        "n_original_answers":len(records),"n_user_rounds":len(rows),
        "R4":{"answer_files_byte_identical":same,"exported_files":names,
            "export_process_differences":changes,
            "actual_model_requests":{"A011":by["A011"].get("real_model_requests"),"A025":by["A025"].get("real_model_requests")},
            "actual_answer_sources":{k:by[k]["rounds"][0]["answer_source"] for k in ["A011","A025"]}},
        "A013":{"actual_delivered_body":a13["answer"],"tool_record_scaled_value":expected,
            "body_contains_scaled_value":str(expected) in a13["answer"],
            "raw_model_contains_scaled_value":str(expected) in (q13.get("raw_model_answer") or ""),
            "source":q13["answer_source"],"score_changes_by_assistant":None},
        "round_source_counts_by_group":{g:dict(collections.Counter(x["answer_source"] for x in rows if x["group"]==g)) for g in ["llm","workflow","agent"]},
        "agent_rounds":{"n":sum(x["group"]=="agent" for x in rows),
            "raw_text_equal_to_delivered":sum(x["group"]=="agent" and x["raw_equals_delivered"] for x in rows),
            "raw_text_differs_from_delivered":sum(x["group"]=="agent" and not x["raw_equals_delivered"] for x in rows)},
        "new_quality_ratings":0,"new_model_calls":0,"originals_modified":False,
        "scope":"Deterministic provenance and equality audit, not independent scientific or human scoring"}
    assert same and names["answers/A011/answer.txt"]["bytes"]==1900
    assert changes==[{"path":"/rounds/0/error_record/stage","a":"fixed_tools","b":"executor"}]
    assert not result["A013"]["body_contains_scaled_value"] and result["A013"]["raw_model_contains_scaled_value"]
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/"audit.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    with (args.output/"answer_origin_by_round.csv").open("w",encoding="utf-8-sig",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    print(json.dumps({"checks":"PASS","answers":len(records),"rounds":len(rows),"R4_export_identical":same,
        "R4_export_bytes":1900,"R4_Agent_real_model_requests":by["A025"].get("real_model_requests"),
        "agent_raw_equal_to_delivered":result["agent_rounds"]["raw_text_equal_to_delivered"],
        "new_quality_ratings":0},ensure_ascii=True))
if __name__=="__main__":main()
