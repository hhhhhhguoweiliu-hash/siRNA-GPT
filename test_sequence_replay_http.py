"""Read-only replay routes serve the checked artifacts, without API/tool execution."""
import json,unittest
from test_http import request

class SequenceReplayHTTPTests(unittest.TestCase):
 def test_three_readonly_cases_and_shared_renderer(self):
  status,js=request('GET','/sequence_ui.js');self.assertEqual(status,200);self.assertIn(b'renderSequenceEvidence',js)
  for case,expected in [('known_error_24','FAIL'),('wrong_base_19','FAIL'),('normal_answer','PASS')]:
   with self.subTest(case=case):
    status,body=request('GET','/sequence-check-replay/'+case+'/result.json');self.assertEqual(status,200)
    result=json.loads(body);self.assertEqual(result['answer_validation']['status'],expected);self.assertEqual(result['new_model_requests'],0)
    status,body=request('GET','/sequence-check-replay/'+case+'/report.html');self.assertEqual(status,200)
    self.assertIn(('data-sequence-status="'+expected+'"').encode(),body)
 def test_unlisted_or_escape_files_not_served(self):
  for path in ['/sequence-check-replay/../../config.example.json','/sequence-check-replay/known_error_24/../../../config.example.json','/sequence-check-replay/unknown/result.json']:
   self.assertEqual(request('GET',path)[0],404)

if __name__=='__main__':unittest.main(verbosity=2)
