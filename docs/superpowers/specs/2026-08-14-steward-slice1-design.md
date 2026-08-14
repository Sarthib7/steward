# Steward slice 1 design

Date: 2026-08-14.
Status: draft, awaiting user review before an implementation plan.
Repo: https://github.com/Sarthib7/steward

This document is the source of truth for the first vertical slice. Vocabulary is in [`CONTEXT.md`](../../../CONTEXT.md). Citadel Archive and Scout are design references only. They are not runtime dependencies.

## Problem

HackNight judges a Slack bot that uses Cognee and Qdrant, runs on Monday, and is deep on one path. The [starter](https://github.com/qdrant-labs/cognee-demo-slack) is `/cognee-ask` plus `/cognee-remember` with no channel ingest. Steward adds public-channel memory and a few seeded docs, then answers with labelled claims.

Submission target: a folder in [qdrant-labs/Cognee_Qdrant_slack_bot](https://github.com/qdrant-labs/Cognee_Qdrant_slack_bot). This GitHub repo is the working copy.

## Goals

- A judge in the HackNight Slack can `/steward-remember` a fact, talk in a public channel, seed a short doc, then `/steward-ask` and get a `SOURCED` or `NOT DETERMINABLE` reply.
- Vectors live on the operator's Qdrant Cloud cluster.
- The project runs locally with ngrok for Slack's HTTPS requirement.

## Non-goals (slice 1)

- Holidays, events, milestones, task assignment, weekly digest
- Private-channel allowlists (planned later)
- Masumi Citadel HTTP, Scout code, production Central
- Per-user Cognee accounts, `/cognee-link`, OAuth
- Chonkie, Twelve Labs, Gemini multimodal embeddings
- DMs as memory (slash commands may still be invoked from a DM; ingest is public channels only)

## Architecture

One FastAPI process on port 8000.

```
Slack  --slash-->  POST /api/v1/slack/commands  -->  cognee.remember / cognee.recall
Slack  --event-->  POST /api/v1/slack/events    -->  cognee.add (public channel messages)
CLI / startup      seed docs/                   -->  cognee.add
Cognee                                          -->  Qdrant Cloud (vectors)
```

Shape copied from [cognee-demo-slack](https://github.com/qdrant-labs/cognee-demo-slack): signing-secret verification, 3s ack, real reply on `response_url`. Extra surface: Events API, bot token, join public channels, seed docs, labelled answers.

## Slack surface

App display name: steward.

| Command | Behaviour |
|---|---|
| `/steward-ask <question>` | Ephemeral ack, then Grounded Answer from dataset `steward` |
| `/steward-remember <fact>` | Ephemeral ack, then store in dataset `steward` |

Bot scopes (slice 1): `commands`, `chat:write`, `channels:read`, `channels:join`. Event: `message.channels`. No `channels:history` and no backfill. Memory starts at join time.

Startup: list public channels, join each, skip archived. If join fails, log and continue. Steward only remembers messages after it has joined.

Skip ingest when: subtype is bot_message, text is empty, user is this bot, text starts with `/`.

Provenance stored with each Channel Memory: channel id, user id, ts, permalink if the API returns one, raw text.

Replies to slash commands stay ephemeral. Channel ingest is silent (no reaction, no ack in-channel).

## Memory

One Cognee dataset named `steward`. `ENABLE_BACKEND_ACCESS_CONTROL=false` matches the HackNight demo, because the Qdrant dataset handler in that demo does not support Cognee multi-tenant mode.

Write paths:

1. `/steward-remember` → `cognee.remember(text, dataset_name="steward")`
2. Public `message.channels` → `cognee.add(...)` into the same dataset, tagged as Slack-origin
3. Seed files under `docs/seed/` → `cognee.add(...)` once (CLI `python -m steward seed` or first-run flag)

Read path: `/steward-ask` → `cognee.recall(question, datasets=["steward"], top_k=5)`.

Grounded Answer rules (copied from Scout's product rule, reimplemented here):

- If a hit addresses the question, emit `SOURCED` plus the permalink or seed filename.
- If hits are nearest-neighbour noise, emit `NOT DETERMINABLE`.
- Do not use `INFERRED` in slice 1. No second LLM pass that rewrites Cognee's recall into new claims.

LLM and embeddings follow the demo defaults unless they fail in this environment: Anthropic for Cognee's LLM, fastembed `BAAI/bge-small-en-v1.5` (384 dims) locally so embeddings do not hit OpenAI. Vector store:

```
VECTOR_DB_PROVIDER=qdrant
VECTOR_DATASET_DATABASE_HANDLER=qdrant
VECTOR_DB_URL=<Qdrant Cloud URL>
VECTOR_DB_KEY=<Qdrant Cloud API key>
```

Secrets stay in `.env`. Never commit them. Never paste them into chat.

## Error handling

- Invalid Slack signature → HTTP 401
- Slash command with empty text → ephemeral usage hint
- Cognee/Qdrant failure after ack → ephemeral "Something went wrong" plus server log. No stack traces in Slack.
- Slack 3s deadline: always ack first when `response_url` is present
- Url verification for Events API: echo `challenge`
- Join-all partial failure: Steward still serves ask/remember; missing channels stay uningested

## Testing

- Signature tests (valid, invalid, expired) copied from the demo's `test_app.py`
- Command routing with Cognee mocked
- Event ingest skip rules with Cognee mocked
- No live Slack or live Qdrant in unit tests

Live check after deploy: remember a fact, post a public message, ask both back, ask something never stored and expect `NOT DETERMINABLE`.

## Demo script (Monday)

1. `/steward-remember The demo bot is named Steward and stores vectors in Qdrant Cloud`
2. In a public channel: `Onboarding: new joiners ask Steward, not three people.`
3. `/steward-ask where are Steward's vectors stored?` → `SOURCED`
4. `/steward-ask what should a new joiner do instead of DMing people?` → `SOURCED` from the channel message or seed doc
5. `/steward-ask who is the CEO of a company we never mentioned?` → `NOT DETERMINABLE`

## Out of this repo

Scout (`/Users/sarthiborkar/masumi/Scout`) and Citadel Archive stay where they are. Do not vendor them. If a rule is useful, write it again in this repo in Steward's words.

## Least confident decisions

1. Join-all public channels at startup may hit Slack rate limits or workspace policy on HackNight. If join-all is refused, fall back to channels the operator invites the bot into. Same ingest code, smaller coverage.
2. `cognee.add` vs `cognee.remember` for channel messages. The demo uses `remember` for slash facts. Channel ingest may need `add` so provenance fields survive. Verify against Cognee 1.5.0.dev on first implementation, not from memory.
3. No history backfill. A channel that existed before install has empty memory until new messages arrive. That may look like a bug in the demo. Backfill is a follow-up if Monday needs old messages.
4. Fastembed + Anthropic is the demo's working pair. If the operator's machine cannot install that Cognee pin, swap only the embedding/LLM env vars, not the architecture.
5. Dataset name `steward` vs the demo's `slack`. Using `steward` avoids colliding with anyone else running the official Cognee app in the same workspace. Cognee datasets are local to this process, so collision is process-level, not Slack-level. Slack command names still must be unique in the workspace.
