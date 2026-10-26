// Manual evaluation only. Preview/status calls never launch a model.
let evaluationPlans=null;
async function loadEvaluationPlans(){
  evaluationPlans=null;
  $('evaluationConfirmed').checked=false;
  const dialogue=$('evaluationProtocol').value==='dialogue-v3';
  $('startDiagnostic').disabled=dialogue;$('startEvaluation').disabled=dialogue;
  if(!dialogue){$('evaluationBudget').textContent='Earlier development set: 6 tasks × 3 configurations × 3 repeats = 54 units. Existing records are preserved.';return}
  try{
    evaluationPlans=await api('/api/development-evaluation-plan');
    const p=evaluationPlans.batch;
    $('evaluationBudget').textContent=p.planned_units+' planned units / '+p.planned_user_round_units+' user-round units; seen development tasks, one repeat. Q1/Q2 excluded before running. Upper bounds: '+p.max_logical_model_requests+' logical model requests, '+p.max_http_attempts+' HTTP attempts including configured retries. Sum of logical request output caps: '+p.max_output_tokens_across_requests+' tokens. This is not a billed-usage or price estimate; input usage and currency cost are unknown. Per round '+p.effective_settings.round_timeout_seconds+' s; per task '+p.effective_settings.case_timeout_seconds+' s. The diagnostic is one ordinary-model request and is not scored.';
    $('startDiagnostic').disabled=false;$('startEvaluation').disabled=false;
  }catch(e){$('evaluationBudget').textContent=e.message}
}
async function startEvaluationMode(mode){
  try{
    if(!$('evaluationConfirmed').checked)throw Error('Confirm model usage before starting.');
    const protocol=$('evaluationProtocol').value;
    if(protocol==='dialogue-v3'&&!evaluationPlans)throw Error('Load the current run plan first.');
    const request={mode,protocol,confirm_api_usage:true};
    if(protocol==='dialogue-v3')request.plan_sha256=evaluationPlans[mode].plan_sha256;
    const result=await api('/api/development-evaluation-start',request);
    $('evaluationStatus').textContent='Started '+result.run_id+'; '+result.expected_records+' planned units. No scientific quality scores are assigned automatically.';
    await refreshEvaluation();
  }catch(e){$('evaluationStatus').textContent=e.message}
}
async function refreshEvaluation(){
  try{
    const s=await api('/api/development-evaluation');
    if(s.status!=='NOT_STARTED')$('evaluationStatus').textContent=uiLabel(s.status)+' · '+(s.completed||0)+' / '+(s.total||0)+' planned units'+(s.error?' · '+s.error:'');
    const done=['COMPLETE','STOPPED','FAILED','STOPPED_TIMEOUT','BLOCKED_ACCOUNT'].includes(s.status);
    $('evaluationDownload').classList.toggle('hidden',!done);
    $('evaluationReviewDownload').classList.toggle('hidden',!done||s.protocol!=='dialogue-v3'||s.total===1||s.review_export_failed===true);
  }catch(e){$('evaluationStatus').textContent='Evaluation status unavailable: '+e.message}
}
$('evaluationProtocol').onchange=loadEvaluationPlans;
$('startDiagnostic').onclick=()=>startEvaluationMode('diagnostic');
$('startEvaluation').onclick=()=>startEvaluationMode('batch');
$('stopEvaluation').onclick=async()=>{try{await api('/api/development-evaluation-stop',{});await refreshEvaluation()}catch(e){$('evaluationStatus').textContent=e.message}};
setInterval(()=>{if(!document.hidden)refreshEvaluation()},10000);
loadEvaluationPlans();refreshEvaluation();
