"""English chrome with original scientific/model content preserved; no API calls."""
import copy,html,json,re,tempfile,unittest
from pathlib import Path
from core import Session,HOME
from runtime_info import manifest
from test_http import request

class EnglishInterfaceTests(unittest.TestCase):
 def test_home_and_labels_asset(self):
  status,body=request('GET','/');self.assertEqual(status,200)
  text=body.decode();self.assertIn('lang="en"',text)
  self.assertIn('Model connection settings',text)
  self.assertIn('Three-arm development evaluation',text)
  self.assertFalse(re.search('[\u4e00-\u9fff]',text))
  status,body=request('GET','/ui_text.js');self.assertEqual(status,200)
  self.assertIn(b'uiSourceLabel',body)
  self.assertEqual(manifest()['interface_language'],'en')
  self.assertIn('index.html',manifest()['assets'])

 def test_saved_report_rerender_preserves_original_model_and_values(self):
  source=HOME/'research/2026-10-24_nearfull_complete/live/tool_export/report.json'
  original_bytes=source.read_bytes();report=json.loads(original_bytes);before=copy.deepcopy(report)
  with tempfile.TemporaryDirectory() as d:
   session=Session.__new__(Session);session.path=Path(d);session.id=report['run_id']
   session.mode='agent';session.tool_mode='imported';session.task=report['task']
   session.expression_source=report['expression_source'];session.render(report)
   page=(Path(d)/'report.html').read_text(encoding='utf-8')
   self.assertIn('lang="en"',page);self.assertIn('Candidate evidence table',page)
   self.assertIn('Detected in hypoxia',page)
   self.assertIn(html.escape(report['model_summary']),page)
   self.assertIn('GAUAGAGCAAGACAAGACAAGAAA',page)
   self.assertIn('GAUAGAGCAAGACAAGAAATT-N3',page)
   self.assertEqual(report,before)
  self.assertEqual(source.read_bytes(),original_bytes)

 def test_source_page_chrome_retains_original_card_text(self):
  status,body=request('GET','/knowledge');self.assertEqual(status,200)
  text=body.decode();self.assertIn('Project information cards',text)
  self.assertIn('original language',text)
  from knowledge import catalogue
  self.assertIn(html.escape(catalogue()['cards'][0]['text']),text)

if __name__=='__main__':unittest.main()
