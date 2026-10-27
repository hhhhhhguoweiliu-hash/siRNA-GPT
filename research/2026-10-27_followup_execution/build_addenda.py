"""Additive evidence handoff: saved-answer replay, hashes, ties, no new ratings."""
import collections,csv,hashlib,json,subprocess,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from sequence_validation import answer_evidence
from evaluation_dialogue import effective_input
from delivery import present_delivery

HERE=Path(__file__).resolve().parent
def dump(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def read(path):
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write(path,rr):
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rr[0]));w.writeheader();w.writerows(rr)
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)

def main():
    records=json.loads((ROOT/'research/2026-10-27_real_dialogue_mini/raw/results_original.json').read_text('utf-8'))
    a13=next(x for x in records if x['answer_id']=='A013');q=a13['rounds'][0]
    inputs=effective_input(q['common_user_input']);raw=q['raw_model_answer']
    namespace={};exec(compile(git('show','33cd228:sequence_validation.py').decode('utf-8'),'sequence_validation_at_33cd228','exec'),namespace)
    before=namespace['answer_evidence'](raw,inputs['candidates'],q['tool_results'])
    after=answer_evidence(raw,inputs['candidates'],q['tool_results'])
    assert before['answer_validation']['status']=='FAIL' and after['answer_validation']['status']=='PASS'
    dump(HERE/'A013_before_after.json',dict(kind='OFFLINE_SAVED_RECORD_REPLAY_NOT_NEW_MODEL_ANSWER',source_commit='33cd2283a951ee71e8788c348ce8ea2e617b7ceb',
        original_answer_unchanged=True,raw_model_sha256=hashlib.sha256(raw.encode()).hexdigest(),before=before['answer_validation'],after=after['answer_validation'],new_model_calls=0))
    display=present_delivery(inputs,q['tool_results'],q['planned_tools'])
    (HERE/'A013_new_display_REPLAY_ONLY.txt').write_text('OFFLINE REPLAY ONLY; original A013 delivery remains unchanged.\n'+display['model_summary_display'],encoding='utf-8')
    write(HERE/'metrics/human_task_reviews_blank.csv',[dict(answer_id=r['answer_id'],case_id=r['case_id'],task_verdict='',invalidating_error_present='',prohibited_action_observed='',reason='',evidence_locator='',reviewer_id='',human_confirmed_at_utc='',adjudication_status='') for r in records])
    scored=read(ROOT/'research/2026-10-27_final_score_review/score_rows_by_actual_group.csv');cases=collections.defaultdict(list)
    for r in scored:cases[r['case_id']].append(r)
    ties=[]
    for case,rr in cases.items():
        best=max(int(r['sum8_audit_only']) for r in rr)
        winners=[r for r in rr if int(r['sum8_audit_only'])==best]
        ties.append(dict(case_id=case,max_sum8_audit_only=best,winner_answer_ids=';'.join(r['answer_id'] for r in winners),winner_groups=';'.join(r['actual_group'] for r in winners),tie=len(winners)>1,source='unchanged original score CSV; arithmetic display only'))
    write(HERE/'tie_display_derived.csv',ties)
    # Verify all original raw files against the source commit, not just counts.
    protected='research/2026-10-27_real_dialogue_mini/raw'
    entries=git('ls-tree','-r','4244ac0',protected).decode('utf-8').splitlines();checked=[]
    for line in entries:
        meta,path=line.split('\t',1);blob=meta.split()[2];b=(ROOT/path).read_bytes()
        actual=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
        assert actual==blob,path
        checked.append(dict(path=path,git_blob_sha=blob,sha256=hashlib.sha256(b).hexdigest(),bytes=len(b)))
    dump(HERE/'original_integrity.json',dict(source_commit='4244ac0d9b9f0b1e01fe46f6871fd664825a4c24',n_answers=len(records),n_rounds=sum(len(r['rounds']) for r in records),raw_files=checked,
        all_original_raw_blobs_unchanged=True,new_model_calls=0,new_human_ratings=0))
    history=git('log','--reverse','--date=iso-strict','--format=%H %aI %s','--name-status','4244ac0..HEAD').decode('utf-8')
    (HERE/'remote_history_in_commit_order.txt').write_text(history,encoding='utf-8')
    # A concurrent review corrected stale derived summaries while implementation
    # was in progress. Validate its actual labels against our earlier inputs.
    old=ROOT/'research/2026-10-27_ai_simulated_review';new=ROOT/'research/2026-10-27_ai_simulated_review_audit_v2'
    same={n:(old/n).read_bytes()==(new/n).read_bytes() for n in ('required_slots.csv','slot_reviews.csv','task_reviews.csv','group_map.csv')}
    # Different transport/newline serialization is permissible only with identical parsed cells.
    parsed={n:read(old/n)==read(new/n) for n in same}
    assert all(parsed.values()),parsed
    dump(HERE/'concurrent_review_checks.json',dict(concurrent_commit='ab54de166d77cf2c34ee7d9a5219e8ff3e6d834b',same_bytes=same,same_parsed_labels=parsed,
        action='fast-forward incorporated concurrent audit; did not overwrite it or old review directory',latest_summary_consistent=True))
    source=Path('C:/Users/86182/.codex/.chatgpt-projects/g-p-6a82e08661e081919f3434650ae4f35c/analysis/ARPE19_agent_v2_20261018/deliverable/04_tools/VEGFA_candidates_cpu.tsv')
    packaged=ROOT/'data/historical_scores.tsv'
    assert source.read_bytes()==packaged.read_bytes()
    with source.open(encoding='utf-8-sig',newline='') as f:official={r['candidate_id']:r for r in csv.DictReader(f,delimiter='\t')}
    pilot=ROOT/'research/2026-10-24_candidate_v2/oligo_pilot_02/result.json'
    purchased=next(r for r in json.loads(pilot.read_text('utf-8'))['rows'] if r['candidate_id']=='USER_PURCHASED_siVEGF')
    seen={}
    for record in records:
        for q in record['rounds']:
            for r in q['tool_results'].get('score_candidates',{}).get('rows',[]):
                cid=r['candidate_id'];expected=purchased if cid=='USER_PURCHASED_siVEGF' else official[cid]
                checks={key:str(r[key])==str(expected[key]) for key in ('guide_core19_5to3','mRNA_context_57nt')}
                checks.update({key:float(r[key])==float(expected[key]) for key in ('raw_class1','oligoformer_scaled_score')})
                assert all(checks.values()),(cid,checks)
                seen[cid]=dict(candidate_id=cid,checks=checks,raw_class1=float(r['raw_class1']),scaled=float(r['oligoformer_scaled_score']))
    observed_ids=sorted(seen)
    with (ROOT/'data/candidates.tsv').open(encoding='utf-8-sig',newline='') as f:default_candidates=list(csv.DictReader(f,delimiter='\t'))
    for candidate in default_candidates:
        cid=candidate['candidate_id'];r=official[cid]
        assert candidate['guide_paired_core_19nt_5to3']==r['guide_core19_5to3']
        if cid not in seen:seen[cid]=dict(candidate_id=cid,checks={'source_table_bytes_identical':True,'input_core_identical':True},raw_class1=float(r['raw_class1']),scaled=float(r['oligoformer_scaled_score']))
    assert len(seen)==10
    dump(HERE/'official_score_source_checks.json',dict(kind='ORIGINAL_OFFICIAL_OUTPUT_BINDING_ONLY_NOT_NEW_PREDICTION',source_files=[dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in (source,packaged,pilot)],rows=list(seen.values()),scored_candidate_ids_observed_in_old_batch=observed_ids,new_inference_runs=0))
    print(json.dumps(dict(A013_before='FAIL',A013_after='PASS',original_raw_files=len(checked),concurrent_labels_identical=all(parsed.values()),tie_cases=[r['case_id'] for r in ties if r['tie']]),ensure_ascii=True))

if __name__=='__main__':main()
