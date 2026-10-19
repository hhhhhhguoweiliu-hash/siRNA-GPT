"""Offline contract/regression tests; fake external services are explicitly identified."""
import io,json,tempfile,unittest,urllib.error
from pathlib import Path
from unittest.mock import patch
from research import fetch,search_pubmed,search_web,read_webpage
from model_client import responses_payload,normalize_responses
from conversation import Conversation

class Reply(io.BytesIO):
    def __init__(self,data,kind='text/html'):
        super().__init__(data.encode() if isinstance(data,str) else data);self.headers={'Content-Type':kind}

def model(text=None,tool=None,args=None):
    m={'role':'assistant','content':text}
    if tool:m['tool_calls']=[{'id':'TEST_CALL','type':'function','function':{'name':tool,'arguments':json.dumps(args or {})}}]
    return {'choices':[{'message':m,'finish_reason':'stop'}],'usage':{'total_tokens':1}}

class ResearchTests(unittest.TestCase):
    def test_native_search_shape_preserved(self):
        r=responses_payload({'messages':[{'role':'user','content':'question'}],
            'tools':[{'type':'web_search','sources':['search_engine'],'limit':5}], 'tool_choice':{'type':'web_search'}})
        self.assertEqual(r['tools'][0]['type'],'web_search');self.assertEqual(r['tool_choice'],{'type':'web_search'})
        self.assertEqual(r['input'][0]['type'],'message')
    def test_native_citations_come_from_annotations_only(self):
        r=normalize_responses({'status':'completed','output':[
            {'type':'web_search_call','status':'completed','action':{'type':'search','query':'TEST'}},
            {'type':'message','content':[{'type':'output_text','text':'TEST_ONLY', 'annotations':[
                {'type':'url_citation','url':'https://pubmed.ncbi.nlm.nih.gov/1/','title':'TEST'},
                {'type':'url_citation','url':'javascript:alert(1)','title':'BAD'}]}]}]})
        self.assertEqual(len(r['sources']),1);self.assertEqual(len(r['web_search_calls']),1)
    def test_fluent_answer_without_search_is_not_verified(self):
        r=search_web('TEST',{'api_mode':'responses'},lambda _:model('I searched, trust me'))
        self.assertEqual(r['status'],'NO_VERIFIABLE_SOURCES');self.assertEqual(r['sources'],[])
    def test_pubmed_parses_nested_title_and_abstract(self):
        xml='<PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>123</PMID><Article><ArticleTitle>Test <i>siRNA</i></ArticleTitle><Abstract><AbstractText Label="RESULTS">Test abstract</AbstractText></Abstract><Journal><Title>Test journal</Title><JournalIssue><PubDate><Year>2026</Year></PubDate></JournalIssue></Journal></Article></MedlineCitation><PubmedData><ArticleIdList><ArticleId IdType="doi">10.test/123</ArticleId></ArticleIdList></PubmedData></PubmedArticle></PubmedArticleSet>'
        with patch('research.ncbi_fetch',side_effect=[json.dumps({'esearchresult':{'idlist':['123']}}),xml]):r=search_pubmed('TEST')
        self.assertEqual(r['articles'][0]['title'],'Test siRNA');self.assertIn('RESULTS: Test abstract',r['articles'][0]['abstract'])
        self.assertEqual(r['sources'][0]['url'],'https://pubmed.ncbi.nlm.nih.gov/123/')
    def test_no_pubmed_results_are_explicit(self):
        with patch('research.ncbi_fetch',return_value='{"esearchresult":{"idlist":[]}}'):r=search_pubmed('TEST')
        self.assertEqual(r['status'],'NO_RESULTS')
    def test_reader_blocks_local_addresses_and_spoofed_hosts(self):
        for url in ['https://127.0.0.1/','http://nature.com/','https://nature.com.evil.test/','https://user:pass@nature.com/','https://nature.com:8080/']:
            with self.subTest(url=url),self.assertRaises(ValueError):fetch(url)
    def test_reader_revalidates_redirect(self):
        def fake(req,timeout):raise urllib.error.HTTPError(req.full_url,302,'redirect',{'Location':'https://127.0.0.1/'},io.BytesIO())
        with self.assertRaises(ValueError):fetch('https://nature.com/test',fake)
    def test_reader_bounds_response_and_rejects_pdf(self):
        with self.assertRaises(ValueError):fetch('https://nature.com/',lambda *a,**k:Reply(b'%PDF-test','application/pdf'))
        with self.assertRaises(ValueError):fetch('https://nature.com/',lambda *a,**k:Reply(b'a'*1_000_001))
    def test_reader_strips_script_and_retains_source(self):
        r=read_webpage('https://nature.com/test',lambda *a,**k:Reply('<title>TEST</title><script>STEAL_SECRET</script><p>'+('Evidence text '*30)+'</p>'))
        self.assertNotIn('STEAL_SECRET',r['text']);self.assertEqual(r['sources'][0]['title'],'TEST')
    def test_reader_does_not_claim_block_page_as_evidence(self):
        with self.assertRaises(ValueError):read_webpage('https://nature.com/test',lambda *a,**k:Reply('Checking your browser'+'x'*200))

class ResearchLoopTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.cfg={'api_mode':'responses','model':'TEST','api_key':'TEST_SECRET'}
    def tearDown(self):self.tmp.cleanup()
    def controller(self,transport):return Conversation(root=Path(self.tmp.name)/'conversations',cfg_loader=lambda:self.cfg,transport=transport)
    def test_tool_result_is_returned_to_model_and_sources_rendered(self):
        requests=[]
        def fake(p):
            requests.append(p)
            return model(tool='search_pubmed',args={'query':'TEST'}) if len(requests)==1 else model('Evidence [S1]. Fabrication [S999].')
        c=self.controller(fake)
        result={'status':'OK','sources':[{'url':'https://pubmed.ncbi.nlm.nih.gov/123/','title':'TEST','kind':'PubMed abstract'}],'articles':[{'abstract':'TEST_ONLY'}]}
        with patch('conversation.research_tool',return_value=result):c.answer('Please search TEST')
        self.assertTrue(any('TEST_ONLY' in m.get('content','') for m in requests[-1]['messages'] if m['role']=='tool'))
        self.assertEqual(c.messages[-1]['sources'][0]['id'],'S1')
        self.assertNotIn('[S999]',c.messages[-1]['text']);self.assertIn('[S1]',c.messages[-1]['text'])
        self.assertNotIn('TEST_SECRET',(c.root/(c.id+'.json')).read_text(encoding='utf-8'))
    def test_tools_disabled_preserves_local_context(self):
        seen=[]
        c=self.controller(lambda p:(seen.append(p),model('TEST_ONLY local answer'))[1]);c.result={'status':'PARTIAL_COMPLETE'}
        c.answer('Explain result',web_enabled=False)
        self.assertNotIn('tools',seen[0]);self.assertIn('PARTIAL_COMPLETE',seen[0]['messages'][-1]['content'])
    def test_failure_allows_new_tool_instead_of_fake_success(self):
        seen=[]
        def fake(p):
            seen.append(p)
            if len(seen)==1:return model(tool='search_web',args={'query':'TEST'})
            if len(seen)==2:return model(tool='search_pubmed',args={'query':'TEST'})
            return model('Found an abstract [S1].')
        c=self.controller(fake)
        with patch('conversation.research_tool',side_effect=[ValueError('TEST search unavailable'),{'status':'OK','sources':[{'title':'TEST','url':'https://pubmed.ncbi.nlm.nih.gov/123/'}]}]):c.answer('Search TEST')
        self.assertEqual(len(c.research_state['steps']),2);self.assertEqual(c.research_state['status'],'complete_with_errors')
        self.assertEqual(len(c.messages[-1]['sources']),1)
    def test_repeating_same_failed_call_is_stopped(self):
        seen=[]
        def fake(p):
            seen.append(p)
            return model(tool='search_pubmed',args={'query':'TEST'}) if len(seen)<3 else model('No sources available')
        c=self.controller(fake)
        with patch('conversation.research_tool',return_value={'status':'NO_RESULTS','sources':[]}) as tool:c.answer('TEST')
        self.assertEqual(tool.call_count,1);self.assertEqual(c.messages[-1]['sources'],[])

if __name__=='__main__':unittest.main()
