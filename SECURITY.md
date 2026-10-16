# Security Policy

## Supported versions

SkillSense is presently **pre-release** with no production-supported version. Security reviews remain welcome.

## Reporting privately

For a vulnerability, use the repository's **GitHub Security → Report a vulnerability** private reporting flow, if enabled. If unavailable, contact the maintainer privately through an established channel before publishing exploit details. Do **not** place credentials, sensitive skill contents, or usable exploits in a public issue.

Do not assume a response SLA until a support policy is published.

## Threat model

Potential attacker-controlled inputs include installed `SKILL.md` text, YAML frontmatter, auxiliary-model output, untrusted skill locations, local HTTP endpoints and gateway commands. Skill content can contain prompt-injection instructions and accidental secrets.

Protected assets include installed skill sources, local model prompts/data, Hermes profiles, runtime availability, private files, credentials and cache integrity.

## Required controls

- **No skill-file writes:** metadata lives in a plugin-owned sidecar.
- **No arbitrary execution:** never run scripts, shell commands or URLs from a skill while indexing.
- **Constrained files:** restrict skill roots and prevent symlink/path traversal outside approved locations.
- **Loopback-only audit transport:** accept only numeric loopback HTTP destinations, bypass environment proxies, and reject redirects and remote DNS. This limits SkillSense's direct connection but cannot attest that the local receiving server uses local weights or does not forward input to cloud backends. Operators must separately verify the model server and disable its external fallbacks.
- **Trust boundaries:** the LLM sees skill documents as untrusted data; all output is independently validated. JSON parse success is insufficient.
- **Data minimisation:** bound skill excerpts; redact secret-looking content where possible; no raw skill content or prompts in normal logs.
- **Safe database:** SQLite transactions, explicit migrations, cross-process locking and previous-good recovery; segregate profile data.
- **No-skill fallback:** an exception in routing must not interrupt Hermes or silently grant unavailable skill capabilities.
- **Authenticated commands:** avoid running scans from untrusted gateway senders; no exposure of audit records through public channels.
- **No false privacy claims:** no audit is allowed when host local-only enforcement cannot be proven; normal-turn routing is always offline.

## Required security tests

1. Cloud or automatic auxiliary provider selection.
2. Cloud fallback after loopback failure.
3. Proxy variables, hostname rebinding, IPv6 and HTTP redirects.
4. Prompt injection in a skill body and model output.
5. Huge or malformed frontmatter, Unicode control chars and broken Markdown.
6. Symlinked roots, escaped paths and replaced files mid-audit.
7. Concurrent audit writers and interrupted schema migrations.
8. Gateway command misuse and cross-profile data access.

Refer to [SPEC.md](SPEC.md) and [AGENTS.md](AGENTS.md).