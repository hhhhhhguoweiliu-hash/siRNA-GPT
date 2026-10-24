"""Deterministic library boundaries and integration, never scientific quality scores."""
import base64
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile,ZIP_DEFLATED
from pypdf import PdfWriter
from pypdf.generic import NameObject,NumberObject,DictionaryObject,DecodedStreamObject
import literature
from literature import Library
from conversation import Conversation
from test_conversation import message_response
from test_http import request
from contextlib import redirect_stdout

ROOT=Path(__file__).resolve().parent


def image_pdf():
    """TEST_ONLY white-image PDF, generated in memory, no scientific content."""
    writer=PdfWriter();page=writer.add_blank_page(width=100,height=100)
    image=DecodedStreamObject();image.set_data(b'\xff\xff\xff')
    image.update({NameObject('/Type'):NameObject('/XObject'),NameObject('/Subtype'):NameObject('/Image'),
                  NameObject('/Width'):NumberObject(1),NameObject('/Height'):NumberObject(1),
                  NameObject('/ColorSpace'):NameObject('/DeviceRGB'),NameObject('/BitsPerComponent'):NumberObject(8)})
    page[NameObject('/Resources')]=DictionaryObject({NameObject('/XObject'):DictionaryObject({NameObject('/Im0'):writer._add_object(image)})})
    content=DecodedStreamObject();content.set_data(b'q 100 0 0 100 0 0 cm /Im0 Do Q')
    page[NameObject('/Contents')]=writer._add_object(content)
    memory=io.BytesIO();writer.write(memory);return memory.getvalue()


class LiteratureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        scratch=ROOT/'.test_tmp';scratch.mkdir(exist_ok=True)
        cls.tmp=tempfile.TemporaryDirectory(dir=scratch)
        cls.root=Path(cls.tmp.name)
        cls.lib=Library(cls.root/'library',ROOT/'references/sirna_library')

    @classmethod
    def tearDownClass(cls):
        assert cls.root.resolve().is_relative_to((ROOT/'.test_tmp').resolve())
        cls.tmp.cleanup()

    def empty(self,name):
        return Library(self.root/name)

    def test_pdf_original_page_and_fragment(self):
        docs=self.lib.catalogue()['documents']
        pdf=next(d for d in docs if d['filename'].endswith('.pdf'))
        doc,path,parts=self.lib.document(pdf['id'])
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),doc['sha256'])
        self.assertTrue(parts);self.assertTrue(all(c['page'] in range(1,doc['page_count']+1) for c in parts) if 'page_count' in doc else all(c['page'] for c in parts))
        self.assertEqual(len(doc['pages']),8)
        self.assertTrue(all(doc['pages'][c['page']-1]['text'][c['start']:c['end']]==c['text'] for c in parts))

    def test_chinese_query_retrieves_english(self):
        r=self.lib.search('OligoFormer需要什么siRNA和mRNA输入，19个碱基和57个碱基分别是什么？')
        self.assertIn('context',r['query_terms'])
        self.assertTrue(any('OligoFormer' in h['title'] and h['source_kind']!='project_record' for h in r['hits']))

    def test_seed_historical_definition_retrieved(self):
        r=self.lib.search('SeedMatchR中guide的mer7m8种子匹配定义是什么，方向怎样确定？')
        self.assertTrue(any(h['source_version']=='1.1.1' for h in r['hits']))

    def test_fragment_url_and_digest(self):
        for h in self.lib.search('siDirect 23 21 guide passenger')['hits']:
            doc,_,parts=self.lib.document(h['document_id'])
            c=next(c for c in parts if c['chunk_id']==h['chunk_id'])
            self.assertEqual(h['chunk_sha256'],c['sha256']);self.assertEqual(h['text'],c['text'])

    def test_boundary_explanation_is_retrieved(self):
        from knowledge import search
        with patch('literature.get_library',return_value=self.lib):r=search('为什么本项目不能根据TPM证明患者疗效？')
        self.assertTrue(r['retrieval_executed']);self.assertIn('expression',[x['id'] for x in r['cards']])

    def test_scope_stop_distinct_from_real_empty_search(self):
        stopped=self.lib.search('请为这位患者制定临床给药方案')
        self.assertEqual(stopped['status'],'OUT_OF_SCOPE');self.assertFalse(stopped['retrieval_executed'])
        empty=self.lib.search('ZXQ987654321')
        self.assertEqual(empty['status'],'NO_RESULTS');self.assertTrue(empty['retrieval_executed'])

    def test_day7_question_reaches_model_with_related_evidence(self):
        calls=[]
        def fake(p):calls.append(p);return message_response('TEST_ONLY 未取得对应实测数据 [S1]')
        c=Conversation(cfg_loader=lambda:{'model':'TEST','api_key':'TEST_ONLY_SECRET'},transport=fake,root=self.root/'day7_test')
        with patch('literature.get_library',return_value=self.lib):
            c.answer('VEGFA_SD_3499在ARPE-19转染后第7天实测敲低率是多少？',web_enabled=False,literature_only=True)
        self.assertEqual(len(calls),1);self.assertTrue(c.current_audit['retrieval_executed'])
        self.assertTrue(c.current_audit['retrieved_excerpts'])

    def test_reject_corrupt_pdf_without_partial_document(self):
        lib=self.empty('bad_pdf');before=lib.version()
        with self.assertRaisesRegex(ValueError,'PDF'):lib.import_document(b'%PDF-1.4\nBROKEN','bad.pdf',{'title':'TEST_ONLY damaged','source_url':'https://example.org/pdf'})
        self.assertEqual(lib.version(),before);self.assertEqual(lib.catalogue()['documents'],[])

    def test_reject_image_only_pdf(self):
        lib=self.empty('image_pdf')
        with self.assertRaisesRegex(ValueError,'扫描版|图片PDF'):lib.import_document(image_pdf(),'TEST_ONLY_image.pdf',{'title':'TEST_ONLY image','source_url':'https://example.org/pdf'})
        self.assertFalse(lib.catalogue()['documents'])

    def test_text_preserves_original_and_has_no_pdf_page(self):
        lib=self.empty('utf8');raw=('TEST_ONLY source. Seed definitions are sequence patterns, not experiments.\n'*3).encode()
        r=lib.import_document(raw,'source.txt',{'title':'TEST_ONLY text','source_url':'https://example.org/source','source_kind':'official_documentation'})
        doc,path,parts=lib.document(r['document']['id'])
        self.assertEqual(path.read_bytes(),raw);self.assertTrue(all(c['page'] is None for c in parts))

    def test_duplicate_preserves_first_metadata(self):
        doc=self.lib.catalogue()['documents'][0];raw=self.lib.document(doc['id'])[1].read_bytes()
        r=self.lib.import_document(raw,doc['filename'],{**doc,'title':'TEST attempt to relabel'})
        self.assertEqual(r['status'],'ALREADY_PRESENT');self.assertEqual(r['document']['title'],doc['title'])

    def test_export_restore_rebuild_identity(self):
        raw=self.lib.export_bundle();restored=self.empty('restored')
        r=restored.import_bundle(raw)
        self.assertTrue(r['same_version']);self.assertEqual(restored.version(),self.lib.version())
        queries=['OligoFormer 19 57 input','siDirect 23 21 guide passenger']
        for q in queries:
            self.assertEqual(restored.search(q)['hits'],self.lib.search(q)['hits'])
        restored.db.unlink();restored.rebuild();self.assertEqual(restored.version(),self.lib.version())

    def test_altered_extracted_text_rejected(self):
        good=ZipFile(io.BytesIO(self.lib.export_bundle()));body=io.BytesIO()
        with ZipFile(body,'w',ZIP_DEFLATED) as z:
            for n in good.namelist():
                raw=good.read(n)
                if n=='library.json':
                    meta=json.loads(raw);meta['documents'][0]['pages'][0]['text']+=' TEST_FORGED'
                    raw=json.dumps(meta).encode()
                z.writestr(n,raw)
        lib=self.empty('tampered')
        with self.assertRaisesRegex(ValueError,'不一致'):lib.import_bundle(body.getvalue())
        self.assertFalse(lib.catalogue()['documents'])

    def test_zip_path_escape_rejected(self):
        body=io.BytesIO()
        with ZipFile(body,'w') as z:z.writestr('../outside.txt','TEST_ONLY')
        with self.assertRaisesRegex(ValueError,'不安全'):self.empty('traversal').import_bundle(body.getvalue())

    def test_no_model_call_when_no_sources(self):
        called=[]
        c=Conversation(cfg_loader=lambda:{'model':'TEST','api_key':'TEST_ONLY_SECRET'},transport=lambda p:called.append(p),root=self.root/'no_answer_conversation')
        with patch('literature.get_library',return_value=self.lib):c.answer('ZXQ987654321',web_enabled=False,literature_only=True)
        self.assertFalse(called);self.assertIn('证据不足',c.messages[-1]['text']);self.assertEqual(c.current_audit['model_call_count'],0)

    def test_actual_retrieved_text_and_unknown_citation_guard(self):
        requests=[]
        def fake(p):requests.append(p);return message_response('TEST_ONLY answer [S999]')
        c=Conversation(cfg_loader=lambda:{'model':'TEST','api_key':'TEST_ONLY_SECRET'},transport=fake,root=self.root/'citation_conversation')
        with patch('literature.get_library',return_value=self.lib):c.answer('OligoFormer分数超过1可以解释为敲低率吗？',web_enabled=False,literature_only=True)
        self.assertNotIn('tools',requests[0]);self.assertIn('retrieved_excerpts',json.loads(requests[0]['messages'][-1]['content']))
        self.assertIn('未核实引用',c.messages[-1]['text']);self.assertEqual(c.current_audit['status'],'citation_warning')
        self.assertEqual(c.current_audit['library_version'],self.lib.version())
        exported=c.export_record();self.assertTrue(any(e.get('retrieved_excerpts') for e in exported['evidence_records']))

    def test_http_library_source_and_manual_usage_gate(self):
        with patch('literature.get_library',return_value=self.lib):
            status,body=request('GET','/api/library');self.assertEqual(status,200)
            doc=json.loads(body)['documents'][0]
            status,body=request('GET',doc['url']);self.assertEqual(status,200);self.assertIn(doc['sha256'].encode(),body)
            status,body=request('GET',doc['original_url']);self.assertEqual(status,200)
            status,body=request('POST','/api/library-demo-start',{'confirm_api_usage':False});self.assertEqual(status,400)
            status,body=request('POST','/api/library-search',{'query':'mer7m8 guide'});self.assertEqual(status,200)
            status,body=request('GET','/api/library/original/../../config.local.json');self.assertEqual(status,400)

    def test_html_source_text_is_escaped(self):
        lib=self.empty('html');raw=('<script>alert("TEST_ONLY")</script>\n'+'SeedMatchR guide sequence data. '*4).encode()
        r=lib.import_document(raw,'TEST.txt',{'title':'<img src=x onerror=alert(1)>','source_url':'https://example.org/source'})
        with patch('literature.get_library',return_value=lib):
            _,html=request('GET','/library/'+r['document']['id'])
        self.assertNotIn(b'<script>alert(',html);self.assertIn(b'&lt;script&gt;',html)

    def test_http_import_keeps_original_bytes(self):
        lib=self.empty('wire_import');raw=b'TEST_ONLY input. A source URL is not independent validation.\n'*3
        payload={'content_base64':base64.b64encode(raw).decode(),'filename':'wire.txt','title':'TEST_ONLY wire import',
                 'source_url':'https://example.org/test','source_kind':'official_documentation'}
        with patch('literature.get_library',return_value=lib):
            status,body=request('POST','/api/library-upload',payload);self.assertEqual(status,200)
            doc=json.loads(body)['document'];status,body=request('GET',doc['original_url'])
            self.assertEqual(body,raw)
            status,body=request('POST','/api/library-import',{'content_base64':base64.b64encode(lib.export_bundle()).decode()})
            self.assertEqual(status,200);self.assertTrue(json.loads(body)['same_version'])

    def test_demo_account_block_preserves_pending_unit(self):
        import library_demo
        from model_client import ModelError
        from core import config
        calls=[];cfg=config();cfg.update(api_key='TEST_ONLY_SECRET',model='TEST')
        def fail(p):
            calls.append(p)
            raise ModelError('TEST_ONLY_SECRET',provider_message='TEST_ONLY_SECRET',provider_code='SetLimitExceeded',http_status=403)
        def controlled(**kw):return Conversation(transport=fail,**kw)
        with patch('library_demo.HOME',self.root/'demo_root'),patch('library_demo.get_library',return_value=self.lib),\
             patch('literature.get_library',return_value=self.lib),patch('library_demo.Conversation',side_effect=controlled),\
             patch.dict(library_demo.STATE,{'status':'RUNNING','run_id':'TEST_ONLY_demo','completed':0,'total':2},clear=True),redirect_stdout(io.StringIO()):
            library_demo.run(lambda:cfg,'TEST_ONLY_demo')
            records=json.loads((self.root/'demo_root/literature_runs/TEST_ONLY_demo/results.json').read_text(encoding='utf-8'))
            self.assertEqual(len(calls),1);self.assertEqual(library_demo.STATE['status'],'BLOCKED_ACCOUNT')
            self.assertEqual([r['status'] for r in records],['FAILED','NOT_STARTED'])
            package=library_demo.export_zip()
            with ZipFile(io.BytesIO(package)) as z:
                for name in z.namelist():self.assertNotIn(b'TEST_ONLY_SECRET',z.read(name))


if __name__=='__main__':unittest.main(verbosity=2)
