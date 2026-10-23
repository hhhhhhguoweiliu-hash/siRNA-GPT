"""Project notes plus actual local document excerpts, with separate source kinds."""
import hashlib,json

CARDS=[
 {'id':'scope','title':'当前系统能完成什么','tags':['能力','范围','支持','限制','scope','工具','VEGFA'],
  'text':'云端支持人 VEGFA 候选信息与参考转录本核对，以及9条已核对候选的历史 OligoFormer、SeedMatchR 结果整合。其他靶点可查文献，不代表已完成其计算筛选。系统没有微调专业问答模型。',
  'basis':'项目代码、data/provenance.json 和云端配置'},
 {'id':'sequence','title':'siRNA 链方向与输入要求','tags':['guide','passenger','序列','方向','19','21','配对'],
  'text':'当前计算输入要求明确标注5′→3′的19nt guide配对核心及来源；程序不自动把21nt序列截断，也不猜测guide与passenger。应先核对候选信息与靶转录本，再使用现有评分。计算核心不自动转为可订购的化学修饰或完整合成序列。',
  'basis':'core.py 的 inspect_candidates / verify_target 输入契约'},
 {'id':'score','title':'模型分数和实验敲低率','tags':['OligoFormer','分数','score','敲低','效率','排序'],
  'text':'当前报告使用已核对的官方 OligoFormer 输出比较候选。模型分数不是实验敲低百分比。固定核查规则先标记需复核项，再在未标记候选中按模型分数排序；没有新造的综合权重，也不根据这8份未扰动转录组推断敲低效率。',
  'basis':'core.py 的 score_candidates / compile_report；data/provenance.json',
  'original_url':'https://pubmed.ncbi.nlm.nih.gov/39321261/'},
 {'id':'seed','title':'seed 匹配和脱靶证据的边界','tags':['SeedMatchR','seed','脱靶','mer7m8','off-target','风险'],
  'text':'本版本读取的 SeedMatchR 结果范围为 guide、mer7m8、0错配、代表性注释3′UTR。seed匹配提示潜在结合位点，不等于已观察到的基因下调、毒性或实验证实脱靶。表达背景仅作注释，不能据此声称证明了状态特异脱靶效应。',
  'basis':'data/provenance.json 和 core.py 的 match_seed / query_expression'},
 {'id':'expression','title':'常氧与缺氧 RNA-seq 的用途','tags':['RNA-seq','表达','常氧','缺氧','Hypoxia','Normoxia','状态','重复'],
  'text':'项目基线数据为ARPE-19常氧4份、缺氧4份，缺氧为1% O₂、24小时。来源记录注明同一次培养运行、每状态4个培养容器。此处不能自动把容器数说成4次独立培养批次。当前仅将基线表达关联至候选匹配基因，不把它当作siRNA处理后的验证数据。',
  'basis':'data/provenance.json 的 expression.tsv.gz scope；项目已确认的实验条件'},
 {'id':'evidence','title':'如何区分回答中的资料来源','tags':['文献','引用','证据','联网','PubMed','摘要','全文','知识库'],
  'text':'PubMed检索返回题名、PMID及摘要；只有摘要时不能声称已阅读全文。来源链接存在不自动证明所有结论受到支持。本地说明卡是项目实现摘要，尚未由外部专家审核；它们不替代原始论文或实验。网页搜索需要火山账号开通，PubMed是独立可用的检索接口。',
  'basis':'research.py 的实际接口与证据记录方式'}
]
VERSION='project-notes-2026-10-19-v1'

def catalogue():
    return {'version':VERSION,'review_status':'DRAFT_PROJECT_NOTES_NOT_EXPERT_APPROVED',
        'cards':CARDS,'sha256':hashlib.sha256(json.dumps(CARDS,ensure_ascii=False,sort_keys=True).encode()).hexdigest()}

def search(query,limit=3):
    if not isinstance(query,str) or not 1<=len(query.strip())<=2000:raise ValueError('请提供有效的资料检索词')
    q=query.casefold();ranked=[]
    for card in CARDS:
        score=sum(len(t) for t in card['tags'] if t.casefold() in q)
        if score:ranked.append((score,card))
    cards=[x[1] for x in sorted(ranked,key=lambda x:-x[0])[:limit]]
    from literature import get_library
    retrieved=get_library().search(query,limit=min(5,limit+2))
    if retrieved.get('reason'):cards=[]
    sources=[{'url':'/knowledge#'+c['id'],'title':c['title'],
        'kind':'项目设置说明（待外部审核）','source_kind':'project_setting','knowledge_id':c['id']} for c in cards]
    excerpts=[dict(s,text=c['text']) for c,s in zip(cards,sources)]
    sources+=retrieved.get('sources',[])
    excerpts+=retrieved.get('hits',[])
    return {'status':'OK' if excerpts else 'NO_RESULTS','version':VERSION,'review_status':'PROJECT_NOTES_NOT_EXPERT_APPROVED_DOCUMENTS_KEEP_DECLARED_SOURCE_TYPE',
        'cards':[dict(c) for c in cards], 'sources':sources, 'excerpts':excerpts,
        'library_version':retrieved['version'],'query_terms':retrieved['query_terms'],
        'retrieval':retrieved}
