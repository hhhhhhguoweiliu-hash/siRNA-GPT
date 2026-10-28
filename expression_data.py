"""Validated baseline TPM imports. No efficacy model or off-target weights."""
import csv, io, json, math, hashlib, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SAMPLES = ['Nor1','Nor2','Nor3','Nor4','Hyp1','Hyp2','Hyp3','Hyp4']
STORE = ROOT/'uploaded_expression'

def parse_tpm(text):
    if not isinstance(text,str) or len(text.encode('utf-8'))>8_000_000:
        raise ValueError('表达表需为不超过8MB的UTF-8 CSV/TSV')
    reader=csv.DictReader(io.StringIO(text.lstrip('\ufeff')), delimiter='\t' if '\t' in text.split('\n')[0] else ',')
    if not {'ENTREZID','approved_symbol',*SAMPLES}.issubset(reader.fieldnames or []):
        raise ValueError('缺少表头：ENTREZID、approved_symbol、Nor1–4、Hyp1–4；必须提供原始TPM，不能用counts或log值替代')
    rows=[];seen=set()
    for row in reader:
        if len(rows)>=100000:raise ValueError('表达表最多100000行')
        gid=(row.get('ENTREZID') or '').strip();symbol=(row.get('approved_symbol') or '').strip()
        if not re.fullmatch(r'[1-9][0-9]{0,11}',gid) or gid in seen:
            raise ValueError('ENTREZID须为唯一正整数；多行转录本不能直接作为基因表达表上传')
        if not symbol or len(symbol)>80 or any(ord(c)<32 for c in symbol):raise ValueError('基因符号缺失或无效')
        if (gid=='7422')!=(symbol=='VEGFA'):raise ValueError('人VEGFA须对应ENTREZID 7422，请先核对物种与基因ID')
        seen.add(gid);out={'feature_id':symbol,'approved_symbol':symbol,'ENTREZID':gid}
        for sample in SAMPLES:
            try:value=float(row[sample])
            except (TypeError,ValueError):raise ValueError('TPM必须是完整的有限非负数，不能缺失')
            if not math.isfinite(value) or not 0<=value<=1_000_000:raise ValueError('TPM必须为0至1000000的有限数；请核对单位')
            out[sample]=value
        for state,prefix in [('Normoxia','Nor'),('Hypoxia','Hyp')]:
            values=[out[prefix+str(i)] for i in range(1,5)]
            out['TPM_'+state+'_mean']=sum(values)/4
            out[state+'_n_TPM_ge1']=sum(v>=1 for v in values)
        rows.append(out)
    if '7422' not in seen:raise ValueError('缺少VEGFA（ENTREZID 7422）；不能静默回退到内置表达数据')
    return rows

def upload(text,label,confirmed,store=None):
    if confirmed is not True:raise ValueError('请确认这是人ARPE-19未转染基线、每状态4个样本的基因级未取对数TPM')
    label=str(label).strip()
    if not label or len(label)>120 or any(ord(c)<32 for c in label):raise ValueError('请填写120字以内的表达表来源说明')
    rows=parse_tpm(text);digest=hashlib.sha256(text.encode('utf-8')).hexdigest()
    identity=hashlib.sha256((digest+'\n'+label).encode('utf-8')).hexdigest()
    receipt={'id':identity,'label':label,'sha256':digest,'rows':len(rows),'source':'USER_UPLOAD',
        'sample_columns':SAMPLES,'scope':'user-declared human ARPE-19 untransfected baseline; 4 samples per state; hypoxia 1% O2 24h',
        'declaration_verified_independently':False,'ranking_changed':False,
        'warning':'这是用户声明和格式校验，不代表系统验证了物种、TPM计算方法或实验独立性'}
    path=Path(store or STORE);path.mkdir(parents=True,exist_ok=True)
    from core import save_json
    save_json(path/(identity+'.json'),{'receipt':receipt,'rows':rows})
    return receipt

def load_dataset(identity,store=None):
    if not isinstance(identity,str) or not re.fullmatch('[0-9a-f]{64}',identity):raise ValueError('表达数据ID无效')
    path=Path(store or STORE)/(identity+'.json')
    if not path.is_file():raise ValueError('所选表达表已不存在（云端重启可能清除上传），请重新上传；未回退内置数据')
    return json.loads(path.read_text(encoding='utf-8'))

BUILTIN_IDS=('builtin','builtin_legacy_20261016')

def builtin_path(identity='builtin'):
    if identity not in BUILTIN_IDS:raise ValueError('未知内置表达版本')
    return ROOT/'data'/('expression.tsv.gz' if identity=='builtin' else 'expression_legacy_20261016.tsv.gz')

def builtin_receipt(identity='builtin'):
    path=builtin_path(identity)
    provenance=json.loads((ROOT/'data/expression_provenance.json').read_text(encoding='utf-8'))
    actual=hashlib.sha256(path.read_bytes()).hexdigest()
    if identity=='builtin_legacy_20261016':
        if actual!=provenance['legacy_sha256']:raise ValueError('历史表达版本指纹不一致，停止评价')
        return {'id':identity,'label':'2026-10-16冻结的历史评价表达表（非当前作图版本）',
                'source':'FROZEN_LEGACY_PROJECT_DATA','sha256':actual,'scope':provenance['scope'],
                'samples':SAMPLES,'per_sample_tpm_available_in_packaged_table':False,'ranking_changed':False}
    if actual!=provenance['sha256']:raise ValueError('内置表达表与校验记录不一致，停止且不回退旧表')
    return {**provenance,'id':'builtin','sha256':actual}
