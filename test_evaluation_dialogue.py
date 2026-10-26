"""Real saved scientific evidence, explicit model STUBS, no paid model calls."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core import HOME, read_tsv
from evaluation_dialogue import run_dialogue, fixed_plan
from test_conversation import message_response

PACK = HOME / 'research/2026-10-27_evaluation_review_response/package'


def fixtures():
    cases = json.loads((PACK / 'runtime/cases.json').read_text(encoding='utf-8'))['cases']
    resources = json.loads((PACK / 'runtime/resources.json').read_text(encoding='utf-8'))
    return {c['id']: c for c in cases}, resources


def test_stub(payload):
    """Scripted transport for plumbing only; NOT evidence of model reasoning."""
    functions = payload.get('tools', [])
    if functions and functions[0]['function']['name'] == 'propose_plan':
        inputs = json.loads(payload['messages'][1]['content'])['input']
        plan = fixed_plan(inputs['task']['evaluation_conditions'])
        return message_response(name='propose_plan', args={
            'decision': 'ready' if plan else 'clarify', 'tools': plan,
            'summary': 'TEST_ONLY_MODEL_STUB，不代表真实模型回答或科研质量',
            'question': ''})
    if functions:
        return message_response(name=functions[0]['function']['name'], args={})
    return message_response('TEST_ONLY_MODEL_STUB，未调用真实模型；此文字不能用作科学回答质量评价。')


class DevelopmentDialogueTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.cases, self.resources = fixtures()
        self.cfg = {'model': 'TEST_MODEL_NOT_PROVIDER', 'provider': 'TEST_ONLY',
                    'max_tool_calls': 18, 'max_model_turns': 12, 'max_output_tokens': 1800}

    def tearDown(self):
        self.temp.cleanup()

    def run_arm(self, identity, group):
        return run_dialogue(group, self.cases[identity], self.cfg, self.root / (identity + '_' + group),
                            test_stub if group != 'workflow' else None, self.resources)

    def test_two_round_same_full_inputs_own_histories_settings_and_no_answer_leak(self):
        results = [self.run_arm('U1', group) for group in ('llm', 'workflow', 'agent')]
        self.assertEqual(len(results[0]['rounds']), 2)
        self.assertEqual(len({r['input_sha256'] for r in results}), 1)
        self.assertEqual(len({r['resource_access']['resources_sha256'] for r in results}), 1)
        for result in results:
            first, second = result['rounds']
            self.assertEqual(first['history_before'], [])
            self.assertEqual(second['history_before'], first['history_after'])
            self.assertEqual(second['history_before'][1]['content'], first['answer'])
            for request in result['test_prepared_requests']:
                value = json.loads(request['payload']['messages'][1]['content'])
                raw = value['input']['task']['shared_user_input']
                index = request['round'] - 1
                self.assertEqual(raw, result['rounds'][index]['common_user_input'])
                self.assertEqual(value['input']['task']['own_history'], result['rounds'][index]['history_before'])
                self.assertEqual(request['effective_settings']['max_output_tokens'], 1800)
                if result['group'] == 'llm':
                    self.assertNotIn('tools', request['payload'])
                    self.assertNotIn('0.9915144175887107', json.dumps(request['payload']))
            self.assertEqual(result['real_model_requests'], 0)
        fixed = results[1]
        self.assertNotIn('score_candidates', fixed['rounds'][0]['completed_tools'])
        self.assertIn('0.9915144175887107', fixed['rounds'][1]['answer'])
        self.assertNotIn('未评分', fixed['rounds'][1]['answer'])
        self.assertIn('本轮新增：score_candidates', fixed['rounds'][1]['answer'])

    def test_raw_docx_only_first_turn_role_assumption_only_second_and_binding_succeeds(self):
        for group in ('llm', 'workflow', 'agent'):
            result = self.run_arm('R1', group)
            first, second = result['rounds']
            self.assertNotIn('calculation_assumptions', first['common_user_input']['user_input'])
            self.assertEqual(first['completed_tools'], [])
            for request in result['test_prepared_requests']:
                if request['round'] == 1:
                    inputs = json.loads(request['payload']['messages'][1]['content'])['input']
                    self.assertEqual(inputs['candidates'], [])
                    self.assertNotIn('sequence_checks', json.dumps(inputs))
                    self.assertNotIn('derivation', json.dumps(inputs))
            self.assertIn('-N3（叠氮基团，用于点击化学）', first['common_user_input']['user_input']['original_order_lines'][0])
            if group != 'llm':
                self.assertIn('score_candidates', second['completed_tools'])
                self.assertEqual(second['tool_results']['score_candidates']['rows'][0]['oligoformer_scaled_score'], 1.121934400320053)

    def test_workflow_score_and_all_compared_candidates_flags_and_query_window_visible(self):
        result = self.run_arm('W3', 'workflow')
        answer = result['answer']
        for text in ('VEGFA_SD_3535', 'VEGFA_SD_3499', '1.0035899763107299', '0.9915144175887107',
                     'IRGM', 'AUTHOR_G2_G20_19NT', 'AUCUGUAUUUCUUUGUCGU', 'NR_170598.1:1724–1742'):
            self.assertIn(text, answer)
        rows = {r['candidate_id']: r for r in result['tool_results']['compile_report']['rows']}
        self.assertTrue(rows['VEGFA_SD_3535']['review_flags'])
        self.assertFalse(rows['VEGFA_SD_3535']['selected_for_review'])
        self.assertTrue(rows['VEGFA_SD_3499']['selected_for_review'])

    def test_purchased_full_report_shows_both_states_without_reranking(self):
        result = self.run_arm('W1', 'workflow')
        row = result['tool_results']['query_expression']['candidate_summary'][0]
        self.assertEqual([row[k] for k in ('seed_site_count_nontarget', 'matched_genes', 'baseline_mapped_genes',
                         'unmapped_genes', 'hypoxia_detected_genes', 'normoxia_detected_genes')], [3539, 2839, 2836, 3, 1595, 1695])
        for text in ('常氧检出基因', '缺氧检出基因', '1695', '1595', 'N3', '18/20'):
            self.assertIn(text, result['answer'])

    def test_wrong_coordinate_declaration_consumed_without_losing_real_target_match(self):
        result = self.run_arm('R3', 'workflow')
        row = result['tool_results']['verify_target']['rows'][0]
        check = row['declared_coordinate_checks'][0]
        self.assertEqual(check['reference_length_nt'], 3609)
        self.assertFalse(check['in_bounds_and_19nt'])
        self.assertEqual((row['core_start_1based'], row['core_end_1based']), (3501, 3519))
        self.assertIn('3610', result['answer'])
        self.assertIn('3501–3519', result['answer'])

    def test_missing_required_expression_does_not_read_builtin_join_and_keeps_partial_evidence(self):
        import core
        for group in ('workflow', 'agent'):
            read_paths = []
            def tracked(path):
                read_paths.append(Path(path).name)
                return read_tsv(path)
            with patch.object(core, 'read_tsv', side_effect=tracked):
                result = self.run_arm('R4', group)
            self.assertIn('score_candidates', result['completed_tools'])
            self.assertIn('match_seed', result['completed_tools'])
            self.assertNotIn('query_expression', result['completed_tools'])
            self.assertNotIn('compile_report', result['completed_tools'])
            self.assertNotIn('expression.tsv.gz', read_paths)
            self.assertIn('禁止回退', result['answer'])
            self.assertNotIn('未评分', result['answer'])

    def test_single_base_change_never_receives_old_score(self):
        for group in ('workflow', 'agent'):
            result = self.run_arm('R2', group)
            self.assertNotIn('score_candidates', result['tool_results'])
            self.assertIn('FAILED', result['status'])
            self.assertEqual(result['rounds'][0]['common_user_input']['user_input']['candidate_rows'][0]['guide_core19_5to3'], 'AUUCUUGUCUUGCUCUAUC')

    def test_no_model_gate_qa_not_comparable_and_no_per_case_preset(self):
        for group in ('llm', 'agent'):
            with self.assertRaisesRegex(ValueError, '尚未接入网页用量确认'):
                run_dialogue(group, self.cases['U1'], self.cfg, self.root / ('gate_' + group))
        with self.assertRaisesRegex(ValueError, '尚未具备三组对等入口'):
            self.run_arm('Q1', 'workflow')
        for case in self.cases.values():
            self.assertNotIn('preset', case)
            for turn in case['rounds']:
                renamed = copy.deepcopy(case)
                renamed['id'] = 'ARBITRARY_NEW_ID'
                self.assertEqual(fixed_plan(turn['conditions']), fixed_plan(renamed['rounds'][case['rounds'].index(turn)]['conditions']))


if __name__ == '__main__':
    unittest.main()
