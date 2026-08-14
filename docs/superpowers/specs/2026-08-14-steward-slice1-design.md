# Steward HackNight design (slice 1)

Date: 2026-08-14.
Status: approved (user reviewed 2026-08-14). Implementation plan may follow this file.
Repo: https://github.com/Sarthib7/steward

This file is the source of truth for the HackNight vertical slice. Vocabulary is in [`CONTEXT.md`](../../../CONTEXT.md). Decisions come from the Wayfinder map [`docs/wayfinder/maps/01-steward-hacknight-design-and-plan.md`](../../wayfinder/maps/01-steward-hacknight-design-and-plan.md). Citadel Archive and Scout are design references for labelled answers only. They are not runtime dependencies.

User approval on 2026-08-14 accepted the defaults in this file except OpenRouter model: use DeepSeek V4 Flash (OpenRouter id below), not `openrouter/openai/gpt-4o-mini`.

## Problem

HackNight judges a Slack bot that uses Cognee and Qdrant. Criteria (quoted in [`docs/wayfinder/research/hacknight-submission-constraints.md`](../../wayfinder/research/hacknight-submission-constraints.md) from the live Cognee_Qdrant_slack_bot README): the project runs (5), depth not breadth (0-5), complexity of stack (0-5), novel application (0-5). Quote from that README: "One integration that genuinely works end to end beats five that half-work."

Judging is the same Friday after 21:00, not Monday. Map: [Research: HackNight submission constraints](../../wayfinder/tickets/04-research-hacknight-submission-constraints.md).

The [starter](https://github.com/qdrant-labs/cognee-demo-slack) is `/cognee-ask` plus `/cognee-remember` with no channel ingest and no extra source. Official Cognee Slack is a different app (OAuth, `/cognee-link`, per-person memory). Map standing decision 6: base v1 on the cognee-demo-slack shape. Do not build full Cognee OAuth `/cognee-link` for v1.

HackNight README project ideas (research note): onboarding buddy (seed docs), Slack plus one more source, weekly digest. Steward's slice is one memory path: remember chats, ask about chat and GitHub product, daily Digest, weekly Digest.

Submission target: a folder named `YOURPROJECTNAME` on [qdrant-labs/Cognee_Qdrant_slack_bot](https://github.com/qdrant-labs/Cognee_Qdrant_slack_bot), plus the Google form with a public GitHub URL and proof of a run. How this working copy becomes that folder is out of scope for this spec (map Out of scope).

## Approaches considered

**1. Recommended: one memory path, two public GitHub repos, one digest generator (this spec).**
Public-channel ingest for all public channels the bot can join. `/steward-ask`, `/steward-remember`, and Digest replies only on an operator allowlist. Off-list slash gets a short ephemeral refuse. GitHub issues and pull requests from `topoteretes/cognee` and `qdrant/qdrant` enter the same dataset `steward`. Digest posts on a schedule (APScheduler in the FastAPI process on the laptop) and via `/steward-digest daily|weekly`. Format is TLDR, then Summary (Slack block then GitHub blocks), then Attention/action. Every bullet is `SOURCED` or the line is omitted. No Slack↔GitHub identity join. Linear is named, not built.

**2. Memory plus weekly digest only. GitHub and daily deferred.**
Fewer moving parts. Weaker than HackNight's "Slack + one more source" idea. Daily morning Digest and GitHub product activity drop out of the demo. Rejected.

**3. Memory plus GitHub org crawl plus identity join plus Linear stub plus cloud cron plus per-person DMs.**
Matches an older wish list. Fights "depth not breadth". Identity join and Linear are each their own product. Map closed identity join as out of scope. Rejected.

Slice 1 is approach 1. If GitHub tokens or rate limits block a pull, Slack memory and digest still run. GitHub sections are omitted for that pull.

## Decomposition

| Subsystem | HackNight slice 1 | Later / plugin |
|---|---|---|
| Ask, remember, public-channel ingest, seed docs, `SOURCED` / `NOT DETERMINABLE` | Ship | |
| Operator allowlist for ask, digest, and replies; join-all public for ingest | Ship | Private-channel ingest, DM ingest |
| GitHub issues and pull requests, two public repos | Ship | Org crawl, commit firehose, releases poll, GitHub App webhooks |
| Daily and weekly Digest from one generator (cron + slash replay) | Ship | Extra digest types |
| Person Rollup / Slack↔GitHub identity join | Out | Later, only with a new ticket |
| Linear | Named Source Plugin slot only | First post-hack plugin |
| Cognee OAuth, `/cognee-link` | Out | Possible later |
| Chonkie, Twelve Labs, Gemini embeddings | Out | Optional later |
| Holidays, tasks, calendar | Out | Later product |

Build order inside this one spec (one implementation plan, sequenced):

1. Ask, remember, channel ingest, seed, labelled answers, allowlist gate. Demo must work here even if later steps slip.
2. GitHub pull into the same dataset and ledger for both configured repos.
3. `/steward-digest` over the ledger in the approved three-part format.
4. APScheduler daily and weekly channel posts while the laptop process is up.

## Goals

- A judge in an allowlist channel can `/steward-remember` a fact, talk in that allowlist channel, seed a short doc, then `/steward-ask` and get a `SOURCED` or `NOT DETERMINABLE` reply. Ask may also quote GitHub product activity from the two configured repos. Off-allowlist public chat is ingested but is not quoted by ask.
- The same judge can `/steward-digest daily` and `/steward-digest weekly` and see TLDR, Summary (Slack then GitHub, separate), and Attention/action. Each bullet has a Slack permalink or a GitHub `html_url`, or the line is omitted.
- Vectors live on the operator's Qdrant Cloud cluster (operator-confirmed: cluster created; credentials stay on disk, not in git).
- Cognee LLM calls go through OpenRouter, not Anthropic. Map: [Task: confirm Qdrant Cloud cluster and Anthropic key](../../wayfinder/tickets/09-task-confirm-qdrant-and-anthropic.md).
- The project runs on the operator laptop with ngrok for Slack HTTPS. Map: [Grill: cron host for Monday demo](../../wayfinder/tickets/05-grill-cron-host-for-monday-demo.md). Ticket title still says Monday. Clock is Friday demo-day uptime.
- If GitHub auth or the GitHub API fails, Slack memory and digest still run. GitHub sections are omitted for that pull.

## Non-goals (slice 1)

- Linear, or any Source Plugin other than GitHub
- GitHub org-wide crawl, commit lists, webhook receiver, GitHub App
- GitHub releases poll (research listed it as optional extra; v1 is issues including PRs)
- Joining `slack:<user_id>` to `github:<login>` in code, or cross-source Person Rollup in Digests
- DMs to managers, absence lists, scores, "who is behind"
- Holidays, events, milestones, task assignment
- Private-channel ingest and DM ingest as memory
- Invite-only ingest (operator chose join-all public instead)
- Masumi Citadel HTTP, Scout code, production Central
- Per-user Cognee accounts, `/cognee-link`, Slack OAuth for Cognee
- Chonkie, Twelve Labs, Gemini multimodal embeddings
- LLM rewrite of digest bullets into themes or insights
- `INFERRED` label

## Architecture

One FastAPI process on port 8000. Shape copied from [cognee-demo-slack](https://github.com/qdrant-labs/cognee-demo-slack): signing-secret verification, 3s ack, real reply on `response_url`. Extra surface: Events API, bot token, join public channels, seed docs, GitHub poll, Ingest Ledger, labelled answers, digest, APScheduler, allowlist gate.

```
Slack slash    POST /api/v1/slack/commands
               allowlist check first
               /steward-ask       --> cognee.recall (dataset steward), drop off-allowlist Channel Memory hits
               /steward-remember  --> cognee.remember + ledger append
               /steward-digest    --> GitHub pull, then ledger window (Slack rows filtered to allowlist)

Slack events   POST /api/v1/slack/events
               message.channels   --> cognee.remember + ledger append (all joined public channels)

Startup        join public channels
               seed docs/         --> cognee.remember + ledger append
               GitHub pull once   --> cognee.remember + ledger append

GitHub HTTP    GET /repos/{owner}/{repo}/issues  (each of two repos)

Scheduler      APScheduler in this process
               daily at STEWARD_DIGEST_HOUR --> chat.postMessage to STEWARD_DIGEST_CHANNEL
               weekly on STEWARD_DIGEST_WEEKDAY at that hour --> same, weekly window

Cognee                                        --> Qdrant Cloud (vectors)
Ingest Ledger  .steward/ingest.jsonl          --> digest windows only
```

Cognee write API is permanent `remember()` without `session_id`. Research: [Research: Cognee remember, add, and recall APIs for Slack and custom text provenance](../../wayfinder/tickets/02-research-cognee-remember-add-recall-apis.md), note [`docs/wayfinder/research/cognee-remember-add-recall-apis.md`](../../wayfinder/research/cognee-remember-add-recall-apis.md). Pin like the demo: `cognee[fastembed] @ git+https://github.com/topoteretes/cognee.git@dev` (`dev` tip `1.5.0.dev1` at research time). `add()` is legacy ingestion-only. Slice 1 uses `remember()` for every write.

Do not pass a bare `http(s)` URL as `data` to `remember()`. Cognee fetches that string as a page (research note, Cognee remember docs). Fetch GitHub through the REST API, then pass formatted text. Put Slack permalinks and GitHub `html_url` in `DataItem.external_metadata` and also in the stored text body so recall can cite them without a join.

`ENABLE_BACKEND_ACCESS_CONTROL=false` matches the HackNight demo, because the Qdrant dataset handler in that demo does not support Cognee multi-tenant mode.

Starter also installs `cognee-community-vector-adapter-qdrant==0.4.0` with `--no-deps --ignore-requires-python` ([demo README](https://github.com/qdrant-labs/cognee-demo-slack)). Slice 1 follows that install shape.

## Slack surface

App display name: steward.

| Command | Behaviour |
|---|---|
| `/steward-ask <question>` | If channel is not on the allowlist: short ephemeral refuse. Else ephemeral ack, then Grounded Answer from dataset `steward` |
| `/steward-remember <fact>` | Same allowlist gate. Else ephemeral ack, then store in dataset `steward` and append the ledger |
| `/steward-digest daily` | Same allowlist gate. Else ephemeral ack, pull GitHub, then Digest for the calendar day |
| `/steward-digest weekly` | Same, for the current ISO week |
| `/steward-digest` with any other or empty text | If on allowlist: ephemeral usage hint. If off list: the same refuse as other commands |

Refuse copy (map: [Grill: which Slack channels count as major](../../wayfinder/tickets/07-grill-major-slack-channels.md)): short ephemeral, equivalent to `Steward isn't enabled here`.

Bot scopes (slice 1): `commands`, `chat:write`, `channels:read`, `channels:join`. Event: `message.channels`. Env: `SLACK_SIGNING_SECRET` and `SLACK_BOT_TOKEN` (join, events, `chat.postMessage`). The starter demo skipped the bot token because it only replied on `response_url`. This slice needs the token. No `channels:history` and no backfill. Memory starts at join time. No `users:read`: Slack user mentions in digest text render as `<@U123>`.

Allowlist (ticket 07):

- Ingest: list public channels at startup, join each, skip archived. If join fails, log and continue. Steward remembers messages after it has joined.
- Ask, digest, and Steward replies: only in operator-configured allowlist channels (`STEWARD_ALLOWLIST_CHANNELS`, comma-separated channel ids).
- Scheduled Digest posts to `STEWARD_DIGEST_CHANNEL`, which must be one of those allowlist ids. If it is missing or not on the list, skip the cron post, log once, and keep slash digest on allowlist channels.
- Digest Slack bullets and ask Channel Memory hits come from allowlist channels only. Off-allowlist public messages still land in Cognee and the ledger (ingest coverage), but ask drops those hits and digest omits those Slack rows.
- GitHub Memory, Remembered Facts, and Seed Docs stay visible to ask on an allowlist channel.

Skip ingest when: subtype is bot_message, text is empty, user is this bot, text starts with `/`. No extra length, thread, or reaction filter in slice 1 (map leftover; this is the design default).

Replies to slash commands stay ephemeral. Channel ingest is silent. A scheduled Digest uses `chat.postMessage` ([Slack method](https://docs.slack.dev/reference/methods/chat.postMessage), scope `chat:write`). Slash digest and cron digest use the same body. Cron is a channel post. Slash is ephemeral to the invoker. Prototype: [`docs/wayfinder/prototypes/digest-message-format.md`](../../wayfinder/prototypes/digest-message-format.md).

## Memory

One Cognee dataset named `steward`.

Write paths (all `cognee.remember(..., dataset_name="steward")`, no `session_id`):

1. `/steward-remember` with the Asker's text (allowlist only).
2. Public `message.channels` with a prefix that names channel, user, ts, permalink.
3. Seed files under `docs/seed/` once (CLI `python -m steward seed` or first-run flag).
4. GitHub issues and pull requests as formatted text (see GitHub ingest).

Each successful write also appends one Ingest Ledger row. Digest reads the ledger. `/steward-ask` does not.

Read path: `/steward-ask` → `cognee.recall(question, datasets=["steward"], top_k=5)` (demo `top_k`). Then drop Channel Memory hits whose channel id is not on the allowlist. Then apply Grounded Answer rules.

Grounded Answer rules (Scout product rule, reimplemented here):

- If a remaining hit addresses the question, emit `SOURCED` plus the permalink, GitHub `html_url`, or seed filename.
- If hits are nearest-neighbour noise, emit `NOT DETERMINABLE`.
- Do not use `INFERRED` in slice 1. No second LLM pass that rewrites Cognee's recall into new claims.

Provenance in the remembered text and in `DataItem.external_metadata`:

- Channel Memory: channel id, user id, ts, permalink if the API returns one, raw text.
- GitHub Memory: `html_url`, number, title, state, login, `updated_at`, repo `owner/name`.
- Remembered Fact: user id, command ts.
- Seed Doc: filename.

### LLM (OpenRouter)

Operator confirmed an OpenRouter API key, not Anthropic ([ticket 09](../../wayfinder/tickets/09-task-confirm-qdrant-and-anthropic.md)). Cognee docs recipe ([LLM providers](https://docs.cognee.ai/setup-configuration/llm-providers), OpenRouter section, fetched this session):

```
LLM_PROVIDER=custom
LLM_MODEL=openrouter/deepseek/deepseek-v4-flash-0731
LLM_ENDPOINT=https://openrouter.ai/api/v1
LLM_API_KEY=<OpenRouter key>
```

`LLM_PROVIDER=custom` is required for the `openrouter/` prefix. Cognee cannot infer that prefix as a native provider (same docs page). Slice 1 model is DeepSeek V4 Flash GA on OpenRouter: slug `deepseek/deepseek-v4-flash-0731`, Cognee env value `openrouter/deepseek/deepseek-v4-flash-0731` (prefix the OpenRouter slug with `openrouter/` per [Cognee LLM providers](https://docs.cognee.ai/setup-configuration/llm-providers)). Verified against OpenRouter model page [DeepSeek V4 Flash 0731](https://openrouter.ai/deepseek/deepseek-v4-flash-0731) and `GET https://openrouter.ai/api/v1/models` on 2026-08-14. Do not set Anthropic vars for this effort.

Embeddings follow the demo, unless they fail on the laptop: `EMBEDDING_PROVIDER=fastembed`, `EMBEDDING_MODEL=BAAI/bge-small-en-v1.5`, `EMBEDDING_DIMENSIONS=384`. Ticket 09 did not confirm fastembed on the demo machine. See Least confident decisions.

### Vectors (Qdrant Cloud)

Operator confirmed a Qdrant Cloud cluster exists (ticket 09, plus human confirmation this session that they created the cluster). Cluster setup reference: [Qdrant Cloud quick start](https://qdrant.tech/documentation/cloud-quickstart/). That page tells you to copy the cluster URL and API key when the cluster is created.

Cognee env (same names as the demo `.env.example`):

```
VECTOR_DB_PROVIDER=qdrant
VECTOR_DATASET_DATABASE_HANDLER=qdrant
VECTOR_DB_URL=<Qdrant Cloud cluster URL>
VECTOR_DB_KEY=<Qdrant Cloud API key>
ENABLE_BACKEND_ACCESS_CONTROL=false
```

Put `VECTOR_DB_URL` and `VECTOR_DB_KEY` in `.env`. Optional local file `steward_api_key.txt` is gitignored. Copy the key into `.env` yourself. Do not commit `.env` or the key file. Do not paste keys into Slack, chat, this spec, or tickets.

This session: `steward_api_key.txt` exists on disk and was never in `git ls-files`. After the gitignore update it is ignored. `.env` is ignored and was not present on disk at that check. This session did not open the key file and did not ping the cluster.

Secrets stay in `.env`. Never commit them.

## GitHub ingest

Two public repos (map: [Research: GitHub REST events for a public-repo activity digest](../../wayfinder/tickets/03-research-github-rest-events-for-digest.md)): `topoteretes/cognee` and `qdrant/qdrant`. Research note: [`docs/wayfinder/research/github-rest-events-for-digest.md`](../../wayfinder/research/github-rest-events-for-digest.md). Both repos were live-checked public.

Env: `GITHUB_REPOS=topoteretes/cognee,qdrant/qdrant` (comma list). If unset, use those two names. Optional `GITHUB_TOKEN` (classic or fine-grained with issues read). PAT preferred (5,000 req/hour). Unauthenticated (60 req/hour) is enough for a few GETs per two-repo digest. If the token is unset, poll unauthenticated. Do not fail Slack commands when GitHub is skipped.

API ([List repository issues](https://docs.github.com/en/rest/issues/issues?apiVersion=2022-11-28)):

```
GET /repos/{owner}/{repo}/issues?state=all&sort=updated&direction=desc&since=<ISO-8601>&per_page=100
```

GitHub returns issues and pull requests from this endpoint. Pull requests have a `pull_request` key. Slice 1 uses that one list per repo. No second commits endpoint. No releases endpoint in v1.

Cite `html_url` as the human `SOURCED` link. Do not cite the API `url`.

When: once at startup (`since` = now minus 7 days), and again at the start of every `/steward-digest` and every scheduled Digest (`since` = window start). No webhook. No 15-minute poll.

Digest grouping is by repo, not by GitHub login. Ask may still quote a login that appears in the remembered text. Map: [Grill: Slack to GitHub identity mapping for Person Rollup](../../wayfinder/tickets/06-grill-slack-github-identity-mapping.md).

Dedup: ledger key is `html_url` plus `updated_at`. Same URL with a new `updated_at` is a new remember. Unchanged rows are skipped. Include `updated_at` in the remembered text so an edit is not a silent no-op.

Cap: 100 items per repo per pull (one page). Do not follow `Link` for a second page in v1. Overflow is dropped. Log the cap.

Do not scrape `html_url` through Cognee URL ingest.

## Digests

One generator. `daily` and `weekly` only change the window. Approved shape: [Prototype: digest message format](../../wayfinder/tickets/08-prototype-digest-message-format.md), asset [`docs/wayfinder/prototypes/digest-message-format.md`](../../wayfinder/prototypes/digest-message-format.md).

Timezone: `STEWARD_DIGEST_TZ` (IANA name, default `Europe/Berlin`). HackNight is in Berlin. The live README does not name a TZ (research note). This default is a design-time pick.

- Daily window: today 00:00 in that timezone through now.
- Weekly window: Monday 00:00 of the current ISO week through now.

Scheduled posts: APScheduler inside FastAPI while the laptop process is on (ticket 05). Slack request URLs point at the ngrok HTTPS tunnel.

- Daily: at `STEWARD_DIGEST_HOUR` (default `8`) in that timezone, if today's daily Digest has not been posted, pull GitHub, build the daily Digest, `chat.postMessage` to `STEWARD_DIGEST_CHANNEL`, record the date in `.steward/last_daily_digest`.
- Weekly: on `STEWARD_DIGEST_WEEKDAY` (default `mon`) at the same hour, same pattern, record in `.steward/last_weekly_digest`.

Friday judging after 21:00 will not wait on Monday weekly cron. Slash `/steward-digest weekly` is the demo path for weekly. Daily cron only fires if the laptop is up at 08:00. Slash replay is the proof path for both windows.

Empty Slack or GitHub block: keep the heading and say the window is empty. Do not invent activity. Prototype empty-window copy: `_No remembered channel activity in this window._` and `_None in this window._` for Attention.

Format is a template, not an LLM rewrite. Each bullet is `SOURCED` and ends with the permalink or GitHub `html_url`. Cap 20 bullets per Summary origin (one Slack allowlist channel block, plus one GitHub block per repo) and 40 Summary bullets total. If the ledger has more, last line is `N more in ledger, not shown.`

How the three parts are filled from the same `SOURCED` pool (design default; prototype left the heuristic open):

1. Summary: all sourced ledger rows in the window. Slack block: allowlist Channel Memory and Remembered Facts, grouped by channel (channel name if known, else id). GitHub blocks: one per repo, issues and PRs only. No person cross-link.
2. TLDR: up to five Summary bullets with the latest `occurred_at` / `updated_at`. Still `SOURCED`. If the pool is empty, omit TLDR lines rather than invent.
3. Attention / action required: GitHub issues and PRs in the window whose `state` is `open`. If none: keep the heading and write `_None in this window._`

Seed Docs are for `/steward-ask`. Digest does not list them.

Shell (mrkdwn, matches the prototype):

```
*Steward daily digest: <day>*

*TLDR*
• <sourced line> (<permalink or html_url>)

*Summary*
*Slack · #<channel>*
• <sourced line> (<permalink>)

*GitHub · topoteretes/cognee*
• <sourced line> (<html_url>)

*GitHub · qdrant/qdrant*
• <sourced line> (<html_url>)

*Attention / action required*
• <open issue or PR> (<html_url>)
```

Weekly uses the same three parts and a wider window.

## Source Plugin slot (Linear, later)

A later plugin is a function that, given a `since` timestamp, returns a list of items with: origin name, occurred_at, permalink, text, and optional repo or channel id. Slice 1 GitHub ingest is that shape without a Person Key join. Linear is the first planned plugin after the hack. Do not add a Linear client, empty module, or stub package in slice 1.

## Error handling

- Invalid Slack signature → HTTP 401
- Off-allowlist slash → ephemeral refuse, no Cognee call
- Slash command with empty text (ask/remember) or bad digest arg, on allowlist → ephemeral usage hint
- Cognee/Qdrant failure after ack → ephemeral "Something went wrong" plus server log. No stack traces in Slack.
- Slack 3s deadline: always ack first when `response_url` is present (after a cheap allowlist check)
- Url verification for Events API: echo `challenge`
- Join-all partial failure: Steward still serves ask/remember/digest; missing channels stay uningested
- Slack rate limit on `channels.join`: backoff, skip the failed channel, continue the list
- GitHub 401/403/404 → log, skip GitHub for that pull, Slack digest still builds
- GitHub rate limit → skip GitHub for that pull, log reset if the header is present
- Missing `GITHUB_TOKEN` → unauthenticated public GETs; if those fail, skip GitHub
- `chat.postMessage` failure for scheduled digest → log, do not retry in a tight loop; slash digest still works
- Ledger write failure after Cognee success → log; ask still works; digest may miss that row (see Least confident decisions)

## Testing

- Signature tests (valid, invalid, expired) copied from the demo's `test_app.py`
- Allowlist gate: on-list commands proceed; off-list commands refuse; Cognee not called
- Command routing with Cognee mocked
- Event ingest skip rules with Cognee mocked
- Ask hit filter: off-allowlist Channel Memory dropped; GitHub and seed hits kept
- GitHub mapper: issue vs pull request (`pull_request` key), two repos from `GITHUB_REPOS`, skip or unauth when token missing (HTTP mocked)
- Digest window: calendar day and ISO week in a fixed timezone with a fake ledger
- Digest parts: TLDR cap, Summary source split, Attention open-only, empty-window copy
- Bullet cap
- No live Slack, live GitHub, or live Qdrant in unit tests

Live check after deploy (allowlist channel): remember a fact, post a public message, ask both back, ask something never stored and expect `NOT DETERMINABLE`, run `/steward-digest daily` and expect Slack and GitHub blocks without person merge. Confirm one recent issue or PR on `topoteretes/cognee` or `qdrant/qdrant` appears under the matching GitHub heading. From a non-allowlist public channel, `/steward-ask` should refuse.

## Demo script (Friday after 21:00)

1. Laptop FastAPI up. ngrok tunnel matches Slack request URLs.
2. In an allowlist channel: `/steward-remember The demo bot is named Steward and stores vectors in Qdrant Cloud`
3. In the same allowlist channel, from at least one human: a sentence Steward should quote later.
4. `/steward-ask where are Steward's vectors stored?` → `SOURCED`
5. `/steward-ask` a question only the channel message (or a seed doc) answers → `SOURCED`
6. `/steward-ask` a question about recent Cognee or Qdrant GitHub activity that keyword search of Slack cannot answer → `SOURCED` with `html_url` (form ranks this kind of question)
7. `/steward-digest daily` and `/steward-digest weekly` → three-part body, Slack then GitHub, no person merge
8. `/steward-ask who is the CEO of a company we never mentioned?` → `NOT DETERMINABLE`
9. Optional: from a non-allowlist channel, `/steward-ask` → ephemeral refuse

Pitch line: Steward is company Slack memory for the hack. It remembers chats. People ask it about chat and about Cognee/Qdrant GitHub product activity. It will not invent. The Digest is the same memory, windowed, Slack and GitHub kept separate.

## Out of this repo

Scout (`/Users/sarthiborkar/masumi/Scout`) and Citadel Archive stay where they are. Do not vendor them. If a rule is useful, write it again in this repo in Steward's words.

Steward product facts in this file come from this repo, the Wayfinder map and tickets, the research notes under `docs/wayfinder/research/`, the digest prototype, HackNight README quotes in the research note, Cognee docs, GitHub REST docs, Slack `chat.postMessage` docs, Qdrant Cloud quick start, and Cognee LLM provider docs. They do not come from the Citadel vault.

## Defaults the user can override before the plan

These are chosen so the spec has no open placeholders. Change them in review if needed.

1. GitHub coverage: `GITHUB_REPOS=topoteretes/cognee,qdrant/qdrant`, issues (PRs included), no releases poll.
2. Digest timezone: `Europe/Berlin`. Daily and weekly both have APScheduler jobs. Slash replay is the Friday proof path.
3. Allowlist: `STEWARD_ALLOWLIST_CHANNELS` plus `STEWARD_DIGEST_CHANNEL` as one of those ids.
4. OpenRouter model: `openrouter/deepseek/deepseek-v4-flash-0731` (DeepSeek V4 Flash GA; user-approved 2026-08-14).
5. Message ingest filter: skip bots, empty text, this bot, slash echoes. No length/thread/reaction extra filter.
6. TLDR: five newest Summary bullets. Attention: open GitHub issues/PRs in the window.

## Least confident decisions

1. Join-all public channels at startup may hit Slack rate limits or workspace policy on HackNight. Design default: backoff, skip the failed channel, continue. Same ingest code, smaller coverage.

2. `cognee.remember` must keep permalinks in the string so recall can cite them. `DataItem.external_metadata` exists but does not automatically become graph structure (research note, Cognee add/datasets docs). Slice 1 writes both. Verify against Cognee `@dev` (`1.5.0.dev1` at research time) on first implementation.

3. No history backfill. A channel that existed before install has empty memory until new messages arrive. That may look like a bug in the demo.

4. Fastembed + OpenRouter is the intended pair. Ticket 09 did not confirm fastembed on the demo machine. If the laptop cannot install that Cognee pin, swap only embedding env vars, not the architecture.

5. Dataset name `steward` vs the demo's `slack`. Using `steward` avoids colliding with anyone else running the official Cognee app in the same workspace. Cognee datasets are local to this process. Slack command names still must be unique in the workspace.

6. Ingest Ledger can drift from Cognee if one write succeeds and the other fails. Ask and digest then disagree. Slice 1 logs that case and does not build a two-phase commit.

7. Scheduled 08:00 posts will not fire during a Friday evening judging window unless the laptop was already up at 08:00. Slash commands are the demo path. The scheduler is extra, not the proof.

8. Off-allowlist Channel Memory still enters Cognee. Ask drops those hits after recall. Nearest-neighbour noise from off-list channels can still crowd `top_k`. If that shows up in the demo, stop remembering off-list text (keep join-all for later) rather than adding a second dataset.

9. Digest TZ default `Europe/Berlin` is inferred from the event venue. The live README does not name a TZ (research note).

10. Skipping GitHub releases keeps v1 to one endpoint per repo (ticket 03). The approved prototype mock included a release line as an example. If the pitch wants a version milestone, add one `GET .../releases` page per repo later; do not block this spec on it.

11. Weekly cron weekday default `mon` will not run before Friday 21:00. Slash weekly is required for the demo either way.

12. TLDR as "five newest" and Attention as "open GitHub items" are deterministic so slice 1 needs no digest LLM. They may look dull next to the prototype's editorial mock.

13. OpenRouter DeepSeek V4 Flash has three live ids (verified 2026-08-14 via OpenRouter models API): `deepseek/deepseek-v4-flash` (0423), `deepseek/deepseek-v4-flash-0731` (GA), and `~deepseek/deepseek-v4-flash-latest` (floating). User asked for DeepSeek V4 Flash without a date. Spec pins Cognee `LLM_MODEL=openrouter/deepseek/deepseek-v4-flash-0731` as the GA Flash release. If live calls fail or the operator wants the undated alias, swap only that env value.

14. Recall `top_k=5` matches the demo. Allowlist filtering happens after recall, so five hits may all be off-list in a busy workspace. If live ask goes empty, raise `top_k` before changing architecture.
