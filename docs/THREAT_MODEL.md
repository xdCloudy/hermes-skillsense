# Threat Model

## Assets

Private skills, Hermes user profile, auth tokens, local inference endpoint, sidecar metadata, and reliable default Hermes operation.

## Trust boundaries

| Source | Trust level | Mitigation |
| --- | --- | --- |
| Installed skill Markdown/YAML | Untrusted content | Parse as inert data, no command execution |
| Model-generated metadata | Untrusted | Validate type, length, evidence and review status |
| User-configured auxiliary provider | Potentially remote | Verify effective route and block fallback |
| Local sidecar DB | Durable but corruptible | Transactions, migrations, last-known-good index |
| Gateway slash commands | Potentially external users | Authorisation and no unsafe long jobs |
| Plugin host API | Trusted documented boundary | No monkey-patching; conservative availability |

## Important failure cases

- An apparently local model URL redirects externally.
- A provider silently switches to a cloud fallback.
- A symlink in a skill directory points to private files.
- Skill YAML embeds malicious prompt instructions.
- A generated alias misclassifies a dangerous capability.
- Two Hermes processes race when writing the same SQLite store.
- Plugin registration fails and breaks Hermes startup.
- A user asks for an unsupported skill with a misleading high lexical score.

## Security invariants

Normal turns perform no network/model calls and ideally no disk writes. The optional audit never sends skill text until endpoint locality is proven. Originals are never modified. Any uncertain state fails to "no suggestion" or refuses the audit, without breaking Hermes.

See [SECURITY.md](../SECURITY.md) for reporting and mandatory tests.