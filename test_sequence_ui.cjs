// Check the actual shared chat renderer with saved replay JSON, without a model.
const fs=require('node:fs'),assert=require('node:assert/strict');
class Element{
 constructor(tag){this.tag=tag;this.children=[];this.dataset={};this.style={};this.textContent=''}
 append(...children){this.children.push(...children)}
 text(){return this.textContent+this.children.map(x=>x.text()).join('')}
}
global.document={createElement:tag=>new Element(tag)};
const {renderSequenceEvidence}=require('./sequence_ui.js');
for(const [name,status] of [['known_error_24','FAIL'],['wrong_base_19','FAIL'],['normal_answer','PASS']]){
 const r=JSON.parse(fs.readFileSync('research/2026-10-24_sequence_guard/replay/'+name+'/result.json','utf8'));
 const dom=renderSequenceEvidence(r.answer_validation,r.verified_sequences,r.model_summary_raw);
 assert.equal(dom.dataset.sequenceStatus,status);assert.ok(dom.text().includes('GAUAGAGCAAGACAAGAAA'));
 assert.ok(dom.text().includes('GAUAGAGCAAGACAAGAAATT-N3'));assert.ok(dom.text().includes('CONDITIONAL'));
 assert.ok(dom.text().includes(r.model_summary_raw));assert.ok(dom.children.some(x=>x.tag==='details'));
 if(status==='FAIL')assert.ok(dom.text().includes('未通过'));else assert.ok(dom.text().includes('检查通过'));
}
console.log('PASS: actual shared chat renderer displays FAIL/FAIL/PASS, verified fields and separate unchanged raw text.');
