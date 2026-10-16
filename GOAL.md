# SkillSense — Project Goal

## Mission

Make skill selection in Hermes Agent **fast, accurate, private, and inexpensive** without increasing baseline prompt context or requiring a continuously running model.

SkillSense is an independently maintained, public, portable plugin. The cloud symbol represents the xdCloudy identity; the project name is **SkillSense**.

## Product principles

1. **Local first.** Standard routing must not use the network. Metadata enrichment may only use an explicitly verified loopback model endpoint.
2. **Lightweight by default.** Use pure-Python BM25 and modest in-process indexes; no vector DB, GPU, PyTorch or model download as a prerequisite.
3. **Always preserve Hermes.** SkillSense supplies hints, not authoritative tool decisions. Uncertain matches must abstain. Hermes remains capable of native discovery.
4. **Read-only skills.** Do not modify or execute installed skills. Generated search metadata is held in versioned plugin sidecars.
5. **User controlled enrichment.** Audit is explicit, local auxiliary inference is opt-in, and material changes require review.
6. **Demonstrated accuracy.** Reproduce real-world benchmarks. Never claim improvements based solely on matching historical skill loads.
7. **Portable and resilient.** Windows, macOS and Linux; no hard-coded home directories or private Hermes monkey-patches.
8. **No unsupported promises.** Clearly distinguish prototype code, plans, and measured capability.

## Default settings

- Metadata cleanup scope: **audit**, including existing metadata.
- Model assignment: **aux** — user-chosen Hermes auxiliary task.
- Storage: **sidecar** — profile-scoped durable cache.
- Normal-turn inference: **off**, unconditionally.
- Cloud inference: **disallowed** during cleaning.
- Maximum contextual suggestions: **3**; usually **0–2**.
- Cache update: **atomic**; last-known-good fallback.
- Default auto-approval of model proposals: **off**.

## Explicit exclusions

No bundled Jev/OpenJev models, mandatory embeddings, cloud fallback, autonomous skill edits, replacement for native skill_view, global prompt rewrite, silent dependency installation or benchmark claims without data.

See [SPEC.md](SPEC.md) and [ARCHITECTURE.md](ARCHITECTURE.md).