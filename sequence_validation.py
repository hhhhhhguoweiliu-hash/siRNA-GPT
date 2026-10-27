"""Deterministic final-answer sequence check; no model or scientific computation.

Only sequence strings actually supplied by checked inputs/tools are allowed.
This is a limited output-integrity guard, not a scientific quality score.
"""
import hashlib,html,re

VERSION='sequence_consistency_v2_token_labels'
TOKEN=re.compile(r'(?<![A-Za-z])[ACGUTNX]{10,}(?![A-Za-z])',re.I)
CORE_FIELDS=('guide_core19_5to3','passenger_core19_5to3')
ORIGINAL_FIELDS=('guide_21nt_original','passenger_21nt_original','original_row1','original_row2')

def verified_rows(candidates,state):
    inspected={r['candidate_id']:r for r in state.get('inspect_candidates',{}).get('rows',[])}
    targets={r['candidate_id']:r for r in state.get('verify_target',{}).get('rows',[])}
    output=[]
    for raw in candidates:
        cid=raw.get('candidate_id');checked=inspected.get(cid)
        if not checked:continue
        guide=checked.get('guide_core19_5to3','')
        passenger=raw.get('passenger_paired_core_19nt_5to3') or raw.get('passenger_core19_5to3') or ''
        # inspect_candidates has already checked this complement; do not infer
        # a missing original chain or truncate a 21nt strand here.
        if passenger and passenger.upper().replace('T','U')!=guide.translate(str.maketrans('ACGU','UGCA'))[::-1]:
            passenger=''
        target=targets.get(cid,{})
        output.append({'candidate_id':cid,'guide_core19_5to3':guide,'passenger_core19_5to3':passenger,
            'guide_21nt_original':raw.get('guide_21nt_RNA_5to3',''),
            'passenger_21nt_original':raw.get('passenger_21nt_RNA_5to3',''),
            'original_row1':raw.get('original_row1',''),'original_row2':raw.get('original_row2',''),
            'strand_assignment_basis':raw.get('strand_assignment_basis','Source-labelled roles; no new role inference by this check'),
            'original_modification':raw.get('original_modification','未新增化学修饰确认'),
            'reference_transcript':target.get('reference_transcript',''),
            'core_start_1based':target.get('core_start_1based'),'core_end_1based':target.get('core_end_1based'),
            'mRNA_context_57nt':target.get('mRNA_context_57nt',''),
            'design_window_23nt':raw.get('target_window_23nt','') if target else '',
            'evidence_source':'inspect_candidates; verify_target where present; unchanged original candidate fields',
            'target_match_checked':bool(target)})
    return output

def _expected_fields(line):
    lower=line.lower()
    if re.search(r'原始?\s*(?:行|第)\s*1|原第1行|row\s*1',lower):return ('original_row1',)
    if re.search(r'原始?\s*(?:行|第)\s*2|原第2行|row\s*2',lower):return ('original_row2',)
    guide=bool(re.search(r'(?<![a-z])guide(?![a-z])|引导链',lower))
    passenger=bool(re.search(r'passenger|另一(?:条)?链|伴随链',lower))
    core=bool(re.search(r'核心|core|19\s*(?:nt|位|bp)',lower))
    full=bool(re.search(r'21\s*(?:nt|位|bp)|原始|original|完整',lower))
    if guide!=passenger:
        role='guide' if guide else 'passenger'
        if core and not full:return (role+'_core19_5to3',)
        if full and not core:return (role+'_21nt_original',)
        return (role+'_core19_5to3',role+'_21nt_original')
    if 'context' in lower or '上下文' in line:return ('mRNA_context_57nt',)
    if re.search(r'23\s*(?:nt|位|bp)|设计窗口|design.window',lower):return ('design_window_23nt',)
    if core:return CORE_FIELDS
    return ()

def token_fields(line,match,previous_end):
    """Bind each claim to its own preceding label, never to its observed length.

    A preceding nucleotide token ends its label's scope. This handles A013's
    core and context on one line without making a mutated core acceptable.
    """
    prefix=line[previous_end:match.start()]
    # Prefer the nearest clause; retain a shared role only for the first token.
    clauses=re.split(r'[，,；;|]',prefix)
    local=clauses[-1]
    expected=_expected_fields(local)
    if not expected and previous_end==0:expected=_expected_fields(prefix)
    return expected

def check_sequences(text,rows):
    claims=[];issues=[]
    fields=CORE_FIELDS+ORIGINAL_FIELDS+('mRNA_context_57nt','design_window_23nt')
    for number,line in enumerate(str(text).splitlines(),1):
        tokens=list(TOKEN.finditer(line))
        if not tokens:continue
        named=[r for r in rows if r['candidate_id'] in line]
        scope=named if len(named)==1 else rows
        previous_end=0
        for match in tokens:
            expected=token_fields(line,match,previous_end)
            previous_end=match.end()
            seq=match.group().upper();valid=[]
            for row in scope:
                for field in expected or fields:
                    value=str(row.get(field) or '')
                    # Original N3/TT strings are preserved verbatim in the table;
                    # token matching does not claim to verify chemistry.
                    if seq in [m.group().upper() for m in TOKEN.finditer(value)]:
                        valid.append({'candidate_id':row['candidate_id'],'field':field})
            record={'line':number,'sequence':match.group(),'length':len(seq),'expected_fields':list(expected),
                'matched_verified_fields':valid,'candidate_association':'explicit' if named or len(rows)==1 else 'ambiguous_pool'}
            claims.append(record)
            if not valid:issues.append({**record,'reason':'SEQUENCE_NOT_EQUAL_TO_VERIFIED_FIELD',
                'correct_fields':[{k:r.get(k,'') for k in ('candidate_id',)+(expected or CORE_FIELDS)} for r in scope]})
    if not rows and claims:status='NOT_CHECKED_NO_VERIFIED_SEQUENCE'
    elif issues:status='FAIL'
    elif claims:status='PASS'
    else:status='NO_SEQUENCE_CLAIMS'
    labels={'FAIL':'模型序列检查未通过','PASS':'模型序列检查通过','NO_SEQUENCE_CLAIMS':'模型未复述长序列；请以核验字段为准',
        'NOT_CHECKED_NO_VERIFIED_SEQUENCE':'缺少核验字段，模型序列未通过核验'}
    return {'version':VERSION,'status':status,'label':labels[status],'claim_count':len(claims),'claims':claims,'issues':issues,
        'raw_model_text_sha256':hashlib.sha256(str(text).encode('utf-8')).hexdigest(),
        'scope':'Checks contiguous nucleotide strings of at least 10 bases against checked input/tool fields, with role labels where explicit. Does not validate scientific conclusions, numerical claims, chemistry, or all natural-language strand statements.',
        'is_scientific_accuracy_or_human_score':False}

def answer_evidence(text,candidates,state):
    rows=verified_rows(candidates,state);check=check_sequences(text,rows)
    failed=check['status'] in ('FAIL','NOT_CHECKED_NO_VERIFIED_SEQUENCE')
    display=(check['label']+'。关键序列直接见下方已核验字段；原始模型文字单独保留，不能按错误序列写论文或订购。工具完成情况以执行记录为准。' if failed else str(text))
    return {'model_summary':str(text),'model_summary_raw':str(text),'model_summary_display':display,
        'answer_validation':check,'verified_sequences':rows,
        'answer_sequence_status':'FAILED' if failed else 'NO_CONFLICT_DETECTED','workflow_completion_is_answer_correctness':False}

def evidence_html(check,rows):
    if not check:return ''
    from ui_labels import sequence_label
    esc=lambda x:html.escape(str(x),quote=True)
    color='#b54735' if check['status']=='FAIL' else '#217d6a' if check['status']=='PASS' else '#71838a'
    body='<section class="sequence-evidence" style="border:2px solid '+color+';padding:16px" data-sequence-status="'+esc(check['status'])+'"><h2>'+esc(sequence_label(check))+'</h2><p>Key sequences are read from verified input and tool fields, not regenerated by the model. This check does not establish that every scientific statement is correct.</p>'
    body+='<div class="scroll"><table><tr><th>Candidate</th><th>Guide core 5′→3′</th><th>Other strand core 5′→3′</th></tr>'
    for r in rows:
        body+='<tr>'+''.join('<td>'+esc(r[k] or 'Not supplied or not verified')+'</td>' for k in ['candidate_id','guide_core19_5to3','passenger_core19_5to3'])+'</tr>'
    body+='</table></div>'
    for r in rows:
        for label,key in [('Original row 1','original_row1'),('Original row 2','original_row2'),('Original full-length guide','guide_21nt_original'),('Original full-length other strand','passenger_21nt_original'),('Basis for strand assignment','strand_assignment_basis'),('Original modification note','original_modification')]:
            if r.get(key):body+='<p>'+label+': '+esc(r[key])+'</p>'
    if check['issues']:body+='<p>Sequences conflicting with verified fields: '+esc('；'.join(i['sequence'] for i in check['issues']))+'. The original answer failed and must not be used as a sequence source.</p>'
    return body+'</section>'
