"""Place fixed RNA bases and exact guide complements on alternating-direction rows."""
import csv, hashlib, json, math, re, shutil
from pathlib import Path

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
COLS=126  # Keeps every 21-nt guide on one row; leaves 81 bases in the last row.
CELL_PT=13

def read_table(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter='\t'))
def write_table(name,rows):
    with (OUT/'tables'/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(rows)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

if __name__=='__main__':
    for name in ['inputs','tables','figures','preview','logs']:(OUT/name).mkdir(exist_ok=True)
    prior=ROOT/'research/2026-10-29_default9_target_sites'
    inputs={'VEGFA_NM003376.gb':prior/'inputs/VEGFA_NM003376.gb',
            'default9_primary_positions.tsv':prior/'tables/default9_primary_positions.tsv',
            'candidates.tsv':ROOT/'data/candidates.tsv'}
    for name,p in inputs.items():shutil.copy2(p,OUT/'inputs'/name)
    gb=inputs['VEGFA_NM003376.gb'].read_text(encoding='utf-8')
    assert re.search(r'^VERSION\s+NM_003376\.6\s*$',gb,re.M)
    rna=re.sub('[^acgtACGT]','',gb.split('\nORIGIN',1)[1].split('//')[0]).upper().replace('T','U')
    assert len(rna)==3609
    candidates=read_table(inputs['default9_primary_positions.tsv']);raw={r['candidate_id']:r for r in read_table(inputs['candidates.tsv'])}
    nrows=math.ceil(len(rna)/COLS);byrow={r:[] for r in range(1,nrows+1)}
    for c in candidates:
        start=int(c['window23_start']);end=start+20
        assert (start-1)//COLS==(end-1)//COLS, 'A guide crosses a row; change row width or explicitly split.'
        row=(start-1)//COLS+1;c['rna_row']=row;c['guide_start']=start;c['guide_end']=end
        guide=c['guide21_RNA_5to3'];sense=rna[start-1:end]
        assert guide==sense.translate(str.maketrans('ACGU','UGCA'))[::-1]
        assert guide==raw[c['candidate_id']]['guide_21nt_RNA_5to3']
        assert guide[:19]==c['guide19_RNA_5to3']
        byrow[row].append(c)
    rows=[];cursor=0.0
    for row in range(1,nrows+1):
        start=(row-1)*COLS+1;end=min(row*COLS,len(rna));ltr=row%2==1
        rows.append({'row':row,'first_coordinate':start,'last_coordinate':end,'direction':'LTR' if ltr else 'RTL',
            'y':-cursor,'left_coordinate':start if ltr else end,'right_coordinate':end if ltr else start,
            'guide_lanes':len(byrow[row])})
        cursor+=3.4+2.0*len(byrow[row])
    rowmeta={r['row']:r for r in rows}
    def x_of(position):
        row=(position-1)//COLS+1;offset=(position-1)%COLS
        return offset+1 if row%2 else COLS-offset
    target_positions={p for c in candidates for p in range(int(c['core_start']),int(c['core_end'])+1)}
    bases=[]
    for position,base in enumerate(rna,1):
        row=(position-1)//COLS+1
        bases.append({'position':position,'base':base,'row':row,'x':x_of(position),'y':rowmeta[row]['y'],
                      'kind':'mRNA target core' if position in target_positions else 'mRNA'})
    guides=[];ends=[];guide_labels=[]
    for row in range(1,nrows+1):
        for lane,c in enumerate(byrow[row],1):
            y=rowmeta[row]['y']-2*lane
            for index,base in enumerate(c['guide21_RNA_5to3'],1):
                p=c['guide_end']-index+1
                assert base==rna[p-1].translate(str.maketrans('ACGU','UGCA'))
                guides.append({'candidate_id':c['candidate_id'],'short_id':c['short_id'],'guide_index_5to3':index,
                    'target_position':p,'mRNA_base':rna[p-1],'base':base,'row':row,'lane':lane,'x':x_of(p),'y':y,
                    'kind':'Guide core (19 nt)' if index<=19 else "Guide 3' duplex terminal (2 nt)"})
            xf=x_of(c['guide_end']);xt=x_of(c['guide_start'])
            ends.extend([{'candidate_id':c['candidate_id'],'x':xf+(1.8 if xf>xt else -1.8),'y':y,'label':"5'"},
                         {'candidate_id':c['candidate_id'],'x':xt+(-1.8 if xf>xt else 1.8),'y':y,'label':"3'"}])
            guide_labels.append({'candidate_id':c['candidate_id'],'row':row,'lane':lane,'x':-5,'y':y,
                'label':c['short_id']+' | '+c['core_start']+'-'+c['core_end'],
                'core_start':int(c['core_start']),'core_end':int(c['core_end']),
                'full_guide_complement_start':c['guide_start'],'full_guide_complement_end':c['guide_end'],
                'guide21_5to3':c['guide21_RNA_5to3']})
    turns=[]
    for meta,nextmeta in zip(rows,rows[1:]):
        right=meta['direction']=='LTR';edge=COLS+1 if right else 0;sign=1 if right else -1
        for k in range(41):
            theta=math.pi*k/40
            turns.append({'turn':meta['row'],'order':k,'x':edge+sign*3*math.sin(theta),
                'y':(meta['y']+nextmeta['y'])/2+(meta['y']-nextmeta['y'])/2*math.cos(theta)})
    last_y=min([r['y'] for r in rows]+[g['y'] for g in guides]);ymin=last_y-8;ymax=11
    xmin=-21;xmax=COLS+13
    settings={'reference':'NM_003376.6','length':len(rna),'columns':COLS,'RNA_rows':nrows,
        'xmin':xmin,'xmax':xmax,'ymin':ymin,'ymax':ymax,'cell_pt':CELL_PT,
        'width_inches':(xmax-xmin)*CELL_PT/72,'height_inches':(ymax-ymin)*CELL_PT/72,
        'base_font_pt':16,'guide_font_pt':16,'title_font_pt':32,'subtitle_font_pt':20,
        'footer_y1':last_y-3.6,'footer_y2':last_y-5.5,'footer_y3':last_y-7.0,
        'terminal_3_x':x_of(len(rna))+2.3,'terminal_3_y':rowmeta[nrows]['y']}
    write_table('mRNA_bases.tsv',bases);write_table('guide_bases.tsv',guides);write_table('rows.tsv',rows)
    write_table('guide_labels.tsv',guide_labels);write_table('guide_ends.tsv',ends);write_table('turn_paths.tsv',turns)
    (OUT/'inputs/NM_003376.6_RNA.fasta').write_text('>NM_003376.6 mRNA reference; T-to-U conversion\n'+rna+'\n',encoding='utf-8')
    (OUT/'settings.json').write_text(json.dumps(settings,indent=2),encoding='utf-8')
    receipt={'status':'PASS','reference':'NM_003376.6','all_mRNA_bases':len(bases),'guide_strands':len(guide_labels),
        'guide_bases':len(guides),'columns':COLS,'rows':nrows,'first_row_direction':'LTR','alternating_directions':True,
        'all9_21nt_exact_reverse_complements':True,'paired_core_19nt_and_full_guide_21nt_distinguished':True,
        'guide_terminal_interpretation':'Gray 3-prime terminal dinucleotides are overhangs relative to the original passenger duplex; here the full 21-nt guide is still exactly complementary to the fixed mRNA reference. Gray does not mean an mRNA mismatch.',
        'alignment':'Guide x coordinates equal their complementary mRNA coordinates; strand-end labels reflect antiparallel orientation.',
        'new_design_prediction_or_RNAseq_analysis':False,'mRNA_RNA_sequence_sha256':hashlib.sha256(rna.encode()).hexdigest(),
        'sources':[{'name':name,'path':str(p),'sha256':digest(p)} for name,p in inputs.items()]}
    (OUT/'logs/coordinate_sequence_audit.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'status':'PASS','RNA_bases':len(bases),'RNA_rows':nrows,'guides':len(guide_labels),'guide_bases':len(guides),'page_inches':[settings['width_inches'],settings['height_inches']]}))
