<div align="center">

<img src="assets/skillsense-logo.png" alt="SkillSense — blue cloud skill routing icon" width="240">

# SkillSense

**The right skill. Right on cue.**

A lightweight, local-first skill router for [Hermes Agent](https://github.com/NousResearch/hermes-agent).

*BM25-powered discovery · On-demand AI metadata enrichment · No always-on model*

[Architecture](ARCHITECTURE.md) · [Specification](SPEC.md) · [Roadmap](ROADMAP.md) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md)

</div>

> [!IMPORTANT]
> **Project status: experimental implementation (v0.2.2), not certified production-ready.** The BM25 router, read-only skill scanner, SQLite sidecar, review commands and strictly local metadata-audit transport are implemented. They are **opt-in**; normal skill hints are disabled until enabled through the CLI. An isolated real-Hermes installation has passed plugin doctor, validation, and CLI lifecycle smoke tests. **Session-dependent skill-eligibility parity ([#7](https://github.com/xdCloudy/hermes-skillsense/issues/7)) and an independent held-out selection-quality evaluation ([#8](https://github.com/xdCloudy/hermes-skillsense/issues/8)) remain stable-release blockers.** Hermes' canonical `skills_list()` is captured during explicit catalogue maintenance; normal turns consume a local snapshot with safe native/plugin fallback entries, without model or catalogue API calls.

## Why SkillSense?

Hermes skills are powerful, but loading every skill description costs context, while finding a skill through an extra search can cost time. Keyword-only name lists are cheap but can miss unfamiliar terminology. Semantic retrieval adds compute and still can miss the right skill.

SkillSense aims to sit between those extremes: maintain a compact, offline search index, suggest only well-supported matches, and leave final skill loading to Hermes. **When uncertain, abstain and preserve normal Hermes discovery.**

## Design

```text
User turn
   │
   ├─ Existing Hermes discovery remains available
   │
   └─ SkillSense pre-LLM hook
         │
         ├─ In-memory BM25 + exact names/aliases
         ├─ Availability filtering + evidence-based selection
         ├─ Uncertain? → No hint
         └─ Confident? → 0–3 short skill hints
                               │
                         Hermes skill_view()
```

**Metadata Clean** is a separate, manually triggered maintenance workflow:

```text
Installed SKILL.md files
   → Audit missing / weak metadata
   → Optional local Hermes auxiliary model
   → Validate proposals and evidence
   → Review and approve
   → Store in plugin-owned sidecar
   → Rebuild BM25 index
```

Neither skill bodies nor generated metadata should be written back to third-party `SKILL.md` files.

## Implemented architecture and known limitations

| Area | Design |
| --- | --- |
| Routing | In-process BM25 with name/alias matching, conservative abstention; explicitly enabled only |
| Runtime inference | **None** — no inference calls during ordinary turns |
| Privacy | Local-only by default; fail closed if auxiliary inference would leave the machine |
| Metadata Clean | Opt-in audit, pending proposals, manual approval, stale-source invalidation |
| AI enrichment | Registered Hermes auxiliary task; uses a numeric loopback OpenAI-compatible endpoint and disables client-side proxies/redirects; a locally hosted forwarding proxy is outside the plugin's control |
| Storage | Profile-scoped SQLite sidecar; skill source files unchanged |
| Compatibility | Native Hermes plugin interfaces; Windows, Linux, macOS |
| Fallback | Return no hint rather than interrupt the agent |
| Dependencies | Python standard library wherever Hermes APIs permit |
| User controls | CLI rebuild, audit, review, enable/disable, status; slash-command status only; Desktop action UI pending |

## Offline retrieval evaluation

```bash
# Included synthetic 30-case smoke dataset.
python tools/evaluate.py

# Your own independently labelled, local Hermes tasks.
python tools/evaluate.py --catalogue ./catalogue.json --cases ./cases.json --json
```

No prompts or skill files are uploaded. See [evaluation methodology](docs/EVALUATION.md). The bundled dataset is deliberately synthetic and **does not establish real-world accuracy**.

## Performance goals (not certified)

These are **production targets**, not guaranteed end-to-end figures. The standalone BM25 implementation has been measured in GitHub Actions on Ubuntu/Python 3.12 using 500 synthetic skills and 2,000 queries: **p50 1.24 ms, p95 1.43 ms, p99 1.62 ms**. This does not include Hermes hook overhead or establish skill-selection accuracy.

- p95 retrieval latency under **5 ms** for a catalogue of ~500 skills.
- No GPU/VRAM usage, background service, or network request on the normal-turn path.
- Under **10 MB** extra runtime memory for a 500-skill index.
- Default context addition of **0–60 tokens** and at most three skill suggestions.
- No skill instructions loaded until Hermes actually requests them.

## Getting started (experimental)

Install into an **isolated Hermes profile** until host compatibility and skill-eligibility parity are validated:

```bash
hermes plugins install xdCloudy/hermes-skillsense --no-enable
hermes plugins enable skillsense
hermes plugins doctor skillsense --ci

# Build an index from the user's installed skills.
hermes skillrouter rebuild

# Inspect current status; enable only after reviewing the index.
hermes skillrouter status
hermes skillrouter enable
# Restart Hermes to activate hints.
```

Disable at any time with `hermes skillrouter disable` and restart Hermes. All original SKILL.md files remain unchanged.

### Metadata Clean

```bash
# Read-only report; no model calls and no writes.
hermes skillrouter clean --audit --dry-run

# Stage suggested retrieval metadata using your own local auxiliary model.
hermes skillrouter clean --audit --model aux \
  --endpoint http://127.0.0.1:8011/v1/chat/completions \
  --model-id YOUR_LOCAL_MODEL --max-inferences 10

# Rerun clean to process the next unreviewed batch, without redoing pending proposals.\n\n# Review and explicitly approve/reject one proposal.
hermes skillrouter review list
hermes skillrouter review approve android-re
```

You may also configure **Enabled**, **Maximum Suggestions**, **Local Model Endpoint**, and **Local Model ID** in Hermes Desktop → Plugins → SkillSense. Restart Hermes after changing routing settings. The CLI requires a **numeric loopback address**, not a hostname or cloud provider, and bypasses proxies and redirects. The Hermes auxiliary task is registered for future native integration, but the host's auxiliary completion API may use remote fallback, so this release intentionally uses the explicit loopback transport instead. A numeric loopback URL constrains **SkillSense's outgoing connection**, but cannot prove the server behind it runs a genuinely local model or does not forward data elsewhere. Verify your chosen inference server's configuration. There are no bundled model weights, background services, or per-turn inference.

For isolated Hermes plugin hosts, `skillrouter rebuild` captures the canonical Hermes skill catalogue in a profile-scoped sidecar. The runtime reads this snapshot without importing host-only modules. **It expires after seven days**; rerun `hermes skillrouter rebuild` after skill/profile changes. Missing or expired snapshots produce no hints.

The default scan covers `$HERMES_HOME/skills` (or `~/.hermes/skills`). Extra trusted skill roots can be selected using `--root PATH`; the plugin does not automatically index untrusted project skills. Unsupported platform/requirement declarations are excluded conservatively.

### Refresh native/plugin skills without scanning

For profiles containing only Hermes-native or plugin-provided skills (even when there is
no local `skills/` directory), run:

```bash
hermes skillrouter refresh-native
hermes skillrouter enable
```

This refreshes Hermes' canonical availability snapshot, preserves existing
approved metadata, and creates an empty sidecar index if necessary.
It never reads or modifies `SKILL.md` files and makes no model calls.
An empty/unavailable host catalogue is an error and preserves the previous snapshot.
Existing Hermes sessions may need a restart after changing routing settings.

## Validate locally

```bash
python -m unittest discover -s tests -v
python tools/check_repo.py
python tools/benchmark.py
hermes plugins doctor . --ci
hermes plugins validate .
```

**Verification:** Native Hermes plugin doctor, validation, isolated CLI lifecycle and Windows/macOS/Linux Python CI have passed. **Remaining production gates:** native skill eligibility/trust parity ([issue #7](https://github.com/xdCloudy/hermes-skillsense/issues/7)) and a manually labelled retrieval-accuracy evaluation ([issue #8](https://github.com/xdCloudy/hermes-skillsense/issues/8)). Until those pass, treat routing as experimental.

## Documentation

| Document | Purpose |
| --- | --- |
| [GOAL.md](GOAL.md) | Mission, scope, and non-negotiable constraints |
| [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) | Clone, test and Hermes integration checks |
| [docs/CONFIGURATION.md](docs/CONFIGURATION.md) | Current and proposed settings |
| [docs/CLI.md](docs/CLI.md) | Available diagnostic commands and planned operations |
| [docs/FAQ.md](docs/FAQ.md) | Design and installation questions |
| [docs/DESIGN_DECISIONS.md](docs/DESIGN_DECISIONS.md) | Architectural decision log |
| [docs/THREAT_MODEL.md](docs/THREAT_MODEL.md) | Threat boundaries and mitigations |
| [docs/RELEASING.md](docs/RELEASING.md) | Release gates |
| [SPEC.md](SPEC.md) | Metadata Clean functional and technical specification |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Component boundaries and lifecycle |
| [ROADMAP.md](ROADMAP.md) | Ordered milestones and release gates |
| [AGENTS.md](AGENTS.md) | Rules for AI coding agents and maintainers |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Development process, checks and pull requests |
| [SECURITY.md](SECURITY.md) | Threat model and vulnerability reporting |
| [docs/METADATA_SCHEMA.md](docs/METADATA_SCHEMA.md) | Sidecar field contract and precedence |
| [docs/BENCHMARKS.md](docs/BENCHMARKS.md) | Baseline and evaluation protocol |
| [docs/INTEGRATION.md](docs/INTEGRATION.md) | Hermes APIs and compatibility checks |

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) and [AGENTS.md](AGENTS.md) before submitting an issue or pull request. Please do not publish performance or accuracy claims without reproducible results, or describe planned commands as functional.

## Acknowledgements and independence

Designed for the [Nous Research Hermes Agent](https://github.com/NousResearch/hermes-agent) ecosystem. SkillSense is an independent community project, not an official Nous Research plugin. "Cloudy" is represented by the cloud in the logo; the project's public-facing name is simply **SkillSense**.

## License

[MIT](LICENSE) © 2026 xdCloudy.