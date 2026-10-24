"""Sequence/reference binding and existing-data regression; no model calls."""
import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from core import Session,HOME,default_candidates
from conversation import prepare_inputs
import verified_imports as vi

class VerifiedImportTests(unittest.TestCase):
 def setUp(self):self.temp=tempfile.TemporaryDirectory(dir=HOME/'_test_runs');self.addCleanup(self.temp.cleanup)
 def session(self,candidate=None):return Session(candidates=[candidate or vi.candidates()[0]],tool_mode='imported',run_root=self.temp.name)
 def test_complete_purchased_workflow_and_export(self):
  s=self.session();self.assertEqual(s.run()['status'],'COMPLETE')
  r=json.loads((s.path/'report.json').read_text(encoding='utf-8'));x=r['rows'][0]
  self.assertEqual(x['candidate_id'],'USER_PURCHASED_siVEGF');self.assertEqual(x['covered_transcripts'],18)
  self.assertAlmostEqual(x['score'],1.121934400320053);self.assertEqual(x['seed_matched_genes'],2839)
  e=s.state['query_expression']['candidate_summary'][0];self.assertEqual(e['seed_site_count_all'],3540);self.assertEqual(e['seed_site_count_nontarget'],3539)
  self.assertEqual(s.state['score_candidates']['status'],'IMPORTED_VERIFIED_LOCAL');self.assertEqual(x['near_match_evidence'],'IMPORTED_VERIFIED_LOCAL')
  self.assertTrue((s.path/'verified_import'/vi.DATASET/'manifest.json').exists())
  self.assertIn('N3',r['limitations'][-2]);self.assertEqual(len(default_candidates()),9)
 def test_wrong_sequence_or_original_chemistry_or_id_rejected(self):
  for field,value in [('guide_core19_5to3','A'*19),('guide_21nt_RNA_5to3','A'*21),('passenger_21nt_RNA_5to3','A'*21),('candidate_id','renamed'),('original_row1','changed'),('original_modification','N3 removed')]:
   with self.subTest(field=field):
    c=vi.candidates()[0];c[field]=value
    with self.assertRaises(ValueError):vi.bind(c)
 def test_reference_version_mismatch_stops_import(self):
  with patch.object(vi,'sha',return_value='wrong'):
   with self.assertRaises(ValueError):vi.load()
 def test_matching_id_cannot_reuse_legacy_version(self):
  c=vi.candidates()[0];c.pop('evidence_dataset_id')
  self.assertEqual(self.session(c).run()['status'],'FAILED')
 def test_context_and_coordinates_must_match(self):
  c=vi.candidates()[0];r=vi.load()[2]
  x={k:r[k] for k in ['guide_core19_5to3','mRNA_context_57nt','core_start_1based','core_end_1based']}
  vi.bind(c,x);x['core_start_1based']+=1
  with self.assertRaises(ValueError):vi.bind(c,x)
 def test_explicit_dropdown_and_unknown_dataset(self):
  p=prepare_inputs({'candidate_dataset_id':vi.DATASET,'tool_mode':'imported'})
  self.assertEqual(len(p['candidates']),1);self.assertEqual(p['candidates'][0]['candidate_id'],'USER_PURCHASED_siVEGF')
  with self.assertRaises(ValueError):prepare_inputs({'candidate_dataset_id':'unknown'})

if __name__=='__main__':unittest.main(verbosity=2)
