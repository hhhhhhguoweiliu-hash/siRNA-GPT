"""Recount all old/new sites against the same reference, and merge 264 statuses."""
import csv,gzip,hashlib,json
from collections import defaultdict,Counter
from pathlib import Path
from complete_nearfull_20261024 import ROOT,PRIOR,OUT,LEGACY,read,key,sha,save,write

def main():
 receipt=json.loads((OUT/'execution.json').read_text(encoding='utf-8'))
 assert receipt.get('exit_code')==0 and receipt['status']=='RETURNED'
 plan=read(PRIOR/'inputs/nearfull_all_264.tsv');bykey={key(r):r for r in plan}
 actual={};allhits=[];raw_records=[]
 phases=[PRIOR/'nearfull_pilot',PRIOR/'nearfull_CDS_remaining',OUT/'new_240']
 session=(phases[0]/'sessionInfo.txt').read_text(encoding='utf-8')
 for phase in phases:
  current=(phase/'sessionInfo.txt').read_text(encoding='utf-8')
  for version in ['R version 4.3.1','Biostrings_2.70.1','data.table_1.14.8','dplyr_1.1.3']:assert version in session and version in current
  summary=read(phase/'summary.tsv');keys={key(r) for r in summary}
  assert len(summary)==len(keys)*3
  for k in keys:
   assert k in bykey and k not in actual
   ss=[r for r in summary if key(r)==k];assert {int(r['max_mismatches']) for r in ss}=={0,1,2}
   assert all(r['status']=='COMPLETED' for r in ss)
   p=phase/('__'.join(k)+'__hits.tsv.gz');hits=read(p)
   assert len(hits)==int(next(r for r in ss if r['max_mismatches']=='2')['site_count'])
   actual[k]={'summary':ss,'hits':hits,'raw':p.relative_to(ROOT).as_posix()}
   raw_records.append({'query':list(k),'file':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p),'site_rows':len(hits)})
   allhits.extend(hits)
 assert set(actual)==set(bykey) and len(actual)==264
 for a in json.loads((OUT/'input_and_reference_manifest.json').read_text(encoding='utf-8')):
  assert sha(Path(a['path']))==a['sha256'],a['path']
 mapping=defaultdict(set);symbols=defaultdict(set)
 for r in read(LEGACY/'prepared/refseq_all_transcript_gene_loci.tsv'):
  mapping[r['transcript_id']].add(r['gene_id']);symbols[r['gene_id']].add(r['symbol'])
 ids={h['transcript_id'] for h in allhits};refs={};reference_order={};cid=None;parts=[];index=0
 def keep():
  if cid in ids:refs[cid]=''.join(parts)
 with (LEGACY/'prepared/refseq_all_transcripts.fasta').open(encoding='utf-8') as f:
  for line in f:
   if line.startswith('>'):
    keep();index+=1;cid=line[1:].split()[0];reference_order[cid]=index;parts=[]
   elif cid in ids:parts.append(line.strip().upper())
  keep()
 assert index==186185 and set(refs)==ids
 potential=[];merged=[];states=[];checks=[];boundaries=[];inbounds_summaries=[]
 for p in plan:
  k=key(p);a=actual[k];hits=a['hits'];seen=set()
  for h in hits:
   assert key(h)==k and h['target_pattern_DNA']==p['target_pattern_DNA']
   s,e=int(h['start']),int(h['end']);ref=refs[h['transcript_id']];pattern=p['target_pattern_DNA']
   assert len(pattern)==int(h['width'])==19
   assert e==s+18 and int(h['group'])==reference_order[h['transcript_id']]
   # Biostrings counts letters outside the subject as mismatches. Preserve the
   # raw match, but never present its clipped overlap as a full 19nt interval.
   absent=sum(not 1<=pos<=len(ref) for pos in range(s,e+1))
   observed_mm=sum(pattern[i]!=ref[pos-1] for i,pos in enumerate(range(s,e+1)) if 1<=pos<=len(ref))
   mm=observed_mm+absent;assert mm==int(h['mismatches'])<=2
   if absent:
    boundaries.append({**h,'reference_length':len(ref),'out_of_reference_bases':absent,'observed_overlap_bases':19-absent,
      'observed_overlap_mismatches':observed_mm,'classification':'RAW_BIOSTRINGS_BOUNDARY_OVERLAP_NOT_FULL_19NT','raw_evidence':a['raw']})
   pos=(h['transcript_id'],s,e);assert pos not in seen;seen.add(pos)
   genes=mapping.get(h['transcript_id'],set());assert h['gene_ids']==(';'.join(sorted(genes)) if genes else 'UNKNOWN_MAPPING')
   if mm<=1 and (genes-{'7422'} or not genes):potential.append({**h,'gene_symbols':';'.join(sorted({v for g in genes for v in symbols[g]})) or 'UNKNOWN','raw_evidence':a['raw']})
  for mm in range(3):
   h=[h for h in hits if int(h['mismatches'])<=mm];geneids=set().union(*(mapping.get(x['transcript_id'],set()) for x in h)) if h else set()
   unknown={x['transcript_id'] for x in h if x['transcript_id'] not in mapping}
   r=next(r for r in a['summary'] if int(r['max_mismatches'])==mm)
   assert len(h)==int(r['site_count']) and len(geneids-{'7422'})==int(r['non_target_gene_n']) and len(unknown)==int(r['unknown_mapping_transcript_n'])
   assert (r['target_gene_present']=='TRUE')==('7422' in geneids)
   merged.append({**r,'raw_evidence':a['raw']})
   within=[x for x in h if int(x['start'])>=1 and int(x['end'])<=len(refs[x['transcript_id']])]
   within_genes=set().union(*(mapping.get(x['transcript_id'],set()) for x in within)) if within else set()
   inbounds_summaries.append({**r,'site_count':len(within),'non_target_gene_n':len(within_genes-{'7422'}),
     'unknown_mapping_transcript_n':len({x['transcript_id'] for x in within if x['transcript_id'] not in mapping}),
     'interpretation':'FULL_19NT_INTERVAL_WITHIN_REFERENCE_ONLY; supplementary, raw result unchanged'})
  states.append({**p,'actual_status':'COMPLETED_WITH_HITS' if hits else 'COMPLETED_ZERO_HITS','site_count_at_most_2mm':len(hits),'raw_evidence':a['raw']})
  checks.append({'key':list(k),'all_positions_mismatches_gene_mappings_and_cumulative_summaries_verified':True,'site_rows':len(hits)})
 write('all_264_actual_states.tsv',states);write('all_264_summary.tsv',merged)
 write('all_264_full_window_within_reference_summary.tsv',inbounds_summaries)
 if boundaries:write('boundary_overlaps_separate.tsv',boundaries)
 save('boundary_overlaps.json',boundaries)
 state_map={key(r):r for r in states};all_units=[]
 for r in read(PRIOR/'planned_units_actual_states.tsv'):
  if r['unit'].startswith('nearfull_'):
   a=state_map[(r['candidate_id'],r['strand'],r['unit'].removeprefix('nearfull_'))]
   all_units.append({**r,'status':a['actual_status'],'evidence':a['raw_evidence']})
  else:all_units.append(r)
 assert len(all_units)==462 and all(r['status'].startswith('COMPLETED') for r in all_units)
 write('all_462_actual_states.tsv',all_units)
 write('all_0or1mm_non_target_or_unknown_sites.tsv',potential)
 prior=json.loads((PRIOR/'new_65_complete_table.json').read_text(encoding='utf-8'))+json.loads((PRIOR/'purchased_siVEGF_separate.json').read_text(encoding='utf-8'))
 new=[]
 for r in prior:
  row=dict(r)
  if 'provisional_review_basis' in row:row['previous_CDS_subset_provisional_review_basis']=row.pop('provisional_review_basis')
  for role in ['guide','passenger']:
   for kind in ['paired_core19','sidirect_g2g20']:
    a=actual[(r['candidate_id'],role,kind)]
    for x in a['summary']:
     for field in ['non_target_gene_n','unknown_mapping_transcript_n','site_count']:
      row[role+'_'+kind+'_mm'+x['max_mismatches']+'_'+field]=int(x[field])
  row['nearfull_status']='COMPLETED_4_QUERIES';new.append(row)
 write('all_65_designs_complete.tsv',new[:-1]);save('all_65_designs_complete.json',new[:-1]);write('purchased_separate_complete.tsv',new[-1:]);save('purchased_separate_complete.json',new[-1:])
 with_findings={h['candidate_id'] for h in potential}
 findings={'designs_with_any_0or1mm_non_target_or_unknown':sorted(with_findings-{'USER_PURCHASED_siVEGF'}),
  'designs_without_such_hits_in_all_four_queries':[r['candidate_id'] for r in new[:-1] if r['candidate_id'] not in with_findings],
  'purchased_has_such_hit':'USER_PURCHASED_siVEGF' in with_findings,
  'previous_CDS_discussion_only':['VEGFA_SD_1157','VEGFA_SD_1555'],'new_best_of_65_claim':False,'no_reranking_or_new_filter_rule':True}
 save('new_findings.json',findings)
 save('all_query_raw_manifest.json',raw_records)
 audit={'status':'PASS','planned_unique':264,'old_completed_reused':24,'new_unique_completed':240,'failed':0,'not_run':0,
  'status_counts':dict(Counter(r['actual_status'] for r in states)),'all_site_rows':len(allhits),'new_site_rows':sum(len(a['hits']) for k,a in actual.items() if a['raw'].startswith(OUT.relative_to(ROOT).as_posix())),
  'boundary_overlap_rows_reported_separately':len(boundaries),'full_19nt_in_reference_site_rows':len(allhits)-len(boundaries),
  'all_queries_checked':checks,'reference_transcripts':index,'versions_unchanged':True,'query_parameters_unchanged':True,
  'difference_from_old_command':'New invocation omitted --vanilla; scientific adapter, reference, parameters and loaded R/package versions independently match. No startup code was changed.',
  'new_model_score_runs':0,'new_seed_runs':0,'source_execution':receipt,'limitations':'Full coverage of this fixed reference and these four overlapping windows is not comprehensive safety or experimental off-target validation.'}
 save('completion_audit.json',audit);print(json.dumps({k:v for k,v in audit.items() if k not in ('all_queries_checked','source_execution')}))
if __name__=='__main__':main()
