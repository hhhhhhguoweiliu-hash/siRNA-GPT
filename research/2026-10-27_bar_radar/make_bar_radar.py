"""Existing expert scores, shown as paired bars and radar.
Usage: python make_bar_radar.py [plot_data.json]
No new ratings, no Accuracy/Precision/Recall/F1 conversion.
"""
from pathlib import Path
from functools import lru_cache
from xml.sax.saxutils import escape
import ast,sys,json,csv,hashlib,math
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image,ImageDraw,ImageFont
from pypdf import PdfReader,PdfWriter
from openpyxl import Workbook
ROOT=Path(__file__).resolve().parent;FIG=ROOT/'figures';FIG.mkdir(exist_ok=True)
FONT=Path(r'C:\Windows\Fonts\arialbd.ttf');assert FONT.is_file()
pdfmetrics.registerFont(TTFont('ArialBold',str(FONT)))
SRC=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT.parent/'2026-10-27_expert_figures/plot_data.json'
data=json.loads(SRC.read_text(encoding='utf-8'))
manifest=json.loads((SRC.parent/'file_manifest.json').read_text(encoding='utf-8'))
source_hash=hashlib.sha256(SRC.read_bytes()).hexdigest()
assert source_hash==next(x['sha256'] for x in manifest['files'] if x['path']=='plot_data.json')
renderer_path=SRC.parent/'make_expert_figures.py'
tree=ast.parse(renderer_path.read_text(encoding='utf-8-sig'))
plot_node=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Plot')
# Load the existing renderer class only, without running its old analysis.
exec(compile(ast.Module(body=[plot_node],type_ignores=[]),str(renderer_path),'exec'))
GROUPS=['llm','workflow','agent'];NAMES={'llm':'LLM','workflow':'Fixed workflow','agent':'Agent'}
COLORS={'llm':'#8295B3','workflow':'#E6B77C','agent':'#A44958'}
DIMKEYS=['factual_accuracy','evidence_support','requirement_completion','boundary_handling']
DIMS=['Factual\naccuracy','Evidence\nsupport','Requirement\ncompletion','Boundary\nhandling']
STRATA={'Standard tasks':4,'Reliability':4,'Requirement change':1}
assert len(data['means'])==72
used=[]
def marker(p,x,y,g,size=4):
 if g=='llm':p.dot(x,y,size,COLORS[g])
 elif g=='workflow':p.rect(x-size,y-size,2*size,2*size,'#FFFFFF',COLORS[g])
 else:
  pts=[(x,y-size-1),(x+size+1,y),(x,y+size+1),(x-size-1,y)]
  for a,b in zip(pts,pts[1:]+pts[:1]):p.line(*a,*b,COLORS[g],1.4)
def values_for(form,st,g):
 values=[]
 for i,dim in enumerate(DIMKEYS):
  rr=[r for r in data['means'] if r['form']==form and r['stratum']==st and r['group']==g and r['dimension']==dim]
  assert len(rr)==1 and rr[0]['n']==STRATA[st]
  value=rr[0]['mean'];raw=[r['scores'][i] for r in data['rows'] if r['form']==form and r['stratum']==st and r['group']==g]
  assert len(raw)==STRATA[st] and math.isclose(value,sum(raw)/len(raw),abs_tol=1e-12) and 0<=value<=2
  values.append(value);used.append({**rr[0],'bar_value':value,'radar_value':value})
 return values
def make(st,name):
 p=Plot(1200,825)
 p.text(40,35,st+': existing expert scores',27)
 p.text(40,61,'Identical 0–2 scores shown as bars and radar profiles',16,color='#666666')
 for x,g in zip([305,555,865],GROUPS):
  p.rect(x,83,20,14,COLORS[g]);marker(p,x+10,90,g,3);p.text(x+30,97,NAMES[g],17)
 for row,form in enumerate(['A','B']):
  x=95;y=185+row*320;ww=510;hh=155
  p.text(x-39,y-48,chr(97+row*2),22);p.text(x+ww/2,y-48,'Form '+form+' | mean scores',19,'middle')
  p.text(755,y-48,chr(98+row*2),22);p.text(955,y-48,'Form '+form+' | radar',19,'middle')
  for tick in [0,1,2]:
   yy=y+hh-hh*tick/2;p.line(x,yy,x+ww,yy,'#E5E5E5',.8);p.line(x-5,yy,x,yy);p.text(x-13,yy+5,tick,15,'end')
  p.line(x,y,x,y+hh);p.line(x,y+hh,x+ww,y+hh);p.text(x-50,y+hh/2,'Expert score (0–2)',17,'middle',angle=-90)
  values={g:values_for(form,st,g) for g in GROUPS}
  for i,label in enumerate(DIMS):
   center=x+(i+.5)*ww/4
   for gi,g in enumerate(GROUPS):
    xx=center+(gi-1)*29;height=hh*values[g][i]/2
    p.rect(xx-11,y+hh-height,22,height,COLORS[g],'#414141')
    raw=[r['scores'][i] for r in data['rows'] if r['form']==form and r['stratum']==st and r['group']==g]
    for ri,score in enumerate(raw):p.dot(xx+(ri-(len(raw)-1)/2)*3.8,y+hh-hh*score/2,2.7)
   p.text(center,y+hh+29,label,16,'middle')
  cx=955;cy=y+77;radius=78;unit=[(0,-1),(1,0),(0,1),(-1,0)]
  for level in [.5,1,1.5,2]:
   pts=[(cx+dx*radius*level/2,cy+dy*radius*level/2) for dx,dy in unit]
   for a,b in zip(pts,pts[1:]+pts[:1]):p.line(*a,*b,'#D8D8D8',.8)
  for dx,dy in unit:p.line(cx,cy,cx+dx*radius,cy+dy*radius,'#C9C9C9',.8)
  for level in [1,2]:p.text(cx+8,cy-radius*level/2+4,str(level),12,color='#777777')
  p.text(cx+8,cy+15,'0',12,color='#777777')
  p.text(cx,cy-radius-23,DIMS[0],16,'middle')
  p.text(cx+radius+19,cy-2,DIMS[1],16)
  p.text(cx,cy+radius+25,DIMS[2],16,'middle')
  p.text(cx-radius-19,cy-2,DIMS[3],16,'end')
  for g in GROUPS:
   pts=[(cx+dx*radius*v/2,cy+dy*radius*v/2) for (dx,dy),v in zip(unit,values[g])]
   for a,b in zip(pts,pts[1:]+pts[:1]):p.line(*a,*b,COLORS[g],2.6 if g=='workflow' else 1.9)
   for xx,yy in pts:marker(p,xx,yy,g,3.8)
 p.text(40,755,f'n = {STRATA[st]} task episode(s) per group; bar dots show all task scores. Forms are not pooled.',16)
 p.text(40,784,'Submitted ratings; evidence checks pending. Rating scores, not classification metrics or user-experience scores.',14,color='#777777')
 p.output(name)
for st,name in [('Standard tasks','fig1_standard_bar_radar'),('Reliability','figS1_reliability_bar_radar'),('Requirement change','figS2_change_bar_radar')]:make(st,name)
assert len(used)==72 and all(x['bar_value']==x['radar_value']==x['mean'] for x in used)
with (ROOT/'bar_radar_plot_data.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(used[0]));w.writeheader();w.writerows(used)
w=Workbook();ws=w.active;ws.title='Exact_values';ws.append(list(used[0]))
for r in used:ws.append(list(r.values()))
ws.freeze_panes='A2';ws.auto_filter.ref=ws.dimensions
for c in ws.columns:ws.column_dimensions[c[0].column_letter].width=25
note=w.create_sheet('说明')
for rr in [
 ['数据来源','沿用已经绘制图的A/B两份评分。'],
 ['雷达图轴','事实准确、证据支持、需求完成、边界处理；0-2分。'],
 ['数字关系','柱图和雷达图72个数值逐项相同，无新增评分或归一化。'],
 ['分组','标准4题、可靠性4题、变化1题分开，不混成总体能力。'],
 ['指标限制','不能从专家均分换算Accuracy/Precision/Recall/F1，不填估计值。'],
 ['评审状态','原评分理由仍有待核对项；A/B不平均，不将文件数当评审人数。'],
 ['没有新增','无模型调用、科学重算、人工评分或新试验。']]:note.append(rr)
note.column_dimensions['A'].width=20;note.column_dimensions['B'].width=100;w.save(ROOT/'bar_radar_plot_data.xlsx')
writer=PdfWriter()
for name in ['fig1_standard_bar_radar','figS1_reliability_bar_radar','figS2_change_bar_radar']:
 for pg in PdfReader(FIG/(name+'.pdf')).pages:writer.add_page(pg)
with (ROOT/'siRNA_GPT_bar_radar_existing_scores_REVIEW_PENDING.pdf').open('wb') as f:writer.write(f)
fontcheck=[]
for path in FIG.glob('*.pdf'):
 fs=[]
 for page in PdfReader(path).pages:
  for obj in page['/Resources']['/Font'].get_object().values():
   font=obj.get_object();name=str(font.get('/BaseFont'));fd=font.get('/FontDescriptor')
   if 'Arial' in name:fs.append({'name':name,'embedded':bool(fd and '/FontFile2' in fd.get_object())})
 assert fs and all('Bold' in f['name'] and f['embedded'] for f in fs);fontcheck.append({'file':path.name,'actual_text_fonts':fs})
checks={'source_plot_data_sha256':source_hash,'source_hash_matches_existing_figure_manifest':True,'source_commit':'748a71bec7043fdd9b031731c237f687009f015b','n_exact_mean_values':72,'bar_and_radar_values_identical':True,'all_means_recomputed_from_original_score_rows':True,'score_scale':[0,2],'forms_pooled':False,'new_scores':0,'new_model_calls':0,'classification_accuracy':None,'precision':None,'recall':None,'f1':None,'png_dpi':600,'pdf_embedded_fonts':fontcheck,'pages':len(PdfReader(ROOT/'siRNA_GPT_bar_radar_existing_scores_REVIEW_PENDING.pdf').pages)}
(ROOT/'figure_checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'figures':3,'pages':checks['pages'],'n_exact_mean_values':72,'all_source_values_preserved':True,'Arial_Bold_embedded':True},ensure_ascii=True))

