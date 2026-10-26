"""Read independent HUMAN review workbooks; do not author scores or infer truth."""
import argparse
import hashlib
import json
import posixpath
import re
import zipfile
import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation
from pathlib import Path

from evaluation_analysis import DIMENSIONS, summarize

SCORE_HEADERS = ['回答编号','题目ID','评审人','事实准确 0–2','证据支持 0–2','需求完成 0–2',
                 '边界处理 0–2','交付判定','严重错误','不可评分原因','依据与备注']
FACT_HEADERS = ['回答编号','题目ID','评审人','事实项目ID','需核对项目','逐项判定','依据/原因']
ADJ_HEADERS = ['回答编号','题目ID','裁决人','裁决依据','交付判定','严重错误','事实项目ID','事实判定']
FACT_MAP = {'正确':'correct','错误':'wrong','缺失':'missing','未评分':None,'':None}
SEVERE_MAP = {'是':True,'否':False,'待核对':None,'':None}
DELIVERY_MAP = {'完成':'完成','部分完成':'部分完成','未交付':'未交付','不可评分':None,'':None}


def read_sheets(path):
    ns = {'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
          'r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:raise ValueError('评分文件ZIP不完整')
        if sum(i.file_size for i in archive.infolist()) > 30_000_000:raise ValueError('评分文件过大')
        shared=[]
        if 'xl/sharedStrings.xml' in archive.namelist():
            shared=[''.join(t.text or '' for t in s.findall('.//m:t',ns))
                    for s in ET.fromstring(archive.read('xl/sharedStrings.xml')).findall('m:si',ns)]
        relations={r.attrib['Id']:r.attrib for r in ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))}
        result={}
        for sheet in ET.fromstring(archive.read('xl/workbook.xml')).findall('m:sheets/m:sheet',ns):
            if sheet.attrib['name'] not in ('评分表','逐事实','裁决'):continue
            rel=relations[sheet.attrib['{'+ns['r']+'}id']]
            if rel.get('TargetMode')=='External':raise ValueError('不能从外部链接读取评分')
            target=rel['Target']
            member=posixpath.normpath(target.lstrip('/') if target.startswith('/') else 'xl/'+target)
            if not member.startswith('xl/'):raise ValueError('评分文件关系路径无效')
            tree=ET.fromstring(archive.read(member))
            rows=[]
            for row in tree.findall('m:sheetData/m:row',ns):
                values={}
                for cell in row.findall('m:c',ns):
                    if cell.find('m:f',ns) is not None:raise ValueError('评分不得用公式代填，请保存实际人工值')
                    value=cell.findtext('m:v','',ns)
                    if cell.get('t')=='s':value=shared[int(value)]
                    elif cell.get('t')=='inlineStr':value=''.join(t.text or '' for t in cell.findall('.//m:t',ns))
                    elif cell.get('t')=='b':value=value=='1'
                    col=re.match('[A-Z]+',cell.attrib['r']).group()
                    number=0
                    for ch in col:number=number*26+ord(ch)-64
                    values[number-1]=value
                if values and any(str(v).strip() for v in values.values()):
                    rows.append((int(row.attrib['r']),[values.get(c,'') for c in range(max(values)+1)]))
            result[sheet.attrib['name']]=rows
        return result


def table(rows,headers):
    if not rows or [str(v).strip() for v in rows[0][1][:len(headers)]]!=headers:
        raise ValueError('评分表/逐事实/裁决的列名不符合模板')
    return [(row,dict(zip(headers,(values+['']*len(headers))[:len(headers)]))) for row,values in rows[1:]]


def text(value):return str(value if value is not None else '').strip()


def score(value):
    value=text(value)
    if not value:return None
    try:number=Decimal(value)
    except InvalidOperation:raise ValueError('人工分只接受0、1、2或空白')
    if not number.is_finite() or number not in (0,1,2):raise ValueError('人工分只接受0、1、2或空白')
    return int(number)


def mapped(value,mapping,name):
    value=text(value)
    if value not in mapping:raise ValueError(name+'标签无效：'+value)
    return mapping[value]


def parse_review_tables(plan,sheets,origin):
    units={p['answer_id']:p for p in plan}
    scores=table(sheets.get('评分表',[]),SCORE_HEADERS)
    facts=table(sheets.get('逐事实',[]),FACT_HEADERS)
    byid={};factrows={};identities=set()
    for row,data in scores:
        aid=text(data['回答编号'])
        if aid not in units or aid in byid:raise ValueError('回答编号未知或评分行重复')
        if text(data['题目ID'])!=units[aid]['case_id']:raise ValueError('评分题目ID与计划不一致')
        byid[aid]=(row,data)
        if text(data['评审人']):identities.add(text(data['评审人']))
    if set(byid)!=set(units):raise ValueError('每份评审文件需保留全部计划编号，未评分行不能删除')
    for row,data in facts:
        aid,fid=text(data['回答编号']),text(data['事实项目ID'])
        if aid not in units or fid not in units[aid]['required_fact_ids']:raise ValueError('逐事实编号不在预定计划中')
        if text(data['题目ID'])!=units[aid]['case_id']:raise ValueError('事实题目ID与计划不一致')
        if (aid,fid) in factrows:raise ValueError('逐事实行重复')
        factrows[aid,fid]=(row,data)
        if text(data['评审人']):identities.add(text(data['评审人']))
    expected={(aid,fid) for aid,p in units.items() for fid in p['required_fact_ids']}
    if set(factrows)!=expected:raise ValueError('逐事实表缺行，不能删除必要事实使完成标签成立')
    if len(identities)>1:raise ValueError('每份独立文件只允许一位评审编号，两表不得矛盾')
    reviewer=next(iter(identities),'')
    imported=[];unfilled=[]
    for aid,p in units.items():
        row,data=byid[aid]
        fact_values={fid:mapped(factrows[aid,fid][1]['逐项判定'],FACT_MAP,'事实') for fid in p['required_fact_ids']}
        grades={key:score(data[header]) for key,header in zip(DIMENSIONS,SCORE_HEADERS[3:7])}
        delivery=mapped(data['交付判定'],DELIVERY_MAP,'交付')
        severe=mapped(data['严重错误'],SEVERE_MAP,'严重错误')
        reason=text(data['不可评分原因'])
        fact_annotations=any(text(factrows[aid,fid][1][key])
            for fid in p['required_fact_ids'] for key in ('逐项判定','依据/原因'))
        active=any(v is not None for v in grades.values()) or fact_annotations or any(text(data[k]) for k in ('交付判定','严重错误','不可评分原因','依据与备注'))
        if not active:
            unfilled.append(aid);continue
        if not reviewer:raise ValueError('已填写的独立文件必须提供真人评审编号；不能按文件名猜测')
        if text(data['交付判定'])=='不可评分' and not reason:raise ValueError('不可评分必须填写理由，不会自动改为未交付')
        if any(v is None for v in grades.values()) and not reason:raise ValueError('四维分有空白时必须说明不可评分原因')
        imported.append({'answer_id':aid,'case_id':p['case_id'],'reviewer_id':reviewer,**grades,
            'delivery_judgement':delivery,'severe_error':severe,'facts':fact_values,
            'unscorable_reason':reason,'notes':text(data['依据与备注']),
            'fact_notes':{fid:text(factrows[aid,fid][1]['依据/原因']) for fid in p['required_fact_ids']},
            'import_origin':{'file':origin,'score_excel_row':row,'fact_excel_rows':{fid:factrows[aid,fid][0] for fid in p['required_fact_ids']},
                'identity_rule':'Single explicit reviewer ID inherited across blank identity cells in this file'},
            'raw_review_fields':data,'raw_fact_fields':{fid:factrows[aid,fid][1] for fid in p['required_fact_ids']}})
    return {'reviewer_id':reviewer,'reviews':imported,'unfilled_ids':unfilled}


def parse_adjudication_tables(plan,sheets,origin):
    units={p['answer_id']:p for p in plan}
    rows=table(sheets.get('裁决',[]),ADJ_HEADERS)
    decisions={}
    for row,data in rows:
        aid=text(data['回答编号'])
        if aid not in units or text(data['题目ID'])!=units[aid]['case_id']:raise ValueError('裁决编号不在计划中')
        fields=('裁决人','裁决依据','交付判定','严重错误','事实项目ID','事实判定')
        if not any(text(data[k]) for k in fields):continue
        person,reason=text(data['裁决人']),text(data['裁决依据'])
        if not person or not reason:raise ValueError('每项真人裁决需填写编号和依据')
        d=decisions.setdefault(aid,{'answer_id':aid,'adjudicator_id':person,'reason':reason,'facts':{},'import_origin':origin,'raw_rows':[]})
        if d['adjudicator_id']!=person:raise ValueError('同单元多个裁决人需先整理一致记录')
        d['raw_rows'].append({'row':row,'fields':data})
        for column,key,mapping in [('交付判定','delivery_judgement',DELIVERY_MAP),('严重错误','severe_error',SEVERE_MAP)]:
            if text(data[column]):
                value=mapped(data[column],mapping,column)
                if key in d and d[key]!=value:raise ValueError('同单元裁决标签相互矛盾')
                d[key]=value
        fid=text(data['事实项目ID'])
        if fid:
            if fid not in units[aid]['required_fact_ids']:raise ValueError('裁决不能删改预定必要事实')
            if fid in d['facts']:raise ValueError('同一事实裁决重复')
            d['facts'][fid]=mapped(data['事实判定'],FACT_MAP,'事实裁决')
        elif text(data['事实判定']):raise ValueError('事实裁决缺少项目ID')
    return list(decisions.values())


def import_workbooks(plan,execution,workbooks,adjudication_workbook=None):
    summarize(plan,execution,[])  # Validate complete plan/status before reading grades.
    reviews=[];sources=[];persons=set()
    for file in workbooks:
        path=Path(file)
        origin={'filename':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
        imported=parse_review_tables(plan,read_sheets(path),origin)
        if imported['reviewer_id'] and imported['reviewer_id'] in persons:raise ValueError('两份独立文件使用重复评审ID')
        if imported['reviewer_id']:persons.add(imported['reviewer_id'])
        reviews.extend(imported['reviews'])
        sources.append({**origin,'reviewer_id':imported['reviewer_id'],'unfilled_ids':imported['unfilled_ids']})
    adjudications=[]
    if adjudication_workbook:
        path=Path(adjudication_workbook)
        origin={'filename':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
        adjudications=parse_adjudication_tables(plan,read_sheets(path),origin)
    result=summarize(plan,execution,reviews,adjudications)
    return {'reviews':reviews,'adjudications':adjudications,'source_workbooks':sources,
        'analysis':result,'no_scores_or_semantic_judgements_invented':True}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--plan',type=Path,required=True)
    parser.add_argument('--execution',type=Path,required=True)
    parser.add_argument('--workbooks',type=Path,nargs='+',required=True)
    parser.add_argument('--adjudication-workbook',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):parser.error('使用新的输出目录，旧导入/评分不覆盖')
    load=lambda path:json.loads(path.read_text(encoding='utf-8'))
    result=import_workbooks(load(args.plan),load(args.execution),args.workbooks,args.adjudication_workbook)
    args.output.mkdir(parents=True,exist_ok=True)
    for key in ('reviews','adjudications','source_workbooks','analysis'):
        (args.output/(key+'.json')).write_text(json.dumps(result[key],ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
