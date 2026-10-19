"""Meaningful input/failure/provenance/protocol checks. Stub API is NOT a real model run."""
import unittest,json,copy,uuid
from pathlib import Path
from core import Session,config,default_candidates,TOOLS,TaskError,read_tsv,DATA,canonical,HOME

class CoreTests(unittest.TestCase):
 def setUp(self):self.root=HOME/'_test_runs'/uuid.uuid4().hex;self.root.mkdir(parents=True);self.c=default_candidates()
 def session(self,**kwargs):return Session(run_root=self.root,tool_mode='imported',**kwargs)
 def test_complete_imported_case(self):
  s=self.session();r=s.run();self.assertEqual(r['status'],'COMPLETE')
  report=json.loads((s.path/'report.json').read_text(encoding='utf-8'))
  self.assertEqual(len(report['rows']),9);self.assertEqual(len(report['selected_for_review']),2)
  self.assertFalse(report['model_used']);self.assertTrue(all(not r['review_flags'] for r in report['rows'] if r['selected_for_review']))
  self.assertNotIn('VEGFA_SD_3535',report['selected_for_review'])
  self.assertTrue(next(r for r in report['rows'] if r['candidate_id']=='VEGFA_SD_3535')['review_flags'])
  self.assertEqual(s.state['score_candidates']['status'],'IMPORTED_HISTORICAL')
 def test_wrong_species_stops_before_scoring(self):
  s=self.session(task={'gene':'VEGFA','species':'Mus musculus','state':'Hypoxia','top_n':2});r=s.run()
  self.assertEqual(r['status'],'FAILED');self.assertNotIn('score_candidates',s.state)
 def test_missing_direction_does_not_truncate(self):
  c=copy.deepcopy(self.c[:1]);c[0]['guide_paired_core_19nt_5to3']='';c[0]['guide_21nt_RNA_5to3']='A'*21
  self.assertEqual(self.session(candidates=c).run()['status'],'FAILED')
 def test_duplicate_id(self):self.assertEqual(self.session(candidates=[self.c[0],self.c[0]]).run()['status'],'FAILED')
 def test_invalid_bases(self):
  c=copy.deepcopy(self.c[:1]);c[0]['guide_paired_core_19nt_5to3']='N'*19
  self.assertEqual(self.session(candidates=c).run()['status'],'FAILED')
 def test_empty_candidates(self):self.assertEqual(self.session(candidates=[]).run()['status'],'FAILED')
 def test_unmatched_target(self):
  c=[{'candidate_id':'new','guide_core19_5to3':'A'*19,'source':'test'}]
  s=self.session(candidates=c);s.call('inspect_candidates');self.assertEqual(s.call('verify_target')['status'],'ERROR')
 def test_changed_sequence_cannot_import(self):
  c=copy.deepcopy(self.c[:1]);c[0]['candidate_id']='renamed'
  s=self.session(candidates=c);s.call('inspect_candidates');s.call('verify_target')
  self.assertEqual(s.call('score_candidates')['status'],'ERROR');self.assertEqual(s.call('match_seed')['status'],'ERROR')
 def test_no_fake_success_after_missing_tool(self):
  s=self.session();self.assertEqual(s.call('compile_report')['status'],'ERROR');self.assertFalse((s.path/'report.html').exists())
 def test_missing_api_no_fallback(self):
  c=config();c.update(api_key='',base_url='',model='');s=self.session(mode='agent',cfg=c);r=s.run()
  self.assertEqual(r['status'],'FAILED');self.assertEqual(s.tool_calls,0)
 def test_unknown_tool_rejected(self):
  with self.assertRaises(TaskError):self.session().call('run_shell',{})
 def test_protocol_with_explicit_stub_transport(self):
  s=self.session(mode='agent');n=[0]
  def stub(payload):
   n[0]+=1
   if n[0]==1:
    return {'choices':[{'message':{'role':'assistant','content':None,'tool_calls':[{'id':'call_'+str(i),'type':'function','function':{'name':name,'arguments':'{}'}} for i,(name,_) in enumerate(TOOLS)]}}]}
   self.assertEqual(len([m for m in payload['messages'] if m['role']=='tool']),6)
   return {'choices':[{'message':{'role':'assistant','content':'STUB_PROTOCOL_TEST_ONLY'}}]}
  self.assertEqual(s.run_agent(transport=stub)['status'],'COMPLETE');self.assertEqual(n[0],2)
 def test_protocol_early_final_is_incomplete(self):
  s=self.session(mode='agent')
  r=s.run_agent(transport=lambda p:{'choices':[{'message':{'role':'assistant','content':'需要更多输入'}}]})
  self.assertEqual(r['status'],'INCOMPLETE_OR_CLARIFICATION');self.assertFalse((s.path/'report.html').exists())
 def test_normoxia_annotation_matches_selected_state(self):
  s=self.session(task={'gene':'VEGFA','species':'Homo sapiens','state':'Normoxia','top_n':2});self.assertEqual(s.run()['status'],'COMPLETE')
  self.assertTrue(all(r['state_detected_genes']==r['normoxia_detected_genes'] for r in s.state['query_expression']['candidate_summary']))

if __name__=='__main__':unittest.main(verbosity=2)
