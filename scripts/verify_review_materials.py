"""Read-only verification of original batch and review archives; never calls an API."""
import argparse,csv,gzip,hashlib,io,json,zipfile
from pathlib import Path

BASE=Path('research/2026-10-22_fairness')
def sha(raw):return hashlib.sha256(raw).hexdigest()
def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
def check(output):
    out=Path(output);out.mkdir(parents=True,exist_ok=True)
    previous=json.loads((BASE/'ARTIFACT_MANIFEST.json').read_text(encoding='utf-8'))
    original_files={name:sha((BASE/name).read_bytes())==meta['sha256'] for name,meta in previous.items()}
    assert all(original_files.values()),'An existing artifact changed'
    raw=(BASE/'three_arm/results.json.gz').read_bytes();rs=json.loads(gzip.decompress(raw))
    reviewed=json.loads(Path('docs/reviews/20261022_1501_full_batch_audit.json').read_text(encoding='utf-8'))
    assert sha(raw)==reviewed['raw_results_gz_sha256'] and len(rs)==54
    byid={r['answer_id']:r for r in rs};assert len(byid)==54
    with zipfile.ZipFile(BASE/'archives/dev_20261022_054717_79c2d3.zip') as full, \
         zipfile.ZipFile(BASE/'three_arm/for_review.zip') as original, \
         zipfile.ZipFile(BASE/'three_arm/for_review_complete.zip') as combined:
        assert full.testzip() is None and original.testzip() is None and combined.testzip() is None
        assert len(full.namelist())==815 and len(original.namelist())==170 and len(combined.namelist())==175
        assert json.loads(full.read('results.json'))==rs
        copies={n:{'sha256':sha(original.read(n)),
            'same_in_complete_bundle':original.read(n)==combined.read(n),
            'same_in_raw_archive':original.read(n)==full.read('for_review/'+n)} for n in original.namelist()}
        assert all(v['same_in_complete_bundle'] and v['same_in_raw_archive'] for v in copies.values())
        units=[];answers=[]
        for r in rs:
            aid=r['answer_id'];prefix='answers/'+aid+'/'
            answer=combined.read(prefix+'answer.txt');snap=combined.read(prefix+'input.json')
            evidence=json.loads(combined.read(prefix+'evidence.json'))
            assert answer.decode('utf-8')==r['answer']
            assert snap==full.read(aid+'/case_input.json')
            assert evidence['tool_results']==r.get('tool_results',{})
            units.append({'answer_id':aid,'case_id':r['case_id'],'answer_sha256':sha(answer),
                'input_sha256':sha(snap),'tool_evidence_matches':True,'answer_unchanged':True})
            answers.append({'answer_id':aid,'case_id':r['case_id'],'answer':r['answer']})
        blank=combined.read('blank_scores.tsv')
        rows=list(csv.DictReader(io.StringIO(blank.decode('utf-8-sig')),delimiter='\t'))
        assert len(rows)==54 and {x['answer_id'] for x in rows}==set(byid)
        score_fields=['reviewer_id','accuracy_0_2','evidence_0_2','task_fit_0_2','limits_0_2','unscorable_reason','notes']
        assert all(not row[k] for row in rows for k in score_fields)
        for n in combined.namelist():
            assert not any(x in n.lower() for x in ('private_key','config.local','.env','group_summary','technical_summary','records.tsv'))
        def keys(value):
            if isinstance(value,dict):
                assert not ({'group','repeat','private_key','api_key','authorization','password'} & set(value))
                for v in value.values():keys(v)
            elif isinstance(value,list):
                for v in value:keys(v)
        for n in original.namelist():
            if n.endswith('.json'):keys(json.loads(original.read(n)))
        addendum=json.loads(combined.read('reviewer_context_addendum.json'))
        for entry in addendum:
            assert entry['original_error']==byid[entry['answer_id']]['record']['result']
            assert entry['answer_unchanged'] and entry['human_score'] is None
        reference_checks={}
        with zipfile.ZipFile(io.BytesIO(combined.read('shared_scientific_references.zip'))) as ref:
            assert ref.testzip() is None and len(ref.namelist())==10
            reference_manifest=json.loads(ref.read('manifest.json'))
            for name,meta in reference_manifest.items():
                assert sha(ref.read(name))==meta['sha256']==reviewed['reference_hashes'][name]
                reference_checks[name]=meta['sha256']
        source={'answers':answers,'blank_rows':rows,'tasks':json.loads(combined.read('complete_tasks.json')),
            'rubric':json.loads(combined.read('rubric.json')),'resources':json.loads(combined.read('shared_resources.json')),
            'field_guide':json.loads(combined.read('field_guide.json'))}
        prep=Path('.test_tmp/review_forms');prep.mkdir(parents=True,exist_ok=True);write(prep/'source.json',source)
        (out/'blank_scores.tsv').write_bytes(blank)
    result={'reviewed_main':'c5fede854c6d9a6e2ed88cdb278a92f9262a1295',
        'source_run_id':reviewed['run_id'],'source_runtime_commit':reviewed['runtime_commit'],
        'original_results_sha256':sha(raw),'original_units':54,'original_files_unchanged':original_files,
        'archive_crc':{'raw_815_files':'PASS','original_review_170_files':'PASS','complete_review_175_files':'PASS'},
        'original_review_files':copies,'answer_checks':units,'scientific_reference_hashes':reference_checks,
        'blank_score_rows':54,'all_scoring_and_reviewer_fields_blank':True,'group_key_in_review_package':False,
        'original_error_addendum_matches':True,'model_or_tool_api_calls_in_this_task':0,
        'quality_scores_assigned':False,'scope':'File/input/evidence verification only, not scientific quality scoring.'}
    write(out/'review_package_verification.json',result);write(out/'original_answers_manifest.json',units)
    print(json.dumps({'original_units':54,'original_review_files_checked':len(copies),
        'existing_artifacts_unchanged':all(original_files.values()),'blank_fields':True,'api_calls':0}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();check(a.output)
