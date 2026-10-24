"""Independent read-only comparisons of saved counts, gene mapping and protected older assets."""
import csv,gzip,hashlib,json,zipfile
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'research/2026-10-24_candidate_v2'
OLD=Path(r'C:\Users\86182\.codex\.chatgpt-projects\g-p-6a82e08661e081919f3434650ae4f35c\analysis\ARPE19_candidates_20261016')
def read(p):
 op=gzip.open if str(p).endswith('.gz') else open
 with op(p,'rt',encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter='\t'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 model={r['candidate_id']:r for phase in ['oligo_pilot_02','oligo_remaining'] for r in json.loads((P/phase/'result.json').read_text(encoding='utf-8'))['rows']}
 scores=[]
 for old in read(ROOT/'data/historical_scores.tsv'):
  r=model[old['candidate_id']];difference=abs(float(old['oligoformer_scaled_score'])-r['oligoformer_scaled_score'])
  assert difference<1e-7 and int(old['official_func_filter'])==r['official_func_filter']
  scores.append({'candidate_id':old['candidate_id'],'absolute_scaled_score_difference':difference,'same_official_flag':True})
 prior={(r['candidate_id'],r['gene_id']):int(r['seed_site_count']) for r in read(ROOT/'data/historical_seed_matches.tsv')}
 new={}
 for cid in {c for c,g in prior}:
  phase='seed_pilot_02' if cid=='VEGFA_SD_1552' else 'seed_remaining'
  for r in read(P/phase/(cid+'__guide__counts.tsv.gz')):
   if int(r['seed_site_count'])>0:new[(cid,r['gene_id'])]=int(r['seed_site_count'])
 assert new==prior and len(new)==14524
 mapping=defaultdict(set);symbols=defaultdict(set)
 for r in read(OLD/'prepared/refseq_all_transcript_gene_loci.tsv'):
  mapping[r['transcript_id']].add(r['gene_id']);symbols[r['gene_id']].add(r['symbol'])
 near_checks=[];potential_matches=[]
 for phase in ['nearfull_pilot','nearfull_CDS_remaining']:
  summary=read(P/phase/'summary.tsv')
  for f in (P/phase).glob('*__hits.tsv.gz'):
   hits=read(f);cid,role,kind=f.name.removesuffix('__hits.tsv.gz').split('__')
   for h in hits:
    genes=mapping.get(h['transcript_id'],set());expected=';'.join(sorted(genes)) if genes else 'UNKNOWN_MAPPING'
    assert h['gene_ids']==expected
    if int(h['mismatches'])<=1 and (genes-{'7422'} or not genes):
     potential_matches.append({**h,'gene_symbols':';'.join(sorted({s for g in genes for s in symbols[g]})) or 'UNKNOWN'})
   for mm in [0,1,2]:
    observed=next(x for x in summary if (x['candidate_id'],x['strand_role'],x['query_kind'],int(x['max_mismatches']))==(cid,role,kind,mm))
    h=[h for h in hits if int(h['mismatches'])<=mm];gene_union=set().union(*(mapping.get(x['transcript_id'],set()) for x in h)) if h else set()
    unknown={x['transcript_id'] for x in h if x['transcript_id'] not in mapping}
    assert len(h)==int(observed['site_count']) and len(gene_union-{'7422'})==int(observed['non_target_gene_n']) and len(unknown)==int(observed['unknown_mapping_transcript_n'])
   near_checks.append({'query':f.name,'all_site_gene_mappings_and_0_1_2mm_summaries_match':True})
 protected=json.loads((ROOT/'research/2026-10-24_followup/offline/verification_02/protected_assets.json').read_text(encoding='utf-8'))
 checks={name:sha(ROOT/name)==value for name,value in protected.items()};assert all(checks.values())
 # Verify the saved 20-transcript quantities against the retained vendor transcript table.
 transcripts=read(P/'inputs/historical_VEGFA_transcript_TPM.tsv');vendor=read(OLD/'prepared/vendor_transcript_tpm.tsv')
 ids={r['transcript_id'] for r in transcripts}
 vendor_selected={r['transcript_id']:r for r in vendor if r.get('transcript_id') in ids}
 tpm_check=[]
 for r in transcripts:
  if r['transcript_id'] not in vendor_selected:raise ValueError('No vendor transcript row')
  v=vendor_selected[r['transcript_id']]
  for sample in ['Hyp1','Hyp2','Hyp3','Hyp4','Nor1','Nor2','Nor3','Nor4']:assert float(r[sample])==float(v[sample])
  tpm_check.append(r['transcript_id'])
 value={'status':'PASS','old_nine_scores':scores,'old_nine_14524_positive_seed_counts_exact':True,
  'nearfull_all_24_gene_summaries_independently_recounted':near_checks,'protected_prior_assets':checks,
  'historical_20_transcript_TPM_verified_against_retained_vendor_table':tpm_check,
  'transcript_TPM_limit':'Historical estimated transcript quantities; not direct read coverage of the siRNA target region; no state risk reranking',
  'new_API_calls':0,'independent_human_scores':None}
 (P/'independent_record_checks.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
 with (P/'CDS_potential_near_matches_0or1mm.tsv').open('w',encoding='utf-8-sig',newline='') as f:
  if potential_matches:
   w=csv.DictWriter(f,fieldnames=list(potential_matches[0]),delimiter='\t');w.writeheader();w.writerows(potential_matches)
 print(json.dumps({'status':'PASS','old_nine_max_difference':max(r['absolute_scaled_score_difference'] for r in scores),'old_seed_positive_rows':len(prior),'near_queries_verified':len(near_checks),'TPM_rows_verified':len(tpm_check)},ensure_ascii=False))
if __name__=='__main__':main()
