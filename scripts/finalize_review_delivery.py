"""Verify exported blank workbook and build an anonymous additive review bundle."""
import argparse,collections,hashlib,json,zipfile,xml.etree.ElementTree as E
from pathlib import Path

NS={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
def decode_sheet(z,name):
    shared=[]
    if 'xl/sharedStrings.xml' in z.namelist():
        shared=[''.join(si.itertext()) for si in E.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si',NS)]
    xml=E.fromstring(z.read(name));cells={}
    for c in xml.findall('.//m:sheetData/m:row/m:c',NS):
        kind=c.get('t');v=c.find('m:v',NS)
        if kind=='s':value=shared[int(v.text)]
        elif kind=='inlineStr':value=''.join(c.find('m:is',NS).itertext())
        elif v is None or v.text is None:value=''
        elif kind=='b':value=v.text=='1'
        elif kind in ('str','e'):value=v.text
        else:value=float(v.text)
        cells[c.get('r')]=value
    return xml,cells

def finish(output):
    root=Path(output);source=json.loads(Path('.test_tmp/review_forms/source.json').read_text(encoding='utf-8'))
    book=root/'blank_scores.xlsx'
    with zipfile.ZipFile(book) as z:
        assert z.testzip() is None
        assert not any('externalLinks' in n or 'vbaProject' in n for n in z.namelist())
        xml,score=decode_sheet(z,'xl/worksheets/sheet1.xml')
        for i,a in enumerate(source['answers'],8):
            assert score['A'+str(i)]==a['answer_id']
            assert all(score.get(c+str(i),'')=='' for c in 'CDEFGHIJ'),'A human field was filled'
        validations=xml.findall('m:dataValidations/m:dataValidation',NS)
        rule=next(v for v in validations if v.get('sqref')=='E8:H61')
        assert rule.get('type')=='whole' and rule.get('operator')=='between'
        assert rule.find('m:formula1',NS).text=='0' and rule.find('m:formula2',NS).text=='2'
        assert not xml.findall('m:sheetProtection',NS),'Score fields must be editable'
        pane=xml.find('m:sheetViews/m:sheetView/m:pane',NS)
        _,lines=decode_sheet(z,'xl/worksheets/sheet2.xml');actual=collections.defaultdict(list)
        for row in range(2,967):
            aid=lines['A'+str(row)];number=int(lines['B'+str(row)])
            assert number==len(actual[aid])+1
            actual[aid].append(lines.get('C'+str(row),''))
        assert len(actual)==54
        for a in source['answers']:assert '\n'.join(actual[a['answer_id']])==a['answer']
        for name in z.namelist():
            if name.startswith('xl/worksheets/sheet') and name.endswith('.xml'):
                assert not E.fromstring(z.read(name)).findall('.//m:f',NS),'No automatic grading formulas allowed'
        _,inputs=decode_sheet(z,'xl/worksheets/sheet4.xml');expected=[]
        def flatten(cid,prefix,value):
            if isinstance(value,(dict,list)) and value:
                items=value.items() if isinstance(value,dict) else enumerate(value)
                for k,v in items:flatten(cid,prefix+('['+str(k)+']' if isinstance(value,list) else '.'+k),v)
            else:
                kind='null' if value is None else 'array' if isinstance(value,list) else 'object' if isinstance(value,dict) else 'boolean' if isinstance(value,bool) else 'number' if isinstance(value,(int,float)) else 'string'
                display=json.dumps(value) if isinstance(value,(dict,list)) else 'null' if value is None else value
                expected.append([cid,prefix,kind,display])
        for task in source['tasks']:
            for key in ('raw_input','raw_task_fields','resolved_input'):flatten(task['case_id'],key,task[key])
        for row,values in enumerate(expected,2):assert [inputs.get(c+str(row),'') for c in 'ABCD']==values
        assert len(expected)==1034
    guide='''# 填写评分表

每位真实评审单独保存一份blank_scores.xlsx，在“评分表”浅黄色区域填写评审编号、可评分情况、四项0–2分及具体依据。
“原始回答”可按匿名编号筛选，保留全部原文及原始换行；“完整输入”有每题全部原始与解析字段；“题目与标准”列出既定标准、资源差异和字段解释。
四项分别评分，不自动相加。空白不是0；不可评分的项目留空，并写出原因。失败不能删除，后台补充信息不能替原回答补分。
也可直接填写原有blank_scores.tsv；两种格式任选一种，每位评审不要同时交两份相互冲突的分数。
标准为运行前的20261022_1310版，没有按本批问题改写标准。所有原始材料完整保留；阅读包内README.md和READ_FIRST.md了解数据来源与限制。
本包不含组别密钥、带组别复核或问题索引。不要另取这些文件给评审。形式和证据可能透露配置，不能保证完全盲法。
'''
    (root/'SCORING_GUIDE.md').write_text(guide,encoding='utf-8')
    original=Path('research/2026-10-22_fairness/three_arm/for_review_complete.zip')
    target=root/'for_review_with_scoring.zip'
    with zipfile.ZipFile(original) as old,zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as new:
        for name in old.namelist():new.writestr(name,old.read(name))
        new.writestr('blank_scores.xlsx',book.read_bytes());new.writestr('SCORING_GUIDE.md',guide)
    with zipfile.ZipFile(original) as old,zipfile.ZipFile(target) as new:
        assert new.testzip() is None and len(new.namelist())==177
        copied={name:{'sha256':sha(old.read(name)),'unchanged':old.read(name)==new.read(name)} for name in old.namelist()}
        assert all(v['unchanged'] for v in copied.values())
        assert not any(x in n.lower() for n in new.namelist() for x in ('private_key','issue_index','full_batch_review','full_batch_audit','records.tsv'))
        assert new.read('blank_scores.tsv')==(root/'blank_scores.tsv').read_bytes()
    receipt={'source_complete_review_entries':175,'delivery_review_entries':177,'crc':'PASS',
        'original_package_files':copied,'original_answers_preserved':54,'original_answer_lines_in_workbook':965,
        'complete_input_fields_in_workbook':1034,'human_fields_blank':54*8,
        'four_quality_dimensions_blank':54*4,'score_validation':'whole numbers 0 through 2',
        'worksheet_pane':pane.attrib if pane is not None else None,'scoring_sheet_protected':False,
        'automatic_scoring_formulas':0,'group_key_in_package':False,'group_labelled_review_or_issue_index_in_package':False,
        'native_excel_interaction_tested':False,'visual_review':'All four sheets rendered and inspected',
        'authoring_process_note':'Exporter returned a saved file and previews but process exited 1 without an error diagnostic. Saved XLSX was separately checked for CRC, cells, validations, original text, complete inputs and no formulas.',
        'xlsx_sha256':sha(book.read_bytes()),'review_zip_sha256':sha(target.read_bytes()),
        'scientific_quality_scores_assigned':False,'api_calls':0}
    write(root/'scoring_and_bundle_verification.json',receipt)
    print(json.dumps({k:v for k,v in receipt.items() if k!='original_package_files'},ensure_ascii=False,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();finish(a.output)
