"""Verify a complete exported diagnostic/batch. Never assigns scientific scores."""
import argparse,collections,csv,gzip,hashlib,io,json,sys,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from core import save_json
from evaluation_contract import input_sha256
from evaluation_protocol import settings_sha256

def user_input(request):
    for message in request.get('messages',request.get('input',[])):
        if message.get('role')!='user':continue
        content=message.get('content','')
        if isinstance(content,list):content=''.join(x.get('text','') for x in content)
        try:value=json.loads(content)
        except (ValueError,TypeError):continue
        if isinstance(value,dict) and isinstance(value.get('input'),dict):return value['input']

def response_fields(response):
    raw=response.get('_raw_response',response)
    return {'response_id':raw.get('id'),'request_id':response.get('_request_id'),
        'response_status':raw.get('status'),'incomplete_details':raw.get('incomplete_details'),
        'usage':raw.get('usage',response.get('usage',{}))}

def audit(archive,output):
    raw=Path(archive).read_bytes();out=Path(output)
    if out.exists() and any(out.iterdir()):raise ValueError('Use a new empty output directory')
    out.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        assert z.testzip() is None,'Archive CRC mismatch'
        read=lambda name:json.loads(z.read(name))
        p=read('protocol.json');cases=read('cases.json');results=read('results.json');completion=read('completion.json')
        schedule=p['scheduled_order'];key=lambda r:(r['case_id'],r['group'],r['repeat'])
        assert len(schedule)==p['planned_observations'] and len({key(x) for x in schedule})==len(schedule)
        assert [key(x) for x in results]==[key(x) for x in schedule[:len(results)]]
        assert len({x['answer_id'] for x in results})==len(results)
        assert completion['pending']==len(schedule)-len(results)
        assert completion['completed']==len(results) and completion['total']==len(schedule)
        assert completion['scientific_quality_scored'] is False
        if completion['status']=='COMPLETE':assert len(results)==len(schedule)
        assert settings_sha256(p['model_settings'])==p['model_settings_sha256']
        settings=p['model_settings'];snapshots={};checks=[];request_checks=[]
        for r in results:
            aid=r['answer_id'];assert read(aid+'/result.json')==r
            snap=read(aid+'/case_input.json');assert input_sha256(snap['input'])==snap['input_sha256']
            snapshots.setdefault(r['case_id'],[]).append(snap['input_sha256'])
            if r['group']=='llm':
                name=aid+'/actual_model_request.json' if aid+'/actual_model_request.json' in z.namelist() else aid+'/model_error_evidence.json'
                request=read(name);request=request.get('request',request)
                visible=user_input(request)
                response_name=aid+'/model_response.json' if aid+'/model_response.json' in z.namelist() else aid+'/model_error_response.json'
                response=read(response_name) if response_name in z.namelist() else {}
                request_checks.append({'answer_id':aid,'stage':'plain','actual_input_matches':visible==snap['input'],
                    'max_output_tokens':request.get('max_output_tokens',request.get('max_tokens')),
                    'thinking':request.get('thinking'),'model':request.get('model'),**response_fields(response)})
            if r['group']=='agent':
                exchanges=r.get('record',{}).get('evidence_records',[])
                first=next((e for e in exchanges if e.get('request') and user_input(e['request']) is not None),None)
                request=first['request'] if first else {}
                request_checks.append({'answer_id':aid,'stage':'planner','actual_input_matches':user_input(request)==snap['input'],
                    'max_output_tokens':request.get('max_output_tokens',request.get('max_tokens')),
                    'thinking':request.get('thinking'),'model':request.get('model'),**response_fields(first.get('response',{}) if first else {})})
            for name in z.namelist():
                if not name.startswith(aid+'/runs/') or not (name.endswith('_response.json') or name.endswith('_error.json')):continue
                saved=read(name);request=saved.get('_request',saved.get('request',{}))
                if request:
                    visible=user_input(request)
                    request_checks.append({'answer_id':aid,'stage':'executor',
                        'actual_candidates_match':visible is not None and visible.get('candidates')==snap['input']['candidates'],
                        'actual_task_matches':visible is not None and visible.get('task')==snap['input']['task'],
                        'max_output_tokens':request.get('max_output_tokens',request.get('max_tokens')),
                        'thinking':request.get('thinking'),'model':request.get('model'),**response_fields(saved)})
            tools=r.get('tool_results',{});states=tools.get('query_expression',{}).get('candidate_summary',[])
            byid={x['candidate_id']:x for x in states}
            count_checks={}
            for suffix,expected in [('3499',[778,728,726]),('3500',[1548,1333,1330]),('1157',[2197,1876,1874])]:
                row=byid.get('VEGFA_SD_'+suffix)
                if row:count_checks[suffix]=[row[k] for k in ('seed_site_count_all','matched_genes','baseline_mapped_genes')]==expected
            checks.append({'answer_id':aid,'case_id':r['case_id'],'status':r['status'],'completed_tools':r.get('completed_tools',[]),
                'count_field_consistency':count_checks,'semantic_score':None})
        assert all(len(set(v))==1 for v in snapshots.values()),'Raw case inputs differ across arms/repeats'
        assert all(x.get('actual_input_matches',True) for x in request_checks),'Actual model input mismatch'
        assert all(x.get('actual_candidates_match',True) and x.get('actual_task_matches',True) for x in request_checks),'Executor original candidates/task mismatch'
        assert all(x['max_output_tokens']==settings['max_output_tokens'] for x in request_checks),'Output cap mismatch'
        assert all(x['thinking']=={'type':settings['thinking']} for x in request_checks),'Thinking setting mismatch'
        assert all(x['model']==p['model'] for x in request_checks),'Model mismatch'
        assert all(all(x['count_field_consistency'].values()) for x in checks),'Tool count fields differ from reviewed anchors'
        for name in ['protocol.json','cases.json','completion.json','execution_status.tsv','private_key.tsv']:
            (out/name).write_bytes(z.read(name))
        review_files=[n for n in z.namelist() if n.startswith('for_review/')]
        assert review_files and not any('private_key' in n for n in review_files)
        rows=list(csv.DictReader(io.StringIO(z.read('for_review/blank_scores.tsv').decode('utf-8-sig')),delimiter='\t'))
        assert len(rows)==len(results)
        assert {row['answer_id'] for row in rows}=={r['answer_id'] for r in results}
        assert all(not row[k] for row in rows for k in ['reviewer_id','accuracy_0_2','evidence_0_2','task_fit_0_2','limits_0_2'])
        assert {x['case_id'] for x in read('for_review/complete_tasks.json')}=={x['id'] for x in cases['cases']}
        for r in results:
            prefix='for_review/answers/'+r['answer_id']+'/'
            assert z.read(prefix+'answer.txt').decode('utf-8')==r.get('answer',''),'Anonymous answer was changed'
            assert read(prefix+'input.json')==read(r['answer_id']+'/case_input.json'),'Review input mismatch'
            assert read(prefix+'evidence.json')['tool_results']==r.get('tool_results',{}),'Review tool evidence mismatch'
        with zipfile.ZipFile(out/'for_review.zip','w',zipfile.ZIP_DEFLATED) as target:
            for name in review_files:target.writestr(name.removeprefix('for_review/'),z.read(name))
    (out/'results.json.gz').write_bytes(gzip.compress(json.dumps(results,ensure_ascii=False).encode('utf-8'),mtime=0))
    summary={'mode':p.get('mode','batch'),'runtime':p['runtime'],'archive_bytes':len(raw),
        'archive_sha256':hashlib.sha256(raw).hexdigest(),'archive_crc':'PASS',
        'planned_units':len(schedule),'recorded_units':len(results),'completion':completion,
        'state_counts':dict(collections.Counter(r['group']+':'+r['status'] for r in results)),
        'input_hashes_by_case':{k:sorted(set(v)) for k,v in snapshots.items()},'same_raw_inputs':True,
        'actual_request_checks':request_checks,'tool_evidence_checks':checks,
        'review_materials_complete_for_recorded_units':True,'independent_scoring_done':False,
        'limitation':'Input/field/record checks are not scientific accuracy. All failures retained; no superiority conclusion.'}
    save_json(out/'audit.json',summary)
    print(json.dumps({k:v for k,v in summary.items() if k not in ('runtime','actual_request_checks','tool_evidence_checks','input_hashes_by_case')},ensure_ascii=False))
    return summary

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--archive',required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args();audit(args.archive,args.output)
