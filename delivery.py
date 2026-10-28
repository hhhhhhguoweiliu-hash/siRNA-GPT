"""Shared deterministic evidence delivery. Generated text stays diagnostic.

No numerical prediction, independent scientific judgment, or quality scoring.
"""
import json
from evaluation_contract import workflow_answer
from sequence_validation import verified_rows

CHECKS={'candidate_check':'inspect_candidates','reference_check':'verify_target',
        'score_check':'score_candidates','seed_check':'match_seed',
        'expression_check':'query_expression','report_required':'compile_report'}

def requirement_audit(inputs,state,planned=()):
    conditions=inputs.get('task',{}).get('evaluation_conditions',{})
    required=[tool for key,tool in CHECKS.items() if conditions.get(key)]
    if not required:required=list(planned)
    if 'compile_report' in required:required=list(dict.fromkeys([*CHECKS.values(),*required]))
    completed=[n for n in required if n in state and state[n].get('status')!='ERROR']
    missing=[n for n in required if n not in completed]
    return {'requirements_source':'explicit structured conditions or confirmed plan; free text coverage not independently validated',
        'requested_steps':required,'completed_steps':completed,'missing_steps':missing,
        'status':'MISSING_REQUIRED_EVIDENCE' if missing else 'REQUESTED_TOOL_EVIDENCE_AVAILABLE' if required else 'NO_CONFIRMED_SCIENTIFIC_REQUIREMENTS',
        'task_scientific_correctness':'NOT_AUTOMATICALLY_SCORED'}

def present_delivery(inputs,state,planned=(),error='',sequence_check=None):
    audit=requirement_audit(inputs,state,planned)
    text=workflow_answer(inputs,state,error)
    if state.get('render_expression_figures',{}).get('status')=='COMPLETE':
        f=state['render_expression_figures']
        text+='\n候选表达背景作图：原生R已生成'+str(f['pages'])+'页PDF；'+str(f['candidate_count'])+'条本次候选，来源表及图包可下载。表达不改变候选排序。'
    if audit['missing_steps'] and not error:
        text='判定：所要求证据尚未齐全；仅展示已取得部分。\n'+text.split('\n',1)[1]
    rows=verified_rows(inputs.get('candidates',[]),state)
    if rows:
        text+='\n已核验输入与参考字段（直接读取，不由模型复述）：\n'+json.dumps(rows,ensure_ascii=False)
    ref=state.get('verify_target',{}).get('reference_sha256')
    if ref:text+='\n参考文件SHA256：'+ref
    score=state.get('score_candidates',{})
    if score.get('rows'):
        text+='\n分数显示约定：上表为原始scaled值；以下6位小数只供阅读，不改原值：'+json.dumps({r['candidate_id']:format(float(r['oligoformer_scaled_score']),'.6f') for r in score['rows']},ensure_ascii=False)
    if audit['missing_steps']:text+='\n所要求证据尚缺：'+'、'.join(audit['missing_steps'])+'；不能据工具局部成功声称整题全部完成。'
    text+='\n来源日期：仅采用实际文件元数据；当前未提供来源日期，不补造日期。历史导入与本轮执行状态见各工具原记录。'
    if error:
        text+='\n复用边界：旧分数只对原序列、链角色、参考、工具参数和数据版本有效；输入绑定不一致时不能沿用。旧输入、原始来源及失败可保留作记录；受变更影响的比对、上下文、分数和seed证据需重新核查，未取得新结果则明确留空。'
    if sequence_check and sequence_check['status']=='FAIL':
        text+='\n模型文字序列检查未通过；原文另存诊断。上述字段仍来自实际工具，不把原模型文字替换成新的成功回答。'
    return {'model_summary_display':text,'delivery_audit':audit,
            'answer_source':'SHARED_VERIFIED_FIELD_PRESENTATION',
            'model_interpretation_scope':'Original generated explanation is preserved separately as diagnostic text; it is not the source of displayed values.'}
