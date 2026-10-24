"""Prepare a complete new-version job from preserved originals; no model inference."""
import csv,hashlib,io,json,re,sys,zipfile
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'research/2026-10-24_candidate_v2'
OLD=Path(r'C:\Users\86182\.codex\.chatgpt-projects\g-p-6a82e08661e081919f3434650ae4f35c\analysis\ARPE19_candidates_20261016')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for part in iter(lambda:f.read(4*1024*1024),b''):h.update(part)
 return h.hexdigest()
def save(name,value):
 p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def table(name,rows):
 p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t');w.writeheader();w.writerows(rows)
def fasta(text):
 result={}
 for block in text.split('>')[1:]:
  lines=block.splitlines();result[lines[0].split()[0]]=''.join(lines[1:]).upper().replace('T','U')
 return result
def rc(seq):return seq.translate(str.maketrans('ACGUT','UGCAA'))[::-1]
def main():
 if (OUT/'inputs/job_all.json').exists():raise SystemExit('Do not overwrite an existing prepared input set')
 with zipfile.ZipFile(ROOT/'research/2026-10-23_candidate_provenance/historical_evidence.zip') as z:
  raw=z.read('prepared/candidates_all.tsv')
  assert raw==(OLD/'prepared/candidates_all.tsv').read_bytes()
  allrows=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig')),delimiter='\t'))
  refs=fasta(z.read('prepared/VEGFA_vendor_versions.fasta').decode('utf-8-sig'))
  (OUT/'inputs').mkdir(parents=True,exist_ok=True)
  (OUT/'inputs/original_all_104.tsv').write_bytes(raw)
  (OUT/'inputs/fixed_VEGFA_references.fasta').write_bytes(z.read('prepared/VEGFA_vendor_versions.fasta'))
 primary=refs['NM_003376.6'];assert len(primary)==3609
 selected=[];decisions=[]
 for r in allrows:
  keep=min(int(r['vendor_min_mismatches_guide_19nt_g2g20']),int(r['vendor_min_mismatches_passenger_19nt_g2g20']))>=2
  decisions.append({**r,'v2_keep':keep,'v2_decision':'RETAIN_LEGACY_SIDIRECT_BOTH_STRANDS_GE2' if keep else 'EXCLUDE_LEGACY_SIDIRECT_NEAR_FULL_LT2',
   'old_GC_homopolymer_coverage_conditions_used_as_hard_filters':False})
  if keep:selected.append(r)
 assert len(allrows)==104 and len(selected)==65
 table('all_104_decisions.tsv',decisions)
 records=[]
 for r in selected:
  p=int(r['target_start_1based'])+1 # zero-based 19bp sense-core start: window start + 2
  g=r['guide_paired_core_19nt_5to3'];s=r['passenger_paired_core_19nt_5to3']
  assert primary[p:p+19]==s and rc(g)==s
  records.append({'candidate_id':r['candidate_id'],'origin':'V2_DESIGN_FROM_ORIGINAL_104',
   'guide21_original':r['guide_21nt_RNA_5to3'],'passenger21_original':r['passenger_21nt_RNA_5to3'],
   'guide_core19_5to3':g,'passenger_core19_5to3':s,'core_start_1based':p+1,'core_end_1based':p+19,
   'window23_start_1based':int(r['target_start_1based']),'window23_end_1based':int(r['target_end_1based']),
   'reference_feature':'CDS' if 497<=p+1 and p+19<=1684 else '3prime_UTR' if p+1>1684 else '5prime_UTR_or_boundary',
   'old_working_pool_pass':r['working_pool_pass'],'old_exclusion_reason':r['exclusion_reason'],
   'legacy_sidirect_guide_min_mismatches_g2g20':int(r['vendor_min_mismatches_guide_19nt_g2g20']),
   'legacy_sidirect_passenger_min_mismatches_g2g20':int(r['vendor_min_mismatches_passenger_19nt_g2g20']),
   'seed_tm_guide_C_as_printed':r['seed_tm_guide_C'],'seed_tm_passenger_C_as_printed':r['seed_tm_passenger_C'],
   'printed_Tm_boundary_21_5':float(r['seed_tm_guide_C'])==21.5 or float(r['seed_tm_passenger_C'])==21.5,
   'guide_GC_percent':100*sum(x in 'GC' for x in g)/19,'guide_max_homopolymer':max(len(x.group()) for x in re.finditer(r'(.)\1*',g)),
   'strand_assignment_basis':'Original siDirect duplex; 5prime-to-3prime validated in prior audit',
   'original_modification':'Original design bases only; no final synthesis chemistry',
   'source_record':'inputs/original_all_104.tsv'})
 purchased=json.loads((ROOT/'data/user_ordered_sequences/20261024/sequence_records.json').read_text(encoding='utf-8'))
 pair=next(x for x in purchased['sequence_checks'] if x['label']=='si-vegf')
 s=pair['strand1_as_written'][:-2];g=pair['strand2_as_written'][:-2];assert len(g)==len(s)==19 and rc(g)==s
 assert primary.count(s)==1;p=primary.index(s)
 records.append({'candidate_id':'USER_PURCHASED_siVEGF','origin':'USER_PURCHASED_SEPARATE',
  'guide21_original':pair['strand2_as_written'],'passenger21_original':pair['strand1_as_written'],
  'guide_core19_5to3':g,'passenger_core19_5to3':s,'core_start_1based':p+1,'core_end_1based':p+19,
  'window23_start_1based':None,'window23_end_1based':None,'reference_feature':'CDS',
  'old_working_pool_pass':'NOT_MEMBER','old_exclusion_reason':'NOT_MEMBER',
  'legacy_sidirect_guide_min_mismatches_g2g20':None,'legacy_sidirect_passenger_min_mismatches_g2g20':None,
  'seed_tm_guide_C_as_printed':None,'seed_tm_passenger_C_as_printed':None,'printed_Tm_boundary_21_5':False,
  'guide_GC_percent':100*sum(x in 'GC' for x in g)/19,'guide_max_homopolymer':max(len(x.group()) for x in re.finditer(r'(.)\1*',g)),
  'strand_assignment_basis':'DERIVED_CONDITIONAL: written order assumed 5prime-to-3prime; row2 core reverse-complements reference sense; not vendor-confirmed roles',
  'original_modification':'Row1 suffix -N3 (azide); TT characters retained; exact chemistry/attachment and assembled construct not independently verified',
  'source_record':'data/user_ordered_sequences/20261024/sequence_synthesis_original.docx'})
 coverage=[];queries=[];strands=[]
 for r in records:
  p=r['core_start_1based']-1;r['mRNA_context_57nt']='X'*max(0,19-p)+primary[max(0,p-19):p+38]+'X'*max(0,p+38-len(primary))
  assert len(r['mRNA_context_57nt'])==57 and r['mRNA_context_57nt'][19:38]==r['passenger_core19_5to3']
  matches=[]
  for acc,seq in refs.items():
   hits=[m.start()+1 for m in re.finditer('(?='+r['passenger_core19_5to3']+')',seq)]
   coverage.append({'candidate_id':r['candidate_id'],'reference_accession':acc,'core_matches':len(hits),'starts_1based':';'.join(map(str,hits)) or 'NONE'})
   if hits:matches.append(acc)
  r['fixed_transcript_matches']=len(matches);r['matched_fixed_transcript_ids']=';'.join(matches)
  for role in ['guide','passenger']:
   core=r[role+'_core19_5to3'];raw21=r[role+'21_original']
   strands.append({'candidate_id':r['candidate_id'],'strand_role':role,'sequence_core19_RNA':core,'original21_as_written':raw21,'origin':r['origin']})
   for kind,seq in [('paired_core19',core),('sidirect_g2g20',raw21[1:20].replace('T','U'))]:
    assert len(seq)==19
    queries.append({'candidate_id':r['candidate_id'],'strand_role':role,'query_kind':kind,'strand19_RNA':seq,'target_pattern_DNA':rc(seq).replace('U','T')})
 table('inputs/all_66_inputs.tsv',records);table('transcript_coverage_all_1320.tsv',coverage)
 table('inputs/seed_all_132.tsv',strands);table('inputs/nearfull_all_264.tsv',queries)
 pilot_ids=['USER_PURCHASED_siVEGF','VEGFA_SD_1552']
 pilot=[next(r for r in records if r['candidate_id']==cid) for cid in pilot_ids]
 base={'reference':'NM_003376.6','seed':42,'cpu_threads':2,'scientific_protocol_sha256':sha(OUT/'PROTOCOL.md')}
 for name,items in [('job_all.json',records),('job_pilot.json',pilot)]:save('inputs/'+name,{**base,'candidates':items})
 table('inputs/seed_pilot_4.tsv',[r for cid in pilot_ids for r in strands if r['candidate_id']==cid])
 table('inputs/nearfull_pilot_8.tsv',[r for cid in pilot_ids for r in queries if r['candidate_id']==cid])
 save('planned_units.json',{'prepared_utc':datetime.now(timezone.utc).isoformat(),'scientific_protocol_sha256':base['scientific_protocol_sha256'],
  'design_candidates':65,'purchased_candidates':1,'oligo_units':66,'seed_units':132,'nearfull_queries':264,
  'candidate_ids':[r['candidate_id'] for r in records],'pilot_ids':pilot_ids,'literature_reference_entries':2,'literature_scoring':'NOT_PLANNED_TARGET_ONLY_OR_27BP_NOT_AUTOMATICALLY_TRIMMED'})
 manifest=[]
 for item in json.loads((ROOT/'research/2026-10-23_candidate_provenance/external_assets_check.json').read_text(encoding='utf-8')):
  p=OLD/item['path'];actual=sha(p);assert actual==item['expected_sha256']
  manifest.append({'path':str(p),'bytes':p.stat().st_size,'sha256':actual,'matches_previous_verified_record':True})
 for name in ['prepared/refseq_all_transcripts.fasta','prepared/refseq_all_transcript_gene_loci.tsv','prepared/utr_manifest_representative.tsv']:
  p=OLD/name;manifest.append({'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p),'matches_previous_verified_record':'NEW_READ_FINGERPRINT_BINDING_EXISTING_REFERENCE'})
 save('input_assets.json',manifest)
 save('reused_previous_batch.json',{'commit':'f60add9','three_papers':'references/vegfa_experiments_20261024/sources.json','actual_day7_run':'library_demo_20261024_052657_5a7974',
  'actual_day7_original_zip_sha256':sha(ROOT/'research/2026-10-24_followup/live/actual_demo_original.zip'),'new_API_calls':0,
  'not_relabelled_as_new_execution':True})
 print(json.dumps({'design':65,'purchased':1,'seed_units':132,'nearfull_queries':264,'asset_sha_verified':True}))
if __name__=='__main__':main()
