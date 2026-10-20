"""Audit a downloaded real pilot ZIP. Execution statistics, never quality scores."""
import argparse,collections,csv,gzip,hashlib,io,json,re,statistics,zipfile
from pathlib import Path

def write_tsv(path,rows,fields):
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,delimiter='\t');w.writeheader();w.writerows(rows)

def main():
    p=argparse.ArgumentParser();p.add_argument('--archive',required=True);p.add_argument('--output',required=True);p.add_argument('--plot',action='store_true');a=p.parse_args()
    src=Path(a.archive);out=Path(a.output)
    if out.exists() and any(out.iterdir()):p.error('Use a new empty directory')
    out.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(src) as z:
        assert z.testzip() is None,'ZIP CRC failed'
        protocol=json.loads(z.read('protocol.json'));cases=json.loads(z.read('cases.json'));results=json.loads(z.read('results.json'));completion=json.loads(z.read('completion.json'))
        jobs=protocol['scheduled_order'];key=lambda r:(r['case_id'],r['group'],r['repeat'])
        assert len(jobs)==54 and len({key(r) for r in jobs})==54
        assert len({r['answer_id'] for r in results})==len(results)
        assert [key(r) for r in results]==[key(r) for r in jobs[:len(results)]]
        assert protocol['web_enabled'] is False and protocol['repeats']==3
        assert len(cases['cases'])==6 and set(protocol['groups'])=={'llm','workflow','agent'}
        for r in results:assert r==json.loads(z.read(r['answer_id']+'/result.json'))
        for name in ['protocol.json','cases.json','completion.json']:(out/name).write_bytes(z.read(name))
        review=out/'for_review';review.mkdir()
        (review/'blind_answers.tsv').write_bytes(z.read('blind_answers.tsv'))
        (out/'private_key.tsv').write_bytes(z.read('private_key.tsv'))
        blind=list(csv.DictReader(io.StringIO(z.read('blind_answers.tsv').decode('utf-8-sig')),delimiter='\t'))
        assert len(blind)==len(results) and {r['answer_id'] for r in blind}=={r['answer_id'] for r in results}
    (out/'results.json.gz').write_bytes(gzip.compress(json.dumps(results,ensure_ascii=False).encode('utf-8'),mtime=0))
    rows=[]
    for r in results:
        workflow=r['group']=='workflow'
        scientific_attempts=(r.get('tool_calls',0) if workflow else sum(e.get('kind')=='tool_started' for e in r.get('record',{}).get('events',[])))
        research_attempts=sum(len(e.get('observations',[])) for e in r.get('record',{}).get('evidence_records',[]))
        error=r.get('provider_error') or (r.get('record',{}).get('result') or {})
        provider_code=error.get('provider_code','')
        diagnostic_source='STRUCTURED' if provider_code else ''
        # Older exports lack structured LLM diagnostics. Parse only the adapter's
        # explicit error header, never infer a provider cause from FAILED alone.
        header=re.search(r'API HTTP (\d+) / ([A-Za-z0-9_.]+)[:：]',r.get('answer',''))
        if not provider_code and header:provider_code=header[2];diagnostic_source='LEGACY_ADAPTER_ERROR_HEADER'
        usage=r.get('usage',[]);known=[u['total_tokens'] for u in usage if isinstance(u.get('total_tokens'),int)]
        complete=workflow or bool(usage) and len(known)==len(usage) and not provider_code
        planner_lost=r['group']=='agent' and bool(r.get('plan')) and not any(e.get('kind')=='planner_finished' for e in r.get('record',{}).get('events',[]))
        if planner_lost:complete=False
        rows.append({'answer_id':r['answer_id'],'case_id':r['case_id'],'group':r['group'],'repeat':r['repeat'],'status':r['status'],
            'all_tool_attempts_raw':r.get('tool_calls'),'scientific_tool_attempts':scientific_attempts,'research_tool_attempts':research_attempts,'seconds':r.get('seconds'),
            'usage_records':len(usage),'usage_complete':complete,'planner_usage_missing_from_export':planner_lost,'total_tokens_audited':sum(known) if complete else None,
            'known_token_subtotal':sum(known) if known or workflow else None,
            'provider_code':provider_code,'provider_diagnostic_source':diagnostic_source,
            'raw_total_tokens':r.get('total_tokens'),'completed_tools':';'.join(r.get('completed_tools',[]))})
    write_tsv(out/'records.tsv',rows,list(rows[0]))
    lookup={key(r):r for r in results}
    schedule=[{**job,'schedule_index':i+1,'answer_id':lookup.get(key(job),{}).get('answer_id',''),
        'execution':'ATTEMPTED' if key(job) in lookup else 'NOT_EXECUTED',
        'status':lookup.get(key(job),{}).get('status','NOT_EXECUTED')} for i,job in enumerate(jobs)]
    write_tsv(out/'execution_status.tsv',schedule,list(schedule[0]))
    grouped=[]
    for group in protocol['groups']:
        sub=[r for r in rows if r['group']==group];seconds=[r['seconds'] for r in sub if isinstance(r['seconds'],(int,float))]
        grouped.append({'group':group,'attempted':len(sub),'status_counts':json.dumps(dict(collections.Counter(r['status'] for r in sub))),
            'provider_error_records':sum(bool(r['provider_code']) for r in sub),'scientific_tool_attempts':sum(r['scientific_tool_attempts'] or 0 for r in sub),
            'usage_unknown_records':sum(not r['usage_complete'] for r in sub),
            'known_token_subtotal':sum(r['known_token_subtotal'] or 0 for r in sub) if any(r['known_token_subtotal'] is not None for r in sub) else None,
            'median_seconds_all_states':statistics.median(seconds) if seconds else None})
    write_tsv(out/'group_summary.tsv',grouped,list(grouped[0]))
    summary={'archive_bytes':src.stat().st_size,'archive_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'zip_crc':'PASS',
        'run_id':protocol['id'],'runtime_commit':protocol['runtime']['commit'],'model':protocol['model'],'planned':54,'attempted':len(results),'pending':54-len(results),
        'completion_status':completion['status'],'groups':grouped,'web_enabled':False,'independent_development_tasks':6,'technical_repeats_per_task':3,
        'scientific_quality_scored':False,'note':'Raw states and timing are not accuracy. Token sums are returned usage only; no monetary cost inferred.'}
    (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    (review/'README.md').write_text('只向评审提供本目录及已冻结题目/评分说明，不提供private_key.tsv或原始ZIP。\n本表去除显式组名，不能保证风格盲法。未代填评分，6题3次是技术重复，不是18道独立题。\n',encoding='utf-8')
    if a.plot:plot(out,rows,cases['cases'])
    print(json.dumps(summary,ensure_ascii=True))

def plot(out,rows,cases):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    from matplotlib.patches import Patch
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'svg.fonttype':'none','pdf.fonttype':42})
    dest=out/'figures';dest.mkdir();groups=['llm','workflow','agent'];ids=[c['id'] for c in cases]
    statuses=sorted({r['status'] for r in rows}|{'NOT_EXECUTED'})
    colors=['#87B9AA','#B5C9DF','#E2B994','#C1B6CD','#D4D8DC','#ECE8D7','#C9A5A5']
    if len(statuses)>len(colors):colors+=['#DDD']*(len(statuses)-len(colors))
    lookup={(r['case_id'],r['group'],r['repeat']):r for r in rows}
    matrix=[[statuses.index(lookup.get((c,g,n),{}).get('status','NOT_EXECUTED')) for g in groups for n in [1,2,3]] for c in ids]
    fig,ax=plt.subplots(figsize=(12,5));ax.imshow(matrix,cmap=ListedColormap(colors[:len(statuses)]),vmin=-.5,vmax=len(statuses)-.5,aspect='auto')
    for i,row in enumerate(matrix):
        for j,s in enumerate(row):ax.text(j,i,statuses[s].replace('_','\n'),ha='center',va='center',fontsize=7)
    ax.set(yticks=range(6),yticklabels=ids,xticks=range(9),xticklabels=[g+' R'+str(n) for g in groups for n in [1,2,3]],title='Recorded development batch: raw execution states, not scientific accuracy')
    ax.axvline(2.5,color='white',lw=3);ax.axvline(5.5,color='white',lw=3)
    save(fig,dest,'Dev01_execution_states')
    fig,axes=plt.subplots(2,3,figsize=(12,7));palette=['#7E8994','#6089AE','#38836F']
    for ax,c in zip(axes.flat,ids):
        for j,g in enumerate(groups):
            data=[r for r in rows if r['case_id']==c and r['group']==g and not r['provider_code'] and isinstance(r['seconds'],(int,float))]
            ax.scatter([j+(r['repeat']-2)*.08 for r in data],[r['seconds'] for r in data],color=palette[j],s=30)
        ax.set(title=c,xticks=range(3),xticklabels=groups,ylabel='Wall time (s)',ylim=(0,None));ax.spines[['top','right']].set_visible(False)
    fig.suptitle('Per-task observed latency; API errors excluded; no quality or significance test')
    fig.tight_layout();save(fig,dest,'Dev02_per_task_latency')

def save(fig,dest,name):
    import matplotlib.pyplot as plt
    for ext in ['png','svg','pdf']:fig.savefig(dest/(name+'.'+ext),dpi=250,bbox_inches='tight',facecolor='white')
    plt.close(fig)

if __name__=='__main__':main()
