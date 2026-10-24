"""Descriptive figures for complete 65-design predictions/seed annotations; no accuracy claims."""
import hashlib,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'research/2026-10-24_candidate_v2';OUT=P/'figures';OUT.mkdir(exist_ok=True)
regular=Path('C:/Windows/Fonts/arial.ttf');bold=Path('C:/Windows/Fonts/arialbd.ttf')
assert regular.is_file() and bold.is_file()
for path in [regular,bold]:fm.fontManager.addfont(str(path))
assert fm.FontProperties(fname=str(regular)).get_name()=='Arial'
plt.rcParams.update({'font.family':'Arial','font.size':8,'axes.labelsize':8,'axes.titlesize':9,'axes.titleweight':'bold','axes.spines.top':False,'axes.spines.right':False,
 'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none','axes.unicode_minus':False,'xtick.labelsize':7,'ytick.labelsize':7,'legend.fontsize':7})
assert Path(fm.findfont(fm.FontProperties(family='Arial'),fallback_to_default=False)).name.casefold()=='arial.ttf'
data=json.loads((P/'new_65_complete_table.json').read_text(encoding='utf-8'));bought=json.loads((P/'purchased_siVEGF_separate.json').read_text(encoding='utf-8'))[0]
assert len(data)==65 and all(r['oligo_status']=='COMPLETED_REAL_NEW' for r in data)
fig,axes=plt.subplots(1,3,figsize=(11.5,3.35),gridspec_kw={'width_ratios':[0.78,1.2,1.1]})
ax=axes[0];ax.bar([0,1,2],[104,65,9],color=['#bec5cc','#377f90','#8ca8b0'],width=0.62)
for i,n in enumerate([104,65,9]):ax.text(i,n+2,str(n),ha='center',weight='bold')
ax.set_xticks([0,1,2],['Original\noutput','Revised\npool','Historical\nsubset*']);ax.set_ylim(0,120);ax.set_ylabel('Number of designs');ax.set_title('Candidate accounting')
ax.text(0.02,-0.26,'*Subset of the revised pool',transform=ax.transAxes,va='top',fontsize=7)
groups=[('5prime_UTR_or_boundary',"5' UTR / boundary",'#9aa1a7'),('CDS','Coding sequence','#2f6ba1'),('3prime_UTR',"3' UTR",'#3a938d')]
ax=axes[1];ax.axvspan(497,1684,color='#e6eef6',zorder=0)
for kind,label,color in groups:
 rows=[r for r in data if r['reference_feature']==kind]
 ax.scatter([r['core_start_1based'] for r in rows],[r['oligoformer_scaled_score'] for r in rows],s=21,c=color,label=label+' (n='+str(len(rows))+')',linewidths=0.35,edgecolors='white')
ax.set_xlim(0,3650);ax.set_ylim(0.3,1.22);ax.set_xlabel('Core start on NM_003376.6 (nt)');ax.set_ylabel('OligoFormer score (scaled)');ax.set_title('All 65 design predictions');ax.legend(loc='lower left',frameon=False,handletextpad=0.4)
ax=axes[2]
for kind,label,color in groups:
 rows=[r for r in data if r['reference_feature']==kind]
 ax.scatter([r['oligoformer_scaled_score'] for r in rows],[int(r['guide_matched_genes_non_target']) for r in rows],s=21,c=color,linewidths=0.35,edgecolors='white')
ax.scatter([bought['oligoformer_scaled_score']],[int(bought['guide_matched_genes_non_target'])],marker='*',s=110,c='#dc8740',edgecolors='#6c3b18',linewidths=0.5,label='Purchased si-VEGF*')
ax.set_xlim(0.3,1.23);ax.set_xlabel('OligoFormer score (scaled)');ax.set_ylabel('Distinct non-target seed-matched genes');ax.set_title('Complete guide-seed annotation');ax.legend(loc='upper left',bbox_to_anchor=(0,-0.25),frameon=False)
for label,ax in zip(['a','b','c'],axes):ax.text(-0.15,1.09,label,transform=ax.transAxes,fontweight='bold',fontsize=12)
fig.subplots_adjust(left=0.055,right=0.99,bottom=0.27,top=0.87,wspace=0.53)
for suffix in ['png','pdf','svg']:fig.savefig(OUT/('candidate_v2_complete_predictions.'+suffix),dpi=300,metadata={'Creator':'siRNA-GPT; complete defined input set'})
plt.close(fig)
fonts=[]
for page in PdfReader(OUT/'candidate_v2_complete_predictions.pdf').pages:
 for ref in page['/Resources']['/Font'].get_object().values():
  font=ref.get_object();name=str(font.get('/BaseFont',''))
  descendants=font.get('/DescendantFonts',[])
  target=descendants[0].get_object() if descendants else font
  descriptor=target.get('/FontDescriptor');descriptor=descriptor.get_object() if descriptor else {}
  embedded=any(k in descriptor for k in ['/FontFile','/FontFile2','/FontFile3'])
  assert 'Arial' in name and embedded,(name,embedded)
  fonts.append({'base_font':name,'embedded':embedded})
value={'all_65_designs_included':True,'purchased_sequence_separate_marker':True,'independent_quality_scores':None,
 'no_nearfull_safety_or_accuracy_plot':True,'font_regular':str(regular),'font_bold':str(bold),'pdf_fonts':fonts,
 'source_new65_sha256':hashlib.sha256((P/'new_65_complete_table.json').read_bytes()).hexdigest(),
 'source_purchased_sha256':hashlib.sha256((P/'purchased_siVEGF_separate.json').read_bytes()).hexdigest()}
(OUT/'figure_checks.json').write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
(OUT/'CAPTION_EN.md').write_text('''# Descriptive candidate records, not experimental efficacy

**Figure. Revised candidate accounting and complete prediction/seed annotation.** (a) The original 104 siDirect 2.0 designs, the 65-design revised pool retained using recorded legacy near-full mismatch criteria, and the historical nine-design subset. These counts are nested, not independent groups. (b) Scaled OligoFormer predictions for all 65 designs, colored by reference-region annotation; the shaded interval is the annotated coding sequence of NM_003376.6. (c) Complete guide mer7m8 annotation for all 65 designs plus the separately purchased si-VEGF, using one representative annotated 3prime UTR per gene for 19,415 genes, zero mismatches and no indels; VEGFA is excluded from the displayed distinct-gene count. Scores are multiplied by the official factor 1.341, may exceed one, and are not measured knockdown percentages or calibrated probabilities. Seed matches are potential sequence interactions, not experimentally demonstrated off-target effects. *The purchased sequence is interpreted conditionally from the documented strand order; its N3 chemistry and conjugated product efficacy are not modeled. Literature sequence entries are not plotted as zero-scored controls. Near-full checks were completed only for the five coding-region designs and purchased sequence; the 60 UTR designs were not scanned in this batch and are not certified clear. No independent scientific quality score or superiority claim is shown.
''',encoding='utf-8',newline='\n')
print(json.dumps(value,ensure_ascii=False))
