# Evaluation plan — proposed, no performance estimates yet

## Questions and comparisons

Compare lexical character TF-IDF, pretrained MiniLM cosine retrieval and the weighted MiniLM adaptation. Each has cleaned-title-only and title-plus-publication-unit-context variants. Report the effect of context separately from retrieval algorithm. ESCO alternate labels are used by lexical retrieval and the weighted lexical component; MiniLM embeds preferred names. This asymmetry is deliberate and must be disclosed. A future controlled ablation should hold target-label inputs constant.

The weighted run preserves the pilot's .65/.20/.15 components, title cleaning, label floors and shortlist construction, while replacing inherited portal profiles with explicitly qualified publication context and removing inherited-pair injection. It is an adaptation, not an exact historical replay. Preserve the archived pilot output separately; compare agreement with it descriptively, never as accuracy.

## Sampling already prepared

`review/sample.csv` contains 330 distinct occupations: 30 calibration, 200 probability-test and 100 challenge-test cases, with every major group represented. A seed of 20261026 partitions entire MASCO unit groups and connected components of identical normalized titles into development and held-out sets. Of 1,000 seeded feasible component assignments, the assignment closest to 20% development units per major group is selected; every major group retains at least three development and thirty held-out occupations. This is a conditional fixed partition, not a simple random first-stage sample. Shared-title grouping is a leakage precaution, not a semantic-equivalence claim. Three occupations per major group are sampled for calibration. Twenty per major group are sampled uniformly from the held-out population; ten additional challenge cases per major group are selected by documented heuristics (short/ambiguous wording, short group descriptions, grades or national/institutional scope).

The probability-test inclusion probability is recorded **conditional on the fixed unit partition**. Report design-weighted results for that held-out population and macro averages by major group. Do not claim these conditional weights estimate the entire 6,620-role population without accounting for the first-stage unit selection. Challenge cases are purposive: report them separately, without population-prevalence claims. The 9,063 pooled pairs are an initial workload, not a final reference set; both reviewers can add targets outside the pool.

This is an initial feasible design, not a power calculation. Use calibration time and disagreement rates to estimate cost and required sample size before final preregistration. Do not inspect held-out labels while making that decision. Technical smoke tests contain no human labels and are not accuracy tests.

## Metrics and denominators

| Outcome | Definition and valid denominator |
|---|---|
| Candidate Recall@k | For an exhaustively referenced source, acceptable gold targets retrieved in top k / all acceptable gold targets; report macro and micro variants at k=1,5,10. Sources with zero gold targets are excluded from recall and reported separately. |
| Partial-pool diagnostic | Judged-positive hit rate and judgment coverage only. Missing/unjudged pairs are unknown, not false. Do not label this Recall@k or full precision. |
| Accepted-pair precision | Correct accepted pairs / audited accepted pairs, using an independent human audit of a stratified probability sample from the frozen accepted release. Auditors must not merely repeat the decisions that accepted those pairs. Report pair-selection probabilities and binomial/design-aware intervals. |
| Relation agreement | Exact pre-adjudication agreement and nominal Cohen's kappa for six relations, with confusion matrix, per-class counts and prevalence. Do not impose ordinal weights: the labels have no natural linear order. Report missing judgments and reviewer-added candidates separately. |
| Coverage | Distinct MASCO sources with ≥1 accepted pair / all 6,620 source codes; also by major group and relation. Distinguish accepted target coverage from full source-scope coverage. |
| Unresolved/unmatched | Counts and denominators for unresolved, insufficient evidence, searched-but-none-found and reviewed-no-suitable-match; do not merge these categories. |
| Effort and errors | Minutes per occupation/pair, extra-search time, targets added outside pools, adjudication rate, index-evidence conflicts, broad-context errors, homonyms, title cleaning/grade loss, cultural or institutional mismatches, and containment-direction errors. |

Use unit-group cluster bootstrap intervals where appropriate because occupations sharing descriptions are correlated. Stratify reporting by major group; predeclare rare-class handling and exact metric definitions. For pooled evaluation, record which methods contributed to the pool, randomize presentation, audit some low-ranked/outside-pool targets, and estimate/report pooling bias. Do not infer full target absence from an incomplete pool.

## Leakage controls

Freeze source hashes, model revision, inputs, parameters, candidate files and sampling seed before test annotation. No fitting of vocabulary on MASCO queries: TF-IDF is fitted only on the target ESCO corpus. This is unsupervised retrieval; no labels were used in baseline generation. If weights, thresholds, prompts, cleaning or a supervised model are later tuned, use development units only. Keep title aliases/near duplicates and all occupations sharing a unit description out of opposing supervised train/test partitions; audit cross-unit title duplicates before any training. ESCO semantic near-neighbor leakage also requires a family-level audit for supervised work.

Pilot decisions and AI proposals cannot become independent human ground truth. Reviewers should be blind to them. Independent human reference collection remains necessary even if a retrieved pair matches the inherited assignment.

## Executable support and remaining work

`evaluate.py` supports macro Recall@k for explicitly exhaustive human references and labeled partial-pool diagnostics. It deliberately refuses the currently empty reference template. It is an unweighted diagnostic implementation; design weighting, cluster intervals, independent accepted-pair audit analysis and agreement reporting remain to be implemented after the protocol is calibrated. Do not publish its raw unweighted values as final study estimates.

`reference_pairs.csv`, `precision_audit.csv` and separate R1/R2 decision files are empty templates. No Recall@k, precision, agreement, accuracy or validated coverage has been measured. The only observed results so far are extraction consistency and retrieval execution/structure.

## Later skill enrichment

Freeze and evaluate the occupation crosswalk first. For later skill transfer, define a separate annotation unit (MASCO occupation, ESCO skill, proposed transfer), especially for broader or overlapping mappings. Preserve ESCO essential/optional labels and source version. The pilot's 100/50 numbers are project weights, not official importance values. Do not transfer every target skill simply because an occupational pair was accepted.
