"""Validation-only recount from raw TPM and archived UTR. No production imports.

Shares measurements, annotation/mapping and official seed definition, not the
production aggregation functions. No inference of biological efficacy/safety.
"""
import argparse, collections, csv, gzip, hashlib, io, json, math, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
EXPECTED={'gene_tpm.xls':'c0ef6fbcfb5ae62f3979dfa1e359dd4d046caa1a281d72ff3816fd22ad5bcdcc',
 'refseq_utr3_representative.fasta':'8a7a99ecc7346c50c76e37cd24cd851ce96adb348cc447f007233e2f10aac779',
 'utr_manifest_representative.tsv':'a63dd3668d6cdb439a816c475b1cb9181183fd2bb2e76212d3a2fe0076d56aab',
 'get_seed.R':'164853a2be7a6b1a7f047604cd92e465ef1e7c73384f28d66df7bdca2835e9b9'}

def rows(p):
    with (gzip.open(p,'rt',encoding='utf-8-sig',newline='') if p.suffix=='.gz' else p.open(encoding='utf-8-sig',newline='')) as f:
        yield from csv.DictReader(f,delimiter='\t')

def table(p,rr,fields=None):
    rr=list(rr);fields=fields or list(rr[0])
    f=io.StringIO(newline='')
    w=csv.DictWriter(f,fieldnames=fields,delimiter='\t');w.writeheader();w.writerows(rr)
    data=f.getvalue().encode('utf-8')
    p.write_bytes(gzip.compress(data,mtime=0) if p.suffix=='.gz' else data)

def dna(seq):return seq.upper().replace('U','T')
def motif(guide):
    s=dna(guide)
    assert set(s)<=set('ACGT') and len(s)>=8
    return s[1:8].translate(str.maketrans('ACGT','TGCA'))[::-1]
def positions(seq,pattern):
    start=0
    while True:
        hit=seq.find(pattern,start)
        if hit<0:return
        yield hit+1
        start=hit+1

def fasta(p):
    name=None;seq=[]
    with p.open(encoding='utf-8') as f:
        for line in f:
            if line.startswith('>'):
                if name is not None:yield name,dna(''.join(seq))
                name=line[1:].split()[0];seq=[]
            else:seq.append(line.strip())
    if name is not None:yield name,dna(''.join(seq))

def controls():
    tests=[('official_example',motif('UUAUAGAGCAAGAACACUGUUUU')=='CTCTATA'),
        ('overlap',list(positions('AAAAA','AAA'))==[1,2,3]),
        ('negative',list(positions('ACGT','TT'))==[]),
        ('N_literal_not_wildcard',list(positions('ACNTA','ACG'))==[]),
        ('end_boundary',list(positions('TTACAAGAA','ACAAGAA'))==[3]),
        ('no_wraparound',list(positions('AAGAAACA','ACAAGAA'))==[]),
        ('direction',motif('UUUCUUGUCUUGCUCUAUCTT')=='ACAAGAA')]
    assert all(v for _,v in tests),tests
    return [{'control':n,'passed':v,'kind':'SYNTHETIC_TEST_ONLY'} for n,v in tests]

def main():
    p=argparse.ArgumentParser();p.add_argument('--analysis',type=Path,required=True);p.add_argument('--tpm',type=Path,required=True);p.add_argument('--mapping',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    started=time.time();a.output.mkdir(parents=True,exist_ok=False);inventory=[]
    def bind(f):
        digest=hashlib.sha256(f.read_bytes()).hexdigest()
        if f.name in EXPECTED:assert digest==EXPECTED[f.name],f
        inventory.append(dict(path=str(f),bytes=f.stat().st_size,sha256=digest));return f
    prep=a.analysis/'prepared';risk=a.analysis/'risk_raw'
    for f in [a.tpm,prep/'refseq_utr3_representative.fasta',prep/'utr_manifest_representative.tsv',a.analysis/'official_tools/SeedMatchR_1.1.1/R/get_seed.R',prep/'reference_gene_baseline_map.tsv',a.analysis/'run_seed_and_search.R',risk/'seed_motifs.tsv',risk/'seed_counts_official.tsv',risk/'seed_sites_7merm8.tsv',prep/'candidates_working_pool.tsv',ROOT/'data/expression.tsv.gz',ROOT/'data/historical_seed_matches.tsv']:
        bind(f)
    table(a.output/'seed_controls.tsv',controls())
    legacy=list(rows(bind(ROOT/'data/candidates.tsv')))
    actual={r['candidate_id']:r for r in rows(prep/'candidates_working_pool.tsv')}
    guides={}
    for c in legacy:
        raw=actual[c['candidate_id']]
        assert raw['guide_21nt_RNA_5to3']==c['guide_21nt_RNA_5to3']
        guides[c['candidate_id']]=raw['guide_21nt_RNA_5to3']
    # Purchased official job exports carry their own full guide input, not legacy rows.
    purchased=ROOT/'research/2026-10-24_candidate_v2'
    # Original order-derived role assumption is explicitly retained in the package.
    candidate=json.loads(bind(ROOT/'data/purchased_sivegf_20261024_v1/verified_local_result.json').read_text('utf-8'))
    original_results=json.loads(bind(ROOT/'research/2026-10-27_real_dialogue_mini/raw/results_original.json').read_text('utf-8'))
    purchased_input=next(r for x in original_results for q in x['rounds'] for r in q['tool_results'].get('inspect_candidates',{}).get('rows',[]) if r['candidate_id']=='USER_PURCHASED_siVEGF')
    # Full actual guide is taken from the official candidate batch input below.
    rawp=next(r for r in rows(bind(purchased/'inputs/seed_pilot_4.tsv')) if r['candidate_id']=='USER_PURCHASED_siVEGF' and r['strand_role']=='guide')
    guides={'USER_PURCHASED_siVEGF':rawp['sequence_core19_RNA'],**guides}
    assert dna(guides['USER_PURCHASED_siVEGF'][:19])==dna(purchased_input['guide_core19_5to3'])
    motifs={cid:motif(g) for cid,g in guides.items()}
    official_motifs={r['candidate_id']:r['target_motif_5to3'] for r in rows(risk/'seed_motifs.tsv') if r['strand_role']=='guide' and r['seed_type']=='mer7m8'}
    for cid in legacy:
        assert motifs[cid['candidate_id']]==official_motifs[cid['candidate_id']]
    pc=bind(ROOT/'data/purchased_sivegf_20261024_v1/seed_pilot_02__USER_PURCHASED_siVEGF__guide__counts.tsv.gz')
    ps=bind(ROOT/'data/purchased_sivegf_20261024_v1/seed_pilot_02__USER_PURCHASED_siVEGF__guide__sites.tsv.gz')
    assert {r['target_motif_DNA'] for r in rows(pc)}=={motifs['USER_PURCHASED_siVEGF']}
    manifest=list(rows(prep/'utr_manifest_representative.tsv'))
    bytx={r['transcript_id']:r['gene_id'] for r in manifest}
    assert len(bytx)==len(manifest)==len({r['gene_id'] for r in manifest})
    ref=dict(fasta(prep/'refseq_utr3_representative.fasta'));assert set(ref)==set(bytx)
    found={cid:set() for cid in guides};counts={cid:collections.Counter() for cid in guides}
    site_rows=[]
    for tx,seq in ref.items():
        for cid,pat in motifs.items():
            for start in positions(seq,pat):
                found[cid].add((tx,start));counts[cid][bytx[tx]]+=1
                site_rows.append(dict(candidate_id=cid,transcript_id=tx,gene_id=bytx[tx],start_utr_1based=start,end_utr_1based=start+6,motif_DNA=pat,context=seq[max(0,start-6):start+11]))
    table(a.output/'seed_sites_independent.tsv.gz.tmp',site_rows)
    # Compress derived detailed output only; no original source is modified.
    tmp=a.output/'seed_sites_independent.tsv.gz.tmp'
    with gzip.GzipFile(filename='',mode='wb',fileobj=(a.output/'seed_sites_independent.tsv.gz').open('wb'),mtime=0) as z:z.write(tmp.read_bytes())
    tmp.unlink()
    expected_counts={cid:{} for cid in guides};expected_sites={cid:set() for cid in guides}
    for r in rows(risk/'seed_counts_official.tsv'):
        cid=r['candidate_id']
        if cid in guides and r['strand_role']=='guide' and r['seed_type']=='mer7m8':
            assert r['gene_id'] not in expected_counts[cid]
            expected_counts[cid][r['gene_id']]=int(r['seed_site_count'])
    for r in rows(pc):expected_counts['USER_PURCHASED_siVEGF'][r['gene_id']]=int(r['seed_site_count'])
    for f in [risk/'seed_sites_7merm8.tsv',ps]:
        for r in rows(f):
            cid=r['candidate_id']
            if cid in guides and r['strand_role']=='guide':expected_sites[cid].add((r['transcript_id'],int(r['start'])))
    comparisons=[];differences=[];gene_counts=[];transcript_counts=[]
    for cid in guides:
        for gid in bytx.values():
            got=counts[cid][gid];want=expected_counts[cid].get(gid)
            gene_counts.append(dict(candidate_id=cid,gene_id=gid,observed=got,expected=want,status='PASS' if got==want else 'DIFFERENCE'))
        txgot=collections.Counter(t for t,s in found[cid]);txwant=collections.Counter(t for t,s in expected_sites[cid])
        for tx in bytx:
            got=txgot[tx];want=txwant[tx]
            transcript_counts.append(dict(candidate_id=cid,transcript_id=tx,gene_id=bytx[tx],observed=got,expected=want,status='PASS' if got==want else 'DIFFERENCE'))
        for tx,start in sorted(found[cid]^expected_sites[cid]):
            seq=ref[tx];differences.append(dict(candidate_id=cid,transcript_id=tx,gene_id=bytx[tx],start_utr_1based=start,end_utr_1based=start+6,context=seq[max(0,start-6):start+11],kind='INDEPENDENT_ONLY' if (tx,start) in found[cid] else 'OFFICIAL_ONLY'))
        allsites=sum(counts[cid].values());target=counts[cid]['7422'];positive={g for g,n in counts[cid].items() if n and g!='7422'}
        comparisons.append(dict(candidate_id=cid,actual_guide_5to3=guides[cid],motif_DNA=motifs[cid],reference_genes=len(bytx),seed_sites_all=allsites,target_sites=target,seed_sites_nontarget=allsites-target,matched_nontarget_genes=len(positive),site_symmetric_difference=len(found[cid]^expected_sites[cid]),gene_count_differences=sum(counts[cid][g]!=n for g,n in expected_counts[cid].items())))
    table(a.output/'seed_gene_counts.tsv.gz',gene_counts);table(a.output/'seed_transcript_counts.tsv.gz',transcript_counts)
    table(a.output/'seed_site_differences.tsv',differences,['candidate_id','transcript_id','gene_id','start_utr_1based','end_utr_1based','context','kind'])
    table(a.output/'seed_candidate_comparison.tsv',comparisons)
    # Independently recalculate per-sample detection, ignoring saved means/counts.
    tpm={};tpm_duplicates=[]
    with a.tpm.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.reader(f,delimiter='\t');header=next(reader);assert header==['','Hyp1','Hyp2','Hyp3','Hyp4','Nor1','Nor2','Nor3','Nor4']
        for row in reader:
            assert len(row)==9
            if row[0] in tpm:tpm_duplicates.append(row[0])
            values=[float(v) for v in row[1:]];assert all(math.isfinite(v) and v>=0 for v in values)
            tpm.setdefault(row[0],values)
    assert not tpm_duplicates,'Ambiguous raw TPM feature rows'
    maps=collections.defaultdict(list)
    mapping_path=a.mapping or prep/'reference_gene_baseline_map.tsv'
    bind(mapping_path)
    # Only static identifiers are extracted. TPM and precomputed detection
    # columns of the shared mapping source are deliberately not read here.
    for r in rows(mapping_path):
        gid=r.get('ENTREZID',r.get('gene_id',''))
        if gid.isdigit():maps[gid].append(dict(gene_id=gid,source_gene_id=r.get('feature_id',r.get('source_gene_id','')),expression_mapping_status=r.get('mapping_status',r.get('expression_mapping_status',''))))
    mapping_issues=[];independent={}
    for gid,rr in maps.items():
        if len(rr)!=1:
            mapping_issues.append(dict(gene_id=gid,reason='DUPLICATE_OR_AMBIGUOUS_GENE_MAPPING',records=json.dumps(rr)));continue
        r=rr[0];feature=r['source_gene_id']
        if feature not in tpm:continue
        values=tpm[feature]
        independent[gid]=dict(feature_id=feature,Hypoxia_n_TPM_ge1=sum(v>=1 for v in values[:4]),Normoxia_n_TPM_ge1=sum(v>=1 for v in values[4:]),**dict(zip(header[1:],values)))
    packaged=collections.defaultdict(list)
    for r in rows(ROOT/'data/expression.tsv.gz'):packaged[r['ENTREZID']].append(r)
    # Duplicates are explicitly listed; identical state counts may still be compared.
    for gid,rr in packaged.items():
        if len(rr)>1:mapping_issues.append(dict(gene_id=gid,reason='PACKAGED_DUPLICATE_ENTREZ',records=json.dumps(rr)))
    table(a.output/'mapping_issues.tsv',mapping_issues,['gene_id','reason','records'])
    per_gene=[];expression_comparison=[];set_diffs=[]
    for cid in guides:
        # Original official counts form the off-target gene set for TPM validation.
        genes={g for g,n in expected_counts[cid].items() if n>0 and g!='7422'}
        sets={k:set() for k in ('mapped','unmapped','normoxia','hypoxia')};old={k:set() for k in sets}
        for gid in sorted(genes):
            r=independent.get(gid);pr=packaged.get(gid,[])
            if len(pr)>1:raise ValueError('Ambiguous packaged mapping in seed panel: '+gid)
            q=pr[0] if pr else None
            sets['mapped' if r else 'unmapped'].add(gid);old['mapped' if q else 'unmapped'].add(gid)
            for state,key in [('Normoxia','normoxia'),('Hypoxia','hypoxia')]:
                if r and r[state+'_n_TPM_ge1']>=2:sets[key].add(gid)
                if q and int(q[state+'_n_TPM_ge1'])>=2:old[key].add(gid)
            same=(r is None and q is None) or bool(r and q and all(r[s+'_n_TPM_ge1']==int(q[s+'_n_TPM_ge1']) for s in ('Normoxia','Hypoxia')))
            per_gene.append(dict(candidate_id=cid,gene_id=gid,feature_id=r['feature_id'] if r else '',
                observed_N=r['Normoxia_n_TPM_ge1'] if r else '',observed_H=r['Hypoxia_n_TPM_ge1'] if r else '',
                expected_N=q['Normoxia_n_TPM_ge1'] if q else '',expected_H=q['Hypoxia_n_TPM_ge1'] if q else '',
                status='PASS' if same else 'DIFFERENCE',**{s:r[s] if r else '' for s in header[1:]}))
        for k in sets:
            for gid in sorted(sets[k]^old[k]):set_diffs.append(dict(candidate_id=cid,set_name=k,gene_id=gid,kind='RAW_TPM_ONLY' if gid in sets[k] else 'PACKAGED_ONLY'))
        expression_comparison.append(dict(candidate_id=cid,matched_genes=len(genes),**{k:len(v) for k,v in sets.items()},**{'expected_'+k:len(v) for k,v in old.items()},set_difference_count=sum(len(sets[k]^old[k]) for k in sets)))
    table(a.output/'expression_per_gene.tsv.gz',per_gene)
    table(a.output/'expression_gene_differences.tsv',[r for r in per_gene if r['status']!='PASS'],list(per_gene[0]))
    table(a.output/'expression_set_differences.tsv',set_diffs,['candidate_id','set_name','gene_id','kind'])
    table(a.output/'expression_candidate_comparison.tsv',expression_comparison)
    status=dict(kind='INDEPENDENT_CODE_PATH_NOT_INDEPENDENT_BIOLOGICAL_TRUTH',started_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime(started)),seconds=round(time.time()-started,3),exit_status=0,
        seed_candidates=len(guides),reference_transcripts=len(bytx),seed_site_differences=len(differences),seed_gene_count_differences=sum(r['status']!='PASS' for r in gene_counts),
        seed_transcript_count_differences=sum(r['status']!='PASS' for r in transcript_counts),
        expression_gene_differences=sum(r['status']!='PASS' for r in per_gene),expression_set_differences=len(set_diffs),mapping_issues=len(mapping_issues),raw_tpm_duplicate_features=tpm_duplicates,
        input_files=inventory,static_mapping=str(mapping_path),static_mapping_columns_only=True,shared_dependencies=['raw TPM measurements','static feature-to-Entrez mapping','representative UTR FASTA/manifest','official guide and mer7m8 definition'],
        not_performed=['independent biological measurements','independent OligoFormer inference','new model answers','human quality ratings'],production_functions_imported=False)
    (a.output/'run.json').write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in status.items() if k!='input_files'},ensure_ascii=True))

if __name__=='__main__':main()
