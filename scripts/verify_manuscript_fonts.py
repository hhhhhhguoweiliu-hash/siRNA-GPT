"""Read-only PDF/SVG checks. Run with a Python containing pypdf."""
import argparse, json, re
from pathlib import Path
from pypdf import PdfReader

def main():
    p=argparse.ArgumentParser();p.add_argument('--paper',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    root=Path(a.paper);out=Path(a.output)
    if out.exists():raise SystemExit('Use a new output path')
    reader=PdfReader(root/'figures/Manuscript_Figures_Arial.pdf')
    assert len(reader.pages)==3,'Incomplete development diagnosis must not be a manuscript quality-comparison page'
    pages=[]
    for number,page in enumerate(reader.pages,1):
        fonts=[]
        for ref in page['/Resources']['/Font'].values():
            font=ref.get_object();base=str(font['/BaseFont'])
            descendants=font.get('/DescendantFonts')
            child=descendants[0].get_object() if descendants else font
            descriptor=child.get('/FontDescriptor');descriptor=descriptor.get_object() if descriptor else {}
            assert 'Arial' in base,base
            assert '/FontFile2' in descriptor,'Expected embedded TrueType font: '+base
            fonts.append({'base_font':base,'embedded_TrueType':True})
        sizes=[]
        def visitor(text,cm,tm,font_dict,font_size):
            if text.strip():sizes.append(font_size)
        text=page.extract_text(visitor_text=visitor)
        assert not re.search(r'[\u3400-\u9fff]',text),'Non-English PDF text'
        assert min(sizes)>=4.99 and max(sizes)<=8.01,(min(sizes),max(sizes))
        assert any('Bold' in f['base_font'] for f in fonts),'Bold panel labels absent'
        pages.append({'page':number,'fonts':fonts,'font_size_min_pt':min(sizes),'font_size_max_pt':max(sizes),
            'width_mm':round(float(page.mediabox.width)*25.4/72,3),'height_mm':round(float(page.mediabox.height)*25.4/72,3),
            'no_CJK_text':True,'text_extractable':bool(text.strip())})
    svgs=[]
    for path in sorted(root.rglob('*.svg')):
        raw=path.read_text(encoding='utf-8')
        assert '<text' in raw and 'Arial' in raw and 'DejaVu' not in raw,path
        assert not re.search(r'[\u3400-\u9fff]',raw),path
        svgs.append({'path':str(path.relative_to(root)),'editable_text':True,'Arial_declared':True,'no_DejaVu_reference':True})
    assert len(svgs)==4
    value={'PDF_pages':pages,'SVG_figures':svgs,'result':'PASS',
        'development_diagnosis_excluded_from_manuscript_PDF':True,
        'scope':'Font and language verification, not scientific result validation. Actual exported sizes reported; target-journal page layout remains to be confirmed.'}
    out.write_text(json.dumps(value,indent=2),encoding='utf-8')
    print(json.dumps(value))

if __name__=='__main__':main()
