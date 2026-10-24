"""Actual saved error, single-base and normal controls; no model API calls."""
import copy,json,tempfile,unittest
from pathlib import Path
from core import HOME,Session,save_json
from conversation import PlannedSession,Conversation
from sequence_validation import answer_evidence,verified_rows

SOURCE=HOME/'research/2026-10-24_nearfull_complete/live/tool_export'
def load(p):return json.loads(p.read_text(encoding='utf-8'))
class SequenceValidationTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir=HOME/'_test_runs');self.addCleanup(self.tmp.cleanup)
  self.inputs=load(SOURCE/'input.json')['candidates'];self.raw=load(SOURCE/'report.json')['model_summary']
  self.state={n:load(SOURCE/(n+'.json')) for n in ['inspect_candidates','verify_target','score_candidates','match_seed','query_expression','compile_report']}
 def check(self,text):return answer_evidence(text,self.inputs,self.state)
 def test_actual_24nt_error_is_blocked_and_raw_kept(self):
  v=self.check(self.raw);self.assertEqual(v['answer_validation']['status'],'FAIL')
  self.assertEqual(v['model_summary_raw'],self.raw);self.assertNotEqual(v['model_summary_display'],self.raw)
  self.assertTrue(any(x['length']==24 for x in v['answer_validation']['issues']))
 def test_single_base_19nt_error_is_not_accepted_by_length(self):
  text='passenger核心19nt：GAUAGAGCAAGACAAGAAC'
  v=self.check(text);self.assertEqual(v['answer_validation']['status'],'FAIL');self.assertEqual(v['answer_validation']['issues'][0]['length'],19)
 def test_correct_original_answer_control_not_false_blocked(self):
  text=self.raw.replace('GAUAGAGCAAGACAAGACAAGAAA','GAUAGAGCAAGACAAGAAA')
  v=self.check(text);self.assertEqual(v['answer_validation']['status'],'PASS');self.assertEqual(v['model_summary_display'],text)
 def test_swapped_roles_and_21nt_labeled_core_are_rejected(self):
  for text in ['passenger核心19nt：UUUCUUGUCUUGCUCUAUC','guide核心19nt：UUUCUUGUCUUGCUCUAUCTT']:
   with self.subTest(text=text):self.assertEqual(self.check(text)['answer_validation']['status'],'FAIL')
 def test_verified_table_keeps_TT_N3_and_conditional_roles(self):
  r=verified_rows(self.inputs,self.state)[0]
  self.assertEqual(r['passenger_core19_5to3'],'GAUAGAGCAAGACAAGAAA');self.assertTrue(r['guide_21nt_original'].endswith('TT'))
  self.assertIn('N3',r['original_row1']);self.assertIn('CONDITIONAL',r['strand_assignment_basis'])
 def test_no_checked_input_cannot_accept_claim(self):
  self.assertEqual(answer_evidence('guide：UUUCUUGUCUUGCUCUAUC',self.inputs,{})['answer_validation']['status'],'NOT_CHECKED_NO_VERIFIED_SEQUENCE')
 def test_no_sequence_claim_not_claimed_as_scientific_accuracy(self):
  r=self.check('模型分数不是敲低率。');self.assertEqual(r['answer_validation']['status'],'NO_SEQUENCE_CLAIMS');self.assertFalse(r['answer_validation']['is_scientific_accuracy_or_human_score'])
 def test_future_session_report_and_chat_share_one_check(self):
  s=PlannedSession(planned_tools=['compile_report'],candidates=self.inputs,tool_mode='imported',run_root=self.tmp.name,cfg={})
  s.state=copy.deepcopy(self.state)
  report=load(SOURCE/'report.json');save_json(s.path/'report.json',report)
  result=s.result_for_plan(self.raw,test_only=True);saved=load(s.path/'report.json')
  c=Conversation(root=Path(self.tmp.name)/'chat',cfg_loader=lambda:{});c.session=s;c.plan={'tools':s.planned_tools};c.finish(result)
  self.assertEqual(saved['answer_validation'],result['answer_validation']);self.assertEqual(c.messages[-1]['answer_validation'],result['answer_validation'])
  self.assertEqual(c.messages[-1]['text'],result['model_summary_display']);self.assertEqual(saved['model_summary_raw'],self.raw)
  html=(s.path/'report.html').read_text(encoding='utf-8');self.assertIn('data-sequence-status="FAIL"',html);self.assertIn('GAUAGAGCAAGACAAGAAA',html)
  self.assertEqual(result['status'],'COMPLETE');self.assertEqual(result['answer_sequence_status'],'FAILED')
if __name__=='__main__':unittest.main(verbosity=2)
