# Contributing

Use a focused branch and a pull request for implementation changes. Describe the research question, changed assumptions, affected experiment IDs and validation performed. Keep title, context, alias and source-version changes explicit.

Run the lightweight test suite and snapshot verifier before submission. Tests use synthetic fixtures; never replace them with unpublished classification text or reviewer records.

Completed experiments are immutable. Add a new experiment directory and registry entry for a substantive iteration. Do not select models using held-out human labels. Do not overwrite completed reviewer work. See [iteration protocol](docs/iterations.md) and [data policy](docs/data-policy.md).

Preserve third-party attribution and source provenance. Similarity scores, model agreement and test execution must never be reported as human-validated mapping accuracy.
