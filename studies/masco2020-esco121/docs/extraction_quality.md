# Extraction quality report — 26 October 2026

Status: the complete visible systematic index was machine-extracted; completeness against authorial intent and semantic correctness remain unvalidated. The immutable primary PDF contains 602 physical pages. All page references below are 1-based physical PDF pages, with printed pages separately recorded.

## Observed inventory

| Level | Extracted unique | Publication statistics table (p.11) |
|---|---:|---:|
| Major | 10 | 10 |
| Sub-major | 51 | 51 |
| Minor | 148 | 147 |
| Unit | 492 | 490 |
| Individual occupation codes | 6,620 | 6,630 title entries |

The paragraph below the statistics table instead states 146 minor groups and 6,366 individual entries. These internally inconsistent figures cannot all be used as extraction acceptance targets. The extraction therefore preserves visible coded entries and reports differences rather than manufacturing rows to reach a published total.

The 6,620 systematic rows have distinct codes; they contain 6,602 distinct exact title strings. Eighteen repeated title strings belong to different codes and were not collapsed. The alphabetical index contributes 6,545 rows for 6,544 unique codes, all already in the systematic index. Its duplicate occurrence is retained as evidence, not counted as a new occupation. Seventy-six systematic codes have no matching parsed visible alphabetical entry. This is a source/index coverage discrepancy to inspect, not proof those occupations are invalid.

## Counts that differ by major group

| Major | Level | Extracted | Table | Difference |
|---|---|---:|---:|---:|
| 0 | minor | 7 | 6 | 1 |
| 1 | unit | 39 | 38 | 1 |
| 1 | occupation | 547 | 551 | -4 |
| 3 | occupation | 1207 | 1211 | -4 |
| 4 | occupation | 370 | 372 | -2 |
| 5 | occupation | 318 | 317 | 1 |
| 7 | occupation | 670 | 672 | -2 |
| 8 | unit | 43 | 42 | 1 |
| 8 | occupation | 714 | 713 | 1 |

For hierarchy counts, the extracted chapter lists and index visibly enumerate the additional groups (seven military minor groups; 39 manager units; 43 plant/machine operator units). Whether the table reflects editorial omissions or an earlier revision is unresolved. The ten-entry net occupation difference is distributed across major groups; it is not explained by removing aliases. Three code-sequence gaps, all in unit 1412, are listed for inspection; gaps alone do not establish missing occupations. Do not assume the remaining difference is a parsing failure or a publication error without review.

## Extraction method and evidence

`cache_pdf.py` reads all PDF pages, excludes glyphs whose origins are outside the visible page or rotated, and deduplicates identical glyphs at coordinates rounded to 0.1 point. This is necessary because the publication contains off-page duplicate text and overprinted headings. It records page rows and coordinates in JSONL. `extract_masco.py` uses section-specific columns on systematic pp.316–445 and alphabetical pp.448–561, preserving the 2020 code and the separate 2013 code/status. It extracts chapter hierarchy headings and explicit narrative blocks across pp.15–314; major-group descriptions use documented chapter-opening pages.

All 701 hierarchy nodes have a context record. All 492 unit records contain parsed descriptions and tasks. Individual occupation descriptions/tasks remain blank; the link to a parent unit is explicitly `context_scope=unit_group`. Group blocks retain raw text and page markers, including examples/inclusions/exclusions and other content where present. English publication wording is preserved, including the Malay task heading “Tugas merangkumi” in unit 8182, which is recognized as a section marker. Structural checks confirm presence, not perfect section parsing.

Two titles absent from extracted systematic text (`2132-15`, `2915-01`) use the unique alphabetical-index wording with separate title page/coordinate provenance. The assistant visually inspected systematic pp.330 and 367 and saw corresponding rendered titles; this was not independent human validation. Systematic row evidence remains unchanged. Page 316 was also visually inspected to verify column layout.

## Review queue

- wrapped_title: 4
- group_title_variants: 59
- index_title_disagreement: 26
- missing_alphabetical_code: 76
- systematic_title_text_missing: 2

These are 167 issue rows, not necessarily distinct occupations. Source-title variants are not automatically accepted aliases. Raw index and heading occurrences retain all alternatives. Group spelling differences, wrapped labels and source errors need manual assessment. The original PDF is retained for evidence that text extraction may miss.

## Checks executed

Twelve structural checks passed: unique valid codes, 145 preserved leading-zero military codes, all major groups, nonblank selected titles, valid parents, complete context-node joins, separation of individual and group evidence, unit descriptions/tasks present, independent visible-row code scan agreement, matching source checksums, and correct handling of “not classified elsewhere” as description rather than exclusion.

The earlier workspace extraction independently contains the identical 6,620-code set; the comparison and checksum are recorded in `outputs/structural_checks.json`. This establishes code-set consistency between implementations, not source accuracy or human validation. A frozen-source hash check and twelve research-contract tests also passed. No occupational mapping has been independently validated.
