"""Retypeset verified records; no model requests or scientific-tool execution."""
from pathlib import Path
import argparse, base64, csv, datetime as dt, hashlib, html, io, json, math, shutil, subprocess, sys, zipfile
from collections import Counter
from xml.etree import ElementTree as ET
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from pypdf import PdfReader, PdfWriter, Transformation
from pypdf.generic import ContentStream
from PIL import Image, ImageOps, ImageDraw

parser=argparse.ArgumentParser()
parser.add_argument('--repo',default='C:/00000/ARPE RNA-seq/sirna-gpt')
parser.add_argument('--out',default='outputs/figure_guide_20261025')
parser.add_argument('--tree',default='tmp/figure_guide_20261025/remote_tree.json')
args=parser.parse_args()
ROOT=Path(args.repo); OUT=Path(args.out).resolve(); FIG=OUT/'figures'; PREVIEW=OUT/'previews'
FIG.mkdir(parents=True,exist_ok=True); PREVIEW.mkdir(exist_ok=True)
snap=json.loads(Path(args.tree).read_text(encoding='utf-8'))
git={x['path']:x['sha'] for x in snap['tree']['tree'] if x['type']=='blob'}
SOURCES={}; EVIDENCE={}; LAYOUT=[]
W,H=1280,720
INK='#173041'; BLUE='#244F73'; TEAL='#317C79'; MUTED='#60727B'; RED='#A84447'
GRID='#DCE4E8'; LILAC='#9484B9'; CREAM='#E6C889'; PALE='#EEF4F6'
REG=Path('C:/Windows/Fonts/arial.ttf'); BOLD=Path('C:/Windows/Fonts/arialbd.ttf'); ZH=Path('C:/Windows/Fonts/msyh.ttc')
for name,p in [('Arial',REG),('ArialBold',BOLD),('ZH',ZH)]:
    pdfmetrics.registerFont(TTFont(name,str(p),subfontIndex=0))
def sha(b): return hashlib.sha256(b).hexdigest()
def blob(b): return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def source(rel):
    b=(ROOT/rel).read_bytes(); mode='raw' if blob(b)==git[rel] else 'LF' if blob(b.replace(b'\r\n',b'\n'))==git[rel] else None
    assert mode, f'Local file is not bound to source main: {rel}'
    SOURCES[rel]={'sha256_local_bytes':sha(b),'bytes':len(b),'git_blob':git[rel],'binding':mode}
    return b
def js(rel): return json.loads(source(rel).decode('utf-8-sig'))
def tsv(rel): return list(csv.DictReader(io.StringIO(source(rel).decode('utf-8-sig')),delimiter='\t'))
def write_json(p,d): p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

class Graphic:
    def __init__(self,name,title,subtitle):
        self.name=name; self.cv=canvas.Canvas(str(FIG/(name+'.pdf')),pagesize=(W,H),invariant=1)
        self.cv.setTitle(title); self.svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><rect width="1280" height="720" fill="white"/>']; self.elements=[]
        self.text(50,57,title,31,bold=True)
        self.text(50,92,subtitle,17,color=MUTED)
        self.line(50,111,1230,111)
    def text(self,x,y,s,size=20,bold=False,color=INK,align='left',source_ref=None):
        assert all(ord(c)<128 for c in s),s
        font='ArialBold' if bold else 'Arial'; width=pdfmetrics.stringWidth(s,font,size)
        xx=x-width/2 if align=='center' else x-width if align=='right' else x
        assert xx>=15 and xx+width<=1265 and size<=y<=705,(self.name,s,xx,width,y)
        self.cv.setFont(font,size);self.cv.setFillColor(color);self.cv.drawString(xx,H-y,s)
        self.svg.append(f'<text x="{xx:.3f}" y="{y:.3f}" font-family="Arial" font-size="{size}" font-weight="{700 if bold else 400}" fill="{color}">{html.escape(s)}</text>')
        self.elements.append({'text':s,'x':xx,'baseline_y':y,'width':width,'font_size':size,'bold':bold,'source':source_ref})
    def line(self,x1,y1,x2,y2,color=GRID,width=1):
        self.cv.setStrokeColor(color);self.cv.setLineWidth(width);self.cv.line(x1,H-y1,x2,H-y2)
        self.svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"/>')
    def rect(self,x,y,w,h,fill,stroke=None):
        self.cv.setFillColor(fill);self.cv.setStrokeColor(stroke or fill);self.cv.rect(x,H-y-h,w,h,fill=1,stroke=bool(stroke))
        self.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke or fill}"/>')
    def dot(self,x,y,r=5,color=BLUE,diamond=False):
        self.cv.setFillColor(color);self.cv.setStrokeColor('white');self.cv.setLineWidth(.8)
        if diamond:
            p=self.cv.beginPath();p.moveTo(x,H-y+r);p.lineTo(x+r,H-y);p.lineTo(x,H-y-r);p.lineTo(x-r,H-y);p.close();self.cv.drawPath(p,fill=1,stroke=1)
            self.svg.append(f'<polygon points="{x},{y-r} {x+r},{y} {x},{y+r} {x-r},{y}" fill="{color}" stroke="white" stroke-width=".8"/>')
        else:
            self.cv.circle(x,H-y,r,fill=1,stroke=1);self.svg.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}" stroke="white" stroke-width=".8"/>')
    def footer(self,a,b=None):
        self.line(50,632,1230,632);self.text(50,665,a,17,color=MUTED)
        if b:self.text(50,695,b,16,color=RED)
    def finish(self):
        self.cv.showPage();self.cv.save();self.svg.append('</svg>')
        (FIG/(self.name+'.svg')).write_text('\n'.join(self.svg),encoding='utf-8')
        write_json(FIG/(self.name+'_elements.json'),self.elements)

A='research/2026-10-24_nearfull_complete/live/'
B='research/2026-10-23_literature/live_20261024/actual_demo/'
conv=js(A+'conversation_export_original.json');score=js(A+'tool_export/score_candidates.json');exp=js(A+'tool_export/query_expression.json')
ins=js(A+'tool_export/inspect_candidates.json')['rows'][0];plan=js(A+'tool_export/plan.json');raw_report=js(A+'tool_export/report.json')
calls=js(A+'actual_model_call_summary.json');other=plan['candidates'][0]['passenger_paired_core_19nt_5to3'];guide=ins['guide_core19_5to3']
assert len(guide)==len(other)==19 and 'GAUAGAGCAAGACAAGACAAGAAA' in raw_report['model_summary']
tools=[e for e in conv['events'] if e['kind']=='tool_finished']; assert len(tools)==6 and calls['total_tokens']==39048 and len(calls['calls'])==8
stats=exp['candidate_summary'][0]
g=Graphic('01_agent_case_compact','One purchased si-VEGF: a recorded Agent run','Saved records, re-typeset | Chinese request translated | run 20261024_121627_1e50c9')
g.text(50,158,'Request',20,bold=True,color=TEAL);g.text(155,158,'Review this duplex using its bound results and expression context.',23)
g.text(50,220,'a  Six confirmed steps, all executed',22,bold=True,color=BLUE)
names=['Check candidate','Match VEGFA reference','Read OligoFormer result','Read seed result','Join expression data','Save report']
for i,name in enumerate(names):
    y=271+i*49;g.text(55,y,f'{i+1:02d}',19,color=MUTED);g.text(103,y,name,22)
    g.text(552,y,'imported' if i in [2,3] else 'executed',18,color=TEAL,align='right')
g.text(680,220,'b  Verified tool fields',22,bold=True,color=BLUE)
g.text(680,267,"19-nt paired cores (5'-3'; conditional roles)",18,color=MUTED)
g.text(680,302,guide,24,bold=True,source_ref='inspect_candidates.rows[0].guide_core19_5to3')
g.text(680,337,other,24,bold=True,source_ref='plan.candidates[0].passenger_paired_core_19nt_5to3')
g.text(680,395,'1.1219',41,bold=True,color=TEAL);g.text(870,395,'model score, not %',22)
g.text(680,444,f"{stats['matched_genes']:,}",38,bold=True,color=BLUE);g.text(870,444,'non-target seed genes (guide)',20)
g.text(680,487,'18/20',36,bold=True,color=LILAC);g.text(870,487,'fixed reference transcripts',20)
g.text(50,594,'8 model requests = 1 planning + 7 execution; 6 tools.',20)
g.text(680,594,'Core-only analysis; TT/N3 not modeled.',18,color=MUTED)
g.footer('OligoFormer and seed results were imported from verified local computations.','Raw answer retained: one 19-nt core was miscopied as 24 nt. This table uses tool evidence.')
g.finish()

qa=js(B+'conversation/evidence/ef511585f2734fe999f4f28c.json');exchange=js(B+'conversation/evidence/8adf373e980643189b6f0479.json')
passed=json.loads(exchange['request']['input'][0]['content'][0]['text'])
assert len(passed['retrieved_excerpts'])==6 and all(a['text']==b['text'] and a['citation_id']==b['citation_id'] for a,b in zip(passed['retrieved_excerpts'],qa['retrieved_excerpts']))
sx={x['citation_id']:x for x in qa['retrieved_excerpts']}; assert 'prediction score for each siRNA' in sx['S3']['text'] and 'Y_PRED = [i*1.341 for i in Y_PRED]' in sx['S2']['text']
g=Graphic('02_literature_evidence_compact','An answer supported by retrieved evidence','B02 saved records | 1 model call | 6 retrieved excerpts | Translated question and answer excerpts')
g.text(50,167,'Does a score above 1 mean more than 100% knockdown?',29,bold=True)
g.text(50,243,'a  Evidence actually passed to the model',22,bold=True,color=BLUE)
g.text(50,303,'[S3] OligoFormer article',21,bold=True)
g.text(50,344,'"prediction score for each siRNA"',25,color=TEAL)
g.text(50,379,'DOI: 10.1093/bioinformatics/btae577',17,color=MUTED)
g.text(50,447,'[S2, S5] Official inference source',21,bold=True)
g.text(50,490,'Y_PRED = [i*1.341 for i in Y_PRED]',24,color=TEAL)
g.text(50,525,'scripts/infer.py @ e2f53ad63387',17,color=MUTED)
g.text(820,243,'b  Saved answer',22,bold=True,color=BLUE)
g.text(820,323,'No.',56,bold=True,color=TEAL)
g.text(820,382,'Prediction score',27,bold=True)
g.text(820,423,'is not measured',27)
g.text(820,464,'knockdown. [S1, S3]',27)
g.text(820,518,'Scaled by 1.341. [S2, S5]',20)
g.footer('English translations are labeled; source quotations are retained. This is not a webpage screenshot.','S1 is a project setting. This single question does not establish overall accuracy or Agent superiority.')
g.finish()

rows=tsv('research/2026-10-24_candidate_v2/new_65_complete_table.tsv')
purchased=tsv('research/2026-10-24_candidate_v2/purchased_siVEGF_separate.tsv')[0]
assert len(rows)==len({r['candidate_id'] for r in rows})==65
assert sum(r['old_working_pool_pass']=='True' for r in rows)==9
assert all(r['oligo_status']=='COMPLETED_REAL_NEW' for r in rows)
all104=tsv('research/2026-10-24_candidate_v2/all_104_decisions.tsv');assert len(all104)==104
COLORS={'5prime_UTR_or_boundary':CREAM,'CDS':BLUE,'3prime_UTR_or_boundary':LILAC,'3prime_UTR':LILAC}
print('FEATURES',json.dumps(Counter(r['reference_feature'] for r in rows)))
def axes(g,x,y,w,h,xmax,ymax,xticks,yticks,xlabel,ylabel):
    for val in yticks:
        py=y+h-h*val/ymax;g.line(x,py,x+w,py,color=GRID);g.text(x-9,py+5,f'{val:g}',15,color=MUTED,align='right')
    g.line(x,y,x,y+h,color=MUTED);g.line(x,y+h,x+w,y+h,color=MUTED)
    for val in xticks:
        px=x+w*val/xmax;g.line(px,y+h,px,y+h+5,color=MUTED);g.text(px,y+h+25,f'{val:g}',15,color=MUTED,align='center')
    g.text(x+w/2,y+h+59,xlabel,17,align='center');g.text(x,y-20,ylabel,17,color=MUTED)
    return lambda a,b:(x+w*a/xmax,y+h-h*b/ymax)
g=Graphic('03_candidate_results','A complete, traceable candidate pool','All 65 design predictions shown | Purchased si-VEGF is a separate entry | Existing calculations re-plotted')
g.text(50,157,'a  Candidate accounting',22,bold=True,color=BLUE)
for i,(label,n,c) in enumerate([('Original designs',104,PALE),('Reporting pool',65,BLUE),('Historical subset',9,LILAC)]):
    y=232+i*111;g.text(50,y-14,label,18);g.rect(50,y,250*n/104,35,c,stroke=GRID if n==104 else None);g.text(50+250*n/104+12,y+27,str(n),23,bold=True)
g.text(50,588,'Nested counts; not final selections.',16,color=MUTED)
g.text(420,157,'b  Score by target position',22,bold=True,color=BLUE)
xy=axes(g,450,230,303,290,4000,1.4,[0,2000,4000],[0,.4,.8,1.2],'Core start on NM_003376.6','OligoFormer scaled score')
for r in rows:g.dot(*xy(float(r['core_start_1based']),float(r['oligoformer_scaled_score'])),r=4.4,color=COLORS.get(r['reference_feature'],LILAC))
g.text(835,157,'c  Score and seed annotation',22,bold=True,color=BLUE)
seed_max=math.ceil(max(int(r['guide_matched_genes_non_target']) for r in rows+[purchased])/1000)*1000
xy=axes(g,880,230,330,290,1.4,seed_max,[0,.4,.8,1.2],list(range(0,seed_max+1,1000)),'OligoFormer scaled score','Guide non-target seed genes')
for r in rows:g.dot(*xy(float(r['oligoformer_scaled_score']),int(r['guide_matched_genes_non_target'])),r=4.4,color=COLORS.get(r['reference_feature'],LILAC))
g.dot(*xy(float(purchased['oligoformer_scaled_score']),int(purchased['guide_matched_genes_non_target'])),r=9,color=TEAL,diamond=True)
for x,label,c in [(425,'5-UTR / boundary',CREAM),(675,'CDS',BLUE),(810,'3-UTR',LILAC),(1055,'Purchased',TEAL)]:
    g.dot(x,606,r=5,color=c,diamond=label=='Purchased');g.text(x+12,612,label,16)
g.footer('Scores use the official 1.341 scale; they are not measured knockdown percentages.','Seed matches are sequence annotations. All sequence flags remain in the source table; no final wet-lab shortlist.')
g.finish()

full=tsv('research/2026-10-24_nearfull_complete/all_264_summary.tsv')
assert len(full)==792 and len({(r['candidate_id'],r['strand_role'],r['query_kind']) for r in full})==264
assert all(r['status']=='COMPLETED' for r in full)
query_kinds=[('guide','paired_core19'),('guide','sidirect_g2g20'),('passenger','paired_core19'),('passenger','sidirect_g2g20')]
labels=['Guide core','Guide 2-20','Other core','Other 2-20']
sets=[]
for strand,q in query_kinds:
    sets.append({r['candidate_id'] for r in full if r['candidate_id']!='USER_PURCHASED_siVEGF' and r['strand_role']==strand and r['query_kind']==q and r['max_mismatches']=='1' and int(r['non_target_gene_n'])>0})
assert [len(s) for s in sets]==[10,7,10,9] and len(set.union(*sets))==23
near_source=tsv('research/2026-10-24_nearfull_complete/figures/source_data.tsv')
g=Graphic('04_nearfull_results','Near-full checks: all 264 queries completed','65 designs + one purchased duplex | Four overlapping 19-nt queries per entry | Fixed 186,185-transcript reference')
g.text(50,159,'a  Designs with a non-target hit at <=1 mismatch',22,bold=True,color=BLUE)
g.text(770,159,'b  Purchased duplex: non-target genes',22,bold=True,color=BLUE)
xy=axes(g,115,231,510,285,4,12,[],[0,4,8,12],'Four strand / window checks','Number of designs')
for i,(s,label) in enumerate(zip(sets,labels)):
    x=147+i*123;y=516-285*len(s)/12;g.rect(x,y,64,516-y,BLUE if i<2 else LILAC);g.text(x+32,y-13,str(len(s)),24,bold=True,align='center');g.text(x+32,547,label,16,align='center')
xy=axes(g,827,231,360,285,3,4,[],[0,1,2,3,4],'Allowed mismatches (cumulative)','Distinct non-target genes')
vals=[]
for j,mm in enumerate([0,1,2]):
    group=[]
    for i,(strand,q) in enumerate(query_kinds):
        n=int(next(r['non_target_gene_n'] for r in full if r['candidate_id']=='USER_PURCHASED_siVEGF' and r['strand_role']==strand and r['query_kind']==q and int(r['max_mismatches'])==mm));group.append(n)
        x=843+j*123+i*21;y=516-285*n/4
        if n:g.rect(x,y,17,516-y,[BLUE,'#91B4CE',LILAC,'#C8BEDD'][i])
        g.text(x+8.5,y-10,str(n),17,align='center')
    vals.append(group);g.text(883+j*123,548,str(mm),18,align='center')
assert vals==[[0,0,0,0],[0,0,0,0],[1,3,3,3]]
g.text(56,606,'Union across the four checks: 23 / 65 designs (overlap allowed).',21,bold=True,color=TEAL)
g.text(810,605,'Bar order: guide core, guide 2-20,',16,color=MUTED);g.text(810,625,'other core, other 2-20.',16,color=MUTED)
g.footer('These overlapping queries are correlated checks, not four independent biological experiments.','Sequence matches are not measured off-target effects. The other 42 designs are not certified safe.')
g.finish()

baseline=tsv('research/2026-10-20_integrity_arial/paper/data/VEGFA_eight_samples_TPM.tsv')
groups={s:[float(r['TPM']) for r in baseline if r['state']==s] for s in ['Normoxia','Hypoxia']}
assert len(baseline)==8 and all(len(v)==4 for v in groups.values())
means={s:sum(v)/len(v) for s,v in groups.items()};ratio=means['Hypoxia']/means['Normoxia']
assert abs(means['Normoxia']-20.09929925)<1e-7 and abs(means['Hypoxia']-102.390068)<1e-7
g=Graphic('05_vegfa_baseline','VEGFA expression in untreated ARPE-19 dishes','Same culture batch | Four dishes per condition | Hypoxia: 1% O2 for 24 h | No siRNA or transfection reagent')
xy=axes(g,130,201,630,330,3,160,[],[0,40,80,120,160],'','VEGFA expression (TPM)')
for j,(state,vals) in enumerate(groups.items()):
    cx=330+j*310;c=BLUE if state=='Normoxia' else TEAL
    for off,v in zip([-37,-12,12,37],vals):g.dot(cx+off,531-330*v/160,r=8,color=c)
    mean=means[state];py=531-330*mean/160;g.line(cx-67,py,cx+67,py,color=c,width=3)
    g.text(cx,573,state,24,bold=True,align='center');g.text(cx,606,f'Mean {mean:.2f} TPM',19,align='center',color=c)
g.text(895,296,f'{ratio:.2f}x',70,bold=True,color=TEAL)
g.text(895,346,'ratio of group means',22)
g.text(895,420,'Descriptive baseline',23,bold=True)
g.text(895,458,'for this culture batch.',23)
g.footer('Dots are the eight actual dish-level TPM values; horizontal lines show group means.','This is expression context, not siRNA knockdown, four independent culture rounds, or a treatment effect.')
g.finish()

originals={
 '06_real_website.png':A+'case_completed.png',
 '07_local_retrieval.png':'research/2026-10-23_literature/offline/local_ui_search.png',
 '08_historical_auto.png':'research/2026-10-20_integrity_arial/paper/figures/Figure2_real_Auto_case.png',
 '09_original_agent.pdf':'research/2026-10-25_ppt_figures/figures/A_purchased_Agent_case.pdf',
 '10_original_literature.pdf':'research/2026-10-25_ppt_figures/figures/B_literature_answer_evidence.pdf'}
for name,rel in originals.items():(FIG/name).write_bytes(source(rel))
EVIDENCE.update({'base_main':snap['head'],'source_case':conv['run_id'],'source_case_code':conv['runtime']['commit'],
 'model_requests':8,'tool_calls':6,'model_tokens':39048,'historical_9_subset':9,'reporting_designs':65,'purchased_entries':1,
 'guide_seed_non_target_genes':stats['matched_genes'],'B02_code':qa['runtime']['commit'],'B02_library':qa['library_version'],
 'B02_all_six_excerpts_match_request':True,'full_nearfull_queries':264,'design_hits_by_query':[len(s) for s in sets],
 'union_design_hits_0or1mm':23,'purchased_cumulative_genes_by_threshold':vals,'baseline_means':means,'baseline_mean_ratio':ratio,
 'new_model_calls':0,'new_scientific_tool_runs':0,'original_files_modified':False})

GUIDE_W,GUIDE_H=1280,900
guide_path=OUT/'siRNA_Agent_PPT_Figure_Guide_20261025.pdf'
work=OUT/'guide_base.pdf'; cv=canvas.Canvas(str(work),pagesize=(GUIDE_W,GUIDE_H),invariant=1)
cv.setTitle('siRNA-GPT 图册：PPT用图与结论说明');cv.setAuthor('siRNA-GPT scientific review')
merges=[];page_text=[];page_no=0
def zhtext(x,y,s,size=18,color=INK):
    cv.setFont('ZH',size);cv.setFillColor(color);cv.drawString(x,GUIDE_H-y,s);page_text.append(s)
def wrap(s,font,size,width):
    lines=[];part=''
    for char in s:
        if char=='\n':lines.append(part);part='';continue
        if pdfmetrics.stringWidth(part+char,font,size)>width and part:
            if char in '。，；：？！、）》”’':lines.append(part+char);part=''
            else:lines.append(part);part=char
        else:part+=char
    if part:lines.append(part)
    return lines
def paragraph(x,y,s,width,size=18,leading=28,color=INK):
    lines=wrap(s,'ZH',size,width)
    for i,line in enumerate(lines):zhtext(x,y+i*leading,line,size,color)
    return y+len(lines)*leading
def header(title,sub):
    global page_no,page_text
    page_no+=1;page_text=[]
    cv.setFillColor(BLUE);cv.rect(0,GUIDE_H-8,GUIDE_W,8,fill=1,stroke=0)
    zhtext(50,48,title,27,BLUE);zhtext(50,78,sub,14,MUTED)
def footer(label='真实记录整理 · 2026-10-25 · 未新增模型调用或科学计算'):
    zhtext(50,875,label,12,MUTED);cv.setFont('Arial',12);cv.drawRightString(1230,25,f'{page_no:02d}')
    LAYOUT.append({'page':page_no,'text':page_text.copy()});cv.showPage()
def place(rel,area=(50,100,1180,612)):
    x,top,w,h=area; path=FIG/rel
    if path.suffix=='.pdf':
        p=PdfReader(path).pages[0];ow,oh=float(p.mediabox.width),float(p.mediabox.height)
    else:
        with Image.open(path) as im:ow,oh=im.size
    scale=min(w/ow,h/oh);dw,dh=ow*scale,oh*scale;xx=x+(w-dw)/2;bottom=GUIDE_H-top-h+(h-dh)/2
    if path.suffix=='.pdf':merges.append((page_no-1,path,scale,xx,bottom))
    else:cv.drawImage(str(path),xx,bottom,dw,dh,preserveAspectRatio=True,mask='auto')
def explanation(what,question,result,boundary):
    for x,label,body in [(50,'这是什么',what),(450,'要说明什么',question),(850,'得到什么结论',result)]:
        zhtext(x,739,label,18,TEAL);end=paragraph(x,768,body,360,size=17,leading=25)
        assert end<=846,(label,body,end)
    zhtext(50,850,'边界：'+boundary,14,RED)

header('siRNA-GPT：PPT 图册与结论说明','五张精简正文图 + 三项真实备份素材 + 两张原版记录图｜图内英文，解释用中文')
zhtext(65,158,'建议汇报顺序',27,TEAL)
contents=[('01','既购 si-VEGF 的真实 Agent 案例','系统按计划协调工具，汇总可追溯证据。'),
 ('02','文献问题、原文与实际回答','回答确实使用检索到的来源；仅展示这一次问答。'),
 ('03','完整 65 条候选的计算结果','展示候选来源、模型分数和种子匹配分布。'),
 ('04','完整 264 项近全长查询','展示全量检查；23/65 条存在非靶近似匹配。'),
 ('05','自有 RNA-seq 的 VEGFA 基线','同批次缺氧组均值更高；仅作表达背景。'),
 ('06–08','真实网页、检索界面与旧版案例','备份使用，保留各自的版本与限制。'),
 ('09–10','原版完整案例图','保留全部细节，方便追溯与答辩追问。')]
for i,(num,title,desc) in enumerate(contents):
    yy=218+i*70;zhtext(65,yy,num,21,BLUE);zhtext(175,yy,title,22);zhtext(175,yy+29,desc,17,MUTED)
paragraph(65,765,'当前证据支持“系统已完成真实案例与可追溯计算整理”。独立质量评分和 siRNA 实测效力仍未完成，不在本图册中补写。',1130,size=20,leading=31,color=RED)
zhtext(65,844,'seed：种子区短序列匹配；TPM：转录本相对表达量单位。seed计数与近全长匹配数不能直接比较。',14,MUTED)
footer()

pages=[
('图 01｜既购 si-VEGF：真实 Agent 运行','正文优先｜精简重排；不是网页截图；不是新模型运行','01_agent_case_compact.pdf',
 '一条既购双链的真实运行，按确认计划完成六步核查。','Agent 能否把序列、已有计算结果和表达背景接起来？','流程跑通并保存报告；8次模型请求对应1个案例。','分数和 seed 为本地结果导入；原答有19位错写24位，不能称回答全对。'),
('图 02｜文献证据支持的真实回答','正文优先｜原问答译文摘录；论文、源码与项目说明分开','02_literature_evidence_compact.pdf',
 'B02 的真实问题、实际传入的原文/源码和回答摘录。','模型是否真正取得来源，并按来源解释专业概念？','这一次问答正确区分模型分数与实测敲低率，引用可核对。','单题演示不代表总体准确率；项目说明不是外部论文结果。'),
('图 03｜候选来源、完整分数与 seed 注释','正文可用｜原104条、修订65条和历史9条的关系已标明','03_candidate_results.pdf',
 '全部65条设计的模型/seed结果，既购序列单列。','候选有无来源？是否只挑了少数高分结果展示？','完整池均有计算结果；各候选的分数与匹配注释存在差异。','9条是历史子集；高分不等于高实测效力；seed匹配不等于实验脱靶。'),
('图 04｜264 项近全长检查已全覆盖','正文可用｜65条设计+既购1条；每条按四种查询检查','04_nearfull_results.pdf',
 '两条链各按1–19、2–20位比对，共264项查询。','所有候选是否都检查？是否有接近全长的非靶匹配？','264项查询完成；65条中23条有0/1错配非靶匹配。','10、7、10、9不可相加成独立候选数；其余42条不能据此称安全。'),
('图 05｜自有 RNA-seq：VEGFA 表达基线','正文可用｜原始8个TPM点重绘；不增加统计显著性','05_vegfa_baseline.pdf',
 '同批ARPE-19常氧/缺氧各4皿，均未转染。','自己的RNA-seq能为课题提供什么直接背景证据？','该批次VEGFA均值为20.10与102.39 TPM，比值约5.09。','仅描述这批样本；不是4轮独立培养、siRNA敲低效果或状态风险重排序。'),
('图 06｜原网站的真实完成界面','备份素材｜2026-10-24既购案例；原图原样放入','06_real_website.png',
 '真实网站完成既购序列核查后的截图。','系统是否具有实际可操作的网页入口与结果界面？','该案例确实在原网站完成；界面可展示运行记录和结果。','完成状态不等于回答全部正确；原序列错误仍需同时说明。'),
('图 07｜本地文献检索的真实界面','备份素材｜历史本地检索界面，不当作最新完整问答','07_local_retrieval.png',
 '本地小型文献库检索后显示来源片段的截图。','用户能否检索资料，并看到命中的来源内容？','本地检索和来源片段展示已有实际入口。','此截图不能单独证明模型读过来源；真实模型问答证据请用图02。'),
('图 08｜旧版真实 Auto 案例：仅作历史备份','历史素材｜2026-10-20；原九条候选，区别于本次既购案例','08_historical_auto.png',
 '旧版Agent执行记录与原九条候选结果的组合图。','项目早期是否已有完整运行？前后版本如何区分？','旧版曾完成六工具案例，但使用的是另一批输入。','旧候选优先级不代表最新65条最佳；当时完整规划用量缺失，不能拿来比成本。'),
('图 09｜原版完整案例图 A','追溯备份｜保留原始图的时间、工具字段、用量与错误说明','09_original_agent.pdf',
 'Codex交付的未精简版既购案例证据图。','精简图中的细节能否回到完整记录？','版本、时间、结果与错误均有完整说明。','与图01是同一个案例，不作为新增样本或新模型回答。'),
('图 10｜原版完整文献图 B','追溯备份｜保留完整文章句子、源码与译文引用','10_original_literature.pdf',
 'Codex交付的未精简版B02证据图。','图02省略的文字与来源说明能否查到？','全文摘录、代码、项目说明和回答引用均可追溯。','与图02是同一道题，不增加独立题数，也不是专家评分。')]
for title,sub,rel,what,question,result,boundary in pages:
    header(title,sub);place(rel);explanation(what,question,result,boundary);footer()

header('这些图能支撑的论文表述','结论按证据层级表达，保留尚未完成的关键环节')
rows_table=[
 ('图01 / 图06','已完成一个真实网页Agent案例，能按确认计划连接六项工具。','系统总体可靠、回答完全正确、优于固定流程。'),
 ('图02 / 图07','已有小文献库检索和一次有来源的真实模型问答。','文库覆盖全部领域文献，或模型总体准确率已得到验证。'),
 ('图03','65条设计与单列既购序列的模型及seed结果已完整整理。','高分即高敲低率，或全部候选都适合订购/实验。'),
 ('图04','264项查询全覆盖，23条设计存在指定条件的非靶近似匹配。','23条已证实脱靶，其余42条已获安全认证。'),
 ('图05','自有未干预RNA-seq提供了本批次VEGFA表达背景。','已经验证siRNA敲低效果，或实现状态风险重排序。')]
for x,s in [(55,'图号'),(250,'现在可以说'),(760,'目前证据不支持')]:zhtext(x,155,s,23,TEAL)
for i,(n,a,b) in enumerate(rows_table):
    yy=214+i*99;cv.setStrokeColor(GRID);cv.line(50,GUIDE_H-yy+24,1230,GUIDE_H-yy+24)
    zhtext(55,yy,n,19);paragraph(250,yy,a,450,19,28);paragraph(760,yy,b,455,19,28,RED)
paragraph(55,760,'下一项关键研究证据仍是独立人员对三组真实回答评分。当前图册没有代填评分，没有新增湿实验，没有调整候选规则或排序。',1160,size=22,leading=34)
footer('来源：main '+snap['head'][:7]+'；完整路径与文件指纹见配套 SOURCE_MAP.md / source_manifest.json。')
cv.save()

reader=PdfReader(work);writer=PdfWriter()
for idx,p in enumerate(reader.pages):
    for target_idx,path,scale,x,y in merges:
        if idx==target_idx:p.merge_transformed_page(PdfReader(path).pages[0],Transformation().scale(scale).translate(x,y),over=True)
    writer.add_page(p)
writer.add_metadata({'/Title':'siRNA-GPT 图册：PPT用图与结论说明','/Author':'siRNA-GPT scientific review','/Subject':'真实记录重排；每图中文解释；非新增科学结果'})
with guide_path.open('wb') as f:writer.write(f)
work.unlink()

pdf_checks=[]
for path in sorted(FIG.glob('0[1-5]*.pdf')):
    reader=PdfReader(path);p=reader.pages[0];current_font=None;used=[]
    for operands,op in ContentStream(p['/Contents'].get_object(),reader).operations:
        if op==b'Tf':current_font=operands[0]
        if op in [b'Tj',b'TJ',b"'",b'"']:
            font=p['/Resources']['/Font'][current_font].get_object();used.append(str(font['/BaseFont']));assert 'Arial' in str(font['/BaseFont'])
            assert '/FontFile2' in font['/FontDescriptor'].get_object()
    text=p.extract_text();elements=json.loads(path.with_name(path.stem+'_elements.json').read_text(encoding='utf-8'))
    assert all(e['text'] in text for e in elements)
    root=ET.parse(path.with_suffix('.svg')).getroot();assert all(e.get('font-family')=='Arial' for e in root.findall('{http://www.w3.org/2000/svg}text'))
    words=len(' '.join(e['text'] for e in elements).split())
    pdf_checks.append({'name':path.stem,'words_approximately':words,'embedded_fonts_used':sorted(set(used)),'page':[1280,720],'all_labels_in_PDF':True})

poppler=shutil.which('pdftoppm'); assert poppler,'Poppler required'
for path in sorted(FIG.glob('0[1-5]*.pdf')):
    subprocess.run([poppler,'-png','-singlefile','-scale-to-x','2560','-scale-to-y','1440',str(path),str(path.with_suffix(''))],check=True,capture_output=True)
subprocess.run([poppler,'-jpeg','-scale-to','1500',str(guide_path),str(PREVIEW/'page')],check=True,capture_output=True)
final=PdfReader(guide_path);assert len(final.pages)==12
for i,p in enumerate(final.pages):
    text=p.extract_text();assert chr(65533) not in text
    assert any(s in text for s in ['这是什么','建议汇报顺序','现在可以说']), (i,text[:300])
    assert tuple(map(float,p.mediabox[2:]))==(1280,900)
guide_fontnames=set()
for p in final.pages:
    for r in p['/Resources']['/Font'].values():
        f=r.get_object()
        if '/FontDescriptor' in f:
            assert '/FontFile2' in f['/FontDescriptor'].get_object();guide_fontnames.add(str(f['/BaseFont']))
assert any('Microsoft' in n or 'YaHei' in n for n in guide_fontnames),guide_fontnames

thumbs=[]
for p in sorted(PREVIEW.glob('page-*.jpg')):
    with Image.open(p) as im:
        im=ImageOps.contain(im.convert('RGB'),(512,360));tile=Image.new('RGB',(530,390),'#E6EBEE');tile.paste(im,((530-im.width)//2,6));ImageDraw.Draw(tile).text((12,373),p.stem,fill='#244F73');thumbs.append(tile)
sheet=Image.new('RGB',(530*3,390*4),'white')
for i,t in enumerate(thumbs):sheet.paste(t,((i%3)*530,(i//3)*390))
sheet.save(PREVIEW/'contact_sheet.jpg',quality=92)

write_json(OUT/'source_manifest.json',{'main':snap['head'],'files':SOURCES})
write_json(OUT/'source_git_tree.json',{'head':snap['head'],'tree':{'tree':[{'path':p,'type':'blob','sha':v['git_blob']} for p,v in SOURCES.items()]}})
write_json(OUT/'figure_data_checks.json',EVIDENCE)
write_json(OUT/'format_checks.json',{'new_figures':pdf_checks,'guide_pages':12,'guide_fonts_embedded':sorted(guide_fontnames),'chinese_text_no_replacement_characters':True,'visual_inspection':'pending final review of rendered pages'})
write_json(OUT/'page_text.json',LAYOUT)
source_lines=['# 来源与用途','',f'所用main：`{snap["head"]}`。源文件均与Git blob核对；PNG原截图未改像素。','',
 '图01/02是保存记录的英文精简重排，图03/04/05从完整底表绘图；没有新增模型请求或科学工具运行。',
 '图01的正确序列取自工具字段，原模型24位错误保留说明。图02是原中文问答的译文摘录，S1项目说明不冒充外部论文。',
 '图03只复用旧表中已完成的分数与seed字段，不沿用旧表NOT_RUN近全长状态；全量近全长结果以图04所用新表为准。',
 '图03不再沿用旧图注中的“只有24项近全长完成”这一历史状态。',
 '图04保留固定参考与条件；四种查询互相重叠，23条是候选并集。原始末端18位边缘匹配保留在历史证据，不影响本图两面板。',
 '图05来自八个原TPM点，仅画均值、不增加显著性检验。图08为旧版案例，不与新案例混算用量或候选。','',
 '## 图册逐页说明','']
for n,(_,sub,rel,what,question,result,boundary) in enumerate(pages,1):
    source_lines.extend([f'### 图{n:02d}：{rel}',f'- 这是什么：{what}',f'- 要说明什么：{question}',f'- 得到什么结论：{result}',f'- 边界：{boundary}',''])
source_lines.extend(['## 精确原件路径','']+[f'- `{p}`' for p in SOURCES])
(OUT/'SOURCE_MAP.md').write_text('\n'.join(source_lines)+'\n',encoding='utf-8')
(OUT/'README.md').write_text('# PPT图册（2026-10-25）\n\n[12页PDF图册](siRNA_Agent_PPT_Figure_Guide_20261025.pdf)：五张精简英文核心图、三项真实备份素材、两张原版记录图及逐图中文解释。\n\n图内是可追溯的已有记录/数据；没有新增模型、评分、seed或近全长计算。英文图为Arial；中文说明用嵌入微软雅黑。\n\n`figures/01–05`提供PNG/PDF/SVG；`SOURCE_MAP.md`解释每图的用途、结论和限制；`source_manifest.json`记录主版本与来源指纹。旧原件不改，三组独立评分和实测效力不在本批补写。\n\n重排命令（在本目录，使用已安装ReportLab/PyPDF/Pillow和Poppler的Windows Python）：`python build_guide.py --repo <原仓库绝对路径> --tree source_git_tree.json --out <新输出路径>`。只读取已绑定的原文件，不执行模型或科学工具；原仓库输入不能被本脚本覆盖。\n',encoding='utf-8')
shutil.copyfile(Path(__file__),OUT/'build_guide.py')
print(json.dumps({'output':str(OUT),'guide_pdf':str(guide_path),'pages':12,'new_figures':pdf_checks,'source_files':len(SOURCES)},ensure_ascii=False))
