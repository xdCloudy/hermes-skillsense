# Configuration Reference

**Version:** scaffold `0.1.0`. Feature toggles mentioned in [SPEC.md](../SPEC.md) are design targets until the implementation exists.

## Manifest settings

Native Hermes Desktop can render `plugin.yaml` `config_schema` fields under plugin settings.

| Setting | Default | Current behaviour |
| --- | --- | --- |
| `enabled` | `false` | Reserved; live hint injection is not implemented |
| `max_suggestions` | `3` | Reserved; no hints are emitted at present |

Setting `enabled: true` in the current scaffold does **not** activate routing. This is intentional.

## Future Metadata Clean settings (not shipped)

| Setting | Intended default |
| --- | --- |
| `clean_scope` | `audit` |
| `model_mode` | `aux` |
| `storage_mode` | `sidecar` |
| `strict_local` | `true` |
| `auto_approve` | `false` |
| `max_suggestions` | `3` |
| `max_hint_tokens` | `60` |

The auxiliary model's **effective** endpoint must be verified as loopback and any cloud fallback disabled before skill contents are transmitted. A provider name that looks local is insufficient.

## Storage

Once the sidecar is implemented, use Hermes' profile-scoped plugin data directory via `plugin_data_dir("skillsense")` and `plugin_db("skillsense")`. The current scaffold does not create a database or write any data.

## Unsupported / intentionally absent

No bundled external model, credentials, API keys, cloud service, automatic downloads or per-turn embedding daemon.