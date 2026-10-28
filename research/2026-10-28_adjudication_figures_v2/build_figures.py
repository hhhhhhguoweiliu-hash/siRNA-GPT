"""Corrected, category-separated scientific figures; require actual Arial fonts.

Set PYTHONPATH to an installed Matplotlib environment if necessary. This script
does not call scientific tools or models and never edits the source reviews.
"""
import argparse,hashlib,json,sys
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from matplotlib.patches import Patch
from matplotlib.colors import ListedColormap
from pypdf import PdfReader,PdfWriter
from audit_data import HERE,GROUPS,CATEGORIES,DIMS,load_data,write_analysis

FIGURES=HERE/'figures';PDF_OUT=HERE/'output/pdf'
COMBINED=PDF_OUT/'siRNA_GPT_corrected_adjudication_figures_20261028.pdf'
NAMES=['Fig1_task_pass_by_category','Fig2_slot_macro_by_category','Fig3A_scores_A_by_category','Fig3C_scores_C_by_category',
       'Fig4A_score_matrix_A','FigS1_score_matrix_C','FigS2_changed_task_verdicts','FigS3_overall_slot_micro']
LABELS={'llm':'LLM','workflow':'Workflow','agent':'Agent'}
FULL={'llm':'Generic LLM','workflow':'Fixed workflow','agent':'Agent'}
COLORS={'llm':'#3477A5','workflow':'#C77B28','agent':'#278577'}
CAT={'STANDARD_TASK':'Standard work (4 tasks)','REQUIREMENT_CHANGE':'Requirement change (1 task)','RELIABILITY':'Reliability (4 tasks)'}

def set_fonts():
    fonts={'normal':Path('C:/Windows/Fonts/arial.ttf'),'bold':Path('C:/Windows/Fonts/arialbd.ttf')}
    result={}
    for weight,path in fonts.items():
        if not path.is_file():raise RuntimeError('Actual Arial font missing: '+str(path)+'; no substitute permitted')
        font_manager.fontManager.addfont(str(path))
        resolved=Path(font_manager.findfont(font_manager.FontProperties(family='Arial',weight=weight),fallback_to_default=False))
        if resolved.resolve()!=path.resolve():raise RuntimeError('Unexpected font resolution: '+str(resolved))
        result[weight]={'path':str(path),'family':font_manager.FontProperties(fname=str(path)).get_name(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    plt.rcParams.update({'font.family':'Arial','font.weight':'normal','font.size':10,'axes.labelweight':'normal','axes.titleweight':'bold',
        'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none','svg.hashsalt':'sirna-corrected-20261028','axes.unicode_minus':False,
        'axes.spines.top':False,'axes.spines.right':False,'savefig.facecolor':'white','figure.facecolor':'white'})
    return result

def decorate(fig,title,subtitle,footer,legend=True,heatmap=False):
    fig.suptitle(title,x=.055,y=.967,ha='left',fontsize=16,fontweight='bold')
    fig.text(.055,.914,subtitle,ha='left',fontsize=10,color='#374151')
    fig.text(.055,.10,footer,ha='left',va='top',fontsize=8.1,linespacing=1.45,color='#374151')
    fig.text(.055,.027,'Human VEGFA / ARPE-19 | Seen development tasks | 2026-10-28',fontsize=8,color='#64748B')
    if legend:
        fig.legend(handles=[Patch(facecolor=COLORS[g],label=FULL[g]) for g in GROUPS],loc='upper left',bbox_to_anchor=(.048,.881),ncol=3,frameon=False,fontsize=10)
    if not heatmap:fig.subplots_adjust(left=.075,right=.975,top=.765,bottom=.20,wspace=.30)

def save(fig,name):
    # Detect unexpected fallback at the actual text-object level before export.
    for text in fig.findobj(matplotlib.text.Text):
        if text.get_text():
            path=Path(font_manager.findfont(text.get_fontproperties(),fallback_to_default=False))
            if path.name.lower() not in ('arial.ttf','arialbd.ttf'):raise RuntimeError('Text uses a substitute font: '+str(path))
    for ext in ('svg','pdf','png'):
        metadata={'Creator':'siRNA-GPT corrected evaluation builder'}
        if ext=='pdf':metadata.update(CreationDate=None,ModDate=None,Title=name)
        elif ext=='svg':metadata['Date']=None
        fig.savefig(FIGURES/(name+'.'+ext),dpi=600,metadata=metadata)
    plt.close(fig)

def frac_axes(ax,maxval=1.18):
    ax.set_ylim(0,maxval);ax.set_yticks([0,.25,.5,.75,1]);ax.set_yticklabels(['0%','25%','50%','75%','100%'])
    ax.grid(axis='y',alpha=.18);ax.set_axisbelow(True)

def task_pass(data):
    fig,axes=plt.subplots(1,3,figsize=(12.6,6.8))
    decorate(fig,'Task-level PASS rates by task category','Initial AI task labels and the recorded project adjudication overlay',
        'Task units are paired across configurations; no task was rerun. The single change case cannot establish general performance.\nThe overlay is retrospective project adjudication, not independent blind validation.',False)
    fig.legend(handles=[Patch(facecolor='white',edgecolor='#444444',label='Initial AI task labels'),Patch(facecolor='#555555',label='After project adjudication')],
        loc='upper left',bbox_to_anchor=(.05,.877),ncol=2,frameon=False)
    for i,(cat,ax) in enumerate(zip(CATEGORIES,axes)):
        for x,g in enumerate(GROUPS):
            r=next(r for r in data['summaries'] if r['group']==g and r['category']==cat)
            for shift,key,alpha in [(-.18,'pass_before',.25),(.18,'pass_after',1)]:
                rate=r[key]/r['n_tasks'];ax.bar(x+shift,rate,width=.33,color=COLORS[g],alpha=alpha,edgecolor=COLORS[g])
                ax.text(x+shift,rate+.035,f"{r[key]}/{r['n_tasks']}",ha='center',fontsize=9)
        ax.set_xticks(range(3));ax.set_xticklabels([LABELS[g] for g in GROUPS]);frac_axes(ax)
        ax.set_title(CAT[cat],fontsize=11,pad=15);ax.text(-.12,1.09,chr(97+i),transform=ax.transAxes,fontweight='bold',fontsize=13)
    axes[0].set_ylabel('Task-level PASS rate')
    save(fig,NAMES[0])

def slot_bars(data,overall=False):
    categories=['OVERALL'] if overall else CATEGORIES
    fig,axes=plt.subplots(1,len(categories),figsize=(9.8,6.4) if overall else (12.6,6.8),squeeze=False)
    decorate(fig,'Overall required-slot micro metrics' if overall else 'Required-slot macro metrics by task category',
        'AI-provisional slot labels, unchanged by the task adjudication overlay',
        ('Supplementary pooled description: 9 seen tasks and 135 required slots per configuration.\n' if overall else 'Macro = arithmetic mean of the per-task metric; the change panel has one task per configuration.\n')+
        'CORRECT -> TP; WRONG -> FP and FN; MISSING -> FN. No biological efficacy or strict C1 planning claim.')
    for i,(cat,ax) in enumerate(zip(categories,axes[0])):
        for gi,g in enumerate(GROUPS):
            r=next(r for r in data['summaries'] if r['group']==g and r['category']==cat)
            vals=[r[k if overall else 'macro_'+k] for k in ('precision','recall','f1')]
            xx=np.arange(3)+(gi-1)*.25;ax.bar(xx,vals,width=.23,color=COLORS[g])
            for x,y in zip(xx,vals):ax.text(x,y+.025,f'{y:.3f}' if overall else f'{y:.2f}',ha='center',fontsize=8 if not overall else 9)
        ax.set_xticks(range(3));ax.set_xticklabels(['Precision','Recall','F1']);frac_axes(ax,1.20)
        if not overall:ax.set_title(CAT[cat],fontsize=11,pad=15);ax.text(-.12,1.09,chr(97+i),transform=ax.transAxes,fontweight='bold',fontsize=13)
    axes[0,0].set_ylabel('Required-slot metric')
    save(fig,NAMES[7] if overall else NAMES[1])

def dimensions(data,form,name):
    fig,axes=plt.subplots(1,3,figsize=(13.6,6.8))
    decorate(fig,f'Original dimension scores - sheet {form}',
        f'Score sheet {form} is kept separate; no dimension score was changed by adjudication',
        'Bars show means on the original 0-2 scale; dots show each task rating. No fabricated error bars or significance tests.\nThese are descriptive scores of prepared-input development configurations, not knockdown accuracy or user-experience measurements.')
    for i,(cat,ax) in enumerate(zip(CATEGORIES,axes)):
        for gi,g in enumerate(GROUPS):
            rr=[r for r in data['ratings'][form] if r['group']==g and r['category']==cat]
            xx=np.arange(4)+(gi-1)*.24;vals=[np.mean([r[d] for r in rr]) for d in DIMS]
            ax.bar(xx,vals,width=.225,color=COLORS[g],alpha=.8)
            for x,d in zip(xx,DIMS):
                shifts=np.linspace(-.04,.04,len(rr)) if len(rr)>1 else [0]
                ax.scatter([x+s for s in shifts],[r[d] for r in rr],s=17,c='white',edgecolors='#222222',linewidths=.65,zorder=5,clip_on=False)
        ax.set_ylim(0,2.24);ax.set_yticks([0,.5,1,1.5,2]);ax.set_xticks(range(4));ax.set_xticklabels(['Factual','Evidence','Completion','Boundary'],rotation=24,ha='right',fontsize=8.7)
        ax.set_title(CAT[cat],fontsize=11,pad=15);ax.grid(axis='y',alpha=.18);ax.set_axisbelow(True);ax.text(-.12,1.09,chr(97+i),transform=ax.transAxes,fontweight='bold',fontsize=13)
    axes[0].set_ylabel('Original dimension score (0-2)');save(fig,name)

def matrix(data,form,name):
    order=['W1','W2','W2b','W3','U1','R1','R2','R3','R4']
    rows=sorted(data['ratings'][form],key=lambda r:(order.index(r['case_id']),GROUPS.index(r['group'])))
    values=np.array([[r[d] for d in DIMS] for r in rows]);fig,ax=plt.subplots(figsize=(10,11.6))
    decorate(fig,f'Complete task-by-dimension score matrix - sheet {form}',
        'All 27 original rating records; three configurations of nine seen task templates',
        'Rows are ordered as standard work, requirement change, and reliability; separators mark category boundaries.\nOriginal sheet scores are preserved. Sheet A and C are not pooled or counted as independent replicate experiments.',False,True)
    fig.subplots_adjust(left=.35,right=.86,top=.855,bottom=.18)
    image=ax.pcolormesh(np.arange(5)-.5,np.arange(28)-.5,values,vmin=0,vmax=2,cmap='Greys',shading='flat',rasterized=False)
    ax.set_xlim(-.5,3.5);ax.set_ylim(26.5,-.5)
    ax.set_xticks(range(4));ax.set_xticklabels(['Factual','Evidence','Completion','Boundary'],fontsize=10)
    ax.set_yticks(range(27));ax.set_yticklabels([f"{r['case_id']}  |  {r['answer_id']}  |  {LABELS[r['group']]}" for r in rows],fontsize=9)
    ax.tick_params(length=0);ax.set_xlabel('Evaluation dimension',labelpad=12)
    for i in range(27):
        for j in range(4):ax.text(j,i,str(values[i,j]),ha='center',va='center',color='white' if values[i,j]==2 else 'black',fontsize=9)
    for y in (11.5,14.5):ax.axhline(y,color='#C77B28',linewidth=2)
    colorbar=fig.colorbar(image,ax=ax,shrink=.45,pad=.05,ticks=[0,1,2],label='Score (0-2)')
    colorbar.solids.set_rasterized(False)
    colorbar.solids.set_edgecolor('face')
    save(fig,name)

def changed(data):
    rr=[r for aid in data['changed_answers'] for r in data['per_task'] if r['answer_id']==aid]
    values=np.array([[int(r['original_verdict']=='PASS'),int(r['final_verdict']=='PASS')] for r in rr])
    fig,ax=plt.subplots(figsize=(10.4,6.4))
    decorate(fig,'Four task labels changed by project adjudication','The other 23 task labels are unchanged; all 405 slot labels and both score sheets remain unchanged',
        'A002/A013/A014: FAIL to PASS. A008: PASS to FAIL. This is a versioned retrospective decision overlay.\nThe changed task labels do not make previously wrong/missing slots correct and do not establish unseen-task performance.',False)
    fig.subplots_adjust(left=.32,right=.89,top=.80,bottom=.22)
    ax.pcolormesh(np.arange(3)-.5,np.arange(len(rr)+1)-.5,values,vmin=0,vmax=1,cmap=ListedColormap(['#B65E4D','#278577']),shading='flat',rasterized=False)
    ax.set_xlim(-.5,1.5);ax.set_ylim(len(rr)-.5,-.5)
    ax.set_xticks([0,1]);ax.set_xticklabels(['Initial AI task label','Project-adjudicated label'])
    ax.set_yticks(range(len(rr)));ax.set_yticklabels([f"{r['answer_id']} | {r['case_id']} | {LABELS[r['group']]}" for r in rr]);ax.tick_params(length=0)
    for i,r in enumerate(rr):
        for j,key in enumerate(('original_verdict','final_verdict')):ax.text(j,i,r[key],ha='center',va='center',color='white',fontweight='bold',fontsize=13)
    save(fig,NAMES[6])

def combine():
    PDF_OUT.mkdir(parents=True,exist_ok=True);writer=PdfWriter()
    for name in NAMES:
        p=FIGURES/(name+'.pdf')
        if len(PdfReader(p).pages)!=1:raise ValueError('Expected one vector page: '+str(p))
        writer.append(p)
    writer.add_metadata({'/Title':'siRNA-GPT corrected adjudication figures - 2026-10-28','/Author':'siRNA-GPT project','/Subject':'Retrospective development analysis; original ratings and slot labels preserved'})
    with COMBINED.open('wb') as f:writer.write(f)
    assert len(PdfReader(COMBINED).pages)==8

def main():
    p=argparse.ArgumentParser();p.add_argument('--pdf-only',action='store_true');args=p.parse_args()
    if args.pdf_only:combine();return
    FIGURES.mkdir(parents=True,exist_ok=True);PDF_OUT.mkdir(parents=True,exist_ok=True)
    fonts=set_fonts();data=load_data();write_analysis(data)
    task_pass(data);slot_bars(data);dimensions(data,'A',NAMES[2]);dimensions(data,'C',NAMES[3]);matrix(data,'A',NAMES[4]);matrix(data,'C',NAMES[5]);changed(data);slot_bars(data,True);combine()
    (HERE/'font_and_environment.json').write_text(json.dumps(dict(fonts=fonts,matplotlib=matplotlib.__version__,numpy=np.__version__,python=sys.version,
        pdf_fonttype=42,svg_fonttype='none',substitution_allowed=False,png_dpi=600,figure_order=NAMES),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(figures=len(NAMES),standalone_pdfs=len(NAMES),combined_pages=8,actual_Arial=True,combined_pdf=str(COMBINED)),ensure_ascii=True))

if __name__=='__main__':main()
