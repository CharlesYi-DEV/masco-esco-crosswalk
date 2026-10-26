# Architecture

The study folder owns version-specific extraction and mapping logic. Its `scripts/common.py` resolves the local study root from `MASCO_ESCO_STUDY_ROOT`, or defaults to the study directory. This allows code to evolve while an existing data archive remains in place.

The data flow is:

`frozen sources → extraction and context → target import → candidate retrieval → reranking → blinded review → independent decisions → adjudication → accepted release`

`experiments/` contains compact snapshots for comparison: aggregate metrics, figure assets, run metadata and relevant source/dependency provenance. It does not hold the complete occupation inventory, raw candidate tables or reviewer decisions.

Original executed source snapshots are kept with their experiments. Portable scripts may differ from those snapshots through path handling, fresh-clone setup and removal of private-workspace checks. Recorded historical hashes refer to the archived executed files, not a claim that every current script is byte-identical to the original run.

`tests/` uses synthetic inputs and exercises ranking, pooling and human-acceptance contracts. It does not estimate real-world mapping accuracy. CI runs these tests and checks the integrity of published aggregate snapshots without downloading source documents or models.
