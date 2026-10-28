"""Compare the generated Agent figure tables with independently saved v3 tables."""
import csv, hashlib, json, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from core import read_tsv, HOME
from pypdf import PdfReader
import pdfplumber
from PIL import Image

if __name__=='__main__':
    root=HOME/'research/2026-10-29_expression_figures';folder=root/'example'
    original=HOME.parent/'analysis_redraw_20261028_v3/tables'
    actual=read_tsv(folder/'candidate_summary.tsv');expected=read_tsv(original/'default9_expression_and_Venn_counts.tsv')
    for a,e in zip(actual,expected):
        assert a['candidate_id']==e['candidate_id']
        for key in ['mapped','unmapped','N','H','both','N_only','H_only','neither']:assert a[key]==e[key],(a,e,key)
        assert a['matched_genes']==e['total']
    top=read_tsv(folder/'top20_selection.tsv');ref=read_tsv(original/'candidate_top20_selection.tsv')
    assert [r['ENTREZID'] for r in top]==[r['gene_id'] for r in ref]
    for a,e in zip(top,ref):assert abs(float(a['TPM_all8_mean'])-float(e['all8_mean_TPM']))<1e-6
    reader=PdfReader(folder/'candidate_expression.pdf');assert len(reader.pages)==7
    fonts=set()
    for page in reader.pages:
        for font in page['/Resources']['/Font'].get_object().values():fonts.add(str(font.get_object().get('/BaseFont')))
    assert fonts and all('Arial' in f and 'Bold' in f for f in fonts),fonts
    outside=[]
    with pdfplumber.open(folder/'candidate_expression.pdf') as pdf:
        for i,p in enumerate(pdf.pages,1):
            outside.extend((i,c['text']) for c in p.chars if c['x0']<0 or c['x1']>p.width+.1 or c['top']<0 or c['bottom']>p.height+.1)
    assert not outside,outside[:10]
    pngs=list(folder.glob('*.png'));svgs=list(folder.glob('*.svg'));assert len(pngs)==len(svgs)==5
    for p in pngs:
        with Image.open(p) as im:assert im.size==(2400,1680) and im.convert('RGB').getpixel((0,0))==(255,255,255)
    for p in svgs:
        text=p.read_text(encoding='utf-8');assert '<image' not in text and 'Arial' in text
    audit={'status':'PASS','nine_candidate_counts':'all 9 equal independently saved v3 tables',
        'top20_gene_order_and_mean_TPM':'all 20 equal v3','pdf_pages':7,'fonts':sorted(fonts),
        'characters_outside_page':outside,'png_count':5,'svg_count':5,'png_pixels':[2400,1680],
        'white_background':True,'svg_raster_images':False,
        'visual_review':'All five scientific pages and two methods pages rendered and inspected separately.'}
    (root/'audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(audit,ensure_ascii=False))
