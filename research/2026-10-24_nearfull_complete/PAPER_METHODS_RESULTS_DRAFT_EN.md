# siRNA-GPT: Methods and Results working draft

Draft for scientific review, not a validated efficacy or comparative-accuracy report. Numerical completion statements for the new near-full scan and the purchased-sequence Agent case must agree with the final receipts linked below. No new wet-laboratory experiment or independent human rating was performed in this batch.

## Methods

### System and evidence boundaries

siRNA-GPT is a single-owner Python web application that combines a configured language-model API with six scientific tools: candidate inspection, target-reference verification, efficacy-score retrieval or execution, seed-match retrieval or execution, baseline-expression annotation, and report compilation. Automatic mode uses model-based planning and iterative tool calls after the existing user-facing plan-confirmation step. Guided mode uses a predefined dependency path. The fixed-workflow comparator applies a predefined tool path without model-based planning or interpretation. These differences in prior path selection and iterative model use are retained in reporting and do not themselves demonstrate scientific superiority. No model fine-tuning or state-dependent risk reranking was undertaken.

Hosted scoring and seed operations import explicitly versioned local outputs; they are not newly executed heavy computations on the free web server. Source candidates, results and evidence versions are checked before reuse. The purchased-sequence dataset is separate from the historical nine-candidate dataset. Raw answers, failures and earlier development batches are retained unchanged; appended explanations do not replace historical answers.

### Candidate source and fixed target references

The revised candidate pool was obtained from the same retained siDirect 2.0 request and its 104 original output rows. Original Ui-Tei and duplex seed melting-temperature settings were retained, including the original 21.5°C printed boundary annotation. A candidate entered the 65-design reporting pool when both strands had a reported minimum non-target mismatch count of at least two in the original siDirect g2–g20 fields. The historical siDirect database release is unavailable. Consequently, those fields are historical design annotations, not substitutes for checks against the fixed local reference.

Unlike the older nine-candidate working pool, the 65-design reporting pool did not discard candidates solely for core GC content outside 30–65%, any homopolymer of four bases, or incomplete coverage of all 20 retained VEGFA transcript references. These properties and official OligoFormer sequence flags were reported explicitly. The official OligoFormer implementation does include a GC-content flag at 30–65%; the absence of a pool-level GC exclusion must not be described as absence of any official GC rule. Pool inclusion is distinct from suitability for an experiment.

NM_003376.6 was the computational demonstration transcript. Exact matches of the 19-nt paired core were reported separately across the 20 fixed VEGFA references. Coordinates refer to a 1-based closed 19-nt core interval; original siDirect 23-nt design-window coordinates are separate fields. Transcript-reference coverage is not a measured proportion of VEGFA suppression or isoform abundance.

### Local OligoFormer and seed calculations

Previously completed local inference covered all 65 designs and the purchased duplex as a separate entry. The pinned OligoFormer implementation and retained weights were used through the documented CPU adaptation, with an explicit 19-nt guide core and 57-nt target context. Raw class-1 outputs, the official 1.341 score scaling and func_filter annotations were retained. These scores have not been calibrated to knockdown measurements in this project; scores above one are not percentages. No inference was repeated for the near-full follow-up.

SeedMatchR 1.1.1, with Biostrings 2.70.1 under R 4.3.1, was previously executed for both strands of all 66 entries using mer7m8, zero mismatches and no indels. The fixed reference contained one representative annotated 3′ UTR for each of 19,415 genes. All 132 strand units retained counts including zero rows (2,562,780 rows in total), together with site-level results. Site counts, deduplicated matched-gene counts, expression-mapped genes and state-detected genes are distinct quantities. The VEGFA target gene (Entrez 7422) is excluded from non-target summaries. This is sequence-based seed matching, not experimental off-target validation.

### Completion of the fixed near-full query plan

The original plan contained 264 unique queries: 66 entries × two strands × two 19-nt windows. Each strand was checked using its paired-core positions 1–19 and original 21-nt sequence positions 2–20. The second window follows the siDirect near-full definition; the first is a project consistency check. The windows overlap by 18 bases and are not independent algorithms or experiments.

Queries were reverse-complemented to target patterns and searched against the same fixed 186,185-transcript RNA reference using Biostrings vmatchPattern, max.mismatch=2, with.indels=FALSE and fixed=TRUE. Actual mismatch counts and 1-based transcript positions were retained. One raw match extended one base beyond the reference end; it was preserved, labelled as an 18-base boundary overlap and checked with the installed official neditStartingAt function. A separate full-window-only summary excludes this boundary overlap without altering raw output; all 0/1-mismatch findings are unaffected. Transcript-to-gene mapping preserved all mapped gene identifiers and explicitly labelled unknown mappings. Cumulative site and non-target-gene summaries were generated for at most zero, one and two mismatches. Unknown mapping was not treated as absence of expression.

The first batch completed 24 queries covering the five coding-region designs and purchased entry; its 15-minute budget was an operational limit, not a biological exclusion. The follow-up derived the exact 240-query difference from the 264-item plan and those 24 completed keys. The older 256-item intermediate list was not rerun because 16 of its entries had subsequently been completed. New raw results, commands, reference fingerprints, loaded package versions, start/end times, exit status and zero-hit states were retained in a separate directory. The final merge independently rechecked stored sites, mismatch counts, reference order, gene mappings and cumulative summaries. Full plan coverage is claimed only in the final completion audit, not from an intermediate checkpoint.

### Purchased duplex and baseline expression

The user-provided original synthesis document records row 1 as `GAUAGAGCAAGACAAGAAATT-N3` with an azide note and row 2 as `UUUCUUGUCUUGCUCUAUCTT`. Both original strings and modification notes were retained. Assuming both rows are written 5′ to 3′, their first 19 bases are complementary and row 2 is the putative guide. These roles are derived, not supplier-confirmed. The literal TT characters were not silently interpreted as dTdT or converted into an asserted chemical specification. The exact N3 attachment and complete assembled construct were not simulated.

The putative guide was bound to NM_003376.6 positions 1439–1457, its 57-nt context, the fixed-reference fingerprint and the original computation records before import into the six-tool workflow. Changed sequences, original-chain fields, coordinates or reference versions stop reuse. The server retains imported evidence with the exported report, including both-strand seed and near-full data. The baseline expression join uses guide seed hits; passenger results remain separately labelled supplementary evidence.

Expression data derive from eight baseline ARPE-19 culture dishes from one culture batch, four normoxic and four exposed to 1% O₂ for 24 h. They are not four independent culture rounds and were not automatically paired by sample number. A gene was labelled detected within a condition when TPM was at least one in at least two of its four dishes. TPM is descriptive baseline context, not siRNA-perturbation evidence and not a score or risk weight.

### Literature retrieval and development records

The scoped library contains 12 source materials representing three tool papers, three experimental papers, official documentation/source excerpts and a project record. Multiple formats of the same paper are not counted as independent papers. Chinese queries retrieve English source passages using the existing lightweight index; generated citations must correspond to retrieved text with a page or text-fragment locator. Project settings, local calculation records and literature findings remain separate source types. Five abstract XPath metadata errors were corrected and all 90 Chen/Osipova block locators were verified against unchanged XML text. The Kleinman material is the acquired 15-page author manuscript; its unavailable supplementary sequence table is not reconstructed.

Earlier 6-task × 3-arm × 3-repeat development records (54 planned units) and failed answers remain historical evidence for their respective code versions. Repeats are technical repetitions rather than independent questions. Independent human quality scores remain unfilled; software/tool completion cannot be used as scientific accuracy. The new literature feature and purchased case are not retroactively added to that old batch. The previously completed day-7 missing-measurement question is a separate real library regression, not an experimental knockdown measurement.

## Results

### Complete pool and offline evidence

The unchanged reporting rule retained 65 of the original 104 designs: five coding-region designs, nine 5′-UTR/boundary designs and 51 3′-UTR designs. The historical nine are a subset. All 66 model predictions and all 132 strand-level seed computations were completed previously; the follow-up did not recalculate them. Recomputed historical-control scores and flags matched the older nine, and their 14,524 positive guide-seed gene-count rows matched the older import.

The follow-up completed the remaining 240 unique queries in 1,640.096 s (27 min 20.096 s), with exit code zero. Together with the original 24, all 264 queries were covered: 246 had raw hits and 18 had zero hits, with no failures or unrun units. All 7,480 stored raw site rows and cumulative summaries were checked; 7,479 intervals lie fully within the transcript reference, while one boundary overlap is reported separately. At least one mapped non-target hit with zero or one mismatch occurred in one or more queries for 23 of 65 designs, including 21 newly examined designs; no unknown-mapping hits were found. The other 42 designs are not thereby established as safe. Full tables, query states, raw results and derived full-window-only summaries are retained in `RESULTS_TABLES.md` and accompanying data. No new pool rule or best-of-65 ranking was inferred.

### Purchased-sequence evidence and real Agent case

The purchased core matched 18 of the 20 fixed VEGFA references. Its raw class-1 score was 0.8366401195526123 and scaled score was 1.121934400320053, with official flag zero. Guide seed results contained 3,540 sites in 2,840 genes including VEGFA, or 3,539 sites in 2,839 non-target genes. Passenger results contained 1,402 sites in 1,286 non-target genes. Across all four near-full queries, there were no mapped non-target or unknown-mapping hits at zero or one mismatch; the at-most-two-mismatch non-target gene counts were 1, 3, 3 and 3 for guide core, guide g2–g20, passenger core and passenger g2–g20, respectively. These are properties of the retained references, not evidence of experimental specificity or conjugate performance.

One real automatic-mode case (20261024_121627_1e50c9, deployed code 03092ef) completed all six tools after the existing plan-confirmation step. One planning request and seven execution requests consumed 39,048 tokens (37,760 input and 1,288 output); all eight responses were completed without an incomplete reason. The 57-file original tool export and planning exchange were retained, and 29 deployed asset hashes matched the corresponding Git blobs. However, the generated final answer incorrectly transcribed the 19-nt passenger core as a 24-nt string. The verified input and structured computation records retained the correct 19-nt sequence. The incorrect answer was preserved and a separate evidence-based correction was added without rerunning the case. Workflow completion therefore must not be interpreted as an error-free answer or scientific accuracy. These records and the correction are in `live/`.

### Candidate discussion and missing validation

1157 and 1555 remain provisional alternatives from the earlier coding-region subgroup, with 20/20 and 14/20 reference coverage, respectively. They are not designated the best candidates among all 65 designs. In particular, the six references not matched by 1555 cannot be assumed irrelevant or unexpressed. The purchased entry provides an authentic user-sequence case with its own evidence version, rather than borrowing a legacy candidate score. Final experimental target scope, supplier-confirmed strand/end chemistry and a laboratory plan remain decisions for the user and scientific review.

No new knockdown measurement, delivery assessment, N3-conjugate assay, independent human score, held-out scientific-accuracy estimate or superiority result was obtained. This work supports a traceable computational assistance prototype within a fixed VEGFA/ARPE-19 scope.

## Figure-caption update

The prior candidate-v2 figure remains an unchanged historical description of all 65 designs plus the separate purchased entry, showing model scores and seed-match annotations. Its original caption accurately described the then-partial 24-query near-full scope. For a revised manuscript caption: “Model outputs and representative-UTR seed counts are descriptive computational annotations, not experimental efficacy or safety measures. The separate near-full follow-up completed the original 264-query plan using the same fixed reference; full results and potential matches are provided in the accompanying complete tables. The previous coding-region discussion candidates are not a validated best-of-65 set.” The completion audit has passed. English figure text uses actual Arial/Arial Bold; no comparative-quality figure is supported before independent scoring.

## Primary sources and reproducibility entry points

- siDirect 2.0: https://doi.org/10.1186/1471-2105-10-392 ; official settings: https://sidirect2.rnai.jp/v2.0/doc/
- OligoFormer: https://doi.org/10.1093/bioinformatics/btae577 ; pinned implementation commit e2f53ad63387bbe166bf123949151e2bc9bf6ec3.
- SeedMatchR: https://doi.org/10.1093/bioinformatics/btae011 ; retained official package 1.1.1.
- Experimental materials: https://doi.org/10.2147/IJN.S39622 ; https://doi.org/10.3390/pharmaceutics12010039 ; https://doi.org/10.1038/nature06765 . These authors' experiments are not this project's experimental results.
- Exact local/remote asset, computation and delivery records: this directory, `../2026-10-24_candidate_v2/`, `../../data/purchased_sivegf_20261024_v1/`, and `../../references/vegfa_experiments_20261024/`.
