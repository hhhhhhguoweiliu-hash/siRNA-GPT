"""SYNTHETIC algorithm checks only. These are not research/model results."""
import copy
import unittest
from evaluation_analysis import summarize, DIMENSIONS


def synthetic_fixture(repeats=1):
    plan = [{'answer_id': g + str(n), 'case_id': 'SYNTHETIC_TASK', 'group': g, 'repeat': n,
             'category': 'work', 'family': 'SYNTHETIC_FAMILY', 'required_fact_ids': ['f1']}
            for g in ('llm', 'workflow', 'agent') for n in range(1, (1 if g == 'workflow' else repeats) + 1)]
    execution = [{'answer_id': p['answer_id'], 'execution': 'ATTEMPTED'} for p in plan]
    reviews = [{**{k: 1 for k in DIMENSIONS}, 'answer_id': p['answer_id'], 'reviewer_id': reviewer,
                'delivery_judgement': '完成' if p['group'] != 'agent' else '未交付',
                'severe_error': False, 'facts': {'f1': 'correct'}, 'unscorable_reason': ''}
               for p in plan for reviewer in ('SYNTHETIC_REVIEWER_A', 'SYNTHETIC_REVIEWER_B')]
    return plan, execution, reviews


class QuantitativeChecks(unittest.TestCase):
    def test_negative_difference_zero_baseline_missing_usage_and_task_weights(self):
        p, e, r = synthetic_fixture(3)
        out = summarize(p, e, r)
        pair = next(x for x in out['paired_differences'] if x['configuration'] == 'agent' and x['baseline'] == 'llm')
        self.assertEqual(pair['completion_percentage_point_difference'], -100)
        self.assertEqual(pair['completion_relative_change_percent'], -100)
        self.assertEqual(pair['completion_task_win_tie_loss']['loss'], 1)
        self.assertTrue(all(s['task_count'] == 1 for s in out['category_summaries']))
        self.assertTrue(all(u['real_total_tokens'] is None for u in out['unit_records']))
        for row in r:
            if row['answer_id'].startswith('llm'):
                row['delivery_judgement'] = '未交付'
        out = summarize(p, e, r)
        pair = next(x for x in out['paired_differences'] if x['configuration'] == 'agent' and x['baseline'] == 'llm')
        self.assertIsNone(pair['completion_relative_change_percent'])
        self.assertEqual(pair['completion_percentage_point_difference'], 0)

    def test_missing_plan_units_duplicate_ratings_and_mismatched_denominators_rejected(self):
        p, e, r = synthetic_fixture()
        with self.assertRaisesRegex(ValueError, '全部计划单元'):
            summarize(p, e[:-1], r)
        with self.assertRaisesRegex(ValueError, '重复评分'):
            summarize(p, e, r + [r[0]])
        with self.assertRaisesRegex(ValueError, '分母不一致'):
            summarize(p[:-1], e[:-1], [])

    def test_blank_scores_not_zero_and_incomplete_batch_cannot_be_full_comparison(self):
        p, e, r = synthetic_fixture()
        e[0]['execution'] = 'NOT_EXECUTED'
        out = summarize(p, e, [])
        self.assertTrue(all(s['completion_rate_percent'] is None for s in out['category_summaries']))
        self.assertTrue(all(s['quality']['accuracy_0_2'] is None for s in out['category_summaries']))
        with self.assertRaisesRegex(ValueError, '未运行'):
            summarize(p, e, r)

    def test_human_disagreement_requires_recorded_human_resolution(self):
        p, e, r = synthetic_fixture()
        r[0]['delivery_judgement'] = '未交付'
        out = summarize(p, e, r)
        unit = next(x for x in out['unit_records'] if x['answer_id'] == r[0]['answer_id'])
        self.assertIsNone(unit['delivery_judgement'])
        self.assertIsNone(next(s for s in out['category_summaries'] if s['group'] == 'llm')['completion_rate_percent'])
        out = summarize(p, e, r, [{'answer_id': r[0]['answer_id'], 'adjudicator_id': 'SYNTHETIC_HUMAN_C',
                                 'reason': 'SYNTHETIC_ONLY', 'delivery_judgement': '完成'}])
        self.assertEqual(next(x for x in out['unit_records'] if x['answer_id'] == r[0]['answer_id'])['complete'], 1)


if __name__ == '__main__':
    unittest.main()
