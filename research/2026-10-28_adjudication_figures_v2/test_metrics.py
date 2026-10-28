"""Regression against the agreed extraction protocol and recorded source layer."""
import unittest
from audit_data import load_data,slot_metrics,protected_integrity

class CorrectedMetricsTests(unittest.TestCase):
    def test_wrong_value_is_both_false_positive_and_missing_correct_value(self):
        rows=[{'review_status':s} for s in ('CORRECT','CORRECT','CORRECT','WRONG','MISSING')]
        r=slot_metrics(rows)
        self.assertEqual((r['TP'],r['FP'],r['FN']),(3,1,2))
        self.assertEqual(r['precision'],.75);self.assertEqual(r['recall'],.6);self.assertAlmostEqual(r['f1'],2/3)
    def test_unjudged_does_not_silently_become_missing_or_zero(self):
        with self.assertRaises(ValueError):slot_metrics([{'review_status':'UNJUDGED'}])
        r=slot_metrics([{'review_status':'MISSING'}]);self.assertTrue(r['precision_undefined']);self.assertEqual(r['recall'],0)
    def test_recorded_overlay_and_exact_slot_totals(self):
        data=load_data();overall={r['group']:r for r in data['summaries'] if r['category']=='OVERALL'}
        self.assertEqual({g:r['pass_after'] for g,r in overall.items()},{'llm':0,'workflow':8,'agent':9})
        self.assertEqual([(overall[g]['TP'],overall[g]['FP'],overall[g]['FN']) for g in ('llm','workflow','agent')],[(55,12,80),(130,0,5),(128,1,7)])
        self.assertAlmostEqual(overall['llm']['f1'],55/101);self.assertAlmostEqual(overall['agent']['f1'],32/33)
        self.assertEqual(data['changed_answers'],['A002','A008','A013','A014'])
    def test_raw_answers_judgments_scores_and_old_figures_unchanged(self):
        result=protected_integrity();self.assertEqual(result['n_files'],32);self.assertTrue(result['all_unchanged'])

if __name__=='__main__':unittest.main(verbosity=2)
