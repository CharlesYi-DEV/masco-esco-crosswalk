# Annotation guide, protocol draft 0.1

This is a proposed research protocol, ready for human calibration. No human annotation has occurred. The project is not an official crosswalk and has no official endorsement.

## Unit of judgment and source direction

Judge a **MASCO 2020 individual occupation → ESCO 1.2.1 occupation URI**. The unit is a pair, not a similarity score. Several ESCO occupations may collectively cover one MASCO occupation; record and judge each pair separately. Conversely, many MASCO occupations may map to one ESCO concept. Zero accepted pairs is valid.

Use the frozen MASCO PDF, the title evidence page in the inventory, the referenced parent context, and the frozen ESCO description/labels. A unit-group task list describes the group: it does not prove that every listed individual occupation performs every task. Preserve Malaysian institutional and professional distinctions. Similar numeric MASCO and ISCO prefixes do not prove common scope. Source spelling and odd titles are evidence to investigate, not permission to invent a correction.

## Six pair relations

| Label | Source-to-target meaning | Illustrative example (hypothetical, not an annotated pair) |
|---|---|---|
| `equivalent_scope` | MASCO and ESCO refer to substantially the same occupational scope, duties and boundaries, supported by evidence. | Both records describe the same kind of vehicle upholsterer with consistent scope. |
| `masco_narrower_than_esco` | All material MASCO scope fits inside ESCO, but ESCO also covers additional work. | A source occupation specifically repairs bus electrical systems; the target covers automotive electrical repair generally. |
| `masco_broader_than_esco` | ESCO is a specialization inside the wider MASCO occupation. | A source covers both marine and freshwater fish breeding; the target covers freshwater breeding only. |
| `close_overlap_without_containment` | Material occupational duties overlap, but each side includes scope absent from the other. | Two environment/safety roles share inspections, while one also covers public enforcement and the other workplace training. |
| `related_insufficient` | A connection exists, but evidence does not justify an accepted occupational mapping. | A worker and the manager of the same business sector share vocabulary but have different occupational functions. |
| `incorrect_candidate` | Evidence indicates an incompatible role or scope. | A clinical neurologist retrieved for a physics occupation through a misleading alternate label. |

The first four relations are eligible for acceptance **only after explicit human adjudication**. Equivalent names alone are insufficient for equivalent scope. If containment cannot be established, do not guess its direction. Do not mechanically convert `close_match`, `broader_proxy` or `partial_proxy` from the pilot.

## Occupation-level status

- `unresolved`: work is pending or reviewers disagree.
- `insufficient_evidence`: available source evidence cannot support a defensible scope judgment.
- `matched`: at least one accepted pair exists; this does not necessarily mean complete source-scope coverage.
- `no_suitable_match_found`: the search so far has not found one; record its limits.
- `reviewed_no_suitable_match`: two reviewers and adjudication have concluded, after a documented broader search of the frozen target corpus, that no suitable counterpart exists **within this version and protocol**.

The last status is not an absolute claim about all occupational systems. Keep `search_status` separate: `not_reviewed`, `shortlist_only`, `broader_search_incomplete`, or `documented_broader_search_reviewed`.

## Independent procedure

1. Coordinator allocates reviewer identities privately and distributes separate R1/R2 worksheet and decision copies. Do not share completed judgments before both lock their initial submissions. Record relevant occupational/domain experience in a reviewer register; public releases may use pseudonyms.
2. Review the 30 calibration occupations, discuss disagreements, refine this draft, and freeze a new guide version before the held-out study. Calibration labels must not enter test metrics.
3. Each reviewer reads MASCO evidence first, then the blinded candidate pool. Scores, methods, ranks, pilot labels and the other reviewer's answers are hidden. Pool display order is randomized with a recorded seed, not retrieval rank.
4. Judge every pooled pair for assigned occupations, add any suitable targets found outside the pool, and record evidence locations, rationale, timing, missing evidence, `decision_method` (normally `human_evidence_review`) and `guide_version` (initial draft `0.1`). Additional pair rows may use any URI in the frozen ESCO corpus.
5. Search beyond the shortlist using `python scripts/search_esco.py 'keywords' --all-terms`, alternate spellings, synonyms, the complete `esco_occupations.csv`, and relevant broader/narrower concepts. The archived ESCO ZIP also contains its hierarchy relations. A search with no hit is not a conclusion that no target exists. Log terms, paths, inspected alternatives, corpus version and stopping rationale.
6. Lock initial reviews. An adjudicator distinct from both reviewers resolves relation and inclusion disagreements using the evidence, including targets proposed by only one reviewer. Never silently replace the original decisions.
7. Run the acceptance gate against an explicit versioned adjudicated decision set. It checks identities/evidence and two independent submissions; it cannot verify that claimed human identities or independence are truthful. The coordinator must verify those facts. The AI must remain `reviewer_type=ai`, `review_stage=ai_proposal` if its proposals are retained at all.

`reference_completeness=partial_pool` is the default. Mark `exhaustive` only when the protocol's systematic search has produced a defensible complete set of acceptable counterparts for that source; document how all relevant target areas were inspected. A fully judged shortlist is still a partial reference.

## Particular cases to calibrate

Inspect vague titles (Officer, Executive, Assistant), short/odd source labels such as `Scratches`, grade-specific public-service roles, Malaysian traditional or religious roles, and military/civilian scope. The source inventory has 18 repeated title strings across distinct codes: identical wording must not collapse occupational identities. A strong model score can reflect lexical coincidence or a group description that is too broad for the individual title.

CSV identifiers must be imported as **text**, preserving `0111-01`, `01`, ESCO codes and URIs. Empty reviewer identity/date/relation fields are intentionally unfilled. Do not run review generation again over completed worksheets; the script refuses existing review files.
