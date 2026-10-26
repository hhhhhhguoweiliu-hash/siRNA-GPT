"""Expert orientation and seen task cards; never create model answers or grades."""
import hashlib
import html
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from dialogue_evaluation import prepare
from dialogue_review import score_payload
from core import save_json

BASE=ROOT/'research/2026-10-27_evaluation_entry'
PACK=ROOT/'research/2026-10-27_evaluation_fixes_v2/package'
MEANING={
 'W1':'已有试剂投入小试前，核对原始序列、条件性链角色及已有计算证据，避免把预测当实测。',
 'W2':'需求只限参考核对时，检查交付是否准确且守住任务范围，避免额外排名代替所需核对。',
 'W2b':'研究者需要已有预测分数时，能否找到同序列、同上下文、同版本的真实记录。',
 'W3':'高分和近匹配警告同时存在时，能否呈现两个候选的证据和限制，而不是只挑一个数。',
 'U1':'用户中途增加取分需求时，检查系统是否保留首轮并正确完成新增要求；两轮合看一题。',
 'R1':'只有订购原文而链角色未明确时，避免擅自分配或删掉末端；在共同补充后继续核查。',
 'R2':'序列变动后，检查是否仍误用旧序列的计算分数，避免证据与实物不一致。',
 'R3':'检查原始序列、参考长度与声明坐标是否一致；仍需区分实际匹配和用户声明。',
 'R4':'缺少所需表达表时，能否保留已完成证据并明确缺项，避免偷偷换用另一份表达数据。',
 'Q1':'解释分数、seed匹配和表达注释各自代表什么；目前只作独立文献功能，尚无三组对等入口。',
 'Q2':'没有实际测量时，能否据实说明不能给第7天敲低百分比；目前不计主要三组比较。'}
CATEGORY={'work':'普通科研任务','change_request':'需求变化','reliability':'缺项与可靠性检查','literature_qa':'文献问答（单列）'}


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    folder=BASE/'expert_topic_review'
    if folder.exists():raise ValueError('Use a new expert package directory; do not overwrite reviewed material')
    folder.mkdir(parents=True)
    suite=json.loads((PACK/'runtime/cases.json').read_text(encoding='utf-8'))
    criteria={c['case_id']:c for c in json.loads((PACK/'review_only/criteria.json').read_text(encoding='utf-8'))}
    plan=json.loads((PACK/'planning/analysis_plan.json').read_text(encoding='utf-8'))
    facts=json.loads((PACK/'review_only/fact_items_DRAFT.json').read_text(encoding='utf-8'))
    shutil.copyfile(ROOT/'docs/reviews/20261027_expert_briefing_ZH.md',folder/'01_PROJECT_BRIEFING_ZH.md')
    brief=folder/'01_PROJECT_BRIEFING_ZH.md'
    brief.write_text(brief.read_text(encoding='utf-8').replace(
        '../../research/2026-10-27_evaluation_fixes_v2/REVIEW_IMPORT.md',
        'reference_for_judgement/REVIEWER_INSTRUCTIONS.md'),encoding='utf-8')
    reference=folder/'reference_for_judgement'
    shutil.copytree(PACK/'review_only',reference)
    # This is the existing unfilled 33-position development form, not a future
    # 27-unit run form. Its answer IDs match the cards below, not new web IDs.
    (reference/'README.md').write_text('仅作审题依据和填写结构介绍；当前33位置全部未运行，禁止填表现分。新网页计划27位置会有自己的编号和表，不能混用。底表并非某份实际回答交付的证据。\n',encoding='utf-8')
    navigation='# 审题版阅读入口：没有新模型成绩\n\n建议顺序：项目说明 → 任务类型与工作安排 → 选一题卡片及判断依据 → 单独的旧真实练习例。当前请审题，不填写模型表现分。\n\n'
    navigation+='1. [项目与证据过程](01_PROJECT_BRIEFING_ZH.md)\n2. [人员、时间及材料范围](02_REVIEW_STAGES_ZH.md)\n3. [旧真实练习例：原答和纠正同读](practice/CASE_CARD.md)\n4. [现有33位置空表](reference_for_judgement/review_form_blank.xlsx)与[填表说明](reference_for_judgement/REVIEWER_INSTRUCTIONS.md)（只介绍结构；不是真实新答复）\n\n'
    navigation+='| 题目 | 科研用途 | 本轮身份 |\n|---|---|---|\n'
    mapping=[]
    for case in suite['cases']:
        cid=case['id'];card=folder/'cards'/cid;card.mkdir(parents=True)
        save_json(card/'original_input.json',{'rounds':case['rounds']})
        save_json(card/'judgement_basis_DRAFT.json',criteria[cid])
        text='# '+cid+'：'+CATEGORY[case['category']]+'（已见开发材料，待独立审核）\n\n'
        text+='为什么有用：'+MEANING[cid]+'\n\n共同母题：'+case['family']+'。同母题变体不增加独立生物学样本数。\n\n'
        for i,turn in enumerate(case['rounds'],1):text+='## 第'+str(i)+'轮完整需求\n\n'+turn['message']+'\n\n'
        text+='[原始序列、来源、假设及每轮条件全文](original_input.json)。原输入已有注释与本次工具取得的证据分开判断。\n\n'
        text+='## 允许资源及判断依据\n\n'+criteria[cid]['full_question_and_judgement_standard_from_uploaded_review']+'\n\n'
        text+='[事实清单草案](../../reference_for_judgement/fact_items_DRAFT.json)、[关键来源定位](../../reference_for_judgement/anchors.json)、[来源原件](../../reference_for_judgement/source_originals/)。这些只用于判断，不给运行模型看，也不替任何答复补证据。\n\n'
        text+='## 实际答复和评分位置\n\n**新三组尚未运行，下面全部是待运行位置，没有回答或分数。**\n\n'
        for item in plan:
            if item['case_id']!=cid:continue
            aid=item['answer_id'];text+='- '+aid+'：待运行；对应空表的同编号四维、交付和严重错误栏；逐事实表保留全部本题项目。\n'
            mapping.append({'answer_id':aid,'case_id':cid,'execution':'NOT_EXECUTED','fact_ids':item['required_fact_ids']})
        if case['category']=='literature_qa':text+='\nQ1/Q2工具资源尚未对等，不能计作主要评价失败，也不能用来凑独立题数。\n'
        text+='\n请审核：这是否是实际科研问题？必要事实是否准确、可查、足够且不过量？哪些有依据的不同结论应允许？哪些严重错误会推翻完成结论？请记录具体修改理由，不填模型表现分。\n'
        (card/'CARD.md').write_text(text,encoding='utf-8')
        navigation+='| ['+cid+'](cards/'+cid+'/CARD.md) | '+MEANING[cid]+' | 已见；'+('只单列文献功能' if case['category']=='literature_qa' else '拟用于开发入口')+' |\n'
    save_json(folder/'score_position_map_NOT_SCORES.json',mapping)
    (folder/'02_REVIEW_STAGES_ZH.md').write_text('''# 人员与分阶段工作

现在可以邀请有siRNA/RNAi（小干扰RNA/RNA干扰）或相关生物信息学经验的人员审题；不必都具有教授头衔。本项目未代用户联系任何人。

现在审题：阅读项目说明和任务类型，核对科研用途、逐题事实和合理答案范围。所附11题均已见，不能改称未见。可先用单独的旧真实练习例理解原答、证据与纠正的区别，不将练习分计入正式结果。

真实运行前：用户安排独立人员审核或准备具体任务、事实标准、允许答案与严重错误定义。具体未见内容由独立人员保管，不用于开发调试；已提供给执行端调试的内容标已见。记录人员、角色、日期、版本及修改；出题与评分者重合须披露。当前没有这些真人记录，空白不由程序或LLM补填。

正式评分：真实完整匿名答案及附件生成后，由两位未参与代码实现或针对性调优的评审独立填写，再处理分歧。任务按普通科研任务、需求变化、可靠性和单列文献问答区分，不混成一个准确率。两人拿同一完整版本；失败和缺项不删除。

时间安排由用户与评审约定。当前材料建议先看约一页说明和一张练习卡，再按选定任务逐题核对；尚无实际测量的评审工时，不能承诺准确的分钟数。

每张题卡先给题干、原始输入和条件，再给允许资源与判断依据，最后给实际答复和评分位置。当前新答复只写待运行；原始HTTP、配置密钥、组别密钥、代码修复讨论和测试合成评分不发正式评审。文风及步骤可能暴露配置，不能保证完全盲法。

当前已见开发包33位置含6个未支持Q1/Q2位置，原件完整保留；新网页主要开发方案事前排除Q1/Q2，9模板×3配置×1次=27位置、33用户轮次，仍不是未见测试。新批次将生成自己的匿名编号和匹配表，禁止混用旧表。
''',encoding='utf-8')
    practice=folder/'practice';practice.mkdir()
    live=ROOT/'research/2026-10-24_nearfull_complete/live'
    for name in ('conversation_export_original.json','actual_model_call_summary.json','ANSWER_CORRECTION_ZH.md','answer_sequence_discrepancy.json'):
        shutil.copyfile(live/name,practice/name)
    conversation=json.loads((live/'conversation_export_original.json').read_text(encoding='utf-8'))
    request=next(m['text'] for m in conversation['messages'] if m['role']=='user')
    delivered=conversation['messages'][-1]['text']
    (practice/'actual_delivered_answer_UNCHANGED.txt').write_text(delivered,encoding='utf-8')
    evidence=practice/'actual_evidence';evidence.mkdir()
    for name in ('input.json','inspect_candidates.json','verify_target.json','score_candidates.json','match_seed.json','query_expression.json','expression_source.json','report.json','report.html','candidates_ranked.tsv','expression_comparison.tsv','seed_expression_details.tsv','events.jsonl'):
        shutil.copyfile(live/'tool_export'/name,evidence/name)
    shutil.copytree(live/'tool_export/verified_import',evidence/'verified_import')
    shutil.copyfile(live/'actual_tool_export_original.zip',practice/'actual_tool_export_original.zip')
    calls=json.loads((live/'actual_model_call_summary.json').read_text(encoding='utf-8'))
    exercise='# 旧真实开发练习例：只理解材料，不纳入正式评分\n\n'
    exercise+='原运行20261024_121627_1e50c9，代码03092ef；是一例实际Agent流程，没有另外两组同题新回答。不能与新W1的两状态题干混配，也不是未见题。\n\n## 当时完整需求\n\n'+request+'\n\n'
    exercise+='[当时实际输入](actual_evidence/input.json)；[用户当时收到的完整答复](actual_delivered_answer_UNCHANGED.txt)；[实际报告](actual_evidence/report.html)。**必须同读[原答错误与纠正](ANSWER_CORRECTION_ZH.md)**：模型把另一链19位核心复述成24位，原答保留；后加纠正不算模型当时说对。\n\n'
    exercise+='## 实际过程与证据导航\n\n'
    exercise+='| 核对项 | 实际原件定位 | 这份证据不能证明什么 |\n|---|---|---|\n'
    exercise+='| 原始两行、TT/N3与条件性链分配 | [input.json](actual_evidence/input.json)、[候选检查](actual_evidence/inspect_candidates.json) | 不是供应商确认或N3实物模拟 |\n'
    exercise+='| 参考核心坐标和公共参考覆盖 | [verify_target.json](actual_evidence/verify_target.json)：rows[0].core_start_1based/core_end_1based、covered_transcripts | 不是本细胞实测异构体覆盖 |\n'
    exercise+='| 预测分数 | [score_candidates.json](actual_evidence/score_candidates.json)：rows[0].oligoformer_scaled_score、evidence_dataset_id | 不是实测敲低率；旧全局legacy指纹不是既购数值的来源 |\n'
    exercise+='| seed位点/基因 | [match_seed.json](actual_evidence/match_seed.json)：seed_site_counts_nontarget、counts、supplemental_both_strand_seed_summaries | 匹配不是实测脱靶，位点不是基因 |\n'
    exercise+='| 表达映射与检出 | [query_expression.json](actual_evidence/query_expression.json)：candidate_summary、expression_comparison；[来源](actual_evidence/expression_source.json) | 未转染基线仅注释，不能证明第7天敲低或安全 |\n'
    exercise+='\n实际6项工具均执行；当时模型请求'+str(calls['total_requests'])+'次，合计'+str(calls['total_tokens'])+'词元，详见[真实调用与用量](actual_model_call_summary.json)。工具执行完整不等于回答无错。完整会话原件另附，不要求评审通读模型提示词或源码；不涉及隐藏思维链。\n\n'
    exercise+='既购数值可继续回查[独立结果](actual_evidence/verified_import/purchased_sivegf_20261024_v1/verified_local_result.json)及[绑定清单](actual_evidence/verified_import/purchased_sivegf_20261024_v1/manifest.json)。[当时完整工具导出原包](actual_tool_export_original.zip)原样保留，不把后来来源说明回填模型原答。\n\n'
    exercise+='没有生成新的完整三组回答，没有练习评分，也不把新软件防错回填旧原答。正式评分包另行从实际运行生成，练习例与本册不随正式匿名回答一起发出，以减少先入判断。\n'
    (practice/'CASE_CARD.md').write_text(exercise,encoding='utf-8')
    (folder/'README.md').write_text(navigation,encoding='utf-8')
    # Compact browser reading page; source files are linked and remain unchanged.
    body='<h1>siRNA-GPT：专家审题材料</h1><p>审题版；无新模型成绩，不填写表现分。先读项目说明，再选题卡。旧真实练习例另列。</p><ol><li><a href="01_PROJECT_BRIEFING_ZH.md">项目与证据过程</a></li><li><a href="02_REVIEW_STAGES_ZH.md">人员与分阶段安排</a></li><li><a href="practice/CASE_CARD.md">旧真实练习例（原错误与纠正同读）</a></li></ol><table><tr><th>题目</th><th>用途</th><th>状态</th></tr>'
    for case in suite['cases']:
        cid=case['id'];body+='<tr><td><a href="cards/'+cid+'/CARD.md">'+cid+'</a></td><td>'+html.escape(MEANING[cid])+'</td><td>'+CATEGORY[case['category']]+'；已见、待审题</td></tr>'
    body+='</table><p>没有真人人员/日期/分数；未运行不是0分。所有正式分数由真人在真实回答齐全后独立填写。</p>'
    (folder/'index.html').write_text('<!doctype html><html lang="zh"><meta charset="utf-8"><title>siRNA-GPT专家审题材料</title><style>body{font:16px/1.7 Arial,"Microsoft YaHei",sans-serif;max-width:1100px;margin:32px auto;padding:0 20px}table{border-collapse:collapse}td,th{border:1px solid #bbc7ce;padding:12px;text-align:left}th{background:#edf3f5}</style>'+body+'</html>',encoding='utf-8')
    cfg=json.loads((ROOT/'config.example.json').read_text(encoding='utf-8'))
    proposed=prepare(cfg)[0]
    save_json(BASE/'proposed_development_plan_NOT_AUTHORIZATION.json',proposed)
    save_json(BASE/'planned_review_workbook_payload.json',{'artifacts':[{'path':str(BASE/'outputs/01a15800-7529-7ee0-b82c-8428c7746a68/planned_review_blank_27.xlsx'),
        'copy_to':str(BASE/'planned_review_blank_27.xlsx'),
        'kind':'PLANNED_DEVELOPMENT_ONLY_NOT_RUN_ALL_HUMAN_FIELDS_BLANK',
        'sheets':score_payload(proposed['schedule'],facts),'preview_dir':str(BASE/'workbook_previews')}]})
    # Validate local navigation; folder links are intentional expandable originals.
    checked=[]
    for p in folder.rglob('*.md'):
        for url in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
            if '://' in url or url.startswith('#'):continue
            target=(p.parent/url.split('#')[0]).resolve()
            if not target.exists():
                # Historical instructions were copied as original documents and
                # may point outside their old folder. Cards/navigation must work.
                if p.parent==reference:continue
                raise ValueError('Broken card link: '+p.as_posix()+' -> '+url)
            checked.append({'from':p.relative_to(folder).as_posix(),'target':url})
    original_copies=[{'copy':str(p.relative_to(folder)).replace('\\','/'),'sha256':sha(p)}
        for p in practice.rglob('*') if p.is_file() and p.name not in ('CASE_CARD.md','actual_delivered_answer_UNCHANGED.txt')]
    save_json(BASE/'expert_pack_checks.json',{'kind':'ORIENTATION_NOT_MODEL_SCORES','task_cards':11,
        'new_real_answers':0,'placeholder_answer_positions':len(mapping),'human_scores_filled':0,
        'practice_original_model_requests':calls['total_requests'],'practice_does_not_count_as_new_run':True,
        'checked_card_links':checked,'practice_original_copy_fingerprints':original_copies,
        'synthetic_scores_or_stub_answers_in_expert_pack':False})
    with zipfile.ZipFile(BASE/'expert_topic_review.zip','w',zipfile.ZIP_DEFLATED) as archive:
        for p in sorted(folder.rglob('*')):
            if p.is_file():archive.write(p,p.relative_to(folder))
    print('PASS: expert orientation, 11 seen task cards / 33 pending answer positions, actual old practice and source links; no new answers or scores.')


if __name__=='__main__':main()
