"""Summarize all recorded units; preserve original answers and blank human scores."""
import argparse,collections,csv,gzip,hashlib,io,json,zipfile
from pathlib import Path

def save_json(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
def table(path,rows):
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t');w.writeheader();w.writerows(rows)

def finalize(root):
    root=Path(root);folder=root/'three_arm'
    rs=json.loads(gzip.decompress((folder/'results.json.gz').read_bytes()))
    audit=json.loads((folder/'audit.json').read_text(encoding='utf-8'))
    assert len(rs)==54 and audit['completion']['pending']==0
    requests=audit['actual_request_checks'];groups=['llm','workflow','agent']
    usage={g:{'total_tokens':sum(r['total_tokens'] for r in rs if r['group']==g) if all(
        r.get('usage_complete') for r in rs if r['group']==g) else None,
        'known_token_subtotal':sum(r.get('known_token_subtotal') or 0 for r in rs if r['group']==g),
        'unknown_answer_ids':[r['answer_id'] for r in rs if r['group']==g and not r.get('usage_complete')]}
        for g in groups}
    addendum=[]
    for r in rs:
        original_error=r.get('record',{}).get('result',{}) or {}
        if original_error.get('status')=='FAILED':
            addendum.append({'answer_id':r['answer_id'],'source':'original record.result and record.events',
                'original_error':original_error,
                'original_tool_errors':[e for e in r['record'].get('events',[]) if e.get('kind')=='tool_failed'],
                'answer_unchanged':True,'human_score':None})
    save_json(folder/'reviewer_context_addendum.json',addendum)
    rows=[]
    for r in rs:
        error=r.get('provider_error') or (r.get('record',{}).get('result',{}) or {}).get('message','')
        rows.append({'answer_id':r['answer_id'],'case_id':r['case_id'],'group':r['group'],'repeat':r['repeat'],
            'status':r['status'],'seconds':r.get('seconds'),'tool_calls':r['tool_calls'],
            'completed_tools':';'.join(r.get('completed_tools',[])),
            'model_calls':len([x for x in requests if x['answer_id']==r['answer_id']]),
            'total_tokens':r.get('total_tokens'),'usage_complete':r.get('usage_complete'),
            'original_error':json.dumps(error,ensure_ascii=False) if isinstance(error,dict) else error,
            'answer':r.get('answer',''),'human_quality_score':''})
    table(folder/'records.tsv',rows)
    table(folder/'model_calls.tsv',[{'answer_id':x['answer_id'],'stage':x['stage'],'model':x['model'],
        'max_output_tokens':x['max_output_tokens'],'thinking':json.dumps(x['thinking']),
        'response_id':x.get('response_id'),'request_id':x.get('request_id'),
        'response_status':x.get('response_status'),'incomplete_details':json.dumps(x.get('incomplete_details')),
        'usage':json.dumps(x.get('usage',{}))} for x in requests])
    summary={'run_id':audit['completion']['run_id'],'runtime_commit':audit['runtime']['commit'],
        'planned':54,'recorded':len(rs),'pending':0,'state_counts':audit['state_counts'],
        'states_by_case':{c:{g:dict(collections.Counter(r['status'] for r in rs if r['case_id']==c and r['group']==g))
            for g in groups} for c in dict.fromkeys(r['case_id'] for r in rs)},
        'actual_model_requests':len(requests),'request_stages':dict(collections.Counter(x['stage'] for x in requests)),
        'response_statuses':dict(collections.Counter(x.get('response_status') for x in requests)),
        'responses_with_incomplete_details':[x['answer_id'] for x in requests if x.get('incomplete_details')],
        'provider_error_answer_ids':[r['answer_id'] for r in rs if r.get('provider_error')],
        'usage_by_group':usage,'generic_failure_answer_ids':[r['answer_id'] for r in rs if r.get('answer')=='这次请求没能完成。'],
        'same_raw_input':audit['same_raw_inputs'],'independent_scores_filled':False,
        'note':'Technical completeness is not scientific accuracy. Generic failure answers remain unchanged and must not be replaced by their error details in scoring.'}
    save_json(folder/'technical_summary.json',summary)
    target=folder/'for_review_complete.zip';assert not target.exists(),'Use a new review bundle path'
    with zipfile.ZipFile(folder/'for_review.zip') as source,zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as out:
        for name in source.namelist():out.writestr(name,source.read(name))
        out.writestr('reviewer_context_addendum.json',(folder/'reviewer_context_addendum.json').read_bytes())
        out.writestr('shared_scientific_references.zip',(root/'shared_scientific_references.zip').read_bytes())
        out.writestr('shared_scientific_references.receipt.json',(root/'shared_scientific_references.receipt.json').read_bytes())
        tasks=json.loads(source.read('complete_tasks.json'));rubric=json.loads(source.read('rubric.json'))
        text=['# 完整题目输入与逐题要求','原始回答不改写；人工分数全部留空。完整原始字段如下，不能只按一句需求评分。']
        for task in tasks:
            text.extend(['## '+task['case_id'],task['request'],'### 完整原始/解析输入',
                '```json',json.dumps(task,ensure_ascii=False,indent=2),'```'])
        text.extend(['## 共用评分与失败处理标准','```json',json.dumps(rubric,ensure_ascii=False,indent=2),'```'])
        out.writestr('TASKS_AND_CRITERIA.md','\n\n'.join(text))
        out.writestr('READ_FIRST.md','''# 本包未评分

先读TASKS_AND_CRITERIA.md、shared_resources.json与field_guide.json，再对照原始回答、输入和证据填写blank_scores.tsv。
原始for_review文件逐字节复制；补充材料在运行后添加，不修改答案或代填分数。
reviewer_context_addendum.json补充原始错误记录中已存在、但原评审导出未附的具体输入拦截原因。
评分仍评价用户实际收到的原回答；不能用补充错误信息替两条笼统失败回答补成成功。
shared_scientific_references.zip提供完整同版本底表以便查数；不是无工具模型当时收到的输入结果。
本包无组别密钥；不要另取上层private_key.tsv、records.tsv、technical_summary.json或完整运行原包给评审。
系统状态、工具数量、答复长度不当科学分数；六题是已见开发题，风格可能暴露配置。
''')
    with zipfile.ZipFile(target) as out,zipfile.ZipFile(folder/'for_review.zip') as original:
        assert out.testzip() is None and not any('private_key' in n for n in out.namelist())
        for name in original.namelist():assert out.read(name)==original.read(name)
        blank=list(csv.DictReader(io.StringIO(out.read('blank_scores.tsv').decode('utf-8-sig')),delimiter='\t'))
        assert len(blank)==54 and all(not r[k] for r in blank for k in ('reviewer_id','accuracy_0_2','evidence_0_2','task_fit_0_2','limits_0_2'))
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);a=p.parse_args();finalize(a.root)
