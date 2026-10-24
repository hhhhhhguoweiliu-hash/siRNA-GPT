"""Replay one saved real answer and two edited controls, with zero API/tool calls."""
import copy,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from core import Session,save_json
from conversation import Conversation,PlannedSession

SOURCE=ROOT/'research/2026-10-24_nearfull_complete/live/tool_export'
OUT=ROOT/'research/2026-10-24_sequence_guard'
TOOLS=['inspect_candidates','verify_target','score_candidates','match_seed','query_expression','compile_report']
WRONG='GAUAGAGCAAGACAAGACAAGAAA';CORRECT='GAUAGAGCAAGACAAGAAA'
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

class SavedReplay(PlannedSession):
    def __init__(self,path,case,source_report):
        # No Session constructor/config lookup, run_workflow, run_agent or call.
        self.path=path;path.mkdir(parents=True,exist_ok='--refresh-derived' in sys.argv)
        self.candidates=load(SOURCE/'input.json')['candidates'];self.task=load(SOURCE/'input.json')['task']
        self.state={n:load(SOURCE/(n+'.json')) for n in TOOLS};self.planned_tools=TOOLS
        self.mode='agent';self.tool_mode='imported';self.id='offline_sequence_replay_'+case
        self.expression_source=source_report['expression_source']
        report=copy.deepcopy(source_report);report.update(run_id=self.id,record_kind='OFFLINE_SAVED_ANSWER_REPLAY',
            model_used=False,source_original_run_id=source_report['run_id'],replay_case=case)
        save_json(path/'report.json',report)

def main():
    replay=OUT/'replay';replay.mkdir(parents=True,exist_ok=True)
    if (OUT/'replay_checks.json').exists():
        if '--refresh-derived' not in sys.argv:raise SystemExit('Preserve existing replay; choose a new output directory')
        assert load(OUT/'replay_checks.json')['source_report_sha256']==sha(SOURCE/'report.json')
    source_report=load(SOURCE/'report.json');raw=source_report['model_summary'];assert WRONG in raw
    inputs=load(SOURCE/'input.json')['candidates'];assert inputs[0]['passenger_paired_core_19nt_5to3']==CORRECT
    cases=[('known_error_24',raw,'FAIL','原24位错误原答，未改文字'),
        ('wrong_base_19',raw.replace(WRONG,CORRECT[:-1]+'C'),'FAIL','确定性测试对照：长度19但最后一个碱基改变，不是新模型回答'),
        ('normal_answer',raw.replace(WRONG,CORRECT),'PASS','确定性正常对照：只将错误串替换为核验19位核心，不冒充当时原答')]
    checks=[]
    for case,text,expected,note in cases:
        folder=replay/case;s=SavedReplay(folder,case,source_report)
        result=s.result_for_plan(text,test_only=True)
        report=load(folder/'report.json');report['agent_status']='OFFLINE_SAVED_ANSWER_REPLAY';save_json(folder/'report.json',report);s.render(report)
        result.update(record_kind='OFFLINE_SAVED_ANSWER_REPLAY',new_model_requests=0,new_scientific_tool_calls=0,replay_note=note)
        save_json(folder/'result.json',result)
        c=Conversation(cfg_loader=lambda:{},root=folder/'chat_record');c.session=s;c.plan={'tools':TOOLS};c.finish(result)
        snapshot=c.snapshot();save_json(folder/'chat_snapshot.json',snapshot)
        check=result['answer_validation'];assert check['status']==expected
        assert check==report['answer_validation']==snapshot['messages'][-1]['answer_validation']
        assert result['model_summary_raw']==text and report['model_summary']==text
        if expected=='FAIL':assert text not in result['model_summary_display']
        assert 'GAUAGAGCAAGACAAGAAATT-N3' in json.dumps(result['verified_sequences'],ensure_ascii=False)
        payload=json.dumps({'message':snapshot['messages'][-1],'note':note},ensure_ascii=False).replace('<','\\u003c')
        body='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>序列检查离线回放</title><style>body{font:15px/1.7 Arial,"Microsoft YaHei",sans-serif;max-width:1000px;margin:28px auto;padding:0 24px;color:#213b43}table{border-collapse:collapse;width:100%}td,th{border:1px solid #d7e1e7;padding:8px;text-align:left}td,pre{overflow-wrap:anywhere}pre{white-space:pre-wrap}strong{font-size:20px}.sequence-evidence{border:2px solid #217d6a;padding:18px;margin-top:15px}.sequence-evidence[data-sequence-status="FAIL"]{border-color:#b54735;background:#fff8f5}</style><script src="/sequence_ui.js"></script><h1>最终回答序列检查：离线回放</h1><p>使用已保存工具证据；本次没有模型、评分、seed或近全长计算，不是新真实案例或人工评分。</p><p><a href="/sequence-check-replay">三个对照入口</a> · <a href="report.html">同一检查状态的完整HTML报告</a> · <a href="result.json">JSON字段</a></p><p id="note"></p><article id="message"></article><div id="evidence"></div><script>const data='''+payload+''';document.getElementById('note').textContent=data.note;document.getElementById('message').textContent=data.message.text;document.getElementById('evidence').append(renderSequenceEvidence(data.message.answer_validation,data.message.verified_sequences,data.message.model_summary_raw));</script></html>'''
        (folder/'chat.html').write_text(body,encoding='utf-8',newline='\n')
        checks.append({'case':case,'fixture_kind':note,'expected':expected,'actual':check['status'],
            'chat_html_json_same_validation':True,'raw_text_sha256':check['raw_model_text_sha256'],
            'model_text_not_silently_rewritten':True,'claim_count':check['claim_count'],'issues':check['issues'],
            'new_model_requests':0,'new_scientific_tool_calls':0})
    index='<!doctype html><meta charset="utf-8"><title>序列检查离线对照</title><h1>已保存回答的序列检查：三个离线对照</h1><p>没有新模型调用或科学计算，不是独立质量评分。</p>'
    for case,_,_,note in cases:index+='<p><a href="/sequence-check-replay/'+case+'/chat.html">'+note+'</a></p>'
    (replay/'index.html').write_text(index,encoding='utf-8')
    save_json(OUT/'replay_checks.json',{'status':'PASS','source_original_run_id':source_report['run_id'],
        'source_report_sha256':sha(SOURCE/'report.json'),'source_input_sha256':sha(SOURCE/'input.json'),
        'validator_source_sha256':sha(ROOT/'sequence_validation.py'),'checks':checks,
        'new_model_requests':0,'new_scientific_tool_calls':0,'independent_human_score':None})
    print(json.dumps({'status':'PASS','cases':[(x['case'],x['actual']) for x in checks],'new_model_requests':0}))
if __name__=='__main__':main()
