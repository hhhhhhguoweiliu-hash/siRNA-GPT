"""Acquire only three core OA papers and reuse pinned Task A official sources."""
import concurrent.futures
import hashlib
import io
import json
import sys
import tarfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'references/sirna_library'
RAW = OUT/'acquisition'
OUT.mkdir(exist_ok=True)
RAW.mkdir(exist_ok=True)
PAPERS = [
    ('oligoformer', 'PMC11494384', 'OligoFormer: an accurate and robust prediction method for siRNA design', '10.1093/bioinformatics/btae577'),
    ('seedmatchr', 'PMC10799297', 'SeedMatchR: identify off-target effects mediated by siRNA seed regions in RNA-seq experiments', '10.1093/bioinformatics/btae011'),
    ('sidirect', 'PMC2791777', 'siDirect 2.0: updated software for designing functional siRNA with reduced seed-dependent off-target effect', '10.1186/1471-2105-10-392'),
]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def fetch(url, maximum=26_000_000):
    request = urllib.request.Request(url, headers={'User-Agent': 'siRNA-GPT-small-library/1.0 (three open-access tool papers)'})
    with urllib.request.urlopen(request, timeout=35) as f:
        raw = f.read(maximum+1)
        if len(raw) > maximum:
            raise ValueError('download exceeds scoped size limit')
        return raw, f.url


def paper(item):
    slug, pmcid, title, doi = item
    record = {'slug':slug, 'pmcid':pmcid, 'title':title, 'doi':doi, 'attempts':[],
              'requested_at_utc':datetime.now(timezone.utc).isoformat()}
    oa = 'https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id='+pmcid
    try:
        raw, final = fetch(oa)
        (RAW/(slug+'_oa.xml')).write_bytes(raw)
        tree = ET.fromstring(raw)
        links = tree.findall('.//link')
        entry = tree.find('.//record')
        record['license'] = entry.get('license') if entry is not None else None
        record['attempts'].append({'url':oa, 'final_url':final, 'status':'METADATA_FETCHED', 'sha256':sha(raw)})
        pdf_link = next((l.get('href') for l in links if l.get('format')=='pdf'), None)
        tgz_link = next((l.get('href') for l in links if l.get('format')=='tgz'), None)
        pdf = None
        if pdf_link:
            url = pdf_link.replace('ftp://','https://')
            pdf, final = fetch(url,8_000_000)
            record['attempts'].append({'url':url,'final_url':final,'status':'DOWNLOADED','sha256':sha(pdf)})
        elif tgz_link:
            url=tgz_link.replace('ftp://','https://')
            archive, final=fetch(url)
            record['attempts'].append({'url':url,'final_url':final,'status':'DOWNLOADED_OA_PACKAGE','sha256':sha(archive)})
            with tarfile.open(fileobj=io.BytesIO(archive),mode='r:gz') as tar:
                members=[m for m in tar.getmembers() if m.isfile() and m.name.lower().endswith('.pdf') and Path(m.name).name.lower() in [doi.split('/')[-1]+'.pdf','1471-2105-10-392.pdf']]
                if not members:
                    members=[m for m in tar.getmembers() if m.isfile() and m.name.lower().endswith('.pdf') and not any(s in m.name.lower() for s in ['supp','additional','btae577_s','btae011_s'])]
                if len(members)==1 and members[0].size<=8_000_000:
                    pdf=tar.extractfile(members[0]).read()
                    record['oa_package_pdf_member']=members[0].name
        if pdf is not None and pdf.startswith(b'%PDF-'):
            from pypdf import PdfReader
            reader=PdfReader(io.BytesIO(pdf),strict=True)
            if sum(len(p.extract_text() or '') for p in reader.pages)<500:
                raise ValueError('no usable paper PDF text layer')
            filename=slug+'_paper.pdf'
            (OUT/filename).write_bytes(pdf)
            record.update(status='PDF_TEXT_LAYER_VERIFIED',file=filename,bytes=len(pdf),sha256=sha(pdf),pages=len(reader.pages))
            return record
    except Exception as error:
        record['attempts'].append({'status':'FAILED','error':str(error)})
    # Official full-text XML fallback is explicitly not a downloaded PDF.
    try:
        url='https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id='+pmcid
        api='https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id='+pmcid.removeprefix('PMC')
        raw, final=fetch(api,4_000_000)
        tree=ET.fromstring(raw)
        body=tree.find('.//body')
        if body is None:
            raise ValueError('official response lacks full-text body')
        text='\n\n'.join(' '.join(n.itertext()).strip() for n in tree.findall('.//abstract')+list(body))
        if len(text)<1000:
            raise ValueError('full text was not obtained')
        (RAW/(slug+'_fulltext.xml')).write_bytes(raw)
        filename=slug+'_paper_extracted_text.txt'
        content=(title+'\nDOI: '+doi+'\n\n'+text+'\n').encode('utf-8')
        (OUT/filename).write_bytes(content)
        record['attempts'].append({'url':api,'final_url':final,'status':'FULL_TEXT_XML_FETCHED','sha256':sha(raw)})
        record.update(status='EXTRACTED_FULL_TEXT_NO_PDF',file=filename,bytes=len(content),sha256=sha(content),pages=None)
    except Exception as error:
        record['attempts'].append({'status':'FAILED','error':str(error)})
        record['status']='NOT_OBTAINED'
    return record


if __name__=='__main__':
    if (OUT/'sources.json').exists():
        raise SystemExit('Preserve the existing acquisition snapshot. Use a new output directory for any new acquisition; do not overwrite the curated sources or PDF page cache.')
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        records=list(pool.map(paper,PAPERS))
    sources=[]
    for r in records:
        if r['status']=='NOT_OBTAINED':continue
        sources.append({'file':r['file'],'sha256':r['sha256'],'title':r['title'],'doi':r['doi'],
            'source_url':'https://pmc.ncbi.nlm.nih.gov/articles/'+r['pmcid']+'/',
            'source_kind':'article_full_text','source_version':r['doi'],
            'source_note':r['status']+'; '+str(r.get('license') or 'license not exposed in OA response')})
    pinned=[
        ('official_tools/OligoFormer/README.md','oligoformer_official_readme.txt','OligoFormer official README (pinned historical version)',
         'https://github.com/lulab/OligoFormer/blob/e2f53ad63387bbe166bf123949151e2bc9bf6ec3/README.md','official_documentation','e2f53ad63387bbe166bf123949151e2bc9bf6ec3'),
        ('official_tools/OligoFormer/scripts/infer.py','oligoformer_official_infer.txt','OligoFormer official inference source, including score scaling and input context',
         'https://github.com/lulab/OligoFormer/blob/e2f53ad63387bbe166bf123949151e2bc9bf6ec3/scripts/infer.py','official_source_code','e2f53ad63387bbe166bf123949151e2bc9bf6ec3'),
        ('official_tools/SeedMatchR_1.1.1/man/get_seed.Rd','seedmatchr_111_get_seed.txt','SeedMatchR 1.1.1 official get_seed documentation',
         'https://github.com/cran/SeedMatchR/blob/b462d4a00520172622f9d8a5a8842d34442c2e68/man/get_seed.Rd','official_documentation','1.1.1'),
        ('official_tools/SeedMatchR_1.1.1/R/get_seed.R','seedmatchr_111_get_seed_source.txt','SeedMatchR 1.1.1 official seed definitions source (g2-g8)',
         'https://github.com/cran/SeedMatchR/blob/b462d4a00520172622f9d8a5a8842d34442c2e68/R/get_seed.R','official_source_code','1.1.1'),
    ]
    with ZipFile(ROOT/'research/2026-10-23_candidate_provenance/historical_evidence.zip') as z:
        for old,name,title,url,kind,version in pinned:
            raw=z.read(old)
            (OUT/name).write_bytes(raw)
            sources.append({'file':name,'sha256':sha(raw),'title':title,'source_url':url,'source_kind':kind,
                            'source_version':version,'source_note':'Recovered historical official bytes, independently compared to pinned official sources in Task A; not a paper PDF'})
    p=ROOT/'research/2026-10-23_candidate_provenance/README.md'
    raw=p.read_bytes();name='project_candidate_provenance_20261023.txt';(OUT/name).write_bytes(raw)
    sources.append({'file':name,'sha256':sha(raw),'title':'本项目默认九条候选来源核查（历史计算记录，不是文献结论）',
        'source_url':'https://github.com/hhhhhhguoweiliu-hash/siRNA-GPT/blob/1e4fe57a059fbf19cf32b4685cc249a3d297e98c/research/2026-10-23_candidate_provenance/README.md',
        'source_kind':'project_record','source_version':'1e4fe57','source_note':'Project provenance audit of historical imports; no new inference or biological experiment'})
    (OUT/'acquisition_receipt.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (OUT/'sources.json').write_text(json.dumps({'scope':'three tool papers, pinned official documentation and project provenance only',
        'not_an_exhaustive_sirna_library':True,'sources':sources},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for r in records:print(r['slug'],r['status'],r.get('bytes'),r.get('pages'))
    print('Indexed source declarations:',len(sources))
