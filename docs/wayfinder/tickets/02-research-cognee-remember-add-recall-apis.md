# Research: Cognee remember, add, and recall APIs for Slack and custom text provenance

- Status: closed
- Labels: `wayfinder:research`
- Assignee: research-agent
- Parent: [Steward HackNight design and plan](../maps/01-steward-hacknight-design-and-plan.md)
- Blocked-by: (none)

## Question

For Cognee 1.5.0.dev, and for the version pinned by the HackNight starter / [cognee-demo-slack](https://github.com/qdrant-labs/cognee-demo-slack), which write and read APIs should Steward use for Slack text, Remembered Facts, seed notes, and GitHub text that is **not** an HTTP URL?

Need live facts, not training-data guesses:

- Signatures and behaviour of `remember()`, `add()`, `cognify()`, `recall()` (dataset name, `session_id` / permanent memory, `top_k`).
- What happens if the string passed to `remember()` or `add()` is an `http(s)` URL versus plain text that *contains* a permalink.
- How to attach provenance so `/steward-ask` and Digest can cite a Slack permalink or a GitHub `html_url`. Prefixed text versus `external_metadata` versus another field.
- Any Slack-specific Cognee helper versus generic text ingest.
- Breaking differences between the demo pin and 1.5.0.dev that would change v1.

Cite `docs.cognee.ai` and the demo repo. Record the exact Cognee version the demo pins.

## Comments

### Resolution (charting session, 2026-08-14)

Permanent `cognee.remember` (no `session_id`) plus `cognee.recall` for Steward v1. Pin like the demo: `cognee[fastembed] @ git+https://github.com/topoteretes/cognee.git@dev` (`dev` tip `1.5.0.dev1`). Do not pass a bare `http(s)` URL as `data` (that scrapes). Put Slack/GitHub permalinks in `DataItem.external_metadata` and/or in the stored text body. Reserve `add`+`cognify` for staged bulk only. No Slack-specific remember helper in the demo; generic text ingest.

Note: [docs/wayfinder/research/cognee-remember-add-recall-apis.md](../research/cognee-remember-add-recall-apis.md)
