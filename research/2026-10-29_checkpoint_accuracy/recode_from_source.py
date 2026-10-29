"""Build a transparent retrospective decision recoding of existing checkpoints.

No new model/science calls and no new human scores. Existing C/W/M outcomes
are retained; their evidence is linked, not silently replaced.
"""
import argparse, csv, hashlib, json, shutil, zipfile
from pathlib import Path
from collections import Counter

parser=argparse.ArgumentParser()
parser.add_argument('--repo-root',type=Path,required=True,help='Checkout containing the immutable source files in source_manifest.json')
BASE=parser.parse_args().repo_root.resolve()
OUT=Path(__file__).resolve().parent
DATA=OUT/'data'
DATA.mkdir(parents=True,exist_ok=True)
COMMIT='0fea37f726b4adff9ba06dc5e55f69ce561a96a3'
OLD='research/2026-10-29_metric_figures_paper_style/data/resolved_slots.csv'
def sha(b): return hashlib.sha256(b).hexdigest()
def write_json(p,d): p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def write_csv(p,rows):
    with p.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def read_csv(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

# These are the original 27 boundary/prohibition checkpoints, not 27 new items.
# A negative label is an unsupported claim or prohibited event, not the word
# "not" appearing in an otherwise positive requirement.
NEG={
'W1_S05_ROLE_ASSUMPTION':('供应商已经确认本题两行的guide/passenger角色，链角色不再只是用户的条件性计算假设。','semantic'),
'W1_S15_SCORE_MEANING':('本题scaled模型分数可以当作实测敲低百分比或实测效力。','semantic'),
'W1_S26_CHEMISTRY_LIMITS':('计算模型已经确认本题供应商链角色、实际TT/N3末端化学或N3连接实物构型。','semantic'),
'W2_COMMON_WINDOW_CORE':('本题可以直接把23nt设计窗口起点作为19nt配对核心起点。','semantic'),
'W2_COMMON_SCOPE':('本轮执行或报告了题目排除的分数、seed、表达关联或候选排名分析。','bounded_event'),
'W2B_SCORE_MEANING':('本题scaled模型分数可以直接换算实测敲低百分比。','semantic'),
'W2B_SCOPE':('本轮扩展执行或报告了题目排除的seed、表达或候选排名分析。','bounded_event'),
'W3_PASS_INTERPRETATION':('本题PASS或近匹配/无警告记录足以确证生物学脱靶、安全性或无脱靶风险。','semantic'),
'U1_R1_SCOPE':('首轮执行或报告了题目排除的分数、seed、表达或排名分析。','bounded_event'),
'U1_R2_SCORE_MEANING':('第二轮模型分数是实测敲低百分比。','semantic'),
'U1_R2_SCOPE':('第二轮额外开展了题目排除的seed、表达、排名或新序列扫描。','bounded_event'),
'U1_R2_NO_PLACEHOLDER_DATE':('第二轮正式来源说明中出现了被当作实际时间使用的未替换占位日期。','bounded_event'),
'R1_R1_ROLES_UNCONFIRMED':('首轮订购记录已经提供供应商确认的guide/passenger角色。','semantic'),
'R1_R1_NOT_ORDER_READY':('首轮信息已足以把这两行当成供应商已确认、可直接下单的双链构型。','semantic'),
'R1_R2_SCORE_MEANING':('第二轮模型分数是实测敲低百分比。','semantic'),
'R1_R2_CHEMISTRY_LIMITS':('第二轮计算已经确认真实N3/TT化学、连接方式或组装构型。','semantic'),
'R1_R2_NO_NEW_CALC':('第二轮进行了新重型预测、seed或表达分析，或宣称这些新科学计算已经完成。','bounded_event'),
'R2_NO_SCORE_REUSE':('核心变成AUUCUUGUCUUGCUCUAUC后，仍可以把旧1.121934400320053当作新核心的分数。','semantic'),
'R2_NO_NEW_SCORE_SCAN':('本轮已经启动题目禁止的新评分或扫描。','bounded_event'),
'R2_NO_BIO_INVALIDITY':('正式交付把字段/序列不一致直接断言成该siRNA生物学无效。','bounded_event'),
'R3_NO_BASE_MUTATION':('本轮修改或截短原19nt核心碱基以迎合错误的声明坐标。','bounded_event'),
'R4_USER_TABLE_ABSENT':('本轮已经取得用户提供、可用于本轮表达关联的表达表。','semantic'),
'R4_NO_BUILTIN_FALLBACK':('缺少用户表达表时，可以回退内置表并当成本轮用户数据。','semantic'),
'R4_SCORE_MEANING':('本题模型分数是实测敲低百分比。','semantic'),
'R4_EXPRESSION_MISSING':('本轮表达关联已经取得有效TPM/检出结果，可以报告真实数值或把缺项填0。','semantic'),
'R4_REPORT_INCOMPLETE':('无需补充用户表达表，本轮包含用户表达背景的完整报告已经可以交付。','semantic'),
'R4_CHEMISTRY_LIMITS':('本题计算已经确认供应商链角色、实物化学或N3连接构型。','semantic'),
}
standards=read_csv(BASE/'research/2026-10-27_ai_simulated_review_audit_v3/required_slots.csv')
old=read_csv(BASE/OLD)
answers=json.loads((BASE/'research/2026-10-27_real_dialogue_mini/raw/results_original.json').read_text())
byid={a['answer_id']:a for a in answers}
archive=zipfile.ZipFile(BASE/'research/2026-10-27_real_dialogue_mini/raw/anonymous_reviewer_package_original.zip')
groups={x['answer_id']:x['group'] for x in answers}
assert len(standards)==135 and len(old)==405 and len(NEG)==27
assert set(NEG)<=set(s['slot_id'] for s in standards)
assert sha((BASE/OLD).read_bytes())=='aee520e7fea925ca0c3358fdf4715861a4547b332e185b615e09f4e307f7e9e6'
assert sha((BASE/'research/2026-10-27_real_dialogue_mini/raw/results_original.json').read_bytes())=='f443d6f358a3c63f45eeef0906ae968f74f231534eb3c5276207767a14c2b9a3'
assert sha((BASE/'research/2026-10-27_ai_simulated_review_audit_v3/required_slots.csv').read_bytes())=='27a9225216be9c35dc0ca36181c19d383c4f057571b440dd55ca69236e214fed'

defs=[]
for s in standards:
    sid=s['slot_id'];neg=sid in NEG
    # Positive checkpoints retain the exact existing fact/complete-tuple rule.
    # A supplied incompatible alternative is a contradiction of this proposition;
    # absence or an incomplete tuple remains ABSTAIN, not an implicit rejection.
    prop=NEG[sid][0] if neg else '本题所要求的对应事实、证据或完整交付成立：'+s['atomic_requirement']+' 标准内容：'+s['accepted_values_json']
    defs.append({'checkpoint_id':sid,'case_id':s['case_id'],'round_id':s['round_id'],
        'gold_label':0 if neg else 1,'proposition':prop,
        'checkpoint_kind':NEG[sid][1] if neg else 'positive_fact_or_required_delivery',
        'original_requirement':s['atomic_requirement'],'reference_value':s['accepted_values_json'],
        'standard_evidence_locator':s['standard_evidence_locator'],
        'gold_basis':'Original task, fixed reference/bound score, and existing requirement; retrospective polarity coding, not expert reapproval'})
write_csv(DATA/'checkpoint_definitions.csv',defs)
definition={s['checkpoint_id']:s for s in defs}
judgments=[];negative_review=[]
for r in old:
    d=definition[r['source_slot_id']];gt=int(d['gold_label']);status=r['final_status']
    if status=='CORRECT':pred=str(gt)
    elif status=='WRONG':pred=str(1-gt)
    elif status=='MISSING':pred='ABSTAIN'
    else:raise ValueError(status)
    outcome='A_POS' if pred=='ABSTAIN' and gt else 'A_NEG' if pred=='ABSTAIN' else {('1','1'):'TP',('0','0'):'TN',('0','1'):'FP',('1','0'):'FN_EXPLICIT'}[(str(gt),pred)]
    aid=r['answer_id'];rd=int(r['round_id']);record=next(x for x in byid[aid]['rounds'] if x['round']==rd)
    text=record['answer'];assert text.strip()
    note=('完整原核查项未满足/缺答；保留ABSTAIN，不补为否，不计TN。' if pred=='ABSTAIN' else
          '复用已核查的正确事实/完整交付。' if gt==1 and status=='CORRECT' else
          '给出与标准事实不相容的值/解释，记显式否定该真命题。' if gt==1 else
          '对假命题给出支持，或实际出现该禁用事件。' if status=='WRONG' else
          '已核查的明确边界否定；不是把缺答当作否定。')
    if gt==0 and d['checkpoint_kind']=='bounded_event' and status=='CORRECT':
        note='在完整正式正文/实际交付或执行记录中核查该有限事件未发生；不是未回答语义问题所产生的TN。'
    row={'answer_id':aid,'group':groups[aid],'case_id':r['case_id'],'round_id':rd,
         'checkpoint_id':d['checkpoint_id'],'gold_label':gt,'prediction':pred,'outcome':outcome,
         'original_status':status,'original_label_source':r['final_status_source'],
         'source_review_item_id':r['review_item_id'],'source_csv_commit':COMMIT,'source_csv_path':OLD,
         'evidence_locator':r['evidence_locator'],'full_evidence_quote_sha256':sha(r['evidence_quote'].encode()),
         'formal_round_body_sha256':sha(text.encode()),'coding_note':note}
    judgments.append(row)
    if gt==0:
        quote=r['evidence_quote'];review_note=note
        if d['checkpoint_id']=='U1_R2_NO_PLACEHOLDER_DATE':
            present='2025年X月X日' in text
            assert (pred=='1')==present
            quote='\n'.join(x for x in text.splitlines() if 'X月' in x) if present else '完整正文检查：未出现未替换占位日期。正文SHA256='+sha(text.encode())
            review_note+=' 占位日期已直接核对本轮正式全文。'
        if d['checkpoint_id']=='R2_NO_NEW_SCORE_SCAN':
            assert not set(record['completed_tools']) & {'score_candidates','match_seed','query_expression'}
            review_note+=' 已直接核对completed_tools；A023仅候选校验停止，不算启动新评分或扫描。'
        scope_exclusions={
            'W2_COMMON_SCOPE':{'score_candidates','match_seed','query_expression','compile_report'},
            'W2B_SCOPE':{'match_seed','query_expression','compile_report'},
            'U1_R1_SCOPE':{'score_candidates','match_seed','query_expression','compile_report'},
            'U1_R2_SCOPE':{'match_seed','query_expression','compile_report'},
            'R1_R2_NO_NEW_CALC':{'match_seed','query_expression'},
        }
        if d['checkpoint_id'] in scope_exclusions:
            assert not set(record['completed_tools']) & scope_exclusions[d['checkpoint_id']]
            review_note+=' 已直接复核本轮完整completed_tools，未完成题目排除的额外工具步骤；分数读取不算新重型模型预测。'
        if d['checkpoint_id']=='R2_NO_BIO_INVALIDITY':
            # Stopping on inconsistent input is not a conclusion of biological ineffectiveness.
            assert '生物学无效' not in text and '生物学上无效' not in text
            review_note+=' 完整正文未把输入不一致宣称为生物学无效；保留停止/需重查原文。'
        if d['checkpoint_id']=='R3_NO_BASE_MUTATION':
            core='UGUACUACGGAAUAUCUCG'
            delivered=[n for n in archive.namelist() if n.startswith(f'answers/{aid}/attachments/round_{rd}/') and n.endswith('/verify_target.json')]
            if delivered:
                assert len(delivered)==1
                result=json.loads(archive.read(delivered[0]));assert result['rows'][0]['guide_core19_5to3']==core
            else:
                assert core in text
            review_note+=' 核对原19nt核心UGUACUACGGAAUAUCUCG在正式正文或verify_target实际交付中保留；不以修改碱基解释坐标纠正。'
        negative_review.append({k:row[k] for k in ['answer_id','group','case_id','checkpoint_id','gold_label','prediction','outcome','original_status','evidence_locator']}|{
            'proposition':d['proposition'],'evidence_quote_excerpt':quote[:1400],
            'excerpt_truncated':len(quote)>1400,'full_original_quote_sha256':sha(r['evidence_quote'].encode()),
            'review_note':review_note})
write_csv(DATA/'judgments.csv',judgments)
write_csv(DATA/'negative_evidence_review.csv',negative_review)

sources=[]
source_paths=[(p,p) for p in ['research/2026-10-27_real_dialogue_mini/raw/results_original.json',
'research/2026-10-27_real_dialogue_mini/raw/anonymous_reviewer_package_original.zip',
'research/2026-10-27_ai_simulated_review_audit_v3/required_slots.csv',OLD,
'research/2026-10-29_metric_figures_paper_style/data/adjudication_receipt_BCC.json']]
for local,remote in source_paths:
    b=(BASE/local).read_bytes()
    sources.append({'path':remote,'commit':COMMIT,'bytes':len(b),'sha256':sha(b),
      'git_blob_sha1':hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()})
write_json(OUT/'source_manifest.json',{'sources':sources,'original_answers':27,'tasks_per_group':9,
  'checkpoints_per_group':135,'positive_checkpoints_per_group':108,'negative_checkpoints_per_group':27,
  'new_checkpoints':0,'new_system_runs':0,'new_expert_scores':0,
  'review_type':'retrospective recoding of existing AI-assisted review plus user-relayed BCC adjudication',
  'independent_test':False,'original_C_W_M_changed':False})
shutil.copyfile(BASE/'research/2026-10-29_metric_figures_paper_style/style_reference.json',OUT/'style_reference.json')
print(json.dumps({'output':str(OUT),'checkpoints':len(defs),'judgments':len(judgments),'negative_reviews':len(negative_review),'gold':dict(Counter(d['gold_label'] for d in defs))}))
