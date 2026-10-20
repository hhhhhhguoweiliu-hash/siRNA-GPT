"""Redraw descriptive figures from checked-in tables, without API or model inference."""
from pathlib import Path
import argparse,shutil
import numpy as np,pandas as pd,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,FancyBboxPatch,FancyArrowPatch
from matplotlib.colors import ListedColormap

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);args=parser.parse_args()
OUT=Path(args.output)
if OUT.exists() and any(OUT.iterdir()):raise SystemExit('Use a new empty output directory')
OUT.mkdir(parents=True,exist_ok=True)
SCI=ROOT/'research/2026-10-19_scientific';AUDIT=ROOT/'research/2026-10-19_evaluation'
def table(name):return pd.read_csv(SCI/'data'/name,sep='\t')
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'svg.fonttype':'none'})
N,H='#427D9D','#D7784C'
def save(fig,name):
 for ext in ['png','svg','pdf']:fig.savefig(OUT/(name+'.'+ext),dpi=300,bbox_inches='tight',facecolor='white')
 plt.close(fig)

fig,ax=plt.subplots(figsize=(10,5));ax.set(xlim=(0,10),ylim=(0,5));ax.axis('off')
labels=[(.3,3.4,2.7,1,'Researcher\nTask / candidates / TPM'),(3.65,3.4,2.7,1,'Doubao API\nPlan / execute / explain'),(7,3.4,2.7,1,'Controlled state machine\nDependencies / retry'),(.3,1.6,2.7,1,'Live guide / transcript checks'),(3.65,1.6,2.7,1,'Verified historical imports\nOligoFormer / SeedMatchR'),(7,1.6,2.7,1,'Actual baseline join\nNormoxia / hypoxia'),(3.65,.1,6.05,.9,'Evidence table / sources / records / human review')]
for x,y,w,h,text in labels:
 ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.08',facecolor='#EAF1F5',edgecolor='#A0ADB7'));ax.text(x+w/2,y+h/2,text,ha='center',va='center')
for start,end in [((3.1,3.9),(3.55,3.9)),((6.45,3.9),(6.9,3.9)),((1.65,3.3),(1.65,2.7)),((8.35,3.3),(8.35,2.7)),((3.1,2.1),(3.55,2.1)),((6.45,2.1),(6.9,2.1)),((8.35,1.5),(8.35,1.1))]:ax.add_patch(FancyArrowPatch(start,end,arrowstyle='-|>',mutation_scale=12,color='#596C7D'))
ax.text(0,-.06,'Human VEGFA / ARPE-19; expression annotation does not change default ranking.',transform=ax.transAxes,fontsize=9)
save(fig,'Fig01_system_scope')

rank=table('candidate_evidence.tsv');rev=rank.iloc[::-1]
fig,ax=plt.subplots(figsize=(9,4.8));ax.barh(rev.candidate_id,rev.score,color=['#C78A4D' if pd.notna(v) and str(v) else '#438C7C' for v in rev.review_flags]);ax.set(xlim=(0,1.09),xlabel='Model score, not knockdown fraction',title='Imported OligoFormer scores; ochre = review flag')
for i,v in enumerate(rev.score):ax.text(v+.01,i,f'{v:.4f}',va='center')
save(fig,'Fig02_candidate_model_scores')

c=pd.read_csv(ROOT/'data/candidates.tsv',sep='\t');guides=c.guide_paired_core_19nt_5to3.str.upper().str.replace('T','U',regex=False)
fig,ax=plt.subplots(figsize=(10,4.5));ax.imshow([[list('ACGU').index(b) for b in g] for g in guides],aspect='auto',cmap=ListedColormap(['#E6C86E','#77A9CA','#79B69D','#C894B4']),vmin=0,vmax=3)
for i,g in enumerate(guides):
 for j,b in enumerate(g):ax.text(j,i,b,ha='center',va='center')
ax.set(xticks=range(19),xticklabels=range(1,20),yticks=range(len(c)),yticklabels=c.candidate_id,xlabel='19 nt paired core, guide 5′ to 3′',title='Seed positions 2–8; not an order-ready duplex');ax.add_patch(Rectangle((.5,-.5),7,len(c),fill=False,edgecolor='#9B3B3B',lw=2));save(fig,'Fig03_guide_seed_map')

fig,ax=plt.subplots(figsize=(9,4.5));ax.barh(rev.candidate_id,rev.covered_transcripts,color=N);ax.set(xlim=(0,22),xlabel='Exactly matched packaged reference transcripts',title='Reference coverage, not measured isoform usage');save(fig,'Fig04_transcript_coverage')
state=table('seed_expression_state_comparison.tsv');x=np.arange(len(state));ids=[s.replace('VEGFA_SD_','') for s in state.candidate_id]
fig,axes=plt.subplots(1,2,figsize=(12,4.8));axes[0].bar(x-.19,state.normoxia_detected_genes,.36,color=N,label='Normoxia');axes[0].bar(x+.19,state.hypoxia_detected_genes,.36,color=H,label='Hypoxia');axes[0].legend(frameon=False);axes[0].set_title('TPM ≥ 1 in at least 2/4 samples')
axes[1].bar(x,state.unmapped_genes,color='#7B8793');axes[1].set_title('Unmapped is not unexpressed')
for ax in axes:ax.set_xticks(x);ax.set_xticklabels(ids,rotation=45);ax.set_xlabel('Candidate ID suffix')
axes[0].set_ylabel('Detected non-target seed-matched genes');axes[1].set_ylabel('Unmapped genes');save(fig,'Fig05_seed_expression_context')

v=table('VEGFA_eight_samples_TPM.tsv');fig,ax=plt.subplots(figsize=(6.5,4.8))
for i,(name,col) in enumerate([('Normoxia',N),('Hypoxia',H)]):
 y=v.loc[v.state==name,'TPM'].to_numpy();ax.scatter(i+np.linspace(-.12,.12,len(y)),y,color=col,s=55);ax.hlines(y.mean(),i-.2,i+.2,color=col,lw=3)
ax.set(ylim=(0,None),xticks=[0,1],xticklabels=['Normoxia','Hypoxia 1% O₂, 24 h'],ylabel='VEGFA gene TPM',title='Untreated baseline: one culture run, four dishes per state');save(fig,'Fig06_VEGFA_baseline_TPM')

m=table('predefined_context_markers_TPM.tsv');samples=['Nor1','Nor2','Nor3','Nor4','Hyp1','Hyp2','Hyp3','Hyp4'];fig,ax=plt.subplots(figsize=(8,6));im=ax.imshow(np.log2(m[samples].to_numpy(float)+1),aspect='auto',cmap='viridis');ax.set(xticks=range(8),xticklabels=samples,yticks=range(len(m)),yticklabels=m.symbol,title='Predefined contextual genes: baseline abundance');ax.axvline(3.5,color='white',lw=2);fig.colorbar(im,ax=ax,label='log₂(TPM + 1)');save(fig,'Fig07_context_marker_expression')

e=table('workflow_development_execution.tsv');cases=['normal_hypoxia','normal_normoxia','target_only','invalid_sequence','unsupported_target','ambiguous_direction'];names=['Hypoxia full','Normoxia full','Target only','Bad guide','KRAS','No strand']
matrix=np.array([[{'FAILED':0,'PARTIAL_COMPLETE':1,'COMPLETE':2}[e[(e.case_id==cid)&(e.repeat==rep)].iloc[0].status] for rep in range(1,4)] for cid in cases])
fig,ax=plt.subplots(figsize=(7,4.3));ax.imshow(matrix,cmap=ListedColormap(['#E9B692','#B9D1E0','#8DBFAE']),vmin=0,vmax=2,aspect='auto')
for i in range(6):
 for j in range(3):ax.text(j,i,['Stopped','Partial','Complete'][matrix[i,j]],ha='center',va='center')
ax.set(xticks=range(3),xticklabels=['R1','R2','R3'],yticks=range(6),yticklabels=names,title='Fixed workflow: 18 local development executions');save(fig,'Fig08_workflow_development_status')
fig,ax=plt.subplots(figsize=(9,4.5))
for i,cid in enumerate(cases):
 y=e.loc[e.case_id==cid,'seconds'].dropna().to_numpy(float);ax.scatter(i+np.linspace(-.08,.08,len(y)),y,color=N);ax.hlines(y.mean(),i-.2,i+.2,color=N)
ax.set(xticks=range(6),xticklabels=names,ylabel='Local wall time (s)',title='Fixed workflow, historical imports; no model API');save(fig,'Fig09_workflow_local_time')

t=table('TPM_detection_threshold_sensitivity.tsv');fig,axes=plt.subplots(3,3,figsize=(11,8),sharex=True,sharey=True)
for ax,cid in zip(axes.flat,c.candidate_id):
 for name,col in [('Normoxia',N),('Hypoxia',H)]:
  sub=t[(t.candidate_id==cid)&(t.state==name)];ax.plot(sub.TPM_threshold,sub.detected_non_target_genes,marker='o',color=col,label=name,ms=3)
 ax.set_title(cid,fontsize=9);ax.set_xscale('log');ax.axvline(1,ls=':',color='#9AA7AF')
axes[0,0].legend(frameon=False,fontsize=8);fig.supxlabel('TPM detection threshold, ≥2/4 samples');fig.supylabel('Detected non-target seed-matched genes');fig.suptitle('Descriptive sensitivity; no fitted or validated risk score');save(fig,'Fig10_TPM_threshold_sensitivity')

# Audit figures are supplied as immutable source SVGs; no model-quality scores are generated.
for p in (AUDIT/'figures').glob('*.svg'):shutil.copy2(p,OUT/p.name)
print('Redrew 10 descriptive figures and copied 3 original audit SVGs; no API or heavy inference used.')
