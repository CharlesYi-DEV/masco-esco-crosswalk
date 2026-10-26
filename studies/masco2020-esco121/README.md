# MASCO 2020 → ESCO v1.2.1 study

This folder contains the portable implementation. Raw data and full outputs are obtained or produced locally and are excluded from version control. Historical aggregate snapshots are under [`experiments/`](../../experiments/).

## Local setup

Run from the repository root. Python 3.14 was used for the later inference environment; baseline dependencies and executed source snapshots are retained with the baseline experiment.

```bash
python -m venv .venv-research
.venv-research/bin/python -m pip install -r requirements/inference.txt -r requirements/extraction.txt
.venv-research/bin/python studies/masco2020-esco121/scripts/acquire_sources.py --esco-zip /path/to/official-v1.2.1-en-csv.zip
.venv-research/bin/python studies/masco2020-esco121/scripts/acquire_models_v2.py
.venv-research/bin/python studies/masco2020-esco121/scripts/cache_pdf.py
.venv-research/bin/python studies/masco2020-esco121/scripts/extract_masco.py
.venv-research/bin/python studies/masco2020-esco121/scripts/prepare_esco.py
.venv-research/bin/python studies/masco2020-esco121/scripts/quality_checks.py
```

Acquire the official ESCO archive separately; its original archived download timestamp is unknown. Source recovery verifies hashes and refuses changed bytes. Model acquisition retrieves pinned snapshots and checks for real local files before treating a download as complete. MiniLM is restored to its baseline-compatible path. Downloads can be several gigabytes.

To reuse an existing local study archive without copying it, set `MASCO_ESCO_STUDY_ROOT` to that archive's absolute study directory before running the scripts. The default root is this study folder. This variable changes local data/output locations, not the uploaded aggregate evidence.

## Retrieval and review

```bash
.venv-research/bin/python studies/masco2020-esco121/scripts/retrieve.py --scope full --run-id baseline_new_001
.venv-research/bin/python studies/masco2020-esco121/scripts/hybrid_v2.py --encoder qwen_embedding --scope full --variants title_context --device cpu --dtype float32 --batch-size 16 --run-id hybrid_new_001
```

Repeat the controlled hybrid run with `minilm`, `gemma2` and `jina5_retrieval`, using distinct run IDs and the same input and device settings. The recorded October 2026 runs used MPS, requested bfloat16 and batch size 32; CPU float32 reproduction is supported but will differ in runtime and may differ numerically.

`prepare_review.py` creates an initial sample and empty reviewer files, and refuses to overwrite them. Its historical baseline input path is `outputs/full_20261026_k10/candidates.csv`: reproduce that run name in a fresh study or explicitly adapt the input path in a new protocol. Preserve the existing sample when comparing later methods.

`rerank_v2.py` accepts the new hybrid run IDs and `--scope review`. Use `--backend torch --device cpu --dtype float32` for portable inference. Apple hardware can use `--backend mlx --device mps --dtype bfloat16` after installing `requirements/apple.txt`. All methods must use the same backend and precision within a comparison.

Copy `configs/review_pool_v2.json`, replace run IDs and assign a fresh `review_version`. Run `expand_review_v2.py --config configs/YOUR_CONFIG.json` to create the new blinded union. Historical `audit_v2.py`, `run_alternatives_v2.py` and plotting helpers retain the registered v2 IDs; adapt these in a new experiment rather than silently reusing a completed run.

## Evaluation and acceptance

`evaluate.py` requires explicitly supplied independent human reference pairs and refuses empty reference files. Partial judgments are not exhaustive recall. `accept_mappings.py` requires independent human decisions and adjudication. Scores never automatically accept a mapping.

The source publication's counts conflict; read the extraction report before claiming completeness. Unit-group context is not an individual occupation description. The original baseline and newer controlled inputs differ in cleaning and alias exposure; report those differences.

The frozen v2 plotting helper verifies exact input hashes from `configs/plot_inputs_v2.json`. To regenerate it against an existing local archive, the hash configuration must also be available in that archive's `configs/` folder. New data requires a new plot-input configuration and experiment snapshot.
