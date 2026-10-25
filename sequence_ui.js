/* Display server-checked fields only. This module never calls a model. */
(function(root){
 function node(tag,text){const e=document.createElement(tag);if(text!==undefined)e.textContent=String(text);return e}
 function renderSequenceEvidence(check,rows,raw){
  const section=node('section');section.className='sequence-evidence';section.dataset.sequenceStatus=check.status;
  const labels={PASS:'Sequence check passed',FAIL:'Sequence check failed - original answer conflicts with verified fields',NO_SEQUENCE_CLAIMS:'No sequence claims to check',NOT_CHECKED_NO_VERIFIED_SEQUENCE:'Sequence check unavailable: no verified sequence evidence',NO_MODEL_ANSWER:'No model answer to check'};
  const title=node('strong',labels[check.status]||check.status);section.append(title,node('p','Key sequences are read directly from verified fields. This check does not establish that every scientific statement is correct.'));
  const wrap=node('div');wrap.className='scroll';const table=node('table'),head=node('tr');
  ['Candidate','Guide core 5′→3′','Other strand core 5′→3′'].forEach(x=>head.append(node('th',x)));table.append(head);
  for(const row of rows){const tr=node('tr');['candidate_id','guide_core19_5to3','passenger_core19_5to3'].forEach(k=>tr.append(node('td',row[k]||'Not supplied or not verified')));table.append(tr)}
  wrap.append(table);section.append(wrap);
  for(const row of rows)for(const [label,key] of [['Original row 1','original_row1'],['Original row 2','original_row2'],['Original full-length guide','guide_21nt_original'],['Original full-length other strand','passenger_21nt_original'],['Basis for strand assignment','strand_assignment_basis'],['Original modification note','original_modification']])if(row[key])section.append(node('p',label+': '+row[key]));
  if(check.issues.length)section.append(node('p','Conflicting sequences in the original answer: '+check.issues.map(x=>x.sequence).join('; ')+'. The original answer failed the sequence check.'));
  if(raw){const details=node('details'),summary=node('summary','View original model text (unchanged; verified fields take precedence)'),pre=node('pre',raw);pre.style.whiteSpace='pre-wrap';pre.style.overflowWrap='anywhere';details.append(summary,pre);section.append(details)}
  return section;
 }
 root.renderSequenceEvidence=renderSequenceEvidence;
 if(typeof module!=='undefined')module.exports={renderSequenceEvidence};
})(typeof window!=='undefined'?window:globalThis);
