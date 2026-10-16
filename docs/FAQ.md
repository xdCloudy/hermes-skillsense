# Frequently Asked Questions

### Does SkillSense use AI every turn?

No. The design uses local BM25 and deterministic ranking during ordinary conversations. A local auxiliary model is reserved for a user-triggered metadata audit.

### Why BM25 rather than embeddings?

A compact lexical index has nearly zero operational overhead. It struggles with synonyms, which is why Metadata Clean will enrich retrieval aliases/intents *offline* ahead of time. Accuracy must be measured against manually labelled prompts before enabling live routing.

### What does "local-only" mean?

Normal turns make no model/network requests. Audit requests are sent only to an explicit numeric loopback address; HTTP proxy environment variables and redirects are bypassed. **This cannot attest what the loopback service does afterward**: an operator's local inference gateway might forward prompts remotely. For full offline operation, configure and verify a genuinely on-device/local model server without external provider fallbacks.

### Will the plugin rewrite my installed skills?

No. Generated metadata is stored in a versioned SQLite sidecar. Source SKILL.md files remain untouched.

### What happens when a skill has no frontmatter?

The future scanner will extract useful Markdown content and can request enrichment. It must handle bad/missing metadata without crashes.

### What happens when retrieval is uncertain?

SkillSense abstains. Native Hermes skill discovery still works; it should never be blocked by the router.

### Is this ready to install?

The current **scaffold** contains a real `plugin.yaml` and registration entry point, but only diagnostic commands. No skill routing or Metadata Clean functionality is implemented yet.

### Is this an official Hermes plugin?

No. It is an independently maintained community plugin for Hermes Agent.