/* Display server-checked fields only. This module never calls a model. */
(function(root){
 function node(tag,text){const e=document.createElement(tag);if(text!==undefined)e.textContent=String(text);return e}
 function renderSequenceEvidence(check,rows,raw){
  const section=node('section');section.className='sequence-evidence';section.dataset.sequenceStatus=check.status;
  const title=node('strong',check.label);section.append(title,node('p','关键序列由程序直接读取核验字段；这项检查不代表科学回答全部正确。'));
  const wrap=node('div');wrap.className='scroll';const table=node('table'),head=node('tr');
  ['候选','引导链核心 5′→3′','另一链核心 5′→3′'].forEach(x=>head.append(node('th',x)));table.append(head);
  for(const row of rows){const tr=node('tr');['candidate_id','guide_core19_5to3','passenger_core19_5to3'].forEach(k=>tr.append(node('td',row[k]||'未提供或未核验')));table.append(tr)}
  wrap.append(table);section.append(wrap);
  for(const row of rows)for(const [label,key] of [['原始第1行','original_row1'],['原始第2行','original_row2'],['原引导链全长','guide_21nt_original'],['原另一链全长','passenger_21nt_original'],['链角色依据','strand_assignment_basis'],['原修饰说明','original_modification']])if(row[key])section.append(node('p',label+'：'+row[key]));
  if(check.issues.length)section.append(node('p','不一致的原答序列：'+check.issues.map(x=>x.sequence).join('；')+'。原答未通过。'));
  if(raw){const details=node('details'),summary=node('summary','查看原始模型文字（原样保留；不替代核验字段）'),pre=node('pre',raw);pre.style.whiteSpace='pre-wrap';pre.style.overflowWrap='anywhere';details.append(summary,pre);section.append(details)}
  return section;
 }
 root.renderSequenceEvidence=renderSequenceEvidence;
 if(typeof module!=='undefined')module.exports={renderSequenceEvidence};
})(typeof window!=='undefined'?window:globalThis);
