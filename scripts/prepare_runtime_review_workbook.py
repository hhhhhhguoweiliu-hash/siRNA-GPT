"""Prepare official-tool authoring payload, or verify its actual saved XLSX."""
import argparse
import json
import sys
import zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from review_import import read_sheets,import_workbooks
from core import save_json


def prepare(run,output,verify=False):
    run,output=Path(run),Path(output)
    source=run/'for_review/score_workbook_payload.json'
    payload=json.loads(source.read_text(encoding='utf-8'))
    if not verify:
        if output.exists():raise ValueError('不覆盖已有人工表；请选新输出位置')
        task={'artifacts':[{'path':str(output.resolve()),'kind':'ACTUAL_RUN_MATCHED_BLANK_FORM_NO_HUMAN_SCORES',
            'sheets':payload['sheets'],'preview_dir':str(output.parent/'previews')}]}
        dest=output.parent/'workbook_authoring.json';save_json(dest,task)
        print(str(dest));return dest
    sheets=read_sheets(output)
    for name,rows in payload['sheets'].items():
        actual=[row for _,row in sheets[name]]
        normalized=lambda row:[str(x) if x is not None else '' for x in row]
        assert [normalized(r) for r in actual]==[normalized(r) for r in rows],name
    plan=json.loads((run/'analysis_plan.json').read_text(encoding='utf-8'))
    execution=json.loads((run/'actual_execution.json').read_text(encoding='utf-8'))
    imported=import_workbooks(plan,execution,[output]);assert imported['reviews']==[]
    dest=run/'reviewer_package_with_blank_xlsx.zip'
    if dest.exists():raise ValueError('不覆盖旧评审包，请保留原版本并使用新的运行副本目录')
    with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
        for file in sorted((run/'for_review').rglob('*')):
            if file.is_file():z.write(file,file.relative_to(run/'for_review'))
        z.write(output,'review_form_blank.xlsx')
    with zipfile.ZipFile(dest) as z:assert z.testzip() is None
    print('PASS: actual run IDs and every fact row match; all human fields blank; new reviewer ZIP contains the XLSX without changing the original run package.')
    return dest


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--verify',action='store_true');a=p.parse_args()
    prepare(a.run,a.output,a.verify)
