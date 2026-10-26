# Experiment v2 — hybrid retrieval and Qwen3 reranking

Date: 26 October 2026. Parent: [v1 baselines](../2026-10-26-v1-baselines/README.md).

Four encoders—MiniLM, Qwen3 Embedding 0.6B, EmbeddingGemma 2 and Jina v5 retrieval—received matched raw-title, qualified group-context and target-alias inputs. BM25, character TF-IDF and dense top-100 candidates were fused with reciprocal-rank fusion (constant 60).

Full retrieval covered 6,620 MASCO codes and 3,039 ESCO targets. Qwen3 reranking covered the same 330 review occupations for all four encoders, retaining 100 candidates per pool. The run scored 44,475 distinct pairs and saved 132,000 reranked rows. MLX used the pinned unquantized weights, checked prefix caching and requested bfloat16. Numerical backend differences are documented; near ties can change order.

The blinded top-10 union grew from 9,063 to 13,782 pairs (+4,719), across 20 registered method/input combinations. Reranking changed the first candidate for about half the sampled occupations. Average pairwise first-choice agreement rose from 76.4% to 99.1%. **Agreement is not accuracy.** No independent human judgments or accepted mappings exist.

## Files

- `figures/`: PNG and scalable SVG comparison plots.
- `metrics/`: aggregate counts, runtime, agreement, pool growth, structural audit and plotting inputs/provenance.
- `provenance/runs/`: original completed run metadata.
- `provenance/executed-source/`: relevant historical executed source and dependency snapshots.

The exact table input hashes refer to locally retained data files, which are not included. Original run source hashes refer to executed snapshots, while the portable implementation contains subsequent packaging adjustments.

## Interpretation limits

The review sample combines 30 calibration, 200 probability-test and 100 purposive challenge cases. Descriptive pooled statistics are not full-population estimates. MiniLM truncated 26 target documents; its shorter context capacity is part of the observed comparison. No method has been selected as the most accurate. Human calibration, independent review, adjudication and evaluated mapping releases remain future work.

These snapshots are immutable. A later run should use a new experiment ID and preserve this evidence.
