"""Descriptive complete-plan figure; refuses partial plans or substitute fonts."""
import csv,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'research/2026-10-24_nearfull_complete'
def read(name):
 with (OUT/name).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter='\t'))
def main():
 a=json.loads((OUT/'completion_audit.json').read_text(encoding='utf-8'));assert a['status']=='PASS' and a['planned_unique']==264 and a['failed']==a['not_run']==0
 for file in ['arial.ttf','arialbd.ttf']:fm.fontManager.addfont('C:/Windows/Fonts/'+file)
 assert Path(fm.findfont(fm.FontProperties(family='Arial',weight='normal'),fallback_to_default=False)).name.lower()=='arial.ttf'
 assert Path(fm.findfont(fm.FontProperties(family='Arial',weight='bold'),fallback_to_default=False)).name.lower()=='arialbd.ttf'
 plt.rcParams.update({'font.family':'Arial','font.size':9,'axes.titlesize':10,'axes.titleweight':'bold','axes.labelsize':9,'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})
 rows=read('all_65_designs_complete.tsv');assert len(rows)==65
 p=read('purchased_separate_complete.tsv')[0]
 queries=[(r,k) for r in ['guide','passenger'] for k in ['paired_core19','sidirect_g2g20']]
 labels=['Guide\n1–19','Guide\n2–20','Passenger\n1–19','Passenger\n2–20']
 counts=[];unknown=[];source=[]
 for (role,kind),label in zip(queries,labels):
  field=role+'_'+kind+'_mm1_non_target_gene_n';u=role+'_'+kind+'_mm1_unknown_mapping_transcript_n'
  counts.append(sum(int(r[field])>0 for r in rows));unknown.append(sum(int(r[u])>0 for r in rows))
  source.append({'scope':'65 designs','query':role+' '+kind,'designs_with_mapped_non_target_at_most_1mm':counts[-1],'designs_with_unknown_mapping_at_most_1mm':unknown[-1]})
 fig,axes=plt.subplots(1,2,figsize=(7.3,3.3),gridspec_kw={'width_ratios':[1,1.15]})
 x=np.arange(4);axes[0].bar(x,counts,width=.62,color='#247f82')
 for i,c in enumerate(counts):axes[0].text(i,c+.25,str(c),ha='center',va='bottom')
 axes[0].set(xticks=x,xticklabels=labels,ylabel='Designs with ≥1 non-target gene',ylim=(0,max(counts+[1])+2))
 axes[0].set_title('65 designs: ≤1 mismatch',pad=13)
 axes[0].text(0,-.28,'Unknown-mapping designs: '+', '.join(map(str,unknown)),transform=axes[0].transAxes,fontsize=8)
 colors=['#c7dede','#75aaa8','#226e76'];width=.23
 for j,mm in enumerate([0,1,2]):
  values=[int(p[role+'_'+kind+'_mm'+str(mm)+'_non_target_gene_n']) for role,kind in queries]
  axes[1].bar(x+(j-1)*width,values,width=width,color=colors[j],label='≤'+str(mm)+' mismatches')
  for i,c in enumerate(values):
   if c:axes[1].text(i+(j-1)*width,c+.08,str(c),ha='center',fontsize=8)
  source.extend({'scope':'Purchased siVEGF','query':role+' '+kind,'max_mismatches':mm,'mapped_non_target_genes':v} for (role,kind),v in zip(queries,values))
 axes[1].set(xticks=x,xticklabels=labels,ylabel='Distinct non-target genes',ylim=(0,4.6));axes[1].set_title('Purchased duplex (separate)',pad=13)
 axes[1].legend(frameon=False,fontsize=7,loc='upper left',ncols=1)
 for ax,letter in zip(axes,['a','b']):
  ax.text(-.16,1.12,letter,transform=ax.transAxes,fontweight='bold',fontsize=12)
  ax.tick_params(labelsize=8)
 fig.subplots_adjust(left=.085,right=.98,top=.83,bottom=.25,wspace=.36)
 folder=OUT/'figures';folder.mkdir(exist_ok=True)
 for ext in ['png','pdf','svg']:fig.savefig(folder/('nearfull_complete.'+ext),dpi=300,facecolor='white')
 with (folder/'source_data.tsv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for r in source for k in r)),delimiter='\t');w.writeheader();w.writerows(source)
 (folder/'CAPTION_EN.md').write_text('Figure. Complete fixed-reference near-full checks. (a) Number of the 65 unchanged reporting-pool designs with at least one mapped non-VEGFA gene hit at at most one mismatch, separately for each strand/window; unknown-mapping design counts are shown below in the same order. (b) Cumulative distinct non-target genes for the purchased duplex alone at at most zero, one and two mismatches. All 264 planned queries (old 24 plus new 240) were completed and audited against the same 186,185-transcript reference. The overlapping 19-nt windows are correlated checks, not independent biological replicates. These descriptive sequence matches are not experimental off-target effects, toxicity, knockdown efficacy or an Agent superiority measure. No new ranking/filter rule is introduced. Font: embedded Arial/Arial Bold.\n',encoding='utf-8')
 print(json.dumps({'designs':65,'non_target_0or1mm_design_counts':counts,'unknown_mapping_design_counts':unknown,'font_files':['arial.ttf','arialbd.ttf']}))
if __name__=='__main__':main()
