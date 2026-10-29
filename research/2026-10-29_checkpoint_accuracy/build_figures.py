"""Render exact computed data with verified Arial Bold and paper-derived colors."""
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
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent
GROUPS=['llm','workflow','agent']
LABELS={'llm':'Generic LLM','workflow':'Fixed workflow','agent':'Agent'}
COLORS={'llm':'#AB88B3','workflow':'#99C4CE','agent':'#90D9CA'}
INK='#17191C';EDGE='#303338';GRID='#E8EAED'
def read(name):
    with (HERE/'data'/name).open(encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def main(font):
    font=font.resolve();tt=TTFont(font)
    names=lambda n:{x.toUnicode() for x in tt['name'].names if x.nameID==n}
    assert 'Arial' in names(1) and any('Bold' in x for x in names(2))
    assert all(c in tt.getBestCmap() for c in range(32,127))
    font_manager.fontManager.addfont(str(font))
    prop=font_manager.FontProperties(family='Arial',weight='bold',fname=str(font))
    plt.rcParams.update({'font.family':'Arial','font.weight':'bold','axes.labelweight':'bold',
        'axes.titleweight':'bold','font.size':12,'text.color':INK,'axes.labelcolor':INK,
        'axes.edgecolor':EDGE,'xtick.color':INK,'ytick.color':INK,'axes.linewidth':1,
        'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none',
        'figure.facecolor':'white','savefig.facecolor':'white','legend.frameon':False})
    micro={r['group']:r for r in read('metrics_micro.csv')}
    macro={r['group']:r for r in read('metrics_macro.csv')}
    assert all(int(r['n'])==135 and int(r['n_negative'])==27 for r in micro.values())
    (HERE/'figures').mkdir(exist_ok=True);exports=[];plot_data=[]
    def save(fig,stem):
        for t in fig.findobj(match=mpltext.Text):
            size=t.get_fontsize();t.set_fontproperties(prop);t.set_fontsize(size)
        fig.canvas.draw();renderer=fig.canvas.get_renderer();fw,fh=fig.canvas.get_width_height()
        for t in fig.findobj(match=mpltext.Text):
            if not t.get_visible() or not t.get_text():continue
            bb=t.get_window_extent(renderer)
            assert bb.x0>=-1 and bb.y0>=-1 and bb.x1<=fw+1 and bb.y1<=fh+1,(stem,t.get_text(),bb.bounds)
            assert Path(font_manager.findfont(t.get_fontproperties(),fallback_to_default=False)).resolve()==font
            assert t.get_fontproperties().get_family()==['Arial'] and t.get_fontproperties().get_weight()=='bold'
        target=HERE/'figures'/stem;fig.savefig(str(target)+'.png',dpi=600);fig.savefig(str(target)+'.svg')
        svg=Path(str(target)+'.svg').read_text();assert '<image' not in svg and '<text' in svg and 'DejaVu' not in svg
        styles=[e.attrib.get('style','') for e in ET.fromstring(svg).iter() if e.tag.endswith('}text')]
        assert styles and all('Arial' in s and re.search(r'font-weight:\s*(700|bold)|font:\s*700',s) for s in styles)
        im=Image.open(str(target)+'.png');exports.append({'stem':stem,'size_inches':list(fig.get_size_inches()),
            'png_pixels':im.size,'png_dpi':im.info.get('dpi'),'font':'Arial Bold',
            'text_inside_canvas':True,'editable_svg_text':True,'raster_layers_in_svg':0})
        im.verify();plt.close(fig)
    def metric_plot(data,stem,title,aggregation):
        fig,ax=plt.subplots(figsize=(10.2,5.6));fig.subplots_adjust(left=.10,right=.985,bottom=.21,top=.75)
        xs=np.arange(4);width=.225;metrics=['accuracy','precision','recall','f1']
        for i,g in enumerate(GROUPS):
            vals=[float(data[g][m]) for m in metrics]
            bars=ax.bar(xs+(i-1)*width,vals,width,color=COLORS[g],edgecolor=EDGE,lw=.8,zorder=3,label=LABELS[g])
            for m,b,v in zip(metrics,bars,vals):
                ax.text(b.get_x()+b.get_width()/2,v+.025,f'{100*v:.1f}',ha='center',va='bottom',fontsize=11)
                plot_data.append({'figure':stem,'group':g,'metric':m,'aggregation':aggregation,'value':v})
        ax.set_xticks(xs,['Accuracy','Precision','Recall','F1']);ax.tick_params(labelsize=13,pad=6)
        ax.set_ylim(0,1.12);ax.set_yticks(np.linspace(0,1,6),[str(x) for x in range(0,101,20)])
        ax.set_ylabel('Score (%)',fontsize=15,labelpad=10);ax.grid(axis='y',color=GRID,lw=.7);ax.set_axisbelow(True)
        fig.text(.10,.955,title,fontsize=18,ha='left',va='top')
        fig.legend(handles=[Patch(facecolor=COLORS[g],edgecolor=EDGE,label=LABELS[g]) for g in GROUPS],
            loc='upper center',bbox_to_anchor=(.55,.89),ncol=3,fontsize=13,handlelength=1.4,columnspacing=1.8)
        fig.text(.10,.09,'All checkpoints retained; missing or incomplete answers are not counted as correct.',fontsize=11)
        save(fig,stem)
    metric_plot(micro,'Fig1_accuracy_precision_recall_f1_micro','Checkpoint accuracy and decision metrics','micro')
    metric_plot(macro,'FigS1_accuracy_precision_recall_f1_macro','Task-averaged checkpoint metrics','macro_9_tasks')
    fig,(ax1,ax2)=plt.subplots(1,2,figsize=(11.2,5.5),gridspec_kw={'width_ratios':[1.45,1]})
    fig.subplots_adjust(left=.12,right=.97,bottom=.20,top=.76,wspace=.42)
    ys=np.arange(3)
    states=[('Correct','#90D9CA'),('Explicit error','#AB88B3'),('Missing / incomplete','#E5E8EC')]
    starts=np.zeros(3)
    counts=[]
    for state,color in states:
        nums=[int(micro[g]['TP'])+int(micro[g]['TN']) if state=='Correct' else
            int(micro[g]['FP'])+int(micro[g]['FN_explicit']) if state=='Explicit error' else
            int(micro[g]['abstain_positive'])+int(micro[g]['abstain_negative']) for g in GROUPS]
        ax1.barh(ys,nums,left=starts,height=.56,color=color,edgecolor=EDGE,lw=.7)
        for y,n,l in zip(ys,nums,starts):
            if n>=9:ax1.text(l+n/2,y,str(n),ha='center',va='center',fontsize=12)
        starts+=nums
    ax1.set_yticks(ys,[LABELS[g] for g in GROUPS],fontsize=12);ax1.invert_yaxis()
    ax1.set_xlim(0,139);ax1.set_xticks([0,45,90,135]);ax1.set_xlabel('Checkpoints',fontsize=14,labelpad=9)
    ax1.set_title('All outcomes',loc='left',fontsize=15,pad=16)
    for y,g in enumerate(GROUPS):
        tp=int(micro[g]['TP']);tn=int(micro[g]['TN'])
        ax2.barh(y,tp,color='#99C4CE',height=.56,edgecolor=EDGE,lw=.7)
        ax2.barh(y,tn,left=tp,color='#90D9CA',height=.56,edgecolor=EDGE,lw=.7)
        ax2.text(tp+tn+2,y,f'TN = {tn}',ha='left',va='center',fontsize=11)
    ax2.set_yticks(ys,['LLM','Workflow','Agent'],fontsize=12);ax2.invert_yaxis()
    ax2.set_xlim(0,175);ax2.set_xticks([0,45,90,135]);ax2.set_xlabel('Correct checkpoints',fontsize=14,labelpad=9)
    ax2.set_title('True positives and negatives',loc='left',fontsize=15,pad=16)
    for ax,letter in [(ax1,'a'),(ax2,'b')]:ax.text(-.18,1.12,letter,transform=ax.transAxes,fontsize=20,ha='left',va='top')
    fig.text(.12,.96,'Correct judgments, errors and missing output',fontsize=18,ha='left',va='top')
    fig.legend(handles=[Patch(facecolor=c,edgecolor=EDGE,label=s) for s,c in states],
        loc='upper left',bbox_to_anchor=(.115,.885),ncol=3,fontsize=11,handlelength=1.2,columnspacing=1.3)
    fig.legend(handles=[Patch(facecolor='#99C4CE',edgecolor=EDGE,label='TP'),Patch(facecolor='#90D9CA',edgecolor=EDGE,label='TN')],
        loc='upper left',bbox_to_anchor=(.70,.885),ncol=2,fontsize=11,handlelength=1.2,columnspacing=1.3)
    fig.text(.12,.075,'135 existing checkpoints per system; no missing item is credited as TN.',fontsize=11)
    save(fig,'Fig2_outcomes_and_true_negatives')
    fig,axs=plt.subplots(1,3,figsize=(11.4,4.8));fig.subplots_adjust(left=.12,right=.98,bottom=.24,top=.73,wspace=.28)
    for i,(ax,g) in enumerate(zip(axs,GROUPS)):
        r=micro[g];m=np.array([[int(r['TP']),int(r['FN_explicit']),int(r['abstain_positive'])],
            [int(r['FP']),int(r['TN']),int(r['abstain_negative'])]])
        for y in range(2):
            for x in range(3):
                good=(x==y);color=COLORS[g] if good else '#F1F2F4' if x==2 else '#F2E9F2'
                ax.add_patch(plt.Rectangle((x-.5,y-.5),1,1,facecolor=color,edgecolor='white',lw=3))
                ax.text(x,y,str(m[y,x]),ha='center',va='center',fontsize=18)
        ax.set_xlim(-.5,2.5);ax.set_ylim(1.5,-.5);ax.set_aspect('equal')
        ax.set_xticks(range(3),['Support','Reject','Missing'],fontsize=11)
        ax.set_yticks([0,1],['Positive','Negative'] if i==0 else ['', ''],fontsize=12)
        ax.tick_params(length=0,pad=8)
        for spine in ax.spines.values():spine.set_visible(False)
        ax.set_title(LABELS[g],loc='left',fontsize=15,pad=16)
        ax.text(-.15,1.20,chr(97+i),transform=ax.transAxes,fontsize=20,ha='left',va='top')
        ax.set_xlabel('System response',fontsize=12,labelpad=11)
    axs[0].set_ylabel('Gold label',fontsize=14,labelpad=12)
    fig.text(.12,.96,'Confusion tables with missing output retained',fontsize=18,ha='left',va='top')
    fig.text(.12,.10,'Gold labels: 108 positive, 27 negative. Missing / incomplete is a separate outcome.',fontsize=11)
    save(fig,'Fig3_confusion_tables_with_abstentions')
    with (HERE/'data/figure_plot_data.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(plot_data[0]));w.writeheader();w.writerows(plot_data)
    checks={'font_file_sha256':hashlib.sha256(font.read_bytes()).hexdigest(),'font_family':'Arial','font_weight':'Bold',
        'fallback_allowed':False,'palette':COLORS,'dpi':600,'pdf_outputs':0,'figures':exports,
        'data_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (HERE/'data').glob('*')}}
    (HERE/'font_and_export_checks.json').write_text(json.dumps(checks,indent=2)+'\n')
    print(json.dumps({'figures':len(exports),'font_and_canvas_checks':'passed','exports':exports}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--font',type=Path,required=True);main(p.parse_args().font)
