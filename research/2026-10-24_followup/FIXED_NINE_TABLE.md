# Complete fixed development pool: all nine candidates

All sequences are written 5prime to 3prime. Coordinates are 1-based and inclusive on NM_003376.6; CDS 497-1684. The 23-nt design window and 19-nt paired core are distinct. The original 21-nt strands and their native two-base 3prime extensions are retained; these are design records, not a finalized chemical order.

Machine-readable full table: [TSV](fixed_nine_complete_table.tsv) and [JSON](fixed_nine_complete_table.json), including original source, versions and input context.

## Sequences and reference coordinates

| candidate_id | target23_sense_DNA | guide21_RNA | passenger21_RNA | guide19_RNA | passenger19_RNA | design_window23_start_1based | design_window23_end_1based | core19_start_1based | core19_end_1based | guide_3prime_overhang | passenger_3prime_overhang | NM003376_6_feature |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| VEGFA_SD_1157 | GTGAAGTTCATGGATGTCTATCA | AUAGACAUCCAUGAACUUCAC | GAAGUUCAUGGAUGUCUAUCA | AUAGACAUCCAUGAACUUC | GAAGUUCAUGGAUGUCUAU | 1157 | 1179 | 1159 | 1177 | AC | CA | CDS |
| VEGFA_SD_2739 | ACCATTGAAACCACTAGTTCTGT | AGAACUAGUGGUUUCAAUGGU | CAUUGAAACCACUAGUUCUGU | AGAACUAGUGGUUUCAAUG | CAUUGAAACCACUAGUUCU | 2739 | 2761 | 2741 | 2759 | GU | GU | 3prime_UTR |
| VEGFA_SD_3119 | TAGCTTATCTTGAACAGATATTT | AUAUCUGUUCAAGAUAAGCUA | GCUUAUCUUGAACAGAUAUUU | AUAUCUGUUCAAGAUAAGC | GCUUAUCUUGAACAGAUAU | 3119 | 3141 | 3121 | 3139 | UA | UU | 3prime_UTR |
| VEGFA_SD_3193 | CACATTCCTTTGAAATAAGGTTT | ACCUUAUUUCAAAGGAAUGUG | CAUUCCUUUGAAAUAAGGUUU | ACCUUAUUUCAAAGGAAUG | CAUUCCUUUGAAAUAAGGU | 3193 | 3215 | 3195 | 3213 | UG | UU | 3prime_UTR |
| VEGFA_SD_3429 | TGCTACTGTTTATCCGTAATAAT | UAUUACGGAUAAACAGUAGCA | CUACUGUUUAUCCGUAAUAAU | UAUUACGGAUAAACAGUAG | CUACUGUUUAUCCGUAAUA | 3429 | 3451 | 3431 | 3449 | CA | AU | 3prime_UTR |
| VEGFA_SD_3499 | TTCGAGATATTCCGTAGTACATA | UGUACUACGGAAUAUCUCGAA | CGAGAUAUUCCGUAGUACAUA | UGUACUACGGAAUAUCUCG | CGAGAUAUUCCGUAGUACA | 3499 | 3521 | 3501 | 3519 | AA | UA | 3prime_UTR |
| VEGFA_SD_3500 | TCGAGATATTCCGTAGTACATAT | AUGUACUACGGAAUAUCUCGA | GAGAUAUUCCGUAGUACAUAU | AUGUACUACGGAAUAUCUC | GAGAUAUUCCGUAGUACAU | 3500 | 3522 | 3502 | 3520 | GA | AU | 3prime_UTR |
| VEGFA_SD_3502 | GAGATATTCCGTAGTACATATTT | AUAUGUACUACGGAAUAUCUC | GAUAUUCCGUAGUACAUAUUU | AUAUGUACUACGGAAUAUC | GAUAUUCCGUAGUACAUAU | 3502 | 3524 | 3504 | 3522 | UC | UU | 3prime_UTR |
| VEGFA_SD_3535 | AACGACAAAGAAATACAGATATA | UAUCUGUAUUUCUUUGUCGUU | CGACAAAGAAAUACAGAUAUA | UAUCUGUAUUUCUUUGUCG | CGACAAAGAAAUACAGAUA | 3535 | 3557 | 3537 | 3555 | UU | UA | 3prime_UTR |

## Historical predicted scores and review flags

| candidate_id | oligo_raw_class1 | oligo_scaled_score | oligo_official_func_filter | historical_review_flags | matched_fixed_transcripts | experimental_knockdown_percent |
| --- | --- | --- | --- | --- | --- | --- |
| VEGFA_SD_1157 | 0.7076764106750488 | 0.9489940667152404 | 0 | None recorded | 20 | NOT_MEASURED_IN_THIS_PROJECT |
| VEGFA_SD_2739 | 0.6573420166969299 | 0.881495644390583 | 0 | None recorded | 20 | NOT_MEASURED_IN_THIS_PROJECT |
| VEGFA_SD_3119 | 0.6884453892707825 | 0.9232052670121192 | 4 | official_func_filter=4 | 20 | NOT_MEASURED_IN_THIS_PROJECT |
| VEGFA_SD_3193 | 0.5737422704696655 | 0.7693883846998214 | 4 | official_func_filter=4 | 20 | NOT_MEASURED_IN_THIS_PROJECT |
| VEGFA_SD_3429 | 0.7010828852653503 | 0.9401521491408348 | 0 | None recorded | 20 | NOT_MEASURED_IN_THIS_PROJECT |
| VEGFA_SD_3499 | 0.7393843531608582 | 0.9915144175887107 | 0 | None recorded | 20 | NOT_MEASURED_IN_THIS_PROJECT |
| VEGFA_SD_3500 | 0.7273184061050415 | 0.9753339825868607 | 0 | None recorded | 20 | NOT_MEASURED_IN_THIS_PROJECT |
| VEGFA_SD_3502 | 0.7251685857772827 | 0.9724510735273361 | 4 | official_func_filter=4 | 20 | NOT_MEASURED_IN_THIS_PROJECT |
| VEGFA_SD_3535 | 0.7483892440795898 | 1.0035899763107299 | 0 | historical near-match <=1 mismatch needs manual review | 20 | NOT_MEASURED_IN_THIS_PROJECT |

## Historical guide mer7m8 matches and baseline annotation

| candidate_id | guide_mer7m8_target_DNA | seed_sites_including_VEGFA | seed_matched_genes_including_VEGFA | seed_sites_excluding_VEGFA | seed_matched_genes_excluding_VEGFA | baseline_mappable_non_target_genes | unmapped_genes | normoxia_detected_genes | hypoxia_detected_genes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| VEGFA_SD_1157 | ATGTCTA | 2197 | 1876 | 2197 | 1876 | 1874 | 2 | 1155 | 1086 |
| VEGFA_SD_2739 | CTAGTTC | 1495 | 1366 | 1494 | 1365 | 1362 | 3 | 851 | 809 |
| VEGFA_SD_3119 | ACAGATA | 2665 | 2210 | 2663 | 2209 | 2206 | 3 | 1335 | 1275 |
| VEGFA_SD_3193 | AATAAGG | 2386 | 1989 | 2385 | 1988 | 1986 | 2 | 1206 | 1150 |
| VEGFA_SD_3429 | CCGTAAT | 279 | 277 | 278 | 276 | 275 | 1 | 200 | 187 |
| VEGFA_SD_3499 | GTAGTAC | 778 | 729 | 777 | 728 | 726 | 2 | 480 | 463 |
| VEGFA_SD_3500 | TAGTACA | 1548 | 1334 | 1547 | 1333 | 1330 | 3 | 858 | 811 |
| VEGFA_SD_3502 | GTACATA | 2516 | 2140 | 2515 | 2139 | 2136 | 3 | 1443 | 1354 |
| VEGFA_SD_3535 | TACAGAT | 3156 | 2603 | 3155 | 2602 | 2600 | 2 | 1646 | 1561 |

## Interpretation

The seed counts are sites and distinct genes, respectively. Mappable genes can be derived as non-target matched genes minus unmapped genes in the saved report; baseline-detected counts apply only to mapped genes in each state and must not be substituted for total matches. A gene can contain multiple sites. The baseline expression annotation is not siRNA-perturbation evidence.

func_filter=4 denotes the historical official palindrome check for 3119, 3193 and 3502. The separate near-full-length review flag for 3535 is retained. A zero flag is not a safety certification. No candidate has a project-measured knockdown percentage. The development pool is not an unseen test set or a final experimental shortlist.
