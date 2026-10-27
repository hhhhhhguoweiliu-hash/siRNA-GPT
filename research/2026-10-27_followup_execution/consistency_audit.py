"""Conditional arithmetic checks of saved tool records and delivered tables.

Unsupported/missing prose fields stay UNCHECKABLE. No truth labels are inferred.
"""
import argparse, collections, csv, io, json, re
from pathlib import Path
from zipfile import ZipFile

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'research/2026-10-27_real_dialogue_mini/raw'
HEADER={'seed位点(含VEGFA)':'all','非靶seed位点':'non','去重非靶匹配基因':'genes',
    '可映射基因':'mapped','常氧检出基因':'N','缺氧检出基因':'H','未映射基因':'unmapped'}

def relations(v):
    specs=[('SITE_PARTITION',['all','non','target'],'all = non + target','sites',lambda x:x['all']==x['non']+x['target']),
        ('GENE_PARTITION',['genes','mapped','unmapped'],'genes = mapped + unmapped','unique genes',lambda x:x['genes']==x['mapped']+x['unmapped']),
        ('N_SUBSET_BOUND',['N','mapped'],'N <= mapped','unique genes',lambda x:x['N']<=x['mapped']),
        ('H_SUBSET_BOUND',['H','mapped'],'H <= mapped','unique genes',lambda x:x['H']<=x['mapped']),
        ('NONNEGATIVE_INTEGERS',list(v),'all supplied counts are nonnegative integers','declared field units',lambda x:all(type(y) is int and y>=0 for y in x.values()))]
    for rid,fields,relation,unit,test in specs:
        complete=bool(fields) and all(k in v for k in fields)
        yield dict(rule=rid,observed=json.dumps(v,sort_keys=True),expected=relation,relation=relation,unit=unit,
            status=('PASS' if test(v) else 'FAIL') if complete else 'UNCHECKABLE',
            reason='same candidate/version and declared units only; internal consistency is not external validity' if complete else 'required explicit fields absent; no reference values imputed')

def delivered_tables(text):
    lines=text.splitlines()
    for i,line in enumerate(lines):
        parts=[x.strip().strip('`*') for x in line.strip('|').split('|')]
        if not all(k in parts for k in HEADER):continue
        for j in range(i+2,len(lines)):
            cells=[x.strip().strip('`*') for x in lines[j].strip('|').split('|')]
            if len(cells)!=len(parts):break
            cid=cells[0]
            if not re.fullmatch(r'(USER_PURCHASED_siVEGF|VEGFA_SD_\d+)',cid):continue
            values={v:int(cells[parts.index(k)]) for k,v in HEADER.items() if re.fullmatch(r'\d+',cells[parts.index(k)])}
            yield cid,values,j+1

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    records=json.loads((BASE/'results_original.json').read_text('utf-8'));output=[]
    with ZipFile(BASE/'anonymous_reviewer_package_original.zip') as z:
        for record in records:
            aid=record['answer_id']
            for q in record['rounds']:
                rn=q['round'];state=q['tool_results'];expr=state.get('query_expression',{}).get('candidate_summary',[])
                supplied=record['case_input'][rn-1]['user_input'].get('candidate_rows',[])
                ids={r['candidate_id'] for r in state.get('inspect_candidates',{}).get('rows',[])} or {r['candidate_id'] for r in supplied} or {'NO_BOUND_CANDIDATE'}
                tool={r['candidate_id']:{k:r[f] for k,f in [('all','seed_site_count_all'),('non','seed_site_count_nontarget'),('genes','matched_genes'),('mapped','baseline_mapped_genes'),('N','normoxia_detected_genes'),('H','hypoxia_detected_genes'),('unmapped','unmapped_genes')]} for r in expr}
                seed=state.get('match_seed',{})
                for cid in ids:
                    for k,f in [('all','seed_site_counts_all'),('non','seed_site_counts_nontarget')]:
                        if cid in seed.get(f,{}):tool.setdefault(cid,{})[k]=seed[f][cid]
                paths=[n for n in z.namelist() if n.startswith('answers/'+aid+'/attachments/round_'+str(rn)+'/') and n.endswith('/seed_matches.tsv')]
                for path in paths:
                    rr=list(csv.DictReader(io.StringIO(z.read(path).decode('utf-8-sig')),delimiter='\t'))
                    for cid in ids:
                        if cid in tool:tool[cid]['target']=sum(int(float(r['seed_site_count'])) for r in rr if r['candidate_id']==cid and r['gene_id']=='7422')
                tables={cid:(v,line) for cid,v,line in delivered_tables(q['answer'])}
                for layer in ('TOOL_RECORD','DELIVERED_MAIN_ANSWER'):
                    for cid in sorted(ids):
                        values=tool.get(cid,{}) if layer=='TOOL_RECORD' else tables.get(cid,({},None))[0]
                        locator=f'results_original.json[answer_id={aid}].rounds[{rn-1}].'+('tool_results' if layer=='TOOL_RECORD' else 'answer')
                        if cid in tables and layer=='DELIVERED_MAIN_ANSWER':locator+=':line'+str(tables[cid][1])
                        for check in relations(values):output.append(dict(answer_id=aid,case_id=record['case_id'],group=record['group'],round=rn,candidate_id=cid,layer=layer,
                            scope=q['common_input_sha256'],source_locator=locator,**check))
    with (a.output/'checks.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(output[0]));w.writeheader();w.writerows(output)
    control=[]
    good=dict(all=3540,non=3539,target=1,genes=2839,mapped=2836,unmapped=3,N=1695,H=1595)
    bad={**good,'genes':2840}
    for name,v in [('valid_with_overlapping_states',good),('broken_gene_identity',bad),('missing_fields',{})]:
        result=list(relations(v));control.append(dict(name=name,kind='SYNTHETIC_TEST_ONLY',checks=result))
    assert all(x['status']=='PASS' for x in control[0]['checks'])
    assert next(x for x in control[1]['checks'] if x['rule']=='GENE_PARTITION')['status']=='FAIL'
    assert all(x['status']=='UNCHECKABLE' for x in control[2]['checks'])
    summary={'n_original_answers':len(records),'n_rounds':sum(len(r['rounds']) for r in records),
        'counts_by_layer':{layer:dict(collections.Counter(x['status'] for x in output if x['layer']==layer)) for layer in ('TOOL_RECORD','DELIVERED_MAIN_ANSWER')},
        'automatic_prose_extraction':'Only explicitly labelled complete tables are parsed. Other prose remains UNCHECKABLE; no conclusion that absent parsing means a false answer.',
        'new_quality_ratings':0,'new_model_calls':0,'controls':control}
    (a.output/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in summary.items() if k!='controls'}))

if __name__=='__main__':main()
