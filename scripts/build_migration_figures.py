"""Compose manuscript figures from immutable real evidence. No API, new scoring or inference.

Usage: python scripts/build_migration_figures.py --output research/<new>/paper
Optional plot dependencies: requirements-research.txt (PYTHONPATH=.plot_deps).
"""
import argparse, csv, datetime as dt, gzip, hashlib, html, json, shutil, subprocess
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Patch

ROOT=Path(__file__).resolve().parents[1]
SCI=ROOT/'research/2026-10-19_scientific/data'
BATCH=ROOT/'research/2026-10-20_takeover'
N,H,LIVE,IMP,GRAY='#427D9D','#D7784C','#338B77','#A97538','#77818D'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,
    'axes.spines.right':False,'pdf.fonttype':42,'svg.fonttype':'none'})

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path): return json.loads(path.read_text(encoding='utf-8-sig'))
def tsv(path): return pd.read_csv(path,sep='\t')
def write(path,value): path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);args=p.parse_args()
    out=Path(args.output)
    if out.exists() and any(out.iterdir()):raise SystemExit('Use a new empty output directory')
    (out/'figures').mkdir(parents=True);(out/'data').mkdir()
    sources=[]
    def source(path):
        sources.append({'path':path.relative_to(ROOT).as_posix(),'bytes':path.stat().st_size,'sha256':sha(path)})
        return path
    def copy(path,name=None):
        source(path);shutil.copy2(path,out/'data'/(name or path.name))
    def save(fig,name):
        for ext in ('png','svg','pdf'):
            fig.savefig(out/'figures'/f'{name}.{ext}',dpi=300,bbox_inches='tight',facecolor='white')
        plt.close(fig)
    def panel(ax,label,title):ax.set_title(title,loc='left',pad=14);ax.text(-.12,1.08,label,transform=ax.transAxes,weight='bold',fontsize=15)
    def box(ax,x,y,w,h,text,color='#EAF1F5'):
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.04',facecolor=color,edgecolor='#B0BBC4'))
        ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=10)
    def arrow(ax,a,b):ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=14,color='#637480'))

    # Only the archived publisher text is interpreted; no original figure is copied.
    source(ROOT/'references/CRISPR-GPT/paper_extracted_text.txt')
    source(ROOT/'docs/reviews/20261020_1435_initial_review.md')
    for name in ['candidate_evidence.tsv','seed_expression_state_comparison.tsv',
                 'VEGFA_eight_samples_TPM.tsv','TPM_detection_threshold_sensitivity.tsv']:
        copy(SCI/name)
    for name in ['records.tsv','paired_availability.tsv','evidence_audit.json','failure_diagnostics.tsv']:
        copy(BATCH/'three_arm'/name)
    auto=read(source(BATCH/'auto_case/conversation.json'))
    summary=read(source(BATCH/'auto_case/summary.json'))
    source(BATCH/'auto_case/tools.zip');source(BATCH/'three_arm_original.zip')
    candidates=tsv(SCI/'candidate_evidence.tsv')
    expression=tsv(SCI/'seed_expression_state_comparison.tsv')
    baseline=tsv(SCI/'VEGFA_eight_samples_TPM.tsv')
    records=tsv(BATCH/'three_arm/records.tsv')
    pairs=tsv(BATCH/'three_arm/paired_availability.tsv')
    with gzip.open(source(BATCH/'three_arm/results.json.gz'),'rt',encoding='utf-8') as f:raw=json.load(f)
    assert len(records)==len(raw)==54 and records.answer_id.nunique()==54
    assert len(records[['case_id','group','repeat']].drop_duplicates())==54
    assert summary['selected_for_review']==['VEGFA_SD_3499','VEGFA_SD_3500']
    # F1: original architecture for this implementation, explicitly distinct from the paper.
    fig,axes=plt.subplots(2,1,figsize=(12,9),gridspec_kw={'height_ratios':[2.1,1]})
    ax=axes[0];ax.set(xlim=(0,12),ylim=(0,6));ax.axis('off');panel(ax,'a','Adapted workflow: human VEGFA / ARPE-19')
    for x,y,w,h,text,col in [
        (.1,4.4,3.2,1.1,'Researcher input\nTask + guide direction + state\nLiterature sequence still needed','#EAF1F5'),
        (4.1,4.4,3.4,1.1,'One API, multiple controller stages\nClarify → plan → human confirmation\nDependencies + bounded state machine','#EAF1F5'),
        (8.3,4.4,3.4,1.1,'Run / pause / retry / export\nEvidence + source fingerprints\nHuman scientific judgement','#EAF1F5'),
        (.1,2.2,3.2,1.2,'Live sequence checks\n19 nt core / strand\n20 packaged transcripts','#DCEEE8'),
        (4.1,2.2,3.4,1.2,'Verified historical results\nOligoFormer + SeedMatchR\nNo fresh heavy inference','#F4E8D8'),
        (8.3,2.2,3.4,1.2,'Live data join\n4 normoxic + 4 hypoxic dishes\nAnnotation; ranking unchanged','#DCEEE8'),
        (2.0,.2,8,1,'Candidate evidence table + real tool records + limits\nIndependent evaluation / real wet-lab validation remain separate','#EAF1F5')]:box(ax,x,y,w,h,text,col)
    for a,b in [((3.35,4.95),(4.0,4.95)),((7.55,4.95),(8.2,4.95)),((1.7,4.3),(1.7,3.5)),
                ((5.8,4.3),(5.8,3.5)),((10,4.3),(10,3.5)),((1.7,2.1),(3.0,1.3)),
                ((5.8,2.1),(5.8,1.3)),((10,2.1),(9,1.3))]:arrow(ax,a,b)
    ax=axes[1];ax.axis('off');panel(ax,'b','Migration scope from CRISPR-GPT')
    rows=[['Meta / Auto / Q&A','Implemented','Single API + controlled tools'],
          ['Planning / tool evidence','Real Auto archived','Six tools; mixed live checks and imports'],
          ['Benchmark / expert review','Development only','6 tasks × 3 arms × 3 technical repeats'],
          ['Fine-tuning / wet lab','Not performed here','No equivalence to the full source system']]
    table=ax.table(cellText=rows,colLabels=['Source-paper concept','This project','Evidence boundary'],loc='center',cellLoc='left',colWidths=[.28,.23,.49])
    table.auto_set_font_size(False);table.set_fontsize(10);table.scale(1,2.1)
    for (r,c),cell in table.get_celld().items():cell.set_edgecolor('#D4DCE2');cell.set_facecolor('#EAF1F5' if r==0 else 'white')
    fig.subplots_adjust(hspace=.28);save(fig,'Figure1_system_migration')

    # F2: timing is measured from executor start, not unrecorded planning latency.
    events=auto['events'];start=dt.datetime.fromisoformat(next(e['time'] for e in events if e['kind']=='model_started'))
    timeline=[];active={};model_index=0
    for e in events:
        if e['kind'] in ('model_started','tool_started'):
            kind='model' if e['kind']=='model_started' else e['message']
            active[kind]=dt.datetime.fromisoformat(e['time'])
        elif e['kind'] in ('model_finished','tool_finished'):
            key='model' if e['kind']=='model_finished' else e['message'];beg=active.pop(key)
            finish=dt.datetime.fromisoformat(e['time'])
            if key=='model':model_index+=1
            timeline.append({'event':f'Model {model_index}' if key=='model' else key,
                'kind':'model' if key=='model' else 'tool','start_seconds':(beg-start).total_seconds(),
                'duration_seconds':(finish-beg).total_seconds(),'status':e.get('status','RETURNED'),
                'tokens':e.get('usage',{}).get('total_tokens')})
    timeline=pd.DataFrame(timeline);timeline.to_csv(out/'data/auto_executor_timeline.tsv',sep='\t',index=False)
    assert len(timeline)==13 and len(timeline[timeline.kind=='tool'])==6
    assert timeline.tokens.sum()==59767
    fig,axes=plt.subplots(1,2,figsize=(13,6.5),gridspec_kw={'width_ratios':[1.2,1]})
    ax=axes[0];panel(ax,'a','Actual Auto execution trace')
    colors=[GRAY if r.kind=='model' else IMP if r.status=='IMPORTED_HISTORICAL' else LIVE for r in timeline.itertuples()]
    ax.barh(range(len(timeline)),timeline.duration_seconds,left=timeline.start_seconds,color=colors,height=.65)
    for i,r in enumerate(timeline.itertuples()):
        if r.kind=='tool':ax.plot(r.start_seconds,i,marker='|',color=colors[i],ms=8,mew=1)
    ax.set(yticks=range(len(timeline)),yticklabels=timeline.event,xlabel='Seconds from first executor request');ax.invert_yaxis()
    ax.legend(handles=[Patch(color=GRAY,label='API request'),Patch(color=LIVE,label='Live check / join / report'),Patch(color=IMP,label='Historical import')],loc='upper left',bbox_to_anchor=(0,-.12),fontsize=8,frameon=False)
    ax=axes[1];ax.axis('off');panel(ax,'b','Input → evidence → output')
    box(ax,.02,.72,.96,.24,'VEGFA; 9 siDirect candidates\nARPE-19 hypoxia: 1% O₂, 24 h\nRequested top 2; external web disabled')
    box(ax,.02,.4,.96,.22,'6 / 6 planned scientific tools recorded\nLive reference check + historical model / seed\nLive expression join; 9 evidence rows agree','#DCEEE8')
    box(ax,.02,.09,.96,.22,'Priority for review: SD_3499 / SD_3500\nNot order-ready; not measured knockdown\nPlanner usage absent; total tokens unknown','#F4E8D8')
    for a,b in [((.5,.71),(.5,.64)),((.5,.39),(.5,.33))]:arrow(ax,a,b)
    fig.text(.12,.015,f"Archived run {summary['run_id']}; runtime e53bacb. Executor returned subtotal = 59,767 tokens; planning latency / usage not reconstructed.",fontsize=9)
    fig.subplots_adjust(wspace=.5,bottom=.25,top=.9);save(fig,'Figure2_real_Auto_case')

    # F3: read-only biological context; no new risk score, selection rule or p-value.
    fig,axes=plt.subplots(2,2,figsize=(13,10));ax=axes[0,0];panel(ax,'a','Untreated VEGFA expression')
    means={}
    for i,(state,color) in enumerate([('Normoxia',N),('Hypoxia',H)]):
        y=baseline.loc[baseline.state==state,'TPM'].to_numpy(float);assert len(y)==4
        means[state]=float(y.mean());ax.scatter(i+np.linspace(-.1,.1,4),y,color=color,s=35,zorder=3);ax.hlines(y.mean(),i-.2,i+.2,color=color,lw=2)
    ratio=means['Hypoxia']/means['Normoxia']
    ax.set(xticks=[0,1],xticklabels=['Normoxia','Hypoxia'],ylabel='VEGFA gene TPM',ylim=(0,None))
    ax.text(.03,.97,f'Mean TPM: {means["Normoxia"]:.2f} → {means["Hypoxia"]:.2f}\nRatio of means: {ratio:.2f}\nOne culture run; 4 dishes per state',transform=ax.transAxes,va='top',fontsize=9)
    ax=axes[0,1];panel(ax,'b','Imported sequence-model scores')
    rank=candidates.iloc[::-1];flag=rank.review_flags.fillna('').ne('')
    ax.barh(rank.candidate_id.str.replace('VEGFA_','',regex=False),rank.score,color=[IMP if v else LIVE for v in flag]);ax.set(xlabel='Model score (not knockdown fraction)',xlim=(0,1.1))
    ax.legend(handles=[Patch(color=LIVE,label='No listed review flag'),Patch(color=IMP,label='Review flag')],fontsize=8,frameon=False,loc='upper center',bbox_to_anchor=(.5,-.2),ncol=2)
    ax=axes[1,0];panel(ax,'c','Seed-matched genes with baseline expression')
    state=expression.set_index('candidate_id').loc[candidates.candidate_id].reset_index();x=np.arange(9)
    ax.bar(x-.18,state.normoxia_detected_genes,.36,color=N,label='Normoxia');ax.bar(x+.18,state.hypoxia_detected_genes,.36,color=H,label='Hypoxia')
    ax.set(xticks=x,xticklabels=state.candidate_id.str.replace('VEGFA_SD_','',regex=False),ylabel='Detected non-target matched genes',xlabel='Candidate ID suffix');ax.tick_params(axis='x',rotation=45);ax.legend(frameon=False,fontsize=8)
    ax.text(0,1.01,'TPM ≥ 1 in ≥ 2/4 dishes; guide 2–8 seed; no mismatches',transform=ax.transAxes,fontsize=8)
    ax=axes[1,1];panel(ax,'d','State-dependent annotation, fixed priority')
    ax.scatter(state.normoxia_detected_genes,state.hypoxia_detected_genes,color=GRAY,s=32)
    # Fixed label positions avoid overlap; leader lines preserve each measured point.
    positions={'2739':(590,900),'3500':(1010,710),'1157':(1190,930),'3193':(1480,1110),
               '3119':(1080,1400),'3502':(1600,1370),'3535':(1670,1660),'3499':(500,570),'3429':(210,300)}
    for r in state.itertuples():
        suffix=r.candidate_id.replace('VEGFA_SD_','')
        ax.annotate(suffix,(r.normoxia_detected_genes,r.hypoxia_detected_genes),xytext=positions[suffix],fontsize=8,
            arrowprops={'arrowstyle':'-','color':'#B0BAC2','lw':.6})
    ax.plot([0,1800],[0,1800],ls=':',color='#AAB5BE',lw=1)
    ax.set(xlabel='Normoxia detected matched genes',ylabel='Hypoxia detected matched genes',xlim=(0,1850),ylim=(0,1850))
    fig.text(.09,.015,'Expression annotates candidate context and does not change ranking. Counts are potential seed matches, not measured off-target effects; no paired design or treatment effect.',fontsize=9)
    fig.subplots_adjust(hspace=.68,wspace=.48,bottom=.12);save(fig,'Figure3_candidate_and_cell_context')
    write(out/'data/baseline_descriptive_summary.json',{'means_TPM':means,'ratio_of_means':ratio,'dishes_per_state':4,'culture_runs':1,'paired':False,'treatment':'untreated baseline','inference':'descriptive only'})

    # F4: raw states, infrastructure and internal planning failures remain distinct.
    order=['normal_hypoxia','normal_normoxia','target_only','invalid_sequence','unsupported_target','ambiguous_direction']
    names=['Hypoxia full','Normoxia full','Target only','3 nt guide','KRAS target','Unclear strand']
    result_by_id={r['answer_id']:r for r in raw}
    def category(row):
        r=result_by_id[row.answer_id];code=r.get('provider_error',{}).get('code','')
        if code=='OUTPUT_TRUNCATED':return 5
        if str(code).startswith('NETWORK'):return 6
        if row.status=='COMPLETE':return 0
        if row.status=='PARTIAL_COMPLETE':return 1
        if row.status=='ANSWERED_NO_TOOLS':return 2
        if row.status=='idle':return 3
        if row.status=='FAILED' and row.group=='agent':return 7
        if row.status=='FAILED' and row.group=='workflow':return 4
        raise AssertionError(('Unclassified execution state',row.answer_id,row.status))
    labels=['Complete','Partial','Answer / no tools','Idle / clarify','Input / program stop','Incomplete output','Network error','Planner format failure']
    cmap=ListedColormap(['#5DA78E','#9BC5B5','#7CA6C0','#B5BDD0','#D6AF77','#CB7A68','#985D75','#C04D3E'])
    grid=np.zeros((6,9),dtype=int);cells=[]
    for i,cid in enumerate(order):
        for j,group in enumerate(['llm','workflow','agent']):
            for repeat in range(1,4):
                row=records[(records.case_id==cid)&(records.group==group)&(records['repeat']==repeat)].iloc[0]
                k=category(row);grid[i,j*3+repeat-1]=k;cells.append({'case_id':cid,'group':group,'repeat':repeat,'answer_id':row.answer_id,'raw_status':row.status,'display_category':labels[k]})
    pd.DataFrame(cells).to_csv(out/'data/evaluation_display_cells.tsv',sep='\t',index=False)
    fig,axes=plt.subplots(1,2,figsize=(13.5,6.5),gridspec_kw={'width_ratios':[1.55,1]})
    ax=axes[0];panel(ax,'a','All 54 scheduled records; raw execution outcomes')
    ax.imshow(grid,cmap=cmap,vmin=0,vmax=7,aspect='auto')
    short=['C','P','A','I','F','T','N','E']
    for i in range(6):
        for j in range(9):ax.text(j,i,short[grid[i,j]],ha='center',va='center',weight='bold',fontsize=10)
    ax.set(yticks=range(6),yticklabels=names,xticks=range(9),xticklabels=['L1','L2','L3','W1','W2','W3','A1','A2','A3'])
    for v in [2.5,5.5]:ax.axvline(v,color='white',lw=4)
    ax.set_xlabel('L: plain LLM   W: fixed workflow   A: Agent; 1–3: technical repeats')
    ax.legend(handles=[Patch(color=cmap(i),label=f'{short[i]}: {v}') for i,v in enumerate(labels)],loc='upper left',bbox_to_anchor=(-.03,-.16),ncol=2,frameon=False,fontsize=8)
    ax=axes[1];panel(ax,'b','Triplets without infrastructure errors')
    available=[int(pairs.loc[pairs.case_id==cid,'all_three_without_infrastructure_error'].sum()) for cid in order]
    ax.barh(range(6),available,color=N);ax.set(yticks=range(6),yticklabels=names,xlim=(0,3.4),xticks=range(4),xlabel='Available technical-repeat triplets / 3');ax.invert_yaxis()
    for i,v in enumerate(available):ax.text(v+.07,i,str(v),va='center')
    ax.text(0,-.24,'Availability ≠ correctness.\nPlanner format failure remains in available records.\nNo independent quality scores; no superiority claim.',transform=ax.transAxes,fontsize=9,va='top')
    fig.subplots_adjust(wspace=.6,bottom=.34,top=.88);save(fig,'Figure4_development_evidence')
    assert sum(available)==12 and available[0]==0

    captions=[
      {'figure':'Figure1_system_migration','reference':'原文 Fig.1–2；本图为本项目重新绘制的架构，不复用原图',
       'caption':'a，研究者提供任务、候选方向和状态；单一豆包API通过多阶段控制器澄清、规划并经人工确认执行。绿色表示本地实际核对或关联，棕色表示经一致性核查的历史官方输出导入。b，与原文的概念对应和当前实现范围。当前未完成专用微调、独立评价或新湿实验。'},
      {'figure':'Figure2_real_Auto_case','reference':'原文 Fig.3a / Fig.4c 的实际案例呈现思路',
       'caption':'a，真实Auto运行20261020_064921_2dae59的执行事件时间轴；横轴从首个执行器请求开始，不包含未保留的规划耗时。七轮执行器API返回与六项工具逐一对应；工具起点竖线使亚毫秒至毫秒级步骤仍可见，横条长度保留实际时间。导入历史结果的步骤不称现场模型推理。b，实际输入、工具证据及优先复核名单。执行器已知token小计59,767；规划轮用量缺失，完整总量未知。没有外部检索，未将本次工具导出替代独立语义评分。'},
      {'figure':'Figure3_candidate_and_cell_context','reference':'本课题增加的siRNA序列与自有细胞表达背景结果',
       'caption':'a，同一培养批次、每状态4皿、未转染的VEGFA逐样本TPM；短横线为均值，均值比约5.09，仅为描述。b，9条siDirect计算候选的历史OligoFormer分数；颜色只标已有复核提示，分数不是敲低比例。c，两状态中符合TPM≥1且至少2/4皿的非靶seed匹配基因数；guide第2–8位、0错配、既有代表性3′UTR，未映射与不表达区分保存在底表。d，同一候选两状态的注释计数；虚线为相等计数参考线，未作回归或新风险评分。TPM不进入排序，不推断缺氧特异敲低或实验脱靶。候选不是用户文献序列或订购单。'},
      {'figure':'Figure4_development_evidence','reference':'原文 Fig.3b / Fig.4 / Fig.5 的分层评价思路；本图仅作开发诊断',
       'caption':'a，新批次54个记录全部显示，6个已见开发任务×3组×3次技术重复。C完整，P局部完成，A无工具回答，I空闲/澄清，F输入/程序停止，T响应不完整，N网络错误，E规划格式失败。F与I是否恰当必须读答案，不能自动记为正确拒绝。b，18个题目重复单元中12个三组均无基础设施错误；缺氧完整题为0/3。1条E是系统自身失败，仍留在无API错误记录中等待评分。不存在独立科学评分，图不表示准确率、优越性或显著性。'}]
    write(out/'figure_captions.json',captions)
    checks={'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'generator_path':Path(__file__).resolve().relative_to(ROOT).as_posix(),'generator_sha256':sha(Path(__file__).resolve()),
        'real_Auto_runtime_commit':summary['runtime_commit'],'real_batch_runtime_commit':read(BATCH/'three_arm/summary.json')['runtime_commit'],
        'records':54,'independent_development_tasks':6,'technical_repeats':3,'complete_hypoxia_triplets':0,
        'no_infrastructure_error_triplets':12,'Auto_tools':6,'Auto_executor_returned_tokens':59767,
        'scientific_quality_scored':False,'new_heavy_model_execution':False,'new_wet_lab':False,'source_files':sources}
    write(out/'provenance.json',checks)
    items=[]
    for c in captions:
        name=c['figure'];items.append(f'<section><h2>{name}</h2><img src="figures/{name}.png" alt="{name}"><p>{html.escape(c["caption"])}</p><p><a href="figures/{name}.svg">SVG</a> · <a href="figures/{name}.pdf">PDF</a></p></section>')
    (out/'index.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>siRNA-GPT 文献迁移结果图</title><style>body{font:16px/1.65 sans-serif;max-width:1150px;margin:30px auto;padding:20px;color:#20313c}img{width:100%}section{margin:44px 0;border-top:1px solid #ddd}a{color:#327292}</style><h1>siRNA-GPT 文献迁移结果图</h1><p>四张组合图来自已归档真实运行和细胞背景数据；不是新增模型推理或湿实验。配对质量评价和独立评分尚未完成。</p>'+''.join(items)+'</html>',encoding='utf-8')
    # A compact preview for visual inspection; independent PNG/PDF/SVG remain the outputs.
    fig,axs=plt.subplots(2,2,figsize=(16,12))
    for ax,c in zip(axs.flat,captions):ax.imshow(plt.imread(out/'figures'/f'{c["figure"]}.png'));ax.axis('off')
    fig.tight_layout();fig.savefig(out/'contact_sheet.jpg',dpi=130);plt.close(fig)
    write(out/'manifest.json',{'files':[{'path':p.relative_to(out).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(out.rglob('*')) if p.is_file()]})
    print(json.dumps({k:v for k,v in checks.items() if k!='source_files'},ensure_ascii=True))

if __name__=='__main__':main()
