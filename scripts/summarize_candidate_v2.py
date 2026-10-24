"""Validate complete declared units and create transparent tables; no new predictor or risk weights."""
import csv,gzip,hashlib,json,math,statistics,sys,zipfile
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'research/2026-10-24_candidate_v2'
OLD=Path(r'C:\Users\86182\.codex\.chatgpt-projects\g-p-6a82e08661e081919f3434650ae4f35c\analysis\ARPE19_candidates_20261016')
def read(p):
 opener=gzip.open if str(p).endswith('.gz') else open
 with opener(p,'rt',encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter='\t'))
def save(name,value):(OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def table(name,rows):
 with (OUT/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t');w.writeheader();w.writerows(rows)
def fasta_selected(p,wanted=None):
 result={};key=None;pieces=[]
 with p.open(encoding='utf-8-sig') as f:
  for line in f:
   if line.startswith('>'):
    if key is not None and (wanted is None or key in wanted):result[key]=''.join(pieces)
    key=line[1:].split()[0];pieces=[]
   elif wanted is None or key in wanted:pieces.append(line.strip().upper().replace('U','T'))
  if key is not None and (wanted is None or key in wanted):result[key]=''.join(pieces)
 return result
def main():
 job=json.loads((OUT/'inputs/job_all.json').read_text(encoding='utf-8'));inputs=job['candidates'];byid={r['candidate_id']:r for r in inputs}
 oligo={};seed={};near={};states=[];seed_checks=[]
 for phase in ['oligo_pilot_02','oligo_remaining']:
  result=json.loads((OUT/phase/'result.json').read_text(encoding='utf-8'))
  assert result['status']=='COMPLETE' and result['planned_units']==result['completed_units']
  assert result['protocol_sha256']==hashlib.sha256((OUT/'PROTOCOL.md').read_bytes()).hexdigest()
  assert json.loads((OUT/phase/'official_loader_parity.json').read_text(encoding='utf-8'))['exact_equality']
  for row in result['rows']:
   cid=row['candidate_id'];assert cid not in oligo
   assert row['guide_core19_5to3']==byid[cid]['guide_core19_5to3'] and row['mRNA_context_57nt']==byid[cid]['mRNA_context_57nt']
   assert abs(row['raw_class1']*1.341-row['oligoformer_scaled_score'])<1e-12
   oligo[cid]=row;states.append({'candidate_id':cid,'unit':'oligo','strand':'guide','status':'COMPLETED','evidence':phase+'/result.json'})
 assert set(oligo)==set(byid) and len(oligo)==66
 utrs=fasta_selected(OLD/'prepared/refseq_utr3_representative.fasta')
 manifest=read(OLD/'prepared/utr_manifest_representative.tsv');genes={r['gene_id'] for r in manifest}
 assert len(utrs)==len(genes)==19415
 for phase in ['seed_pilot_02','seed_remaining']:
  for row in read(OUT/phase/'summary.tsv'):
   cid,role=row['candidate_id'],row['strand_role'];key=(cid,role);assert key not in seed
   counts=read(OUT/phase/(cid+'__'+role+'__counts.tsv.gz'));sites=read(OUT/phase/(cid+'__'+role+'__sites.tsv.gz'))
   assert len(counts)==19415 and {r['gene_id'] for r in counts}==genes and len({r['gene_id'] for r in counts})==19415
   observed=Counter()
   for hit in sites:
    s,e=int(hit['start']),int(hit['end']);ref=utrs[hit['transcript_id']]
    assert ref[s-1:e]==hit['target_motif_DNA'] and e-s+1==7
    observed[hit['gene_id']]+=1
   assert all(int(r['seed_site_count'])==observed[r['gene_id']] for r in counts)
   assert sum(observed.values())==int(row['seed_sites_all']) and sum(v>0 for v in observed.values())==int(row['matched_genes_all'])
   seed[key]=row;seed_checks.append({'candidate_id':cid,'strand':role,'all_19415_genes_including_zeros':True,'all_sites_exact_reference_matches':True,'site_rows':len(sites)})
   states.append({'candidate_id':cid,'unit':'seed_mer7m8','strand':role,'status':'COMPLETED','evidence':phase+'/'+cid+'__'+role+'__counts.tsv.gz'})
 assert len(seed)==132 and all((cid,role) in seed for cid in byid for role in ['guide','passenger'])
 hits_all=[]
 for phase in ['nearfull_pilot','nearfull_CDS_remaining']:
  for row in read(OUT/phase/'summary.tsv'):
   cid,role,kind=row['candidate_id'],row['strand_role'],row['query_kind'];key=(cid,role,kind)
   if row['max_mismatches']=='2':
    assert key not in near;near[key]=[]
    hits=read(OUT/phase/('__'.join(key)+'__hits.tsv.gz'));assert len(hits)==int(row['site_count'])
    hits_all.extend(hits)
    states.append({'candidate_id':cid,'unit':'nearfull_'+kind,'strand':role,'status':'COMPLETED','evidence':phase+'/'+'__'.join(key)+'__hits.tsv.gz'})
  for row in read(OUT/phase/'summary.tsv'):near[(row['candidate_id'],row['strand_role'],row['query_kind'])].append(row)
 assert len(near)==24 and all(len(rows)==3 for rows in near.values())
 refs=fasta_selected(OLD/'prepared/refseq_all_transcripts.fasta',{h['transcript_id'] for h in hits_all})
 for hit in hits_all:
  s,e=int(hit['start']),int(hit['end']);seq=refs[hit['transcript_id']][s-1:e];pattern=hit['target_pattern_DNA']
  assert len(seq)==len(pattern)==19 and sum(a!=b for a,b in zip(seq,pattern))==int(hit['mismatches'])<=2
 for cid in byid:
  for role in ['guide','passenger']:
   for kind in ['paired_core19','sidirect_g2g20']:
    if (cid,role,kind) not in near:states.append({'candidate_id':cid,'unit':'nearfull_'+kind,'strand':role,'status':'NOT_RUN_BUDGET_SCOPE','evidence':'RUN_SCOPE_DECISION.json'})
 assert Counter(x['status'] for x in states)=={'COMPLETED':222,'NOT_RUN_BUDGET_SCOPE':240}
 table('planned_units_actual_states.tsv',sorted(states,key=lambda x:(x['candidate_id'],x['unit'],x['strand'])))
 rows=[]
 for inp in inputs:
  cid=inp['candidate_id'];row={**inp,'oligo_status':'COMPLETED_REAL_NEW','oligo_raw_class1':oligo[cid]['raw_class1'],
   'oligoformer_scaled_score':oligo[cid]['oligoformer_scaled_score'],'official_func_filter':oligo[cid]['official_func_filter']}
  for role in ['guide','passenger']:
   s=seed[(cid,role)]
   for k in ['target_motif_DNA','seed_sites_all','matched_genes_all','seed_sites_non_target','matched_genes_non_target']:row[role+'_'+k]=s[k]
   for kind in ['paired_core19','sidirect_g2g20']:
    result=near.get((cid,role,kind))
    for mm in [0,1,2]:
     r=next((r for r in result if int(r['max_mismatches'])==mm),None) if result else None
     for k in ['non_target_gene_n','unknown_mapping_transcript_n']:row[role+'_'+kind+'_mm'+str(mm)+'_'+k]=int(r[k]) if r else 'NOT_RUN'
  row['nearfull_status']='COMPLETED_4_QUERIES' if all((cid,role,kind) in near for role in ['guide','passenger'] for kind in ['paired_core19','sidirect_g2g20']) else 'NOT_RUN_BUDGET_SCOPE'
  row['experimental_knockdown']='NOT_MEASURED_IN_THIS_PROJECT';row['final_synthesis_order']='NOT_CONFIRMED';rows.append(row)
 design=[r for r in rows if r['origin'].startswith('V2')];purchased=[r for r in rows if r['origin']=='USER_PURCHASED_SEPARATE']
 eligible=[]
 for r in design:
  reasons=[]
  if r['reference_feature']!='CDS':reasons.append('UTR_OUTSIDE_THIS_BATCH_COMPLETE_NEARFULL_SCOPE')
  if r['official_func_filter']!=0:reasons.append('OFFICIAL_SEQUENCE_FLAG_REQUIRES_REVIEW')
  if r['nearfull_status'].startswith('COMPLETED'):
   for role in ['guide','passenger']:
    for kind in ['paired_core19','sidirect_g2g20']:
     if r[role+'_'+kind+'_mm1_non_target_gene_n']>0:reasons.append('NON_TARGET_NEAR_MATCH_0_OR_1MM')
     if r[role+'_'+kind+'_mm1_unknown_mapping_transcript_n']>0:reasons.append('UNKNOWN_MAPPING_NEAR_MATCH')
  r['provisional_review_basis']=';'.join(dict.fromkeys(reasons)) if reasons else 'ELIGIBLE_FOR_PROVISIONAL_NONOVERLAPPING_CDS_REVIEW'
  if not reasons:eligible.append(r)
 chosen=[]
 for r in sorted(eligible,key=lambda r:-r['oligoformer_scaled_score']):
  overlaps=any(max(r['core_start_1based'],s['core_start_1based'])<=min(r['core_end_1based'],s['core_end_1based']) for s in chosen)
  if overlaps:r['provisional_review_basis']='OVERLAPS_HIGHER_SCORE_SELECTED_CDS_ALTERNATIVE'
  elif len(chosen)<3:chosen.append(r);r['provisional_review_basis']='PROVISIONAL_REVIEW_CANDIDATE_NOT_EXPERIMENTALLY_VALIDATED'
 table('new_65_complete_table.tsv',design);save('new_65_complete_table.json',design)
 table('purchased_siVEGF_separate.tsv',purchased);save('purchased_siVEGF_separate.json',purchased)
 save('provisional_small_trial_candidates.json',{'method':'Preregistered transparent CDS review rule; no risk-weight fusion; not a validated efficacy optimum','new_candidate_ids':[r['candidate_id'] for r in chosen],
  'maximum_requested':3,'actual_nonoverlapping_eligible_count':len(chosen),'purchased_reference_separate':purchased[0],
  'not_a_final_synthesis_order':True,'remaining_nearfull_UTR_queries':240})
 # Preserve original literature sequence forms, without assigning scores to incompatible/target-only inputs.
 literature=json.loads((ROOT/'research/2026-10-24_followup/literature_reference_sequences.json').read_text(encoding='utf-8'))
 for r in literature:r['new_model_score']=None;r['new_seed_scan']=None;r['new_computation_status']='NOT_PLANNED_TARGET_ONLY' if not r['complete_duplex_reported'] else 'NOT_PLANNED_27BP_NOT_AUTOMATICALLY_TRIMMED'
 save('literature_references_separate.json',literature)
 old=read(ROOT/'data/historical_scores.tsv');oldids={r['candidate_id'] for r in old}
 comparisons=[]
 for r in old:
  new=oligo[r['candidate_id']];fields=[k for k in r if 'score' in k or 'raw' in k]
  comparisons.append({'candidate_id':r['candidate_id'],'historical_values':{k:r[k] for k in fields},'new_raw_class1':new['raw_class1'],'new_scaled_score':new['oligoformer_scaled_score']})
 save('old_nine_score_readonly_comparison.json',comparisons)
 timing={phase:json.loads((OUT/'execution'/(phase+'.json')).read_text(encoding='utf-8')) for phase in ['oligo_pilot','oligo_pilot_02','seed_pilot','seed_pilot_02','nearfull_pilot','oligo_remaining','seed_remaining','nearfull_CDS_remaining']}
 save('execution_timings.json',timing)
 # Historical transcript abundance is annotation only, retained verbatim and checked against its saved vendor table.
 raw=(OLD/'prepared/VEGFA_transcript_TPM.tsv').read_bytes();(OUT/'inputs/historical_VEGFA_transcript_TPM.tsv').write_bytes(raw)
 checks={'all_104_decisions_retained':len(read(OUT/'all_104_decisions.tsv'))==104,'new_design_pool_all_65':len(design)==65,'purchased_separate_one':len(purchased)==1,
  'oligo_unique_complete_66':len(oligo)==66,'seed_unique_complete_132':len(seed)==132,'all_seed_gene_rows_including_zeros':132*19415,
  'all_seed_sites_verified':all(r['all_sites_exact_reference_matches'] for r in seed_checks),'nearfull_declared_scope_complete_24':len(near)==24,
  'nearfull_unexecuted_explicit_240':sum(r['status']=='NOT_RUN_BUDGET_SCOPE' for r in states)==240,'all_scanned_nearfull_sites_rechecked':len(hits_all),
  'old_nine_in_new_complete_pool':oldids.issubset(set(oligo)),'no_new_API_calls':True,'independent_human_scores':None}
 save('completion_audit.json',{'checks':checks,'seed_units':seed_checks,'new_design_regions':dict(Counter(r['reference_feature'] for r in design)),
  'total_seed_count_rows':132*19415,'total_seed_site_rows':sum(r['site_rows'] for r in seed_checks),'nearfull_site_rows':len(hits_all),
  'provisional_new_ids':[r['candidate_id'] for r in chosen],'nearfull_full_264_complete':False,'nearfull_current_24_scope_complete':True,
  'no_scientific_accuracy_or_experimental_efficacy_claim':True})
 print(json.dumps({'new_designs':len(design),'seed_count_rows':132*19415,'nearfull_queries_completed':24,'nearfull_queries_not_run':240,'provisional_new':[r['candidate_id'] for r in chosen]},ensure_ascii=False))
if __name__=='__main__':main()
