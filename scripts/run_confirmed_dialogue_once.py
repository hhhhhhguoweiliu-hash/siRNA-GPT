"""One explicitly authorized provider run through the existing confirmed entry.

No startup/schedule hook, test transport, model fallback or configuration change.
The human's explicit consent and exact prepared plan must already be saved.
"""
import argparse
import contextlib
import json
import subprocess
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from core import config,save_json,now
from dialogue_evaluation import prepare,run


def main():
    p=argparse.ArgumentParser();p.add_argument('--authorization',type=Path,required=True);p.add_argument('--mode',choices=['diagnostic','batch'],required=True)
    args=p.parse_args();authorization=json.loads(args.authorization.read_text(encoding='utf-8'))
    if authorization.get('confirm_api_usage') is not True:raise ValueError('Explicit human consent missing')
    folder=args.authorization.parent;cfg=config();plan=prepare(cfg,args.mode)[0]
    data_consent=json.loads((folder/'provider_data_authorization.json').read_text(encoding='utf-8'))
    if data_consent.get('allow_send_and_run') is not True or data_consent.get('model')!=cfg.get('model'):
        raise ValueError('Explicit provider/data consent missing or model differs')
    approved=authorization['plans'][args.mode]
    if approved!=plan:raise ValueError('Prepared plan differs from the recorded authorized plan; no requests sent')
    identity=authorization['run_ids'][args.mode]
    save_json(folder/(args.mode+'_execution_version.json'),{'kind':'REAL_PROVIDER_RUN_NOT_TEST_TRANSPORT','started_at':now(),
        'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'confirmation':'Explicit user instruction preserved in authorization.json; confirm_api_usage=True is passed to the same execution function used by the web confirmation endpoint',
        'browser_button_clicked':False,'production_deployed':False,'plan_sha256':plan['plan_sha256']})
    with (folder/(args.mode+'_owner_archive_log.jsonl')).open('w',encoding='utf-8') as log:
        with contextlib.redirect_stdout(log):
            state=run(config,identity,mode=args.mode,confirm_api_usage=True,plan_sha256=plan['plan_sha256'],execution_mode='provider')
    save_json(folder/(args.mode+'_completion.json'),state)
    print(json.dumps(state,ensure_ascii=False))


if __name__=='__main__':main()
