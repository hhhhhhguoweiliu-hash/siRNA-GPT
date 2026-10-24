"""Curated source-located evidence, not new experiments or model quality scores."""
import csv,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'references/vegfa_experiments_20261024';OUT=ROOT/'research/2026-10-24_followup'
def write(name,value):
 (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def main():
 rows=[
 {'paper':'Chen et al., 2013','doi':'10.2147/IJN.S39622','species_cells':'Human ARPE-19 retinal pigment epithelial cells',
  'target':'VEGF; three 19-base target sequences reported; second selected by authors under their conditions',
  'sequence_form':'DNA-alphabet target2 GCAGATTATGCGGATCAAA; not the reported full RNA duplex; missing strands/end chemistry not inferred',
  'delivery_dose':'Initial siRNA comparison: Lipofectamine 2000, 48 h. Delivery study: 3 mol% PEGylated or RGD-PEGylated liposomes; 40, 80 or 160 nM in dose experiments. Serum-free exposure 4 h, then fresh medium.',
  'readouts_time':'Semiquantitative RT-PCR/gel-band VEGF mRNA normalized to GAPDH at 24/48/72 h; secreted VEGF ELISA in medium, measured during 72 h. Dose comparison reported at 48 h. Do not relabel semiquantitative PCR as qPCR.',
  'controls':'Untreated cells; non-targeting control siRNA with corresponding carriers; Lipofectamine comparison',
  'reported_result_scope':'Authors report target2 as most effective of three tested; their carrier/dose effects are published results, not measurements for the project nine. No numerical effect digitized from figures.',
  'locators':['chen2013 xml-block-0009 Chemicals and reagents','chen2013 xml-block-0017 RNA isolation and semiquantitative RT-PCR','chen2013 xml-block-0018 ELISA','chen2013 xml-block-0026 mRNA/protein results'],
  'limits_missing':'No PDF pagination assigned to XML. Oxygen-state condition not supplied in these extracted experimental paragraphs; no assumption of hypoxia. Exact complete duplex/end chemistry for target2 is not reconstructed.'},
 {'paper':'Osipova et al., 2020','doi':'10.3390/pharmaceutics12010039','species_cells':'Human ARPE-19 retinal epithelial cells',
  'target':'VEGF-A165; authors report a 27-bp siRNA',
  'sequence_form':'Sense 5prime-CUUCCUACAGCACAACAAAUGUGAAUG-3prime; antisense 3prime-GAAGGAUGUCGUGUUGUUUACACUUAC-5prime, exactly as printed. Reverse the printed antisense to express 5prime-to-3prime, explicitly derived. Not trimmed to a 19-nt tool input.',
  'delivery_dose':'mRNA: 4e4 cells/well, 24-well; 0.05 nmol siRNA + 33.5 microgram polypeptide particles, polymer/siRNA mass ratio 4:1, 500 microlitre serum-free DMEM-F12, author-stated 100 nM; 4 h exposure + 44 h after medium change. Protein: 8e5 cells/well, 6-well; 0.8 nmol in 2 mL; ratio 4:1. Preserve these distinct assay conditions.',
  'readouts_time':'mRNA qRT-PCR normalized to GAPDH at 48 h (2 days); VEGF protein Western blot at 5 days. The 7-day time point in particle-stability/DLS section is not a day-7 knockdown measurement.',
  'controls':'Scrambled 27-bp siControl with particles; empty-particle control in protein results',
  'reported_result_scope':'Authors report about 60%, 82%, 71% mRNA reductions for KEF1, KEI1, KEI2 at 48 h; about 60% protein suppression for KEI2 at 5 days. These are reported paper findings under distinct conditions, not new project data.',
  'locators':['osipova2020 xml-block-0011 Materials','osipova2020 xml-block-0033 VEGF gene silencing','osipova2020 xml-block-0034 Gene expression','osipova2020 xml-block-0035 Western blot','osipova2020 xml-block-0050 Particle stability','osipova2020 xml-block-0052 mRNA results','osipova2020 xml-block-0054 protein results'],
  'limits_missing':'Cy5-labeled and unlabeled forms mentioned, but exact terminal/modification specification not established by the sequence paragraph. The paper prints 0.05 nmol, 33.5 microgram particles and 4:1 together; these quantities may not reconcile using the printed 27-bp duplex mass and must be checked before transferring a protocol, not silently corrected. No transplantation of carrier efficacy to the nine candidates; no day-7 value.'},
 {'paper':'Kleinman et al., 2008','doi':'10.1038/nature06765','species_cells':'Laser-induced CNV in 6-8-week-old mice; wild-type and Tlr3-deficient comparisons, other genetic controls; human choroidal and other endothelial-cell assays. Not an ARPE-19 silencing study.',
  'target':'Non-targeted and targeted siRNAs; human VEGFA-targeting hVegfa and mouse Vegfa/VEGFR1 examples test specificity and TLR3 mechanisms',
  'sequence_form':'Chemical sequences/modifications are assigned by the authors to Supplementary Table, absent from the acquired manuscript. Do not reconstruct Bevasiranib or full duplex sequences.',
  'delivery_dose':'Naked siRNA in siRNA buffer or PBS, intravitreal total volume 1 microlitre (Methods); Fig.3 targeted-siRNA experiments specify 1 microgram. Cholesterol-conjugated and 5prime-methoxy variants are separate conditions; Fig.1 also has 0.25 microgram Luc examples. Do not collapse them into one common dose.',
  'readouts_time':'CNV volume by confocal microscopy/isolectin B4; gene expression in mouse RPE/choroid by RT-PCR; immune cytokines by ELISA, surface TLR3/uptake assays. Global CNV endpoint day is not stated in acquired Methods; cited prior methods and missing supplementary information were not substituted. PDF p15 has assay-specific 1-day cell isolation and 3-day tissue preparation, not a universal CNV endpoint.',
  'controls':'Vehicle/buffer/PBS or no injection; Tlr3 knockout vs wild type; soluble TLR3 vs soluble TLR4/heat-denatured TLR3; anti-TLR3 vs IgG; target-matched vs mismatched mouse/human VEGFA and cholesterol/methoxy variants as separate comparisons',
  'reported_result_scope':'The tested extracellular siRNAs can suppress neovascularization through TLR3-dependent mechanisms; some targeted constructs lose apparent specificity without active intracellular delivery. Anti-angiogenic phenotype alone is not proof of specific VEGFA knockdown.',
  'locators':['kleinman2008_author_manuscript.pdf p1 version/supplement disclaimer','PDF p2-3 Fig.1 and surface TLR3','PDF p5-6 Fig.3 and targeted constructs','PDF p6-7 length experiments','PDF p10 Methods summary','PDF p13-15 Online Methods; p14 visually checked'],
  'limits_missing':'Institutional author manuscript, 15 pages, not publisher copy of record. Supplementary sequence table not obtained. Do not generalize to all siRNAs, all delivery systems, clinical efficacy or the project nine; no new TLR3 experiment required.'}
 ]
 for row in rows:
  row['evidence_type']='PUBLISHED_EXPERIMENT_NOT_PROJECT_MEASUREMENT'
  src=next(x for x in json.loads((P/'sources.json').read_text(encoding='utf-8'))['sources'] if x['doi']==row['doi'])
  row['source_file']=src['file'];row['source_sha256']=src['sha256'];row['source_url']=src['source_url']
  if src['file'].endswith('.txt'):
   text=(P/src['file']).read_text(encoding='utf-8')
   for loc in row['locators']:assert loc.split()[1] in text,loc
 write('experimental_literature_evidence.json',rows)
 with (OUT/'experimental_literature_evidence.tsv').open('w',encoding='utf-8-sig',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t');writer.writeheader()
  for row in rows:writer.writerow({k:'; '.join(v) if isinstance(v,list) else v for k,v in row.items()})
 nine=json.loads((OUT/'fixed_nine_complete_table.json').read_text(encoding='utf-8'))
 for row in nine:
  row['baseline_mappable_non_target_genes']=int(row['seed_matched_genes_excluding_VEGFA'])-row['unmapped_genes']
 write('fixed_nine_complete_table.json',nine)
 with (OUT/'fixed_nine_complete_table.tsv').open('w',encoding='utf-8-sig',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=list(nine[0]),delimiter='\t');writer.writeheader();writer.writerows(nine)
 sections=[('Sequences and reference coordinates',['candidate_id','target23_sense_DNA','guide21_RNA','passenger21_RNA','guide19_RNA','passenger19_RNA','design_window23_start_1based','design_window23_end_1based','core19_start_1based','core19_end_1based','guide_3prime_overhang','passenger_3prime_overhang','NM003376_6_feature']),
  ('Historical predicted scores and review flags',['candidate_id','oligo_raw_class1','oligo_scaled_score','oligo_official_func_filter','historical_review_flags','matched_fixed_transcripts','experimental_knockdown_percent']),
  ('Historical guide mer7m8 matches and baseline annotation',['candidate_id','guide_mer7m8_target_DNA','seed_sites_including_VEGFA','seed_matched_genes_including_VEGFA','seed_sites_excluding_VEGFA','seed_matched_genes_excluding_VEGFA','baseline_mappable_non_target_genes','unmapped_genes','normoxia_detected_genes','hypoxia_detected_genes'])]
 md=['# Complete fixed development pool: all nine candidates','','All sequences are written 5prime to 3prime. Coordinates are 1-based and inclusive on NM_003376.6; CDS 497-1684. The 23-nt design window and 19-nt paired core are distinct. The original 21-nt strands and their native two-base 3prime extensions are retained; these are design records, not a finalized chemical order.','','Machine-readable full table: [TSV](fixed_nine_complete_table.tsv) and [JSON](fixed_nine_complete_table.json), including original source, versions and input context.']
 for title,cols in sections:
  md+=['','## '+title,'','| '+' | '.join(cols)+' |','| '+' | '.join(['---']*len(cols))+' |']
  md+=['| '+' | '.join(str(row[k]).replace('|','/').replace('\n',' ') or 'None recorded' for k in cols)+' |' for row in nine]
 md+=['','## Interpretation','','The seed counts are sites and distinct genes, respectively. Mappable genes can be derived as non-target matched genes minus unmapped genes in the saved report; baseline-detected counts apply only to mapped genes in each state and must not be substituted for total matches. A gene can contain multiple sites. The baseline expression annotation is not siRNA-perturbation evidence.','','func_filter=4 denotes the historical official palindrome check for 3119, 3193 and 3502. The separate near-full-length review flag for 3535 is retained. A zero flag is not a safety certification. No candidate has a project-measured knockdown percentage. The development pool is not an unseen test set or a final experimental shortlist.']
 (OUT/'FIXED_NINE_TABLE.md').write_text('\n'.join(md)+'\n',encoding='utf-8',newline='\n')
 print('prepared 3 source-located literature rows and all-nine readable tables')
if __name__=='__main__':main()
