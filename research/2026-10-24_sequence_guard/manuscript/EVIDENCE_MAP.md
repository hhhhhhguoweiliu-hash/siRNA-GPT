# Manuscript evidence map

All paths below are relative to the repository root. The manuscript is an integrated working draft for scientific/author review, not a claim that independent scoring or wet-laboratory validation is finished.

| Manuscript item | Original or derived evidence | Limit |
|---|---|---|
| Original 104 and 65-entry reporting pool | research/2026-10-24_candidate_v2/inputs/original_all_104.tsv; all_104_decisions.tsv; research/2026-10-23_candidate_provenance/ | Retained historical siDirect request/output; exact historical database release unavailable |
| 66 predictions and 132 strand-level seed calculations | research/2026-10-24_candidate_v2/oligo_pilot_02/, oligo_remaining/, seed_pilot_02/, seed_remaining/; completion_audit.json | Actual local official-tool execution through recorded adaptation; not new hosted inference or measured efficacy |
| 264 completed near-full queries | research/2026-10-24_nearfull_complete/remaining_240.tsv; execution.json; completion_audit.json; all_264_actual_states.tsv; all_query_raw_manifest.json | New 240 plus unchanged prior 24, same fixed reference; no duplicate claim for the old intermediate 256 list |
| 7480 raw / 7479 full-window sites | research/2026-10-24_nearfull_complete/all_264_summary.tsv; all_264_full_window_within_reference_summary.tsv; boundary_overlaps_separate.tsv; boundary_confirmation/ | One actual 18-base boundary overlap remains separately visible; no raw row silently deleted |
| 23/65 with zero-/one-mismatch non-target matches | research/2026-10-24_nearfull_complete/new_findings.json; all_0or1mm_non_target_or_unknown_sites.tsv; all_65_designs_complete.tsv | Sequence-reference flags, not experimentally measured off-target effects or a new ranking |
| Purchased original duplex, TT/N3 and role assumption | data/user_ordered_sequences/20261024/sequence_synthesis_original.docx; sequence_records.json; data/purchased_sivegf_20261024_v1/ | Source strings retained; supplier-confirmed physical role/end chemistry unavailable |
| Purchased genuine model case | research/2026-10-24_nearfull_complete/live/conversation_export_original.json; actual_tool_export_original.zip; tool_export/attempts/; actual_model_call_summary.json | One case, eight requests, 39048 tokens; code03092ef; not eight independent questions |
| Incorrect 24-nt passenger string | Same actual tool export’s report.json/model_summary and model responses; live/answer_sequence_discrepancy.json; ANSWER_CORRECTION_ZH.md | Error also appeared in the original HTML/JSON narrative; correction is later and does not make the original answer correct |
| Baseline expression association | Original case query_expression.json and seed_expression_details.tsv; data/expression.tsv.gz; docs/reviews/20261024_2218_complete_results_audit.json | 2836 mapped, hypoxia1595, normoxia1695, unmapped3; baseline, not siRNA treatment |
| Historical 54 records and stored software states | research/2026-10-22_fairness/three_arm/results.json.gz; research/2026-10-24_sequence_guard/historical_development_readonly_check.json | Six development tasks × three arms × three repetitions; no independent quality scores or accuracy comparison |
| Source library and 90 locators | references/sirna_library/sources.json; references/vegfa_experiments_20261024/; research/2026-10-24_nearfull_complete/metadata_corrections/ | 12 materials / six papers; duplicate formats not independent papers; missing Kleinman supplement remains missing |
| Guard and three replay controls | sequence_validation.py; sequence_ui.js; scripts/replay_sequence_guard.py; research/2026-10-24_sequence_guard/replay_checks.json; replay/ | Deterministic replay only, no new API/scientific run; edited controls explicitly distinguished from the real original answer |
| Figure 1 | research/2026-10-24_nearfull_complete/figures/nearfull_complete.pdf; CAPTION_EN.md; source_data.tsv; font_verification.json | Actual full-scope descriptive plot, embedded Arial/Arial Bold; not a quality/superiority figure |
| References [1-3,5-6] metadata | research/2026-10-24_sequence_guard/manuscript/reference_metadata.json and listed original XML | Authors/DOIs checked against retained originals; publisher formatting may be adjusted later |
| Reference [4] reading scope | references/CRISPR-GPT/README.md; paper_extracted_text.txt; source_manifest.json | Extracted text available; original PDF binary/supplementary images not asserted acquired |

## Still absent

Independent human ratings; held-out scientific quality evaluation; user-project siRNA knockdown, delivery or N3-construct performance measurements; supplier-confirmed direction/end chemistry and quality information; final experimental target/measurement plan. Author affiliations/contributions/funding/conflicts and release permissions must be completed by the real authors.

No new full-pool ranking, model fine-tuning, state-risk reranking, HIF extension, ordering or wet experiment is implied by this draft.
