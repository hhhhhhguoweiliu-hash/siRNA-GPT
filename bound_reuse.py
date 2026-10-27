"""Conservative in-process reuse of imported evidence within one conversation.

Unknown/live environments are deliberately not cached. No cross-arm reuse.
"""
import copy, hashlib, json, shutil
from pathlib import Path

REUSABLE=('inspect_candidates','verify_target','score_candidates')

def binding(session):
    if session.tool_mode!='imported':return None
    from core import DATA
    # Imported scientific outputs and versioned source manifests are small;
    # bind every asset, including references and weights fingerprints in manifests.
    assets={str(p.relative_to(DATA)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(Path(DATA).rglob('*')) if p.is_file()}
    task={k:v for k,v in session.task.items() if k not in ('request','evaluation_conditions','shared_user_input','own_history')}
    cfg={k:v for k,v in session.cfg.items() if k not in ('api_key','base_url','model','provider','max_model_turns','max_tool_calls','max_output_tokens')}
    payload={'candidates':session.candidates,'task':task,'tool_mode':session.tool_mode,'mode':session.mode,'parameters':cfg,
             'expression_source':session.expression_source,'expression_rows':session.expression_rows,
             'assets':assets,'implementation':{n:hashlib.sha256(Path(__file__).with_name(n).read_bytes()).hexdigest() for n in ('core.py','verified_imports.py','bound_reuse.py')}}
    return hashlib.sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False).encode()).hexdigest()

def remember(session):
    session.evidence_binding=binding(session)
    session.evidence_state_sha256=hashlib.sha256(json.dumps(session.state,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    session.evidence_artifacts={str(p.relative_to(session.path)):hashlib.sha256(p.read_bytes()).hexdigest() for p in session.path.rglob('*') if p.is_file() and (p.name in ('inspect_candidates.json','verify_target.json','score_candidates.json') or 'verified_import' in p.relative_to(session.path).parts)}

def reuse(session,previous):
    current=binding(session)
    state_digest=hashlib.sha256(json.dumps(previous.state,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    artifacts=getattr(previous,'evidence_artifacts',{})
    intact=all((previous.path/n).is_file() and hashlib.sha256((previous.path/n).read_bytes()).hexdigest()==digest for n,digest in artifacts.items())
    complete_artifacts=all(n+'.json' in artifacts for n in REUSABLE if n in previous.state)
    accepted=current is not None and current==getattr(previous,'evidence_binding',None) and state_digest==getattr(previous,'evidence_state_sha256',None) and intact and complete_artifacts
    names=[n for n in REUSABLE if accepted and n in session.planned_tools and n in previous.state]
    # Source artifacts, including nested verified-import files, must travel with
    # values. Reports and expression are always regenerated for the new request.
    allowed=('inspect_candidates.json','verify_target.json','score_candidates.json','verified_import','target_matches.tsv','target_verification.tsv')
    for name in allowed:
        src=previous.path/name
        if not names or not src.exists():continue
        dst=session.path/name
        if src.is_dir():shutil.copytree(src,dst,dirs_exist_ok=True)
        else:shutil.copy2(src,dst)
    for n in names:
        session.state[n]=copy.deepcopy(previous.state[n]);session.emit('tool_reused',n,status='REUSED_BOUND_PREVIOUS_ROUND',source_run_id=previous.id,binding=current)
    # Purchased imports are integrity-checked and retain their own source bundle.
    session.verified_imports=copy.deepcopy(previous.verified_imports) if names else {}
    result={'source_run_id':previous.id,'binding':current,'binding_equal':accepted,'reused_steps':names,
            'reason':'EXACT_INPUT_DATA_IMPLEMENTATION_BINDING' if accepted else 'CHANGED_OR_UNSUPPORTED_BINDING',
            'not_reused':['match_seed','query_expression','compile_report'],'new_tool_calls':0}
    from core import save_json
    save_json(session.path/'reuse_audit.json',result)
    return result
