"""Extract the actually acquired institutional author manuscript; retain the initial abstract."""
import hashlib,json,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from literature import extract
P=ROOT/'references/vegfa_experiments_20261024'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def main():
 raw=(P/'kleinman2008_author_manuscript.pdf').read_bytes()
 result=extract(raw,'kleinman2008_author_manuscript.pdf',use_cache=False)
 assert len(result['pages'])==15
 assert '10.1038/nature06765' in result['pages'][0]['text']
 assert 'Supplementary information not included' in result['pages'][0]['text']
 assert 'Chemical siRNA sequences and modifications are listed in the Supplementary Table' in result['pages'][13]['text']
 code=(ROOT/'pdf_text_worker.py').read_text(encoding='utf-8').replace('\r\n','\n').encode()
 cache={'source_sha256':sha(raw),'extraction_code_sha256':sha(code),'result':result,
        'scope_note':'Actual PDF pages 1-15; institutional author manuscript, not copy of record. Supplementary information absent.'}
 cache_path=P/'kleinman2008_author_manuscript.pdf.pages.json'
 cache_path.write_text(json.dumps(cache,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
 manifest=json.loads((P/'sources.json').read_text(encoding='utf-8'))
 if not (P/'sources_initial_abstract_only.json').exists():
  (P/'sources_initial_abstract_only.json').write_bytes((P/'sources.json').read_bytes())
 old=manifest['sources'][2]
 manifest['sources'][2]={**old,'file':'kleinman2008_author_manuscript.pdf','source_kind':'article_full_text',
  'source_url':'https://www.digitalgreensboro.org/record/9872/files/facultystaff_9887_PDF.pdf',
  'source_version':'Institutional author manuscript; not publisher copy of record; no supplementary information',
  'source_note':'Actual 15-page PDF text layer, including Online Methods on pages 13-15. Page 14 visually checked. No supplementary sequence table; no invented sequences or CNV endpoint. Initial PMC abstract and failed acquisition receipts retained separately.',
  'sha256':sha(raw),'pages_file':cache_path.name,'pages_sha256':sha(cache_path.read_bytes()),
  'acquired_utc':datetime.fromtimestamp((P/'kleinman2008_author_manuscript.pdf').stat().st_mtime,timezone.utc).isoformat(),
  'acquisition_time_basis':'Original downloaded PDF filesystem last-write timestamp, captured during preparation; download receipt omitted time'}
 (P/'sources.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
 print(json.dumps({'pages':15,'source_sha256':sha(raw),'extractor':result['extractor'],'supplement_obtained':False}))
if __name__=='__main__':main()
