# Experiment v1 — initial baselines

Date: 26 October 2026. Six method/input combinations: character TF-IDF, MiniLM and weighted MiniLM adaptation, each using title-only and title-plus-context input. The run retrieved 10 candidates for each of 6,620 sources, producing 397,200 rows.

The original model used CPU float32. Runtime was 117.37 seconds across all six combinations; it is not directly comparable with the later per-encoder GPU runs. No independent reference labels or accepted mappings were produced.

`provenance/` preserves original run metadata, executed retrieval code and dependency versions. Full candidate files, source text and model weights remain local. This experiment is superseded for controlled encoder comparisons by [v2](../2026-10-26-v2-hybrid/README.md), while remaining a historical comparator.
