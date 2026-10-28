"""Deterministic expression IO and native R dispatch. No scoring or DE inference."""
import csv, gzip, hashlib, html, json, math, os, shutil, subprocess
from pathlib import Path
from expression_data import SAMPLES, parse_tpm

ROOT=Path(__file__).resolve().parent
VERSION='candidate-expression-figures-v1'

def write_tsv(path, rows, fields=None):
    opener=gzip.open if str(path).endswith('.gz') else open
    with opener(path,'wt',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields or list(rows[0]),delimiter='\t',lineterminator='\n')
        w.writeheader();w.writerows(rows)

def prepare(candidates, seed_rows, expression_rows):
    """Validate TPM afresh; zero-match, missing-map and undetected remain distinct."""
    ids=[c['candidate_id'] for c in candidates]
    if not ids or len(ids)>20 or len(set(ids))!=len(ids):raise ValueError('需要1至20条唯一候选')
    # Same validator as uploads; summaries are recomputed from the eight raw TPM columns.
    import io
    buf=io.StringIO();w=csv.DictWriter(buf,fieldnames=['ENTREZID','approved_symbol',*SAMPLES],delimiter='\t',extrasaction='ignore')
    w.writeheader();w.writerows(expression_rows)
    validated=parse_tpm(buf.getvalue());genes={r['ENTREZID']:r for r in validated}
    original={r['ENTREZID']:r for r in expression_rows}
    for gid,r in genes.items():r['feature_id']=original[gid].get('feature_id',r['feature_id'])
    matched={cid:set() for cid in ids}
    for r in seed_rows:
        cid=r['candidate_id']
        if cid not in matched:raise ValueError('匹配表包含本次未选择的候选')
        n=float(r['seed_site_count'])
        if not math.isfinite(n) or n<0 or not n.is_integer():raise ValueError('seed位点数无效')
        if n>0 and r['gene_id']!='7422':matched[cid].add(r['gene_id'])
    summary=[];union=set()
    for cid in ids:
        all_ids=matched[cid];mapped=all_ids&genes.keys();union.update(mapped)
        nor={g for g in mapped if genes[g]['Normoxia_n_TPM_ge1']>=2}
        hyp={g for g in mapped if genes[g]['Hypoxia_n_TPM_ge1']>=2}
        summary.append({'candidate_id':cid,'matched_genes':len(all_ids),'mapped':len(mapped),'unmapped':len(all_ids-mapped),
            'N':len(nor),'H':len(hyp),'both':len(nor&hyp),'N_only':len(nor-hyp),'H_only':len(hyp-nor),'neither':len(mapped-(nor|hyp))})
    top=[dict(r) for r in sorted((genes[g] for g in union),key=lambda r:(-sum(r[s] for s in SAMPLES)/8,r['approved_symbol'],int(r['ENTREZID'])))[:20]]
    # Gene IDs are the keys; symbols are labels and need not be unique.
    label_count={r['approved_symbol']:sum(x['approved_symbol']==r['approved_symbol'] for x in top) for r in top}
    for i,r in enumerate(top,1):
        r['display_rank']=i;r['display_label']=r['approved_symbol']+((' ['+r['ENTREZID']+']') if label_count[r['approved_symbol']]>1 else '')
        r['TPM_all8_mean']=sum(r[s] for s in SAMPLES)/8
    matrix=[{'candidate_id':cid,'ENTREZID':r['ENTREZID'],'display_label':r['display_label'],'matched':int(r['ENTREZID'] in matched[cid])} for r in top for cid in ids]
    long=[{'ENTREZID':r['ENTREZID'],'display_label':r['display_label'],'sample':s,'TPM':r[s]} for r in top for s in SAMPLES]
    return {'summary':summary,'top':top,'matrix':matrix,'long':long,'expression':list(genes.values())}

def rscript_path():
    # Server-side administrator setting only; never accept executable paths from HTTP input.
    explicit=os.environ.get('RPE_PLOT_RSCRIPT')
    if explicit:
        if not Path(explicit).is_file():raise ValueError('配置的Rscript不存在；未生成替代图片')
        return explicit
    found=shutil.which('Rscript')
    if found:return found
    windows=Path('C:/Program Files/R/R-4.5.1/bin/Rscript.exe')
    if windows.is_file():return str(windows)
    raise ValueError('此服务未安装R绘图运行环境；已保留表达关联表，未声称作图成功')

def render(session):
    from core import save_json, sha
    session.require('query_expression')
    folder=session.path/'expression_figures';folder.mkdir(exist_ok=True)
    result=prepare(session.state['inspect_candidates']['rows'],session.seed_rows,session.expression_rows)
    write_tsv(folder/'candidate_summary.tsv',result['summary'])
    write_tsv(folder/'top20_selection.tsv',result['top'],['feature_id','approved_symbol','ENTREZID',*SAMPLES,'TPM_Normoxia_mean','Normoxia_n_TPM_ge1','TPM_Hypoxia_mean','Hypoxia_n_TPM_ge1','display_rank','display_label','TPM_all8_mean'])
    write_tsv(folder/'match_matrix.tsv',result['matrix'],['candidate_id','ENTREZID','display_label','matched'])
    write_tsv(folder/'expression_long.tsv',result['long'],['ENTREZID','display_label','sample','TPM'])
    write_tsv(folder/'expression_snapshot.tsv.gz',result['expression'])
    write_tsv(folder/'seed_snapshot.tsv',session.seed_rows,['candidate_id','gene_id','seed_site_count']) if not session.seed_rows else write_tsv(folder/'seed_snapshot.tsv',session.seed_rows)
    save_json(folder/'candidate_snapshot.json',session.candidates)
    rules={'version':VERSION,'samples':SAMPLES,'candidate_ids':[r['candidate_id'] for r in result['summary']],
        'detected':'TPM >= 1 in >= 2 of 4 vessels per state','excluded_target_entrez':'7422',
        'top20':'Unique mapped non-target genes in the union of positive guide seed matches; mean TPM across all eight descending, symbol then numeric Entrez tie-break. No DE/FDR/direction filter.',
        'venn':'Counts exact; circle areas schematic, not proportional; neither is below detection criterion in both states, not zero expression; unmapped is unknown.',
        'heatmap':'log2(TPM+1), no row standardization; same gene order and color limits across pages; top20 are display only, full matches retained.',
        'expression_source':session.expression_source,'seed_source':session.state['match_seed'],
        'provenance':'Current run candidates; seed mode recorded separately. Imported historical matches are not a new sequence screen.',
        'ranking_changed':False,'font':'Arial Bold','width_inches':10,'height_inches':7,'title_pt':24,'main_label_pt':18,'dense_label_pt':16}
    save_json(folder/'settings.json',rules)
    script=ROOT/'workers/expression_figures.R';shutil.copy2(script,folder/'expression_figures.R')
    try:
        executable=rscript_path()
        proc=subprocess.run([executable,'--vanilla',str(script),str(folder)],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180,check=False)
        (folder/'render.log').write_text(proc.stdout+'\n'+proc.stderr,encoding='utf-8')
        if proc.returncode:raise ValueError('R绘图未完成，查看expression_figures/render.log；没有返回成功图片')
        pdf=folder/'candidate_expression.pdf'
        if not pdf.is_file() or pdf.stat().st_size<1000:raise ValueError('R未产生有效PDF')
        pages=json.loads((folder/'render_receipt.json').read_text(encoding='utf-8'))
        files={p.name:sha(p) for p in folder.iterdir() if p.is_file() and p.name not in ('manifest.json','report.html')}
        manifest={'status':'COMPLETE','version':VERSION,'run_id':session.id,'renderer':'native R','model_called_by_plot_tool':False,'settings':'settings.json','files':files,**pages}
        save_json(folder/'manifest.json',manifest)
        images=''.join('<section><img style="width:100%;height:auto" src="'+html.escape(n,quote=True)+'"></section>' for n in pages['png_files'])
        captions=''.join('<p>'+html.escape(rules[k])+'</p>' for k in ('top20','venn','heatmap','provenance'))
        (folder/'report.html').write_text('<!doctype html><meta charset="utf-8"><title>Candidate expression background</title><style>body{max-width:1100px;margin:24px auto;font:16px Arial}section{margin:24px 0}</style><h1>Candidate expression background</h1><a href="candidate_expression.pdf">PDF</a> · <a href="manifest.json">Versions and checksums</a><p>All eight untreated vessels retained. Expression annotation does not alter candidate ranking. Seed matches do not demonstrate experimental off-target effects.</p>'+captions+images,encoding='utf-8')
        return {'status':'COMPLETE','candidate_count':len(result['summary']),'display_gene_count':len(result['top']),
                'pdf':'expression_figures/candidate_expression.pdf','report':'expression_figures/report.html','manifest':'expression_figures/manifest.json','ranking_changed':False,'pages':pages['pages']}
    except (OSError,ValueError,subprocess.TimeoutExpired) as exc:
        save_json(folder/'failure.json',{'status':'FAILED','message':str(exc),'tables_retained':True})
        raise ValueError(str(exc)) from exc
