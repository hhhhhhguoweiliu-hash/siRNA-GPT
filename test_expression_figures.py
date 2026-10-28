"""Real baseline regression and failure boundaries; synthetic fixtures explicitly marked."""
import copy, io, json, tempfile, unittest, zipfile
from pathlib import Path
from unittest.mock import patch
from core import DATA, HOME, Session, default_candidates, read_tsv
from conversation import expand_plan, PRESETS
from expression_figures import prepare, rscript_path, render
from expression_data import parse_tpm

EXPECTED=[(1876,1156,1087,1077,79,10,710),(1365,853,811,797,56,14,498),
 (2209,1337,1277,1260,77,17,855),(1988,1207,1151,1136,71,15,766),
 (276,200,187,185,15,2,74),(728,481,464,457,24,7,240),
 (1333,860,813,804,56,9,464),(2139,1444,1355,1338,106,17,678),
 (2602,1647,1562,1541,106,21,934)]

class FigureTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.c=default_candidates();cls.e=read_tsv(DATA/'expression.tsv.gz');cls.seed=read_tsv(DATA/'historical_seed_matches.tsv')
 def test_real_nine_counts_equal_verified_v3(self):
  result=prepare(self.c,self.seed,self.e)
  for row,expected in zip(result['summary'],EXPECTED):
   self.assertEqual(tuple(row[k] for k in ('matched_genes','N','H','both','N_only','H_only','neither')),expected)
   self.assertEqual(row['unmapped'],0);self.assertEqual(row['mapped'],row['both']+row['N_only']+row['H_only']+row['neither'])
  self.assertEqual(result['top'][0]['approved_symbol'],'VIM')
  self.assertEqual(result['top'][1]['approved_symbol'],'HMGA1')
  self.assertEqual(len(result['matrix']),20*9)
 def test_subset_is_current_candidates_and_reselects_genes(self):
  c=[self.c[4]];seed=[r for r in self.seed if r['candidate_id']==c[0]['candidate_id']]
  r=prepare(c,seed,self.e)
  self.assertEqual(len(r['summary']),1);self.assertEqual(len(r['matrix']),20)
  self.assertTrue(all(x['candidate_id']==c[0]['candidate_id'] for x in r['matrix']))
  with self.assertRaises(ValueError):prepare(c,self.seed,self.e)
 def test_upload_changes_values_and_unknown_is_not_zero(self):
  # SYNTHETIC TEST ONLY: detection boundary, unknown and duplicated sites.
  header='ENTREZID\tapproved_symbol\tNor1\tNor2\tNor3\tNor4\tHyp1\tHyp2\tHyp3\tHyp4\n'
  e=parse_tpm(header+'7422\tVEGFA\t1\t1\t1\t1\t1\t1\t1\t1\n1\tA1BG\t1\t1\t0\t0\t1\t0\t0\t0\n')
  seed=[{'candidate_id':'SYNTHETIC','gene_id':g,'seed_site_count':'1'} for g in ['7422','1','1','999999999']]
  a=prepare([{'candidate_id':'SYNTHETIC'}],seed,e)
  self.assertEqual(a['summary'][0],{'candidate_id':'SYNTHETIC','matched_genes':2,'mapped':1,'unmapped':1,'N':1,'H':0,'both':0,'N_only':1,'H_only':0,'neither':0})
  e[1]['Hyp2']=2
  self.assertEqual(prepare([{'candidate_id':'SYNTHETIC'}],seed,e)['summary'][0]['both'],1)
 def test_missing_per_sample_values_fails(self):
  e=copy.deepcopy(self.e[:2]);e[0].pop('Hyp2')
  with self.assertRaises(ValueError):prepare(self.c,self.seed,e)
 def test_no_r_honest_failure_keeps_tables(self):
  with tempfile.TemporaryDirectory() as tmp:
   s=Session(candidates=self.c[:1],tool_mode='imported',run_root=tmp)
   for tool in ['inspect_candidates','match_seed','query_expression']:self.assertNotEqual(s.call(tool)['status'],'ERROR')
   with patch('expression_figures.rscript_path',side_effect=ValueError('R unavailable TEST ONLY')):
    result=s.call('render_expression_figures')
   self.assertEqual(result['status'],'ERROR');self.assertNotIn('render_expression_figures',s.state)
   self.assertTrue((s.path/'expression_figures/candidate_summary.tsv').is_file())
   self.assertFalse((s.path/'expression_figures/manifest.json').exists())
 def test_plans_and_six_tool_default_remain_unchanged(self):
  self.assertEqual(len(expand_plan(['compile_report'])),6)
  self.assertEqual(expand_plan(['render_expression_figures']),PRESETS['figures'])
  self.assertNotIn('render_expression_figures',PRESETS['full'])
  self.assertEqual(len(expand_plan(PRESETS['full_figures'])),7)
 def test_frozen_legacy_evaluation_remains_separate(self):
  from expression_data import builtin_receipt, builtin_path
  from dialogue_evaluation import load_package
  current=builtin_receipt();old=builtin_receipt('builtin_legacy_20261016')
  self.assertNotEqual(current['sha256'],old['sha256'])
  self.assertTrue(current['per_sample_tpm_available_in_packaged_table'])
  self.assertFalse(old['per_sample_tpm_available_in_packaged_table'])
  suite,resources=load_package()
  self.assertEqual(resources['files']['data/expression.tsv.gz']['sha256'],old['sha256'])
  from delivery import requirement_audit
  audit=requirement_audit({'task':{}},{'compile_report':{'status':'COMPLETE'}},['compile_report','render_expression_figures'])
  self.assertIn('render_expression_figures',audit['missing_steps'])
 def test_pdf_and_source_downloads_obey_existing_http_boundary(self):
  import app
  from test_http import request
  with tempfile.TemporaryDirectory() as tmp,patch.object(app,'HOME',Path(tmp)):
   folder=Path(tmp)/'runs/UNITTEST_ONLY/expression_figures';folder.mkdir(parents=True)
   (folder.parent/'result.json').write_text('{}')
   (folder/'candidate_expression.pdf').write_bytes(b'%PDF-UNITTEST-ONLY')
   (folder/'Candidates_Venn_1.png').write_bytes(b'PNG-UNITTEST-ONLY')
   (folder/'expression_figures.R').write_text('# UNITTEST ONLY')
   (folder/'settings.json').write_text('{}')
   self.assertEqual(request('GET','/runs/UNITTEST_ONLY/expression_figures/candidate_expression.pdf')[1],b'%PDF-UNITTEST-ONLY')
   self.assertEqual(request('GET','/runs/UNITTEST_ONLY/expression_figures/candidate_expression.pdf',headers={'Host':'foreign.example'})[0],403)
   status,body=request('GET','/runs/UNITTEST_ONLY/download.zip');self.assertEqual(status,200)
   with zipfile.ZipFile(io.BytesIO(body)) as z:
    self.assertIn('expression_figures/candidate_expression.pdf',z.namelist())
    self.assertIn('expression_figures/expression_figures.R',z.namelist())

if __name__=='__main__':unittest.main(verbosity=2)
