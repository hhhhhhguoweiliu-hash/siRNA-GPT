"""Readable reviewer cards from actual deliveries; no invented answers or grades."""
import csv
import hashlib
import html
import json
import re
import shutil
import zipfile
from pathlib import Path
from core import HOME,save_json
from review_import import SCORE_HEADERS,FACT_HEADERS,ADJ_HEADERS


def digest(data):return hashlib.sha256(data).hexdigest()


def remove_identity(value):
    if isinstance(value,list):return [remove_identity(x) for x in value]
    if isinstance(value,dict):return {k:remove_identity(v) for k,v in value.items()
        if k!='agent_status' and not (k in ('group','mode') and isinstance(v,str) and v in ('llm','workflow','agent','guided'))}
    return value


def score_payload(schedule,fact_specs):
    scores=[SCORE_HEADERS];facts=[FACT_HEADERS];adj=[ADJ_HEADERS]
    for row in schedule:
        aid,cid=row['answer_id'],row['case_id']
        scores.append([aid,cid,*([None]*9)])
        adj.append([aid,cid,*([None]*6)])
        for item in fact_specs[cid]:facts.append([aid,cid,None,item['fact_id'],item['required_fact'],None,None])
    return {'评分表':scores,'逐事实':facts,'裁决':adj}


def export_review(out,cases,plan,results,resources,*,package,fixture_only=False):
    out,package=Path(out),Path(package)
    if not fixture_only and any(r.get('execution_mode')!='provider' for r in results):
        raise ValueError('替身回答不能进入真实评审包')
    review=out/'for_review';review.mkdir(parents=True,exist_ok=False)
    actual={r['answer_id']:r for r in results}
    specs=json.loads((package/'review_only/fact_items_DRAFT.json').read_text(encoding='utf-8'))
    criteria=json.loads((package/'review_only/criteria.json').read_text(encoding='utf-8'))
    bycase={r['case_id']:r for r in criteria}
    reference=review/'reference_for_judgement';reference.mkdir()
    for name in ('criteria.json','anchors.json','fact_items_DRAFT.json','REVIEWER_INSTRUCTIONS.md'):
        shutil.copyfile(package/'review_only'/name,reference/name)
    # These are reference answers, never appended to an arm's actual delivery.
    for name in ('source_originals','purchased_existing_evidence'):
        if (package/'review_only'/name).is_dir():shutil.copytree(package/'review_only'/name,reference/name)
    brief=HOME/'docs/reviews/20261027_expert_briefing_ZH.md'
    shutil.copyfile(brief,review/'PROJECT_BRIEFING_ZH.md')
    copied=review/'PROJECT_BRIEFING_ZH.md'
    copied.write_text(copied.read_text(encoding='utf-8').replace(
        '../../research/2026-10-27_evaluation_fixes_v2/REVIEW_IMPORT.md',
        'reference_for_judgement/REVIEWER_INSTRUCTIONS.md'),encoding='utf-8')
    save_json(review/'allowed_resources.json',{'files':resources['files'],
        'ordinary_model':'共同原始输入；无科学工具或外网','tool_configurations':'相同科学资源、不同选路方式；多轮调用数可不同',
        'reference_evidence_is_not_actual_delivery':True})
    save_json(review/'score_workbook_payload.json',{'kind':'BLANK_HUMAN_FIELDS_NOT_SCORED','sheets':score_payload(plan['schedule'],specs)})
    sheets=score_payload(plan['schedule'],specs)
    for name,rows in sheets.items():
        with (review/(name+'_blank.tsv')).open('w',encoding='utf-8-sig',newline='') as f:
            csv.writer(f,delimiter='\t').writerows(rows)
    keys=[];analysis_plan=[];execution=[];file_checks=[]
    for item in plan['schedule']:
        aid,cid=item['answer_id'],item['case_id'];r=actual.get(aid)
        keys.append(item)
        case=next(c for c in cases if c['id']==cid)
        analysis_plan.append({**item,'category':case['category'],'family':case['family'],
            'required_fact_ids':[f['fact_id'] for f in specs[cid]]})
        execution.append({'answer_id':aid,'execution':'ATTEMPTED' if r else 'NOT_EXECUTED',
            'seconds':r.get('seconds') if r else None,'model_requests':r.get('real_model_requests') if r else None,
            'real_total_tokens':r.get('total_tokens') if r else None})
        folder=review/'answers'/aid;folder.mkdir(parents=True)
        save_json(folder/'input.json',{'rounds':case['rounds']})
        if not r:
            (folder/'answer.txt').write_text('未运行；没有实际回答，不得评分。\n',encoding='utf-8')
            save_json(folder/'process.json',{'execution':'NOT_EXECUTED','no_answer_or_evidence_invented':True})
            continue
        transcript=[];raw=[];process=[]
        for turn in r['rounds']:
            n=turn['round']
            transcript.append('第'+str(n)+'轮\n'+turn['answer'])
            if turn.get('raw_model_answer') is not None:raw.append('第'+str(n)+'轮\n'+turn['raw_model_answer'])
            process.append(remove_identity({k:turn.get(k) for k in ('round','execution','status','planned_tools',
                'completed_tools','tool_results','error','error_record','planner_task_update_check','common_input_sha256')}))
            for rel in turn.get('delivered_files',[]):
                path=out/aid/rel
                if not path.is_file() or path.resolve().is_relative_to((out/aid).resolve()) is False:
                    raise ValueError('交付附件路径无效')
                # Model prompts, run configuration, events and owner-side plans are
                # method evidence, not the scientist's delivered report attachments.
                if any(part=='attempts' for part in path.parts) or path.name.startswith('model_') or path.name in (
                    'input.json','run_config.json','plan.json','result.json'):continue
                dest=folder/'attachments'/rel;dest.parent.mkdir(parents=True,exist_ok=True)
                original=path.read_bytes();data=original;transform='NONE'
                if path.suffix=='.json':
                    parsed=json.loads(original)
                    cleaned=remove_identity(parsed)
                    if cleaned!=parsed:
                        data=json.dumps(cleaned,ensure_ascii=False,indent=2).encode('utf-8')
                        transform='Explicit configuration metadata group/mode/agent_status removed; scientific content unchanged'
                elif path.name=='report.html':
                    text=original.decode('utf-8')
                    text,count=re.subn(r'<p>(?:API Agent|Guided tools \(no LLM\)|Fixed-workflow demonstration · No model call) \| [^<]+</p>',
                        '<p>Anonymous delivery '+aid+' · round '+str(n)+'</p>',text,count=1)
                    if count:data=text.encode('utf-8');transform='Configuration label and original run identifier removed from report heading only'
                elif path.suffix=='.jsonl':
                    parsed=[json.loads(line) for line in original.decode('utf-8').splitlines() if line.strip()]
                    cleaned=remove_identity(parsed)
                    if parsed!=cleaned:
                        data=('\n'.join(json.dumps(x,ensure_ascii=False) for x in cleaned)+'\n').encode('utf-8')
                        transform='Explicit configuration identity metadata removed from event records only'
                dest.write_bytes(data)
                file_checks.append({'answer_id':aid,'review_path':dest.relative_to(review).as_posix(),
                    'source_sha256':digest(original),'review_sha256':digest(data),'transformation':transform})
        answer='\n\n'.join(transcript)
        (folder/'answer.txt').write_text(answer,encoding='utf-8')
        (folder/'raw_model_answer.txt').write_text('\n\n'.join(raw),encoding='utf-8')
        (folder/'answer.html').write_text('<!doctype html><meta charset="utf-8"><title>'+aid+'</title><style>body{font:16px/1.7 Arial,sans-serif;max-width:1000px;margin:30px auto}pre{white-space:pre-wrap;overflow-wrap:anywhere}</style><h1>'+aid+'</h1><pre>'+html.escape(answer)+'</pre>',encoding='utf-8')
        save_json(folder/'process.json',{'rounds':process,'scope':'Actual steps and delivered evidence; not hidden model reasoning. Reference answers are separate.'})
        attachments=folder/'attachments';attachments.mkdir(exist_ok=True)
        attached=any(p.is_file() for p in attachments.rglob('*'))
        (attachments/'README.md').write_text('这里仅有本答复实际取得的附件匿名副本；参考底表另放，不能当成本答复证据。\n' if attached else '本答复未交付科学附件；请按实际原文和过程判断，不能用参考底表事后补证据。\n',encoding='utf-8')
    save_json(out/'analysis_plan.json',analysis_plan);save_json(out/'actual_execution.json',execution)
    save_json(out/'private_group_key.json',keys)
    save_json(review/'attachment_transformations.json',file_checks)
    intro='# 评审阅读入口\n\n'
    if fixture_only:intro+='**程序HTTP替身检查专用，不是真实模型回答，禁止用于科研评分或论文。**\n\n'
    intro+='先读[项目说明](PROJECT_BRIEFING_ZH.md)，再按下面题卡阅读。全部任务为已见开发材料；不是独立未见测试。所有人工字段空白。参考底表与各答复实际交付严格分开，不给缺证据的回答事后补答案。\n\n'
    for case in cases:
        cid=case['id'];path=review/'cards'/ (cid+'.md');path.parent.mkdir(exist_ok=True)
        text='# '+cid+'：完整题卡（已见开发材料）\n\n'
        purpose={'W1':'已购试剂小试前核对序列和证据版本；不能用预测代替实测。',
            'W2':'按限定需求核对参考，不用额外筛选代替任务。','W2b':'准确取得与序列及上下文绑定的已有分数。',
            'W3':'同时考虑分数和近匹配警告，允许有依据的不同建议。','U1':'保留首轮并响应新增科研需求。',
            'R1':'缺链角色时澄清，避免擅自截短或分配。','R2':'变动序列不套用原分数。',
            'R3':'核对序列、参考和声明坐标的一致性。','R4':'表达缺项不偷偷用其他数据代替。'}
        text+='实际用途：'+purpose.get(cid,'依据来源核对所请求的科学证据。')+'\n\n'
        text+='类别：'+case['category']+'；共同母题：'+case['family']+'。多轮题合起来评价一个任务。\n\n'
        text+='## 科研用途、完整问题与判断依据\n\n'+bycase[cid]['full_question_and_judgement_standard_from_uploaded_review']+'\n\n'
        text+='## 原始输入和每轮条件全文\n\n```json\n'+json.dumps(case['rounds'],ensure_ascii=False,indent=2)+'\n```\n\n'
        text+='允许资源见[资源表](../allowed_resources.json)；[事实标准草案](../reference_for_judgement/fact_items_DRAFT.json)和[定位依据](../reference_for_judgement/anchors.json)供判断，不算某份答复实际交付。\n\n## 实际匿名交付\n\n'
        for item in plan['schedule']:
            if item['case_id']!=cid:continue
            aid=item['answer_id'];r=actual.get(aid)
            text+='- '+aid+'：'+('已尝试，保留各轮原文与失败' if r else '未运行；无回答，不可评分')+'；[全文](../answers/'+aid+'/answer.txt)、[原始输入](../answers/'+aid+'/input.json)、[实际过程与证据](../answers/'+aid+'/process.json)'
            if r:text+='、[安全阅读页](../answers/'+aid+'/answer.html)、[模型原文字段](../answers/'+aid+'/raw_model_answer.txt)、[实际附件目录](../answers/'+aid+'/attachments/)'
            text+='。\n'
        text+='\n评分位置：评分表按上述答复编号填写四维、交付、严重错误和理由；逐事实表按相同编号逐项核对。空白不是0。完成与必要事实/严重错误矛盾时等待人工核对。不能只按工具数或程序完成状态评分。\n'
        path.write_text(text,encoding='utf-8')
        intro+='- ['+cid+'完整题卡](cards/'+cid+'.md)\n'
    intro+='\n附件匿名副本只移除明确配置身份字段或报告标题身份，科学数值和回答原文不改；逐文件变化及原/副本指纹见attachment_transformations.json。未改原件保留在执行端完整包。工具过程/文风可能暴露来源，不声称完全盲法。组别密钥、模型原始HTTP与修复讨论不在本包。\n\n'
    intro+='score_workbook_payload.json及三个_blank.tsv用于生成编号一致的Excel；执行端回收运行包后用现有官方表格工具生成XLSX并读回检查，再交正式评分。不能把旧33行空表冒充本批匹配表。当前不要填写替身、未运行位置或虚构的人名。\n'
    (review/'README.md').write_text(intro,encoding='utf-8')
    with zipfile.ZipFile(out/'reviewer_package.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(review.rglob('*')):
            if p.is_file():z.write(p,p.relative_to(review))
    with zipfile.ZipFile(out/'reviewer_package.zip') as z:
        assert z.testzip() is None
        assert not any('private_group' in n or 'http_attempt_' in n for n in z.namelist())
