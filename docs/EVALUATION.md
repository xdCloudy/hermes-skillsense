# SkillSense selection evaluation

## Purpose and limitations

`python tools/evaluate.py` compares three **deterministic routing configurations** on a small, intentionally **synthetic** set of 30 developer-authored requests. It can detect regressions in the retrieval pipeline, but does **not** establish accuracy on real Hermes workloads.

Do not use this fixture to fit weights, thresholds or aliases and then present its results as held-out performance. The catalogue was authored with the requests in mind. Report errors rather than hiding them.

## Reproduce

```bash
python tools/evaluate.py
python tools/evaluate.py --json
```

Data: `benchmarks/selection-catalogue-v1.json` and `benchmarks/selection-cases-v1.json`.

`names` indexes names only, `source` adds skill descriptions/tags, and `enriched` also indexes example aliases/intents. All three use the same BM25 implementation, decision gate and requests.

## Metrics

- **Positive top-1 hit rate:** proportion of cases with at least one relevant skill whose first suggestion is relevant.
- **Positive Recall@3:** proportion of relevant cases where at least one of the top three suggestions is relevant.
- **No-skill false-positive rate:** proportion of intentionally irrelevant/ambiguous cases where *any* skill was suggested.
- **Latency p95:** isolated in-process ranker latency, not Hermes hook startup or skill loading time.
- Misses and unwanted suggestions are printed as structured JSON.

These should be reported together. A router which always abstains has low false positives but zero recall; a router which always suggests a skill has high coverage but poor precision.

## Production accuracy release gate

See [GitHub issue #8](https://github.com/xdCloudy/hermes-skillsense/issues/8). A production evaluation requires:

1. A separately reviewed, **unseen**, consented or publicly shareable dataset with tasks from actual Hermes skill usage.
2. Skill IDs identified independently of the router's predictions.
3. Distinct task categories, multi-skill and no-skill ground truths, project precedence and unavailable skill cases.
4. A frozen training/dev set for any thresholds and a different held-out evaluation set.
5. Baseline comparison against Hermes' existing discovery, task completion outcomes and agent tool round trips.
6. A published protocol and results that distinguish cost/latency from retrieval accuracy.
7. No upload of raw private conversations, credentials or proprietary skill bodies.

The synthetic fixtures should remain a **non-release-gating smoke suite**, unless a specific regression expectation is explicitly justified and documented.

## Evaluate your own labelled dataset

You can supply local JSON files without transmitting prompts or skills:

```bash
python tools/evaluate.py --catalogue ./catalogue.json --cases ./cases.json --json > results.json
```

Catalogue schema: `{"schema_version":1,"skills":[{"id":"a","name":"skill-name","description":"...","tags":[],"aliases":[],"intents":[]}]}`.
Cases schema: `{"schema_version":1,"source":"dataset provenance","cases":[{"id":"case-1","prompt":"task","gold":["skill-name"]}]}`. Use `gold: []` for a task requiring no skill. All prompts are processed offline; output identifies case IDs and labels, not raw prompt text.

The tool does not know whether your labels are correct or independent. Results should be reviewed before being used for release decisions.
