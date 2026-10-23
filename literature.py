"""Small single-owner document library. SQLite FTS5, originals and page locators.

No embeddings, scientific scoring, OCR, network retrieval or model calls here.
User metadata is a declaration; importing a DOI does not validate a claim.
"""
import base64
import hashlib
import io
import json
import re
import sqlite3
import subprocess
import sys
import threading
import uuid
import zipfile
from datetime import datetime, timezone
from contextlib import closing
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
FORMAT = 'sirna-small-library-v1'
INDEX_VERSION = 'fts5-bilingual-v1'
CHUNK_SIZE, OVERLAP = 1800, 200
KINDS = {
    'article_full_text': '文献全文（文字部分）', 'abstract': '文献摘要',
    'official_documentation': '官方工具文档', 'official_source_code': '官方工具源码',
    'project_setting': '项目设置说明', 'project_record': '本地计算记录（历史来源核查）',
}
# Explicit query expansion, not model translation or a biological predictor.
LEXICON = [
    (['OligoFormer', '效力', '敲低', '分数', '概率'], ['OligoFormer', 'efficacy', 'score', 'knockdown', 'prediction', '1.341', 'scaled']),
    (['输入', '上下文'], ['input', 'siRNA', 'mRNA', 'context', '19', '57']),
    (['链方向', '双链', '配对', '核心', 'guide', 'passenger', '设计窗口', 'siDirect'], ['guide', 'passenger', 'antisense', 'sense', 'siDirect', 'overhang', '19', '21', '23']),
    (['SeedMatchR', '种子', 'seed', 'mer7m8', '脱靶'], ['SeedMatchR', 'seed', 'mer7m8', 'off-target', 'matches', 'UTR']),
    (['位点', '基因数', '错配'], ['matches', 'counts', 'gene', 'mismatches', 'indels']),
    (['TPM', 'RNA-seq', '表达', '未转染', '常氧', '缺氧'], ['TPM', 'RNA-seq', 'expression', 'baseline', 'untreated', 'perturbation']),
    (['来源', '历史', '重新计算', '版本'], ['historical', 'version', 'source', 'reference', 'import']),
]
_SINGLETON = None
_SINGLETON_LOCK = threading.RLock()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def tokens(text):
    english = re.findall(r'[a-z0-9]+(?:[.-][a-z0-9]+)*', text.casefold())
    english_stop={'the','and','or','is','are','what','how','can','this','that','please','test','test_only','question','explain','result','results','search','do','does','one','two','only','with','from'}
    english=[w for w in english if w not in english_stop]
    chinese = [s[i:i+2] for s in re.findall(r'[\u4e00-\u9fff]+', text) for i in range(len(s)-1)]
    stop = {'本项', '项目', '请给', '给出', '已经', '可以', '如何', '怎样', '什么', '这个', '我们', '多少', '分别'}
    return english + [w for w in chinese if w not in stop]


def query_terms(query):
    if not isinstance(query, str) or not 1 <= len(query.strip()) <= 2000:
        raise ValueError('请输入1至2000字的检索问题。')
    terms = tokens(query)
    for triggers, expanded in LEXICON:
        if any(t.casefold() in query.casefold() for t in triggers):
            terms.extend(expanded)
    return list(dict.fromkeys(t.casefold() for t in terms))[:60]


def chunks(pages):
    result = []
    for page in pages:
        text = page['text']
        start, ordinal = 0, 1
        while start < len(text):
            end = min(start + CHUNK_SIZE, len(text))
            if end < len(text):
                boundary = max(text.rfind('\n', start+CHUNK_SIZE//2, end), text.rfind('. ', start+CHUNK_SIZE//2, end))
                if boundary > start:
                    end = boundary+1
            value = text[start:end]
            if value.strip():
                prefix = 'p%04d' % page['page'] if page['page'] is not None else 'text'
                result.append({'chunk_id': prefix+'-c%03d' % ordinal, 'page': page['page'],
                               'start': start, 'end': end, 'text': value, 'sha256': digest(value.encode('utf-8'))})
            if end == len(text):
                break
            start, ordinal = max(start+1, end-OVERLAP), ordinal+1
    return result


def extract(raw, filename, use_cache=True):
    suffix = Path(filename).suffix.casefold()
    if not raw or len(raw) > 8_000_000:
        raise ValueError('文件为空或超过8MB。')
    if suffix == '.pdf':
        if not raw.startswith(b'%PDF-'):
            raise ValueError('PDF文件头无效，未导入。')
        # Bundled originals have a reproducible page-text cache, avoiding repeated
        # vector-graphics parsing on the small hosted instance. Verify both files.
        seed=ROOT/'references/sirna_library'
        if use_cache and (seed/'sources.json').exists():
            for source in json.loads((seed/'sources.json').read_text(encoding='utf-8'))['sources']:
                if source.get('sha256')==digest(raw) and source.get('pages_file'):
                    cache=(seed/source['pages_file']).read_bytes()
                    cached=json.loads(cache)
                    code_hash=digest((ROOT/'pdf_text_worker.py').read_text(encoding='utf-8').replace('\r\n','\n').encode('utf-8'))
                    if digest(cache)==source['pages_sha256'] and cached['source_sha256']==digest(raw) and cached['extraction_code_sha256']==code_hash:
                        return cached['result']
        try:
            p = subprocess.run([sys.executable, str(ROOT/'pdf_text_worker.py')], input=raw,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=25)
            value = json.loads(p.stdout.decode('utf-8'))
        except subprocess.TimeoutExpired:
            raise ValueError('PDF文字提取超时，未导入；请提供更小的文字版文件。')
        except (ValueError, UnicodeError):
            raise ValueError('PDF提取进程未正常完成，未导入。')
        if p.returncode or value.get('error'):
            raise ValueError('PDF未导入：' + value.get('error', '解析失败'))
        value['parser_warnings'] = p.stderr.decode('utf-8',errors='replace')[:2000]
        return value
    if suffix not in ('.txt', '.md'):
        raise ValueError('只支持文字PDF、UTF-8 TXT或Markdown文本。')
    try:
        value = raw.decode('utf-8-sig')
    except UnicodeError:
        raise ValueError('文本须为UTF-8编码，未导入。')
    if '\x00' in value or len(value.strip()) < 30 or len(value) > 1_000_000:
        raise ValueError('文本过短、过长或含无效字符，未导入。')
    return {'pages': [{'page': None, 'text': value}], 'extractor': 'utf8-text-v1',
            'scope': 'TEXT_FILE_NO_PDF_PAGE_NUMBERS', 'pages_without_text': []}


class Library:
    def __init__(self, root=None, seed_root=None):
        self.root = Path(root or ROOT/'literature_library')
        self.root.mkdir(parents=True, exist_ok=True)
        self.documents = self.root/'documents'
        self.documents.mkdir(exist_ok=True)
        self.lock = threading.RLock()
        self.db = self.root/'index.sqlite'
        self.seed_root = Path(seed_root) if seed_root else None
        self._indexed_signature = None
        if self.seed_root and (self.seed_root/'sources.json').is_file():
            for source in json.loads((self.seed_root/'sources.json').read_text(encoding='utf-8'))['sources']:
                raw = (self.seed_root/source['file']).read_bytes()
                if digest(raw) != source['sha256']:
                    raise ValueError('内置文献文件校验失败：'+source['file'])
                self.import_document(raw, source['file'], source)
        self.rebuild()

    def _metadata(self):
        return [json.loads(p.read_text(encoding='utf-8')) for p in sorted(self.documents.glob('*/metadata.json'))]

    def _prepare(self, raw, filename, metadata):
        filename = Path(str(filename).replace('\\', '/')).name
        title = str(metadata.get('title', '')).strip()
        kind = metadata.get('source_kind', 'article_full_text')
        url = str(metadata.get('source_url', '')).strip()
        doi = str(metadata.get('doi', '')).strip().removeprefix('https://doi.org/')
        if not 1 <= len(title) <= 250 or kind not in KINDS:
            raise ValueError('请填写题名和有效的来源类别。')
        if len(url) > 2000 or (url and (urlsplit(url).scheme != 'https' or urlsplit(url).username or urlsplit(url).password)):
            raise ValueError('来源链接须为不含账号密码的HTTPS链接。')
        if doi and (len(doi) > 200 or not re.fullmatch(r'10\.\d{4,9}/\S+', doi)):
            raise ValueError('DOI格式无效。')
        if not url and not doi and kind not in ('project_setting', 'project_record'):
            raise ValueError('请填写DOI或来源链接；上传本身不认证来源声明。')
        extracted = extract(raw, filename)
        h = digest(raw)
        doc = {'id': h[:24], 'sha256': h, 'filename': filename, 'title': title, 'doi': doi,
               'source_url': url, 'source_kind': kind, 'source_label': KINDS[kind],
               'source_note': str(metadata.get('source_note', ''))[:1000],
               'source_version': str(metadata.get('source_version', ''))[:100],
               'metadata_status': 'SOURCE_DECLARATION_NOT_INDEPENDENT_SCIENTIFIC_REVIEW',
               'bytes': len(raw), 'added_at': datetime.now(timezone.utc).isoformat(), **extracted}
        return doc

    def _store(self, doc, raw):
        folder = self.documents/doc['id']
        folder.mkdir(exist_ok=True)
        suffix = '.pdf' if doc['filename'].casefold().endswith('.pdf') else '.txt'
        original=folder/('original'+suffix)
        temporary=folder/('pending_'+uuid.uuid4().hex)
        temporary.write_bytes(raw);temporary.replace(original)
        temporary=folder/('pending_'+uuid.uuid4().hex)
        temporary.write_bytes(canonical(doc));temporary.replace(folder/'metadata.json')

    def import_document(self, raw, filename, metadata):
        with self.lock:
            identity = digest(raw)[:24]
            existing = self.documents/identity/'metadata.json'
            if existing.exists():
                old = json.loads(existing.read_text(encoding='utf-8'))
                if old['sha256'] != digest(raw):
                    raise ValueError('文件标识冲突，未覆盖原件。')
                return {'status': 'ALREADY_PRESENT', 'document': self.public_document(old), 'version': self.version()}
            docs = self._metadata()
            if len(docs) >= 40 or sum(d['bytes'] for d in docs)+len(raw) > 20_000_000:
                raise ValueError('当前小文库上限为40份、原件共20MB；请先导出保存。')
            doc = self._prepare(raw, filename, metadata)
            self._bundle_bytes(docs+[doc],{doc['id']:raw})  # Admit only a library that can be exported intact.
            self._store(doc, raw)
            self._indexed_signature = None
            self.rebuild()
            return {'status': 'IMPORTED', 'document': self.public_document(doc), 'version': self.version()}

    @staticmethod
    def public_document(doc):
        return {k: v for k, v in doc.items() if k != 'pages'} | {'page_count': len(doc['pages']),
            'chunk_count': len(chunks(doc['pages'])), 'url': '/library/'+doc['id'],
            'original_url': '/api/library/original/'+doc['id']}

    def version(self, documents=None):
        entries=self._metadata() if documents is None else sorted(documents,key=lambda d:d['id'])
        docs = [{k:d[k] for k in ('id', 'sha256', 'title', 'doi', 'source_url', 'source_kind', 'source_version', 'source_note', 'extractor', 'scope')}
                | {'pages_sha256': digest(canonical(d['pages']))} for d in entries]
        code_hash=digest(Path(__file__).read_text(encoding='utf-8').replace('\r\n','\n').encode('utf-8'))
        return digest(canonical({'documents': docs, 'index_version': INDEX_VERSION,
            'retrieval_code_sha256':code_hash,'chunk_size': CHUNK_SIZE, 'overlap': OVERLAP}))

    def catalogue(self):
        with self.lock:
            return {'version': self.version(), 'index_version': INDEX_VERSION,
                    'documents': [self.public_document(d) for d in self._metadata()],
                    'storage': '当前实例临时文件；重启或部署可能丢失。请导出文库并自行保存。',
                    'source_boundary': '来源类别按声明记录；全文仅索引文字，不读取图像或认证科学结论。'}

    def rebuild(self):
        with self.lock:
            signature = self.version()
            if self._indexed_signature == signature and self.db.exists():
                return signature
            with closing(sqlite3.connect(self.db)) as db:
                db.execute('DROP TABLE IF EXISTS search_index')
                db.execute('CREATE VIRTUAL TABLE search_index USING fts5(terms, title, document_id UNINDEXED, chunk_id UNINDEXED, text UNINDEXED, page UNINDEXED, start UNINDEXED, end UNINDEXED)')
                for doc in self._metadata():
                    for c in chunks(doc['pages']):
                        db.execute('INSERT INTO search_index VALUES(?,?,?,?,?,?,?,?)',
                                   (' '.join(tokens(c['text'])), ' '.join(tokens(doc['title'])), doc['id'], c['chunk_id'], c['text'], c['page'], c['start'], c['end']))
                db.commit()
            self._indexed_signature = signature
            return signature

    def search(self, query, limit=5):
        terms = query_terms(query)
        with self.lock:
            version = self.rebuild()
            # The authorized library is not a clinical dosing/outcome source.
            if re.search(r'患者|视力改善|临床给药', query):
                return {'status': 'NO_RESULTS', 'question': query, 'query_terms': terms, 'version': version, 'hits': [], 'sources': [],
                        'reason': '此小文库不支持本项目患者疗效或临床给药结论。'}
            if type(limit) is not int or not 1 <= limit <= 8:
                raise ValueError('检索条数应为1至8。')
            expression = ' OR '.join('"'+t.replace('"','""')+'"' for t in terms)
            with closing(sqlite3.connect(self.db)) as db:
                db.row_factory = sqlite3.Row
                found = list(db.execute('SELECT *, bm25(search_index,1.0,1.5) AS rank FROM search_index WHERE search_index MATCH ? ORDER BY rank,document_id,chunk_id LIMIT 40', (expression,))) if terms else []
            docs = {d['id']: d for d in self._metadata()}
            named=[name for name in ('oligoformer','seedmatchr','sidirect') if name in query.casefold()]
            if len(named)==1:
                # Explicit tool-name intent takes precedence over incidental
                # Chinese phrase overlap in long project reports.
                found.sort(key=lambda r:(named[0] not in docs[r['document_id']]['title'].casefold(),r['rank'],r['document_id'],r['chunk_id']))
            hits, per_doc = [], {}
            for row in found:
                d = docs[row['document_id']]
                if per_doc.get(d['id'], 0) >= 2:
                    continue
                per_doc[d['id']] = per_doc.get(d['id'], 0)+1
                c = {k: row[k] for k in ('chunk_id', 'text', 'page', 'start', 'end')}
                hits.append({**c, 'document_id': d['id'], 'file_sha256': d['sha256'], 'chunk_sha256': digest(c['text'].encode('utf-8')),
                             'title': d['title'], 'doi': d['doi'], 'source_kind': d['source_kind'], 'kind': d['source_label'],
                             'source_url': d['source_url'], 'source_version': d['source_version'], 'library_version': version,
                             'source_note':d['source_note'],'extraction_scope':d['scope'],
                             'metadata_status':d['metadata_status'],
                             'url': '/library/'+d['id']+'#'+c['chunk_id'],
                             'original_url': '/api/library/original/'+d['id']+('#page='+str(c['page']) if c['page'] else ''),
                             'locator': ('PDF第'+str(c['page'])+'页，' if c['page'] else '文本，')+'片段'+c['chunk_id']})
                if len(hits) >= limit:
                    break
            return {'status': 'OK' if hits else 'NO_RESULTS', 'question': query, 'query_terms': terms,
                    'version': version, 'index_version': INDEX_VERSION, 'hits': hits,
                    'sources': [{k:h[k] for k in h if k != 'text'} for h in hits]}

    def document(self, identity):
        if not re.fullmatch(r'[a-f0-9]{24}', identity):
            raise ValueError('文献编号无效。')
        with self.lock:
            folder = self.documents/identity
            try:
                doc = json.loads((folder/'metadata.json').read_text(encoding='utf-8'))
            except FileNotFoundError:
                raise ValueError('未找到该文献；实例重启后可能需要重新导入文库。')
            path = folder/('original.pdf' if doc['filename'].casefold().endswith('.pdf') else 'original.txt')
            if digest(path.read_bytes()) != doc['sha256']:
                raise ValueError('文献原件校验失败，不能作为引用依据。')
            return doc, path, chunks(doc['pages'])

    def _bundle_bytes(self,docs,overrides=None):
            overrides=overrides or {}
            docs=sorted(docs,key=lambda d:d['id'])
            payload = {'format': FORMAT, 'version': self.version(docs), 'index_spec': {'version': INDEX_VERSION,
                       'chunk_size': CHUNK_SIZE, 'overlap': OVERLAP, 'rebuild': 'literature.Library.rebuild'}, 'documents': docs}
            memory = io.BytesIO()
            with zipfile.ZipFile(memory, 'w', zipfile.ZIP_DEFLATED) as z:
                z.writestr('library.json', canonical(payload))
                for d in docs:
                    suffix='.pdf' if d['filename'].casefold().endswith('.pdf') else '.txt'
                    content=overrides[d['id']] if d['id'] in overrides else self.document(d['id'])[1].read_bytes()
                    z.writestr('originals/'+d['id']+suffix,content)
            if memory.tell() > 24_000_000:
                raise ValueError('合并后文库导出会超过24MB，未加入新资料；本版不拆分或丢弃文件。')
            return memory.getvalue()

    def export_bundle(self):
        with self.lock:
            return self._bundle_bytes(self._metadata())

    def import_bundle(self, raw):
        with self.lock:
            if len(raw) > 24_000_000:
                raise ValueError('文库压缩包不能超过24MB。')
            try:
                with zipfile.ZipFile(io.BytesIO(raw)) as z:
                    names = z.namelist()
                    if len(names) != len(set(names)) or len(names) > 50 or sum(i.file_size for i in z.infolist()) > 55_000_000:
                        raise ValueError('文库文件数、重复路径或解压大小不符合本版要求。')
                    if any(PurePosixPath(n).is_absolute() or '..' in PurePosixPath(n).parts or '\\' in n for n in names):
                        raise ValueError('压缩包包含不安全路径，未导入。')
                    bundle = json.loads(z.read('library.json'))
                    if bundle.get('format') != FORMAT or bundle.get('index_spec', {}).get('version') != INDEX_VERSION:
                        raise ValueError('文库格式或索引版本不受支持。')
                    docs = bundle['documents']
                    if not isinstance(docs, list) or len(docs) > 40:
                        raise ValueError('文库清单无效。')
                    if len({d['id'] for d in docs})!=len(docs):
                        raise ValueError('文库清单包含重复文献编号，未导入。')
                    staged, expected_names = [], {'library.json'}
                    for d in docs:
                        identity = d['id']
                        if not re.fullmatch(r'[a-f0-9]{24}', identity):
                            raise ValueError('文库编号无效。')
                        suffix = '.pdf' if d['filename'].casefold().endswith('.pdf') else '.txt'
                        name = 'originals/'+identity+suffix
                        expected_names.add(name)
                        content = z.read(name)
                        fresh = self._prepare(content, d['filename'], d)
                        if fresh['sha256'] != d['sha256'] or fresh['id'] != identity or fresh['pages'] != d['pages'] or fresh['extractor'] != d['extractor']:
                            raise ValueError('原件或提取文字与文库清单不一致，未导入。')
                        fresh['added_at'] = d.get('added_at', fresh['added_at'])
                        staged.append((fresh, content))
                    if set(names) != expected_names:
                        raise ValueError('文库含不在清单中的文件，未导入。')
            except (zipfile.BadZipFile, KeyError, TypeError, UnicodeError, json.JSONDecodeError):
                raise ValueError('文库压缩包或清单损坏，未导入。')
            existing = {d['id']:d for d in self._metadata()}
            merged = {**existing, **{d['id']:d for d,_ in staged}}
            if len(merged) > 40 or sum(d['bytes'] for d in merged.values()) > 20_000_000:
                raise ValueError('合并后超过小文库上限，未导入。')
            # Verify every item before committing any; never overwrite a prior source declaration.
            for d, _ in staged:
                if d['id'] in existing:
                    fields = ('sha256', 'title', 'doi', 'source_url', 'source_kind', 'source_note', 'source_version', 'pages')
                    if any(d[k] != existing[d['id']][k] for k in fields):
                        raise ValueError('同一原件的来源声明不同，未覆盖已有文献。')
            self._bundle_bytes(list(merged.values()),{d['id']:content for d,content in staged})
            for d, content in staged:
                if d['id'] not in existing:
                    self._store(d, content)
            self._indexed_signature = None
            self.rebuild()
            return {'status': 'IMPORTED', 'documents_in_bundle': len(staged), 'added': len(merged)-len(existing),
                    'version': self.version(), 'bundle_version': bundle['version'],
                    'same_version': self.version() == bundle['version']}


def get_library():
    global _SINGLETON
    with _SINGLETON_LOCK:
        if _SINGLETON is None:
            _SINGLETON = Library(seed_root=ROOT/'references/sirna_library')
        return _SINGLETON


def decode_upload(value, maximum=8_000_000):
    if not isinstance(value, str) or len(value) > maximum*4//3+8:
        raise ValueError('上传内容为空或超过本版大小上限。')
    try:
        raw = base64.b64decode(value, validate=True)
    except (ValueError, __import__('binascii').Error):
        raise ValueError('文件编码无效，请重新选择原文件。')
    if not raw or len(raw) > maximum:
        raise ValueError('上传文件为空或过大。')
    return raw
