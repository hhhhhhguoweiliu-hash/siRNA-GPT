"""Retain engineering failure-injection records. No real model or human grades."""
import copy
import hashlib
import json
import sys
import zipfile
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from evaluation_dialogue import run_dialogue
from model_client import ModelError
from test_evaluation_dialogue import test_stub
from test_conversation import message_response

BASE=ROOT/'research/2026-10-27_evaluation_fixes_v2'
TEMP=ROOT/'_test_runs/evaluation_boundary_v2'


def main():
    if TEMP.exists() and any(TEMP.iterdir()):raise ValueError('Use a fresh boundary-record directory')
    cases={c['id']:c for c in json.loads((BASE/'package/runtime/cases.json').read_text(encoding='utf-8'))['cases']}
    resources=json.loads((BASE/'package/runtime/resources.json').read_text(encoding='utf-8'))
    cfg={'model':'TEST_ONLY_NOT_PROVIDER','api_key':'TEST_SECRET_VALUE','max_tool_calls':18,'max_model_turns':12}
    summaries=[]
    for kind in ('ordinary_error','planner_error','executor_error','unchanged_update','conflicting_update',
                 'invalid_input','malformed_plan','partial_response','case_timeout','round_timeout'):
        group='llm' if kind in ('ordinary_error','invalid_input','partial_response','case_timeout','round_timeout') else 'agent'
        case=copy.deepcopy(cases['U1']);count=[0];clock=[0];settings=dict(cfg)
        if kind=='invalid_input':case['rounds'][0]['message']='X'*2001
        if kind=='case_timeout':settings.update(dialogue_case_timeout_seconds=1,dialogue_round_timeout_seconds=1)
        if kind=='round_timeout':settings.update(dialogue_case_timeout_seconds=10,dialogue_round_timeout_seconds=1)
        def transport(payload):
            count[0]+=1
            if kind in ('ordinary_error','planner_error'):raise RuntimeError('SYNTHETIC_FAILURE TEST_SECRET_VALUE')
            if kind=='executor_error' and count[0]>2:raise RuntimeError('SYNTHETIC_EXECUTOR_FAILURE')
            if kind=='malformed_plan':return {'choices':[]}
            if kind=='partial_response':
                e=ModelError('SYNTHETIC_PARTIAL','OUTPUT_TRUNCATED')
                e.response_snapshot={'status':'incomplete','output':'SYNTHETIC TEST_SECRET_VALUE'}
                raise e
            if kind in ('case_timeout','round_timeout'):
                clock[0]=2;return message_response('SYNTHETIC_TIMEOUT_RESPONSE')
            response=test_stub(payload)
            calls=response['choices'][0]['message'].get('tool_calls',[])
            if kind in ('unchanged_update','conflicting_update') and calls and calls[0]['function']['name']=='propose_plan':
                args=json.loads(calls[0]['function']['arguments'])
                args['task_updates']={'state':'Hypoxia' if kind=='unchanged_update' else 'Normoxia'}
                calls[0]['function']['arguments']=json.dumps(args)
            return response
        if kind in ('case_timeout','round_timeout'):
            with patch('evaluation_dialogue.time.monotonic',side_effect=lambda:clock[0]):
                result=run_dialogue(group,case,settings,TEMP/kind,transport,resources)
        else:result=run_dialogue(group,case,settings,TEMP/kind,transport,resources)
        if kind=='unchanged_update':assert result['pending_rounds']==0
        else:
            assert result['attempted_rounds']==1 and result['pending_rounds']==1
            assert result['rounds'][1]['status']=='NOT_EXECUTED'
            assert (TEMP/kind/'round_1/error.json').exists()
        assert (TEMP/kind/'result.json').exists() and (TEMP/kind/'round_2/turn_record.json').exists()
        assert 'TEST_SECRET_VALUE' not in (TEMP/kind/'result.json').read_text(encoding='utf-8')
        summaries.append({'scenario':kind,'kind':'ENGINEERING_TEST_ONLY_NOT_MODEL_PERFORMANCE',
            'attempted_rounds':result['attempted_rounds'],'pending_rounds':result['pending_rounds'],
            'first_status':result['rounds'][0]['status'],'failure_stage':(result['rounds'][0]['error_record'] or {}).get('stage'),
            'case_timeout_seconds':result['effective_settings']['case_timeout_seconds'],
            'round_timeout_seconds':result['effective_settings']['round_timeout_seconds'],
            'all_planned_rounds_have_records':True,'real_model_requests':0})
    path=BASE/'boundary_test_records.zip'
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as archive:
        for p in sorted(TEMP.rglob('*')):
            if p.is_file():archive.write(p,p.relative_to(TEMP))
    with zipfile.ZipFile(path) as archive:
        assert archive.testzip() is None
        entries=[{'path':p.filename,'bytes':p.file_size,'sha256':hashlib.sha256(archive.read(p)).hexdigest()} for p in archive.infolist()]
    (BASE/'boundary_acceptance.json').write_text(json.dumps({'kind':'FAILURE_INJECTION_TEST_NOT_SCIENTIFIC_RESULTS',
        'scenarios':summaries,'archive_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'files':entries,'crc':'PASS','real_model_requests':0},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('PASS: 10 explicit engineering scenarios retain inputs, errors, prior evidence and unexecuted rounds.')


if __name__=='__main__':main()
