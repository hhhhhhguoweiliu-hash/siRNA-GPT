"""Shared answer/field contract. No model, scientific method, or quality scoring."""
import hashlib,json

FINAL_ANSWER_STYLE = (
    '最终答复统一为四部分：判定、关键结果、证据、限制或下一步。简短中文，不重复抄长输入。'
    '关键结果按需用短表：完整排序题仅列所要求候选；仅核对题保留全部候选的核对结果。'
    '无工具证据时可引用原始输入已有字段并明确来源，不得猜测缺失结果或假装新计算。'
    '异常输入指出已提供的具体序列及其问题，不再索要已经提供的碱基；不举未经计数的序列示例。'
    '19nt为本系统当前明确配对核心要求，不是所有siRNA的生物学定律。')
FIELD_GUIDE = {
    'seed_site_count_all': 'seed位点数，包含目标VEGFA时明确标注；不是基因数',
    'seed_site_count_nontarget': '排除VEGFA后的seed位点数',
    'matched_genes': '排除VEGFA后的去重seed匹配基因数',
    'baseline_mapped_genes': '上述非靶基因中可映射表达表的去重基因数',
    'state_detected_genes': '上述已映射基因中指定状态至少2/4皿TPM>=1的基因数',
    'unmapped_genes': '未映射表达表，不等于不表达',
    'design_window_start_1based': '来源记录的23nt设计窗口起点，不是19nt核心起点',
    'target_start_1based / target_end_1based': '原始候选表中23nt设计窗口坐标，不得改叫19nt核心坐标或未经比对声称已验证',
    'core_matches_n / all_20_transcripts_core_match': '原始输入已有参考覆盖注释；转述它不算本轮独立运行比对',
    'core_start_1based': '在明确参考转录本上实际比对所得19nt核心起点；1-based闭区间',
    'score': 'OligoFormer模型分数，不是敲低百分比',
}
FIELD_INSTRUCTIONS = '字段必须按以下含义表达，不混称脱靶数：'+json.dumps(FIELD_GUIDE,ensure_ascii=False)

def input_sha256(inputs):
    return hashlib.sha256(json.dumps(inputs,ensure_ascii=False,sort_keys=True,
        separators=(',',':')).encode('utf-8')).hexdigest()

def workflow_answer(inputs,results,error=''):
    """Presentation of actual new workflow results; never rewrites model answers."""
    def table(headers,body):
        return '\n'.join([' | '.join(headers),' | '.join(['---']*len(headers))]+
                         [' | '.join(str(v) for v in row) for row in body])
    report=results.get('compile_report',{})
    score_result=results.get('score_candidates',{})
    score_rows=score_result.get('rows',[])
    target_rows=results.get('verify_target',{}).get('rows',[])
    selected=report.get('selected_for_review')
    requested=inputs.get('task',{}).get('evaluation_conditions',{}).get('compare_all_requested_candidates',False)
    visible=None if selected is None or requested else set(selected)|{r['candidate_id'] for r in report.get('rows',[]) if r.get('review_flags')}
    show=lambda row:visible is None or row['candidate_id'] in visible
    lines=[]
    if error:
        supplied=[{'candidate_id':r.get('candidate_id'),**{k:v for k,v in r.items() if 'guide' in k and ('core' in k or '21nt' in k)}} for r in inputs['candidates']]
        lines.append(error+'；原始输入：'+(json.dumps(supplied,ensure_ascii=False) if len(supplied)<=1 else '已提供'+str(len(supplied))+'条候选'))
        lines.append('已完成工具：'+('、'.join(results) or '无')+'；以下只展示实际已取得的证据。')
    if target_rows:
        lines.append(table(['候选','参考','19nt核心起止(1-based)','参考转录本覆盖'],[
            [r['candidate_id'],r['reference_transcript'],
             ';'.join(str(s['start_1based'])+'–'+str(s['start_1based']+18) for s in r['sites'] if s['transcript']==r['reference_transcript']),
             str(r['covered_transcripts'])+'/'+str(r['reference_transcript_count'])] for r in target_rows if show(r)]))
        for r in target_rows:
            for claim in r.get('declared_coordinate_checks',[]):
                lines.append('用户坐标声明核对：'+json.dumps({'candidate_id':r['candidate_id'],**claim},ensure_ascii=False))
    if score_rows:
        lines.append(table(['候选','模型分数(scaled，原始精度)','raw_class1','来源状态'],[
            [r['candidate_id'],r['oligoformer_scaled_score'],r.get('raw_class1','未提供'),score_result.get('status','未知')] for r in score_rows if show(r)]))
    if report.get('rows'):
        lines.append(table(['候选','复核警告','近匹配窗口/转录本','当前规则列为优先核查'],[
            [r['candidate_id'],r.get('review_flags') or '未见当前规则的已知提示，不代表安全',
             r.get('near_match_transcripts') or '见绑定记录；未见提示不代表全范围无匹配',r.get('selected_for_review',False)]
            for r in report['rows'] if show(r)]))
    supplied_evidence=inputs.get('task',{}).get('user_provided_evidence',{})
    near=supplied_evidence.get('near_match_review',[])
    if near:
        lines.append('用户提供的既有近匹配核对记录（非本轮重新扫描）：\n'+table(
            ['候选','实际查询窗口','查询序列5′→3′','参考/坐标','基因','错配数'],[
            [r['candidate_id'],r['query_definition'],r['guide_window_5to3'],
             r['reference_transcript']+':'+r['reference_start_1based']+'–'+r['reference_end_1based'],r['mapped_gene'],r['actual_mismatches']] for r in near]))
    expression=results.get('query_expression',{}).get('candidate_summary',[])
    if expression:
        lines.append(table(['候选','seed位点(含VEGFA)','非靶seed位点','去重非靶匹配基因','可映射基因','常氧检出基因','缺氧检出基因','未映射基因'],[
            [r['candidate_id'],r['seed_site_count_all'],r['seed_site_count_nontarget'],r['matched_genes'],
             r['baseline_mapped_genes'],r['normoxia_detected_genes'],r['hypoxia_detected_genes'],r['unmapped_genes']] for r in expression if show(r)]))
    elif 'match_seed' in results:
        lines.append('已取得guide seed位点（含VEGFA）：'+json.dumps(results['match_seed'].get('seed_site_counts_all',{}),ensure_ascii=False)+'；未取得表达关联，不填零。')
    if selected is not None:
        lines.append('当前工作规则的优先核查名单：'+('、'.join(selected) or '无')+'；不是生物学最佳答案。')
    evidence='本轮实际完成：'+('、'.join(results) or '无成功科学工具')+'。'
    if target_rows:evidence+='核心坐标来自verify_target，不用23nt设计窗口坐标代替。'
    if score_rows:evidence+='分数导入来源指纹：'+str(score_result.get('source_sha256') or score_result.get('legacy_source_sha256') or score_rows[0].get('evidence_dataset_id','未提供'))+'。'
    if report:evidence+='交付报告：'+report.get('report','report.html')+'；全部候选底表：'+report.get('table','candidates_ranked.tsv')+'。'
    limits=[]
    if not score_rows:limits.append('未评分')
    if 'match_seed' not in results:limits.append('未做seed分析')
    if not expression:limits.append('未做表达关联')
    if report:limits.append('分数不是敲低率；seed不是实测脱靶；表达仅作注释、不改变排序；警告不是实测脱靶，无提示不是安全认证')
    else:limits.append('未选top候选；分数不是敲低率；参考覆盖不等于细胞内异构体表达')
    if any(r.get('original_row1') for r in inputs.get('candidates',[])):
        limits.append('两行链角色仅按用户明确计算假设使用，不是供应商确认；原始TT/N3保留，模型未模拟N3连接实物')
    if expression:limits.append('同一培养批次、每状态4皿、未转染；缺氧1% O2 24h；检出为至少2/4皿TPM≥1，不是实际敲低效果')
    if error:limits.append('未完成部分不当作结果；确认支持的目标、链身份及19nt核心，不自动截短21nt或回退缺失数据')
    verdict=('停止后续计算；已有局部证据保留。' if error else '本题报告流程完成；以下仅为优先复核证据。' if report else
             '所要求的参考及模型分数核查完成。' if score_rows else '所要求的候选及转录本核对完成。')
    return '判定：'+verdict+'\n关键结果：\n'+'\n\n'.join(lines)+'\n证据：'+evidence+'\n限制或下一步：'+'；'.join(limits)+'。'
