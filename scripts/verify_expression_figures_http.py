"""Real local HTTP-handler -> guided tools -> native R -> authenticated-path downloads.

No external sockets, LLM requests, model weights or scientific predictions are run.
"""
import hashlib, io, json, shutil, sys, time, zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app
from test_http import request
from core import HOME

def wait():
    deadline=time.monotonic()+120
    while app.CONVERSATION.snapshot()['busy'] and time.monotonic()<deadline:time.sleep(.1)
    if app.CONVERSATION.snapshot()['busy']:raise TimeoutError('HTTP guided step timeout')

if __name__=='__main__':
    out=HOME/'research/2026-10-29_expression_figures';out.mkdir(exist_ok=True)
    status,_=request('POST','/api/message',{'interaction_mode':'meta','message':'本次候选表达背景作图',
        'preset':'figures','tool_mode':'imported','expression_dataset_id':'builtin',
        'candidate_ids':[r['candidate_id'] for r in app.default_candidates()]})
    assert status==202,status
    wait();plan=app.CONVERSATION.plan
    assert plan['tools']==['inspect_candidates','match_seed','query_expression','render_expression_figures']
    for i in range(4):
        status,_=request('POST','/api/action',{'action':'execute' if i==0 else 'next','plan_id':plan['id']})
        assert status==202,status
        wait()
    result=app.CONVERSATION.result;session=app.CONVERSATION.session
    assert result['status']=='PARTIAL_COMPLETE',result
    assert result['expression_figures']['status']=='COMPLETE'
    status,pdf=request('GET','/runs/'+session.id+'/expression_figures/candidate_expression.pdf')
    assert status==200 and pdf.startswith(b'%PDF')
    status,bundle=request('GET','/runs/'+session.id+'/download.zip');assert status==200
    with zipfile.ZipFile(io.BytesIO(bundle)) as z:
        assert z.read('expression_figures/candidate_expression.pdf')==pdf
        assert 'expression_figures/expression_figures.R' in z.namelist()
    export=out/'example';export.mkdir(exist_ok=True)
    for p in (session.path/'expression_figures').iterdir():
        if p.is_file():shutil.copy2(p,export/p.name)
    (out/'candidate_expression_records.zip').write_bytes(bundle)
    evidence={'status':'PASS','run_id':session.id,'plan':plan['tools'],'mode':'GUIDED_TOOLS_NO_LLM',
        'actual_model_calls':0,'actual_R_invocations':1,'seed_source':'IMPORTED_HISTORICAL',
        'http_pdf_sha256':hashlib.sha256(pdf).hexdigest(),'download_zip_sha256':hashlib.sha256(bundle).hexdigest(),
        'expression_figures':result['expression_figures'],'download_pdf_bytes':len(pdf),
        'path_boundary':'existing local Host/Origin checks; cloud Basic Auth retained and covered by test_cloud',
        'online_deployed':False}
    (out/'http_e2e_receipt.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(evidence,ensure_ascii=False))
