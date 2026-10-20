"""Read-only CPU adapter for pinned official OligoFormer/RNA-FM code and weights.
No upstream files are modified. No model is trained. Scores are not percentages.
"""
from pathlib import Path
import sys,json,random,hashlib

root=Path(sys.argv[1]);job=json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))
out=Path(sys.argv[3])
sys.path.insert(0,str(root/'official_tools/OligoFormer/scripts'))
sys.path.insert(0,str(root/'official_tools/RNA-FM/source'))
import torch,numpy as np,pandas as pd
from Bio import SeqIO
from infer import calculate_td,func_filter,antiRNA
from model import Oligo
from loader_infer import sequence_OneHot
import fm
torch.set_num_threads(2);random.seed(42);np.random.seed(42);torch.manual_seed(42)
torch.use_deterministic_algorithms(True)
rna,alphabet=fm.pretrained.rna_fm_t12(str(root/'official_tools/RNA-FM/RNA-FM_pretrained.pth'))
rna=rna.cpu().eval();convert=alphabet.get_batch_converter()
model=Oligo(vocab_size=26,embedding_dim=128,lstm_dim=32,n_head=8,n_layers=1,lm1=19,lm2=19).cpu()
model.load_state_dict(torch.load(str(root/'official_tools/OligoFormer/model/best_model.pth'),map_location='cpu'),strict=True)
model.eval();cache={}
def embedding(seq):
 if seq not in cache:
  _,_,tokens=convert([('RNA',seq)])
  with torch.no_grad():cache[seq]=rna(tokens,repr_layers=[12],return_contacts=False)['representations'][12][0,1:1+len(seq)].cpu()
  assert tuple(cache[seq].shape)==(len(seq),640) and torch.isfinite(cache[seq]).all()
 return cache[seq]
def predict(guide,context):
 assert len(guide)==19 and len(context)==57
 td=calculate_td(pd.DataFrame({'siRNA':[guide],'mRNA':[context]})).td.iloc[0]
 si=torch.tensor(sequence_OneHot(list(guide)).T[None,None,:,:],dtype=torch.float64)
 mr=torch.tensor(sequence_OneHot(list(context)).T[None,None,:,:],dtype=torch.float64)
 with torch.no_grad():p,_,_=model(si,mr,embedding(guide)[None,:,:],embedding(context)[None,:,:],torch.tensor([td],dtype=torch.float32))
 raw=float(p[:,1].item());assert np.isfinite(raw)
 return {'raw_class1':raw,'oligoformer_scaled_score':raw*1.341,'official_func_filter':int(func_filter([guide])[0])}
def context_for(mrna,guide):
 p=mrna.find(antiRNA(guide))
 if p<0:return None
 c='X'*max(0,19-p)+mrna[max(0,p-19):p+38]+'X'*max(0,p+38-len(mrna))
 assert len(c)==57
 return c
examples=[]
for mr in SeqIO.parse(root/'official_tools/OligoFormer/data/example.fa','fasta'):
 for gr in SeqIO.parse(root/'official_tools/OligoFormer/data/example_siRNA.fa','fasta'):
  g=str(gr.seq).upper().replace('T','U');m=str(mr.seq).upper().replace('T','U');c=context_for(m,g)
  if c:
   a=predict(g,c);b=predict(g,c);assert a==b
   examples.append({'mrna_id':mr.id,'guide_id':gr.id,**a,'repeat_identical':True})
assert examples
results=[]
for x in job['candidates']:
 a=predict(x['guide_core19_5to3'],x['mRNA_context_57nt'])
 results.append({'candidate_id':x['candidate_id'],'guide_core19_5to3':x['guide_core19_5to3'],**a})
 print('scored '+x['candidate_id'],flush=True)
out.write_text(json.dumps({'status':'LIVE_EXECUTED','official_examples':examples,'rows':results,'device':'cpu','compatibility':['Python I/O adapter','explicit eval/no_grad','official layer12 token slice','deterministic CPU'],'not_tested':['PITA','TargetScan','toxicity','mismatch model'],'score_not_percent':True},ensure_ascii=False,indent=2),encoding='utf-8')
