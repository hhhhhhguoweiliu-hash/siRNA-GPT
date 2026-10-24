"""Focused no-API development checks, preserving all previous question records."""
import base64,hashlib,json,sys,tempfile,unittest,time
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from literature import Library
from knowledge import search
from conversation import Conversation
from test_conversation import message_response
from test_http import request

OUT=ROOT/'research/2026-10-24_followup/offline'/('verification_02' if '--verification-02' in sys.argv else '')

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 if (OUT/'focused_checks.json').exists():raise SystemExit('Preserve existing run; choose a new output directory before repeating checks.')
 with tempfile.TemporaryDirectory(dir=ROOT/'.test_tmp') as td:
  library=Library(Path(td)/'library',ROOT/'references/sirna_library')
  with patch('literature.get_library',return_value=library):
   imports=[]
   manifest=json.loads((ROOT/'references/vegfa_experiments_20261024/sources.json').read_text(encoding='utf-8'))
   for source in manifest['sources']:
    raw=(ROOT/'references/vegfa_experiments_20261024'/source['file']).read_bytes()
    code,body=request('POST','/api/library-upload',{**source,'filename':source['file'],'content_base64':base64.b64encode(raw).decode()})
    result=json.loads(body);imports.append({'file':source['file'],'http_status':code,'result':result})
    if code!=200:raise RuntimeError(result)
   questions={'boundary':'为什么本项目不能根据TPM证明患者疗效？','scope':'请为这位患者制定临床给药方案','empty':'ZXQ987654321',
    'day7':'VEGFA_SD_3499在ARPE-19转染后第7天实测敲低率是多少？',
    'arpe_experiment':'ARPE-19细胞中VEGF siRNA转染实测沉默的实验条件和剂量是什么？',
    'different_readouts':'ARPE-19实验中VEGF mRNA和蛋白在什么时间检测，指标有什么不同？',
    'tlr3':'TLR3研究中序列无关的抗血管生成结果有哪些适用边界？'}
   records={key:search(q) for key,q in questions.items()}
   checks={'three_documents_imported':len(imports)==3,'boundary_search_executed':records['boundary']['retrieval_executed'],
    'baseline_card_retrieved':any(c['id']=='expression' for c in records['boundary']['cards']),
    'scope_stop_not_searched':records['scope']['status']=='OUT_OF_SCOPE' and not records['scope']['retrieval_executed'],
    'real_empty_search':records['empty']['status']=='NO_RESULTS' and records['empty']['retrieval_executed'],
    'day7_has_related_evidence':bool(records['day7']['excerpts']) and records['day7']['retrieval_executed'],
    'arpe_experimental_paper_retrieved':any(h.get('doi') in ['10.2147/IJN.S39622','10.3390/pharmaceutics12010039'] for h in records['arpe_experiment']['excerpts']),
    'readout_paper_retrieved':any(h.get('doi') in ['10.2147/IJN.S39622','10.3390/pharmaceutics12010039'] for h in records['different_readouts']['excerpts']),
    'tlr3_paper_retrieved':any(h.get('doi')=='10.1038/nature06765' for h in records['tlr3']['excerpts'])}
   calls=[]
   def mock(p):calls.append(p);return message_response('TEST_ONLY 没有该项目该时间点的实测记录 [S1]')
   c=Conversation(cfg_loader=lambda:{'model':'TEST_ONLY','api_key':'TEST_ONLY'},transport=mock,root=Path(td)/'mock')
   c.answer(questions['day7'],web_enabled=False,literature_only=True)
   checks['day7_not_programmatically_blocked']=len(calls)==1
   (OUT/'day7_transport_TEST_ONLY.json').write_text(json.dumps(c.export_record(),ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
   snapshot=library.export_bundle();(OUT/'expanded_library.zip').write_bytes(snapshot)
   restored=Library(Path(td)/'restored');restore=restored.import_bundle(snapshot);restored.db.unlink();restored.rebuild()
   checks['export_restore_rebuild']=restore['same_version'] and restored.version()==library.version()
   checks['twelve_documents']=len(library.catalogue()['documents'])==12
   old=json.loads((ROOT/'research/2026-10-23_literature/offline/verification_02/retrieval_records.json').read_text(encoding='utf-8'))
   changes={}
   for key,record in old.items():
    current=search(record['retrieval']['question']);changes[key]={'old_version':record['library_version'],'new_version':current['library_version'],
     'old_urls':[e['url'] for e in record['excerpts']],'new_urls':[e['url'] for e in current['excerpts']]}
   for name,value in [('focused_checks.json',{'checks':checks,'all_pass':all(checks.values()),'documents':library.catalogue(),
     'real_model_calls':False,'independent_scores':None,'actual_day7_demo':'PENDING_MANUAL_CONFIRMED_RUN'}),('retrieval_records.json',records),('http_imports.json',imports),('old_dev_question_retrieval_changes.json',changes)]:
    (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
   print(json.dumps({'checks':checks,'all_pass':all(checks.values()),'library_version':library.version()},ensure_ascii=False))
   if not all(checks.values()):raise SystemExit(1)

if __name__=='__main__':main()
