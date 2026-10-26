const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
(async()=>{
 const elements={};const $=id=>elements[id]??=( {value:id==='evaluationProtocol'?'dialogue-v3':'',checked:false,disabled:false,textContent:'',classList:{toggle(){}}});
 const calls=[];const plan={plan_sha256:'SYNTHETIC_PLAN',planned_units:27,planned_user_round_units:33,max_logical_model_requests:154,max_http_attempts:308,max_output_tokens_across_requests:277200,effective_settings:{case_timeout_seconds:720,round_timeout_seconds:360}};
 const api=async(path,body)=>{calls.push({path,body});if(path.endsWith('-plan'))return {batch:plan,diagnostic:{...plan,planned_units:1}};if(path.endsWith('-start'))return {run_id:'SYNTHETIC_ONLY',expected_records:27};return {status:'NOT_STARTED'}};
 const c=vm.createContext({$,api,uiLabel:x=>x,setInterval(){},document:{hidden:false},console});
 vm.runInContext(fs.readFileSync('evaluation_ui.js','utf8'),c);
 await new Promise(resolve=>setImmediate(resolve));
 assert(calls.every(x=>!x.body),'Preview and polling must not launch a run');
 await $('startEvaluation').onclick();assert(!calls.some(x=>x.path.endsWith('-start')));
 $('evaluationConfirmed').checked=true;await $('startEvaluation').onclick();
 const started=calls.find(x=>x.path.endsWith('-start'));
 assert.equal(started.body.protocol,'dialogue-v3');assert.equal(started.body.plan_sha256,'SYNTHETIC_PLAN');assert.equal(started.body.confirm_api_usage,true);
 $('evaluationProtocol').value='legacy';await $('evaluationProtocol').onchange();assert.equal($('evaluationConfirmed').checked,false);
 console.log('PASS: preview never starts a model; manual acknowledgement and current plan are sent; changing task set clears acknowledgement.');
})().catch(e=>{console.error(e);process.exitCode=1});
