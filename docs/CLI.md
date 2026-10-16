# Command-Line and Slash Interface

## Available in scaffold v0.1.0

```text
hermes skillrouter status
hermes skillrouter doctor
/skillrouter status
/skillrouter doctor
```

These provide honest scaffold status and diagnostics. They do not perform skill scanning, selection or metadata cleaning.

## Planned, not implemented

```text
hermes skillrouter clean --audit [--dry-run] [--force] [--model aux]
hermes skillrouter review [--skill ID]
hermes skillrouter show SKILL
hermes skillrouter rebuild
hermes skillrouter benchmark --dataset PATH
hermes skillrouter export --format json
```

Slash commands should offer `/skillrouter clean|review|show` only once they can safely execute with gateway authentication and without blocking conversations. Prefer a CLI command for any long-running maintenance process.

## Exit codes (future contract)

- `0`: success, including a clean abstention.
- `2`: bad arguments/configuration.
- `3`: local model route unsafe/unavailable.
- `4`: validation failure or partial audit.
- `5`: durable storage or migration failure.

Exact handling will be implemented and tested before being considered stable.