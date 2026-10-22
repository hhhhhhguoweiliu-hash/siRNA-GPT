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
    rows=results.get('verify_target',{}).get('rows',[])
    report=results.get('compile_report',{})
    if error:
        supplied=[]
        for row in inputs['candidates']:
            seq={k:v for k,v in row.items() if 'guide' in k and ('core' in k or '21nt' in k)}
            if seq:supplied.append({'candidate_id':row.get('candidate_id'),**seq})
        detail=json.dumps(supplied,ensure_ascii=False) if len(supplied)<=1 else '已提供'+str(len(supplied))+'条候选'
        return '判定：停止后续计算。\n关键结果：'+error+'；原始输入：'+detail+'。\n证据：本题原始输入及输入检查错误；未执行后续评分或排序。\n限制或下一步：确认支持的目标、链身份和明确19nt配对核心；不自动截短21nt。'
    selected=report.get('selected_for_review')
    if selected is not None:
        scores={r['candidate_id']:r for r in results['score_candidates']['rows']}
        expression={r['candidate_id']:r for r in results['query_expression']['candidate_summary']}
        lines=['候选 | 模型分数 | seed位点(含VEGFA) | 去重非靶匹配基因 | 可映射基因 | '+inputs['task']['state']+'检出基因',
               '--- | --- | --- | --- | --- | ---']
        for cid in selected:
            r=expression[cid]
            lines.append(' | '.join(map(str,[cid,round(scores[cid]['oligoformer_scaled_score'],4),
                r['seed_site_count_all'],r['matched_genes'],r['baseline_mapped_genes'],r['state_detected_genes']])))
        return ('判定：本题报告流程完成；以下仅为优先复核名单。\n关键结果：\n'+'\n'.join(lines)+
            '\n证据：候选/参考核对、以前保存的官方分数和seed匹配、两状态表达关联、报告文件。'
            '\n限制或下一步：分数不是敲低率；seed不是实测脱靶；表达仅作注释、不改变排序；合成形式和实验仍待核对。')
    lines=['候选 | 参考 | 19nt核心起止(1-based) | 参考转录本覆盖','--- | --- | --- | ---']
    for row in rows:
        sites=[s for s in row['sites'] if s['transcript']==row['reference_transcript']]
        coords=';'.join(str(s['start_1based'])+'–'+str(s['start_1based']+18) for s in sites)
        lines.append(' | '.join(map(str,[row['candidate_id'],row['reference_transcript'],coords,
            str(row['covered_transcripts'])+'/'+str(row['reference_transcript_count'])])))
    return ('判定：所要求的候选及转录本核对完成。\n关键结果：\n'+'\n'.join(lines)+
        '\n证据：本次候选检查和参考序列比对；核心坐标来自verify_target，不用23nt设计窗口坐标代替。'
        '\n限制或下一步：未评分、未做seed/表达分析、未选top候选；参考覆盖不等于细胞内异构体表达。')
