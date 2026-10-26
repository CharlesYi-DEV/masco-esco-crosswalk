# Iteration protocol

1. State the research question and freeze the intended comparison before looking at held-out human labels.
2. Copy `experiments/TEMPLATE/` to a new directory, for example `YYYY-MM-DD-v3-description`.
3. Record parent experiment, source versions and hashes, model revisions, input construction, prompts, precision, device, candidate depth, fusion settings and review sample/split hashes.
4. Use new run IDs and a new review version. Preserve earlier completed runs, candidate pools and decisions.
5. Run synthetic tests first, then a technical smoke run. Full inference is a deliberate local step, not a CI job.
6. For every added method, expand the blinded pool at the same depth for every sampled occupation. Keep scores and method provenance separate from reviewer exports.
7. Evaluate only against independent human references. An incompletely judged pool supports limited diagnostics, not exhaustive recall or no-match claims.
8. Export compact aggregate metrics and figures after checking their interpretation. Keep raw tables and source text in excluded local storage.
9. Add the experiment to `experiments/index.json`, update the changelog, then regenerate `experiments/SHA256SUMS` with `python scripts/verify_snapshot.py --write`.
10. Use a version tag for a documented repository milestone. Correct a published experiment through a new snapshot and a supersession note, rather than silently replacing its evidence.

The current primary experimental method is Qwen embedding hybrid retrieval followed by Qwen3 reranking. The other encoders remain controlled alternatives; no winner has been established through independent labels.
