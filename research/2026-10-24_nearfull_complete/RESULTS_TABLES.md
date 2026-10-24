# Results tables: completed scope

All counts below describe the retained fixed-reference computation. They are not biological replicate counts, experimental efficacy, safety or independent human accuracy.

| Item | Actual result |
|---|---:|
| Unchanged reporting-pool designs | 65 |
| Purchased duplex, separate | 1 |
| Previously completed near-full queries reused | 24 |
| New unique near-full queries completed | 240 |
| Complete unique query plan | 264 |
| Queries with at least one raw hit | 246 |
| Zero-hit queries | 18 |
| Failed / not run | 0 / 0 |
| New run wall time | 1640.096 s (27 min 20.096 s) |
| Raw stored site rows, all queries | 7480 |
| New raw site rows | 6943 |
| Full 19-nt intervals within reference | 7479 |
| Boundary overlap, separately reported | 1 |
| Designs with a mapped non-target 0/1-mismatch hit in any query | 23 / 65 |
| Designs without such a hit in all four queries | 42 / 65 |
| Unknown-mapping hit rows | 0 |
| Stored non-target 0/1-mismatch sites | 127 |

The 23 designs include the two previously found coding-region entries and 21 additional entries from the newly completed scope. Absence of these hits is not proof of safety. No change to the 65-entry pool, no best-of-65 ranking and no new OligoFormer or seed computation were made.

One raw Biostrings hit for VEGFA_SD_3573, passenger positions 2–20, maps to XR_007059861.1:6983–7001 while the reference length is 7000. The overlap contains 18 observed bases, one observed mismatch and one pattern base beyond the reference; the fixed Biostrings 2.70.1 neditStartingAt result is two. Raw output is retained. For that query at at most two mismatches, raw totals are 64 sites/16 non-target genes; the supplementary full-window-only view is 63/15. The 0/1-mismatch findings and purchased case are unaffected. The full-window view is an explicit derived interpretation, not a hidden change to raw output or pool rules.

## All 65 designs (source order, not a new rank)

Scores are model outputs, coverage counts refer to 20 retained transcript references, and columns G1/G2/P1/P2 count non-target genes at at most one mismatch for guide core / guide 2–20 / passenger core / passenger 2–20. Complete sequences, original chains, context, reference matches and all mismatch summaries are in all_65_designs_complete.tsv/.json.

| Candidate | Core position | Region | Coverage | Score | Official flag | G1 | G2 | P1 | P2 |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| VEGFA_SD_0124 | 126–144 | 5prime_UTR_or_boundary | 19 | 0.939009 | 1 | 0 | 0 | 0 | 0 |
| VEGFA_SD_0126 | 128–146 | 5prime_UTR_or_boundary | 19 | 1.026206 | 1 | 0 | 0 | 0 | 0 |
| VEGFA_SD_0149 | 151–169 | 5prime_UTR_or_boundary | 19 | 0.966429 | 0 | 0 | 0 | 0 | 0 |
| VEGFA_SD_0150 | 152–170 | 5prime_UTR_or_boundary | 19 | 0.917387 | 0 | 0 | 0 | 0 | 0 |
| VEGFA_SD_0192 | 194–212 | 5prime_UTR_or_boundary | 19 | 0.953370 | 0 | 0 | 0 | 0 | 0 |
| VEGFA_SD_0194 | 196–214 | 5prime_UTR_or_boundary | 19 | 0.973202 | 1 | 0 | 0 | 0 | 0 |
| VEGFA_SD_0199 | 201–219 | 5prime_UTR_or_boundary | 19 | 0.864287 | 1 | 0 | 0 | 0 | 0 |
| VEGFA_SD_0203 | 205–223 | 5prime_UTR_or_boundary | 19 | 0.847733 | 1 | 0 | 0 | 0 | 0 |
| VEGFA_SD_0278 | 280–298 | 5prime_UTR_or_boundary | 19 | 0.880882 | 4 | 0 | 0 | 1 | 0 |
| VEGFA_SD_1157 | 1159–1177 | CDS | 20 | 0.948994 | 0 | 0 | 0 | 0 | 0 |
| VEGFA_SD_1552 | 1554–1572 | CDS | 14 | 0.972631 | 0 | 2 | 1 | 0 | 0 |
| VEGFA_SD_1555 | 1557–1575 | CDS | 14 | 0.967256 | 0 | 0 | 0 | 0 | 0 |
| VEGFA_SD_1559 | 1561–1579 | CDS | 14 | 0.939003 | 4 | 0 | 0 | 0 | 0 |
| VEGFA_SD_1588 | 1590–1608 | CDS | 14 | 0.985282 | 2 | 0 | 1 | 0 | 0 |
| VEGFA_SD_1979 | 1981–1999 | 3prime_UTR | 20 | 1.065038 | 0 | 0 | 0 | 0 | 0 |
| VEGFA_SD_1980 | 1982–2000 | 3prime_UTR | 20 | 0.978723 | 1 | 0 | 0 | 0 | 0 |
| VEGFA_SD_2739 | 2741–2759 | 3prime_UTR | 20 | 0.881496 | 0 | 0 | 0 | 0 | 0 |
| VEGFA_SD_2924 | 2926–2944 | 3prime_UTR | 20 | 0.841346 | 1 | 0 | 0 | 0 | 0 |
| VEGFA_SD_2925 | 2927–2945 | 3prime_UTR | 20 | 0.873781 | 1 | 1 | 0 | 0 | 1 |
| VEGFA_SD_2937 | 2939–2957 | 3prime_UTR | 20 | 0.845078 | 1 | 0 | 0 | 0 | 0 |
| VEGFA_SD_2947 | 2949–2967 | 3prime_UTR | 20 | 0.820012 | 1 | 0 | 0 | 0 | 0 |
| VEGFA_SD_2949 | 2951–2969 | 3prime_UTR | 20 | 0.720183 | 1 | 0 | 0 | 0 | 0 |
| VEGFA_SD_2970 | 2972–2990 | 3prime_UTR | 20 | 0.857564 | 1 | 0 | 0 | 1 | 0 |
| VEGFA_SD_2980 | 2982–3000 | 3prime_UTR | 20 | 0.926884 | 1 | 0 | 0 | 0 | 0 |
| VEGFA_SD_2982 | 2984–3002 | 3prime_UTR | 20 | 0.901698 | 1 | 1 | 1 | 0 | 0 |
| VEGFA_SD_2987 | 2989–3007 | 3prime_UTR | 20 | 0.822054 | 1 | 1 | 0 | 1 | 1 |
| VEGFA_SD_2990 | 2992–3010 | 3prime_UTR | 20 | 0.950965 | 1 | 0 | 0 | 0 | 0 |
| VEGFA_SD_3009 | 3011–3029 | 3prime_UTR | 20 | 0.847742 | 1 | 0 | 0 | 0 | 0 |
| VEGFA_SD_3046 | 3048–3066 | 3prime_UTR | 20 | 0.947723 | 2 | 0 | 0 | 0 | 0 |
| VEGFA_SD_3056 | 3058–3076 | 3prime_UTR | 20 | 1.003133 | 1 | 0 | 0 | 0 | 0 |
| VEGFA_SD_3057 | 3059–3077 | 3prime_UTR | 20 | 0.908414 | 1 | 0 | 0 | 0 | 0 |
| VEGFA_SD_3058 | 3060–3078 | 3prime_UTR | 20 | 0.918742 | 1 | 0 | 0 | 0 | 0 |
| VEGFA_SD_3065 | 3067–3085 | 3prime_UTR | 20 | 0.865261 | 1 | 0 | 0 | 2 | 1 |
| VEGFA_SD_3119 | 3121–3139 | 3prime_UTR | 20 | 0.923205 | 4 | 0 | 0 | 0 | 0 |
| VEGFA_SD_3125 | 3127–3145 | 3prime_UTR | 20 | 0.818176 | 1 | 0 | 0 | 1 | 0 |
| VEGFA_SD_3131 | 3133–3151 | 3prime_UTR | 20 | 0.860958 | 1 | 0 | 0 | 1 | 1 |
| VEGFA_SD_3193 | 3195–3213 | 3prime_UTR | 20 | 0.769388 | 4 | 0 | 0 | 0 | 0 |
| VEGFA_SD_3202 | 3204–3222 | 3prime_UTR | 20 | 0.921756 | 1 | 0 | 0 | 0 | 0 |
| VEGFA_SD_3210 | 3212–3230 | 3prime_UTR | 20 | 0.893629 | 1 | 0 | 0 | 0 | 1 |
| VEGFA_SD_3214 | 3216–3234 | 3prime_UTR | 20 | 0.770635 | 1 | 0 | 0 | 0 | 0 |
| VEGFA_SD_3221 | 3223–3241 | 3prime_UTR | 20 | 0.820668 | 1 | 0 | 0 | 1 | 1 |
| VEGFA_SD_3281 | 3283–3301 | 3prime_UTR | 20 | 0.797621 | 1 | 1 | 2 | 0 | 0 |
| VEGFA_SD_3287 | 3289–3307 | 3prime_UTR | 20 | 0.858021 | 1 | 0 | 0 | 0 | 0 |
| VEGFA_SD_3295 | 3297–3315 | 3prime_UTR | 20 | 0.913571 | 1 | 0 | 0 | 0 | 0 |
| VEGFA_SD_3297 | 3299–3317 | 3prime_UTR | 20 | 0.934861 | 1 | 1 | 0 | 0 | 0 |
| VEGFA_SD_3314 | 3316–3334 | 3prime_UTR | 20 | 0.832579 | 1 | 1 | 1 | 0 | 0 |
| VEGFA_SD_3318 | 3320–3338 | 3prime_UTR | 20 | 0.870196 | 1 | 0 | 0 | 0 | 0 |
| VEGFA_SD_3361 | 3363–3381 | 3prime_UTR | 20 | 0.990044 | 1 | 0 | 0 | 0 | 0 |
| VEGFA_SD_3375 | 3377–3395 | 3prime_UTR | 20 | 0.866235 | 2 | 0 | 0 | 2 | 1 |
| VEGFA_SD_3385 | 3387–3405 | 3prime_UTR | 20 | 0.808415 | 1 | 1 | 0 | 1 | 1 |
| VEGFA_SD_3429 | 3431–3449 | 3prime_UTR | 20 | 0.940152 | 0 | 0 | 0 | 0 | 0 |
| VEGFA_SD_3432 | 3434–3452 | 3prime_UTR | 20 | 0.890536 | 1 | 0 | 0 | 0 | 0 |
| VEGFA_SD_3434 | 3436–3454 | 3prime_UTR | 20 | 0.857354 | 1 | 0 | 0 | 0 | 0 |
| VEGFA_SD_3455 | 3457–3475 | 3prime_UTR | 20 | 0.971205 | 1 | 0 | 0 | 1 | 0 |
| VEGFA_SD_3499 | 3501–3519 | 3prime_UTR | 20 | 0.991514 | 0 | 0 | 0 | 0 | 0 |
| VEGFA_SD_3500 | 3502–3520 | 3prime_UTR | 20 | 0.975334 | 0 | 0 | 0 | 0 | 0 |
| VEGFA_SD_3502 | 3504–3522 | 3prime_UTR | 20 | 0.972451 | 4 | 0 | 0 | 0 | 0 |
| VEGFA_SD_3508 | 3510–3528 | 3prime_UTR | 20 | 0.912314 | 1 | 0 | 0 | 0 | 0 |
| VEGFA_SD_3509 | 3511–3529 | 3prime_UTR | 20 | 0.884798 | 1 | 0 | 0 | 0 | 0 |
| VEGFA_SD_3510 | 3512–3530 | 3prime_UTR | 20 | 0.832881 | 1 | 0 | 0 | 0 | 2 |
| VEGFA_SD_3535 | 3537–3555 | 3prime_UTR | 20 | 1.003590 | 0 | 0 | 1 | 0 | 0 |
| VEGFA_SD_3536 | 3538–3556 | 3prime_UTR | 20 | 0.930051 | 1 | 0 | 0 | 0 | 0 |
| VEGFA_SD_3538 | 3540–3558 | 3prime_UTR | 20 | 0.898817 | 1 | 2 | 0 | 0 | 0 |
| VEGFA_SD_3542 | 3544–3562 | 3prime_UTR | 20 | 0.971725 | 1 | 0 | 2 | 0 | 0 |
| VEGFA_SD_3573 | 3575–3593 | 3prime_UTR | 20 | 0.753887 | 1 | 1 | 0 | 0 | 0 |

## Real purchased case

One case completed six scientific tools, with one planning and seven execution model requests (39048 tokens). Original responses and the observed 24-nt passenger transcription error are retained; see live/ANSWER_CORRECTION_ZH.md. The correct source core is 19 nt. This is not an error-free-answer or scientific-accuracy result. No independent human scores or new wet-lab measurements are available.
