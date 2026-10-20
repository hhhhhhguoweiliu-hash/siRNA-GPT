"""Reproduce today's descriptive results from actual project data; no invented API arms."""
from pathlib import Path
import sys,json,csv,hashlib,shutil,datetime,textwrap
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch,Rectangle
from matplotlib.colors import ListedColormap

ROOT=Path(__file__).resolve().parents[1]
BUNDLED=(ROOT/'reproduce/app/core.py').is_file()
CODE=ROOT/'reproduce/app' if BUNDLED else ROOT/'render/sirna-gpt'
sys.path.insert(0,str(CODE))
from core import Session,default_candidates,read_tsv,DATA,canonical
from evaluate import run_case
from runtime_info import manifest

OUT=ROOT/'reproduced_results' if BUNDLED else ROOT/'deliverables/siRNA_GPT_results_20261019_v1'
FIG=OUT/'figures';TAB=OUT/'data';RAW=OUT/'raw';SCRIPTS=OUT/'reproduce'
for p in [FIG,TAB,RAW,SCRIPTS]:p.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'svg.fonttype':'none'})
COL={'N':'#427D9D','H':'#D7784C','good':'#438C7C','flag':'#C78A4D','muted':'#7B8793'}
captions=[]
def save(fig,name,title,caption):
 fig.savefig(FIG/(name+'.png'),dpi=320,bbox_inches='tight',facecolor='white')
 fig.savefig(FIG/(name+'.pdf'),bbox_inches='tight',facecolor='white')
 fig.savefig(FIG/(name+'.svg'),bbox_inches='tight',facecolor='white')
 plt.close(fig);captions.append({'figure':name,'title':title,'caption_zh':caption,'scope':'descriptive or engineering; not experimental siRNA efficacy'})
def export(df,name):df.to_csv(TAB/name,sep='\t',index=False,encoding='utf-8-sig')

# Actual deterministic scientific workflow, with the hosted system's imported outputs.
s=Session(run_root=RAW/'candidate_run',tool_mode='imported',mode='workflow');res=s.run()
assert res['status']=='COMPLETE',res
report=json.loads((s.path/'report.json').read_text(encoding='utf-8'));rank=pd.DataFrame(report['rows'])
summary=pd.DataFrame(report['expression_comparison']);detail=pd.read_csv(s.path/'seed_expression_details.tsv',sep='\t')
export(rank,'candidate_evidence.tsv');export(summary,'seed_expression_state_comparison.tsv')
shutil.copy2(s.path/'seed_expression_details.tsv',TAB/'seed_expression_gene_details.tsv')
for f in DATA.iterdir():
 if f.is_file():shutil.copy2(f,RAW/f.name)
(RAW/'runtime.json').write_text(json.dumps(manifest(),ensure_ascii=False,indent=2),encoding='utf-8')

# 01: precise implementation schematic, not an experimental result.
fig,ax=plt.subplots(figsize=(10.5,6));ax.set(xlim=(0,10),ylim=(0,6));ax.axis('off')
nodes=[(.25,4.55,2.6,.95,'Researcher input\nCandidates + task\nBaseline TPM','#EAF1F5'),(3.55,4.55,2.8,.95,'Doubao API\nPlan / execute / explain','#E7F1ED'),(7,4.55,2.7,.95,'Controlled state machine\nDependencies / stop / retry','#EAF1F5'),(.25,2.45,2.6,1.1,'Live checks\nGuide orientation\nVEGFA reference matching','#EAF1F5'),(3.55,2.45,2.8,1.1,'Verified historical imports\nOligoFormer score\nSeedMatchR mer7m8 matches','#FFF0DF'),(7,2.45,2.7,1.1,'Actual baseline join\nNormoxia / hypoxia TPM\nNon-target gene annotation','#EAF1F5'),(3.55,.35,6.15,1.0,'Auditable outputs\nCandidate table / sources / raw records / human review','#E7F1ED')]
for x,y,w,h,label,color in nodes:
 ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.1',facecolor=color,edgecolor='#A0ADB7'));ax.text(x+w/2,y+h/2,label,ha='center',va='center',fontsize=10)
for a,b in [((2.95,5),(3.45,5)),((6.45,5),(6.9,5)),((8.35,4.4),(8.35,3.7)),((3.05,3),(3.4,3)),((6.45,3),(6.9,3)),((8.35,2.3),(8.35,1.5)),((1.55,4.4),(1.55,3.7))]:ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=13,color='#596C7D'))
ax.text(.015,-.045,'Current scope: human VEGFA / ARPE-19; expression annotation does not alter model score or ranking.',fontsize=9,color='#526371',transform=ax.transAxes)
save(fig,'Fig01_system_scope','当前系统框架','迁移原文的规划、执行、工具和人机协作结构。橙色框明确标为历史结果导入；不是完整复现原文，也不表示已实现新序列现场计算。')

# 02: efficacy and review flags are separate evidence, no fused score.
fig,ax=plt.subplots(figsize=(9,4.8));ordered=rank.iloc[::-1]
bars=ax.barh(ordered.candidate_id,ordered.score,color=[COL['flag'] if str(x) not in ('','nan') else COL['good'] for x in ordered.review_flags],height=.64)
ax.set(xlim=(0,1.08),xlabel='OligoFormer model score (not knockdown fraction)',title='Nine computed VEGFA candidates: imported model scores')
for b,v in zip(bars,ordered.score):ax.text(v+.01,b.get_y()+b.get_height()/2,f'{v:.4f}',va='center',fontsize=9)
ax.text(0,-.18,'Green: no current review flag. Ochre: requires review. No biological validation.',transform=ax.transAxes,fontsize=9,color=COL['muted'])
save(fig,'Fig02_candidate_model_scores','9条候选效力模型分数','使用10月16日已有计算结果。颜色只表示当前复核提示，不表示安全/危险已获验证；分数不是敲低比例。排序沿用当前原型规则，TPM没有参与排序。')

# 03: orientation and seed region are visible.
seqs=[canonical(x) for x in default_candidates()];ids=[x['candidate_id'] for x in default_candidates()]
alphabet='ACGU';encoded=np.array([[alphabet.index(b) for b in seq] for seq in seqs])
fig,ax=plt.subplots(figsize=(10,4.5));ax.imshow(encoded,cmap=ListedColormap(['#E6C86E','#77A9CA','#79B69D','#C894B4']),vmin=0,vmax=3,aspect='auto')
for i,seq in enumerate(seqs):
 for j,base in enumerate(seq):ax.text(j,i,base,ha='center',va='center',fontsize=10)
ax.set(yticks=range(len(ids)),yticklabels=ids,xticks=range(19),xticklabels=range(1,20),xlabel='Guide paired-core position, 5′ to 3′',title='Guide orientation and seed positions (2–8)')
ax.add_patch(Rectangle((.5,-.5),7,len(ids),fill=False,edgecolor='#9B3B3B',linewidth=2))
save(fig,'Fig03_guide_seed_map','候选序列与seed位置','展示经核对的19nt guide配对核心，红框为位置2–8。不是可直接订购的完整双链与修饰方案。')

# 04: all reference matching, without implying expression of all isoforms.
fig,ax=plt.subplots(figsize=(9,4.5));ax.barh(rank.candidate_id.iloc[::-1],rank.covered_transcripts.iloc[::-1],color=COL['N'])
ax.set(xlim=(0,22),xticks=[0,5,10,15,20],xlabel='Exactly matched reference transcripts (20 included)',title='Sequence coverage in the packaged VEGFA reference set')
for i,v in enumerate(rank.covered_transcripts.iloc[::-1]):ax.text(v+.2,i,str(v),va='center')
save(fig,'Fig04_transcript_coverage','参考转录本覆盖','固定20条参考VEGFA转录本中的序列匹配覆盖，不代表这些异构体都在ARPE-19中表达，也不是全基因组脱靶检查。')

# 05: actual gene-wise baseline association; target excluded, missing explicit.
fig,axes=plt.subplots(1,2,figsize=(12.2,4.8),gridspec_kw={'width_ratios':[1.5,1]})
x=np.arange(len(summary));axes[0].bar(x-.19,summary.normoxia_detected_genes,.36,color=COL['N'],label='Normoxia');axes[0].bar(x+.19,summary.hypoxia_detected_genes,.36,color=COL['H'],label='Hypoxia')
axes[0].set(xticks=x,xticklabels=[i.replace('VEGFA_SD_','') for i in summary.candidate_id],xlabel='Candidate ID suffix',ylabel='Matched non-target genes detected',title='TPM ≥ 1 in at least 2/4 samples');axes[0].legend(frameon=False);axes[0].tick_params(axis='x',labelrotation=45);axes[0].tick_params(axis='x',labelrotation=45)
axes[1].bar(x,summary.unmapped_genes,color=COL['muted']);axes[1].set(xticks=x,xticklabels=[i.replace('VEGFA_SD_','') for i in summary.candidate_id],xlabel='Candidate ID suffix',ylabel='Genes without a baseline mapping',title='Unmapped is not unexpressed');axes[1].tick_params(axis='x',labelrotation=45);axes[1].tick_params(axis='x',labelrotation=45)
save(fig,'Fig05_seed_expression_context','seed匹配与两状态表达关联','仅guide mer7m8、代表性参考3′UTR。排除目标基因VEGFA；TPM阈值为描述性检测规则，不是毒性阈值。匹配、表达和未映射分开记录，不能从柱高推断实际脱靶程度。')

# Recover the eight actual gene TPM values from the user's earlier vendor table.
BASE=ROOT/'raw/baseline_source' if BUNDLED else ROOT/'deliverables/ARPE19_baseline_20261016_v0.1/03_baseline'
tpm=pd.read_csv(BASE/'expression_tpm_vendor.tsv',sep='\t',index_col=0)
mapping=pd.read_csv(BASE/'gene_id_map_vendor.tsv',sep='\t')
targets=mapping.loc[mapping.symbol=='VEGFA','source_gene_id'].tolist();assert len(targets)==1
values=tpm.loc[targets[0]]
assert abs(float(values[['Nor1','Nor2','Nor3','Nor4']].mean())-float(report['expression']['TPM_Normoxia_mean']))<1e-5
assert abs(float(values[['Hyp1','Hyp2','Hyp3','Hyp4']].mean())-float(report['expression']['TPM_Hypoxia_mean']))<1e-5
target_rows=pd.DataFrame([{'sample':k,'state':'Hypoxia' if k.startswith('Hyp') else 'Normoxia','TPM':float(v)} for k,v in values.items()]);export(target_rows,'VEGFA_eight_samples_TPM.tsv')
fig,ax=plt.subplots(figsize=(6.5,4.8))
for i,(state,prefix,col) in enumerate([('Normoxia','Nor',COL['N']),('Hypoxia','Hyp',COL['H'])]):
 v=values[[prefix+str(n) for n in range(1,5)]].to_numpy(float);ax.scatter(i+np.linspace(-.1,.1,4),v,s=55,color=col,zorder=3)
 ax.hlines(v.mean(),i-.2,i+.2,color=col,linewidth=3)
 for n,y in enumerate(v):ax.annotate(prefix+str(n+1),(i+np.linspace(-.1,.1,4)[n],y),xytext=([(-38,12),(-30,-20),(10,-20),(10,8)][n] if prefix=='Nor' else (4,3)),textcoords='offset points',fontsize=8,arrowprops={'arrowstyle':'-','color':'#9AA7AF','lw':.6} if prefix=='Nor' else None)
ax.set(xticks=[0,1],xticklabels=['Normoxia','Hypoxia 1% O₂, 24 h'],ylabel='VEGFA gene TPM',title='Untreated ARPE-19 baseline: eight separately harvested dishes',xlim=(-.5,1.6))
ax.set_ylim(bottom=0)
save(fig,'Fig06_VEGFA_baseline_TPM','VEGFA基线表达','每点为一个分别提取RNA的培养皿，横线为均值。8样本属于同一培养批次；本图不进行推断检验，不是siRNA处理后的敲低结果。均值已与网页内置表达表核对。')

# 07: predefined contextual markers, descriptive and not a selected discovery signature.
markers=['VEGFA','HIF1A','SLC2A1','CA9','BNIP3','EGLN3','LDHA','PGK1','PDK1','ADM','NDRG1','DDIT4','ACTB','GAPDH']
marker_rows=[];marker_values=[];samples=['Nor1','Nor2','Nor3','Nor4','Hyp1','Hyp2','Hyp3','Hyp4']
for gene in markers:
 selected=mapping.loc[mapping.symbol==gene,'source_gene_id'].tolist()
 if len(selected)!=1 or selected[0] not in tpm.index:continue
 row=tpm.loc[selected[0],samples];marker_rows.append({'symbol':gene,'source_gene_id':selected[0],**row.to_dict()});marker_values.append(row.to_numpy(float))
export(pd.DataFrame(marker_rows),'predefined_context_markers_TPM.tsv')
fig,ax=plt.subplots(figsize=(8,6));im=ax.imshow(np.log2(np.array(marker_values)+1),aspect='auto',cmap='viridis')
ax.set(xticks=range(8),xticklabels=samples,yticks=range(len(marker_rows)),yticklabels=[r['symbol'] for r in marker_rows],title='Predefined contextual genes: baseline abundance');ax.axvline(3.5,color='white',linewidth=2);fig.colorbar(im,ax=ax,label='log₂(TPM + 1)')
save(fig,'Fig07_context_marker_expression','预先列出的背景基因表达','这是指定基因的基线表达展示，不是从显著性结果挑选的发现性signature，不证明缺氧导致了siRNA效力改变。GAPDH/ACTB仅展示，不能据本图认定适合作内参。')

# Fixed-workflow developmental execution, all cases and repeats retained.
suite=json.loads((CODE/'evaluation_cases.example.json').read_text(encoding='utf-8'));case_results=[]
for case in suite['cases']:
 for repeat in range(1,4):
  try:r=run_case('workflow',case,{},RAW/'workflow_development'/case['id']/str(repeat))
  except Exception as e:r={'case_id':case['id'],'group':'workflow','status':'FAILED','answer':str(e),'tool_calls':0,'seconds':None,'usage':[]}
  r['repeat']=repeat;case_results.append(r)
(RAW/'workflow_results.json').write_text(json.dumps(case_results,ensure_ascii=False,indent=2),encoding='utf-8')
execution=pd.DataFrame([{k:r.get(k) for k in ['case_id','group','repeat','status','tool_calls','seconds','total_tokens']} for r in case_results]);export(execution,'workflow_development_execution.tsv')
case_ids=[c['id'] for c in suite['cases']];labels=['Hypoxia full','Normoxia full','Target check only','Invalid guide length','Unsupported KRAS','Missing strand/core']
matrix=np.array([[{'COMPLETE':2,'PARTIAL_COMPLETE':1,'FAILED':0}.get(next(r for r in case_results if r['case_id']==cid and r['repeat']==rep)['status'],-1) for rep in range(1,4)] for cid in case_ids])
fig,ax=plt.subplots(figsize=(7,4.3));ax.imshow(matrix,cmap=ListedColormap(['#E9B692','#B9D1E0','#8DBFAE']),vmin=0,vmax=2,aspect='auto')
for i in range(6):
 for j in range(3):ax.text(j,i,['Stopped','Partial','Complete'][matrix[i,j]],ha='center',va='center')
ax.set(xticks=range(3),xticklabels=['Repeat 1','Repeat 2','Repeat 3'],yticks=range(6),yticklabels=labels,title='Fixed workflow: all 18 developmental executions')
save(fig,'Fig08_workflow_development_status','固定流程开发任务记录','实际运行6个开发案例各3次：正常任务和错误输入全部保留。Stopped表示程序停止，不自动等于语义上正确拒绝。不是三组比较，也不是独立测试集准确率。')

fig,ax=plt.subplots(figsize=(8.5,4.5))
for i,cid in enumerate(case_ids):
 v=execution.loc[execution.case_id==cid,'seconds'].dropna().to_numpy(float)
 ax.scatter(np.full(len(v),i)+np.linspace(-.08,.08,len(v)),v,color=COL['N'],s=42)
 if len(v):ax.hlines(v.mean(),i-.18,i+.18,color=COL['N'])
ax.set(xticks=range(6),xticklabels=['Hypoxia','Normoxia','Target only','Bad guide','KRAS','No strand'],ylabel='Wall time (seconds)',title='Local fixed-workflow time: historical imports, no model API')
save(fig,'Fig09_workflow_local_time','固定流程本地耗时','只报告本机固定流程的实测耗时，每点一次运行。不可与未运行的普通LLM/Agent比较，不代表重型模型现场推理时间，也不是云端响应时间。')

# Threshold sensitivity uses original per-sample baseline TPM with the fixed ID map.
baseline=pd.read_csv(DATA/'expression.tsv.gz',sep='\t',dtype={'ENTREZID':str})
# Use only unambiguous symbols that can be matched to the original vendor rows.
unique=mapping.groupby('symbol').source_gene_id.agg(list).to_dict();expmap={}
for row in baseline.itertuples(index=False):
 genes=unique.get(row.approved_symbol,[])
 if len(genes)==1 and genes[0] in tpm.index and str(row.ENTREZID).isdigit():expmap[str(row.ENTREZID)]=tpm.loc[genes[0],samples].to_numpy(float)
matches=read_tsv(DATA/'historical_seed_matches.tsv');thresholds=[.1,.5,1,2,5];sensitivity=[]
for cid in ids:
 genes={x['gene_id'] for x in matches if x['candidate_id']==cid and x['gene_id']!='7422'}
 for threshold in thresholds:
  for state,indices in [('Normoxia',slice(0,4)),('Hypoxia',slice(4,8))]:
   count=sum(int(np.sum(expmap[g][indices]>=threshold))>=2 for g in genes if g in expmap)
   sensitivity.append({'candidate_id':cid,'state':state,'TPM_threshold':threshold,'detected_non_target_genes':count,'unambiguous_sample_level_mapping':sum(g in expmap for g in genes),'seed_gene_total':len(genes),'scope':'descriptive sensitivity; different mapping scope from cloud aggregate table'})
sens=pd.DataFrame(sensitivity);export(sens,'TPM_detection_threshold_sensitivity.tsv')
fig,axes=plt.subplots(3,3,figsize=(11,8),sharex=True,sharey=True)
for ax,cid in zip(axes.flat,ids):
 for state,col in [('Normoxia',COL['N']),('Hypoxia',COL['H'])]:
  sub=sens[(sens.candidate_id==cid)&(sens.state==state)];ax.plot(sub.TPM_threshold,sub.detected_non_target_genes,marker='o',ms=3,color=col,label=state)
 ax.set_title(cid,fontsize=9);ax.set_xscale('log');ax.axvline(1,color='#9AA7AF',ls=':',lw=1)
axes[0,0].legend(frameon=False,fontsize=8);fig.supxlabel('TPM detection threshold (≥2 of 4 samples)');fig.supylabel('Detected seed-matched non-target genes');fig.suptitle('Descriptive threshold sensitivity; not a validated risk score')
save(fig,'Fig10_TPM_threshold_sensitivity','TPM检测阈值敏感性','使用可唯一回连到原始逐样本TPM的基因，改变描述性检测阈值；不拟合新权重、不选择最有利阈值，不改变候选排序。此图映射范围与云端汇总表可能不同，详见数据列。')

export(pd.DataFrame(captions),'figure_captions.tsv')
(OUT/'figure_captions.json').write_text(json.dumps(captions,ensure_ascii=False,indent=2),encoding='utf-8')
for name in ['evaluate.py','paper_pilot.py','evaluation_cases.example.json','EVALUATION.md','SCIENTIFIC_SCOPE.md','REFERENCE_ALIGNMENT.md']:
 shutil.copy2(CODE/name,SCRIPTS/name)
shutil.copy2(Path(__file__),SCRIPTS/'build_results_20261019.py')
appcopy=SCRIPTS/'app';appcopy.mkdir(exist_ok=True)
for source in CODE.iterdir():
 if source.is_file() and (source.suffix=='.py' or source.name in ('config.example.json','evaluation_cases.example.json')):
  shutil.copy2(source,appcopy/source.name)
shutil.copytree(DATA,appcopy/'data',dirs_exist_ok=True)
basecopy=RAW/'baseline_source';basecopy.mkdir(exist_ok=True)
for name in ['expression_tpm_vendor.tsv','gene_id_map_vendor.tsv']:shutil.copy2(BASE/name,basecopy/name)
summary={'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'runtime':manifest(),'candidate_count':len(rank),'selected_for_review':report['selected_for_review'],'expression_target':report['expression'],
 'workflow_records':len(execution),'workflow_status_counts':execution.status.value_counts().to_dict(),'figure_count':len(captions),
 'new_llm_agent_comparative_runs':0,'formal_blinded_review_completed':False,'new_wetlab_data':False,'new_heavy_inference':False,
 'source_scope':'Own baseline, one culture run, four dishes per oxygen condition; historical official scientific outputs; development examples only'}
(OUT/'results_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=True))
