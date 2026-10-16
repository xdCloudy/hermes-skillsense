# Architecture

> **Status: implemented experimental beta, not production-certified.** The sections below distinguish active components from intended future integration. The standalone router and real Hermes plugin registration/CLI have passed CI, but session-specific eligibility and independently validated selection quality remain outstanding.

## Execution domains

### A. Hot path — every user turn

```text
Hermes pre_llm_call
  → cached local index and native-eligibility snapshot (refreshed at most once/minute)
  → tokenise current user request
  → BM25 retrieval
  → repeated name/alias terms and whole-phrase gate
  → canonical native catalogue filter (snapshot captured during maintenance)
  → ambiguity / abstention gate
  → return None or ephemeral {context: hint}
```

**Never** invoke an auxiliary model, read full skill bodies from disk, rebuild an index, connect to a network, or perform SQLite writes on this path.

Hints are advisory. Hermes continues to choose when to call its native skill-viewing tool.

### B. Cold path — requested maintenance

```text
Discovery → parse source → hash → deterministic audit
  → compare sidecar history → optional local auxiliary inference
  → independent JSON/schema/evidence checks → review states
  → SQLite transaction → build immutable index → swap
```

Audit work must not block conversations. If the host has no safe background execution surface, require CLI maintenance rather than spawning unmanaged threads from a chat command.

## Implemented modules and remaining design work

| File | Active responsibility |
| --- | --- |
| `__init__.py` | Hermes hook registration, CLI commands and explicit metadata maintenance |
| `catalog.py` | Bounded read-only SKILL.md scanning, restricted frontmatter and proposal validation |
| `eligibility.py` | Maintenance-time native skill-list capture and safe candidate gating |
| `store.py` | Profile-scoped SQLite sidecar, source-hash checks, atomic index and catalogue snapshots |
| `core.py` | Pure Python BM25 implementation |
| `routing.py` | Conservative matching, abstention, snapshot refresh and session hint deduplication |
| `local_model.py` | Explicit loopback-only audit transport, bounded responses and best-effort redaction |
| `tools/evaluate.py` | Synthetic and user-provided offline labelled retrieval evaluation |
| `tests/` | Unit, local-model stub and real-Hermes CI fixture coverage |

**Not yet implemented:** full Hermes session-scoped catalogue access, an independently held-out relevance benchmark, Desktop audit/review UI, advanced field-granular review and complete audit provenance tables. These remain design targets, not shipping guarantees.

## Availability & security

Prefer a **supported** Hermes skills catalogue/eligibility surface. If unavailable, do not invent eligibility or suggest possibly ineligible skills; use a restrictive adapter and provide a clear compatibility warning. Required tools/platform rules are higher priority than generated tags.

Use host-registered `pre_llm_call` with callback `**kwargs`, returning `{"context": "..."}` or `None`. No monkey-patching, overriding internal prompts or swapping native tools. Keep prompt-caching compatible.

Store plugin metadata in the Hermes-managed profile plugin-data directory, not alongside a third-party skill. Use stable scoped identifiers; names alone are not unique.

## Durability

- Source SHA-256 drives stale-source invalidation; additional model/prompt provenance keys are a future enhancement.
- Persist approved records and pending proposals separately.
- Use SQLite transactions and a busy timeout; JSON indexes are published atomically. More extensive migration/recovery support remains planned.
- Readers use a snapshot index; writer atomically publishes an entirely built replacement.
- Missing or corrupt cache ⇒ return `None`; keep native Hermes functional.
- Uninstall ⇒ no changes to original skills or Hermes runtime.

## Model transport trust boundary

Normal-turn routing does not invoke a model or make network requests. Opt-in cleanup accepts only an explicit numeric loopback inference URL, blocks redirects and bypasses environment HTTP proxies. **This cannot attest that the process listening on loopback does not forward prompts to a remote provider.** Operators must independently verify their local model server and disabled cloud fallbacks. See [SECURITY.md](SECURITY.md).

## Runtime targets and evidence

Targets: p95 ≤ 5ms for up to 500 skills; <10 MB additional memory; zero per-turn model/network/GPU usage; 0–60 hint tokens. On one Ubuntu CI runner, the isolated 500-skill synthetic BM25 microbenchmark measured approximately 1.43ms p95. **Memory, full Hermes hook overhead, token savings and real-world routing accuracy have not been independently certified.**

## Related material

[SPEC.md](SPEC.md) · [INTEGRATION.md](docs/INTEGRATION.md) · [METADATA_SCHEMA.md](docs/METADATA_SCHEMA.md)