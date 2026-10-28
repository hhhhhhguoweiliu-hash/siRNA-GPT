"""Real local deterministic run. Historical science outputs; no new LLM call."""
import json, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from core import Session, HOME

if __name__=='__main__':
    task={'gene':'VEGFA','species':'Homo sapiens','state':'Hypoxia','top_n':2,
          'request':'本次候选与8样本基线表达关联并由R生成图表和报告',
          'expression_dataset_id':'builtin','include_expression_figures':True}
    s=Session(task=task,mode='workflow',tool_mode='imported')
    r=s.run()
    receipt={'run_id':s.id,'run_dir':str(s.path),'status':r['status'],
             'expression_figures':r.get('expression_figures'),
             'actual_model_calls':0,'seed_and_score_mode':'IMPORTED_HISTORICAL',
             'actual_tools':list(s.state),'message':r.get('message')}
    folder=HOME/'research/2026-10-29_expression_figures';folder.mkdir(parents=True,exist_ok=True)
    (folder/'local_run_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(receipt,ensure_ascii=False))
    sys.exit(0 if r['status']=='COMPLETE' else 1)
