# Steward

Slack memory bot for Cognee + Qdrant HackNight. It remembers public-channel chat and facts you store, then answers with `SOURCED` or `NOT DETERMINABLE`.

Working copy: this repo. Event starter and rules: [Cognee_Qdrant_slack_bot](https://github.com/qdrant-labs/Cognee_Qdrant_slack_bot). Slack command shape: [cognee-demo-slack](https://github.com/qdrant-labs/cognee-demo-slack).

Slice 1 design: [`docs/superpowers/specs/2026-08-14-steward-slice1-design.md`](docs/superpowers/specs/2026-08-14-steward-slice1-design.md). Words: [`CONTEXT.md`](CONTEXT.md).

## Slice 1

- `/steward-ask` searches dataset `steward`
- `/steward-remember` stores a fact
- Public channels the bot has joined are ingested as they arrive
- A few seed notes cover questions Slack has not asked yet
- Vectors: Qdrant Cloud
- Not in slice 1: private-channel allowlists, holidays, tasks, digests, Masumi APIs

## Status

Docs only. App code is not in the repo yet.

## Secrets

Put Qdrant Cloud URL and API key in `.env` as `VECTOR_DB_URL` and `VECTOR_DB_KEY`. Do not commit `.env`. Do not paste keys into Slack or chat.

## Next

Review the slice 1 design. After that, implementation plan, then the FastAPI app, Slack manifest, and ngrok runbook.
