# Methods review and proposed experiments

**Search cutoff:** 26 October 2026, Asia/Kuala_Lumpur. **Status:** research recommendations; no new model has been downloaded or run and no improvement on MASCO has been measured. This memo supplements the existing frozen baseline release without changing its candidates, reviewer sample, source manifest or accepted-mapping gate.

## Recommendation

Test a pipeline that combines **lexical and modern embedding retrieval, pairwise reranking, and a separate evidence-based scope-relation stage**. Keep MiniLM as a historical baseline. Test recent compact open-weight models before considering larger models or hosted APIs. The architecture change is at least as important a hypothesis as the model change: the current weighted similarity formula never jointly reads both occupation records or directly assesses containment.

“Better” must mean better independently judged retrieval, scope decisions and review efficiency. Higher cosine similarity, greater agreement with the pilot, more accepted-looking pairs, or a larger model do not establish improvement.

## Recent research: what transfers and what does not

| Primary source and date | Relevant contribution | Limit on applying it here |
|---|---|---|
| [Achananuparp & Lim, ICWSM, 25 May 2026](https://ojs.aaai.org/index.php/ICWSM/article/view/42622) | Taxonomy descriptions and grounded examples support inference, retrieval and reranking. | Its occupation task maps job records to O*NET-SOC. The published paper's §5 evaluation derives most reference labels from GPT-4o, with a small human check. Useful architecture evidence, not an independent accuracy standard for our crosswalk. |
| [AgentMap, preprint, 29 July 2026](https://arxiv.org/abs/2607.27130) | Combines candidate retrieval, hierarchy exploration and explicit equivalence/subsumption decisions. | Evaluated on biomedical/food ontologies, with constructed subsumption references and a single equivalent target or subsumer. It does not establish six-way, multi-target occupation mapping. Do not inherit its equivalence-first lexical override. |
| [Which Model, Which Prompt?, OM 2026; event 25 October, repository available 14 September](https://openaccess.city.ac.uk/id/eprint/38303/) | Studies model/prompt choices and mutual-subsumption prompts across five ontology-matching tracks. | The authors report configuration-dependent outcomes. Test prompts on development cases; neither repeated model agreement nor two prompts constitute independent human validation. |
| [He, *Matching granularity matters…*, 27 September 2026](https://link.springer.com/article/10.1007/s44163-026-02232-w) | Studies combining different text granularities and distinguishes retrieval errors from taxonomy-fit limitations. | The occupation improvement was not statistically significant. Its Ethiopian-vacancy sample and nearest-available reference labels differ from our task; materials are available on request. Treat context fusion as an ablation, not a proven gain. |
| [MELO, October 2024; highlighted by ESCO January 2025](https://arxiv.org/abs/2410.08319) | Public occupation-linking benchmark based on existing human annotations, across 48 datasets and 21 languages; includes national terminology/crosswalk sources. | Older but closer to our target domain than generic retrieval leaderboards. It supports external screening, not replacement of Malaysian human reference data. Its experiments also caution against assuming a domain-named encoder is strongest. |
| [SkiLLens, EACL Industry, March 2026](https://aclanthology.org/2026.eacl-industry.65/) | Encoder retrieval followed by decoder refinement and human involvement for ESCO linking. | The objects being linked are skills. Keep it as supporting architecture evidence and later skill-enrichment reading, not occupation-crosswalk validation. |

These are not directly comparable leaderboard results. Their target inventories, relation types, reference construction and sampling differ. Sources after the cutoff were excluded. This was a targeted literature review, not an exhaustive systematic review.

## Models worth benchmarking

| Candidate | Verified release information | Role in this study |
|---|---|---|
| `google/embeddinggemma-2` | [Google guide, 6 October 2026](https://developers.googleblog.com/embeddinggemma-2-the-developer-guide/): modular model, 270M text-only configuration, Apache-2.0. | Recent compact text-only challenger. Multimodal capability is unnecessary for already extracted occupation text. Requires a separate environment: guide specifies Sentence Transformers 6.1.0+, whereas our executed baseline used 5.7.0. |
| `jinaai/jina-embeddings-v5-text-small` | [Official model card](https://huggingface.co/jinaai/jina-embeddings-v5-text-small): 18 February 2026, 677M parameters, task-specific adapters, CC-BY-NC-4.0. | Strong recent research challenger. Test `retrieval` and `text-matching` configurations separately; pin the adapter and input instructions. Noncommercial terms require review before later commercial application. |
| `Qwen/Qwen3-Embedding-0.6B` + `Qwen/Qwen3-Reranker-0.6B` | [Qwen release, 5 June 2025](https://qwenlm.github.io/blog/qwen3-embedding/), [official reranker card](https://huggingface.co/Qwen/Qwen3-Reranker-0.6B): Apache-2.0; embedding and reranking families. | Reproducible local retrieval/reranking comparator. Start with the smaller variants; larger variants are optional resource ablations. Generic benchmark gains are not MASCO gains. |
| Cohere `rerank-v5.0-pro` / `rerank-v5.0-fast` | [Official release, 21 October 2026](https://docs.cohere.com/v2/changelog/rerank-v5): hosted rerankers with optional passage-span output. | Very recent optional external comparator. No API calls or data submission are authorized/executed by this review. Provider relevance calibration is not calibration for occupation equivalence or our six relations. |

Model release dates are not immutable checkpoint revisions. Before execution, record a specific revision, licence, tokenizer, prompt, adapter, precision and dependencies. Claims in model cards are provider-reported general benchmarks. Select the winner on independent occupation evidence, not release recency or model size. This shortlist is not a claim that no newer model exists.

## Proposed pipeline

### 1. Preserve several views of the evidence

Use the raw individual title, the existing cleaned title as a separate ablation, and a third view with explicitly labeled unit-group description/tasks. Keep official ESCO preferred/alternate labels and descriptions in separate fields. Never let removing a grade or institutional qualifier silently change the identity under study.

Encode alternate target labels as views of the **same URI**. Collapse duplicate label hits before fusion so concepts with many aliases do not receive extra votes merely for having more names. Compare matched-input configurations to isolate model improvements from extra label access.

Group context should remain auxiliary: sibling MASCO titles often share it. Test title-only, title plus unit description, and title plus individually selected **group-context** task evidence. Selected parent tasks remain parent evidence; they cannot be rewritten as proven individual duties. For unclear source titles, missing evidence should remain missing. Longer context windows do not justify filling them with unsupported material.

### 2. Retrieve broadly, then combine ranked lists

Add word BM25 alongside existing character TF-IDF and a newer dense retriever. Retrieve the top 100 from each channel, deduplicate by target URI, and combine ranks using reciprocal rank fusion (RRF), initially with a fixed rank constant of 60. This is an older established fusion technique, not a 2026 invention: [Cormack, Clarke & Buettcher, SIGIR 2009](https://doi.org/10.1145/1571941.1572114).

This avoids pretending different score scales are comparable or immediately learning weights from an unvalidated pilot. RRF still needs testing: it can reduce performance if weak or correlated channels dominate. Retain each channel's rank and score for diagnosis. Assess candidate Recall@50/100 before final top-10 ordering, wherever an exhaustive reference supports recall.

The target corpus has only 3,039 unique occupations. Exact dense scoring is feasible in principle and removes approximate-nearest-neighbor recall loss as a confound; there is no need to introduce a vector-database service merely for scale.

### 3. Rerank source–target pairs

Score each MASCO record jointly with each of the fused top 100 ESCO records using a reranker. The proposed starting comparator is Qwen3-Reranker-0.6B. Return a ranked list, not a mandatory winner. This adds a different interaction mechanism from independent-vector cosine similarity.

At full scale, top-100 reranking is **662,000 pair scores**; a 30-occupation development smoke test needs 3,000. These are workload counts, not timing or cost estimates. Measure latency and memory on the actual device before expanding. Reranking can improve ordering but cannot recover a target excluded from its candidate pool; report retrieval and reranking failures separately.

Remove exact-title score floors in one ablation. Retain exact-label evidence as a feature, but a homonym or wrong alternate label must not bypass scope assessment. A reranker's relevance score remains distinct from equivalence, confidence and acceptance.

### 4. Propose scope relations using source-grounded evidence

Use a structured second-stage assessor on the most plausible pairs. Ask separately whether the supplied evidence supports MASCO scope contained in ESCO scope, ESCO scope contained in MASCO scope, material overlap, or a conflict. Permit `unknown` for each evidence question. Then propose one of our six relations or defer to `insufficient_evidence`; do not mechanically infer containment from generic topical relevance.

Require actual source/target identifiers, evidence locations, which evidence is group-level, a concise rationale and any unsupported assumption. Validate cited text spans programmatically. Restrict output to existing ESCO URIs and allow zero or several proposals. A matching label cannot force equivalence. Missing an exact target must not force a broader proxy.

Use hierarchy **labels and documented parent relations** to inspect neighboring alternatives and inconsistent decisions. Keep a global retrieval channel so an incorrect branch does not exclude the correct target. Do not treat matching MASCO/ISCO digits as an alignment. LLM consensus, model-vs-model critique and reverse-direction checks are diagnostic signals only. All such records remain `ai_proposal`; the existing human acceptance gate stays in force.

AgentMap motivates explicit relation reasoning, but our extension needs its own validation: both containment directions, overlap, unknown evidence and many-to-many mappings are materially beyond its single-target formulation.

### 5. Learn only after independent labels exist

Later, test domain adaptation with human-judged hard negatives: same-sector but wrong-function roles, manager/worker distinctions, and plausible siblings. Use multi-positive objectives or masks for multiple acceptable counterparts; unjudged alternatives and broader/overlapping matches are not automatically negatives. Synthetic examples can be a labeled training experiment, never the independent test reference.

Prioritize human review of disagreement and ambiguity within the development partition. Keep the probability-test sample separate from active-learning selection. If abstention thresholds or probability calibration are introduced, fit them on dedicated development/calibration data and measure selective risk versus coverage on untouched test data. Do not attach a percentage confidence to raw cosine, reranker logits or self-reported LLM confidence.

## Minimal experiment ladder

| ID | Change from control | Main question |
|---|---|---|
| E0 | Existing six frozen runs | Historical comparison; no modification. |
| E1 | Raw versus cleaned titles; equal target-label access | Is preprocessing or input asymmetry responsible for differences? |
| E2a–c | EmbeddingGemma 2 text-only; Jina v5-small; Qwen3-0.6B | Does a modern encoder improve independently judged retrieval? |
| E3 | BM25 + char TF-IDF + selected E2 model, fused by RRF | Does the wider pool contain more acceptable counterparts? |
| E4 | E3 + Qwen3 pairwise reranking | Does joint scoring improve top-5/10 usefulness at the same pool coverage? |
| E5 | E4 + explicit relation/unknown-evidence assessor | Are relationship labels and deferrals better, independently of rank? |
| E6 | Optional supervised adaptation, after sufficient development labels | Does occupation-specific learning add value beyond the frozen pretrained pipeline? |

E2 models must use their documented prompts/adapters and a pinned checkpoint; do not sweep all variants on test labels. Change one factor at a time, retain multiple-candidate outputs and save all run provenance. Use an isolated environment for new dependencies. The accompanying JSON config is a proposed experiment specification, not an implemented runner.

## How to demonstrate improvement without changing the standard of evidence

- Use development data to choose models, prompts, pool depth, weights and thresholds. Freeze the chosen configurations before revealing held-out decisions. The 30 calibration occupations support procedure calibration, not a powered performance claim or broad hyperparameter search.
- Keep the existing 330-occupation sample and unit/title-component partitions. Audit semantic near-duplicates before supervised training. If the study needs a larger development/reference set, sample and document it without inspecting test labels.
- Create a **new versioned blinded candidate pool** containing outputs from every compared system. Reviewers must search beyond it. Preserve the original pool; evaluating new methods only against old top-10 judgments would favor the old systems.
- Use MELO for external screening with its own frozen source versions and human reference provenance. Resolve ESCO-version differences explicitly; do not treat its mappings as automatically valid in 1.2.1 or as Malaysian truth.
- Measure retrieval Recall@k only on sufficiently exhaustive references; use explicitly labeled partial-pool diagnostics elsewhere. Add independent accepted-pair precision, per-relation agreement/F1, unresolved rates, review time and unit-cluster uncertainty intervals. Report probability and challenge samples separately.
- Predeclare a primary outcome and a rule for selecting a model across the ablations. Make claims against paired, independently reviewed cases and report uncertainty. No paper's published improvement can be copied into our results.

**First implementation to prioritize:** a new immutable run with raw-title controls, BM25/character/dense rank fusion, and a small local reranker. Benchmark the two 2026 embedding challengers alongside Qwen3. Develop the scope assessor only against source-evidence examples and independent labels. No upgrade is designated a winner yet.
