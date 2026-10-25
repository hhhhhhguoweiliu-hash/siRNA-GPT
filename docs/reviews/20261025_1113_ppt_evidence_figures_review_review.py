from pathlib import Path
import base64
import datetime as dt
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
import zlib
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
ROOT = Path('C:/00000/ARPE RNA-seq/sirna-gpt')
PREFIX = 'research/2026-10-25_ppt_figures/'
snap = json.loads((HERE/'remote_snapshot.json').read_text(encoding='utf-8'))
current = {e['path']:e for e in snap['tree']['tree'] if e['type']=='blob'}
old = {e['path']:e for e in snap['parenttree']['tree'] if e['type']=='blob'}
checks=[]
def check(name, condition, detail=None):
    checks.append({'name':name,'pass':bool(condition),'detail':detail})
def read(p):
    return json.loads((ROOT/p).read_text(encoding='utf-8'))
def blob(b):
    return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def sha(b):
    return hashlib.sha256(b).hexdigest()

added=sorted(set(current)-set(old))
deleted=sorted(set(old)-set(current))
modified=sorted(p for p in set(old)&set(current) if old[p]['sha']!=current[p]['sha'])
check('old files changed only WORKBOARD and STATUS',modified==['docs/STATUS.md','docs/WORKBOARD.md'],modified)
check('no deletions',not deleted,deleted)
check('all additions confined to figures delivery and build script',all(p.startswith(PREFIX) or p=='scripts/build_ppt_evidence_figures_20261025.py' for p in added),len(added))
bindings=[]
for p in added+modified:
    b=(ROOT/p).read_bytes()
    mode='raw' if blob(b)==current[p]['sha'] else 'LF' if blob(b.replace(b'\r\n',b'\n'))==current[p]['sha'] else 'MISMATCH'
    bindings.append({'path':p,'mode':mode,'sha256':sha(b)})
    check('current Git binding '+p,mode!='MISMATCH',mode)

manifest=read(PREFIX+'source_manifest.json')
check('39 declared source files',len(manifest)==39,len(manifest))
for p,item in manifest.items():
    copied=PREFIX+'raw_evidence/'+p
    b=(ROOT/copied).read_bytes()
    check('copied source hash '+p,sha(b)==item['sha256'] and len(b)==item['bytes'])
    check('copied source matches prior Git blob '+p,blob(b)==old[p]['sha'])
    check('source unchanged on current main '+p,current[p]['sha']==old[p]['sha'])

A='research/2026-10-24_nearfull_complete/live/'
B='research/2026-10-23_literature/live_20261024/actual_demo/'
conv=read(A+'conversation_export_original.json')
summary=read(A+'actual_model_call_summary.json')
ev=conv['events']
starts=[e for e in ev if e['kind']=='model_started']
ends=[e for e in ev if e['kind']=='model_finished']
tools=[e for e in ev if e['kind']=='tool_finished']
planner=next(e for e in ev if e['kind']=='planner_finished')
stamp=dt.datetime.fromisoformat
gap=(stamp(starts[0]['time'])-stamp(planner['time'])).total_seconds()
span=(stamp(ends[-1]['time'])-stamp(starts[0]['time'])).total_seconds()
answer_time=(stamp(ends[-1]['time'])-stamp(starts[-1]['time'])).total_seconds()
check('A recorded model and tool counts',len(starts)==len(ends)==7 and len(tools)==6 and len(summary['calls'])==8)
check('A model request phase separation',[c['phase'] for c in summary['calls']]==['planning']+['execution']*7)
check('A exact timing values',round(gap,3)==103.357 and round(span,3)==36.040 and round(answer_time,3)==21.870,{'gap':gap,'span':span,'last_response':answer_time})
tool_names=['inspect_candidates','verify_target','score_candidates','match_seed','query_expression','compile_report']
check('A tools agree with saved plan',[e['message'] for e in tools]==conv['plan']['tools']==conv['plan']['completed']==tool_names)
actual_exec_tokens=0
for i in range(1,8):
    r=read(A+f'tool_export/attempts/7a372161375c_turn{i}_response.json')
    raw=r['_raw_response']
    check(f'A actual response {i} completed',raw['status']=='completed')
    check(f'A actual response {i} model parameters',r['_request']['model']=='doubao-seed-2-1-pro-260915' and r['_request']['max_output_tokens']==1800 and r['_request']['thinking']=={'type':'disabled'})
    calls=[o['name'] for o in raw['output'] if o['type']=='function_call']
    check(f'A actual tool call {i}',calls==([tool_names[i-1]] if i<=6 else []))
    actual_exec_tokens+=raw['usage']['total_tokens']
planning_tokens=sum(c['usage']['total_tokens'] for c in summary['calls'] if c['phase']=='planning')
planner_raw=next(e['response'] for e in conv['evidence_records'] if e['id']=='bf86f0f4d5024764bb704f42')
check('A planner actual response completed',planner_raw['status']=='completed')
check('A planner usage same as summary',planner_raw['usage']['total_tokens']==planning_tokens)
check('A tokens independently summed from all actual responses',actual_exec_tokens+planner_raw['usage']['total_tokens']==39048,{'execution':actual_exec_tokens,'planning':planning_tokens})
ins=read(A+'tool_export/inspect_candidates.json')['rows'][0]
target=read(A+'tool_export/verify_target.json')['rows'][0]
score=read(A+'tool_export/score_candidates.json')
seed=read(A+'tool_export/match_seed.json')
expression=read(A+'tool_export/query_expression.json')
stats=expression['candidate_summary'][0]
report=read(A+'tool_export/report.json')
plan=read(A+'tool_export/plan.json')
guide=ins['guide_core19_5to3']
other=plan['candidates'][0]['passenger_paired_core_19nt_5to3']
check('A exact 19 nt complementary cores',len(guide)==len(other)==19 and other.translate(str.maketrans('ACGU','UGCA'))[::-1]==guide)
check('A original 24 nt error still present','GAUAGAGCAAGACAAGACAAGAAA' in report['model_summary'])
check('A coordinate and transcript coverage',target['reference_transcript']=='NM_003376.6' and target['core_start_1based']==1439 and target['core_end_1based']==1457 and target['covered_transcripts']==18 and target['reference_transcript_count']==20)
check('A imported score/seed statuses',score['status']==seed['status']=='IMPORTED_VERIFIED_LOCAL')
check('A displayed score rounding',f"{score['rows'][0]['oligoformer_scaled_score']:.6f}"=='1.121934')
check('A seed sites and genes are separate',stats['seed_site_count_nontarget']==3539 and stats['matched_genes']==2839)
check('A expression mapping and detection counts',stats['baseline_mapped_genes']==2836 and stats['state_detected_genes']==1595 and stats['unmapped_genes']==3)
check('A no ranking change',expression['source']['ranking_changed'] is False)

qa=read(B+'conversation/evidence/ef511585f2734fe999f4f28c.json')
exchange=read(B+'conversation/evidence/8adf373e980643189b6f0479.json')
payload=json.loads(exchange['request']['input'][0]['content'][0]['text'])
result=next(r for r in read(B+'results.json') if r['id']=='B02')
check('B answer, question and usage same as actual saved result',qa['question']==result['question'] and qa['answer']==result['answer'] and qa['model_call_count']==1 and result['usage'][0]['total_tokens']==6232)
check('B six actual retrieved snippets',len(payload['retrieved_excerpts'])==len(qa['retrieved_excerpts'])==6)
for a,b in zip(qa['retrieved_excerpts'],payload['retrieved_excerpts']):
    check('B actual request exact citation and text '+a['citation_id'],a['citation_id']==b['citation_id'] and a['text']==b['text'])
ex={e['citation_id']:e for e in qa['retrieved_excerpts']}
paper_sentence='The output of the model represents a prediction score for each siRNA, reflecting its potential effectiveness in inducing gene knockdown.'
code_line='Y_PRED = [i*1.341 for i in Y_PRED]'
check('B paper quotation exact retrieved substring',paper_sentence in ex['S3']['text'])
check('B code quotation in both actually retrieved source chunks',all(code_line in ex[s]['text'] for s in ['S2','S5']))
with zipfile.ZipFile(ROOT/B/'library.zip') as z:
    check('B original library ZIP CRC',z.testzip() is None)
    code=z.read('originals/ec77cffdc9e76e478068430f.txt')
    paper=z.read('originals/e2cea21b6712b85250758e8b.txt')
    check('B official code archived original hash',sha(code)==ex['S2']['file_sha256'])
    check('B article archived original hash',sha(paper)==ex['S3']['file_sha256'])
    lines=[i+1 for i,l in enumerate(code.decode('utf-8').splitlines()) if code_line in l]
    offset=paper.decode('utf-8').index(paper_sentence)
    check('B original code line locator',lines==[252,385],lines)
    check('B original paper character locator',offset==30046,offset)
    for sid,full in [('S2',code),('S3',paper),('S4',paper),('S5',code)]:
        e=ex[sid]
        check('B exact chunk source range '+sid,full.decode('utf-8')[e['start']:e['end']]==e['text'])

figures=[]
for name in ['A_purchased_Agent_case','B_literature_answer_evidence']:
    root=ET.parse(ROOT/PREFIX/'figures'/f'{name}.svg').getroot()
    texts=root.findall('{http://www.w3.org/2000/svg}text')
    els=read(PREFIX+'figures/'+name+'_elements.json')
    check('SVG exact element text '+name,[t.text for t in texts]==[e['text'] for e in els])
    check('SVG Arial declared '+name,all(t.get('font-family')=='Arial' for t in texts))
    check('SVG 16:9 '+name,root.get('viewBox')=='0 0 1280 720')
    with Image.open(ROOT/PREFIX/'figures'/f'{name}.png') as im:
        check('PNG 3840x2160 '+name,im.size==(3840,2160))
    pdf=(ROOT/PREFIX/'figures'/f'{name}.pdf').read_bytes()
    font_objs={}
    used_fonts=set()
    for m in re.finditer(rb'(\d+) 0 obj\s*(.*?)\s*endobj',pdf,re.S):
        obj=m.group(2)
        base=re.search(rb'/BaseFont\s*/([^\s/]+)',obj)
        if base: font_objs[m.group(1)]=base.group(1).decode()
    font_refs={name.decode():font_objs.get(num) for name,num in re.findall(rb'/(F[^\s/]+)\s+(\d+) 0 R',pdf)}
    for m in re.finditer(rb'(.*?)stream\r?\n(.*?)endstream',pdf,re.S):
        header,body=m.group(1),m.group(2).rstrip(b'\r\n')
        try:
            if b'/ASCII85Decode' in header: body=base64.a85decode(body,adobe=True)
            if b'/FlateDecode' in header: body=zlib.decompress(body)
        except Exception:
            continue
        active=None
        for match in re.finditer(rb'/(F[^\s/]+)\s+[\d.]+\s+Tf|\bTj\b|\bTJ\b',body):
            if match.group(1): active=match.group(1).decode()
            elif active: used_fonts.add(font_refs.get(active,'UNKNOWN'))
    check('PDF actual text uses Arial only '+name,bool(used_fonts) and all('Arial' in f for f in used_fonts),sorted(used_fonts))
    check('PDF embedded TrueType font streams '+name,pdf.count(b'/FontFile2')==2)
    check('SVG labels fit page bounds '+name,all(e['x']>=0 and e['x']+e['width']<1280 and 0<e['baseline_y']<720 for e in els))
    figures.append({'name':name,'text_elements':len(texts),'displayed_word_count':len(' '.join(e['text'] for e in els).split()),'minimum_font':min(e['font_size'] for e in els),'actual_PDF_fonts':sorted(used_fonts),'visually_inspected':True})

bad_review='docs/reviews/20261025_1040_ppt_figure_selection.md'
badbytes=(ROOT/PREFIX/'raw_evidence'/bad_review).read_bytes()
bad_count=badbytes.decode('utf-8').count(chr(65533))
check('prior review encoding problem confirmed on remote-bound original',bad_count==3170,bad_count)
payload={'reviewed_head':snap['head'],'previous_review_head':'927910c74181417b2d3229e4e8a3ffeedec841bd','added_count':len(added),'modified':modified,'deleted':deleted,'figures':figures,'source_copies_verified':len(manifest),'current_local_remote_bindings':bindings,'checks':checks,'pass_count':sum(c['pass'] for c in checks),'failed':[c for c in checks if not c['pass']],'scope':'Saved-data and final-file inspection only. No model call, scientific rerun, website verification, Drive download or independent human scoring.'}
(HERE/'independent_audit.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in payload.items() if k not in ['checks','current_local_remote_bindings']},ensure_ascii=False,indent=2))
sys.exit(1 if payload['failed'] else 0)
