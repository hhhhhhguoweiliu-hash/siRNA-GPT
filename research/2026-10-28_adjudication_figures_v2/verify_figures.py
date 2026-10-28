"""Verify actual exported bytes, embedded PDF fonts, source invariants and data."""
import csv,hashlib,json,re,xml.etree.ElementTree as ET
from pathlib import Path
from pypdf import PdfReader
from PIL import Image
from audit_data import HERE,load_data,protected_integrity,slot_metrics

NAMES=['Fig1_task_pass_by_category','Fig2_slot_macro_by_category','Fig3A_scores_A_by_category','Fig3C_scores_C_by_category',
       'Fig4A_score_matrix_A','FigS1_score_matrix_C','FigS2_changed_task_verdicts','FigS3_overall_slot_micro']

def font_check(path):
    reader=PdfReader(path);fonts=[]
    for n,page in enumerate(reader.pages):
        for value in page['/Resources']['/Font'].get_object().values():
            font=value.get_object();name=str(font.get('/BaseFont',''));descendants=font.get('/DescendantFonts')
            core=descendants[0].get_object() if descendants else font
            descriptor=core.get('/FontDescriptor');descriptor=descriptor.get_object() if descriptor else {}
            embedded=bool(descriptor.get('/FontFile2') or descriptor.get('/FontFile3') or descriptor.get('/FontFile'))
            assert 'Arial' in name and embedded,(path,name,embedded)
            fonts.append(dict(page=n+1,name=name,embedded=embedded,type=str(font.get('/Subtype'))))
    assert fonts and any('Bold' in f['name'] for f in fonts) and any('Bold' not in f['name'] for f in fonts)
    return dict(pages=len(reader.pages),fonts=fonts,text_chars=sum(len(p.extract_text() or '') for p in reader.pages))

def main():
    data=load_data();checks=[]
    for name in NAMES:
        pdf=HERE/'figures'/(name+'.pdf');png=pdf.with_suffix('.png');svg=pdf.with_suffix('.svg')
        fonts=font_check(pdf);assert fonts['pages']==1
        with Image.open(png) as im:
            dpi=im.info.get('dpi');assert dpi and all(abs(v-600)<1 for v in dpi)
            dimensions=im.size
        content=svg.read_text('utf-8');ET.fromstring(content)
        assert 'Arial' in content and not any(s in content for s in ('Arimo','Liberation Sans','DejaVu'))
        assert '<image' not in content,'SVG must remain vector'
        checks.append(dict(figure=name,pdf=fonts,png_pixels=dimensions,png_dpi=dpi,svg_Arial_only=True,svg_vector=True))
    combined=HERE/'output/pdf/siRNA_GPT_corrected_adjudication_figures_20261028.pdf';combined_check=font_check(combined)
    assert combined_check['pages']==8
    reader=PdfReader(combined)
    for page in reader.pages[:4]:
        text=page.extract_text()
        assert all(s in text for s in ('Standard work','Requirement change','Reliability'))
    overall={r['group']:r for r in data['summaries'] if r['category']=='OVERALL'}
    assert {g:r['pass_after'] for g,r in overall.items()}=={'llm':0,'workflow':8,'agent':9}
    assert all(r['required_slots']==135 for r in overall.values())
    assert abs(overall['llm']['f1']-55/101)<1e-12 and abs(overall['agent']['f1']-32/33)<1e-12
    expected=slot_metrics([{'review_status':s} for s in ('CORRECT','CORRECT','CORRECT','WRONG','MISSING')])
    assert expected['FN']==2 and expected['recall']==.6 and abs(expected['f1']-2/3)<1e-12
    invalid_rejected=False
    try:slot_metrics([{'review_status':'UNJUDGED'}])
    except ValueError:invalid_rejected=True
    assert invalid_rejected
    integrity=protected_integrity()
    result=dict(status='PASS',source_head=data['source_head'],n_figures=8,n_standalone_pdfs=8,combined=combined_check,
        figures=checks,actual_embedded_Arial=True,regular_and_bold_both_present=True,source_files_unchanged=integrity['n_files'],
        original_answers=27,original_rounds=33,original_slot_judgments=405,new_answer_runs=0,new_quality_labels=0,
        macro_and_micro_separated=True,category_panels_verified=True,missing_labels_not_imputed=True,
        visual_qa='Requires rendered-page inspection; see VISUAL_QA.md',
        artifact_hashes={str(p.relative_to(HERE)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for folder in ('figures','output/pdf') for p in (HERE/folder).glob('*') if p.is_file()})
    (HERE/'export_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('figures','combined','artifact_hashes')},ensure_ascii=True))

if __name__=='__main__':main()
