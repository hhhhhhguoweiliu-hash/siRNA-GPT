"""Publication figures from one confirmed expert and the user-corrected Q9."""
import argparse
import csv
import hashlib
import json
import subprocess
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Polygon
import numpy as np
from pypdf import PdfReader,PdfWriter
from PIL import Image

GROUPS=['llm','workflow','agent']
LABELS={'llm':'LLM','workflow':'Workflow','agent':'Agent'}
COLORS={'llm':'#8197B7','workflow':'#D7A66B','agent':'#A44859'}
MARKERS={'llm':'o','workflow':'s','agent':'D'}
DIMS=['factual_accuracy','evidence_support','requirement_completion','boundary_handling']
DIM_LABELS=['Factual\naccuracy','Evidence\nsupport','Requirement\ncompletion','Boundary\nhandling']
CATS=[('standard','Standard tasks',4),('requirement_change','Requirement change',1),('reliability','Reliability tasks',4)]
NAMES=['Q1','Q2','Q3','Q4','Q5','Q6','Q7','Q8','Q9']
CAPTIONS={
 'Fig1_rating_summary':'Agent received higher overall ratings, mainly in evidence support and requirement completion.',
 'Fig2_rating_radar':'LLM scored slightly higher on factual accuracy. Agent and LLM tied on boundary handling.',
 'Fig3_task_totals':'Agent exceeded LLM on all nine tasks and tied Workflow on Q4 and Q9.',
 'Fig4_task_categories':'The largest mean gap from Workflow occurred in reliability tasks: 7.75 versus 4.50 points.',
 'Fig5_dimension_matrix':'All 108 dimension ratings are shown. Q9 Workflow and Agent entries are both 2/2/2/2.',
 'Fig6_paired_differences':'Q6 and Q7 contribute 11 of the 19 cumulative Agent-Workflow rating points.'}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--font',type=Path,required=True)
    p.add_argument('--output',type=Path,default=Path('research/2026-10-28_authoritative_expert_figures'))
    p.add_argument('--source',type=Path,default=Path('research/2026-10-28_authoritative_expert_analysis'))
    args=p.parse_args();out=args.output;figdir=out/'figures';figdir.mkdir(parents=True,exist_ok=True)
    font_manager.fontManager.addfont(str(args.font))
    resolved=font_manager.findfont(font_manager.FontProperties(family='Arial',weight='bold'),fallback_to_default=False)
    assert Path(resolved).resolve()==args.font.resolve(),resolved
    plt.rcParams.update({'font.family':'Arial','font.weight':'bold','font.size':11,
        'axes.labelweight':'bold','axes.titleweight':'bold','axes.titlesize':13,
        'axes.labelsize':12,'xtick.labelsize':10.5,'ytick.labelsize':10.5,
        'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none',
        'axes.unicode_minus':False,'savefig.facecolor':'white','figure.facecolor':'white'})
    with (args.source/'scores_by_actual_group.csv').open(encoding='utf-8-sig',newline='') as f:
        rows=list(csv.DictReader(f))
    for r in rows:
        for k in ['question_number','total']+DIMS:r[k]=int(r[k])
    assert len(rows)==27 and all(0<=r[k]<=2 for r in rows for k in DIMS)
    by={g:sorted([r for r in rows if r['group']==g],key=lambda x:x['question_number']) for g in GROUPS}
    assert [r['total'] for r in by['agent']]==[8,8,8,7,8,7,8,8,8]
    assert [r['total'] for r in by['workflow']]==[7,6,7,7,6,2,2,6,8]
    assert sum(r['total'] for r in by['llm'])==52
    analysis=json.loads((args.source/'analysis.json').read_text())
    means={g:np.array([np.mean([r[k] for r in by[g]]) for k in DIMS]) for g in GROUPS}
    for g in GROUPS:
        old=next(x for x in analysis['summary'] if x['category']=='all' and x['group']==g)
        assert np.allclose(means[g],[old[k] for k in DIMS],rtol=0,atol=1e-12)
    data=[];saved=[];figures=[]

    def base(title,key):
        fig=plt.figure(figsize=(12,7.2))
        fig.suptitle(title,x=.075,y=.975,ha='left',fontsize=17,fontweight='bold',color='#242A35')
        fig.text(.075,.928,'One expert. Nine seen development tasks per group. Q9 recording correction applied.',fontsize=10,color='#626B79')
        fig.text(.075,.047,CAPTIONS[key],fontsize=10,color='#414A58')
        fig.text(.075,.018,'Ratings describe the delivered evidence and response. These are not classification Accuracy, Precision, Recall or F1.',fontsize=8.5,color='#626B79')
        return fig

    def axes_style(ax,maxval,label=True):
        ax.spines[['top','right']].set_visible(False)
        for s in ['left','bottom']:ax.spines[s].set_color('#505864');ax.spines[s].set_linewidth(.9)
        ax.set_axisbelow(True);ax.grid(axis='y',color='#E5E8ED',linewidth=.7)
        ax.set_ylim(0,maxval+.65 if maxval==8 else 2.3)
        ax.set_yticks([0,2,4,6,8] if maxval==8 else [0,.5,1,1.5,2])
        ax.tick_params(length=3,color='#505864')
        ax.yaxis.set_label_position('left');ax.yaxis.tick_left()
        if label:ax.set_ylabel('Total rating (0-8)' if maxval==8 else 'Dimension rating (0-2)',labelpad=10)

    def point_bar(ax,x,values,g,width=.62,label=False):
        mean=float(np.mean(values))
        ax.bar(x,mean,width=width,color=COLORS[g],alpha=.88,zorder=2)
        jitter=np.linspace(-width*.29,width*.29,len(values))
        ax.scatter(x+jitter,values,s=22,marker=MARKERS[g],facecolor=COLORS[g],edgecolor='#FFFFFF',linewidth=.6,zorder=4)
        if label:ax.text(x,max(mean-.5,.25),f'{mean:.2f}',ha='center',va='center',color='white',fontsize=12,zorder=5)
        return mean

    def legend(fig,y=.875):
        handles=[plt.Line2D([],[],color=COLORS[g],marker=MARKERS[g],linewidth=2,label=LABELS[g]) for g in GROUPS]
        fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.52,y),ncol=3,frameon=False,fontsize=11,columnspacing=2)

    def export(fig,key):
        for ax in fig.axes:
            for t in ax.get_xticklabels()+ax.get_yticklabels():t.set_fontweight('bold')
        fig.canvas.draw()
        for suffix in ['pdf','svg','png']:
            target=figdir/(key+'.'+suffix)
            fig.savefig(target,dpi=600 if suffix=='png' else None)
            saved.append(target)
        try:
            with Image.open(figdir/(key+'.png')) as check:check.load()
        except OSError:
            subprocess.run(['pdftoppm','-r','600','-singlefile','-png',str(figdir/(key+'.pdf')),str(figdir/key)],check=True)
            with Image.open(figdir/(key+'.png')) as check:check.load()
        figures.append({'key':key,'caption':CAPTIONS[key]})
        plt.close(fig)

    key='Fig1_rating_summary';fig=base('Expert ratings: overall score and four dimensions',key)
    gs=fig.add_gridspec(1,2,left=.08,right=.98,bottom=.20,top=.80,width_ratios=[1,1.85],wspace=.30)
    ax=fig.add_subplot(gs[0]);axes_style(ax,8)
    for i,g in enumerate(GROUPS):
        m=point_bar(ax,i,np.array([r['total'] for r in by[g]]),g,label=True)
        data.append({'figure':key,'scope':'all','group':g,'metric':'total','mean':m,'n_tasks':9})
    ax.set_xticks(range(3),[LABELS[g] for g in GROUPS]);ax.set_title('a  Overall rating',loc='left',pad=12)
    ax=fig.add_subplot(gs[1]);axes_style(ax,2);ax.set_title('b  Dimension ratings',loc='left',pad=12)
    for gi,g in enumerate(GROUPS):
        for di,k in enumerate(DIMS):
            point_bar(ax,di+(gi-1)*.24,np.array([r[k] for r in by[g]]),g,width=.21)
            data.append({'figure':key,'scope':'all','group':g,'metric':k,'mean':float(means[g][di]),'n_tasks':9})
    ax.set_xticks(range(4),DIM_LABELS);legend(fig);export(fig,key)

    key='Fig2_rating_radar';fig=base('Four dimensions of expert-rated responses',key)
    ax=fig.add_axes([.13,.15,.74,.65]);ax.set_aspect('equal');ax.axis('off')
    vectors=np.array([[0,1],[1,0],[0,-1],[-1,0]])
    for r in [.5,1,1.5,2]:
        poly=vectors*r;ax.add_patch(Polygon(poly,closed=True,fill=False,edgecolor='#DDE2E9',linewidth=.8))
        ax.text(.09,r+.015,f'{r:g}',fontsize=8,color='#7A8391')
    for v in vectors:ax.plot([0,2*v[0]],[0,2*v[1]],color='#DDE2E9',linewidth=.8)
    for g in GROUPS:
        coords=vectors*means[g][:,None];closed=np.vstack([coords,coords[0]])
        ax.fill(closed[:,0],closed[:,1],color=COLORS[g],alpha=.08)
        ax.plot(closed[:,0],closed[:,1],color=COLORS[g],marker=MARKERS[g],linewidth=2.2,markersize=6,label=LABELS[g])
        for i,k in enumerate(DIMS):data.append({'figure':key,'scope':'all','group':g,'metric':k,'mean':float(means[g][i]),'n_tasks':9})
    for (x,y),label in zip([[0,2.5],[3.05,0],[0,-2.5],[-3.05,0]],['Factual\naccuracy','Evidence\nsupport','Requirement\ncompletion','Boundary\nhandling']):
        ax.text(x,y,label,ha='center',va='center',fontsize=13)
    ax.set_xlim(-3.9,3.9);ax.set_ylim(-2.85,2.85);legend(fig);export(fig,key)

    key='Fig3_task_totals';fig=base('Total rating for every task',key)
    ax=fig.add_axes([.08,.20,.89,.59]);axes_style(ax,8)
    x=np.arange(9)
    for gi,g in enumerate(GROUPS):
        values=[r['total'] for r in by[g]]
        bars=ax.bar(x+(gi-1)*.25,values,width=.22,color=COLORS[g],label=LABELS[g])
        for bar,value in zip(bars,values):ax.text(bar.get_x()+bar.get_width()/2,value+.08,str(value),ha='center',va='bottom',fontsize=10)
    ax.set_xticks(x,NAMES);ax.set_xlabel('Task',labelpad=9)
    for xx in [3.5,4.5]:ax.axvline(xx,color='#C7CDD6',linewidth=.9,linestyle='--')
    for xx,label in [(1.5,'Standard tasks'),(4,'Requirement\nchange'),(6.5,'Reliability tasks')]:ax.text(xx,8.72,label,ha='center',va='bottom',fontsize=10,color='#505A69')
    ax.set_ylim(0,9.35);legend(fig,.905);export(fig,key)

    key='Fig4_task_categories';fig=base('Ratings by task category',key)
    gs=fig.add_gridspec(1,3,left=.08,right=.98,bottom=.20,top=.80,wspace=.28)
    for ci,(cat,title,n) in enumerate(CATS):
        ax=fig.add_subplot(gs[ci]);axes_style(ax,8,label=ci==0)
        ax.set_title(f'{chr(97+ci)}  {title}\n{n} task'+('s' if n!=1 else '')+' per group',loc='left',pad=12,fontsize=12)
        for gi,g in enumerate(GROUPS):
            vals=np.array([r['total'] for r in by[g] if r['category']==cat]);assert len(vals)==n
            m=point_bar(ax,gi,vals,g,label=True)
            data.append({'figure':key,'scope':cat,'group':g,'metric':'total','mean':m,'n_tasks':n})
        ax.set_xticks(range(3),[LABELS[g] for g in GROUPS]);ax.tick_params(axis='x',labelsize=10)
    export(fig,key)

    key='Fig5_dimension_matrix';fig=base('All task-level dimension ratings',key)
    gs=fig.add_gridspec(1,3,left=.08,right=.98,bottom=.25,top=.82,wspace=.18)
    cm=LinearSegmentedColormap.from_list('rating',['#F6F7FA','#E8C7CC','#9E4254'])
    for gi,g in enumerate(GROUPS):
        ax=fig.add_subplot(gs[gi]);values=np.array([[r[k] for k in DIMS] for r in by[g]])
        im=ax.imshow(values,cmap=cm,vmin=0,vmax=2,aspect='auto')
        for (i,j),value in np.ndenumerate(values):ax.text(j,i,str(value),ha='center',va='center',color='white' if value==2 else '#333E4C',fontsize=12)
        ax.set_title(LABELS[g],color=COLORS[g],fontsize=14,pad=12)
        ax.set_xticks(range(4),['Factual\naccuracy','Evidence\nsupport','Requirement\ncompletion','Boundary\nhandling'],fontsize=9)
        ax.set_yticks(range(9),NAMES if gi==0 else ['']*9)
        if gi==0:ax.set_ylabel('Task',labelpad=12)
        ax.tick_params(length=0,pad=7)
        ax.set_xticks(np.arange(-.5,4,1),minor=True);ax.set_yticks(np.arange(-.5,9,1),minor=True)
        ax.grid(which='minor',color='white',linewidth=2);ax.tick_params(which='minor',length=0)
        for spine in ax.spines.values():spine.set_visible(False)
    cax=fig.add_axes([.40,.125,.25,.018]);cb=fig.colorbar(im,cax=cax,orientation='horizontal',ticks=[0,1,2])
    cb.set_label('Dimension rating (0-2)',labelpad=4,fontsize=10);cb.ax.tick_params(labelsize=9,length=2);cb.outline.set_visible(False)
    export(fig,key)

    key='Fig6_paired_differences';fig=base('Within-task differences in total rating',key)
    gs=fig.add_gridspec(1,2,left=.10,right=.97,bottom=.20,top=.80,wspace=.23)
    for j,g in enumerate(['llm','workflow']):
        ax=fig.add_subplot(gs[j]);diff=np.array([a['total']-b['total'] for a,b in zip(by['agent'],by[g])])
        yy=np.arange(9);ax.barh(yy,diff,height=.56,color=COLORS[g],alpha=.9)
        ax.scatter(diff,yy,marker=MARKERS[g],color=COLORS[g],edgecolor='white',linewidth=.8,s=40,zorder=4)
        for y,v in zip(yy,diff):ax.text(v+.14,y,f'+{v}' if v else '0',va='center',fontsize=11)
        ax.set_yticks(yy,NAMES);ax.invert_yaxis();ax.set_xlim(-.35,6.75);ax.set_xticks(range(7))
        ax.axvline(0,color='#626C79',linewidth=.9);ax.grid(axis='x',color='#E5E8ED',linewidth=.7);ax.set_axisbelow(True)
        ax.spines[['top','right','left']].set_visible(False);ax.spines['bottom'].set_color('#505864')
        ax.set_xlabel('Difference in total rating (points)',labelpad=10)
        if j==0:ax.set_ylabel('Task',labelpad=10)
        ax.set_title('Agent - '+LABELS[g],loc='left',pad=13)
        for r,v in zip(by['agent'],diff):data.append({'figure':key,'scope':r['case_id'],'group':'agent_minus_'+g,'metric':'total_difference','mean':int(v),'n_tasks':1})
    export(fig,key)

    # Data are actual scores/means, never synthetic run replicates.
    with (out/'plot_data.csv').open('w',encoding='utf-8-sig',newline='') as f:
        wr=csv.DictWriter(f,fieldnames=['figure','scope','group','metric','mean','n_tasks']);wr.writeheader();wr.writerows(data)
    (out/'figure_manifest.json').write_text(json.dumps({'source_commit':'c68baaf2a47b91c9713fc1c046f2bbfa45b217c8',
        'source_score_csv_sha256':hashlib.sha256((args.source/'scores_by_actual_group.csv').read_bytes()).hexdigest(),
        'source_corrected_workbook_sha256':analysis['source_sha256'],'figures':figures,'n_experts':1,'n_seen_cases_per_group':9,
        'q9_workflow_total':8,'q9_agent_total':8,'new_model_calls':0,'new_ratings':0,'classification_metrics_created':False},ensure_ascii=False,indent=2)+'\n')
    writer=PdfWriter()
    font_checks=[]
    for item in figures:
        pdf=figdir/(item['key']+'.pdf');reader=PdfReader(pdf)
        names=[]
        for page in reader.pages:
            writer.add_page(page)
            for ref in page['/Resources']['/Font'].values():
                font=ref.get_object();name=str(font.get('/BaseFont'));names.append(name)
                actual=font['/DescendantFonts'][0].get_object() if '/DescendantFonts' in font else font
                desc=actual.get('/FontDescriptor');desc=desc.get_object() if desc else None
                assert 'Arial-BoldMT' in name and desc and '/FontFile2' in desc,(pdf,name)
        font_checks.append({'figure':item['key'],'embedded_fonts':sorted(set(names))})
    combined=out/'siRNA_GPT_authoritative_expert_figures.pdf'
    with combined.open('wb') as f:writer.write(f)
    assert len(PdfReader(combined).pages)==6
    (out/'figure_checks.json').write_text(json.dumps({'source_means_verified':True,'all_108_dimension_scores_preserved':True,
        'q9_correction_applied':True,'png_dpi':600,'pdf_pages':6,'font_family':'Arial','font_weight':'Bold',
        'font_file':args.font.name,'pdf_fonts_verified':font_checks,'svg_editable_text':True,'fake_error_bars':False,
        'new_human_scores':0,'new_model_calls':0},indent=2)+'\n')
    print(json.dumps({'figures':len(figures),'formats':['PNG 600 dpi','PDF vector','SVG editable text'],
                      'combined_pdf':str(combined),'font_checks':'all embedded Arial Bold','source_scores':'user-corrected Q9; all 27 answers'}))


if __name__=='__main__':main()
