# Hermes Integration Notes

**Status: experimental plugin implementation; host integration still unverified.** `plugin.yaml` and `__init__.py` register no-op `pre_llm_call`, terminal `skillrouter status|doctor` and slash `skillrouter`. Validate on installed Hermes before advertising installation support. Metadata Clean remains design only.

## Primary source

[Official Hermes plugin development documentation](https://hermes-agent.nousresearch.com/docs/developer-guide/plugins)

## Relevant native APIs

- General directory plugin: `plugin.yaml` plus a Python `register(ctx)` entry point.
- `ctx.register_hook("pre_llm_call", callback)`: observers can return ephemeral `{"context": "..."}` or `None`; callback accepts `**kwargs`.
- `ctx.register_cli_command(name=..., help=..., setup_fn=..., handler_fn=...)`: terminal subcommands.
- `ctx.register_command("skillrouter", handler=..., description=...)`: in-session slash commands.
- Manifest `config_schema`: native Desktop settings fields.
- Host-owned per-profile `plugin_data_dir()` / `plugin_db()`: plugin durable storage.
- Host-owned plugin LLM access for metadata generation; carefully check any privileged capabilities and provider routing.

These are integration targets, **not** a claim of an installable plugin in this repository. Do not copy an unverified `register_auxiliary_task` or `complete_structured` call signature from a draft spec without checking current authoritative docs and host validation.

## Packaging sequence

1. Implement safe no-op `register(ctx)` with basic status commands. **Complete in scaffold.**
2. Add accurate `plugin.yaml` declarations; do not declare hooks or tools that aren't registered.
3. Validate via `hermes plugins doctor . --ci`.
4. Validate catalog compatibility via `hermes plugins validate .`.
5. Test isolated `HERMES_HOME`, multiple profiles, runtime failures and uninstall/reinstall.
6. Only then document `hermes plugins install xdCloudy/hermes-skillsense` as a working command.

## Desktop UX limitation

Manifest settings render standard fields; custom Scan/Clean/Review buttons require separately tested Desktop SDK support. Use CLI and slash commands for operations until that UI is implemented. Never assume arbitrary custom controls can be added by manifest alone.

## Eligibility boundary

A router hint must not claim a skill is available unless Hermes' own availability rules are verified. A fallback scanner may discover raw files but cannot on its own infer hidden host eligibility or trust decisions.

## Local LLM boundary

Host auxiliary routing may include remote providers and automatic fallbacks; before sending skill text check the resolved **effective** route and fallback handling. If proof is unavailable, block host-based enrichment and optionally use a separate explicit loopback-only transport with proxy and redirect restrictions.

## Tests

Hermes doctor with ephemeral home; callback context injection/no-op; invalid manifests; multiple plugins; profile changes; unavailable skill; transient model/network failures. Pin a tested minimum Hermes version only after integration tests pass.
## Native skill eligibility gate (experimental)

At first router activation, SkillSense calls Hermes' `tools.skills_tool.skills_list()`, the same API Hermes uses for native listing. It explicitly rejects load names missing from the native list, duplicate names, and source-description mismatches. This covers Hermes' platform/environment/app/disabled gates and namespaced plugin listings without replicating their rules. If the listing fails, it injects **no hints**.

**Trade-offs:** native eligibility is captured once per loaded router/session, so changes require a restart. Skills with no declared description cannot yet be safely matched to their filesystem source and are omitted from hints (but may still be audited). Individual project roots should be revalidated when changing working directory. This gate must not be mistaken for full session-specific availability parity.
