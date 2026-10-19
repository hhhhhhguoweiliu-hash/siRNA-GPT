import copy, json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import expression_data as expression
from core import Session, default_candidates
from conversation import prepare_inputs

HEADER='ENTREZID\tapproved_symbol\tNor1\tNor2\tNor3\tNor4\tHyp1\tHyp2\tHyp3\tHyp4\n'
TABLE=HEADER+'7422\tVEGFA\t1\t2\t3\t4\t10\t20\t30\t40\n'+'1\tA1BG\t0\t0\t0\t0\t2\t2\t0\t0\n'

class ExpressionTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
  self.patch=patch.object(expression,'STORE',self.root/'datasets');self.patch.start()
 def tearDown(self):self.patch.stop();self.temp.cleanup()
 def upload(self,text=TABLE):return expression.upload(text,'SYNTHETIC TEST ONLY',True)
 def test_means_and_sample_detection_are_actual_tpm(self):
  r=expression.parse_tpm(TABLE);self.assertEqual(r[0]['TPM_Hypoxia_mean'],25)
  self.assertEqual(r[1]['Hypoxia_n_TPM_ge1'],2);self.assertEqual(r[0]['TPM_Normoxia_mean'],2.5)
 def test_counts_header_not_accepted(self):
  with self.assertRaises(ValueError):self.upload(TABLE.replace('Nor1','counts_Nor1'))
 def test_duplicates_missing_nan_negative_rejected(self):
  for text in [TABLE+TABLE.splitlines()[-1]+'\n',TABLE.replace('\t10\t','\tNaN\t'),TABLE.replace('\t10\t','\t-1\t'),HEADER,TABLE.replace('7422\tVEGFA','7422\tOTHER')]:
   with self.subTest(text=text):
    with self.assertRaises(ValueError):self.upload(text)
 def test_declaration_required(self):
  with self.assertRaises(ValueError):expression.upload(TABLE,'test',False)
 def test_traversal_and_absent_dataset_fail_without_fallback(self):
  for identity in ['../data','f'*64]:
   with self.assertRaises(ValueError):expression.load_dataset(identity)
 def test_source_labels_have_distinct_identity(self):
  a=self.upload();b=expression.upload(TABLE,'SECOND SYNTHETIC SOURCE',True)
  self.assertNotEqual(a['id'],b['id']);self.assertEqual(a['sha256'],b['sha256'])
 def test_uploaded_expression_is_used_and_snapshotted(self):
  receipt=self.upload();inputs=prepare_inputs({'expression_dataset_id':receipt['id'],'tool_mode':'imported'})
  s=Session(run_root=self.root/'runs',**inputs)
  for n in ['inspect_candidates','match_seed']:self.assertNotEqual(s.call(n)['status'],'ERROR')
  cid=default_candidates()[0]['candidate_id']
  s.seed_rows=[{'candidate_id':cid,'gene_id':'7422','seed_site_count':'3'}, {'candidate_id':cid,'gene_id':'1','seed_site_count':'1'}, {'candidate_id':cid,'gene_id':'99999999','seed_site_count':'1'}]
  r=s.call('query_expression');self.assertEqual(float(r['target']['TPM_Hypoxia_mean']),25)
  first=r['candidate_summary'][0];self.assertEqual(first['matched_genes'],2)
  self.assertEqual(first['hypoxia_detected_genes'],1);self.assertEqual(first['normoxia_detected_genes'],0)
  self.assertEqual(first['hypoxia_only_detected_genes'],1);self.assertEqual(first['unmapped_genes'],1)
  expression.STORE.joinpath(receipt['id']+'.json').unlink()
  self.assertTrue((s.path/'expression_snapshot.json').exists());self.assertEqual(r['source']['source'],'USER_UPLOAD')
 def test_two_states_do_not_modify_sequence_score_or_ranking(self):
  selected=[]
  for state in ['Hypoxia','Normoxia']:
   s=Session(run_root=self.root/'runs',tool_mode='imported',task={'gene':'VEGFA','species':'Homo sapiens','state':state,'top_n':2})
   self.assertEqual(s.run()['status'],'COMPLETE');r=json.loads((s.path/'report.json').read_text(encoding='utf-8'))
   self.assertFalse(r['expression_changes_ranking']);selected.append([(x['candidate_id'],x['score']) for x in r['rows']])
   self.assertIn('expression_comparison',r);self.assertTrue((s.path/'expression_comparison.tsv').is_file())
  self.assertEqual(*selected)

class ExpressionHTTPTests(unittest.TestCase):
 def test_authenticated_upload_and_source_endpoints(self):
  import os
  from test_cloud import call
  with tempfile.TemporaryDirectory() as root,patch.object(expression,'STORE',Path(root)),patch.dict(os.environ,{'WEB_PASSWORD':'TEST_WEB_PASSWORD_123456789','RENDER_EXTERNAL_HOSTNAME':'sirna-test.onrender.com','RENDER_EXTERNAL_URL':'https://sirna-test.onrender.com'}):
   self.assertEqual(call('/api/expression-upload','POST',{},auth=False)[0],401)
   self.assertEqual(call('/api/data-source')[0],200)
   status,body,_=call('/api/expression-upload','POST',{'text':TABLE,'label':'SYNTHETIC ONLY','confirmed':True})
   self.assertEqual(status,200);self.assertEqual(json.loads(body)['rows'],2)
   self.assertEqual(call('/api/expression-upload','POST',{'text':TABLE,'label':'TEST','confirmed':False})[0],400)

if __name__=='__main__':unittest.main()
