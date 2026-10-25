/* English interface labels only. Never pass model answers or source passages here. */
(function(root){
 const sequenceLabels={PASS:'Sequence check passed',FAIL:'Sequence check failed - original answer conflicts with verified fields',NO_SEQUENCE_CLAIMS:'No sequence claims to check',NOT_CHECKED_NO_VERIFIED_SEQUENCE:'Sequence check unavailable: no verified sequence evidence',NO_MODEL_ANSWER:'No model answer to check'};
 const labels={
  '豆包LLM规划':'Model-generated plan','预设引导路径（未调用LLM规划）':'Preset guided path (no model planning)',
  '当前实例临时文件；重启或部署可能丢失。请导出文库并自行保存。':'Temporary instance storage. Restarts or deployments may remove files. Export and retain a library backup.',
  '文献全文（文字部分）':'Article full text (text only)','文献全文':'Article full text','仅摘要':'Abstract only','官方工具文档':'Official tool documentation','官方工具源码':'Official source code','官方源码文本':'Official source code','项目设置说明（待外部审核）':'Project setting (not independently reviewed)','项目设置说明':'Project setting','本地计算记录':'Local computation record',
  '任务规划已返回':'Task plan returned','执行助手正在选择下一步':'Execution model selecting the next step','执行助手已返回':'Execution model returned','等待模型选择下一步':'Waiting for model decision','豆包已返回下一步':'Model decision returned','固定工具流程；本次没有调用大模型':'Fixed workflow; no model call','API Agent开始；由模型选择并调用工具':'Agent started; the model selects tool calls','模型工具调用完成；数值报告以程序表格为准':'Model tool calls finished; numeric results follow the structured evidence',
  '请先填写模型ID':'Enter a model ID first','已检测到密钥，还需模型ID或ep-接入点ID':'API key detected; add a model or ep- endpoint ID','配置齐全，尚需连接检查':'Configured; connection check required','API已配置，可以连接检测':'API configured; ready for connection check','API已配置，可检测连接':'API configured; ready for connection check','尚未配置API':'API not configured','已配置，可测试连接':'Configured; connection can be checked',
  '请选择有效候选':'Select valid candidates','候选需为1至20条记录':'Provide 1 to 20 candidate records','细胞状态无效':'Invalid cell state','工具模式无效':'Invalid tool mode','核查数量应为1至5的整数':'Review count must be an integer from 1 to 5','已有任务或连接检查正在运行':'A task or connection check is already running','请先勾选模型API用量确认':'Confirm model API usage before starting','请确认本次运行会产生模型API用量':'Confirm model API usage before starting',
  '此小文库不支持本项目患者疗效或临床给药结论。':'This scoped library does not support patient efficacy or clinical dosing conclusions for this project.',
  '范围规则停止，未检索。':'Stopped by scope rules; no retrieval performed.',
  '已实际检索，未找到片段；未调用模型，也未联网。':'Search completed without matching snippets; no model call or online search.',
  '依据本轮实际检索片段；来源类别和页码可展开查看。引用编号核对不代替原文含义复核。':'Based on snippets retrieved for this question. Expand source types and locators. Citation-ID checks do not replace semantic review.',
  '依据当前记录或一般知识；本轮没有取得可核查来源':'Based on current records or general knowledge; no verifiable source was retrieved for this answer.',
  '请先确认本次最多2题演示会调用模型并产生用量。':'Confirm API usage for this demo of up to two questions before starting.',
  '需先确认本次诊断或开发评价会调用模型并产生用量':'Confirm model API usage for the diagnostic or development evaluation before starting.',
  '本项目2026-10-16整理的ARPE-19基线表达表':'Project ARPE-19 baseline expression prepared on 16 October 2026'
 };
 const kinds={article_full_text:'Article full text',abstract:'Abstract only',official_documentation:'Official documentation',official_source_code:'Official source code',project_setting:'Project setting',project_record:'Local computation record'};
 function uiLabel(value){const text=String(value??'');return labels[text]||text}
 function uiSourceLabel(source){return kinds[source.source_kind]||uiLabel(source.source_label||source.kind||'')}
 function uiSequenceLabel(check){return sequenceLabels[check.status]||check.status}
 function uiLocator(hit){return (hit.page?'PDF p. '+hit.page:'Text')+' · '+(hit.chunk_id||uiLabel(hit.locator||''))}
 Object.assign(root,{uiLabel,uiSourceLabel,uiSequenceLabel,uiLocator});
 if(typeof module!=='undefined')module.exports={uiLabel,uiSourceLabel,uiSequenceLabel,uiLocator};
})(typeof window!=='undefined'?window:globalThis);
