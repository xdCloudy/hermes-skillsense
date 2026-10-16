<div align="center">

<img src="assets/skillsense-logo.png" alt="SkillSense — blue cloud skill routing icon" width="240">

# SkillSense

**The right skill. Right on cue.**

A lightweight, local-first skill router for [Hermes Agent](https://github.com/NousResearch/hermes-agent).

*BM25-powered discovery · On-demand AI metadata enrichment · No always-on model*

[Architecture](ARCHITECTURE.md) · [Specification](SPEC.md) · [Roadmap](ROADMAP.md) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md)

</div>

> [!IMPORTANT]
> **Project status: pre-alpha scaffold (v0.1.0).** A native Hermes plugin entry point, diagnostic commands, a standalone BM25 core and unit tests are now present. **Live routing, skill scanning and Metadata Clean are not implemented.** The registered pre-LLM hook is intentionally a no-op. Plugin API compatibility must still be validated on a real Hermes installation.

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

## Architecture and planned capabilities

| Area | Design |
| --- | --- |
| Routing | In-process BM25, name and alias boosts, conservative selection |
| Runtime inference | **None** — no inference calls during ordinary turns |
| Privacy | Local-only by default; fail closed if auxiliary inference would leave the machine |
| Metadata Clean | Explicit `audit` mode for missing, poor, stale and conflicting metadata |
| AI enrichment | Existing Hermes **auxiliary model**, used only during cleanup |
| Storage | Profile-scoped SQLite sidecar; skill source files unchanged |
| Compatibility | Native Hermes plugin interfaces; Windows, Linux, macOS |
| Fallback | Return no hint rather than interrupt the agent |
| Dependencies | Python standard library wherever Hermes APIs permit |
| User controls | CLI, slash commands, native Desktop settings; dedicated Desktop UI later |

## Performance goals

These are **targets, not achieved benchmark results**:

- p95 retrieval latency under **5 ms** for a catalogue of ~500 skills.
- No GPU/VRAM usage, background service, or network request on the normal-turn path.
- Under **10 MB** extra runtime memory for a 500-skill index.
- Default context addition of **0–60 tokens** and at most three skill suggestions.
- No skill instructions loaded until Hermes actually requests them.

## Available scaffold commands

```bash
hermes skillrouter status
hermes skillrouter doctor
```

Available in-session commands: `/skillrouter status` and `/skillrouter doctor`.

**Planned, not yet available:** `clean --audit`, `review`, `rebuild`, and `benchmark`. Metadata Clean defaults will be **audit + auxiliary model + sidecar storage**. No cleanup runs in the scaffold.

## Develop and validate the scaffold

```bash
python -m unittest discover -s tests -v
python tools/check_repo.py
hermes plugins doctor . --ci  # requires a local Hermes installation
```

See [development setup](docs/DEVELOPMENT.md). The plain Python tests do not substitute for a successful Hermes integration test.

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