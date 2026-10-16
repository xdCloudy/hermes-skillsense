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

`names` indexes names only, `source` adds skill descriptions/tags, and `enriched` also uses approved aliases, positive intents and negative-intent vetoes. Only the enriched variant applies negative-intent exclusions, so baseline comparisons remain meaningful. All three use the same BM25 implementation and task requests.

## Metrics

- **Positive top-1 hit rate:** proportion of cases with at least one relevant skill whose first suggestion is relevant.
- **Positive top-3 task hit rate:** proportion of positive tasks where at least one of the top three suggestions is relevant (legacy output key `recall_at_3_on_positive`).
- **Micro Recall@3:** relevant skill labels retrieved among the three suggestions, divided by all relevant skill labels across tasks. Unlike the hit rate, this accounts for multi-skill ground truth.
- **Precision of emitted hints:** relevant emitted skill hints divided by all emitted hints (up to three per task).
- **No-skill false-positive rate:** proportion of irrelevant/ambiguous tasks where *any* skill was suggested. New JSON metrics use `null` for missing denominators; zero observations do not imply a zero error rate.
- **Wilson 95% intervals:** descriptive binomial uncertainty intervals for top-1 positive-task hit rate and no-skill false-positive rate. Small samples produce wide bounds; they do not correct biased task selection or incorrect labels.
- **Latency p95:** isolated in-process ranker latency, not Hermes hook startup or skill loading time.
- Misses and unwanted suggestions are printed as structured JSON.

These should be reported together. The historical JSON fields `precision_at_1_on_positive` and `recall_at_3_on_positive` remain for compatibility but are **task hit rates**, not micro recall or hint precision. Prefer the explicitly named new metrics. A router which always abstains has low false positives but zero recall; a router which always suggests a skill has high coverage but poor precision.

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

## Export your actual installed catalogue (local only)

From a Hermes profile where you have already run `hermes skillrouter rebuild` or
`hermes skillrouter refresh-native`, export the skills eligible under the most
recent local native snapshot:

```bash
python tools/export_catalogue.py \
  --data-dir ~/.hermes/plugin-data/skillsense \
  --output ./my-local-catalogue.json
```

The exporter refuses missing or expired native snapshots, and refuses to
overwrite an existing output. New exports use owner-only file permissions
(`0600` on POSIX) and new output directories use `0700` where supported;
permissions of existing parent directories remain outside its control. It uses the same conservative native/sidecar
matching code as routing, with no model, browser or network calls.

**Privacy:** The exporter replaces internal skill IDs (which may include absolute
profile paths) with opaque, export-local identifiers. The resulting file can
still contain private skill names, descriptions and approved aliases. Nothing is uploaded automatically. Inspect the JSON
before sharing it with reviewers or committing it to a public repository.
No prompt histories or user tasks are included.

Pair the export with a *separately created* case file whose `gold` labels
have been manually reviewed. Do not use the router's own predictions as labels:

```bash
python tools/evaluate.py \
  --catalogue ./my-local-catalogue.json \
  --cases ./my-held-out-cases.json --json
```

This export is infrastructure to make issue #8 easier to evaluate; it does
not itself satisfy the held-out accuracy release gate.

## Dataset validation

The evaluator rejects duplicate skill names or IDs, malformed metadata arrays,
unlabelled/duplicate tasks, duplicate or unknown gold labels and unsupported
schemas before reporting accuracy. Labels identify unique canonical load names,
not potentially ambiguous project-shadowed display names. A dataset that
contains same-name skills requires separately resolved session eligibility
before it can be scored reliably; this evaluator does not claim to test native
session/project precedence. This prevents silent metric distortion but does
not verify that human labels are independently correct.
