# Steward

Slack memory agent for Cognee + Qdrant HackNight.

Code: https://github.com/Sarthib7/steward

Steward stores public-channel chat, GitHub issues and PRs from `topoteretes/cognee` and `qdrant/qdrant`, and facts you save on purpose. It answers from dataset `steward` on Qdrant Cloud. Cognee owns remember/recall. LLM calls go through OpenRouter (DeepSeek). Every claim is `SOURCED` or `NOT DETERMINABLE`.

This process is FastAPI. Cognee is a library in the same process. Skip the Cognee frontend, `cognee/api/client.py`, and Cognee OAuth. This repo does not import Scout or Citadel.

Words: [`CONTEXT.md`](CONTEXT.md). Design: [`docs/superpowers/specs/2026-08-14-steward-slice1-design.md`](docs/superpowers/specs/2026-08-14-steward-slice1-design.md).

## Commands

| Command | What it does |
|---|---|
| `/steward-ask <question>` | Grounded Answer from Cognee recall |
| `/steward-remember <fact>` | Store a Remembered Fact in dataset `steward` |
| `/steward-digest daily\|weekly` | Digest of the Ingest Ledger for today or the current ISO week |

Ask, remember, digest, and Steward replies run only in allowlist channels (`STEWARD_ALLOWLIST_CHANNELS`). Off-list slash gets the ephemeral line `Steward isn't enabled here`. Ingest can still join other public channels. Private channels and DMs are not memory.

## Talk in Slack

In an allowlist channel, ask with `/steward-ask <question>` or `@Steward <question>`.

Example: `@Steward whats going on in the #all-hacknight`

`NOT DETERMINABLE` means dataset `steward` has no sourced hit. The bot is not in that channel, there is no ingest yet, or the question is not in memory. That reply is empty Channel Memory. It is not a Slack timeout.

To fill memory, run `/invite @Steward` in `#all-hacknight`, then `/steward-remember`, then ask again.

## Run locally

Copy the env template. Never commit `.env` or key files.

```bash
cp .env.example .env
```

Set `VECTOR_DB_URL` and `VECTOR_DB_KEY` (Qdrant Cloud cluster URL and API key), `LLM_API_KEY` (OpenRouter), `SLACK_SIGNING_SECRET`, `SLACK_BOT_TOKEN` (`xoxb-`), `STEWARD_ALLOWLIST_CHANNELS`, and `STEWARD_DIGEST_CHANNEL`. `LLM_MODEL` in the example is OpenRouter DeepSeek.

`VECTOR_DB_PROVIDER=qdrant` is not enough. Qdrant is a community adapter. Steward calls `cognee_community_vector_adapter_qdrant.register()` at process start. Skip that call and Cognee raises `OSError: Unsupported vector database provider: qdrant`.

Steward is HTTP Events API plus ngrok. Leave Socket Mode off. Do not set `SLACK_APP_TOKEN` (`xapp-`). Slack POSTs slash commands to `/api/v1/slack/commands` and events to `/api/v1/slack/events`.

Install, optional seed, then boot on port 8000:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uv pip install "cognee[fastembed] @ git+https://github.com/topoteretes/cognee.git@dev"
uv pip install cognee-community-vector-adapter-qdrant==0.4.0 --no-deps --ignore-requires-python
python -m steward
uvicorn steward.app:app --host 0.0.0.0 --port 8000
```

`pip` works in place of `uv pip`. The adapter pins a different Cognee version, so install it with `--no-deps`. `--ignore-requires-python` is for Python 3.14. `python -m steward` seeds `docs/seed`. `register()` also runs when uvicorn starts.

Tunnel Slack HTTPS:

```bash
ngrok http 8000
```

Commands: `https://<ngrok>/api/v1/slack/commands`. Events: `https://<ngrok>/api/v1/slack/events`.

Create the Slack app from `slack-manifest.json` at [api.slack.com/apps](https://api.slack.com/apps) (Create New App, From an app manifest). Paste the ngrok URLs, then install to the workspace. Reinstall after you add or change slash commands or bot scopes (`channels:read`, `channels:join`, `channels:history`). Copy the signing secret and bot token into `.env` if Slack rotated them.

## Tests

```bash
STEWARD_SKIP_STARTUP=1 pytest -q
```

Unit tests mock Cognee and `register()`. They do not need Qdrant, Slack, or an LLM key.
