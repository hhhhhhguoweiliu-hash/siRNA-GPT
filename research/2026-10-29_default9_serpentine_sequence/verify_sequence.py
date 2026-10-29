"""Audit every placed RNA and guide base, orientation, and actual PDF glyph."""
import csv, hashlib, json
from pathlib import Path
from pypdf import PdfReader
import pdfplumber

OUT=Path(__file__).resolve().parent
def table(name):
    with (OUT/'tables'/name).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f,delimiter='\t'))
s=json.loads((OUT/'settings.json').read_text());rna=table('mRNA_bases.tsv');guides=table('guide_bases.tsv');rows=table('rows.tsv')
labels=table('guide_labels.tsv');ends=table('guide_ends.tsv')
reference=''.join((OUT/'inputs/NM_003376.6_RNA.fasta').read_text().splitlines()[1:])
assert len(rna)==3609 and {int(r['position']) for r in rna}==set(range(1,3610))
assert ''.join(r['base'] for r in sorted(rna,key=lambda x:int(x['position'])))==reference
assert len(guides)==9*21 and len(labels)==9 and len(ends)==18
complement=str.maketrans('ACGU','UGCA');bypos={int(r['position']):r for r in rna}
for row in rows:
    subset=sorted((r for r in rna if r['row']==row['row']),key=lambda x:float(x['x']),reverse=row['direction']=='RTL')
    assert ''.join(r['base'] for r in subset)==reference[int(row['first_coordinate'])-1:int(row['last_coordinate'])]
    assert (row['direction']=='LTR')==(int(row['row'])%2==1)
for lab in labels:
    group=sorted((g for g in guides if g['candidate_id']==lab['candidate_id']),key=lambda x:int(x['guide_index_5to3']))
    assert ''.join(g['base'] for g in group)==lab['guide21_5to3']
    assert sum(g['kind']=='Guide core (19 nt)' for g in group)==19
    assert sum(g['kind']=="Guide 3' duplex terminal (2 nt)" for g in group)==2
    assert [int(g['target_position']) for g in group]==list(range(int(lab['full_guide_complement_end']),int(lab['full_guide_complement_start'])-1,-1))
    for g in group:
        target=bypos[int(g['target_position'])]
        assert g['x']==target['x'] and float(g['y'])<float(target['y'])
        assert g['base']==target['base'].translate(complement)
    prime={e['label']:e for e in ends if e['candidate_id']==lab['candidate_id']}
    # 5-prime end is next to guide base 1; 3-prime end next to base 21.
    assert abs(abs(float(prime["5'"]['x'])-float(group[0]['x']))-1.8)<1e-8
    assert abs(abs(float(prime["3'"]['x'])-float(group[-1]['x']))-1.8)<1e-8
pdfpath=OUT/'figures/default9_VEGFA_serpentine_full_sequence.pdf';reader=PdfReader(pdfpath)
assert len(reader.pages)==1
fonts={str(f.get_object().get('/BaseFont')) for f in reader.pages[0]['/Resources']['/Font'].get_object().values()}
assert fonts and all('Arial-Bold' in f for f in fonts)
outside=[];allchars=[];rna_glyphs=0;guide_glyphs=0
with pdfplumber.open(pdfpath) as pdf:
    page=pdf.pages[0];allchars=page.chars
    outside=[c['text'] for c in allchars if c['x0']<-.1 or c['x1']>page.width+.1 or c['top']<-.1 or c['bottom']>page.height+.1]
    assert not outside,outside[:10]
    # cairo_pdf rounds device dimensions to whole points; allow sub-point rounding.
    assert abs(page.width-s['width_inches']*72)<1 and abs(page.height-s['height_inches']*72)<1
    # Match each expected nucleotide to a real glyph at its intended cell.
    # Labels contain no A/C/G/U on the base rows. Header/footer use different y positions.
    bases=[c for c in allchars if c['text'] in 'ACGU' and abs(c['size']-16)<.2]
    used=set()
    for expected in [*rna,*guides]:
        ex=(float(expected['x'])-s['xmin'])*s['cell_pt']
        ey=(s['ymax']-float(expected['y']))*s['cell_pt']
        found=[(i,c) for i,c in enumerate(bases) if i not in used and abs((c['x0']+c['x1'])/2-ex)<1 and abs((c['top']+c['bottom'])/2-ey)<8]
        assert len(found)==1,(expected,[(c['text'],c['x0'],c['top']) for _,c in found])
        i,c=found[0];assert c['text']==expected['base'],(expected,c['text']);used.add(i)
    rna_glyphs=len(rna);guide_glyphs=len(guides)
audit={'status':'PASS','PDF_pages':1,'RNA_reference_bases_verified':3609,'siRNA_guides':9,'guide_bases_verified':189,
 'all_PDF_nucleotide_glyphs_checked':rna_glyphs+guide_glyphs,'all_guide_bases_complementary_and_x_aligned':True,
 'all9_guides_match_original_5to3_sequences':True,'guide_5prime_3prime_end_labels_correct':True,
 'all_29_rows_reconstruct_the_original_RNA_in_S_reading_order':True,'fonts':sorted(fonts),'text_outside_page':outside,
 'width_inches':s['width_inches'],'height_inches':s['height_inches'],'font_size_bases_pt':16,
 'pdf_sha256':hashlib.sha256(pdfpath.read_bytes()).hexdigest()}
(OUT/'logs/output_audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
print(json.dumps(audit))
