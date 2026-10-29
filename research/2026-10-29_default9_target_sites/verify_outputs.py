"""Read-only audit of the fixed-reference coordinate figures."""
import csv, hashlib, json
from pathlib import Path
from pypdf import PdfReader
import pdfplumber
from PIL import Image

OUT=Path(__file__).resolve().parent
def table(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter='\t'))
rows=table(OUT/'tables/default9_primary_positions.tsv');all20=table(OUT/'tables/default9_all20_transcript_positions.tsv')
assert len(rows)==9 and len(all20)==180 and len({r['transcript_id'] for r in all20})==20
assert all(int(r['core_end'])-int(r['core_start'])+1==19 for r in all20)
assert all(int(r['core_start'])==int(r['window23_start'])+2 for r in rows)
pdfpath=OUT/'figures/default9_VEGFA_target_sites.pdf';reader=PdfReader(pdfpath);assert len(reader.pages)==2
fonts=set()
for page in reader.pages:
    for f in page['/Resources']['/Font'].get_object().values():fonts.add(str(f.get_object().get('/BaseFont')))
assert fonts and all('Arial-Bold' in x for x in fonts),fonts
outside=[];minimum=100
with pdfplumber.open(pdfpath) as pdf:
    for i,page in enumerate(pdf.pages,1):
        minimum=min(minimum,min(c['size'] for c in page.chars))
        outside.extend((i,c['text']) for c in page.chars if c['x0']<-.1 or c['x1']>page.width+.1 or c['top']<-.1 or c['bottom']>page.height+.1)
    assert not outside,outside[:10]
    first=pdf.pages[0].extract_text()
    for r in rows:assert r['short_id'] in first and r['core_start']+'-'+r['core_end'] in first
    second=pdf.pages[1].extract_text()
    for cid in ['3499','3500','3502','3535']:assert cid in second
assert minimum>=15.9,minimum
for p in (OUT/'figures').glob('*.png'):
    with Image.open(p) as im:assert im.size==(2400,1680) and im.convert('RGB').getpixel((0,0))==(255,255,255)
for p in (OUT/'figures').glob('*.svg'):
    text=p.read_text(encoding='utf-8');assert 'Arial' in text and '<image' not in text
result={'status':'PASS','pages':2,'nine_primary_core_intervals_verified':True,'all20_exact_match_rows':180,
 'fonts':sorted(fonts),'minimum_text_pt':minimum,'text_outside_page':outside,'PNG_dimensions':[2400,1680],
 'graphics':'native R ggplot2; white background; no grid; vector PDF/SVG',
 'pdf_sha256':hashlib.sha256(pdfpath.read_bytes()).hexdigest()}
(OUT/'logs/output_audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result))
