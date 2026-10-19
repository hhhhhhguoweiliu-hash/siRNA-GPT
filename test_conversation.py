"""Explicit fake model tests plus real local tool calls; no real API success implied."""
import json, tempfile, time, unittest
from pathlib import Path
from conversation import Conversation, PlannedSession, expand_plan, propose, prepare_inputs
from core import default_candidates, config, TaskError

def message_response(content=None, name=None, args=None):
    m = {'role': 'assistant', 'content': content}
    if name: m['tool_calls'] = [{'id': 'test_call', 'type': 'function', 'function': {'name': name, 'arguments': json.dumps(args or {})}}]
    return {'choices': [{'finish_reason': 'stop', 'message': m}], 'usage': {'total_tokens': 3}}

class ConversationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name)
        self.cfg = config(); self.cfg['api_key'] = 'TEST_ONLY_SECRET'
    def tearDown(self): self.tmp.cleanup()
    def controller(self, transport=None):
        def factory(**kwargs): return PlannedSession(run_root=self.root/'runs', **kwargs)
        return Conversation(cfg_loader=lambda: self.cfg, root=self.root/'conversations', transport=transport, session_factory=factory)
    def wait(self, c):
        deadline = time.monotonic()+15
        while c.snapshot()['busy'] and time.monotonic()<deadline: time.sleep(.01)
        self.assertFalse(c.snapshot()['busy'])
    def test_dependency_expansion_minimal(self):
        self.assertEqual(expand_plan(['verify_target']), ['inspect_candidates', 'verify_target'])
        self.assertEqual(expand_plan(['query_expression']), ['inspect_candidates', 'match_seed', 'query_expression'])
        self.assertEqual(len(expand_plan(['compile_report'])), 6)
    def test_unknown_tool_refused(self):
        with self.assertRaises(ValueError): expand_plan(['shell'])
    def test_empty_candidates_refused(self):
        with self.assertRaises(ValueError): prepare_inputs({'candidate_ids': []})
    def test_planner_structure_and_clarification(self):
        args={'decision':'clarify','summary':'需求缺少目标','tools':[],'question':'要核对还是评分？'}
        plan,usage=propose('做一下',prepare_inputs({}),[],self.cfg,lambda _:message_response(name='propose_plan',args=args))
        self.assertEqual(plan['decision'],'clarify');self.assertEqual(plan['tools'],[])
    def test_planner_does_not_turn_plain_text_into_plan(self):
        with self.assertRaises(TaskError): propose('核对',prepare_inputs({}),[],self.cfg,lambda _:message_response('已经完成'))
    def test_natural_language_conditions_are_frozen_in_plan(self):
        args={'decision':'ready','summary':'常氧下核查3条','tools':['compile_report'],'question':'','task_updates':{'state':'Normoxia','top_n':3}}
        c=self.controller(lambda _:message_response(name='propose_plan',args=args))
        c.submit({'message':'常氧，给我3条','interaction_mode':'auto'});self.wait(c)
        self.assertEqual(c.plan['state'],'Normoxia');self.assertEqual(c.plan['top_n'],3)
        self.assertEqual(c.private['task']['state'],'Normoxia')
    def test_unsupported_gene_cannot_be_replaced_silently(self):
        args={'decision':'ready','summary':'test','tools':['verify_target'],'question':'','task_updates':{'gene':'KRAS'}}
        with self.assertRaises(TaskError):propose('KRAS',prepare_inputs({}),[],self.cfg,lambda _:message_response(name='propose_plan',args=args))
    def test_guided_pauses_and_executes_real_target_tools(self):
        c=self.controller();c.submit({'interaction_mode':'meta','message':'核对序列','preset':'target'});self.wait(c)
        pid=c.plan['id'];self.assertIsNone(c.session)
        c.action('execute',pid);self.wait(c)
        self.assertEqual(c.phase,'guided');self.assertEqual(list(c.session.state),['inspect_candidates'])
        c.action('next',pid);self.wait(c)
        self.assertEqual(c.result['status'],'PARTIAL_COMPLETE');self.assertEqual(len(c.session.state['verify_target']['rows']),9)
        self.assertFalse((c.session.path/'report.json').exists())
        with self.assertRaises(TaskError):c.action('next',pid)
    def test_old_plan_not_replayable(self):
        c=self.controller();c.submit({'interaction_mode':'meta','message':'核对','preset':'target'});self.wait(c);pid=c.plan['id']
        c.action('cancel',pid)
        with self.assertRaises(TaskError):c.action('execute',pid)
    def test_bad_guide_stops_before_target(self):
        c=self.controller();c.submit({'interaction_mode':'meta','message':'核对','preset':'target','candidate_text':json.dumps([{'candidate_id':'bad','guide_core19_5to3':'AAA','source':'test'}])});self.wait(c)
        c.action('execute',c.plan['id']);self.wait(c)
        self.assertEqual(c.result['status'],'FAILED');self.assertNotIn('verify_target',c.session.state)
    def test_qa_failure_keeps_pending_plan(self):
        def fail(_):raise TaskError('TEST_MODEL_FAILURE')
        c=self.controller(fail);c.submit({'interaction_mode':'meta','message':'核对','preset':'target'});self.wait(c);pid=c.plan['id']
        c.submit({'interaction_mode':'qa','message':'解释一下'});self.wait(c)
        self.assertEqual(c.plan['id'],pid);self.assertEqual(c.phase,'awaiting_execution')
    def test_auto_partial_plan_real_tools_fake_model(self):
        seen=[]
        def fake(p):
            seen.append(p)
            if p.get('tools') and p['tools'][0]['function']['name']=='propose_plan':
                return message_response(name='propose_plan',args={'decision':'ready','summary':'仅核对','tools':['verify_target'],'question':''})
            tool_messages=[m for m in p['messages'] if m['role']=='tool']
            if len(tool_messages)<2:return message_response(name=['inspect_candidates','verify_target'][len(tool_messages)])
            return message_response('TEST_ONLY：两项真实本地核对已完成，没有评分。')
        c=self.controller(fake);c.submit({'interaction_mode':'auto','message':'只核对序列'});self.wait(c)
        self.assertEqual(c.plan['tools'],['inspect_candidates','verify_target'])
        c.action('execute',c.plan['id']);self.wait(c)
        self.assertEqual(c.result['status'],'PARTIAL_COMPLETE');self.assertEqual(len(seen),4)
        self.assertNotIn('TEST_ONLY_SECRET',(self.root/'conversations'/(c.id+'.json')).read_text(encoding='utf-8'))
    def test_executor_cannot_escape_plan(self):
        s=PlannedSession(['verify_target'],cfg=self.cfg,run_root=self.root/'runs')
        with self.assertRaises(TaskError):s.call('match_seed',{})
    def test_premature_model_summary_is_incomplete(self):
        s=PlannedSession(['verify_target'],cfg=self.cfg,run_root=self.root/'runs')
        r=s.run_agent(lambda _:message_response('TEST_ONLY: done'))
        self.assertEqual(r['status'],'INCOMPLETE_OR_CLARIFICATION');self.assertFalse((s.path/'report.json').exists())
    def test_qa_receives_actual_results_not_invented_history(self):
        captured=[]
        def fake(p):captured.append(p);return message_response('TEST_ONLY：仅完成转录本核对。')
        c=self.controller(fake);c.submit({'interaction_mode':'meta','message':'核对','preset':'target'});self.wait(c)
        pid=c.plan['id'];c.action('execute',pid);self.wait(c);c.action('next',pid);self.wait(c)
        c.submit({'interaction_mode':'qa','message':'刚才做了什么？'});self.wait(c)
        context=json.loads(captured[-1]['messages'][-1]['content'])['local_context']
        self.assertEqual(context['result']['status'],'PARTIAL_COMPLETE');self.assertIn('verify_target',context['tool_results'])
    def test_guided_full_historical_workflow_is_labeled(self):
        c=self.controller();c.submit({'interaction_mode':'meta','message':'完整核对','preset':'full','tool_mode':'imported'});self.wait(c)
        pid=c.plan['id']
        for i in range(6):c.action('execute' if i==0 else 'next',pid);self.wait(c)
        self.assertEqual(c.result['status'],'COMPLETE')
        report=json.loads((c.session.path/'report.json').read_text(encoding='utf-8'))
        self.assertEqual(report['mode'],'guided');self.assertFalse(report['model_used']);self.assertEqual(report['agent_status'],'GUIDED_TOOLS_NO_LLM')
        self.assertIn('Guided tools',(c.session.path/'report.html').read_text(encoding='utf-8'))
    def test_auto_full_report_is_marked_test_model(self):
        from conversation import ORDER
        def fake(p):
            if p.get('tools') and p['tools'][0]['function']['name']=='propose_plan':
                return message_response(name='propose_plan',args={'decision':'ready','summary':'TEST_ONLY完整计划','tools':['compile_report'],'question':''})
            n=len([m for m in p['messages'] if m['role']=='tool'])
            if n<6:return message_response(name=ORDER[n])
            return message_response('TEST_ONLY工具证据总结')
        c=self.controller(fake);c.submit({'interaction_mode':'auto','message':'完整排序','tool_mode':'imported'});self.wait(c)
        c.action('execute',c.plan['id']);self.wait(c)
        self.assertEqual(c.result['status'],'COMPLETE')
        report=json.loads((c.session.path/'report.json').read_text(encoding='utf-8'))
        self.assertEqual(report['agent_status'],'TEST_TRANSPORT_ONLY');self.assertEqual(len(report['rows']),9)
    def test_auto_followup_answers_without_replacing_current_task(self):
        captured=[]
        def fake(p):
            captured.append(p)
            return message_response(name='propose_plan',args={'decision':'answer','summary':'这一步是在核对候选信息，还没有计算效力分数。','tools':[],'question':''})
        c=self.controller(fake);c.submit({'interaction_mode':'meta','message':'核对','preset':'target'});self.wait(c)
        pid=c.plan['id'];c.action('execute',pid);self.wait(c);session=c.session
        c.submit({'interaction_mode':'auto','message':'刚才这一步是什么意思？'});self.wait(c)
        self.assertIs(c.session,session);self.assertEqual(c.plan['id'],pid);self.assertEqual(c.phase,'guided')
        self.assertEqual(list(c.session.state),['inspect_candidates'])
        context=json.loads(captured[-1]['messages'][-1]['content'])['local_context']
        self.assertIn('inspect_candidates',context['tool_results']);self.assertEqual(c.messages[-1]['kind'],'qa')
    def test_auto_followup_network_failure_preserves_guided_task(self):
        def fail(_):raise TaskError('TEST_NETWORK_FAILURE')
        c=self.controller(fail);c.submit({'interaction_mode':'meta','message':'核对','preset':'target'});self.wait(c)
        pid=c.plan['id'];c.action('execute',pid);self.wait(c)
        c.submit({'interaction_mode':'auto','message':'这是什么意思？'});self.wait(c)
        self.assertEqual(c.plan['id'],pid);self.assertEqual(c.phase,'guided')
        self.assertEqual(list(c.session.state),['inspect_candidates']);self.assertIn('TEST_NETWORK_FAILURE',c.messages[-1]['diagnostics'])

if __name__=='__main__':unittest.main(verbosity=2)
