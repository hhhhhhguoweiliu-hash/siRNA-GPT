import csv, gzip, hashlib, json, re, sys, zipfile
from pathlib import Path
from collections import defaultdict, Counter
from xml.etree import ElementTree as ET

sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(r'C:\00000\ARPE RNA-seq\sirna-gpt')
OUT = Path(__file__).resolve().parent
B = ROOT / 'research/2026-10-24_nearfull_complete'
LEGACY = Path.cwd() / 'analysis/ARPE19_candidates_20261016'
CHECKS = []
def check(name, valid, detail=None):
    CHECKS.append(dict(name=name, passed=bool(valid), detail=detail))
def js(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def tab(p):
    p=Path(p)
    with (gzip.open(p,'rt',encoding='utf-8-sig') if p.suffix=='.gz' else p.open(encoding='utf-8-sig')) as f:
        return list(csv.DictReader(f,delimiter='\t'))
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for x in iter(lambda:f.read(1048576),b''):h.update(x)
    return h.hexdigest()
def blob(data): return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
def key(r): return tuple(r[k] for k in ('candidate_id','strand_role','query_kind'))
def revcomp(s): return s.upper().replace('U','T').translate(str.maketrans('ACGT','TGCA'))[::-1]

# Bind local evidence to the independently obtained main tree, allowing only
# documented CRLF conversion for four source-code text files.
snapshot=js(OUT/'snapshot.json') if (OUT/'snapshot.json').exists() else json.loads(gzip.decompress((OUT/'20261024_2218_complete_results_audit_full.json.gz').read_bytes()))['review_source_snapshot']
for entry in snapshot['files']:
    data=(ROOT/entry['path']).read_bytes()
    direct=blob(data)==entry['sha']
    lf=blob(data.replace(b'\r\n',b'\n'))==entry['sha']
    check('github_binding:'+entry['path'],direct or lf,dict(raw=direct,LF=lf))

plan=tab(ROOT/'research/2026-10-24_candidate_v2/inputs/nearfull_all_264.tsv')
initial=tab(B/'plan_264_initial_states.tsv');remaining=tab(B/'remaining_240.tsv')
actual=tab(B/'all_264_actual_states.tsv');manifest=js(B/'all_query_raw_manifest.json')
pmap={key(r):r for r in plan};amap={key(r):r for r in actual}
check('264_unique_identical_plan_and_actual',len(pmap)==len(plan)==len(actual)==len(amap)==264 and set(pmap)==set(amap))
oldkeys={key(r) for r in initial if r['source_phase']!='new_240'}
newkeys={key(r) for r in remaining}
check('old24_plus_exact_remaining240',len(oldkeys)==24 and len(newkeys)==len(remaining)==240 and not oldkeys&newkeys and oldkeys|newkeys==set(pmap))
hits={}
for item in manifest:
    q=tuple(item['query']);f=ROOT/item['file'];rows=tab(f);hits[q]=rows
    check('raw_sha:'+str(q),sha(f)==item['sha256'] and f.stat().st_size==item['bytes'] and len(rows)==item['site_rows'])
    check('status_and_file:'+str(q),amap[q]['raw_evidence']==item['file'] and int(amap[q]['site_count_at_most_2mm'])==len(rows) and amap[q]['actual_status']==('COMPLETED_WITH_HITS' if rows else 'COMPLETED_ZERO_HITS'))
    check('phase:'+str(q),('/new_240/' in item['file'])==(q in newkeys))
check('264_raw_files',len(hits)==len(manifest)==264 and set(hits)==set(pmap))

for item in js(B/'input_and_reference_manifest.json'):
    check('input_reference_sha:'+item['path'],sha(item['path'])==item['sha256'])
mapping=defaultdict(set)
for r in tab(LEGACY/'prepared/refseq_all_transcript_gene_loci.tsv'):
    mapping[r['transcript_id']].add(r['gene_id'])
wanted={h['transcript_id'] for v in hits.values() for h in v}
ref={};ordinal={};seq=[];name=None;n=0
def finish():
    if name in wanted:ref[name]=''.join(seq)
with (LEGACY/'prepared/refseq_all_transcripts.fasta').open(encoding='utf-8') as f:
    for line in f:
        if line.startswith('>'):
            finish();n+=1;name=line[1:].split()[0];ordinal[name]=n;seq=[]
        elif name in wanted: seq.append(line.strip().upper())
finish()
check('reference_transcripts_and_all_hit_ids',n==186185 and set(ref)==wanted,dict(reference_n=n,hit_transcripts=len(wanted)))
summ={(*key(r),int(r['max_mismatches'])):r for r in tab(B/'all_264_summary.tsv')}
within_summ={(*key(r),int(r['max_mismatches'])):r for r in tab(B/'all_264_full_window_within_reference_summary.tsv')}
boundaries=[];risk=set();risk_sites=[];total=0
for q,rows in hits.items():
    pat=pmap[q]['target_pattern_DNA'];seen=set();valid=True
    check('query_reverse_complement:'+str(q),len(pat)==19 and pat==revcomp(pmap[q]['strand19_RNA']))
    for h in rows:
        s,e=int(h['start']),int(h['end']);ss=ref[h['transcript_id']]
        missing=sum(not 1<=pos<=len(ss) for pos in range(s,e+1))
        mm=sum(pat[i]!=ss[pos-1] for i,pos in enumerate(range(s,e+1)) if 1<=pos<=len(ss))+missing
        genes=mapping[h['transcript_id']];site=(h['transcript_id'],s,e)
        valid &= key(h)==q and h['target_pattern_DNA']==pat and e-s+1==int(h['width'])==19 and mm==int(h['mismatches'])<=2 and int(h['group'])==ordinal[h['transcript_id']] and h['gene_ids']==(';'.join(sorted(genes)) if genes else 'UNKNOWN_MAPPING') and site not in seen
        seen.add(site)
        if missing:boundaries.append(dict(query=q,transcript=h['transcript_id'],start=s,end=e,length=len(ss),missing=missing,mm=mm))
        if mm<=1 and (genes-{'7422'} or not genes):risk.add(q[0]);risk_sites.append(h)
    check('all_saved_positions_mm_mapping:'+str(q),valid,dict(rows=len(rows)))
    for lim in (0,1,2):
        for full_only,lookup in [(False,summ),(True,within_summ)]:
            selected=[h for h in rows if int(h['mismatches'])<=lim and (not full_only or 1<=int(h['start'])<=int(h['end'])<=len(ref[h['transcript_id']]))]
            gs=set().union(*(mapping[h['transcript_id']] for h in selected)) if selected else set()
            unknown={h['transcript_id'] for h in selected if not mapping[h['transcript_id']]}
            expected=(len(selected),len(gs-{'7422'}),len(unknown),'7422' in gs)
            r=lookup[(*q,lim)]
            observed=(int(r['site_count']),int(r['non_target_gene_n']),int(r['unknown_mapping_transcript_n']),r['target_gene_present']=='TRUE')
            check(('full_window_summary:' if full_only else 'raw_summary:')+str((*q,lim)),expected==observed,dict(expected=expected,observed=observed))
    total+=len(rows)
check('7480_raw_and_one_boundary',total==7480 and len(boundaries)==1,boundaries)
check('23_designs_and_no_purchased_01mm',len(risk)==23 and 'USER_PURCHASED_siVEGF' not in risk,sorted(risk))
check('127_01mm_risk_sites',len(risk_sites)==127)
full=tab(B/'all_65_designs_complete.tsv')+tab(B/'purchased_separate_complete.tsv')
for r in full:
    for role in ('guide','passenger'):
        for kind in ('paired_core19','sidirect_g2g20'):
            for mm in (0,1,2):
                s=summ[(r['candidate_id'],role,kind,mm)]
                check('candidate_summary:'+str((r['candidate_id'],role,kind,mm)),all(int(r[f'{role}_{kind}_mm{mm}_{field}'])==int(s[field]) for field in ('site_count','non_target_gene_n','unknown_mapping_transcript_n')))
execution=js(B/'execution.json')
check('successful_new240_execution',execution['exit_code']==0 and execution['status']=='RETURNED' and abs(execution['wall_seconds']-1640.0956658)<0.001)
for phase in [ROOT/'research/2026-10-24_candidate_v2/nearfull_pilot',ROOT/'research/2026-10-24_candidate_v2/nearfull_CDS_remaining',B/'new_240']:
    text=(phase/'sessionInfo.txt').read_text(encoding='utf-8')
    check('same_R_packages:'+phase.name,all(v in text for v in ['R version 4.3.1','Biostrings_2.70.1','data.table_1.14.8','dplyr_1.1.3']))

# Verify changed locators against the original XML, including all descendants.
changed=0;locator_n=0
for paper in ('chen2013','osipova2020'):
    folder=ROOT/'references/vegfa_experiments_20261024'
    root=ET.parse(folder/(paper+'.xml')).getroot()
    if root.tag!='article':root=root.find('article')
    before=js(B/f'metadata_corrections/{paper}_locators.json')
    after=js(folder/(paper+'_locators.json'))
    for x,y in zip(before,after):
        locator_n+=1;changed+=x['xpath']!=y['xpath']
        nodes=root.findall('./'+y['xpath'].split('/',2)[2])
        text=' '.join(''.join(nodes[0].itertext()).split()) if len(nodes)==1 else None
        check('XML:'+paper+':'+y['locator'],len(nodes)==1 and text==' '.join(y['text'].split()) and x['text']==y['text'])
check('90_locators_five_path_changes',locator_n==90 and changed==5,dict(n=locator_n,changed=changed))
wording=js(ROOT/'research/2026-10-24_candidate_v2/provisional_small_trial_candidates.json')['method']
check('locally_prespecified_wording',wording.startswith('locally prespecified') and 'preregister' not in wording.lower(),wording)

# Original ZIP, imported evidence and real request/response chain.
L=B/'live';T=L/'tool_export'
with zipfile.ZipFile(L/'actual_tool_export_original.zip') as z:
    files=[f for f in z.namelist() if not f.endswith('/')]
    check('57file_ZIP_CRC',len(files)==57 and z.testzip() is None)
    for f in files:check('ZIP_exact:'+f,z.read(f)==(T/f).read_bytes())
dataset=ROOT/'data/purchased_sivegf_20261024_v1';manifest=js(dataset/'manifest.json')
for filename,digest in manifest['files'].items():
    check('import20:'+filename,sha(dataset/filename)==digest and sha(T/'verified_import/purchased_sivegf_20261024_v1'/filename)==digest)
check('dataset_fixed_reference',sha(ROOT/'data/VEGFA.fasta')==manifest['fixed_target_fasta_sha256'])
check('source_purchased_result',sha(ROOT/manifest['source_result'])==manifest['source_result_sha256'])
conv=js(L/'conversation_export_original.json');records=conv['evidence_records']
planner=[x for x in records if x['kind']=='model_exchange']
check('one_planner_exchange',len(planner)==1)
check('one_case_one_candidate',len(js(T/'input.json')['candidates'])==1 and js(T/'input.json')['candidates'][0]['candidate_id']=='USER_PURCHASED_siVEGF')
calls=[]
for r in planner:calls.append((r['request'],r['response']))
for p in sorted((T/'attempts').glob('*_request.json')):calls.append((js(p),js(p.with_name(p.name.replace('_request','_response')))))
check('8_real_model_requests',len(calls)==8)
usage=Counter()
response_ids=[]
for request,response in calls:
    # Wrapped evidence exchanges and per-attempt native API bodies differ.
    if 'raw' in response and 'status' not in response: response=response['raw']
    if '_raw_response' in response:
        request=response['_request'];response=response['_raw_response']
    check('real_response:'+response.get('id','?'),response.get('status')=='completed' and not response.get('incomplete_details') and request['max_output_tokens']==1800 and request['stream'] is False and request['thinking']=={'type':'disabled'})
    response_ids.append(response.get('id'))
    for name in ('input_tokens','output_tokens','total_tokens'):usage[name]+=response['usage'][name]
check('usage_and_unique_responses',len(set(response_ids))==8 and dict(usage)==dict(input_tokens=37760,output_tokens=1288,total_tokens=39048),dict(usage))
transcript=js(T/'model_transcript.json')
tools=[c['function']['name'] for x in transcript for c in x.get('tool_calls',[])]
check('six_actual_tools_in_order',tools==['inspect_candidates','verify_target','score_candidates','match_seed','query_expression','compile_report'],tools)
check('six_tool_responses',len([x for x in transcript if x['role']=='tool'])==6)
inp=js(T/'input.json')['candidates'][0]
check('correct_input_strands',inp['guide_core19_5to3']=='UUUCUUGUCUUGCUCUAUC' and inp['passenger_paired_core_19nt_5to3']=='GAUAGAGCAAGACAAGAAA')
fasta={};name=None
for line in (ROOT/'data/VEGFA.fasta').read_text(encoding='utf-8').splitlines():
    if line.startswith('>'):name=line[1:].split()[0];fasta[name]=''
    else:fasta[name]+=line.strip().upper()
pattern=revcomp(inp['guide_core19_5to3'])
check('target_position_coverage',len(fasta)==20 and sum(pattern in seq for seq in fasta.values())==18 and fasta['NM_003376.6'][1438:1457]==pattern)
score=js(T/'score_candidates.json')['rows'][0]
check('purchased_correct_score',score['oligoformer_scaled_score']==1.121934400320053 and score['raw_class1']==0.8366401195526123 and score['official_func_filter']==0)
seed=tab(T/'seed_matches.tsv');expr=tab(ROOT/'data/expression.tsv.gz')
express={r['ENTREZID']:r for r in expr if r['ENTREZID']};non=[r for r in seed if r['gene_id']!='7422']
mapped=[r for r in non if r['gene_id'] in express]
unknown=[r['gene_id'] for r in non if r['gene_id'] not in express]
hyp={r['gene_id'] for r in mapped if int(express[r['gene_id']]['Hypoxia_n_TPM_ge1'])>=2}
norm={r['gene_id'] for r in mapped if int(express[r['gene_id']]['Normoxia_n_TPM_ge1'])>=2}
counts=dict(seed_site_count_all=sum(int(r['seed_site_count']) for r in seed),seed_site_count_nontarget=sum(int(r['seed_site_count']) for r in non),matched_genes=len({r['gene_id'] for r in non}),baseline_mapped_genes=len(mapped),hypoxia_detected_genes=len(hyp),normoxia_detected_genes=len(norm),state_detected_genes=len(hyp),unmapped_genes=len(unknown),hypoxia_only_detected_genes=len(hyp-norm),normoxia_only_detected_genes=len(norm-hyp))
reported=js(T/'query_expression.json')['candidate_summary'][0]
check('independent_expression_join',all(reported[k]==v for k,v in counts.items()),dict(recalculated=counts,unknown=unknown))
details=tab(T/'seed_expression_details.tsv')
check('all_expression_detail_fields',all(all(r.get(k)==v for k,v in express[r['gene_id']].items()) for r in details if r['gene_id'] in express))
run=js(T/'run_config.json')['runtime']
for path,digest in run['assets'].items():
    data=(ROOT/path).read_bytes()
    check('deployed_assets:'+path,hashlib.sha256(data).hexdigest()==digest or hashlib.sha256(data.replace(b'\r\n',b'\n')).hexdigest()==digest)
report=js(T/'report.json');answer=report['model_summary'];issue=js(L/'answer_sequence_discrepancy.json')
check('known_sequence_error_preserved',issue['original_generated_text'] in answer and len(issue['original_generated_text'])==24 and issue['correct_from_original_input']==inp['passenger_paired_core_19nt_5to3'] and len(issue['correct_from_original_input'])==19)
check('raw_answer_in_multiple_original_exports',answer==js(T/'result.json')['model_summary'] and answer==conv['result']['model_summary'] and answer in [x.get('content') for x in transcript if x['role']=='assistant'])
check('correction_not_hidden',(L/'ANSWER_CORRECTION_ZH.md').exists() and '24-nt' in (B/'PAPER_METHODS_RESULTS_DRAFT_EN.md').read_text(encoding='utf-8'))

audit=dict(reviewed_commit=snapshot['head'],scope='independent saved-data, summaries, expression join and raw-exchange audit; no API calls, new model inference, seed search, or full-reference near-full search',checks_n=len(CHECKS),failed=[x for x in CHECKS if not x['passed']],nearfull=dict(queries=len(hits),sites=total,boundaries=boundaries,with_01mm=sorted(risk),status_counts=dict(Counter(r['actual_status'] for r in actual))),real_case=dict(run_id=report['run_id'],tools=tools,model_requests=len(calls),usage=dict(usage),expression=counts,answer_quality='KNOWN_SEQUENCE_TRANSCRIPTION_ERROR_PRESERVED'),checks=CHECKS)
(OUT/'independent_audit_full.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in audit.items() if k!='checks'},ensure_ascii=False,indent=2))
