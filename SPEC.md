# Metadata Clean — Technical Implementation Specification

**Revision:** 1.1 · **Status:** implementation-aware design specification; functional beta, not full feature parity. See [ROADMAP.md](ROADMAP.md) for release gates.

## 1. Decisions

| Dimension | Selected |
| --- | --- |
| Scope | `audit`: inspect missing *and existing* metadata |
| LLM | Local OpenAI-compatible loopback endpoint for explicit audits; Hermes auxiliary task registration exists but is not the transport |
| Storage | `sidecar`: never rewrite skill files |
| Model locality | Numeric HTTP loopback-only connection; local server forwarding behavior cannot be attested |
| Trigger | User initiated, not normal conversation |
| Approval | Manual approval required; no automatic approval shipped |
| Runtime routing | BM25 and deterministic rules; no LLM |
| Platforms | Windows, Linux, macOS |
| Dependencies | Prefer standard library only |

**Goal:** increase retrieval recall/precision while keeping normal-turn performance imperceptible and the main Hermes skill system available.

## 2. Lifecycle

```text
User requests audit
  1. Discover available installed skills
  2. Parse name/description/frontmatter/When to Use/body
  3. Compare SHA-256 and existing metadata/proposal history
  4. Run deterministic quality checks
  5. Decide if proposal generation is necessary
  6. Verify auxiliary task is actually local and fallback disabled
  7. Ask local auxiliary LLM for bounded structured metadata
  8. Parse independently; validate schema and source evidence
  9. Mark unchanged / proposed / needs_review / rejected / failed
 10. Persist transactionally to profile sidecar
 11. Review / approve selected fields
 12. Atomically rebuild read-only BM25 index
```

`--dry-run` must never write. Default `clean --audit` may save **pending** proposals but must not alter active retrieval until approval.

## 3. Discovery & extraction

Prefer documented Hermes skill discovery and availability handling. Supply an adapter for host-version differences. Fallback filesystem access is limited to configured trusted skill roots; reject symlink traversal outside them.

Extract at least: stable profile/source/skill identifier, directory/name/description, frontmatter metadata/tags/category, platform/tool requirements, `When to Use`, procedure titles, bounded body text, source SHA-256 and prior approved sidecar metadata.

Handle absent and malformed frontmatter, duplicate names, Unicode, invalid encodings, missing Markdown headings, read-only directories and extra-long skills safely. Do not execute instructions embedded in the skill or automatically load referenced URLs/files.

## 4. Audit quality checks

Audit missing descriptions/tags/intents, generic or contradictory descriptions, redundant aliases, tags unrelated to the documented capability, stale source hashes and ambiguous neighbouring skills. Existing correct metadata should be retained unchanged.

Models may propose a compact retrieval-only description, tags, aliases, positive intents, negative intents and evidence references. They may **not** invent capabilities, tools, execution permissions, authentication requirements or skill availability.

### Proposal review states

`unchanged`, `proposed`, `needs_review`, `approved`, `rejected`, `stale`, `failed`.

Current implementation approves or rejects a proposal as a whole, with no automatic approval or field-granular review. Rejected proposals remain skipped unless explicitly regenerated with `--force`.

## 5. LLM integration and locality

SkillSense registers the Hermes auxiliary task `skillrouter_tagger`, but **does not use host `ctx.llm` for model transport**: a host-configured auxiliary provider might fall back to the cloud. Instead, a manually triggered audit uses the explicit numeric loopback endpoint and locally served model ID. All model output undergoes independent proposal validation.

**Direct-transport restriction:** remote addresses, DNS hostnames, redirects and environment proxies are rejected/bypassed. A loopback endpoint may still point to a forwarding gateway, so operators must verify its server is genuinely offline. No bundled model, automatic download or built-in cloud fallback.

Use strong untrusted-document framing. A model responding with commands, webhooks, instructions or off-schema fields causes a validation error. No raw skill content is logged by default.

Implemented limits: source excerpt ≤ 12,000 characters, output cap 768 tokens, 30-second per-request default timeout, sequential model requests and a default batch of ten calls (configurable 1–50). No enforced assumption that every model supports JSON Schema.

## 6. Sidecar schema & precedence

Desired fully auditable schema (some tables remain future work):

- `skills`: canonical key, source location, current content hash, scan time.
- `metadata`: schema version, model/prompt origin, retrieval JSON, review state.
- `audits`: run ID, scope, duration, counts, failures and timestamps.
- `overrides`: explicit user-authored field values and rejection history.

Currently the primary `skills` table carries source identity, hash, metadata, review state and pending/approved JSON; atomic `index.json` and `native-catalogue.json` provide read-only snapshots. Separate audit-history/override/provenance tables are **not implemented**. Source eligibility/platform/required tools remain native Hermes decisions. Precedence: native eligibility → user overrides → source metadata → approved enriched metadata → deterministic fallback. Enriched fields can expand **search vocabulary**, never permissions.

Cache key combines source hash + schema version + audit prompt version + model identity (with stable canonical encoding). Regenerate only when stale or forced; allow a full rescan without repeating every LLM call. SQLite schema changes require explicit migrations, validation and previous-good recovery. See [schema](docs/METADATA_SCHEMA.md).

## 7. Normal-turn retrieval

```text
pre_llm_call → query normalization → indexed BM25
             → weighted name/alias/intent/title evidence
             → native eligibility filtering
             → ambiguity and abstention
             → 0–3 short hints OR None
```

A high BM25 score is *not* a calibrated probability. Weighting and abstention thresholds must be established using held-out labelled prompts. Do not reject candidates based on negative intents alone without contextual evidence.

No full skill bodies in prompt hints. Avoid modifying the system prompt; preserve cache prefix stability. Never load a skill automatically in the pre-LLM hook.

## 8. CLI commands: implemented vs planned

**Implemented in v0.2.2 beta:**

```text
hermes skillrouter status
hermes skillrouter doctor
hermes skillrouter rebuild [--root DIRECTORY]
hermes skillrouter refresh-native
hermes skillrouter clean --audit --dry-run
hermes skillrouter clean --audit --model aux --endpoint LOOPBACK_URL --model-id MODEL
    [--max-inferences 10] [--offset 0] [--force]
hermes skillrouter review list
hermes skillrouter review approve SKILL_NAME_OR_ID
hermes skillrouter review reject SKILL_NAME_OR_ID
hermes skillrouter enable
hermes skillrouter disable
```

The slash-command form supports **read-only** `/skillrouter status`. Maintenance remains CLI-only to avoid unauthorised model or file operations from messaging gateways.

**Not implemented:** field-granular review, a dedicated `show` command, native `benchmark` subcommand (the offline CLI is `python tools/evaluate.py`), JSON exports, auto-approval, and a slash-command cleanup interface.

## 9. Desktop UX

Manifest `config_schema` may provide toggles/choices for enablement, clean scope, local-only policy, max suggestions, auto-approval and local endpoint selection. Auxiliary-model assignment belongs to the host's model configuration.

Native settings forms **do not automatically grant arbitrary action buttons**. A dedicated Scan/Clean/Review panel requires separately validated Desktop SDK integration. Until then, expose maintainable CLI + slash workflows without pretending a custom Desktop button exists.

Desktop read-only status should show installed skill count, metadata coverage, pending proposals, last audit time and current index health when supported.

## 10. Failure modes

| Failure | Required behaviour |
| --- | --- |
| Auxiliary model unavailable | Abort enrichment; deterministic retrieval remains |
| Cloud/unknown endpoint | Abort before transmission |
| Invalid model JSON | Reject; log limited diagnostic |
| Skill source changes mid-audit | Invalidate/retry proposal after rehash |
| Missing eligibility API | Conservative fallback; never bypass host |
| Corrupt SQLite/index | Last-known-good or no hints |
| Multiple writers | SQLite locking; idempotent operations |
| Profile switch | Isolated state/index |
| Uninstall/update | Do not touch SKILL.md |
| Long skill body | Bounded excerpt + provenance references |

## 11. Test matrix

**Unit:** parser edge cases, deterministic audit, hashing/canonical keys, JSON constraints, provenance, approved/rejected transitions, weighting, negative intent, abstention.

**Integration:** actual Hermes plugin doctor/validator, registration under temporary HERMES_HOME, CLI and slash handling, native eligibility filtering, concurrent sessions, Windows/Linux/macOS file paths, upgrades/migrations.

**Security:** prompt injection in SKILL.md; unsafe symlinks; credential-looking content; malicious model JSON; localhost→remote redirect; proxy variables; auto/cloud auxiliary provider; disabled fallback; cross-profile leakage.

**Performance:** measured p50/p95/p99 retrieval, memory, prompt tokens, cache startup, index rebuild, process isolation, failure overhead.

**Quality:** held-out retrieval labels; Recall@1/@3, Precision@1/@3, false positives on no-skill tasks, actual task success. Compare (A) native names-only, (B) BM25 source, (C) deterministic enriched, (D) AI-audited approved.

Historical skills loaded are **weak labels**, not proof of correctness.

## 12. Release gates

No public claim of being fully functional before plugin registration, install/uninstall, reproducible benchmarks, local-only enforcement and rollback/upgrade tests pass. Quantitative targets are aspirational until measured.

Related: [ROADMAP.md](ROADMAP.md), [SECURITY.md](SECURITY.md), [docs/INTEGRATION.md](docs/INTEGRATION.md).