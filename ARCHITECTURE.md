# Architecture

> Design document. No production integration is implemented yet.

## Execution domains

### A. Hot path — every user turn

```text
Hermes pre_llm_call
  → immutable in-memory index
  → tokenise current task/context
  → BM25 retrieval
  → exact name/alias bonuses
  → native eligibility filter
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

## Modules (planned)

| Boundary | Responsibility |
| --- | --- |
| `discovery` | Hermes catalogue adapter + safe filesystem fallback |
| `parser` | Read skill YAML/Markdown as untrusted data |
| `audit` | Missing, vague, stale, duplicate, contradictory metadata |
| `auxiliary` | Host LLM API adapter + strictly local fallback transport |
| `validation` | JSON schema, evidence, uniqueness, size and provenance |
| `storage` | Profile-scoped SQLite, migrations, recovery and overrides |
| `retrieval` | Pure Python BM25, field weights, filtering, abstention |
| `hooks` | Hermes hook + lightweight commands |
| `cli` | status/clean/review/show/rebuild/doctor/benchmark |
| `benchmark` | Dataset replay, metrics and performance checks |

## Availability & security

Prefer a **supported** Hermes skills catalogue/eligibility surface. If unavailable, do not invent eligibility or suggest possibly ineligible skills; use a restrictive adapter and provide a clear compatibility warning. Required tools/platform rules are higher priority than generated tags.

Use host-registered `pre_llm_call` with callback `**kwargs`, returning `{"context": "..."}` or `None`. No monkey-patching, overriding internal prompts or swapping native tools. Keep prompt-caching compatible.

Store plugin metadata in the Hermes-managed profile plugin-data directory, not alongside a third-party skill. Use stable scoped identifiers; names alone are not unique.

## Durability

- Source SHA-256 + schema/prompt/model versions drive invalidation.
- Persist approved records and pending proposals separately.
- Use transactions, busy timeout, explicit migrations, and interruption-safe rebuilds.
- Readers use a snapshot index; writer atomically publishes an entirely built replacement.
- Missing or corrupt cache ⇒ return `None`; keep native Hermes functional.
- Uninstall ⇒ no changes to original skills or Hermes runtime.

## Offline guarantee

The host auxiliary task may not itself guarantee offline routing if it supports cloud fallbacks. Resolve and verify the **effective** provider/endpoint and disable fallback before any skill text is sent. If the host cannot prove locality, use a strictly loopback-only minimal transport or abort. Model load, authentication and network policy are evaluated in [SECURITY.md](SECURITY.md).

## Runtime targets (not measured)

p95 ≤ 5ms for up to 500 skills; <10MB additional memory; zero per-turn model/network/GPU usage; 0–60 hint tokens.

## Related material

[SPEC.md](SPEC.md) · [INTEGRATION.md](docs/INTEGRATION.md) · [METADATA_SCHEMA.md](docs/METADATA_SCHEMA.md)