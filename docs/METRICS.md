# Metrics and Evaluation

SkillSense optimises **accuracy, abstention, token usage and latency together**.

## Retrieval quality

Collect labelled prompts with relevant skill IDs and no-skill cases. Compare names-only, source-only BM25, deterministic extraction and audited sidecar variants. Report Recall@1, Recall@3, Precision@1, Precision@3 and no-skill false-positive rate.

## Runtime

Track per-turn ranking p50/p95/p99, incremental RSS, hints emitted per 100 turns, token overhead and native discovery round trips. Do not include model audit compute in per-turn ranking numbers; report separately.

## Privacy

A mandatory zero-network test must exercise every normal hook. For audit, mock cloud/fallback/proxy/redirect endpoints and assert **no skill bytes leave the machine**.

## Data sources

Historical skill loads are imperfect weak labels. Use manually reviewed, held-out test sets, including ambiguous queries, misspellings, synonyms, no-skill tasks and duplicate skill names. Never publish private session content without consent.

## Targets

p95 under 5 ms at 500 skills; <10 MB incremental RAM; zero hot-path inference/network; max 3 hints and typically 0–60 extra tokens. These are **unmeasured targets** until published benchmarks exist.