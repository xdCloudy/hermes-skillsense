<div align="center">

<img src="assets/skillsense-logo.png" alt="SkillSense — cloud with an intelligent skill selection pathway" width="420">

# SkillSense

**The right skill. Right on cue.**

A lightweight, local-first skill router for [Hermes Agent](https://github.com/NousResearch/hermes-agent).

*BM25-powered discovery · On-demand AI metadata enrichment · No always-on model*

[Architecture](ARCHITECTURE.md) · [Specification](SPEC.md) · [Roadmap](ROADMAP.md) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md)

</div>

> [!IMPORTANT]
> **Project status: planning / bootstrap (pre-alpha).** This repository currently describes the intended plugin; its routing, metadata-cleaning and integration features are **not yet implemented or released**. The interfaces and commands below are design targets, not installation instructions.

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

## Planned capabilities

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

## Command design (not implemented)

```bash
hermes skillrouter status
hermes skillrouter clean --audit --dry-run
hermes skillrouter clean --audit --model aux
hermes skillrouter review
hermes skillrouter rebuild
hermes skillrouter benchmark
hermes skillrouter doctor
```

Planned in-session entry point: `/skillrouter`.

The default cleanup choice is **audit + auxiliary model + sidecar storage**. Cleaning is opt-in; proposals are not automatically activated without approval unless the user explicitly enables a conservative auto-approval policy.

## Documentation

| Document | Purpose |
| --- | --- |
| [GOAL.md](GOAL.md) | Mission, scope, and non-negotiable constraints |
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