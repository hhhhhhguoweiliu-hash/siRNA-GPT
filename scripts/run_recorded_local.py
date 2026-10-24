"""Run one explicitly provided local command, retaining stdout/stderr, timeout and exit status."""
import argparse,datetime,json,os,subprocess,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--name',required=True);p.add_argument('--timeout',type=int,required=True);p.add_argument('command',nargs=argparse.REMAINDER);a=p.parse_args()
root=Path(__file__).resolve().parents[1];out=root/'research/2026-10-24_candidate_v2/execution';out.mkdir(exist_ok=True)
receipt=out/(a.name+'.json');log=out/(a.name+'.log')
if receipt.exists() or log.exists():raise SystemExit('Preserve existing run; use a new name')
cmd=a.command[1:] if a.command[:1]==['--'] else a.command
env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';env['PYTHONUTF8']='1'
start=datetime.datetime.now(datetime.timezone.utc).isoformat();clock=time.perf_counter();status='RETURNED';code=None
receipt.write_text(json.dumps({'status':'RUNNING','started_utc':start,'command':cmd,'cwd':str(root)},indent=2),encoding='utf-8')
with log.open('wb') as f:
 try:code=subprocess.run(cmd,cwd=root,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=a.timeout).returncode
 except subprocess.TimeoutExpired:status='TIMED_OUT_PROCESS_STOPPED'
value={'status':status,'started_utc':start,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'wall_seconds':time.perf_counter()-clock,
 'exit_code':code,'timeout_seconds':a.timeout,'command':cmd,'cwd':str(root),'log_file':log.relative_to(root).as_posix(),
 'scope':'Real local official-tool execution, no API, no training, no wet experiment'}
receipt.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(value,ensure_ascii=False))
raise SystemExit(0 if code==0 else 1)
