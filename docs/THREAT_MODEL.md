# Threat Model

## Assets

Private skills, Hermes user profile, auth tokens, local inference endpoint, sidecar metadata, and reliable default Hermes operation.

## Trust boundaries

| Source | Trust level | Mitigation |
| --- | --- | --- |
| Installed skill Markdown/YAML | Untrusted content | Parse as inert data, no command execution |
| Model-generated metadata | Untrusted | Validate type, length, evidence and review status |
| User-configured loopback server | Could proxy externally despite local address | Restrict direct connection to numeric loopback; require operator verification of server behavior |
| Local sidecar DB | Durable but corruptible | Transactions, migrations, last-known-good index |
| Gateway slash commands | Potentially external users | Authorisation and no unsafe long jobs |
| Plugin host API | Trusted documented boundary | No monkey-patching; conservative availability |

## Important failure cases

- An apparently local model URL redirects externally.
- The process bound to a numeric loopback endpoint silently relays skill contents to a cloud provider.
- A symlink in a skill directory points to private files.
- Skill YAML embeds malicious prompt instructions.
- A generated alias misclassifies a dangerous capability.
- Two Hermes processes race when writing the same SQLite store.
- Plugin registration fails and breaks Hermes startup.
- A user asks for an unsupported skill with a misleading high lexical score.

## Security invariants

Before the optional audit call, SkillSense performs **best-effort** masking of common private-key blocks, bearer tokens, API keys and credential assignments. This is not comprehensive secret detection; users should review skill text and verify their inference server.\n\nNormal turns perform no network/model calls and ideally no disk writes. The optional audit sends skill text only to an explicit numeric loopback endpoint (with proxy/redirect bypass), but cannot attest that the receiving process will not forward it. Originals are never modified. Any uncertain state fails to "no suggestion" or refuses the audit, without breaking Hermes.

See [SECURITY.md](../SECURITY.md) for reporting and mandatory tests.