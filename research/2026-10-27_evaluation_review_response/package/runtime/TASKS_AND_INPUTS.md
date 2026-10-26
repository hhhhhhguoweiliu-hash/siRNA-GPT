# 共同用户输入全文（不是标准答案）

所有模板已见；Q1/Q2对等入口未接通。

## W1

类别：work；关联母题：purchased_complete

### 第1轮

我已有这份si-vegf试剂。请保留订购记录的两行与TT、N3原文。本次仅作计算核查：假设两行均按5′→3′写，第2行为guide，其19nt核心是UUUCUUGUCUUGCUCUAUC；另一行配对核心是GAUAGAGCAAGACAAGAAA。这是本次计算假设，不是供应商已确认。请核对固定人VEGFA参考，读取与该序列和参考绑定的OligoFormer结果；对guide整理seed位点、去重非靶基因、表达可映射基因、常氧和缺氧检出基因，生成可回查报告。说明这些证据能支持什么，实验前仍需确认什么。不要换成九条设计候选，不要把它称为最有效或最安全的siRNA。

原始资料全文与共同条件：

```json
{
  "user_input": {
    "original_order_lines": [
      "GAUAGAGCAAGACAAGAAATT-N3（叠氮基团，用于点击化学）",
      "UUUCUUGUCUUGCUCUAUCTT"
    ],
    "calculation_assumptions": {
      "rows_written_5to3": true,
      "guide_row": 2,
      "guide_core19_5to3": "UUUCUUGUCUUGCUCUAUC",
      "passenger_core19_5to3": "GAUAGAGCAAGACAAGAAA"
    }
  },
  "conditions": {
    "candidate_check": true,
    "reference_check": true,
    "score_check": true,
    "seed_check": true,
    "expression_check": true,
    "report_required": true,
    "both_expression_states": true,
    "compare_all_requested_candidates": false,
    "chain_assumption_provided": true,
    "allow_builtin_expression": true
  }
}
```

允许资源：以resources.json为准；工具配置读取同一绑定数据，普通模型不开放科学工具/外网。评审底表不得用作运行附件。

## W2

类别：work；关联母题：reference_score

### 第1轮

请对附件九条原始VEGFA候选逐条核对guide的19nt配对核心，在固定参考NM_003376.6上报告实际匹配坐标，并列出在附件20条固定公共参考中的覆盖。请区分原表23nt设计窗口和本次19nt核心坐标。只做这些核对，不读取效力分数，不做seed、表达关联或优先排序。

原始资料全文与共同条件：

```json
{
  "user_input": {
    "candidate_rows": [
      {
        "source_run": "VEGFA_NM003376_6",
        "source_tool": "siDirect_2.0",
        "target_start_1based": "1157",
        "target_end_1based": "1179",
        "target_window_23nt": "GTGAAGTTCATGGATGTCTATCA",
        "guide_21nt_RNA_5to3": "AUAGACAUCCAUGAACUUCAC",
        "passenger_21nt_RNA_5to3": "GAAGUUCAUGGAUGUCUAUCA",
        "guide_paired_core_19nt_5to3": "AUAGACAUCCAUGAACUUC",
        "passenger_paired_core_19nt_5to3": "GAAGUUCAUGGAUGUCUAU",
        "guide_overhang_3prime": "AC",
        "passenger_overhang_3prime": "CA",
        "functional_rule": "U",
        "seed_tm_guide_C": "20.3",
        "seed_tm_passenger_C": "19.2",
        "vendor_min_mismatches_guide_19nt_g2g20": "2",
        "vendor_min_mismatches_passenger_19nt_g2g20": "3",
        "candidate_id": "VEGFA_SD_1157",
        "target_gene": "VEGFA",
        "design_transcript": "NM_003376.6",
        "core_matches_n": "20",
        "core_matches_transcripts": "NM_001171623.2;NM_001171626.2;NM_001171628.2;NM_001317010.2;NM_001025369.3;NM_001171627.2;NM_001171625.2;NM_001204384.2;NM_001287044.2;NM_001025367.3;NM_001171630.2;NM_001171622.2;NM_001171624.2;NM_001025370.3;NM_001204385.2;NM_001025368.3;NM_001033756.3;NM_003376.6;NM_001025366.3;NM_001171629.2",
        "all_20_transcripts_core_match": "True",
        "guide_gc_pct": "36.8421052631579",
        "working_pool_pass": "True",
        "exclusion_reason": "NA",
        "synthesis_status": "NOT_ORDER_READY_MODIFICATIONS_UNFROZEN",
        "oligo_input_derivation": "19_BP_PAIRED_CORE_FROM_VERIFIED_AUTHOR_21NT_DUPLEX_NOT_ARBITRARY_TRUNCATION"
      },
      {
        "source_run": "VEGFA_NM003376_6",
        "source_tool": "siDirect_2.0",
        "target_start_1based": "2739",
        "target_end_1based": "2761",
        "target_window_23nt": "ACCATTGAAACCACTAGTTCTGT",
        "guide_21nt_RNA_5to3": "AGAACUAGUGGUUUCAAUGGU",
        "passenger_21nt_RNA_5to3": "CAUUGAAACCACUAGUUCUGU",
        "guide_paired_core_19nt_5to3": "AGAACUAGUGGUUUCAAUG",
        "passenger_paired_core_19nt_5to3": "CAUUGAAACCACUAGUUCU",
        "guide_overhang_3prime": "GU",
        "passenger_overhang_3prime": "GU",
        "functional_rule": "U",
        "seed_tm_guide_C": "18.9",
        "seed_tm_passenger_C": "7.4",
        "vendor_min_mismatches_guide_19nt_g2g20": "3",
        "vendor_min_mismatches_passenger_19nt_g2g20": "2",
        "candidate_id": "VEGFA_SD_2739",
        "target_gene": "VEGFA",
        "design_transcript": "NM_003376.6",
        "core_matches_n": "20",
        "core_matches_transcripts": "NM_001171623.2;NM_001171626.2;NM_001171628.2;NM_001317010.2;NM_001025369.3;NM_001171627.2;NM_001171625.2;NM_001204384.2;NM_001287044.2;NM_001025367.3;NM_001171630.2;NM_001171622.2;NM_001171624.2;NM_001025370.3;NM_001204385.2;NM_001025368.3;NM_001033756.3;NM_003376.6;NM_001025366.3;NM_001171629.2",
        "all_20_transcripts_core_match": "True",
        "guide_gc_pct": "36.8421052631579",
        "working_pool_pass": "True",
        "exclusion_reason": "NA",
        "synthesis_status": "NOT_ORDER_READY_MODIFICATIONS_UNFROZEN",
        "oligo_input_derivation": "19_BP_PAIRED_CORE_FROM_VERIFIED_AUTHOR_21NT_DUPLEX_NOT_ARBITRARY_TRUNCATION"
      },
      {
        "source_run": "VEGFA_NM003376_6",
        "source_tool": "siDirect_2.0",
        "target_start_1based": "3119",
        "target_end_1based": "3141",
        "target_window_23nt": "TAGCTTATCTTGAACAGATATTT",
        "guide_21nt_RNA_5to3": "AUAUCUGUUCAAGAUAAGCUA",
        "passenger_21nt_RNA_5to3": "GCUUAUCUUGAACAGAUAUUU",
        "guide_paired_core_19nt_5to3": "AUAUCUGUUCAAGAUAAGC",
        "passenger_paired_core_19nt_5to3": "GCUUAUCUUGAACAGAUAU",
        "guide_overhang_3prime": "UA",
        "passenger_overhang_3prime": "UU",
        "functional_rule": "U",
        "seed_tm_guide_C": "20.3",
        "seed_tm_passenger_C": "11.6",
        "vendor_min_mismatches_guide_19nt_g2g20": "2",
        "vendor_min_mismatches_passenger_19nt_g2g20": "2",
        "candidate_id": "VEGFA_SD_3119",
        "target_gene": "VEGFA",
        "design_transcript": "NM_003376.6",
        "core_matches_n": "20",
        "core_matches_transcripts": "NM_001171623.2;NM_001171626.2;NM_001171628.2;NM_001317010.2;NM_001025369.3;NM_001171627.2;NM_001171625.2;NM_001204384.2;NM_001287044.2;NM_001025367.3;NM_001171630.2;NM_001171622.2;NM_001171624.2;NM_001025370.3;NM_001204385.2;NM_001025368.3;NM_001033756.3;NM_003376.6;NM_001025366.3;NM_001171629.2",
        "all_20_transcripts_core_match": "True",
        "guide_gc_pct": "31.57894736842105",
        "working_pool_pass": "True",
        "exclusion_reason": "NA",
        "synthesis_status": "NOT_ORDER_READY_MODIFICATIONS_UNFROZEN",
        "oligo_input_derivation": "19_BP_PAIRED_CORE_FROM_VERIFIED_AUTHOR_21NT_DUPLEX_NOT_ARBITRARY_TRUNCATION"
      },
      {
        "source_run": "VEGFA_NM003376_6",
        "source_tool": "siDirect_2.0",
        "target_start_1based": "3193",
        "target_end_1based": "3215",
        "target_window_23nt": "CACATTCCTTTGAAATAAGGTTT",
        "guide_21nt_RNA_5to3": "ACCUUAUUUCAAAGGAAUGUG",
        "passenger_21nt_RNA_5to3": "CAUUCCUUUGAAAUAAGGUUU",
        "guide_paired_core_19nt_5to3": "ACCUUAUUUCAAAGGAAUG",
        "passenger_paired_core_19nt_5to3": "CAUUCCUUUGAAAUAAGGU",
        "guide_overhang_3prime": "UG",
        "passenger_overhang_3prime": "UU",
        "functional_rule": "U",
        "seed_tm_guide_C": "10.9",
        "seed_tm_passenger_C": "18.7",
        "vendor_min_mismatches_guide_19nt_g2g20": "2",
        "vendor_min_mismatches_passenger_19nt_g2g20": "2",
        "candidate_id": "VEGFA_SD_3193",
        "target_gene": "VEGFA",
        "design_transcript": "NM_003376.6",
        "core_matches_n": "20",
        "core_matches_transcripts": "NM_001171623.2;NM_001171626.2;NM_001171628.2;NM_001317010.2;NM_001025369.3;NM_001171627.2;NM_001171625.2;NM_001204384.2;NM_001287044.2;NM_001025367.3;NM_001171630.2;NM_001171622.2;NM_001171624.2;NM_001025370.3;NM_001204385.2;NM_001025368.3;NM_001033756.3;NM_003376.6;NM_001025366.3;NM_001171629.2",
        "all_20_transcripts_core_match": "True",
        "guide_gc_pct": "31.57894736842105",
        "working_pool_pass": "True",
        "exclusion_reason": "NA",
        "synthesis_status": "NOT_ORDER_READY_MODIFICATIONS_UNFROZEN",
        "oligo_input_derivation": "19_BP_PAIRED_CORE_FROM_VERIFIED_AUTHOR_21NT_DUPLEX_NOT_ARBITRARY_TRUNCATION"
      },
      {
        "source_run": "VEGFA_NM003376_6",
        "source_tool": "siDirect_2.0",
        "target_start_1based": "3429",
        "target_end_1based": "3451",
        "target_window_23nt": "TGCTACTGTTTATCCGTAATAAT",
        "guide_21nt_RNA_5to3": "UAUUACGGAUAAACAGUAGCA",
        "passenger_21nt_RNA_5to3": "CUACUGUUUAUCCGUAAUAAU",
        "guide_paired_core_19nt_5to3": "UAUUACGGAUAAACAGUAG",
        "passenger_paired_core_19nt_5to3": "CUACUGUUUAUCCGUAAUA",
        "guide_overhang_3prime": "CA",
        "passenger_overhang_3prime": "AU",
        "functional_rule": "U",
        "seed_tm_guide_C": "20.6",
        "seed_tm_passenger_C": "19.0",
        "vendor_min_mismatches_guide_19nt_g2g20": "3",
        "vendor_min_mismatches_passenger_19nt_g2g20": "3",
        "candidate_id": "VEGFA_SD_3429",
        "target_gene": "VEGFA",
        "design_transcript": "NM_003376.6",
        "core_matches_n": "20",
        "core_matches_transcripts": "NM_001171623.2;NM_001171626.2;NM_001171628.2;NM_001317010.2;NM_001025369.3;NM_001171627.2;NM_001171625.2;NM_001204384.2;NM_001287044.2;NM_001025367.3;NM_001171630.2;NM_001171622.2;NM_001171624.2;NM_001025370.3;NM_001204385.2;NM_001025368.3;NM_001033756.3;NM_003376.6;NM_001025366.3;NM_001171629.2",
        "all_20_transcripts_core_match": "True",
        "guide_gc_pct": "31.57894736842105",
        "working_pool_pass": "True",
        "exclusion_reason": "NA",
        "synthesis_status": "NOT_ORDER_READY_MODIFICATIONS_UNFROZEN",
        "oligo_input_derivation": "19_BP_PAIRED_CORE_FROM_VERIFIED_AUTHOR_21NT_DUPLEX_NOT_ARBITRARY_TRUNCATION"
      },
      {
        "source_run": "VEGFA_NM003376_6",
        "source_tool": "siDirect_2.0",
        "target_start_1based": "3499",
        "target_end_1based": "3521",
        "target_window_23nt": "TTCGAGATATTCCGTAGTACATA",
        "guide_21nt_RNA_5to3": "UGUACUACGGAAUAUCUCGAA",
        "passenger_21nt_RNA_5to3": "CGAGAUAUUCCGUAGUACAUA",
        "guide_paired_core_19nt_5to3": "UGUACUACGGAAUAUCUCG",
        "passenger_paired_core_19nt_5to3": "CGAGAUAUUCCGUAGUACA",
        "guide_overhang_3prime": "AA",
        "passenger_overhang_3prime": "UA",
        "functional_rule": "U",
        "seed_tm_guide_C": "21.3",
        "seed_tm_passenger_C": "15.9",
        "vendor_min_mismatches_guide_19nt_g2g20": "3",
        "vendor_min_mismatches_passenger_19nt_g2g20": "3",
        "candidate_id": "VEGFA_SD_3499",
        "target_gene": "VEGFA",
        "design_transcript": "NM_003376.6",
        "core_matches_n": "20",
        "core_matches_transcripts": "NM_001171623.2;NM_001171626.2;NM_001171628.2;NM_001317010.2;NM_001025369.3;NM_001171627.2;NM_001171625.2;NM_001204384.2;NM_001287044.2;NM_001025367.3;NM_001171630.2;NM_001171622.2;NM_001171624.2;NM_001025370.3;NM_001204385.2;NM_001025368.3;NM_001033756.3;NM_003376.6;NM_001025366.3;NM_001171629.2",
        "all_20_transcripts_core_match": "True",
        "guide_gc_pct": "42.10526315789474",
        "working_pool_pass": "True",
        "exclusion_reason": "NA",
        "synthesis_status": "NOT_ORDER_READY_MODIFICATIONS_UNFROZEN",
        "oligo_input_derivation": "19_BP_PAIRED_CORE_FROM_VERIFIED_AUTHOR_21NT_DUPLEX_NOT_ARBITRARY_TRUNCATION"
      },
      {
        "source_run": "VEGFA_NM003376_6",
        "source_tool": "siDirect_2.0",
        "target_start_1based": "3500",
        "target_end_1based": "3522",
        "target_window_23nt": "TCGAGATATTCCGTAGTACATAT",
        "guide_21nt_RNA_5to3": "AUGUACUACGGAAUAUCUCGA",
        "passenger_21nt_RNA_5to3": "GAGAUAUUCCGUAGUACAUAU",
        "guide_paired_core_19nt_5to3": "AUGUACUACGGAAUAUCUC",
        "passenger_paired_core_19nt_5to3": "GAGAUAUUCCGUAGUACAU",
        "guide_overhang_3prime": "GA",
        "passenger_overhang_3prime": "AU",
        "functional_rule": "U",
        "seed_tm_guide_C": "20.2",
        "seed_tm_passenger_C": "6.6",
        "vendor_min_mismatches_guide_19nt_g2g20": "3",
        "vendor_min_mismatches_passenger_19nt_g2g20": "3",
        "candidate_id": "VEGFA_SD_3500",
        "target_gene": "VEGFA",
        "design_transcript": "NM_003376.6",
        "core_matches_n": "20",
        "core_matches_transcripts": "NM_001171623.2;NM_001171626.2;NM_001171628.2;NM_001317010.2;NM_001025369.3;NM_001171627.2;NM_001171625.2;NM_001204384.2;NM_001287044.2;NM_001025367.3;NM_001171630.2;NM_001171622.2;NM_001171624.2;NM_001025370.3;NM_001204385.2;NM_001025368.3;NM_001033756.3;NM_003376.6;NM_001025366.3;NM_001171629.2",
        "all_20_transcripts_core_match": "True",
        "guide_gc_pct": "36.8421052631579",
        "working_pool_pass": "True",
        "exclusion_reason": "NA",
        "synthesis_status": "NOT_ORDER_READY_MODIFICATIONS_UNFROZEN",
        "oligo_input_derivation": "19_BP_PAIRED_CORE_FROM_VERIFIED_AUTHOR_21NT_DUPLEX_NOT_ARBITRARY_TRUNCATION"
      },
      {
        "source_run": "VEGFA_NM003376_6",
        "source_tool": "siDirect_2.0",
        "target_start_1based": "3502",
        "target_end_1based": "3524",
        "target_window_23nt": "GAGATATTCCGTAGTACATATTT",
        "guide_21nt_RNA_5to3": "AUAUGUACUACGGAAUAUCUC",
        "passenger_21nt_RNA_5to3": "GAUAUUCCGUAGUACAUAUUU",
        "guide_paired_core_19nt_5to3": "AUAUGUACUACGGAAUAUC",
        "passenger_paired_core_19nt_5to3": "GAUAUUCCGUAGUACAUAU",
        "guide_overhang_3prime": "UC",
        "passenger_overhang_3prime": "UU",
        "functional_rule": "U",
        "seed_tm_guide_C": "15.8",
        "seed_tm_passenger_C": "15.4",
        "vendor_min_mismatches_guide_19nt_g2g20": "3",
        "vendor_min_mismatches_passenger_19nt_g2g20": "2",
        "candidate_id": "VEGFA_SD_3502",
        "target_gene": "VEGFA",
        "design_transcript": "NM_003376.6",
        "core_matches_n": "20",
        "core_matches_transcripts": "NM_001171623.2;NM_001171626.2;NM_001171628.2;NM_001317010.2;NM_001025369.3;NM_001171627.2;NM_001171625.2;NM_001204384.2;NM_001287044.2;NM_001025367.3;NM_001171630.2;NM_001171622.2;NM_001171624.2;NM_001025370.3;NM_001204385.2;NM_001025368.3;NM_001033756.3;NM_003376.6;NM_001025366.3;NM_001171629.2",
        "all_20_transcripts_core_match": "True",
        "guide_gc_pct": "31.57894736842105",
        "working_pool_pass": "True",
        "exclusion_reason": "NA",
        "synthesis_status": "NOT_ORDER_READY_MODIFICATIONS_UNFROZEN",
        "oligo_input_derivation": "19_BP_PAIRED_CORE_FROM_VERIFIED_AUTHOR_21NT_DUPLEX_NOT_ARBITRARY_TRUNCATION"
      },
      {
        "source_run": "VEGFA_NM003376_6",
        "source_tool": "siDirect_2.0",
        "target_start_1based": "3535",
        "target_end_1based": "3557",
        "target_window_23nt": "AACGACAAAGAAATACAGATATA",
        "guide_21nt_RNA_5to3": "UAUCUGUAUUUCUUUGUCGUU",
        "passenger_21nt_RNA_5to3": "CGACAAAGAAAUACAGAUAUA",
        "guide_paired_core_19nt_5to3": "UAUCUGUAUUUCUUUGUCG",
        "passenger_paired_core_19nt_5to3": "CGACAAAGAAAUACAGAUA",
        "guide_overhang_3prime": "UU",
        "passenger_overhang_3prime": "UA",
        "functional_rule": "U",
        "seed_tm_guide_C": "20.3",
        "seed_tm_passenger_C": "19.2",
        "vendor_min_mismatches_guide_19nt_g2g20": "2",
        "vendor_min_mismatches_passenger_19nt_g2g20": "2",
        "candidate_id": "VEGFA_SD_3535",
        "target_gene": "VEGFA",
        "design_transcript": "NM_003376.6",
        "core_matches_n": "20",
        "core_matches_transcripts": "NM_001171623.2;NM_001171626.2;NM_001171628.2;NM_001317010.2;NM_001025369.3;NM_001171627.2;NM_001171625.2;NM_001204384.2;NM_001287044.2;NM_001025367.3;NM_001171630.2;NM_001171622.2;NM_001171624.2;NM_001025370.3;NM_001204385.2;NM_001025368.3;NM_001033756.3;NM_003376.6;NM_001025366.3;NM_001171629.2",
        "all_20_transcripts_core_match": "True",
        "guide_gc_pct": "31.57894736842105",
        "working_pool_pass": "True",
        "exclusion_reason": "NA",
        "synthesis_status": "NOT_ORDER_READY_MODIFICATIONS_UNFROZEN",
        "oligo_input_derivation": "19_BP_PAIRED_CORE_FROM_VERIFIED_AUTHOR_21NT_DUPLEX_NOT_ARBITRARY_TRUNCATION"
      }
    ]
  },
  "conditions": {
    "candidate_check": false,
    "reference_check": true,
    "score_check": false,
    "seed_check": false,
    "expression_check": false,
    "report_required": false,
    "both_expression_states": false,
    "compare_all_requested_candidates": false,
    "chain_assumption_provided": false,
    "allow_builtin_expression": true
  }
}
```

允许资源：以resources.json为准；工具配置读取同一绑定数据，普通模型不开放科学工具/外网。评审底表不得用作运行附件。

## W2b

类别：work；关联母题：reference_score

### 第1轮

请核查VEGFA_SD_3499对应的OligoFormer scaled预测分数，给出保留原始精度的数值、来源和与输入序列的对应关系，并说明是否能换算成实际敲低百分比。不做seed、表达或候选排名。

原始资料全文与共同条件：

```json
{
  "user_input": {
    "candidate_rows": [
      {
        "source_run": "VEGFA_NM003376_6",
        "source_tool": "siDirect_2.0",
        "target_start_1based": "3499",
        "target_end_1based": "3521",
        "target_window_23nt": "TTCGAGATATTCCGTAGTACATA",
        "guide_21nt_RNA_5to3": "UGUACUACGGAAUAUCUCGAA",
        "passenger_21nt_RNA_5to3": "CGAGAUAUUCCGUAGUACAUA",
        "guide_paired_core_19nt_5to3": "UGUACUACGGAAUAUCUCG",
        "passenger_paired_core_19nt_5to3": "CGAGAUAUUCCGUAGUACA",
        "guide_overhang_3prime": "AA",
        "passenger_overhang_3prime": "UA",
        "functional_rule": "U",
        "seed_tm_guide_C": "21.3",
        "seed_tm_passenger_C": "15.9",
        "vendor_min_mismatches_guide_19nt_g2g20": "3",
        "vendor_min_mismatches_passenger_19nt_g2g20": "3",
        "candidate_id": "VEGFA_SD_3499",
        "target_gene": "VEGFA",
        "design_transcript": "NM_003376.6",
        "core_matches_n": "20",
        "core_matches_transcripts": "NM_001171623.2;NM_001171626.2;NM_001171628.2;NM_001317010.2;NM_001025369.3;NM_001171627.2;NM_001171625.2;NM_001204384.2;NM_001287044.2;NM_001025367.3;NM_001171630.2;NM_001171622.2;NM_001171624.2;NM_001025370.3;NM_001204385.2;NM_001025368.3;NM_001033756.3;NM_003376.6;NM_001025366.3;NM_001171629.2",
        "all_20_transcripts_core_match": "True",
        "guide_gc_pct": "42.10526315789474",
        "working_pool_pass": "True",
        "exclusion_reason": "NA",
        "synthesis_status": "NOT_ORDER_READY_MODIFICATIONS_UNFROZEN",
        "oligo_input_derivation": "19_BP_PAIRED_CORE_FROM_VERIFIED_AUTHOR_21NT_DUPLEX_NOT_ARBITRARY_TRUNCATION"
      }
    ]
  },
  "conditions": {
    "candidate_check": false,
    "reference_check": false,
    "score_check": true,
    "seed_check": false,
    "expression_check": false,
    "report_required": false,
    "both_expression_states": false,
    "compare_all_requested_candidates": false,
    "chain_assumption_provided": false,
    "allow_builtin_expression": true
  }
}
```

允许资源：以resources.json为准；工具配置读取同一绑定数据，普通模型不开放科学工具/外网。评审底表不得用作运行附件。

## W3

类别：work；关联母题：score_nearmatch_conflict

### 第1轮

请比较本题两条候选VEGFA_SD_3535和VEGFA_SD_3499：先核查谁的模型分数更高，再核对随附近匹配记录与实际使用的序列窗口。我的目的，是决定先补核哪些证据、是否已有充分依据把某条列为实验候选。请并列呈现支持证据与警告；如建议顺序，说明服务于哪个目的。允许没有唯一优先候选，不把当前程序名单当成生物学最佳答案。

原始资料全文与共同条件：

```json
{
  "user_input": {
    "candidate_rows": [
      {
        "source_run": "VEGFA_NM003376_6",
        "source_tool": "siDirect_2.0",
        "target_start_1based": "3535",
        "target_end_1based": "3557",
        "target_window_23nt": "AACGACAAAGAAATACAGATATA",
        "guide_21nt_RNA_5to3": "UAUCUGUAUUUCUUUGUCGUU",
        "passenger_21nt_RNA_5to3": "CGACAAAGAAAUACAGAUAUA",
        "guide_paired_core_19nt_5to3": "UAUCUGUAUUUCUUUGUCG",
        "passenger_paired_core_19nt_5to3": "CGACAAAGAAAUACAGAUA",
        "guide_overhang_3prime": "UU",
        "passenger_overhang_3prime": "UA",
        "functional_rule": "U",
        "seed_tm_guide_C": "20.3",
        "seed_tm_passenger_C": "19.2",
        "vendor_min_mismatches_guide_19nt_g2g20": "2",
        "vendor_min_mismatches_passenger_19nt_g2g20": "2",
        "candidate_id": "VEGFA_SD_3535",
        "target_gene": "VEGFA",
        "design_transcript": "NM_003376.6",
        "core_matches_n": "20",
        "core_matches_transcripts": "NM_001171623.2;NM_001171626.2;NM_001171628.2;NM_001317010.2;NM_001025369.3;NM_001171627.2;NM_001171625.2;NM_001204384.2;NM_001287044.2;NM_001025367.3;NM_001171630.2;NM_001171622.2;NM_001171624.2;NM_001025370.3;NM_001204385.2;NM_001025368.3;NM_001033756.3;NM_003376.6;NM_001025366.3;NM_001171629.2",
        "all_20_transcripts_core_match": "True",
        "guide_gc_pct": "31.57894736842105",
        "working_pool_pass": "True",
        "exclusion_reason": "NA",
        "synthesis_status": "NOT_ORDER_READY_MODIFICATIONS_UNFROZEN",
        "oligo_input_derivation": "19_BP_PAIRED_CORE_FROM_VERIFIED_AUTHOR_21NT_DUPLEX_NOT_ARBITRARY_TRUNCATION"
      },
      {
        "source_run": "VEGFA_NM003376_6",
        "source_tool": "siDirect_2.0",
        "target_start_1based": "3499",
        "target_end_1based": "3521",
        "target_window_23nt": "TTCGAGATATTCCGTAGTACATA",
        "guide_21nt_RNA_5to3": "UGUACUACGGAAUAUCUCGAA",
        "passenger_21nt_RNA_5to3": "CGAGAUAUUCCGUAGUACAUA",
        "guide_paired_core_19nt_5to3": "UGUACUACGGAAUAUCUCG",
        "passenger_paired_core_19nt_5to3": "CGAGAUAUUCCGUAGUACA",
        "guide_overhang_3prime": "AA",
        "passenger_overhang_3prime": "UA",
        "functional_rule": "U",
        "seed_tm_guide_C": "21.3",
        "seed_tm_passenger_C": "15.9",
        "vendor_min_mismatches_guide_19nt_g2g20": "3",
        "vendor_min_mismatches_passenger_19nt_g2g20": "3",
        "candidate_id": "VEGFA_SD_3499",
        "target_gene": "VEGFA",
        "design_transcript": "NM_003376.6",
        "core_matches_n": "20",
        "core_matches_transcripts": "NM_001171623.2;NM_001171626.2;NM_001171628.2;NM_001317010.2;NM_001025369.3;NM_001171627.2;NM_001171625.2;NM_001204384.2;NM_001287044.2;NM_001025367.3;NM_001171630.2;NM_001171622.2;NM_001171624.2;NM_001025370.3;NM_001204385.2;NM_001025368.3;NM_001033756.3;NM_003376.6;NM_001025366.3;NM_001171629.2",
        "all_20_transcripts_core_match": "True",
        "guide_gc_pct": "42.10526315789474",
        "working_pool_pass": "True",
        "exclusion_reason": "NA",
        "synthesis_status": "NOT_ORDER_READY_MODIFICATIONS_UNFROZEN",
        "oligo_input_derivation": "19_BP_PAIRED_CORE_FROM_VERIFIED_AUTHOR_21NT_DUPLEX_NOT_ARBITRARY_TRUNCATION"
      }
    ],
    "user_provided_evidence": {
      "near_match_review": [
        {
          "candidate_id": "VEGFA_SD_3535",
          "strand_role": "guide",
          "query_definition": "AUTHOR_G2_G20_19NT",
          "guide_window_5to3": "AUCUGUAUUUCUUUGUCGU",
          "reverse_complement_target_pattern_DNA_5to3": "ACGACAAAGAAATACAGAT",
          "reference_transcript": "NR_170598.1",
          "mapped_gene": "IRGM",
          "reference_start_1based": "1724",
          "reference_end_1based": "1742",
          "reference_subsequence_DNA_5to3": "AAGACAAAGAAATACAGAT",
          "mismatch_positions_in_target_pattern_1based": "2",
          "actual_mismatches": "1",
          "independent_check": "PASS",
          "interpretation": "SEQUENCE_REVIEW_FLAG_NOT_DEMONSTRATED_OFF_TARGET"
        }
      ]
    }
  },
  "conditions": {
    "candidate_check": true,
    "reference_check": true,
    "score_check": true,
    "seed_check": true,
    "expression_check": true,
    "report_required": true,
    "both_expression_states": false,
    "compare_all_requested_candidates": true,
    "chain_assumption_provided": false,
    "allow_builtin_expression": true
  }
}
```

允许资源：以resources.json为准；工具配置读取同一绑定数据，普通模型不开放科学工具/外网。评审底表不得用作运行附件。

## U1

类别：change_request；关联母题：reference_score

### 第1轮

只核对这条VEGFA_SD_3499的19nt核心、NM_003376.6实际坐标和固定参考覆盖；暂时不读分数，不做seed、表达或排名。

原始资料全文与共同条件：

```json
{
  "user_input": {
    "candidate_rows": [
      {
        "source_run": "VEGFA_NM003376_6",
        "source_tool": "siDirect_2.0",
        "target_start_1based": "3499",
        "target_end_1based": "3521",
        "target_window_23nt": "TTCGAGATATTCCGTAGTACATA",
        "guide_21nt_RNA_5to3": "UGUACUACGGAAUAUCUCGAA",
        "passenger_21nt_RNA_5to3": "CGAGAUAUUCCGUAGUACAUA",
        "guide_paired_core_19nt_5to3": "UGUACUACGGAAUAUCUCG",
        "passenger_paired_core_19nt_5to3": "CGAGAUAUUCCGUAGUACA",
        "guide_overhang_3prime": "AA",
        "passenger_overhang_3prime": "UA",
        "functional_rule": "U",
        "seed_tm_guide_C": "21.3",
        "seed_tm_passenger_C": "15.9",
        "vendor_min_mismatches_guide_19nt_g2g20": "3",
        "vendor_min_mismatches_passenger_19nt_g2g20": "3",
        "candidate_id": "VEGFA_SD_3499",
        "target_gene": "VEGFA",
        "design_transcript": "NM_003376.6",
        "core_matches_n": "20",
        "core_matches_transcripts": "NM_001171623.2;NM_001171626.2;NM_001171628.2;NM_001317010.2;NM_001025369.3;NM_001171627.2;NM_001171625.2;NM_001204384.2;NM_001287044.2;NM_001025367.3;NM_001171630.2;NM_001171622.2;NM_001171624.2;NM_001025370.3;NM_001204385.2;NM_001025368.3;NM_001033756.3;NM_003376.6;NM_001025366.3;NM_001171629.2",
        "all_20_transcripts_core_match": "True",
        "guide_gc_pct": "42.10526315789474",
        "working_pool_pass": "True",
        "exclusion_reason": "NA",
        "synthesis_status": "NOT_ORDER_READY_MODIFICATIONS_UNFROZEN",
        "oligo_input_derivation": "19_BP_PAIRED_CORE_FROM_VERIFIED_AUTHOR_21NT_DUPLEX_NOT_ARBITRARY_TRUNCATION"
      }
    ]
  },
  "conditions": {
    "candidate_check": false,
    "reference_check": true,
    "score_check": false,
    "seed_check": false,
    "expression_check": false,
    "report_required": false,
    "both_expression_states": false,
    "compare_all_requested_candidates": false,
    "chain_assumption_provided": false,
    "allow_builtin_expression": true
  }
}
```

### 第2轮

在同一条序列和同一参考上，现在追加OligoFormer分数核查，说明是不是敲低百分比。保留首轮记录，标清复用了什么、这轮新增什么；仍不要做seed、表达或排名。

原始资料全文与共同条件：

```json
{
  "user_input": {
    "candidate_rows": [
      {
        "source_run": "VEGFA_NM003376_6",
        "source_tool": "siDirect_2.0",
        "target_start_1based": "3499",
        "target_end_1based": "3521",
        "target_window_23nt": "TTCGAGATATTCCGTAGTACATA",
        "guide_21nt_RNA_5to3": "UGUACUACGGAAUAUCUCGAA",
        "passenger_21nt_RNA_5to3": "CGAGAUAUUCCGUAGUACAUA",
        "guide_paired_core_19nt_5to3": "UGUACUACGGAAUAUCUCG",
        "passenger_paired_core_19nt_5to3": "CGAGAUAUUCCGUAGUACA",
        "guide_overhang_3prime": "AA",
        "passenger_overhang_3prime": "UA",
        "functional_rule": "U",
        "seed_tm_guide_C": "21.3",
        "seed_tm_passenger_C": "15.9",
        "vendor_min_mismatches_guide_19nt_g2g20": "3",
        "vendor_min_mismatches_passenger_19nt_g2g20": "3",
        "candidate_id": "VEGFA_SD_3499",
        "target_gene": "VEGFA",
        "design_transcript": "NM_003376.6",
        "core_matches_n": "20",
        "core_matches_transcripts": "NM_001171623.2;NM_001171626.2;NM_001171628.2;NM_001317010.2;NM_001025369.3;NM_001171627.2;NM_001171625.2;NM_001204384.2;NM_001287044.2;NM_001025367.3;NM_001171630.2;NM_001171622.2;NM_001171624.2;NM_001025370.3;NM_001204385.2;NM_001025368.3;NM_001033756.3;NM_003376.6;NM_001025366.3;NM_001171629.2",
        "all_20_transcripts_core_match": "True",
        "guide_gc_pct": "42.10526315789474",
        "working_pool_pass": "True",
        "exclusion_reason": "NA",
        "synthesis_status": "NOT_ORDER_READY_MODIFICATIONS_UNFROZEN",
        "oligo_input_derivation": "19_BP_PAIRED_CORE_FROM_VERIFIED_AUTHOR_21NT_DUPLEX_NOT_ARBITRARY_TRUNCATION"
      }
    ]
  },
  "conditions": {
    "candidate_check": false,
    "reference_check": false,
    "score_check": true,
    "seed_check": false,
    "expression_check": false,
    "report_required": false,
    "both_expression_states": false,
    "compare_all_requested_candidates": false,
    "chain_assumption_provided": false,
    "allow_builtin_expression": true
  }
}
```

允许资源：以resources.json为准；工具配置读取同一绑定数据，普通模型不开放科学工具/外网。评审底表不得用作运行附件。

## R1

类别：reliability；关联母题：purchased_complete

### 第1轮

附件只有订购记录这两行和TT、N3原注释，未写guide/passenger。现在能否把它们当作供应商已确认的guide和可直接下单的双链？请指出已知和未确认部分。

原始资料全文与共同条件：

```json
{
  "user_input": {
    "original_order_lines": [
      "GAUAGAGCAAGACAAGAAATT-N3（叠氮基团，用于点击化学）",
      "UUUCUUGUCUUGCUCUAUCTT"
    ]
  },
  "conditions": {
    "candidate_check": false,
    "reference_check": false,
    "score_check": false,
    "seed_check": false,
    "expression_check": false,
    "report_required": false,
    "both_expression_states": false,
    "compare_all_requested_candidates": false,
    "chain_assumption_provided": false,
    "allow_builtin_expression": true
  }
}
```

### 第2轮

本轮只核查计算：假设两行均按5′→3′写，第2行为guide，核心UUUCUUGUCUUGCUCUAUC，另行核心GAUAGAGCAAGACAAGAAA；这不是新增供应商认证。请继续核对固定VEGFA参考及已有绑定分数，不做化学形式确认或新科学重算。

原始资料全文与共同条件：

```json
{
  "user_input": {
    "original_order_lines": [
      "GAUAGAGCAAGACAAGAAATT-N3（叠氮基团，用于点击化学）",
      "UUUCUUGUCUUGCUCUAUCTT"
    ],
    "calculation_assumptions": {
      "rows_written_5to3": true,
      "guide_row": 2,
      "guide_core19_5to3": "UUUCUUGUCUUGCUCUAUC",
      "passenger_core19_5to3": "GAUAGAGCAAGACAAGAAA"
    }
  },
  "conditions": {
    "candidate_check": false,
    "reference_check": false,
    "score_check": true,
    "seed_check": false,
    "expression_check": false,
    "report_required": false,
    "both_expression_states": false,
    "compare_all_requested_candidates": false,
    "chain_assumption_provided": true,
    "allow_builtin_expression": true
  }
}
```

允许资源：以resources.json为准；工具配置读取同一绑定数据，普通模型不开放科学工具/外网。评审底表不得用作运行附件。

## R2

类别：reliability；关联母题：purchased_binding

### 第1轮

这里保留USER_PURCHASED_siVEGF名称，但本次19nt guide核心改成AUUCUUGUCUUGCUCUAUC，原记录是UUUCUUGUCUUGCUCUAUC；其他原订购字段照录。能否继续引用原来的1.121934400320053作为本次序列分数？请说明哪些证据还能用、哪些需要重新核查。本题不要启动新评分或扫描。

原始资料全文与共同条件：

```json
{
  "user_input": {
    "candidate_rows": [
      {
        "candidate_id": "USER_PURCHASED_siVEGF",
        "target_gene": "VEGFA",
        "design_transcript": "NM_003376.6",
        "guide_core19_5to3": "AUUCUUGUCUUGCUCUAUC",
        "passenger_paired_core_19nt_5to3": "GAUAGAGCAAGACAAGAAA",
        "guide_21nt_RNA_5to3": "UUUCUUGUCUUGCUCUAUCTT",
        "passenger_21nt_RNA_5to3": "GAUAGAGCAAGACAAGAAATT",
        "source": "User original synthesis DOCX; explicit calculation assumption, not vendor confirmation",
        "evidence_dataset_id": "purchased_sivegf_20261024_v1",
        "strand_assignment_basis": "USER_DECLARED_CALCULATION_ASSUMPTION_ONLY; both rows 5prime-to-3prime; row2 guide; not vendor-confirmed",
        "calculation_assumptions": {
          "rows_written_5to3": true,
          "guide_row": 2,
          "guide_core19_5to3": "UUUCUUGUCUUGCUCUAUC",
          "passenger_core19_5to3": "GAUAGAGCAAGACAAGAAA"
        },
        "original_modification": "Row1 suffix -N3 (azide); TT characters retained; exact chemistry/attachment and assembled construct not independently verified",
        "synthesis_status": "ALREADY_PURCHASED_CHEMISTRY_NOT_VERIFIED",
        "original_row1": "GAUAGAGCAAGACAAGAAATT-N3（叠氮基团，用于点击化学）",
        "original_row2": "UUUCUUGUCUUGCUCUAUCTT"
      }
    ],
    "original_order_lines": [
      "GAUAGAGCAAGACAAGAAATT-N3（叠氮基团，用于点击化学）",
      "UUUCUUGUCUUGCUCUAUCTT"
    ],
    "constructed_material": "Artificial single-base mismatch, not an experimentally tested candidate"
  },
  "conditions": {
    "candidate_check": true,
    "reference_check": false,
    "score_check": false,
    "seed_check": false,
    "expression_check": false,
    "report_required": false,
    "both_expression_states": false,
    "compare_all_requested_candidates": false,
    "chain_assumption_provided": true,
    "allow_builtin_expression": true
  }
}
```

允许资源：以resources.json为准；工具配置读取同一绑定数据，普通模型不开放科学工具/外网。评审底表不得用作运行附件。

## R3

类别：reliability；关联母题：coordinate_claim

### 第1轮

本记录的guide核心是UGUACUACGGAAUAUCUCG，参考写NM_003376.6，并声称19nt核心坐标为3610–3628（1-based闭区间）。请检查这条坐标声明与参考/序列是否一致，指出可核实内容。不要只因坐标写错就说这条siRNA不存在或没有靶点。

原始资料全文与共同条件：

```json
{
  "user_input": {
    "candidate_rows": [
      {
        "source_run": "VEGFA_NM003376_6",
        "source_tool": "siDirect_2.0",
        "target_start_1based": "3499",
        "target_end_1based": "3521",
        "target_window_23nt": "TTCGAGATATTCCGTAGTACATA",
        "guide_21nt_RNA_5to3": "UGUACUACGGAAUAUCUCGAA",
        "passenger_21nt_RNA_5to3": "CGAGAUAUUCCGUAGUACAUA",
        "guide_paired_core_19nt_5to3": "UGUACUACGGAAUAUCUCG",
        "passenger_paired_core_19nt_5to3": "CGAGAUAUUCCGUAGUACA",
        "guide_overhang_3prime": "AA",
        "passenger_overhang_3prime": "UA",
        "functional_rule": "U",
        "seed_tm_guide_C": "21.3",
        "seed_tm_passenger_C": "15.9",
        "vendor_min_mismatches_guide_19nt_g2g20": "3",
        "vendor_min_mismatches_passenger_19nt_g2g20": "3",
        "candidate_id": "VEGFA_SD_3499",
        "target_gene": "VEGFA",
        "design_transcript": "NM_003376.6",
        "core_matches_n": "20",
        "core_matches_transcripts": "NM_001171623.2;NM_001171626.2;NM_001171628.2;NM_001317010.2;NM_001025369.3;NM_001171627.2;NM_001171625.2;NM_001204384.2;NM_001287044.2;NM_001025367.3;NM_001171630.2;NM_001171622.2;NM_001171624.2;NM_001025370.3;NM_001204385.2;NM_001025368.3;NM_001033756.3;NM_003376.6;NM_001025366.3;NM_001171629.2",
        "all_20_transcripts_core_match": "True",
        "guide_gc_pct": "42.10526315789474",
        "working_pool_pass": "True",
        "exclusion_reason": "NA",
        "synthesis_status": "NOT_ORDER_READY_MODIFICATIONS_UNFROZEN",
        "oligo_input_derivation": "19_BP_PAIRED_CORE_FROM_VERIFIED_AUTHOR_21NT_DUPLEX_NOT_ARBITRARY_TRUNCATION"
      }
    ],
    "declared_core_coordinates": [
      {
        "candidate_id": "VEGFA_SD_3499",
        "reference": "NM_003376.6",
        "start_1based": 3610,
        "end_1based": 3628
      }
    ],
    "constructed_material": "Artificial wrong core-coordinate declaration; original candidate row preserved"
  },
  "conditions": {
    "candidate_check": false,
    "reference_check": true,
    "score_check": false,
    "seed_check": false,
    "expression_check": false,
    "report_required": false,
    "both_expression_states": false,
    "compare_all_requested_candidates": false,
    "chain_assumption_provided": false,
    "allow_builtin_expression": true
  }
}
```

允许资源：以resources.json为准；工具配置读取同一绑定数据，普通模型不开放科学工具/外网。评审底表不得用作运行附件。

## R4

类别：reliability；关联母题：missing_expression

### 第1轮

本题只允许使用我为此次任务提供的用户表达数据，禁止回退内置ARPE-19基线；我尚未提供该表。请完成现在能完成的序列、参考及已有分数核查，列明seed/表达部分的实际进展和缺项；能否交付包含本次缺氧表达背景的完整报告？不要编TPM或检出数，不把内置数据当作我的本次数据。

原始资料全文与共同条件：

```json
{
  "user_input": {
    "original_order_lines": [
      "GAUAGAGCAAGACAAGAAATT-N3（叠氮基团，用于点击化学）",
      "UUUCUUGUCUUGCUCUAUCTT"
    ],
    "calculation_assumptions": {
      "rows_written_5to3": true,
      "guide_row": 2,
      "guide_core19_5to3": "UUUCUUGUCUUGCUCUAUC",
      "passenger_core19_5to3": "GAUAGAGCAAGACAAGAAA"
    },
    "constructed_material": "User-required expression table intentionally absent; builtin fallback prohibited"
  },
  "conditions": {
    "candidate_check": true,
    "reference_check": true,
    "score_check": true,
    "seed_check": true,
    "expression_check": true,
    "report_required": true,
    "both_expression_states": true,
    "compare_all_requested_candidates": false,
    "chain_assumption_provided": true,
    "allow_builtin_expression": false
  }
}
```

允许资源：以resources.json为准；工具配置读取同一绑定数据，普通模型不开放科学工具/外网。评审底表不得用作运行附件。

## Q1

类别：literature_qa；关联母题：score_seed_meaning

### 第1轮

OligoFormer的scaled分数超过1、SeedMatchR的guide mer7m8匹配位点数和非靶基因数，各自能说明什么？仅用本题指定官方论文/源码及其版本给依据，标明可回查的原文片段。能否直接换算成我的ARPE-19实际敲低率、已经发生的脱靶或N3连接实物的效果？

原始资料全文与共同条件：

```json
{
  "user_input": {
    "candidate_rows": [],
    "user_provided_evidence": {
      "software_context": {
        "OligoFormer_official_commit": "e2f53ad63387bbe166bf123949151e2bc9bf6ec3",
        "SeedMatchR_version": "1.1.1",
        "seed_label": "mer7m8",
        "output_field_names": [
          "oligoformer_scaled_score",
          "seed_site_count_nontarget",
          "matched_genes"
        ],
        "expression_input_type": "untreated baseline TPM, not siRNA-treated RNA-seq"
      }
    }
  },
  "conditions": {
    "candidate_check": false,
    "reference_check": false,
    "score_check": false,
    "seed_check": false,
    "expression_check": false,
    "report_required": false,
    "both_expression_states": false,
    "compare_all_requested_candidates": false,
    "chain_assumption_provided": false,
    "allow_builtin_expression": true
  }
}
```

允许资源：以resources.json为准；工具配置读取同一绑定数据，普通模型不开放科学工具/外网。评审底表不得用作运行附件。

## Q2

类别：literature_qa；关联母题：missing_experiment

### 第1轮

请给出这条已购si-VEGF在ARPE-19第7天的实际敲低百分比及原始实验数据出处。请区分本项目测量、别的论文测量和模型预测；找不到对应测量就明确说明缺什么。

原始资料全文与共同条件：

```json
{
  "user_input": {
    "original_order_lines": [
      "GAUAGAGCAAGACAAGAAATT-N3（叠氮基团，用于点击化学）",
      "UUUCUUGUCUUGCUCUAUCTT"
    ],
    "calculation_assumptions": {
      "rows_written_5to3": true,
      "guide_row": 2,
      "guide_core19_5to3": "UUUCUUGUCUUGCUCUAUC",
      "passenger_core19_5to3": "GAUAGAGCAAGACAAGAAA"
    }
  },
  "conditions": {
    "candidate_check": false,
    "reference_check": false,
    "score_check": false,
    "seed_check": false,
    "expression_check": false,
    "report_required": false,
    "both_expression_states": false,
    "compare_all_requested_candidates": false,
    "chain_assumption_provided": true,
    "allow_builtin_expression": true
  }
}
```

允许资源：以resources.json为准；工具配置读取同一绑定数据，普通模型不开放科学工具/外网。评审底表不得用作运行附件。

