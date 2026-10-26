"""One human-readable expert volume from actual three-arm deliveries.

No semantic grading, answer rewriting, model calls or scientific recalculation.
Complete source answers and raw inputs are also embedded as an attachment ZIP.
"""
import argparse
import collections
import datetime
import hashlib
import html
import io
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from core import save_json
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate,Frame,PageTemplate,Paragraph,Spacer,PageBreak,Table,TableStyle,KeepTogether
from reportlab.platypus.tableofcontents import TableOfContents
from pypdf import PdfReader,PdfWriter

PACK=ROOT/'research/2026-10-27_evaluation_fixes_v2/package'
LABELS={
 'W1':'已有试剂的完整计算核查','W2':'只核对序列与目标参考','W2b':'查询已有分数及其含义',
 'W3':'比较高分与近似匹配警告','U1':'同一问题追加新要求',
 'R1':'订购记录没有明确链角色','R2':'改了序列能否沿用旧分数',
 'R3':'坐标声明是否与序列一致','R4':'缺少本次表达表时如何处理'}
PURPOSES={
 'W1':'研究者已经有试剂，希望在安排小试前，确认计算记录是否确实对应这份试剂，以及哪些实验判断仍没有依据。',
 'W2':'有时研究者只需要确认某条序列能否匹配目标。系统应交付这项核查，不能用额外筛选和排序代替用户要求。',
 'W2b':'研究者需要一个已存在的预测值时，应取得与同一序列、上下文和版本相对应的记录，同时解释它是否代表实际敲低率。',
 'W3':'候选的预测分数较高，同时又有近似匹配提示时，研究者需要知道证据之间的关系，而不是只得到一个“最佳”名单。',
 'U1':'实际交流中，研究者常在拿到初步核查后再追加要求。这一题看完整两轮，判断是否保留原问题并完成新增任务。',
 'R1':'订购文件里的两行序列不一定已经说明哪条是引导链。需要区分已有事实与计算假设，不能把作者的假设说成供应商已确认。',
 'R2':'同一个名称可能对应被修改过的序列。本题检查结果是否仍与真实输入相符，避免把旧分数套给新序列。',
 'R3':'记录可能把设计窗口坐标和配对核心坐标混淆。需要核对原始序列与指定参考，不能看到一个错误就否定全部记录。',
 'R4':'用户指定的数据没有上传时，应完成仍有依据的部分，并说明缺了什么，不能悄悄换用另一份表达数据。'}
TOOLS={'inspect_candidates':'候选与链假设检查','verify_target':'固定参考匹配核对','score_candidates':'读取序列绑定的预测分数',
 'match_seed':'读取种子区匹配证据','query_expression':'关联表达背景','compile_report':'生成文件报告'}


def load(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def esc(text):return html.escape(str(text)).replace('\n','<br/>')


class Book(BaseDocTemplate):
    def afterFlowable(self,flowable):
        mark=getattr(flowable,'book_mark',None)
        if mark:
            label,key,level=mark
            self.canv.bookmarkPage(key);self.canv.addOutlineEntry(label,key,level=level,closed=False)
            if level==0 and key!='contents':self.notify('TOCEntry',(0,label,self.page,key))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();run=args.run;output=args.output
    results=load(run/'results.json');status=load(run/'completion.json');plan=load(run/'protocol.json')['plan']
    assert len(results)==plan['planned_units']==27 and status['pending']==0
    assert all(r['execution_mode']=='provider' for r in results)
    cases={c['id']:c for c in load(run/'cases.json')}
    expected=load(PACK/'review_only/anchors.json');facts=load(PACK/'review_only/fact_items_DRAFT.json')
    purchased=load(ROOT/'data/purchased_sivegf_20261024_v1/verified_local_result.json')
    old_expression=load(PACK/'review_only/purchased_existing_evidence/query_expression.json')
    score_by_id={r['candidate_id']:r for r in expected['scores_original_rows']}
    coord_by_id={r['candidate_id']:r for r in expected['coordinates_independently_found_from_fixed_FASTA']}
    pdfmetrics.registerFont(TTFont('CJK','C:/Windows/Fonts/msyh.ttc',subfontIndex=0))
    pdfmetrics.registerFont(TTFont('CJKB','C:/Windows/Fonts/msyhbd.ttc',subfontIndex=0))
    pdfmetrics.registerFont(TTFont('Arial','C:/Windows/Fonts/arial.ttf'))
    pdfmetrics.registerFontFamily('CJK',normal='CJK',bold='CJKB',italic='CJK',boldItalic='CJKB')
    styles={
      'body':ParagraphStyle('body',fontName='CJK',fontSize=10.4,leading=16,spaceAfter=7,wordWrap='CJK'),
      'small':ParagraphStyle('small',fontName='CJK',fontSize=8.5,leading=12,spaceAfter=5,wordWrap='CJK',textColor=colors.HexColor('#485764')),
      'title':ParagraphStyle('title',fontName='CJKB',fontSize=22,leading=31,spaceAfter=16),
      'h1':ParagraphStyle('h1',fontName='CJKB',fontSize=16,leading=24,spaceBefore=8,spaceAfter=12,keepWithNext=True),
      'h2':ParagraphStyle('h2',fontName='CJKB',fontSize=12,leading=18,spaceBefore=10,spaceAfter=7,keepWithNext=True),
      'quote':ParagraphStyle('quote',fontName='CJK',fontSize=10.2,leading=16,spaceAfter=8,leftIndent=8,rightIndent=4,wordWrap='CJK'),
      'cell':ParagraphStyle('cell',fontName='CJK',fontSize=8.8,leading=13,wordWrap='CJK'),
      'seq':ParagraphStyle('seq',fontName='Arial',fontSize=9.5,leading=14,spaceAfter=6),
    }
    story=[];pagew,pageh=A4;width=pagew-36*mm
    def p(text,style='body'):story.append(Paragraph(esc(text),styles[style]))
    def h(text,level=1,key=None):
        para=Paragraph(esc(text),styles['h1' if level==1 else 'h2'])
        if key:para.book_mark=(text,key,0 if level==1 else 1)
        story.append(para)
    def table(rows,widths=None):
        cells=[[Paragraph(esc(c),styles['cell']) for c in row] for row in rows]
        t=Table(cells,colWidths=widths or [width/len(rows[0])]*len(rows[0]),repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#eaf0f4')),
            ('FONTNAME',(0,0),(-1,0),'CJKB'),('VALIGN',(0,0),(-1,-1),'TOP'),
            ('LINEBELOW',(0,0),(-1,0),0.6,colors.HexColor('#8b9ba5')),
            ('LINEBELOW',(0,1),(-1,-1),0.3,colors.HexColor('#d6dfe5')),
            ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
            ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
        story.append(t);story.append(Spacer(1,8))
    raw_checks=[]
    def raw_answer(text):
        # Only typography is changed. Verbatim source text is embedded separately.
        lines=text.splitlines();i=0
        while i<len(lines):
            line=lines[i]
            next_separator=i+1<len(lines) and bool(re.fullmatch(r'[\s|:-]+',lines[i+1])) and '|' in lines[i+1]
            if ('|' in line and line.strip().startswith('|')) or ('|' in line and next_separator):
                block=[]
                while i<len(lines) and '|' in lines[i] and lines[i].strip():
                    row=[x.strip() for x in lines[i].strip().strip('|').split('|')]
                    if not all(re.fullmatch(r'[\s:-]+',x or ' ') for x in row):block.append(row)
                    i+=1
                if len(block)>1 and all(len(x)==len(block[0]) for x in block):
                    if len(block[0])<=5:table(block)
                    else:
                        headers=block[0]
                        for row in block[1:]:table([['原答字段','原答内容']]+list(map(list,zip(headers,row))),[width*.27,width*.73])
                else:
                    for row in block:p(' | '.join(row),'quote')
                continue
            if re.match(r'^#{1,6}\s+',line):h(line.lstrip('#').strip(),level=2)
            elif line.strip():p(line,'quote')
            else:story.append(Spacer(1,3))
            i+=1
    def input_summary(case):
        raw=case['rounds'][0]['user_input']
        if raw.get('original_order_lines'):
            p('原订购记录的两行如下，末端TT和N3均保留；N3指叠氮基团。')
            for line in raw['original_order_lines']:p(line,'quote')
            if raw.get('calculation_assumptions'):p('本题明确采用计算假设：两行均按5′到3′书写，第2行作为引导链；这不是供应商确认，也不等于已经模拟N3连接后的实物。')
        rows=raw.get('candidate_rows',[])
        if rows:
            grid=[['候选名称','给定的19位引导链核心','原表23位设计窗口坐标','原表注释覆盖数']]
            for r in rows:grid.append([r['candidate_id'],r.get('guide_paired_core_19nt_5to3',r.get('guide_core19_5to3','未提供')),
                (str(r.get('target_start_1based'))+'至'+str(r.get('target_end_1based'))) if r.get('target_start_1based') else '未给设计窗口',r.get('core_matches_n','未给此字段')])
            table(grid,[width*.25,width*.35,width*.22,width*.18])
            p('原表注释已经作为共同输入给三种方式；复述原表不等于本次独立核查。完整原始字段、两条链及附带记录均在本PDF内嵌原件包中。','small')
        if raw.get('constructed_material'):p('本题包含为开发检查而构造的记录，不是新增实验观测。','small')
        if raw.get('user_provided_evidence'):p('本题还给了近匹配记录，包括具体序列窗口、参考转录本及错配位置；这份记录是三种方式都可见的原始输入。')
    def reference(cid):
        if cid in ('W1','R1','R4'):
            grid=[['可核对项目','现有原件中的记录'],['条件性引导链核心',purchased['guide_core19_5to3']],
                ['另一链核心',purchased['passenger_core19_5to3']],['固定参考核心坐标',f"{purchased['core_start_1based']}至{purchased['core_end_1based']}（从1开始计数）"],
                ['固定公共参考覆盖',str(purchased['fixed_transcript_matches'])+'/20'],['预测分数',str(purchased['oligoformer_scaled_score'])+'；不是实际敲低百分比']]
            if cid=='W1':
                summary=old_expression['candidate_summary']
                if isinstance(summary,dict):summary=summary.get(purchased['candidate_id'],summary)
                if isinstance(summary,list):summary=next(x for x in summary if x['candidate_id']==purchased['candidate_id'])
                grid += [['引导链非靶种子匹配',str(purchased['guide_seed_sites_non_target'])+'个位点；'+str(purchased['guide_matched_genes_non_target'])+'个去重基因'],
                    ['可映射到表达数据的基因',str(summary.get('baseline_mapped_genes','见原始表达底表'))],
                    ['常氧达到检出规则的基因',str(summary.get('normoxia_detected_genes','见原始表达底表'))],
                    ['缺氧达到检出规则的基因',str(summary.get('hypoxia_detected_genes','见原始表达底表'))],
                    ['未映射基因',str(summary.get('unmapped_genes','见原始表达底表'))]]
            table(grid,[width*.31,width*.69])
            if cid=='W1':p('本项目的检出规则为：至少2/4个培养皿达到TPM≥1；这不是siRNA处理后效果的判定阈值。','small')
            p('来源一：原订购文件、既购独立结果及其绑定清单。R4明确禁止把既有基线当成本次用户尚未提交的表达表。','small')
        elif cid in ('W2','W2b','U1','R3','W3'):
            ids=['VEGFA_SD_3535','VEGFA_SD_3499'] if cid=='W3' else ['VEGFA_SD_3499']
            if cid=='W2':ids=[x['candidate_id'] for x in cases[cid]['rounds'][0]['user_input']['candidate_rows']]
            grid=[['候选','核对底表的19位核心坐标','固定公共参考覆盖','本题相关的已有分数']]
            for identity in ids:
                c=coord_by_id[identity];score=score_by_id[identity]['oligoformer_scaled_score'] if cid in ('W2b','U1','W3') else '本题不要求读取分数'
                grid.append([identity,str(c['start_1based'])+'至'+str(c['end_1based']),str(c['covered_transcripts'])+'/'+str(c['reference_count']),score])
            table(grid,[width*.24,width*.27,width*.2,width*.29])
            p('来源二：保存的原始分数行和固定参考核对底表。坐标从1开始且两端计入；23位设计窗口不能直接当成19位配对核心坐标。','small')
            if cid=='W3':
                x=expected['supplied_IRGM_record_original'][0] if isinstance(expected['supplied_IRGM_record_original'],list) else expected['supplied_IRGM_record_original']
                p('来源三：原近匹配记录。请特别核对窗口定义 '+str(x.get('query_definition'))+'，而不把另一种19位窗口混为同一查询。')
                table([['近匹配项目','输入附带的原记录'],['查询序列窗口',x.get('guide_window_5to3','')],['匹配参考',str(x.get('reference_transcript'))+'：'+str(x.get('reference_start_1based'))+'至'+str(x.get('reference_end_1based'))],['基因及错配',str(x.get('mapped_gene'))+'；'+str(x.get('actual_mismatches'))+'处错配'],['解释限制','只是序列核查警告，不是实验证实的脱靶，也没有给出唯一最佳候选']],[width*.28,width*.72])
        elif cid=='R2':
            p('本题明确把引导链核心从 UUUCUUGUCUUGCUCUAUC 改为 AUUCUUGUCUUGCUCUAUC，但保留其他原字段。原始旧分数仍只能对应旧的、经过绑定核对的输入；哪些字段矛盾、哪些仍可用，请据原件与回答判断。')
    # Opening pages: explain the study before showing any identifier or score form.
    story.append(Paragraph('siRNA辅助系统<br/>三种方式的真实问答评审材料',styles['title']))
    p('给首次接触本课题的老师','h2')
    p('本课题想做一个帮助研究人员核查siRNA计算证据的助手。研究者可能已经买了试剂，也可能拿到了设计候选；系统需要把序列、目标参考、已有预测和匹配结果对应起来，并说明还不能确定什么。')
    p('这次比较想回答：让语言模型使用科学工具，是否比直接问模型或按固定步骤处理，更能准确、有依据地完成研究者的要求？是否存在差距、差距在哪里，需根据真实问答由独立评审判断。')
    p('本项目当前只支持人VEGFA及已有ARPE-19资料。ARPE-19是人视网膜色素上皮细胞系。本次不评价哪条siRNA在实验上最有效或最安全，也没有新增敲低或脱靶实验。')
    p('请您根据后面的完整问题、三份实际匿名答复和判断依据，独立评价：事实对不对、证据是否支持结论、任务有没有完成、未知和限制有没有说清。允许三份同分，也允许固定流程或普通模型表现更好。')
    p('本册已包含本次真实运行的问答，不是只有编号的空表。每题先解释为什么问，再展示输入与完整需求，随后列出三份原答，最后才是评分位置。所有评分均留空，未由程序或模型代填。')
    table([['本次实际状态','记录'],['计划及实际尝试','9个已见开发情景 × 3种方式 × 1次，共27个位置；全部已尝试'],['用户交流轮次','两题有两轮交流；共33个用户轮次，不能把它们当成33个独立问题'],['所用模型','两个需模型的方式均使用 doubao-seed-2-0-mini-260428；固定流程不调用模型'],['本批实际模型用量',str(sum(r['real_model_requests'] for r in results))+'次请求；'+str(sum(r.get('total_tokens') or 0 for r in results))+'词元；不是题目数或人工分数'],['尚未完成','独立真人评分。以下程序完成、部分完成或停止状态，不直接等于答对或答错']],[width*.29,width*.71])
    p('时间：2026年10月27日。题目已用于开发，不能称独立未见测试；本次结果只能按开发评价解释。','small')
    story.append(PageBreak())
    h('怎样阅读和评价',key='orientation')
    p('三种方式都收到相同的原始问题、序列、条件及预设用户补充。资源的区别如下；并不要求评审猜出匿名答复来自哪一种。')
    p('除了自然语言问题，本批还共同提供了明确步骤范围的结构化条件，下面逐题译成中文列出。因此这次不是对纯自由文字理解能力的测试。两轮题各保留自己的首轮回答，不把另一种方式的回答传给它。')
    table([['辅助方式','如何产生回答'],['普通模型','只根据共同输入回答，不开放科学工具或外网，不提前提供其他方式运行后取得的结果。'],['固定流程','按共同条件选择事先规定的工具路径，由程序整理工具字段；不调用语言模型。'],['Agent（会安排工具步骤的模型助手）','由同款语言模型安排步骤，调用与固定流程相同的科学工具和数据，可能进行多次请求。']],[width*.27,width*.73])
    p('与普通模型比较，能看到工具、数据和规则支持的整体帮助；Agent与固定流程比较，才更接近考察安排步骤、解释与响应追加需求的额外作用。不能把全部差值都归因于Agent规划。')
    p('前五个情景是实际核查或需求追加；后四个是链角色、记录错误和缺资料的处理。它们分开报告，不合成一个“科研准确率”。其中有共同母题，不能当成互不相关的生物学样本。')
    p('常氧和缺氧表达表来自同一培养批次，各4个培养皿，均未经过siRNA处理。表达背景只作注释，不改变排名；不能据此推算实际敲低率。预测分数也不是敲低百分比，种子区匹配不等于已发生脱靶。')
    p('本册隐藏了各答复的组别对应表，但原答措辞和实际步骤可能暴露来源，不能保证完全盲法。判断依据与实际回答分开：某份答复没有交付的证据，不能因为本册提供了核对底表就替它补上。')
    h('这次怎么给分',level=2)
    table([['维度','请核对什么'],['事实准确','序列、数值、坐标、单位和条件是否正确，有没有把不同版本混用。'],['证据支持','相邻结论是否确实由引用材料支持，而不只是出现一个文件名。'],['需求完成','是否交付本题要求的内容；两轮问题要合看，不能只评最后一句。'],['边界处理','能否说清缺项、假设和不能判断的部分，不把推测说成实验事实。']],[width*.23,width*.77])
    p('每维2分＝充分满足本题条件；1分＝部分满足或有明确缺漏；0分＝明确错误或未达到。不能评分时留空并写原因，不用0代替缺失。另判断本题是完成、部分完成还是未交付，并指出是否有会推翻完成结论的严重错误。')
    p('例如，诚实说“没有实际测量，无法给出敲低百分比”，可以是正确的限制说明；但如果本题要求交付一个已存在的计算分数，只说不知道仍没有完成该数值交付。请按具体维度分别判断，不按回答长度、工具数或程序状态打分。')
    story.append(PageBreak())
    h('本册问题目录',key='contents')
    toc=TableOfContents();toc.levelStyles=[ParagraphStyle('toc',fontName='CJK',fontSize=10.5,leading=18,spaceBefore=5,leftIndent=0,firstLineIndent=0)]
    story.append(toc)
    p('本PDF内嵌一个原始材料ZIP，包含完整用户输入、实际答复和取得的证据；可在支持附件的PDF阅读器中查看。正文已经给出评审必需的主要内容，不要求您读源码或模型内部推理。','small')
    p('登记号只用于把您的评分对应到某份原答。甲、乙、丙仅是本题匿名显示顺序，不代表优劣，也不保证不同题的“甲”来自同一种方式。','small')
    ordered=list(LABELS)
    private=[]
    for number,cid in enumerate(ordered,1):
        case=cases[cid];story.append(PageBreak());h(str(number)+' '+LABELS[cid],key='case_'+cid)
        p('问题用途：'+PURPOSES[cid])
        h('本题完整问题',level=2)
        for index,turn in enumerate(case['rounds'],1):
            if len(case['rounds'])>1:p('第'+str(index)+'轮用户要求','h2')
            p(turn['message'],'quote')
        h('原始输入和允许资源',level=2);input_summary(case)
        p('普通模型仅有共同输入，不能使用科学工具或外网。两个工具方式使用相同版本的数据，并遵守下面给三种方式共同展示的范围。调用已有分数前必要的序列与参考绑定核对仍需完成。')
        condition_names={'candidate_check':'候选检查','reference_check':'参考核对','score_check':'已有分数查询','seed_check':'种子匹配证据','expression_check':'表达背景','report_required':'文件报告'}
        for index,turn in enumerate(case['rounds'],1):
            flags=turn['conditions'];required=[name for field,name in condition_names.items() if flags.get(field)]
            notes=('；同份展示两状态' if flags.get('both_expression_states') else '')+('；两条指定比较对象均需展示' if flags.get('compare_all_requested_candidates') else '')+('；禁止回退内置表达表' if not flags.get('allow_builtin_expression',True) else '')
            p('第'+str(index)+'轮共同条件：'+('、'.join(required) if required else '暂不启动科学工具，先处理问题中的事实和假设')+notes+'。','small')
        h('请老师核对的要点',level=2)
        labels=[f['required_fact'] for f in facts[cid]]
        p('；'.join(labels)+'。')
        p('这些要点仍是作者方的判断依据草案，欢迎指出不合理或重复项目。有依据的不同建议可以成立；本题不预设必须选中某条“最佳siRNA”。')
        h('用于判断的原件摘录',level=2);reference(cid)
        selected=sorted([r for r in results if r['case_id']==cid],key=lambda x:x['answer_id'])
        assert len(selected)==3
        for index,r in enumerate(selected):
            display='甲乙丙'[index];identity=r['answer_id'];h('回答'+display+'  登记号'+identity,level=2,key='ans_'+identity)
            private.append({'question_number':number,'question_name':LABELS[cid],'case_id':cid,'display_answer':display,'answer_id':identity,'group':r['group']})
            p('以下是当时实际交付的全文，仅调整排版，不替原答纠错。','small')
            for turn in r['rounds']:
                if len(r['rounds'])>1:h('第'+str(turn['round'])+'轮实际交付',level=2)
                if turn['execution']=='NOT_EXECUTED':p('本轮未执行，没有模型回答。')
                else:raw_answer(turn['answer'])
                raw=turn.get('raw_model_answer')
                if raw and raw!=turn['answer']:
                    h('与交付显示不同的原始模型文字',level=2)
                    p('下面保留当时模型原文。两段内容的差异不能当成模型一开始就说对。','small');raw_answer(raw)
                steps=[TOOLS.get(x,x) for x in turn.get('completed_tools',[])]
                p('本轮实际取得的工具步骤：'+('；'.join(steps) if steps else '没有成功完成的科学工具步骤')+'。','small')
                if turn.get('error'):p('本轮有停止或错误记录，原文已经保留。停止是否符合本题要求，仍由您结合题干判断，不能自动算生物学事实错误。','small')
                raw_checks.append({'case_id':cid,'answer_id':identity,'round':turn['round'],
                    'actual_delivered_text_sha256':hashlib.sha256(turn['answer'].encode('utf-8')).hexdigest(),
                    'actual_delivered_characters':len(turn['answer']),'raw_model_text_separately_preserved':bool(raw and raw!=turn['answer'])})
            p('这份答复的原文、每轮步骤及实际附件，可在本PDF内嵌原件包的 answers/'+identity+' 目录按同一登记号回查。','small')
        grading_start=len(story)
        h('本题评分登记处',level=2)
        table([['实际答复','事实准确\n0至2','证据支持\n0至2','需求完成\n0至2','边界处理\n0至2','是否做完及依据']]+[
            ['回答'+'甲乙丙'[i]+'\n'+r['answer_id'],'','','','',''] for i,r in enumerate(selected)],
            [width*.2,width*.12,width*.12,width*.12,width*.12,width*.32])
        p('不可评分原因或严重错误：________________________________________________')
        p('其他意见：____________________________________________________________')
        grading=story[grading_start:];del story[grading_start:];story.append(KeepTogether(grading))
    story.append(PageBreak());h('读完以后怎样形成比较结果',key='after_review')
    p('请两位评审先独立填写，不互看分数。登记号用于回收分数后对应组别；组别密钥由执行端单独保管，不在本册。若题目作者与评分者重合，应说明角色。')
    p('收到真人评分后，再分别统计科研任务、追加需求和资料错误/缺项处理的完成情况、四维分数、严重错误和实际用量。同一题三份答复进行对应比较；差异为零或负也照实报告，不删掉失败或只挑成功子集。')
    p('目前没有任何独立真人分数，因此本册不宣布哪种方式更好，也不画优势图。它提供的是您能够据实判断的完整材料。')
    p('这套问题和作者方标准在运行前已经保存，但尚没有独立人员事先审定的记录。本次可做对真实开发交付的独立评分，不能因为后来有人评分就改称独立出题或未见测试。若核对依据有客观错误，请明确指出，原记录和纠正需分别保留。')
    h('常用词和来源定位',level=2)
    table([['词语','本册中的意思'],['引导链（guide）','计算时假设负责识别目标的那一条链；在既购试剂中仍须区分计算假设与供应商确认。'],['19位核心与23位窗口','本项目计算使用的配对核心，和siDirect原表的设计窗口是两个坐标范围，不能混用。nt表示核苷酸数。'],['种子区（seed）','引导链中用于短序列匹配的区域；本项目按保存的7位g2至g8匹配定义核查，不能把匹配当成实验脱靶。'],['TPM','每百万转录本的标准化表达量；本册是未转染基线背景，不是处理后的敲低量。'],['OligoFormer','已发表的siRNA效力预测模型。本次读取此前真实计算、经序列及参考一致性核对的结果。'],['来源一','原订购DOCX中的si-VEGF两行；既购独立版本的原始结果和绑定清单；既有表达核对底表。'],['来源二','固定VEGFA参考序列、九条候选原表、原始分数行和坐标核对底表。'],['来源三','题目附带的IRGM近匹配记录，含实际查询窗口、参考子序列和错配位置。']],[width*.28,width*.72])
    p('原件包中 reference_for_judgement 是评审核对依据；answers 下才是各答复实际交付。前者不是给后者事后补答案。模型原始请求/响应、实际用量和组别密钥另由执行端保留，可用于方法复核，不要求评审通读。','small')
    p('评审人：________________  日期：________________  所用材料版本：本册2026年10月27日版')
    output.parent.mkdir(parents=True,exist_ok=True)
    rawpdf=output.parent/'_layout_without_embedded_sources.pdf'
    def footer(canvas,doc):
        canvas.saveState();canvas.setFont('CJK',8);canvas.setFillColor(colors.HexColor('#5c6d78'))
        canvas.drawString(18*mm,12*mm,'siRNA-GPT 三种方式真实问答  尚无人工评分')
        canvas.drawRightString(pagew-18*mm,12*mm,'第'+str(doc.page)+'页');canvas.restoreState()
    doc=Book(str(rawpdf),pagesize=A4,rightMargin=18*mm,leftMargin=18*mm,topMargin=17*mm,bottomMargin=19*mm,
        title='siRNA辅助系统三种方式真实问答评审材料',author='siRNA-GPT project')
    doc.addPageTemplates([PageTemplate(id='normal',frames=[Frame(18*mm,19*mm,width,pageh-36*mm,id='main',leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)],onPage=footer)])
    doc.multiBuild(story)
    writer=PdfWriter();writer.clone_document_from_reader(PdfReader(rawpdf))
    reviewer_zip=run/'reviewer_package.zip'
    writer.add_attachment('原始输入与实际回答证据.zip',reviewer_zip.read_bytes())
    writer.add_metadata({'/Title':'siRNA辅助系统三种方式真实问答评审材料','/Author':'siRNA-GPT project','/Subject':'真实27个任务位置的匿名原答与人工评价依据，未填写评分'})
    with output.open('wb') as handle:writer.write(handle)
    save_json(output.parent/'private_display_key_DO_NOT_SEND_REVIEWERS.json',private)
    save_json(output.parent/'document_integrity.json',{'kind':'REAL_DELIVERIES_PRESENTATION_NOT_AUTOMATIC_HUMAN_GRADING',
        'run_id':plan.get('id',run.name),'source_answer_units':len(results),'source_rounds':len(raw_checks),
        'source_records':raw_checks,'source_review_zip_sha256':sha(reviewer_zip),'pdf_sha256':sha(output),
        'pdf_pages':len(PdfReader(output).pages),'embedded_source_zip':True,'human_scores_filled':0,
        'raw_answers_rewritten':False,'group_key_in_pdf':False,'all_planned_units_present':True})
    print(json.dumps({'pdf':str(output),'pages':len(PdfReader(output).pages),'actual_answer_units':len(results),'human_scores_filled':0},ensure_ascii=False))


if __name__=='__main__':main()
