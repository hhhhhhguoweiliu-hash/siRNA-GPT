"""Restyle verified metrics; no model calls, relabelling, or metric recomputation.

Run from this directory with --font /path/to/Arial-Bold.ttf.
Only a verified Arial Bold font is accepted. No font file is redistributed.
"""
import argparse,csv,hashlib,json,re
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager,text as mpltext
from matplotlib.patches import Patch
from fontTools.ttLib import TTFont
from PIL import Image

HERE=Path(__file__).resolve().parent
GROUPS=['llm','workflow','agent']
LABELS={'llm':'Generic LLM','workflow':'Fixed workflow','agent':'Agent'}
# Sampled from solid bar interiors in CRISPR-GPT Figure 3b, not estimated by eye.
COLORS={'llm':'#AB88B3','workflow':'#99C4CE','agent':'#90D9CA'}
EDGE='#303338';INK='#17191C';GRID='#E8EAED'

def read(name):
 with (HERE/'data'/name).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def run(font_path):
 font_path=font_path.resolve();tt=TTFont(font_path)
 def names(n):return {x.toUnicode() for x in tt['name'].names if x.nameID==n}
 assert any(x=='Arial' for x in names(1)),names(1)
 assert any('Bold' in x for x in names(2)),names(2)
 assert any('Arial-Bold' in x for x in names(6)),names(6)
 assert all(i in tt.getBestCmap() for i in range(32,127))
 font_manager.fontManager.addfont(str(font_path));prop=font_manager.FontProperties(family='Arial',weight='bold',fname=str(font_path))
 assert prop.get_name()=='Arial'
 plt.rcParams.update({'font.family':'Arial','font.weight':'bold','axes.labelweight':'bold','axes.titleweight':'bold','font.size':12,'text.color':INK,'axes.labelcolor':INK,'xtick.color':INK,'ytick.color':INK,'axes.edgecolor':EDGE,'axes.linewidth':1.0,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none','figure.facecolor':'white','savefig.facecolor':'white','legend.frameon':False,'xtick.major.size':4,'ytick.major.size':4})
 metric={r['group']:r for r in read('metrics_by_group_category.csv') if r['category']=='OVERALL'}
 task={r['group']:r for r in read('task_pass_rates.csv') if r['category']=='OVERALL'}
 assert all(int(r['n_tasks'])==9 and int(r['micro_n_slots'])==135 for r in metric.values())
 assert {g:int(task[g]['passed']) for g in GROUPS}=={'llm':0,'workflow':8,'agent':9}
 records=[];exports=[];(HERE/'figures').mkdir(exist_ok=True)
 def axes(ax,ylabel=True,tick_size=12):
  ax.set_ylim(0,1.13);ax.set_yticks(np.linspace(0,1,6));ax.grid(axis='y',color=GRID,lw=.7,zorder=0)
  ax.set_axisbelow(True);ax.tick_params(axis='both',labelsize=tick_size,pad=5)
  if ylabel:ax.set_ylabel('Score',fontsize=14,labelpad=9)
 def save(fig,stem,figure_kind):
  for t in fig.findobj(match=mpltext.Text):
   size=t.get_fontsize();t.set_fontproperties(prop);t.set_fontsize(size)
  fig.canvas.draw();renderer=fig.canvas.get_renderer();fw,fh=fig.canvas.get_width_height()
  for t in fig.findobj(match=mpltext.Text):
   if not t.get_visible() or not t.get_text():continue
   bounds=t.get_window_extent(renderer)
   assert bounds.x0>=-1 and bounds.y0>=-1 and bounds.x1<=fw+1 and bounds.y1<=fh+1,('clipped_text',stem,t.get_text(),tuple(bounds.bounds),fw,fh)
   resolved=font_manager.findfont(t.get_fontproperties(),fallback_to_default=False)
   assert Path(resolved).resolve()==font_path,('wrong_font',t.get_text(),resolved)
   assert t.get_fontproperties().get_weight() in ['bold',700]
   assert t.get_fontproperties().get_family()==['Arial']
  stem_path=HERE/'figures'/stem
  fig.savefig(str(stem_path)+'.png',dpi=600)
  fig.savefig(str(stem_path)+'.svg')
  svg=Path(str(stem_path)+'.svg').read_text()
  assert '<image' not in svg and '<text' in svg
  import xml.etree.ElementTree as ET
  text_styles=[e.attrib.get('style','') for e in ET.fromstring(svg).iter() if e.tag.endswith('}text')]
  assert text_styles and all('Arial' in s and 'DejaVu' not in s and re.search(r'font-weight:\s*(700|bold)|font:\s*700',s) for s in text_styles),text_styles[:2]
  image=Image.open(str(stem_path)+'.png');pixels=image.size;dpi=image.info.get('dpi');image.verify()
  exports.append({'stem':stem,'kind':figure_kind,'size_inches':list(fig.get_size_inches()),'png_pixels':pixels,'png_dpi':dpi,'text_clipping_check':'passed','font_file_used_for_every_text_artist':'Arial Bold verified','svg_text_editable':True,'svg_raster_layers':0})
  plt.close(fig)
 def bars_for_metrics(ax,aggregation,figid,value_size=10):
  x=np.arange(3);width=.235
  for i,g in enumerate(GROUPS):
   values=[float(metric[g][aggregation+'_'+m]) for m in ['precision','recall','f1']]
   bars=ax.bar(x+(i-1)*width,values,width=width,color=COLORS[g],edgecolor=EDGE,linewidth=.8,zorder=3,label=LABELS[g])
   for j,(bar,value) in enumerate(zip(bars,values)):
    ax.text(bar.get_x()+bar.get_width()/2,value+.022,f'{value:.4f}',ha='center',va='bottom',fontsize=value_size)
    records.append({'figure':figid,'group':g,'metric':['precision','recall','f1'][j],'aggregation':aggregation,'value':value,'numerator':'','denominator':135})
  ax.set_xticks(x,['Precision','Recall','F1']);axes(ax)
 def legend(fig,anchor,fontsize=12):
  handles=[Patch(facecolor=COLORS[g],edgecolor=EDGE,linewidth=.8,label=LABELS[g]) for g in GROUPS]
  fig.legend(handles=handles,loc='upper center',bbox_to_anchor=anchor,ncol=3,fontsize=fontsize,handlelength=1.4,handleheight=.9,columnspacing=1.6,handletextpad=.55)
 for aggregation,stem,title in [('macro','Fig1_macro_precision_recall_f1_BCC','Task-averaged required-slot metrics'),('micro','FigS1_micro_precision_recall_f1_BCC','Overall required-slot metrics')]:
  fig,ax=plt.subplots(figsize=(8.4,5.4));fig.subplots_adjust(left=.12,right=.98,bottom=.16,top=.76)
  bars_for_metrics(ax,aggregation,stem,value_size=10.5)
  fig.text(.12,.947,title,fontsize=17,ha='left',va='top')
  legend(fig,(.55,.875),fontsize=12)
  save(fig,stem,aggregation)
 fig,ax=plt.subplots(figsize=(7.2,5.0));fig.subplots_adjust(left=.14,right=.98,bottom=.17,top=.80)
 xs=np.arange(3);values=[float(task[g]['pass_rate']) for g in GROUPS]
 bars=ax.bar(xs,values,width=.54,color=[COLORS[g] for g in GROUPS],edgecolor=EDGE,linewidth=.9,zorder=3)
 for bar,g,value in zip(bars,GROUPS,values):
  label=f'{int(task[g]["passed"])}/9 ({100*value:.1f}%)';ax.text(bar.get_x()+bar.get_width()/2,value+.03,label,ha='center',va='bottom',fontsize=12)
  records.append({'figure':'Fig2_task_pass_rate_reconciled','group':g,'metric':'Task-level PASS rate','aggregation':'task','value':value,'numerator':int(task[g]['passed']),'denominator':9})
 axes(ax,False);ax.set_ylabel('Task-level PASS rate',fontsize=14,labelpad=9);ax.set_xticks(xs,[LABELS[g] for g in GROUPS]);ax.tick_params(axis='x',labelsize=12)
 fig.text(.14,.95,'Task-level PASS rate',fontsize=17,ha='left',va='top')
 save(fig,'Fig2_task_pass_rate_reconciled','task')
 fig,(left,right)=plt.subplots(1,2,figsize=(12.8,5.6),gridspec_kw={'width_ratios':[1,1.85]})
 fig.subplots_adjust(left=.075,right=.985,bottom=.25,top=.74,wspace=.30)
 left_bars=left.bar(range(3),values,width=.54,color=[COLORS[g] for g in GROUPS],edgecolor=EDGE,linewidth=.9,zorder=3)
 axes(left,False);left.set_ylabel('Proportion',fontsize=14,labelpad=8);left.set_xticks(range(3),['LLM','Workflow','Agent'])
 for bar,g,value in zip(left_bars,GROUPS,values):
  left.text(bar.get_x()+bar.get_width()/2,value+.035,f'{int(task[g]["passed"])}/9',ha='center',fontsize=12)
  records.append({'figure':'Fig3_task_and_slot_metrics_separate_panels','group':g,'metric':'Task-level PASS rate','aggregation':'task','value':value,'numerator':int(task[g]['passed']),'denominator':9})
 left.set_title('Task-level PASS rate',fontsize=15,loc='left',pad=17)
 bars_for_metrics(right,'micro','Fig3_task_and_slot_metrics_separate_panels',value_size=10)
 right.set_ylabel('');right.set_title('Required-slot metrics (micro)',fontsize=15,loc='left',pad=17)
 for ax,label in [(left,'a'),(right,'b')]:ax.text(-.17,1.12,label,transform=ax.transAxes,fontsize=20,va='top',ha='left')
 fig.text(.075,.96,'Task-level PASS and required-slot metrics',fontsize=18,ha='left',va='top')
 legend(fig,(.60,.88),fontsize=13)
 fig.text(.075,.13,'a  Existing project task adjudication; 9 seen tasks per system.',fontsize=10.5)
 fig.text(.075,.075,'b  AI-assisted review + BCC adjudication; 135 required slots per system.',fontsize=10.5)
 save(fig,'Fig3_task_and_slot_metrics_separate_panels','separate_task_and_slot_units')
 with (HERE/'data'/'figure_plot_data.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
 data_files=list((HERE/'data').glob('*'));data_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in data_files}
 checks={'font_family':'Arial','font_subfamily':'Bold','font_postscript_names':sorted(names(6)),'font_file_sha256':hashlib.sha256(font_path.read_bytes()).hexdigest(),'fallback_allowed':False,'all_text_uses_explicit_font_file':True,'exports':exports,'data_sha256':data_hashes,'new_model_calls':0,'new_scientific_runs':0,'new_label_changes':0,'pdf_outputs':0}
 (HERE/'font_and_export_checks.json').write_text(json.dumps(checks,indent=2)+'\n')
 print(json.dumps({'figures':len(exports),'all_fonts_verified':True,'all_text_inside_canvas':True,'palette':COLORS,'output_dir':str(HERE/'figures')}))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--font',type=Path,required=True,help='Actual Arial Bold TTF; fail rather than substitute.')
 args=p.parse_args();run(args.font)
