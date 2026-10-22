"""State, provenance and input regressions; no real external API calls."""
import json,tempfile,time,threading,unittest
from pathlib import Path
from unittest.mock import patch
from conversation import Conversation,PlannedSession,prepare_inputs
from core import config,save_json,TaskError
from test_conversation import message_response
from knowledge import search,catalogue
from test_http import request

class OptimizationTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.cfg=config();self.cfg['api_key']='TEST_SECRET'
 def tearDown(self):self.tmp.cleanup()
 def controller(self,transport=None):
  return Conversation(cfg_loader=lambda:self.cfg,transport=transport,root=self.root/'conversations',
   session_factory=lambda **kw:PlannedSession(run_root=self.root/'runs',**kw))
 def wait(self,c):
  deadline=time.monotonic()+10
  while c.snapshot()['busy'] and time.monotonic()<deadline:time.sleep(.01)
  self.assertFalse(c.snapshot()['busy'])
 def guided(self,c):
  c.submit({'interaction_mode':'meta','message':'核对','preset':'target','tool_mode':'imported'});self.wait(c)
  c.action('execute',c.plan['id']);self.wait(c)
 def test_atomic_write_failure_preserves_old_record(self):
  path=self.root/'record.json';save_json(path,{'value':1})
  with self.assertRaises(TypeError):save_json(path,{'value':object()})
  self.assertEqual(json.loads(path.read_text()),{'value':1});self.assertFalse(list(self.root.glob('*.tmp')))
 def test_notes_retrieval_is_versioned_and_explicitly_unreviewed(self):
  r=search('OligoFormer 模型分数等于敲低率吗')
  self.assertIn('score',[c['id'] for c in r['cards']]);self.assertIn('NOT_EXPERT_APPROVED',r['review_status'])
  self.assertTrue(catalogue()['sha256'])
 def test_notes_and_runtime_routes(self):
  code,body=request('GET','/knowledge');self.assertEqual(code,200);self.assertIn('待外部专家审核'.encode(),body)
  code,body=request('GET','/api/runtime');r=json.loads(body)
  self.assertEqual(code,200);self.assertIn('data/historical_scores.tsv',r['assets']);self.assertNotIn('api_key',r)
 def test_scientific_failure_can_retry_without_repeating_completed_tool(self):
  c=self.controller();self.guided(c);pid=c.plan['id'];s=c.session
  real=s.tool_verify_target
  with patch.object(s,'tool_verify_target',side_effect=TaskError('TEMPORARY_TEST_FAILURE')):
   c.action('next',pid);self.wait(c)
  self.assertEqual(c.phase,'failed');self.assertEqual(c.plan['id'],pid);self.assertIn('inspect_candidates',s.state)
  c.action('retry',pid);self.wait(c)
  self.assertEqual(c.result['status'],'PARTIAL_COMPLETE');self.assertIs(c.session,s)
  started=[e['message'] for e in s.events if e['kind']=='tool_started']
  self.assertEqual(started.count('inspect_candidates'),1);self.assertEqual(started.count('verify_target'),2)
 def test_stop_prevents_the_next_scientific_tool_then_allows_retry(self):
  started=threading.Event();release=threading.Event();blocked=[False]
  def fake(p):
   names=[t['function']['name'] for t in p.get('tools',[])]
   if names==['propose_plan']:return message_response(name='propose_plan',args={'decision':'ready','summary':'TEST','tools':['verify_target'],'question':''})
   if not blocked[0]:
    blocked[0]=True;started.set();release.wait(5)
   if names:return message_response(name=names[0])
   return message_response('TEST_ONLY completed')
  c=self.controller(fake);c.submit({'message':'核对转录本','tool_mode':'imported'});self.wait(c);pid=c.plan['id']
  c.action('execute',pid);self.assertTrue(started.wait(3));self.assertTrue(c.request_stop()['requested']);release.set();self.wait(c)
  self.assertEqual(c.phase,'paused');self.assertEqual(c.session.state,{})
  c.action('retry',pid);self.wait(c);self.assertEqual(c.result['status'],'PARTIAL_COMPLETE')
 def test_executor_only_exposes_dependency_ready_tools(self):
  s=PlannedSession(['verify_target'],cfg=self.cfg,run_root=self.root/'runs',tool_mode='imported');seen=[]
  def fake(p):
   names=[t['function']['name'] for t in p.get('tools',[])];seen.append(names)
   return message_response(name=names[0]) if names else message_response('TEST_ONLY summary')
  self.assertEqual(s.run_agent(fake)['status'],'PARTIAL_COMPLETE')
  self.assertEqual(seen,[['inspect_candidates'],['verify_target'],[]])
 def test_research_does_not_require_selected_candidates(self):
  def fake(p):
   if p.get('tools',[{}])[0].get('function',{}).get('name')=='propose_plan':
    return message_response(name='propose_plan',args={'decision':'research','summary':'TEST','tools':[],'question':''})
   return message_response('TEST_ONLY general explanation')
  c=self.controller(fake);c.submit({'message':'查文献','candidate_ids':[]});self.wait(c)
  self.assertEqual(c.messages[-1]['kind'],'qa');self.assertIsNone(c.plan)
 def test_guided_request_can_change_conditions_with_new_plan(self):
  def fake(p):return message_response(name='propose_plan',args={'decision':'ready','summary':'TEST new conditions','tools':['verify_target'],'question':'','task_updates':{'state':'Normoxia','top_n':3}})
  c=self.controller(fake);self.guided(c);old=c.session.id
  c.submit({'message':'改为常氧，重新核对','interaction_mode':'auto','tool_mode':'imported'});self.wait(c)
  self.assertEqual(c.plan['state'],'Normoxia');self.assertIsNone(c.session);self.assertEqual(c.previous_runs[-1]['run_id'],old)
 def test_source_ids_stay_stable_and_export_retains_raw_results(self):
  n=[0]
  def fake(p):
   n[0]+=1
   if n[0]%2:return message_response(name='search_pubmed',args={'query':'TEST'+str(n[0])})
   return message_response('TEST source [S1]' if n[0]==2 else 'TEST sources [S1] [S2]')
  c=self.controller(fake)
  with patch('conversation.research_tool',side_effect=[
   {'status':'OK','sources':[{'title':'TEST A','url':'https://pubmed.ncbi.nlm.nih.gov/1/'}],'articles':[{'abstract':'RAW_TEST_A'}]},
   {'status':'OK','sources':[{'title':'TEST B','url':'https://pubmed.ncbi.nlm.nih.gov/2/'}],'articles':[{'abstract':'RAW_TEST_B'}]}]):
   c.answer('TEST one');c.answer('TEST two')
  self.assertEqual(c.source_registry['https://pubmed.ncbi.nlm.nih.gov/1/']['id'],'S1')
  self.assertEqual({s['id'] for s in c.messages[-1]['sources']},{'S1','S2'})
  exported=c.export_record();self.assertEqual(len([r for r in exported['evidence_records'] if r.get('kind')!='model_exchange']),2)
  self.assertEqual(len([r for r in exported['evidence_records'] if r.get('kind')=='model_exchange']),4)
  encoded=json.dumps(exported);self.assertIn('RAW_TEST_A',encoded);self.assertIn('RAW_TEST_B',encoded);self.assertNotIn('TEST_SECRET',encoded)
 def test_continue_in_meta_mode_advances_current_plan(self):
  c=self.controller();self.guided(c);c.submit({'interaction_mode':'meta','message':'继续'});self.wait(c)
  self.assertEqual(c.result['status'],'PARTIAL_COMPLETE')
 def test_evaluation_workflow_runs_real_tools_without_a_model(self):
  from evaluate import run_case
  r=run_case('workflow',{'id':'test','request':'核对转录本','preset':'target'},self.cfg,self.root/'eval')
  self.assertEqual(r['status'],'PARTIAL_COMPLETE');self.assertEqual(r['tool_calls'],2);self.assertEqual(r['usage'],[])
  self.assertEqual(len(r['tool_results']['verify_target']['rows']),9)
 def test_evaluation_plain_llm_has_no_tools_or_scoring_outputs(self):
  from evaluate import run_case
  seen=[]
  r=run_case('llm',{'id':'test','request':'核对','preset':'target'},self.cfg,self.root/'eval',
   lambda p:(seen.append(p),message_response('TEST_ONLY no tools'))[1])
  self.assertNotIn('tools',seen[0]);self.assertEqual(r['tool_calls'],0)
  self.assertNotIn('TEST_SECRET',json.dumps(r))
 def test_stopping_qa_preserves_the_guided_task_phase(self):
  began=threading.Event();released=threading.Event()
  def fake(p):began.set();released.wait(3);return message_response('TEST_ONLY answer')
  c=self.controller(fake);self.guided(c);pid=c.plan['id']
  c.submit({'interaction_mode':'qa','message':'解释当前步骤'});self.assertTrue(began.wait(2))
  c.request_stop();released.set();self.wait(c)
  self.assertEqual(c.phase,'guided');self.assertEqual(c.plan['id'],pid)

if __name__=='__main__':unittest.main()
