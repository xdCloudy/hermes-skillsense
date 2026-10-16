# Retrieval and Performance Benchmark Plan

> No benchmark results have been published yet.

## Comparisons

- **A:** Existing names-only Hermes skill index/native discovery (baseline).
- **B:** BM25 over source-provided metadata.
- **C:** BM25 plus deterministic extracted metadata.
- **D:** BM25 plus reviewed AI-audited sidecar metadata.

Use identical skill catalogues and test prompts across comparisons; do not optimise and evaluate on the same held-out labels.

## Dataset

Create a consented or synthetic task set with manually verified relevant skill IDs, including:
- Direct keyword requests.
- Synonyms and jargon without obvious title overlap.
- Multi-skill and no-skill queries.
- Same-word/different-intent tasks.
- Weak, stale or contradictory frontmatter.
- Skills with identical display names from separate namespaces.
- Windows/Linux/macOS and eligibility restrictions.

Historical Hermes skill loads can be used as **weak labels only**; they do not establish the correct answer.

## Metrics

Measure Recall@1, Recall@3, Precision@1, Precision@3, no-skill false positive rate, incorrect hints, end-to-end task success, extra tool discovery round trips, injected tokens, p50/p95/p99 router latency, process RSS delta and index rebuild time.

Report warm vs cold cache, Python/Hermes version, OS/CPU, number of skills, prompt length and dataset composition. Separate runtime ranking cost from optional one-time auxiliary audit cost.

## Proposed performance targets

- p95 hot-path ranker below **5ms** on 500 skills.
- Incremental memory use below **10MB** for 500 skills.
- Zero model calls and network requests in the normal route.
- Added hint context typically **0–60 tokens**, with at most 3 names.

Treat these as **acceptance criteria**, never as benchmark results.

## Release gate

The router should meaningfully improve measured skill discovery without reducing end-to-end task reliability; otherwise retain the names-only native baseline. Publish scripts and aggregate results, not private user transcripts. Use explicit test splits and raw tabular data where permissible.