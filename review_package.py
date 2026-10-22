"""Complete anonymous review context; group key remains outside for_review/."""
import csv,json
from pathlib import Path
from core import HOME,save_json
from conversation import prepare_inputs
from evaluation_contract import FIELD_GUIDE

def export_review_package(out,cases,results):
    from evaluate import write_rows
    review=out/'for_review';review.mkdir(parents=True,exist_ok=True)
    case_map={c['id']:c for c in cases};rubric_path=HOME/'evaluation_rubric.json'
    rubric=json.loads(rubric_path.read_text(encoding='utf-8'))
    save_json(review/'rubric.json',rubric);save_json(review/'field_guide.json',FIELD_GUIDE)
    full=[]
    for c in cases:
        inputs=prepare_inputs({**c.get('input',{}),**c.get('task',{}),'message':c['request'],'tool_mode':'imported','web_enabled':False})
        full.append({'case_id':c['id'],'request':c['request'],'raw_input':c.get('input',{}),
            'raw_task_fields':c.get('task',{}),'resolved_input':inputs,
            'requirements':rubric['case_requirements'].get(c['id'],{})})
    save_json(review/'complete_tasks.json',full)
    fields=['answer_id','case_id','request','answer','input_file','evidence_file','reviewer_id',
            'accuracy_0_2','evidence_0_2','task_fit_0_2','limits_0_2','unscorable_reason','notes']
    rows=[];availability=[]
    for r in results:
        identity=r['answer_id'];folder=review/'answers'/identity;folder.mkdir(parents=True,exist_ok=True)
        c=case_map[r['case_id']]
        source=out/identity/'case_input.json'
        inputs=json.loads(source.read_text(encoding='utf-8')) if source.exists() else next(x for x in full if x['case_id']==r['case_id'])
        save_json(folder/'input.json',inputs)
        # Actual evidence, including input-provided annotations; no group or repeat key.
        tool_results=r.get('tool_results',{})
        save_json(folder/'evidence.json',{'tool_results':tool_results,
            'execution_error':r.get('provider_error') or (r.get('record',{}).get('result') if r.get('status')=='FAILED' else None),
            'evidence_scope':'Tool outputs only if actually obtained; input-provided fields are in input.json. No independent wet-lab proof.'})
        answer=r.get('answer','');(folder/'answer.txt').write_text(answer,encoding='utf-8')
        rows.append(dict.fromkeys(fields,'')|{'answer_id':identity,'case_id':r['case_id'],
            'request':c['request'],'answer':answer,'input_file':str((folder/'input.json').relative_to(review)).replace('\\','/'),
            'evidence_file':str((folder/'evidence.json').relative_to(review)).replace('\\','/')})
        availability.append({'answer_id':identity,'case_id':r['case_id'],'has_text':bool(answer),
            'reported_output_or_system_error':bool(r.get('provider_error')) or r.get('status') in ('FAILED','TIMED_OUT','INCOMPLETE_OR_CLARIFICATION'),
            'quality_score':'','independent_reviewer_id':''})
    write_rows(review/'blind_answers.tsv',rows,fields)
    write_rows(review/'blank_scores.tsv',[{k:x[k] for k in fields if k not in ('answer','request')} for x in rows],
        [k for k in fields if k not in ('answer','request')])
    save_json(review/'availability_unscored.json',availability)
    protocol=out/'protocol.json'
    if protocol.exists():
        p=json.loads(protocol.read_text(encoding='utf-8'))
        save_json(review/'shared_resources.json',{'model':p.get('model'),'model_settings':p.get('model_settings'),
            'scientific_assets':{k:v for k,v in p.get('runtime',{}).get('assets',{}).items() if k.startswith('data/')},
            'tools':'same scientific tool pool for tool-enabled configurations; no external web',
            'differences':['one configuration has no scientific tools','one has a human-selected preset path','one may plan and make multiple model requests'],
            'shared_raw_input':True,'blindness_limit':'Evidence and writing style may reveal configuration; identifiers removed, no claim of perfect blinding'})
    (review/'README.md').write_text('''# 独立评审材料（未评分）

先读complete_tasks.json中的完整原始/解析输入和逐题要求，再读rubric.json及field_guide.json。
blind_answers.tsv与answers/保留原始回答，不做改写；对应input.json和evidence.json供核对。
填写blank_scores.tsv，保留评审编号和具体依据；空白不是0分。不要按工具数、COMPLETE或回复长度评分。
shared_resources.json说明资源与模型设置：普通模型无科学工具，两个工具条件共享科学数据；固定流程预选路径，Agent多轮，总预算不等同。
不向评审提供上一层private_key.tsv或完整运行原包。当前只移除组别标记，风格和证据可暴露配置，不能承诺完全盲法。
可用性/系统失败与科学质量分开；不可评分写原因，失败仍保留。六题为已见开发题，不是独立正式测试。
''',encoding='utf-8')
