import fs from 'node:fs/promises';
import path from 'node:path';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
const require=createRequire(pathToFileURL(path.resolve('.test_tmp/review_forms/runtime.cjs')));
const { Workbook,SpreadsheetFile }=await import(pathToFileURL(require.resolve('@oai/artifact-tool')).href);
const source=JSON.parse(await fs.readFile('.test_tmp/review_forms/source.json','utf8'));
const out=path.resolve('research/2026-10-22_review_ready');
const previews=path.resolve('.test_tmp/review_forms/previews');await fs.mkdir(previews,{recursive:true});
const wb=Workbook.create();
const score=wb.worksheets.add('评分表');const answers=wb.worksheets.add('原始回答');
const standards=wb.worksheets.add('题目与标准');const inputs=wb.worksheets.add('完整输入');
const names={normal_hypoxia:'缺氧完整筛选',normal_normoxia:'常氧完整筛选',target_only:'仅候选与转录本核对',
  invalid_sequence:'AAA异常序列',unsupported_target:'KRAS范围外任务',ambiguous_direction:'21nt链身份不明确'};
const font={name:'Arial',size:11,color:'#172435'};
function base(s,range){s.showGridLines=false;s.getRange(range).format.font=font;s.getRange(range).format.verticalAlignment='center';}
function header(s,range){s.getRange(range).format={fill:'#334B63',font:{...font,bold:true,color:'#FFFFFF'},
  wrapText:true,verticalAlignment:'center',horizontalAlignment:'center',rowHeight:36};}
function width(s,col,pixels){s.getRange(col).format.columnWidthPx=pixels;}
function textHeight(text,maxWidth=140){const count=[...String(text)].reduce((sum,c)=>sum+(c.charCodeAt(0)>255?2:1),0);return Math.max(22,Math.ceil(count/maxWidth)*19+6);}
base(score,'A1:J61');score.tabColor='#334B63';
score.getRange('A2').values=[['54条开发回答独立评分']];score.getRange('A2').format.font={...font,size:15,bold:true};
score.getRange('A4').values=[['填写浅黄色区域。四项各0–2分，空白不代表0；不可评分请写原因。']];
score.getRange('A5').values=[['每位评审单独保存一份。先看原始回答、完整输入及标准，不查看组别密钥或带组别复核。']];
const headers=['匿名回答编号','题目','评审编号','可评分情况','事实准确\n0–2','证据支持\n0–2','需求完成\n0–2','边界处理\n0–2','不可评分原因','评分依据与备注'];
score.getRange('A7:J7').values=[headers];
score.getRange('A8:J61').values=source.answers.map(a=>[a.answer_id,names[a.case_id],null,null,null,null,null,null,null,null]);
const table=score.tables.add('A7:J61',true,'IndependentScores');table.showFilterButton=true;
score.getRange('A8:J61').format.rowHeight=32;
score.getRange('C8:J61').format.fill='#FFF4CF';score.getRange('C8:J61').setNumberFormat('@');
score.getRange('E8:H61').setNumberFormat('0');
score.getRange('E8:H61').dataValidation={rule:{type:'whole',operator:'between',formula1:0,formula2:2}};
score.getRange('D8:D61').dataValidation={rule:{type:'list',values:['可评分','不可评分','部分项目不可评分']}};
score.getRange('E8:H61').format.horizontalAlignment='center';
for(const [col,w] of Object.entries({A:100,B:190,C:100,D:150,E:95,F:95,G:95,H:95,I:200,J:270}))width(score,col+'1:'+col+'61',w);
header(score,'A7:J7');score.freezePanes.freezeRows(7);score.freezePanes.freezeColumns(2);

const lines=source.answers.flatMap(a=>a.answer.split('\n').map((line,i)=>[a.answer_id,i+1,line]));
base(answers,`A1:C${lines.length+1}`);answers.getRange('A1:C1').values=[['匿名回答编号','原始行号','完整原始回答（按原换行分行，未改写）']];
answers.getRange(`A2:C${lines.length+1}`).values=lines;
answers.tables.add(`A1:C${lines.length+1}`,true,'OriginalAnswerLines').showFilterButton=true;
width(answers,`A1:A${lines.length+1}`,100);width(answers,`B1:B${lines.length+1}`,90);width(answers,`C1:C${lines.length+1}`,1080);
answers.getRange(`C2:C${lines.length+1}`).format.wrapText=true;
answers.getRange(`C2:C${lines.length+1}`).format.verticalAlignment='top';
for(let i=0;i<lines.length;i++)answers.getRange(`A${i+2}:C${i+2}`).format.rowHeight=textHeight(lines[i][2]);
header(answers,'A1:C1');answers.freezePanes.freezeRows(1);answers.freezePanes.freezeColumns(2);

const standardRows=[['项目','说明']];
standardRows.push(['评分依据','逐项评价原始回答。后台错误用于解释执行过程，不能替最终回答补分。所有失败仍保留。']);
for(const task of source.tasks)standardRows.push([names[task.case_id],
  '原始需求：'+task.request+'\n应满足：'+task.requirements.required+'\n不应认定完成的情形：'+task.requirements.not_allowed]);
standardRows.push(['四项分数','事实准确、证据支持、需求完成、边界处理；每项分别填写0、1或2，不自动合成总分。']);
for(const [key,value] of Object.entries(source.rubric.score_meaning))standardRows.push([key==='blank'?'空白':key+'分',value]);
for(const rule of source.rubric.common_rules)standardRows.push(['共用标准',rule]);
standardRows.push(['原始完整题目','完整输入页列出原始与解析字段；包内complete_tasks.json、TASKS_AND_CRITERIA.md和answers/保留完整原件。']);
standardRows.push(['允许使用的资源','模型与资源说明以包内shared_resources.json为准。无工具配置不预先得到工具结果；两种工具配置使用同版科学数据，其中一种有人工预选路径，另一种可多轮规划。外网关闭。']);
standardRows.push(['评审核对底表','shared_scientific_references.zip提供完整同版参考表供核查，不代表所有回答当时取得了这些工具输出。']);
standardRows.push(['开发题边界','六道已见开发题，每题三次技术重复；不是未见正式测试，也不是独立生物学重复。去掉组别标记不保证完全盲法。']);
for(const [key,value] of Object.entries(source.field_guide))standardRows.push([key,value]);
standardRows.push(['来源','dev_20261022_054717_79c2d3；原评审包和20261022_1310版标准。没有按新复核改写本批量表。']);
base(standards,`A1:B${standardRows.length}`);standards.getRange(`A1:B${standardRows.length}`).values=standardRows;
width(standards,`A1:A${standardRows.length}`,250);width(standards,`B1:B${standardRows.length}`,1050);
standards.getRange(`A2:B${standardRows.length}`).format.wrapText=true;
standards.getRange(`A2:B${standardRows.length}`).format.verticalAlignment='top';
for(let i=1;i<standardRows.length;i++)standards.getRange(`A${i+1}:B${i+1}`).format.rowHeight=
  standardRows[i][1].split('\n').reduce((sum,line)=>sum+textHeight(line,136),0)+8;
header(standards,'A1:B1');

const inputRows=[];
function flatten(caseId,prefix,value){
  if(value!==null && typeof value==='object' && Object.keys(value).length){
    for(const [key,child] of Object.entries(value))flatten(caseId,prefix+(Array.isArray(value)?`[${key}]`:'.'+key),child);
  }else{
    const type=value===null?'null':Array.isArray(value)?'array':typeof value;
    inputRows.push([caseId,prefix,type,value!==null&&typeof value==='object'?JSON.stringify(value):value===null?'null':value]);
  }
}
for(const task of source.tasks)for(const name of ['raw_input','raw_task_fields','resolved_input'])flatten(task.case_id,name,task[name]);
base(inputs,`A1:D${inputRows.length+1}`);inputs.getRange('A1:D1').values=[['题目ID','完整字段路径','原始数据类型','原始值']];
inputs.getRange(`A2:D${inputRows.length+1}`).values=inputRows;
inputs.tables.add(`A1:D${inputRows.length+1}`,true,'CompleteTaskInputs').showFilterButton=true;
for(const [col,w] of Object.entries({A:185,B:510,C:120,D:650}))width(inputs,`${col}1:${col}${inputRows.length+1}`,w);
inputs.getRange(`A2:D${inputRows.length+1}`).format.rowHeight=24;
inputs.getRange(`B2:D${inputRows.length+1}`).format.wrapText=true;
for(let i=0;i<inputRows.length;i++)inputs.getRange(`A${i+2}:D${i+2}`).format.rowHeight=Math.max(textHeight(inputRows[i][1],68),textHeight(inputRows[i][3],86));
header(inputs,'A1:D1');inputs.freezePanes.freezeRows(1);inputs.freezePanes.freezeColumns(1);

wb.recalculate();
const empty=score.getRange('C8:J61').values;if(empty.some(row=>row.some(v=>v!==null&&v!==''&&v!==undefined)))throw Error('Human fields must stay blank');
const inspected=await wb.inspect({kind:'table',range:'评分表!A7:J10',include:'values,formulas',tableMaxRows:4,tableMaxCols:10,maxChars:2200});
await fs.writeFile(path.join(previews,'inspect.txt'),inspected.ndjson);
const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:20},maxChars:1000});
await fs.writeFile(path.join(previews,'errors.txt'),errors.ndjson);
for(const [sheetName,range,file] of [['评分表','A1:J12','scoring'],['原始回答','A1:C12','answers'],['题目与标准','A1:B5','standards'],['完整输入','A1:D12','inputs']]){
  const blob=await wb.render({sheetName,range,scale:1.2,format:'png'});await fs.writeFile(path.join(previews,file+'.png'),new Uint8Array(await blob.arrayBuffer()));
}
await fs.mkdir(out,{recursive:true});const xlsx=await SpreadsheetFile.exportXlsx(wb);await xlsx.save(path.join(out,'blank_scores.xlsx'));
await fs.writeFile(path.join(previews,'builder_summary.json'),JSON.stringify({answer_ids:source.answers.map(a=>a.answer_id),
  original_answer_lines:lines.length,input_fields:inputRows.length,human_cells_blank:true,quality_scores_assigned:false},null,2));
console.log(JSON.stringify({output:path.join(out,'blank_scores.xlsx'),answer_rows:54,original_answer_lines:lines.length,input_fields:inputRows.length}));
