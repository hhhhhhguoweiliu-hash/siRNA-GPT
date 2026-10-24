"""Package previously audited, genuine local outputs. No recomputation or API."""
import csv,gzip,hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT/'research/2026-10-24_candidate_v2'
OUT=ROOT/'data/purchased_sivegf_20261024_v1';CID='USER_PURCHASED_siVEGF'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def main():
 if OUT.exists():raise SystemExit('Preserve existing package')
 OUT.mkdir();result=json.loads((SRC/'purchased_siVEGF_separate.json').read_text(encoding='utf-8'))[0]
 original=json.loads((ROOT/'data/user_ordered_sequences/20261024/sequence_records.json').read_text(encoding='utf-8'))
 candidate={'candidate_id':CID,'target_gene':'VEGFA','design_transcript':'NM_003376.6',
  'guide_core19_5to3':result['guide_core19_5to3'],'passenger_paired_core_19nt_5to3':result['passenger_core19_5to3'],
  'guide_21nt_RNA_5to3':result['guide21_original'],'passenger_21nt_RNA_5to3':result['passenger21_original'],
  'source':'User original synthesis DOCX, 20261024; conditional strand assignment',
  'evidence_dataset_id':OUT.name,'strand_assignment_basis':result['strand_assignment_basis'],
  'original_modification':result['original_modification'],'synthesis_status':'ALREADY_PURCHASED_CHEMISTRY_NOT_VERIFIED',
  'original_row1':'GAUAGAGCAAGACAAGAAATT-N3（叠氮基团，用于点击化学）','original_row2':'UUUCUUGUCUUGCUCUAUCTT'}
 save(OUT/'candidate.json',candidate);save(OUT/'verified_local_result.json',result);save(OUT/'original_sequence_records.json',original)
 copied=[]
 for phase,names in [('seed_pilot_02',[CID+'__'+role+suffix for role in ['guide','passenger'] for suffix in ['__counts.tsv.gz','__sites.tsv.gz']]+['sessionInfo.txt','summary.tsv']),
  ('nearfull_pilot',[CID+'__'+role+'__'+kind+'__hits.tsv.gz' for role in ['guide','passenger'] for kind in ['paired_core19','sidirect_g2g20']]+['sessionInfo.txt','summary.tsv']),
  ('oligo_pilot_02',['result.json','runtime.json'])]:
  for name in names:
   p=SRC/phase/name
   if not p.exists():
    if name=='runtime.json':continue
    raise FileNotFoundError(p)
   dest=OUT/(phase+'__'+name);shutil.copyfile(p,dest);copied.append({'package_file':dest.name,'source':p.relative_to(ROOT).as_posix(),'sha256':sha(p)})
 save(OUT/'upstream_sources.json',copied)
 for name in ['input_assets.json','successful_source_manifest.json','inputs/job_all.json']:
  shutil.copyfile(SRC/name,OUT/Path(name).name)
 manifest={'dataset_id':OUT.name,'status':'VERIFIED_LOCAL_RESULTS_IMPORTED_NOT_RECOMPUTED_ON_SERVER','source_commit':'9dd8831ebc28a42584ba57f288a314ccb5042b2c',
  'fixed_target_fasta_sha256':sha(ROOT/'data/VEGFA.fasta'),'reference_transcript':'NM_003376.6',
  'original_docx_sha256':sha(ROOT/'data/user_ordered_sequences/20261024/sequence_synthesis_original.docx'),
  'source_result':(SRC/'purchased_siVEGF_separate.json').relative_to(ROOT).as_posix(),
  'source_result_sha256':sha(SRC/'purchased_siVEGF_separate.json'),
  'limits':['Strand roles derived assuming both original rows written 5prime to 3prime; not vendor-confirmed',
   'Original TT and row1 N3 retained; exact terminal chemistry/attachment not established',
   'Model uses unmodified 19nt core and 57nt context; N3-linked physical construct not simulated',
   'Offline official computations imported by exact sequence/reference binding; no new score/seed execution'],
  'files':{p.name:sha(p) for p in sorted(OUT.iterdir()) if p.is_file()}}
 save(OUT/'manifest.json',manifest);print(json.dumps({'dataset_id':OUT.name,'files':len(manifest['files']),'bytes':sum(p.stat().st_size for p in OUT.iterdir())}))
if __name__=='__main__':main()
