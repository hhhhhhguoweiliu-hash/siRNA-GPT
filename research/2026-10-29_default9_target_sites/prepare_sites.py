"""Exact IO/coordinate audit of the historical default nine; no new design/prediction."""
import argparse, csv, hashlib, json, re, shutil
from pathlib import Path

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
REFERENCE='NM_003376.6'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read_tsv(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter='\t'))
def write_tsv(p,rows):
    with p.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(rows)
def rc(s):return s.upper().replace('U','T').translate(str.maketrans('ACGT','TGCA'))[::-1]
def fasta(p):
    result={};key=None
    for line in p.read_text(encoding='utf-8').splitlines():
        if line.startswith('>'):key=line[1:].split()[0];result[key]=''
        elif key:result[key]+=line.strip().upper().replace('U','T')
    return result
def genbank(p):
    result={}
    for record in p.read_text(encoding='utf-8').split('\n//'):
        version=re.search(r'^VERSION\s+(\S+)',record,re.M)
        if not version:continue
        seq=re.sub('[^acgtACGT]','',record.split('\nORIGIN',1)[1]).upper()
        cds=re.findall(r'^     CDS\s+(\d+)\.\.(\d+)\s*$',record,re.M)
        # Refuse to guess complicated CDS locations; only simple mature-mRNA ranges.
        assert len(cds)==1,(version.group(1),'CDS is not one simple inclusive interval')
        result[version.group(1)]={'sequence':seq,'cds_start':int(cds[0][0]),'cds_end':int(cds[0][1])}
    return result
def hits(seq,motif):
    return [m.start()+1 for m in re.finditer('(?='+re.escape(motif)+')',seq)]

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source-dir',type=Path,required=True)
    args=parser.parse_args()
    for name in ('inputs','tables','figures','logs','preview'):(OUT/name).mkdir(exist_ok=True)
    sources={'candidates.tsv':ROOT/'data/candidates.tsv','candidate_trace.tsv':ROOT/'research/2026-10-23_candidate_provenance/candidate_trace.tsv',
        'VEGFA.fasta':ROOT/'data/VEGFA.fasta','VEGFA_NM003376.gb':args.source_dir/'VEGFA_NM003376.gb',
        'VEGFA_vendor_versions.gb':args.source_dir/'VEGFA_vendor_versions.gb'}
    for name,p in sources.items():shutil.copy2(p,OUT/'inputs'/name)
    candidates=read_tsv(sources['candidates.tsv']);trace={r['candidate_id']:r for r in read_tsv(sources['candidate_trace.tsv'])}
    refs=fasta(sources['VEGFA.fasta']);records=genbank(sources['VEGFA_vendor_versions.gb']);primary=genbank(sources['VEGFA_NM003376.gb'])[REFERENCE]
    assert len(candidates)==9 and len(refs)==20 and len(primary['sequence'])==3609
    assert primary['sequence']==refs[REFERENCE] and primary['cds_start']==497 and primary['cds_end']==1684
    assert all(records[acc]['sequence']==seq for acc,seq in refs.items())
    rows=[];all_rows=[]
    for c in candidates:
        cid=c['candidate_id'];t=trace[cid];window_start=int(c['target_start_1based']);window_end=int(c['target_end_1based'])
        start=window_start+2;end=window_start+20;guide=c['guide_paired_core_19nt_5to3'];target=rc(guide)
        assert c['design_transcript']==REFERENCE and end-start+1==19 and window_end-window_start+1==23
        assert refs[REFERENCE][start-1:end]==target==c['passenger_paired_core_19nt_5to3'].replace('U','T')
        assert refs[REFERENCE][window_start-1:window_end]==c['target_window_23nt']
        assert int(t['core19_start_1based'])==start and int(t['core19_end_1based'])==end
        assert hits(refs[REFERENCE],target)==[start]
        region='CDS' if primary['cds_start']<=start and end<=primary['cds_end'] else '3UTR' if start>primary['cds_end'] else '5UTR_or_boundary'
        row={'candidate_id':cid,'short_id':cid.removeprefix('VEGFA_SD_'),'reference':REFERENCE,'transcript_length':3609,
            'window23_start':window_start,'window23_end':window_end,'core_start':start,'core_end':end,
            'core_length':19,'reference_region':region,'target19_sense_DNA_5to3':target,'guide19_RNA_5to3':guide,
            'guide21_RNA_5to3':c['guide_21nt_RNA_5to3'],'fixed_reference_transcripts_matched':20}
        rows.append(row)
        for acc,seq in refs.items():
            at=hits(seq,target);assert len(at)==1,(cid,acc,at)
            a=at[0];b=a+18;meta=records[acc]
            kind='CDS' if meta['cds_start']<=a and b<=meta['cds_end'] else '3UTR' if a>meta['cds_end'] else '5UTR_or_boundary'
            all_rows.append({'candidate_id':cid,'transcript_id':acc,'transcript_length':len(seq),'core_start':a,'core_end':b,
                'CDS_start':meta['cds_start'],'CDS_end':meta['cds_end'],'reference_region':kind,'exact_match_count':len(at),
                'target19_sense_DNA_5to3':target,'guide19_RNA_5to3':guide})
    assert sum(r['reference_region']=='CDS' for r in rows)==1 and sum(r['reference_region']=='3UTR' for r in rows)==8
    write_tsv(OUT/'tables/default9_primary_positions.tsv',rows)
    write_tsv(OUT/'tables/default9_all20_transcript_positions.tsv',all_rows)
    regions=[{'region':'5UTR','start':1,'end':496},{'region':'CDS','start':497,'end':1684},{'region':'3UTR','start':1685,'end':3609}]
    write_tsv(OUT/'tables/primary_reference_regions.tsv',regions)
    receipt={'status':'PASS','primary_reference':REFERENCE,'primary_length':3609,'coordinate_system':'mature mRNA; 1-based inclusive; target 19-nt paired core; not genomic coordinates',
        'core_formula':'design window start +2 through +20','candidates':9,'reference_transcripts':20,'candidate_transcript_pairs':len(all_rows),
        'all180_single_exact_matches':True,'primary_CDS_targets':1,'primary_3UTR_targets':8,
        'new_siRNA_design_or_prediction':False,'RNAseq_expression_used_for_positioning':False,
        'reference_policy':'Fixed historical versions; no substitution with current unversioned reference. Reference matches do not establish isoform expression or knockdown.',
        'source_files':[{'name':name,'original_path':str(p),'sha256':sha(p)} for name,p in sources.items()],
        'existing_figure_search':'Found 20-reference coverage-count bar chart and 65-candidate position-versus-score plot; no default-nine target-interval diagram found in searched local files.',
        'prior_related_figure':'research/2026-10-20_takeover/figures/Fig04_transcript_coverage.png'}
    (OUT/'logs/sequence_coordinate_audit.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'status':'PASS','positions':[(r['short_id'],r['core_start'],r['core_end'],r['reference_region']) for r in rows],'exact_pairs':len(all_rows)}))
