"""Regenerate the existing-candidate evidence report using pinned imports only."""
from pathlib import Path
import argparse,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from core import Session
p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--state',choices=['Hypoxia','Normoxia'],default='Hypoxia');a=p.parse_args()
out=Path(a.output)
if out.exists() and any(out.iterdir()):raise SystemExit('Use a new empty output directory')
out.mkdir(parents=True,exist_ok=True)
s=Session(mode='workflow',tool_mode='imported',run_root=out,
    task={'gene':'VEGFA','species':'Homo sapiens','state':a.state,'top_n':2,'request':'Rebuild checked-in candidate evidence'})
r=s.run();print(json.dumps({'result':r,'directory':str(s.path.resolve()),'model_api_used':False},ensure_ascii=True))
if r.get('status')!='COMPLETE':raise SystemExit(1)
