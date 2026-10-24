"""One explicitly selected evidence dataset, separate from the historical nine."""
import gzip,csv,hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parent
DATASET='purchased_sivegf_20261024_v1'
DIRECTORY=ROOT/'data'/DATASET
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load():
 m=json.loads((DIRECTORY/'manifest.json').read_text(encoding='utf-8'))
 if m['dataset_id']!=DATASET or sha(ROOT/'data/VEGFA.fasta')!=m['fixed_target_fasta_sha256']:
  raise ValueError('既购结果的固定靶参考版本不一致，停止导入')
 for name,digest in m['files'].items():
  if Path(name).name!=name or sha(DIRECTORY/name)!=digest:raise ValueError('既购证据文件指纹不一致：'+name)
 return m,json.loads((DIRECTORY/'candidate.json').read_text(encoding='utf-8')),json.loads((DIRECTORY/'verified_local_result.json').read_text(encoding='utf-8'))
def candidates():return [load()[1]]
def bind(candidate,verified=None):
 if candidate.get('evidence_dataset_id')!=DATASET:
  if candidate.get('candidate_id')=='USER_PURCHASED_siVEGF':raise ValueError('既购序列需显式选择其独立证据版本，不能套用旧九条')
  return None
 m,expected,result=load()
 for name in ['candidate_id','guide_core19_5to3','passenger_paired_core_19nt_5to3','guide_21nt_RNA_5to3','passenger_21nt_RNA_5to3','strand_assignment_basis','original_modification','original_row1','original_row2']:
  if candidate.get(name)!=expected[name]:raise ValueError('既购证据与输入字段不一致：'+name)
 if verified:
  for name in ['guide_core19_5to3','mRNA_context_57nt','core_start_1based','core_end_1based']:
   if verified.get(name)!=result[name]:raise ValueError('既购结果与核对后靶参考不一致：'+name)
 return {'manifest':m,'candidate':expected,'result':result}
def rows(name):
 with gzip.open(DIRECTORY/name,'rt',encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter='\t'))
def copy_evidence(path):
 dest=path/'verified_import'/DATASET;dest.mkdir(parents=True,exist_ok=True)
 for p in DIRECTORY.iterdir():
  if p.is_file():shutil.copyfile(p,dest/p.name)
 return 'verified_import/'+DATASET+'/manifest.json'
