"""Acquire only the three requested experimental articles from official PMC XML."""
import hashlib,json,urllib.request,xml.etree.ElementTree as ET
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'references/vegfa_experiments_20261024'
PAPERS=[('chen2013','3726441','10.2147/IJN.S39622'),('osipova2020','7022581','10.3390/pharmaceutics12010039'),('kleinman2008','2642938','10.1038/nature06765')]

def text(element):return ' '.join(''.join(element.itertext()).split()) if element is not None else ''

def main():
 OUT.mkdir(exist_ok=True);receipts=[];sources=[]
 if (OUT/'sources.json').exists():raise SystemExit('Preserve existing acquisition; use a new directory for another attempt.')
 for key,pmc,doi in PAPERS:
  url='https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id='+pmc
  receipt={'id':key,'pmcid':'PMC'+pmc,'doi':doi,'requested_url':url,'accessed_utc':datetime.now(timezone.utc).isoformat(),'direct_pmc_web_read':'browser verification page, not article text; no CAPTCHA interaction'}
  try:
   request=urllib.request.Request(url,headers={'User-Agent':'siRNA-GPT-scoped-evidence-audit/1.0'})
   with urllib.request.urlopen(request,timeout=40) as response:
    raw=response.read(5_000_001);receipt.update(http_status=response.status,final_url=response.url,content_type=response.headers.get('Content-Type'))
   if len(raw)>5_000_000:raise ValueError('Unexpectedly large response')
   article=ET.fromstring(raw).find('.//article')
   if article is None:raise ValueError('No article XML')
   actual_doi=[text(x) for x in article.findall('.//article-id') if x.get('pub-id-type')=='doi']
   if doi.casefold() not in [x.casefold() for x in actual_doi]:raise ValueError('DOI mismatch')
   (OUT/(key+'.xml')).write_bytes(raw)
   title=text(article.find('.//article-title'));rows=[]
   def walk(node,path,section=''):
    if node.tag=='sec':section=text(node.find('title')) or section
    if node.tag in ('p','table-wrap','fig'):
     value=text(node)
     if value:rows.append({'locator':'xml-block-%04d'%(len(rows)+1),'xpath':path,'original_id':node.get('id'),'section':section,'type':node.tag,'text':value})
     if node.tag in ('table-wrap','fig'):return
    counts={}
    for child in node:
     counts[child.tag]=counts.get(child.tag,0)+1
     walk(child,path+'/'+child.tag+'[%d]'%counts[child.tag],section)
   for tag in ('abstract','body'):
    nodes=article.findall('.//'+tag) if tag=='abstract' else article.findall('body')
    for i,node in enumerate(nodes):walk(node,('/article/front[1]/article-meta[1]/' if tag=='abstract' else '/article/')+tag+'[%d]'%(i+1),tag)
   full_body=article.find('body') is not None
   scope='PMC full article XML abstract/body text and available captions/table text' if full_body else 'PMC abstract-only XML; full body not supplied'
   extracted=title+'\nDOI: '+doi+'\nSource: '+scope+'. No PDF page numbers or image reading.\n\n'
   extracted+='\n\n'.join('['+r['locator']+'; '+r['section']+'; original-id='+str(r['original_id'])+']\n'+r['text'] for r in rows)
   (OUT/(key+'_text.txt')).write_text(extracted,encoding='utf-8',newline='\n')
   (OUT/(key+'_locators.json')).write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
   receipt.update(status='FULL_ARTICLE_XML_ACQUIRED' if full_body else 'ABSTRACT_ONLY_XML_ACQUIRED',body_present=full_body,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),title=title,blocks=len(rows),pdf_acquired=False)
   source={'file':key+'_text.txt','title':title,'doi':doi,'source_url':'https://pmc.ncbi.nlm.nih.gov/articles/PMC'+pmc+'/',
    'source_kind':'article_full_text' if full_body else 'abstract','source_version':'Published article XML from PMC; acquired 2026-10-24',
    'source_note':scope+'; no PDF page numbers or image interpretation. XML locator map retained.',
    'sha256':hashlib.sha256(extracted.encode()).hexdigest(),'original_xml_file':key+'.xml','original_xml_sha256':receipt['sha256'],'acquired_utc':receipt['accessed_utc']}
   sources.append(source)
  except Exception as error:receipt.update(status='FAILED',error=str(error))
  receipts.append(receipt)
  (OUT/'acquisition_receipt.json').write_text(json.dumps(receipts,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
 (OUT/'sources.json').write_text(json.dumps({'scope':'Only the three requested VEGFA-related experimental articles; no original-nine changes','sources':sources},ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
 print(json.dumps([{'id':r['id'],'status':r['status'],'bytes':r.get('bytes'),'blocks':r.get('blocks'),'error':r.get('error')} for r in receipts]))

if __name__=='__main__':main()
