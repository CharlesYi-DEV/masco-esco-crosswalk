# Data dictionary

CSV files serialize values as text. The logical types below describe intended interpretation; identifiers must always remain strings. Empty optional fields are missing/unfilled, not zero or negative findings. Source tables, candidates, decisions and accepted pairs are separate entities. See `schemas/crosswalk_contract.json` for enums, keys and cardinality.

An occurrence is evidence, not a distinct occupation. Repeated alphabetical entries and differing titles stay in occurrence tables. An alternate source title is not automatically a validated alias. Raw ESCO CSV and pilot tables retain upstream schemas unchanged; their original documentation and manifest remain alongside them.

## data/processed/masco_occupations.csv

| Field | Logical type | Meaning |
|---|---|---|
| `source_id` | string | Foreign key to source_manifest.json; names a frozen import, not a changing portal. |
| `source_version` | string | Edition/version string from the source manifest. |
| `source_sha256` | string | SHA-256 of the original source PDF/CSV, never of a translated or normalized substitute. |
| `code` | string | Source classification identifier; exact string, preserving leading zeros and printed hyphen. |
| `code_digits` | string | Six-character machine key with only the printed hyphen removed; leading zeros retained. |
| `parent_code` | string | Parent MASCO code; hierarchy membership within MASCO only, not an ISCO crosswalk. |
| `major_group` | string | First MASCO digit, including 0 for Armed Forces. |
| `title_original` | string | Source wording selected from the documented evidence; whitespace reconstructed, source spelling/case retained. |
| `title_evidence_section` | string | Where the selected title was found; may differ from the systematic identity row. |
| `title_pdf_page` | integer | 1-based physical page supporting selected title, including alphabetical fallback. |
| `title_y_top` | number | Title evidence top coordinate in PDF points. |
| `language` | string | Source language code: en for the English publication. Some proper names/section headings are Malaysian-language text. |
| `pdf_page` | integer | 1-based physical source PDF page for this occurrence/identity. |
| `printed_page` | string | Printed page label; systematic index page = physical page minus 14. |
| `y_top` | number | Top coordinate in PDF points (origin upper left) of the source row. |
| `individual_description` | string | Empty: no individual-level description asserted; group context is kept separately. |
| `individual_tasks` | string | Empty: parent tasks are not individual duties. |
| `context_code` | string | Join to masco_group_context.code; explicitly a parent group. |
| `context_scope` | string | major_group, sub_major_group, minor_group or unit_group; never silently individual. |
| `alphabetical_occurrences` | integer | Count of visible alphabetical rows for this code, not number of unique occupations. |
| `extraction_status` | string | machine_extracted_unreviewed; does not assert human validation. |

## data/processed/masco_groups.csv

| Field | Logical type | Meaning |
|---|---|---|
| `source_id` | string | Foreign key to source_manifest.json; names a frozen import, not a changing portal. |
| `source_version` | string | Edition/version string from the source manifest. |
| `source_sha256` | string | SHA-256 of the original source PDF/CSV, never of a translated or normalized substitute. |
| `code` | string | Source classification identifier; exact string, preserving leading zeros and printed hyphen. |
| `level` | string | major (1 digit), sub_major (2), minor (3), unit (4). |
| `parent_code` | string | Parent MASCO code; hierarchy membership within MASCO only, not an ISCO crosswalk. |
| `title_original` | string | Source wording selected from the documented evidence; whitespace reconstructed, source spelling/case retained. |
| `language` | string | Source language code: en for the English publication. Some proper names/section headings are Malaysian-language text. |
| `pdf_page` | integer | 1-based physical source PDF page for this occurrence/identity. |
| `y_top` | number | Top coordinate in PDF points (origin upper left) of the source row. |
| `title_evidence_section` | string | Where the selected title was found; may differ from the systematic identity row. |
| `context_available` | boolean | Whether an extracted narrative record exists; not a quality assurance claim. |
| `context_scope` | string | major_group, sub_major_group, minor_group or unit_group; never silently individual. |
| `review_status` | string | Machine/unreviewed state or explicit completed human decision state; never inferred from score. |

## data/processed/masco_group_context.csv

| Field | Logical type | Meaning |
|---|---|---|
| `code` | string | Source classification identifier; exact string, preserving leading zeros and printed hyphen. |
| `source_id` | string | Foreign key to source_manifest.json; names a frozen import, not a changing portal. |
| `source_sha256` | string | SHA-256 of the original source PDF/CSV, never of a translated or normalized substitute. |
| `context_scope` | string | major_group, sub_major_group, minor_group or unit_group; never silently individual. |
| `pdf_page_start` | integer | First physical page of context block. |
| `pdf_page_end` | integer | Last physical page represented in block. |
| `y_start` | number | Start-heading top coordinate. |
| `description` | string | Source description at the stated group/ESCO level; no generated paraphrase. |
| `tasks` | string | Source group task text; retained separately from description. |
| `inclusions` | string | Group examples/subgroup enumeration and inclusion-related text, not new individual inventory entries. |
| `exclusions` | string | Explicit exclusion/elsewhere-classified section where identified; blank does not prove none exist. |
| `other` | string | Other retained parsed section text, if any. |
| `raw_block` | string | Unsegmented visible block with physical page markers; consult when section parsing is uncertain. |
| `review_status` | string | Machine/unreviewed state or explicit completed human decision state; never inferred from score. |

## data/processed/masco_index_occurrences.csv

| Field | Logical type | Meaning |
|---|---|---|
| `source_id` | string | Foreign key to source_manifest.json; names a frozen import, not a changing portal. |
| `source_sha256` | string | SHA-256 of the original source PDF/CSV, never of a translated or normalized substitute. |
| `section` | string | systematic_index, alphabetical_index, narrative_heading or classification_list. |
| `code` | string | Source classification identifier; exact string, preserving leading zeros and printed hyphen. |
| `title_original` | string | Source wording selected from the documented evidence; whitespace reconstructed, source spelling/case retained. |
| `language` | string | Source language code: en for the English publication. Some proper names/section headings are Malaysian-language text. |
| `pdf_page` | integer | 1-based physical source PDF page for this occurrence/identity. |
| `printed_page` | string | Printed page label; systematic index page = physical page minus 14. |
| `y_top` | number | Top coordinate in PDF points (origin upper left) of the source row. |
| `masco2013_code_or_status` | string | Original comparison-column value; not an alternative 2020 identity. |

## data/processed/masco_heading_occurrences.csv

| Field | Logical type | Meaning |
|---|---|---|
| `source_id` | string | Foreign key to source_manifest.json; names a frozen import, not a changing portal. |
| `source_sha256` | string | SHA-256 of the original source PDF/CSV, never of a translated or normalized substitute. |
| `section` | string | systematic_index, alphabetical_index, narrative_heading or classification_list. |
| `code` | string | Source classification identifier; exact string, preserving leading zeros and printed hyphen. |
| `title_original` | string | Source wording selected from the documented evidence; whitespace reconstructed, source spelling/case retained. |
| `language` | string | Source language code: en for the English publication. Some proper names/section headings are Malaysian-language text. |
| `pdf_page` | integer | 1-based physical source PDF page for this occurrence/identity. |
| `printed_page` | string | Printed page label; systematic index page = physical page minus 14. |
| `y_top` | number | Top coordinate in PDF points (origin upper left) of the source row. |
| `masco2013_code_or_status` | string | Original comparison-column value; not an alternative 2020 identity. |

## data/processed/esco_occupations.csv

| Field | Logical type | Meaning |
|---|---|---|
| `source_id` | string | Foreign key to source_manifest.json; names a frozen import, not a changing portal. |
| `source_version` | string | Edition/version string from the source manifest. |
| `source_sha256` | string | SHA-256 of the original source PDF/CSV, never of a translated or normalized substitute. |
| `concept_uri` | string | Stable ESCO occupation URI; primary target identity within version. |
| `code` | string | Source classification identifier; exact string, preserving leading zeros and printed hyphen. |
| `title_original` | string | Source wording selected from the documented evidence; whitespace reconstructed, source spelling/case retained. |
| `alt_labels` | string | Official ESCO alternate labels separated by newlines; not reviewed MASCO aliases. |
| `description` | string | Source description at the stated group/ESCO level; no generated paraphrase. |
| `isco_group` | string | ESCO-provided ISCO grouping retained as metadata; not used to rank MASCO pairs. |
| `language` | string | Source language code: en for the English publication. Some proper names/section headings are Malaysian-language text. |
| `csv_record_number` | integer | Logical CSV record number including header as record 1; multiline records are not physical line numbers. |
| `modified_date` | string | Source ESCO modification timestamp used for explicit duplicate-URI selection. |

## outputs/full_20261026_k10/candidates.csv

| Field | Logical type | Meaning |
|---|---|---|
| `run_id` | string | Join to run.json for inputs, source/model hashes, parameters and runtime. |
| `method` | string | lexical_tfidf, minilm or weighted_minilm_adaptation. |
| `input_variant` | string | title or title_context; full actual input strings saved in query_inputs.csv. |
| `masco_version` | string | Fixed source edition string 2020. |
| `masco_code` | string | MASCO printed identifier; string including hyphen and leading zeros. |
| `esco_version` | string | Fixed target release string 1.2.1. |
| `esco_uri` | string | ESCO target URI; may be reviewer-added outside the shortlist. |
| `esco_code` | string | ESCO source code string, secondary to URI. |
| `rank` | integer | Genuine within-run, method, variant, MASCO-query rank; starts at 1. |
| `score` | number | Ranking similarity only, not probability, confidence or acceptance. Floating-point cosine can marginally exceed 1. |
| `score_type` | string | ranking_similarity_not_probability. |
| `title_cosine` | number | Normalized embedding dot product between cleaned source and preferred target titles. |
| `profile_cosine` | number | Profile embedding dot product; equals title cosine in title-only weighted adaptation. |
| `lexical_component` | number | Best normalized-label SequenceMatcher ratio used by weighted adaptation, not TF-IDF score. |
| `matched_label` | string | Target preferred/alternate label supplying weighted lexical evidence. |
| `label_boost` | string | Exact-label score floor applied by pilot adaptation, or none; not a semantic judgment. |
| `candidate_origin` | string | fresh_retrieval; no inherited pairs are appended. |
| `review_status` | string | Machine/unreviewed state or explicit completed human decision state; never inferred from score. |

## review/decisions.csv

| Field | Logical type | Meaning |
|---|---|---|
| `decision_id` | string | Unique immutable decision identifier assigned by review coordinator. |
| `masco_version` | string | Fixed source edition string 2020. |
| `masco_code` | string | MASCO printed identifier; string including hyphen and leading zeros. |
| `esco_version` | string | Fixed target release string 1.2.1. |
| `esco_uri` | string | ESCO target URI; may be reviewer-added outside the shortlist. |
| `relation` | string | One of six explicit source-to-target relations in crosswalk_contract.json. |
| `review_stage` | string | independent, adjudication or ai_proposal. |
| `decision_method` | string | Explicit evidence-review method; human_evidence_review or documented AI method, never inferred from model score. |
| `guide_version` | string | Version of annotation protocol used for this decision. |
| `reviewer_id` | string | Actual reviewer identifier/pseudonym; blank until human assignment. |
| `reviewer_type` | string | human or ai; AI cannot be an independent human reviewer. |
| `reviewed_at` | string | Reviewer-supplied timestamp with timezone. |
| `independence_attested` | string | Explicit true/false attestation of independent initial judgment. |
| `source_evidence` | string | Source version, PDF page/coordinate and supporting scope evidence; distinguish unit context. |
| `target_evidence` | string | Frozen ESCO URI/version/record and supporting description/label evidence. |
| `rationale` | string | Evidence-based explanation; no score-only rationale. |
| `search_beyond_shortlist` | string | Reviewer records whether broader target search was undertaken. |
| `search_terms_and_scope` | string | Search terms, inspected target areas, alternatives and stopping rationale. |
| `minutes_spent` | number | Observed human review effort in minutes, blank until measured. |
| `reference_completeness` | string | partial_pool by default; exhaustive only after justified systematic search. |
| `review_status` | string | Machine/unreviewed state or explicit completed human decision state; never inferred from score. |

## review/accepted_mappings.csv

| Field | Logical type | Meaning |
|---|---|---|
| `mapping_id` | string | Unique accepted-release pair identifier. |
| `masco_version` | string | Fixed source edition string 2020. |
| `masco_code` | string | MASCO printed identifier; string including hyphen and leading zeros. |
| `esco_version` | string | Fixed target release string 1.2.1. |
| `esco_uri` | string | ESCO target URI; may be reviewer-added outside the shortlist. |
| `relation` | string | One of six explicit source-to-target relations in crosswalk_contract.json. |
| `adjudication_decision_id` | string | Foreign key to explicit completed human adjudication. |
| `supporting_decision_ids` | string | JSON array of independent human decision IDs. |
| `source_evidence` | string | Source version, PDF page/coordinate and supporting scope evidence; distinguish unit context. |
| `target_evidence` | string | Frozen ESCO URI/version/record and supporting description/label evidence. |
| `rationale` | string | Evidence-based explanation; no score-only rationale. |
| `accepted_by` | string | Actual adjudicator identity; never the AI. |
| `accepted_at` | string | Adjudication timestamp. |
| `status` | string | For mappings: human_adjudicated. For occupation status: unresolved/matched/insufficient_evidence/no_suitable_match_found/reviewed_no_suitable_match. |

## review/occupation_status.csv

| Field | Logical type | Meaning |
|---|---|---|
| `masco_version` | string | Fixed source edition string 2020. |
| `masco_code` | string | MASCO printed identifier; string including hyphen and leading zeros. |
| `status` | string | For mappings: human_adjudicated. For occupation status: unresolved/matched/insufficient_evidence/no_suitable_match_found/reviewed_no_suitable_match. |
| `search_status` | string | Separate search-progress state; no match found is not a reviewed absence conclusion. |
| `reviewer_id` | string | Actual reviewer identifier/pseudonym; blank until human assignment. |
| `reviewer_type` | string | human or ai; AI cannot be an independent human reviewer. |
| `reviewed_at` | string | Reviewer-supplied timestamp with timezone. |
| `evidence` | string | Supporting provenance for status or change event; not generated confidence. |
| `rationale` | string | Evidence-based explanation; no score-only rationale. |

## review/sample.csv

| Field | Logical type | Meaning |
|---|---|---|
| `masco_code` | string | MASCO printed identifier; string including hyphen and leading zeros. |
| `major_group` | string | First MASCO digit, including 0 for Armed Forces. |
| `unit_code` | string | Four-digit MASCO parent grouping, as text. |
| `title` | string | Human-readable source label; does not replace code identity. |
| `cohort` | string | calibration, probability_test or challenge_test; challenge results are not population estimates. |
| `partition` | string | development or held_out; entire units and identical-normalized-title components stay together. |
| `eligible_major_population` | integer | Eligible occupation count within that major group and fixed partition. |
| `inclusion_probability_conditional_on_partition` | number | Probability sample inclusion rate; blank for purposive/calibration samples. Not a full-population first-stage weight. |
| `challenge_flags` | string | Heuristic selection reasons, not validated characteristics. |
| `source_pdf_page` | integer | Physical identity-row source page. |
| `title_pdf_page` | integer | 1-based physical page supporting selected title, including alphabetical fallback. |
| `unit_context_pdf_page` | integer | First physical page of parent group narrative. |

## review/reference_pairs.csv

| Field | Logical type | Meaning |
|---|---|---|
| `masco_code` | string | MASCO printed identifier; string including hyphen and leading zeros. |
| `esco_uri` | string | ESCO target URI; may be reviewer-added outside the shortlist. |
| `relation` | string | One of six explicit source-to-target relations in crosswalk_contract.json. |
| `acceptable` | string | Human-adjudicated true/false pair inclusion in a reference set. |
| `reference_completeness` | string | partial_pool by default; exhaustive only after justified systematic search. |
| `independent_human_reference` | string | Explicit provenance declaration; inherited/AI labels cannot be set true. |
| `adjudication_id` | string | Reference decision provenance; required by evaluator. |

## Supporting outputs

`query_inputs.csv` retains original/cleaned titles, full constructed profiles, parent context location, source hash, tokenizer counts and truncation flags. `count_reconciliation.csv` records extracted versus published counts for every major group/level. `extraction_queue.csv` gives issue type, code, evidence, detail and unreviewed status. `repeated_titles.csv` and `code_sequence_gaps.csv` identify non-unique wording and missing numeric suffixes without inventing identities. `esco_duplicate_records.csv` retains original conflicting rows as JSON, source modification date and selection flags. `pilot_comparison.csv` keeps prior assignments outside fresh retrieval; its optional rank is populated only for actual fresh top-10 presence.

`run.json` is the reproducibility record for each immutable candidate output. `source_manifest.json` is the publisher/version/acquisition/checksum/reuse record. `review/title_split_audit.csv` audits identical title strings across development and held-out partitions. Reviewer worksheets contain prospective blank fields, not completed annotations. No outputs contain official confidence scores or externally validated labels.
