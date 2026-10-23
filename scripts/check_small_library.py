"""Run the ten predeclared development checks; no real model API calls."""
import base64
import hashlib
import io
import json
import sys
import tempfile
import time
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from literature import Library,canonical
from knowledge import search
from conversation import Conversation
from test_http import request
from test_literature import image_pdf
from test_conversation import message_response
from runtime_info import manifest

BASE=ROOT/'research/2026-10-23_literature'
OUT=BASE/'offline'/sys.argv[1] if len(sys.argv)>1 else BASE/'offline'
OUT.mkdir(parents=True,exist_ok=True)
if (OUT/'development_checks.json').exists():
    raise SystemExit('Existing check records are preserved. Supply a new output subdirectory.')
protocol_file=BASE/'development_protocol.json'
protocol=json.loads(protocol_file.read_text(encoding='utf-8'))
scratch=ROOT/'.test_tmp';scratch.mkdir(exist_ok=True)
temp=tempfile.TemporaryDirectory(dir=scratch)
work=Path(temp.name)
library=Library(work/'library')
declarations=json.loads((ROOT/'references/sirna_library/sources.json').read_text(encoding='utf-8'))
checks=[]
retrievals={}
inputs=[]


def record(identity,passed,detail):
    checks.append({'id':identity,'automated_check_passed':bool(passed),'detail':detail,
                   'human_scientific_quality_score':None})


with patch('literature.get_library',return_value=library):
    # Exercise the same HTTP import used by the UI, for every actual source.
    for source in declarations['sources']:
        raw=(ROOT/'references/sirna_library'/source['file']).read_bytes()
        body={**source,'filename':source['file'],'content_base64':base64.b64encode(raw).decode('ascii')}
        code,data=request('POST','/api/library-upload',body)
        response=json.loads(data)
        inputs.append({'file':source['file'],'sha256':hashlib.sha256(raw).hexdigest(),'http_status':code,'result':response})
        if code!=200:raise RuntimeError(response)
    for case in protocol['planned_cases'][:7]:
        retrievals[case['id']]=search(case['question'])
    b01=retrievals['B01']
    pdfs=[d for d in library.catalogue()['documents'] if d['filename'].endswith('.pdf')]
    record('B01',all(i['http_status']==200 for i in inputs) and bool(pdfs) and
           any('OligoFormer' in h['title'] and h['source_kind']!='project_record' for h in b01['retrieval']['hits']),
           {'sources_imported_through_http':len(inputs),'pdfs':pdfs,'english_source_retrieved':True,
            'note':'OligoFormer full text is extracted XML text, without invented PDF page numbers; siDirect original PDF supplies real page-level checks.'})
    b02=retrievals['B02']
    record('B02',any(h['source_kind']=='official_source_code' and '1.341' in h['text'] for h in b02['retrieval']['hits'])
           and any(c['id']=='score' for c in b02['cards']),
           {'source_kinds':[h['source_kind'] for h in b02['retrieval']['hits']],
            'boundary':'Retrieval of scaling and project explanation only; no automated correctness score for a generated answer.'})
    b03=retrievals['B03']
    record('B03',any(c['id']=='sequence' for c in b03['cards']) and any(h['source_kind']=='project_record' for h in b03['retrieval']['hits']),
           {'project_coordinate_record_retrieved':any(h['source_kind']=='project_record' for h in b03['retrieval']['hits']),
            'source_kinds':[h['source_kind'] for h in b03['retrieval']['hits']]})
    b04=retrievals['B04']
    record('B04',any(h['source_version']=='1.1.1' for h in b04['retrieval']['hits']),
           {'retrieved_historical_definition':[h['url'] for h in b04['retrieval']['hits'] if h['source_version']=='1.1.1']})
    b05=retrievals['B05']
    record('B05',any(c['id']=='seed' for c in b05['cards']) and any('SeedMatchR' in h['title'] for h in b05['retrieval']['hits']),
           {'project_seed_note_and_tool_source_retrieved':True,'not_measured_off_target_evidence':True})
    b06=retrievals['B06']
    record('B06',any(c['id']=='expression' for c in b06['cards']),
           {'project_expression_source':[c for c in b06['cards'] if c['id']=='expression'],'no_new_calculation':True})
    b07=retrievals['B07']
    record('B07',any(h['source_kind']=='project_record' for h in b07['retrieval']['hits']),
           {'project_record_sources':[h['url'] for h in b07['retrieval']['hits'] if h['source_kind']=='project_record']})
    # Actual controller abstention path, with a transport that must never run.
    attempts=[]
    def forbidden(p):attempts.append(p);raise RuntimeError('Unexpected model request in no-evidence development check')
    c=Conversation(cfg_loader=lambda:{'model':'NOT_CALLED','api_key':''},transport=forbidden,root=work/'no_evidence')
    c.answer(protocol['planned_cases'][7]['question'],web_enabled=False,literature_only=True)
    record('B08',not attempts and c.current_audit['status']=='no_evidence' and '证据不足' in c.messages[-1]['text'],
           {'actual_program_answer':c.messages[-1]['text'],'model_api_calls':0,'external_search':False})
    (OUT/'no_evidence_offline_record.json').write_bytes(canonical(c.export_record()))
    # Citation plumbing is exercised with an explicitly simulated transport;
    # this output is kept separately and never presented as a real model demo.
    captured=[]
    def simulated(p):
        captured.append(p)
        context=json.loads(p['messages'][-1]['content'])
        return message_response('TEST_ONLY citation transport ['+context['retrieved_excerpts'][0]['citation_id']+']')
    c=Conversation(cfg_loader=lambda:{'model':'TEST_ONLY_SIMULATED','api_key':''},transport=simulated,root=work/'citation_transport')
    c.answer(protocol['planned_cases'][1]['question'],web_enabled=False,literature_only=True)
    citations=c.current_audit
    (OUT/'citation_transport_TEST_ONLY.json').write_bytes(canonical(c.export_record()))
    # Verify every source URL opens a fragment containing precisely the stored text.
    source_checks=[]
    for value in retrievals.values():
        for h in value['retrieval']['hits']:
            doc,_,parts=library.document(h['document_id'])
            fragment=next(p for p in parts if p['chunk_id']==h['chunk_id'])
            source_checks.append(fragment['text']==h['text'] and fragment['sha256']==h['chunk_sha256'])
    fixtures=[('TEST_ONLY_corrupt.pdf',b'%PDF-1.4\nBROKEN_PDF_TEST_ONLY'),('TEST_ONLY_image_only.pdf',image_pdf())]
    rejections=[];version_before=library.version()
    for name,raw in fixtures:
        code,body=request('POST','/api/library-upload',{'filename':name,'content_base64':base64.b64encode(raw).decode(),
            'title':'TEST_ONLY invalid input','source_url':'https://example.org/test'})
        rejections.append({'filename':name,'http_status':code,'response':json.loads(body),
                           'input_sha256':hashlib.sha256(raw).hexdigest(),'input_base64_TEST_ONLY':base64.b64encode(raw).decode()})
    record('B09',all(r['http_status']==400 for r in rejections) and library.version()==version_before,
           {'rejected_inputs':rejections,'no_partial_import':library.version()==version_before})
    exported=library.export_bundle();(OUT/'library_export.zip').write_bytes(exported)
    restored=Library(work/'restored')
    restore=restored.import_bundle(exported)
    restored.db.unlink();restored.rebuild()
    q01=protocol['planned_cases'][0]['question']
    same_hits=restored.search(q01)==library.search(q01)
    same_pdf=True;pdf_parts=0
    for d in pdfs:
        old=library.document(d['id']);new=restored.document(d['id'])
        same_pdf=same_pdf and old[1].read_bytes()==new[1].read_bytes() and old[2]==new[2]
        pdf_parts+=len(old[2])
    record('B10',restore['same_version'] and same_hits and same_pdf and all(source_checks)
           and citations['citation_check']['has_citation'] and not citations['citation_check']['unknown_ids'],
           {'restored':restore,'same_B01_retrieval':same_hits,'same_all_pdf_originals_pages_fragments':same_pdf,
            'pdf_fragments_verified':pdf_parts,'all_retrieved_fragment_links_verified':all(source_checks),
            'citation_transport':'TEST_ONLY_SIMULATED_NOT_REAL_MODEL','rebuilt_index_after_database_removal':True})

result={'kind':'TEN_VISIBLE_DEVELOPMENT_CHECKS_NOT_INDEPENDENT_EVALUATION','time_utc':datetime.now(timezone.utc).isoformat(),
        'protocol_sha256':hashlib.sha256(protocol_file.read_bytes()).hexdigest(),'runtime':manifest(),
        'library_version':library.version(),'documents':library.catalogue()['documents'],
        'checks':checks,'all_automated_checks_passed':all(c['automated_check_passed'] for c in checks),
        'real_model_api_calls':False,'independent_scores':None,'old_54_modified':False}
(OUT/'development_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(OUT/'retrieval_records.json').write_text(json.dumps(retrievals,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(OUT/'import_records.json').write_text(json.dumps(inputs,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert work.resolve().is_relative_to(scratch.resolve())
temp.cleanup()
print(json.dumps({'checks':len(checks),'failed':[c['id'] for c in checks if not c['automated_check_passed']],
                  'documents':len(result['documents']),'real_model_api_calls':False}))
sys.exit(not result['all_automated_checks_passed'])
