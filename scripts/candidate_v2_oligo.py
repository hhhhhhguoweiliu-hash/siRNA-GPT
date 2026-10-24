"""Real deterministic CPU inference via pinned, unchanged official OligoFormer/RNA-FM."""
from pathlib import Path
import datetime,hashlib,json,os,random,sys,time
START=time.perf_counter();old=Path(sys.argv[1]);job_path=Path(sys.argv[2]);out=Path(sys.argv[3]);out.mkdir(parents=True,exist_ok=False)
print('START_REAL_OFFICIAL_ADAPTER',flush=True)
job=json.loads(job_path.read_text(encoding='utf-8'));sys.dont_write_bytecode=True
sys.path.insert(0,str(old/'official_tools/OligoFormer/scripts'));sys.path.insert(0,str(old/'official_tools/RNA-FM/source'))
import torch,numpy as np,pandas as pd
from Bio import SeqIO
from infer import calculate_td,func_filter,antiRNA
from model import Oligo
from loader_infer import sequence_OneHot
import fm
IMPORT_SECONDS=time.perf_counter()-START
print('IMPORT_SECONDS',IMPORT_SECONDS,flush=True)
torch.set_num_threads(2);random.seed(42);np.random.seed(42);torch.manual_seed(42);torch.use_deterministic_algorithms(True)
t=time.perf_counter()
rna,alphabet=fm.pretrained.rna_fm_t12(str(old/'official_tools/RNA-FM/RNA-FM_pretrained.pth'));rna=rna.cpu().eval();convert=alphabet.get_batch_converter()
model=Oligo(vocab_size=26,embedding_dim=128,lstm_dim=32,n_head=8,n_layers=1,lm1=19,lm2=19).cpu()
model.load_state_dict(torch.load(str(old/'official_tools/OligoFormer/model/best_model.pth'),map_location='cpu'),strict=True);model.eval()
LOAD_SECONDS=time.perf_counter()-t;cache={}
print('WEIGHT_LOAD_SECONDS',LOAD_SECONDS,flush=True)
def save(name,value):(out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def embedding(seq):
 if seq not in cache:
  _,_,tokens=convert([('RNA',seq)])
  with torch.no_grad():cache[seq]=rna(tokens,repr_layers=[12],return_contacts=False)['representations'][12][0,1:1+len(seq)].cpu()
  assert tuple(cache[seq].shape)==(len(seq),640) and torch.isfinite(cache[seq]).all()
 return cache[seq]
def predict(g,c):
 assert len(g)==19 and len(c)==57
 td=calculate_td(pd.DataFrame({'siRNA':[g],'mRNA':[c]})).td.iloc[0]
 si=torch.tensor(sequence_OneHot(list(g)).T[None,None,:,:],dtype=torch.float64);mr=torch.tensor(sequence_OneHot(list(c)).T[None,None,:,:],dtype=torch.float64)
 with torch.no_grad():pred,_,_=model(si,mr,embedding(g)[None,:,:],embedding(c)[None,:,:],torch.tensor([td],dtype=torch.float32))
 value=float(pred[:,1].item());assert np.isfinite(value)
 return {'raw_class1':value,'oligoformer_scaled_score':value*1.341,'official_func_filter':int(func_filter([g])[0])}
t=time.perf_counter();examples=[]
for mr in SeqIO.parse(old/'official_tools/OligoFormer/data/example.fa','fasta'):
 for gr in SeqIO.parse(old/'official_tools/OligoFormer/data/example_siRNA.fa','fasta'):
  g=str(gr.seq).upper().replace('T','U');m=str(mr.seq).upper().replace('T','U');p=m.find(antiRNA(g))
  if p<0:continue
  c='X'*max(0,19-p)+m[max(0,p-19):p+38]+'X'*max(0,p+38-len(m));a=predict(g,c);b=predict(g,c);assert a==b
  examples.append({'mrna_id':mr.id,'guide_id':gr.id,'guide19':g,'context57':c,**a,'repeat_identical':True})
assert examples
save('official_examples.json',examples);EXAMPLE_SECONDS=time.perf_counter()-t
# Check adapter layout against the official Dataset/DataLoader on the same example.
from loader import data_process_loader_infer
q=out/'official_loader_qa/data/infer/QA'
example=examples[0]
for role,key in [('siRNA','guide19'),('mRNA','context57')]:
 folder=q/role/'representations';folder.mkdir(parents=True,exist_ok=True)
 np.save(folder/'RNA0.npy',embedding(example[key]).numpy())
 (q/(role+'.fa')).write_text('>RNA0\n'+example[key]+'\n',encoding='utf-8')
df=calculate_td(pd.DataFrame({'siRNA':[example['guide19']],'mRNA':[example['context57']]}));cwd=os.getcwd()
try:
 os.chdir(out/'official_loader_qa');ds=data_process_loader_infer(df.index.values,df,'QA')
 batch=next(iter(torch.utils.data.DataLoader(ds,batch_size=1,shuffle=False,num_workers=0)))
 with torch.no_grad():pred,_,_=model(*batch)
 assert float(pred[:,1].item())==example['raw_class1']
finally:os.chdir(cwd)
save('official_loader_parity.json',{'exact_equality':True,'raw_class1':example['raw_class1'],'upstream_sources_modified':False})
rows=[]
for item in job['candidates']:
 t=time.perf_counter();value=predict(item['guide_core19_5to3'],item['mRNA_context_57nt'])
 row={'candidate_id':item['candidate_id'],'guide_core19_5to3':item['guide_core19_5to3'],'mRNA_context_57nt':item['mRNA_context_57nt'],**value,
  'prediction_seconds':time.perf_counter()-t,'status':'COMPLETED_REAL_NEW_LOCAL_EXECUTION','origin':item['origin']}
 rows.append(row);save('rows_checkpoint.json',rows);print(json.dumps(row),flush=True)
manifest={'status':'COMPLETE','planned_units':len(job['candidates']),'completed_units':len(rows),'rows':rows,
 'import_seconds':IMPORT_SECONDS,'weight_load_seconds':LOAD_SECONDS,'official_examples_seconds':EXAMPLE_SECONDS,'total_worker_seconds':time.perf_counter()-START,
 'started_from_job_sha256':hashlib.sha256(job_path.read_bytes()).hexdigest(),'protocol_sha256':job['scientific_protocol_sha256'],
 'python':sys.version,'torch':torch.__version__,'numpy':np.__version__,'pandas':pd.__version__,'cpu_threads':2,'seed':42,
 'compatibility':['Existing deterministic CPU adapter','explicit eval/no_grad','official RNA-FM layer12 tokens[1:1+length]','official features/model/weights unchanged','official loader equality checked'],
 'score_interpretation':'Prediction for unmodified paired-core and reference context; not measured knockdown or modified/conjugated product efficacy',
 'not_executed':['PITA','TargetScan','toxicity','mismatch model','training','wet experiments']}
save('result.json',manifest);print('COMPLETE '+str(len(rows)),flush=True)
