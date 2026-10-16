# Sidecar Metadata Schema (proposed)

The sidecar describes **retrieval**, not permission or actual supported execution capability. Files under a skill directory remain unchanged.

## Example record

```json
{
  "schema_version": 1,
  "skill_id": "user:android-reverse-engineering",
  "source_sha256": "<64-digit-sha256>",
  "audit": {
    "status": "proposed",
    "model_id": "<local-auxiliary-model>",
    "prompt_version": "1",
    "reviewed": false
  },
  "retrieval": {
    "description": "Inspect and decompile existing Android APKs",
    "tags": ["android", "apk", "jadx", "dex", "decompile"],
    "aliases": ["inspect an APK", "analyse DEX bytecode"],
    "positive_intents": ["Understand an existing Android application"],
    "negative_intents": ["Create a new Android UI"]
  }
}
```

Values shown here are **illustrative**, not a representation of an installed skill.

## Record contract

| Field | Constraint |
| --- | --- |
| `schema_version` | Integer; explicit migrations |
| `skill_id` | Stable scoped key, never name-only |
| `source_sha256` | SHA-256 of canonical source snapshot |
| `audit.status` | unchanged/proposed/needs_review/approved/rejected/stale/failed |
| `retrieval.description` | Retrieval-only; ≤240 characters |
| `tags` | Max 12 distinct normalised terms |
| `aliases` | Max 8 distinct phrases |
| `positive_intents` | Max 8 evidenced phrases |
| `negative_intents` | Max 6 evidenced phrases |
| `model_id` | Local auxiliary model identifier only |
| `prompt_version` | Versioned proposal template |
| `reviewed` | Whether an operator accepted the proposal |

Each generated field or item must preserve its `origin` (source/extracted/model/user) and a verifiable source-evidence reference. Sidecar JSON above simplifies this per-item provenance; implementation may normalise it into child tables.

No arbitrary commands, URLs, instructions, secrets or execution-capability declarations are valid generated metadata. Never treat negative intents as an unconditional veto.

## Identity and invalidation

Prefer a Hermes-native catalogue identity; otherwise use a canonical combination of profile, source namespace and root-relative skill path. Guard against collisions, Unicode differences and Windows case differences.

Re-evaluate cache when source hash, metadata schema, audit prompt, or generator identity changes. User rejections should not be silently overwritten. Never carry stale permissions across skill versions.

## Precedence

1. Native Hermes availability and platform/tool requirements.
2. Explicit approved user overrides.
3. Skill-declared source metadata.
4. Approved generated retrieval metadata.
5. Deterministic extraction fallback.

Only **approved** sidecar records affect live ranking. See [SPEC.md](../SPEC.md).