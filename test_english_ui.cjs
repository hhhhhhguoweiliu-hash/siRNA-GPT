const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const labels=require('./ui_text.js');
for(const file of ['library_ui.js','sequence_ui.js','ui_text.js'])new vm.Script(fs.readFileSync(file,'utf8'));
assert.equal(labels.uiLabel('豆包LLM规划'),'Model-generated plan');
assert.equal(labels.uiSourceLabel({source_kind:'official_source_code',kind:'官方工具源码'}),'Official source code');
assert.equal(labels.uiLocator({page:3,chunk_id:'p003-c001'}),'PDF p. 3 · p003-c001');
assert.equal(labels.uiSequenceLabel({status:'FAIL',label:'未通过'}),'Sequence check failed - original answer conflicts with verified fields');
const raw='Original record: GAUAGAGCAAGACAAGAAATT-N3 [S3] 原文';
assert.equal(labels.uiLabel(raw),raw); // Labels do not rewrite arbitrary original content.
const py=fs.readFileSync('ui_labels.py','utf8');
for(const status of ['PASS','FAIL','NO_SEQUENCE_CLAIMS','NOT_CHECKED_NO_VERIFIED_SEQUENCE','NO_MODEL_ANSWER']){
 const label=labels.uiSequenceLabel({status});assert(py.includes(label));
}
console.log('PASS: English dynamic labels, citation locators, Python/JS status agreement and unchanged original content.');
