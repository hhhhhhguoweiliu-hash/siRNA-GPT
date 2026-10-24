"""Read-only sequence/source checks and publication tables. No scientific models."""
import csv,hashlib,io,json,zipfile,xml.etree.ElementTree as ET
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'research/2026-10-24_followup'
PAPERS=ROOT/'references/vegfa_experiments_20261024'

def save(name,value):
 (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')

def table(name,rows):
 with (OUT/name).open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(rows)

def rc(seq):return seq.translate(str.maketrans('ACGT','TGCA'))[::-1]

def main():
 OUT.mkdir(exist_ok=True);(OUT/'originals').mkdir(exist_ok=True)
 source=Path(r'D:\WHY\课题\框架核酸逻辑门放大\purchase\序列合成.docx')
 raw=source.read_bytes();(OUT/'originals/purchased_sequence_spec_original.docx').write_bytes(raw)
 ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
 with zipfile.ZipFile(io.BytesIO(raw)) as z:
  tree=ET.fromstring(z.read('word/document.xml'));blocks=[]
  for i,node in enumerate(tree.find('w:body',ns)):
   if node.tag.endswith('}tbl'):
    for j,row in enumerate(node.findall('w:tr',ns)):
     blocks.append({'body_block_0based':i,'table_row_0based':j,'cells':[''.join(t.text or '' for t in c.findall('.//w:t',ns)) for c in row.findall('w:tc',ns)]})
   else:
    text=''.join(t.text or '' for t in node.findall('.//w:t',ns))
    if text:blocks.append({'body_block_0based':i,'text':text})
 save('purchase_document_extraction.json',{'source_path':str(source),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'reading_method':'Original OOXML paragraphs and table cells; no visual-layout claim','blocks':blocks})
 fasta={};key=None
 for line in (ROOT/'data/VEGFA.fasta').read_text().splitlines():
  if line.startswith('>'):key=line[1:].split()[0];fasta[key]=''
  elif key:fasta[key]+=line.strip().upper()
 chains=[{'label':'document row 1','written_sequence':'GAUAGAGCAAGACAAGAAATT','written_annotation':'-N3（叠氮基团，用于点击化学）'},
         {'label':'document row 2','written_sequence':'UUUCUUGUCUUGCUCUAUCTT','written_annotation':None}]
 for c in chains:
  q=c['written_sequence'][:-2].replace('U','T');c.update(core19_for_alignment_only=q,assumption='Treat written order as 5prime-to-3prime and omit terminal TT for alignment only; chemical meaning and strand roles not assigned')
  hits=[]
  for accession,sequence in fasta.items():
   for orientation,query in [('as_written',q),('reverse_complement',rc(q))]:
    start=sequence.find(query)
    if start>=0:hits.append({'accession':accession,'orientation':orientation,'start_1based':start+1,'end_1based':start+19})
  c['exact_matches_assuming_written_direction']=hits
 save('purchased_siVEGF_sequence_check.json',{'raw_source':'originals/purchased_sequence_spec_original.docx','source_sha256':hashlib.sha256(raw).hexdigest(),
  'source_locator':'word/document.xml body block 1, rows 1 and 2 (zero-based)',
  'chains':chains,'rna19_parts_reverse_complementary':rc(chains[0]['core19_for_alignment_only'])==chains[1]['core19_for_alignment_only'],
  'reference_sha256':hashlib.sha256((ROOT/'data/VEGFA.fasta').read_bytes()).hexdigest(),'fixed_reference_count':len(fasta),
  'not_assigned':['guide/passenger roles','siRNA strand orientation confirmation','exact terminal chemistry and modification positions','supplier final specification or quality certificate'],
  'not_performed':['efficacy prediction','seed scan','wet experiment','order placement']})
 refs=[{'reference_id':'LIT_CHEN2013_TARGET2','doi':'10.2147/IJN.S39622','original_locator':'chen2013 xml-block-0009, Chemicals',
  'original_reported_type':'second target sequence; DNA alphabet; not a reported complete siRNA duplex',
  'original_sequence':'GCAGATTATGCGGATCAAA','sense_5to3_as_reported':None,'antisense_as_reported':None,'antisense_5to3_derived':None,
  'complete_duplex_reported':False,'end_or_modifications_reported_for_target':None,'source_file':'chen2013_text.txt','not_order_ready':True},
  {'reference_id':'LIT_OSIPOVA2020_DUPLEX27','doi':'10.3390/pharmaceutics12010039','original_locator':'osipova2020 xml-block-0011, Materials',
  'original_reported_type':'27-bp VEGF-A165 siRNA; sense 5prime-to-3prime and antisense 3prime-to-5prime explicitly printed',
  'original_sequence':None,'sense_5to3_as_reported':'CUUCCUACAGCACAACAAAUGUGAAUG','antisense_as_reported':'3prime-GAAGGAUGUCGUGUUGUUUACACUUAC-5prime',
  'antisense_5to3_derived':'GAAGGAUGUCGUGUUGUUUACACUUAC'[::-1],
  'derivation':'Reverse the characters of the printed 3prime-to-5prime antisense; do not reverse-complement it again',
  'complete_duplex_reported':True,'end_or_modifications_reported_for_target':'Cy5-labeled and unlabeled forms mentioned; terminal chemistry details not supplied in this paragraph',
  'source_file':'osipova2020_text.txt','not_order_ready':True}]
 for r in refs:
  rows=json.loads((PAPERS/r['source_file'].replace('_text.txt','_locators.json')).read_text(encoding='utf-8'))
  loc=r['original_locator'].split()[1].rstrip(',');paragraph=next(x for x in rows if x['locator']==loc)
  expected=r.get('original_sequence') or r['sense_5to3_as_reported']
  if expected not in paragraph['text']:raise ValueError('Reference sequence not in original paragraph')
  r['original_paragraph_sha256']=hashlib.sha256(paragraph['text'].encode()).hexdigest()
 save('literature_reference_sequences.json',refs)
 table('literature_reference_sequences.tsv',[{k:('NOT_REPORTED' if v is None else v) for k,v in {**r,'derivation':r.get('derivation','No derived full duplex generated')}.items()} for r in refs])
 trace=list(csv.DictReader((ROOT/'research/2026-10-23_candidate_provenance/candidate_trace.tsv').open(encoding='utf-8-sig'),delimiter='\t'))
 with zipfile.ZipFile(ROOT/'research/2026-10-23_literature/live_20261024/predeploy_existing_auto.zip') as z:
  report=json.loads(z.read('report.json'))
 report_rows={x['candidate_id']:x for x in report['rows']};expression={x['candidate_id']:x for x in report['expression_comparison']}
 full=[]
 for row in trace:
  cid=row['candidate_id'];start=int(row['core19_start_1based']);end=int(row['core19_end_1based'])
  region='CDS' if start>=497 and end<=1684 else '3prime_UTR' if start>1684 else '5prime_UTR_or_boundary'
  full.append({**row,'NM003376_6_feature':region,'CDS_reference_1based':'497-1684',
   'historical_review_flags':report_rows[cid]['review_flags'],
   'normoxia_detected_genes':expression[cid]['normoxia_detected_genes'],'hypoxia_detected_genes':expression[cid]['hypoxia_detected_genes'],
   'unmapped_genes':expression[cid]['unmapped_genes'],'experimental_knockdown_percent':'NOT_MEASURED_IN_THIS_PROJECT','order_ready':False})
 if len(full)!=9:raise ValueError('The complete nine must be retained')
 table('fixed_nine_complete_table.tsv',full);save('fixed_nine_complete_table.json',full)
 comparisons=list(csv.DictReader((ROOT/'research/2026-10-23_candidate_provenance/selection_104_audit.tsv').open(encoding='utf-8-sig'),delimiter='\t'))
 rule_steps=['SIDIRECT_LEGACY_DATABASE_MIN_MISMATCH_LT2','CORE_GC_OUTSIDE_WORKING_30_65','CORE_HOMOPOLYMER_GE4','NOT_COMMON_TO_ALL_20_VENDOR_TRANSCRIPT_CORES']
 remaining=comparisons;counts=[104]
 for rule in rule_steps:
  remaining=[x for x in remaining if rule not in x['recorded_exclusion_reasons']];counts.append(len(remaining))
 if counts!=[104,65,20,12,9]:raise ValueError(counts)
 table('104_rule_comparison_only.tsv',[{**r,'legacy_mismatch_ge2_only':'SIDIRECT_LEGACY_DATABASE_MIN_MISMATCH_LT2' not in r['recorded_exclusion_reasons'],'not_a_new_active_candidate_pool':True} for r in comparisons])
 save('lightweight_method_checks.json',{'sequential_counts':counts,'all_nine_retained':True,'unchanged_candidate_ids':[r['candidate_id'] for r in trace],
  'CDS_count':sum(x['NM003376_6_feature']=='CDS' for x in full),'three_prime_UTR_count':sum(x['NM003376_6_feature']=='3prime_UTR' for x in full),
  'no_new_design_or_scoring':True,'source_trace_sha256':hashlib.sha256((ROOT/'research/2026-10-23_candidate_provenance/candidate_trace.tsv').read_bytes()).hexdigest()})
 print(json.dumps({'purchase_document_bytes':len(raw),'nine_table_rows':len(full),'literature_references':len(refs),'sequential_counts':counts}))

if __name__=='__main__':main()
