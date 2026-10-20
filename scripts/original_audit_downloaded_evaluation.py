from pathlib import Path
import zipfile,json,hashlib,csv,collections,shutil,html
import numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];SOURCE=Path(r'C:\Users\86182\Downloads\development_evaluation.zip')
OUT=ROOT/'deliverables/evaluation_audit_20261019';OUT.mkdir(exist_ok=True)
with zipfile.ZipFile(SOURCE) as z:
 assert z.testzip() is None
 protocol=json.loads(z.read('protocol.json'));completion=json.loads(z.read('completion.json'));results=json.loads(z.read('results.json'));cases=json.loads(z.read('cases.json'))
 assert len(results)==54 and len({r['answer_id'] for r in results})==54
 expected={(c['id'],g,n) for c in cases['cases'] for g in protocol['groups'] for n in range(1,4)}
 assert {(r['case_id'],r['group'],r['repeat']) for r in results}==expected
 for row,job in zip(results,protocol['scheduled_order']):
  assert (row['case_id'],row['group'],row['repeat'])==(job['case_id'],job['group'],job['repeat'])
  assert json.loads(z.read(row['answer_id']+'/result.json'))==row
 rows=[]
 for r in results:
  error=r.get('record',{}).get('result') or {}
  limited=error.get('provider_code')=='SetLimitExceeded' or 'SetLimitExceeded' in r.get('answer','')
  if r['group'] in ('agent','llm'):assert limited and r['status']=='FAILED'
  if r['group']=='agent':assert r['tool_calls']==0
  category='ACCOUNT_LIMIT_BLOCKED' if limited else 'FULL_WORKFLOW_COMPLETE' if r['status']=='COMPLETE' else 'REQUESTED_PARTIAL_COMPLETE' if r['status']=='PARTIAL_COMPLETE' else 'WORKFLOW_STOP_ON_INVALID_INPUT'
  rows.append({'answer_id':r['answer_id'],'case_id':r['case_id'],'group':r['group'],'repeat':r['repeat'],'raw_status':r['status'],'audit_category':category,'provider_code':'SetLimitExceeded' if limited else '',
   'seconds':r.get('seconds') if r.get('seconds') is not None else 'NOT_RECORDED','tool_calls':r.get('tool_calls',0),
   'token_usage':'NOT_RETURNED_BY_PROVIDER' if limited else r.get('total_tokens',0),'eligible_for_scientific_quality_comparison':False})
 for g in ['agent','llm','workflow']:assert sum(r['group']==g for r in rows)==18
 # Verify normal scientific outputs for all six complete fixed runs.
 verified=[]
 for r in results:
  if r['group']!='workflow' or r['status']!='COMPLETE':continue
  names=[n for n in z.namelist() if n.startswith(r['answer_id']+'/') and n.endswith('/report.json')]
  assert len(names)==1;report=json.loads(z.read(names[0]));assert report['expression_changes_ranking'] is False
  assert len(report['rows'])==9
  assert all(x['covered_transcripts']==20 for x in report['rows'])
  assert abs(float(report['expression']['TPM_Hypoxia_mean'])-102.390068)<1e-6
  verified.append({'answer_id':r['answer_id'],'case_id':r['case_id'],'repeat':r['repeat'],'selected_for_review':report['selected_for_review'],'state':report['task']['state'],'target_TPM_H':report['expression']['TPM_Hypoxia_mean'],'target_TPM_N':report['expression']['TPM_Normoxia_mean']})
 for cid in ['normal_hypoxia','normal_normoxia']:
  assert len({json.dumps(r['selected_for_review']) for r in verified if r['case_id']==cid})==1
shutil.copy2(SOURCE,OUT/'original_development_evaluation.zip')
with (OUT/'all_54_records_audited.tsv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t');w.writeheader();w.writerows(rows)
(OUT/'verified_fixed_workflow_reports.json').write_text(json.dumps(verified,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'archive_verification.json').write_text(json.dumps({'archive_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'zip_crc_valid':True,'unique_answers':54,'complete_group_case_repeat_grid':True,'per_answer_files_equal_summary':True,'order_matches_protocol':True,'protocol':protocol,'completion':completion,'scientific_comparison_valid':False,'limitation':'All 36 model-dependent cases were blocked by account limit; cannot infer scientific superiority; provider usage absent.'},ensure_ascii=False,indent=2),encoding='utf-8')

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'svg.fonttype':'none'})
def save(fig,name):
 for ext in ['png','svg','pdf']:fig.savefig(OUT/(name+'.'+ext),dpi=300,bbox_inches='tight',facecolor='white')
 plt.close(fig)
fig,ax=plt.subplots(figsize=(8,4.8));groups=['llm','workflow','agent'];left=np.zeros(3)
for cat,color,label in [('ACCOUNT_LIMIT_BLOCKED','#CD8B83','Account limit: model unavailable'),('WORKFLOW_STOP_ON_INVALID_INPUT','#DCC58C','Stopped on invalid workflow input'),('REQUESTED_PARTIAL_COMPLETE','#91B6CC','Requested partial workflow complete'),('FULL_WORKFLOW_COMPLETE','#78AC97','Full workflow complete')]:
 count=np.array([sum(r['group']==g and r['audit_category']==cat for r in rows) for g in groups]);bars=ax.barh(range(3),count,left=left,color=color,label=label)
 for i,n in enumerate(count):
  if n:ax.text(left[i]+n/2,i,str(n),ha='center',va='center')
 left+=count
ax.set(yticks=range(3),yticklabels=['Ordinary LLM','Fixed workflow','Agent'],xlim=(0,18.6),xlabel='Recorded scheduled entries',title='Batch audit: infrastructure outcomes, NOT scientific accuracy');ax.legend(loc='upper center',bbox_to_anchor=(.5,-.2),ncol=1,frameon=False,fontsize=9)
save(fig,'Audit01_infrastructure_outcomes')
fig,axes=plt.subplots(1,3,figsize=(12,4.7));ids=[c['id'] for c in cases['cases']];labels=['Hypoxia full','Normoxia full','Target only','Bad guide','KRAS','No strand']
from matplotlib.colors import ListedColormap
for ax,g in zip(axes,groups):
 matrix=np.array([[0 if next(r for r in rows if r['group']==g and r['case_id']==cid and r['repeat']==rep)['audit_category']=='ACCOUNT_LIMIT_BLOCKED' else 1 if cid in ids[3:] else 2 for rep in range(1,4)] for cid in ids])
 ax.imshow(matrix,cmap=ListedColormap(['#CD8B83','#DCC58C','#78AC97']),vmin=0,vmax=2,aspect='auto')
 for i in range(6):
  for j in range(3):ax.text(j,i,['Limit','Stop','Done'][matrix[i,j]],ha='center',va='center',fontsize=9)
 ax.set(xticks=range(3),xticklabels=['R1','R2','R3'],yticks=range(6),yticklabels=labels if g=='llm' else [],title={'llm':'Ordinary LLM','workflow':'Fixed workflow','agent':'Agent'}[g])
fig.suptitle('All 54 records retained; blocked model cases are not quality scores')
save(fig,'Audit02_complete_record_grid')
fig,ax=plt.subplots(figsize=(8.8,4.5))
for i,cid in enumerate(ids):
 values=[float(r['seconds']) for r in rows if r['group']=='workflow' and r['case_id']==cid and r['seconds']!='NOT_RECORDED'];ax.scatter(i+np.linspace(-.08,.08,len(values)),values,color='#427D9D');ax.hlines(np.median(values),i-.2,i+.2,color='#427D9D')
ax.set(xticks=range(6),xticklabels=['Hypoxia','Normoxia','Target only','Bad guide','KRAS','No strand'],ylabel='Cloud wall time (seconds)',title='Fixed workflow only: three repeats per case, historical imports')
save(fig,'Audit03_fixed_cloud_runtime')
report='''# 下载批次核查结果

批次 dev_20261019_141929_60c55b 于2026-10-19 22:19:29至22:20:58（北京时间）记录了54项任务。外层COMPLETE仅表示循环结束，不表示模型成功回答。

## 核查结论

- ZIP校验通过；54个唯一答案ID，6题×3组×3次齐全；逐条文件与汇总一致，顺序与协议一致。
- 普通LLM 18/18、Agent 18/18均遇到账号模型累计用量上限：429 / SetLimitExceeded。Agent没有调用任何科学工具。不能把这些失败当成推理能力差，也不能由此说固定脚本优于Agent。
- 固定流程18条：6次完整完成、3次完成指定的局部核对、9次在预设异常输入处停止。6份完整报告的候选数、20条参考覆盖、表达数据及同题重复的一致性已核对。
- 模型未返回可用token用量；Agent旧记录中的0和普通LLM的缺失都标为“服务端未返回”，不能推断实际费用为0。
- 此批不能用于三组科学质量、答案准确率、正常模型响应耗时或优越性比较。原始记录完整保留，不删除，不混入下一批成功记录。

## 需要处理的账号问题

登录火山方舟控制台→开通管理，找到doubao-seed-2-1-pro，查看“模型用量上限/安心体验模式”和已用额度。官方对SetLimitExceeded的说明是达到已设置的模型用量上限、模型服务已暂停，不是网页搜索未开通，也不能仅由此认定账户余额不足。请先确认用量和计费情况；若愿意继续，设置你接受的有限额度。无需为本项目直接关闭全部上限。

官方依据：https://console.volcengine.com/ark/region:cn-beijing/docs/error-codes

## 程序修复

新增区分账号累计限额与瞬时限流：SetLimitExceeded不自动重试；批次在首个账号/账务/鉴权阻断后停止并保留原始记录，待执行任务单独计数。普通LLM异常也记录耗时和结构化错误；Agent保留同样错误码。缺失用量不填0。页面区分“批次结束”和“全部成功”，支持下载账号阻断后的记录。

恢复后先点“检测模型与联网”，确认模型连接成功，再手动启动一个全新三组批次。不要把本批失败替换为新结果，或与旧本地固定流程凑成配对数据。后续正式质量评价仍需专家审核独立题目和评分标准。

## 文件

original_development_evaluation.zip为用户下载的原包，逐字节保留；all_54_records_audited.tsv为每条审计分类；archive_verification.json为输入校验和协议；verified_fixed_workflow_reports.json为6份完整报告核查结果。

Audit01和Audit02仅展示基础设施结果，不是准确率图。Audit03仅展示当前云端固定流程耗时，不能拿账号报错的耗时与正常模型执行比较。每图含PNG、SVG、PDF。
'''
(OUT/'先读这个_批次核查.md').write_text(report,encoding='utf-8')
page='<meta charset="utf-8"><title>三组批次核查</title><style>body{font:16px/1.8 system-ui;max-width:1000px;margin:30px auto;padding:20px}pre{white-space:pre-wrap}img{max-width:100%}</style><pre>'+html.escape(report)+'</pre>'
for n in ['Audit01_infrastructure_outcomes','Audit02_complete_record_grid','Audit03_fixed_cloud_runtime']:page+='<img src="'+n+'.png">'
(OUT/'打开这个_批次核查.html').write_text(page,encoding='utf-8')
shutil.copy2(__file__,OUT/'audit_downloaded_evaluation.py')
archive=OUT.parent/'evaluation_audit_20261019.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for p in OUT.rglob('*'):
  if p.is_file():z.write(p,OUT.name+'/'+str(p.relative_to(OUT)))
print(json.dumps({'records':len(rows),'model_blocked':sum(r['audit_category']=='ACCOUNT_LIMIT_BLOCKED' for r in rows),'fixed_reports_verified':len(verified),'archive':str(archive),'bytes':archive.stat().st_size},ensure_ascii=True))
