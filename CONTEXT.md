# Steward

Steward is a Slack memory agent for HackNight. It remembers public-channel chat, GitHub product activity from `topoteretes/cognee` and `qdrant/qdrant`, and a handful of seeded docs, then answers questions from that memory. It can also post a Digest of the same writes. The vector store is Qdrant Cloud. The memory engine is Cognee. The Cognee LLM path uses OpenRouter.

This is a new product. It does not call Masumi Citadel. It does not import Scout. Those two codebases are design references only: labelled answers, refuse to invent, one dataset as the quoteable memory.

## Language

**Steward**:
The Slack agent. It ingests public-channel messages and two public GitHub repos, stores facts, answers `/steward-ask` from Cognee memory on Qdrant Cloud, and builds a Digest from the Ingest Ledger. Ask, digest, and replies run only on an operator allowlist.
_Avoid_: Scout, Citadel, company bot, chief of staff platform

**Org Space**:
The Slack workspace where the app is installed. Slice 1 joins public channels for ingest. Ask, digest, and replies run only in allowlist channels. Private channels and DMs are not memory.
_Avoid_: Masumi Slack, company Slack

**Allowlist**:
Operator-configured public channel ids where `/steward-ask`, `/steward-remember`, `/steward-digest`, and Steward replies run. Off-list slash gets a short ephemeral refuse. Ingest may still join other public channels.
_Avoid_: private-channel allowlist, invite-only ingest

**Asker**:
Anyone who runs `/steward-ask` or `/steward-digest` in an allowlist channel.
_Avoid_: employee, teammate, licensed user

**Grounded Answer**:
A reply where every claim is `SOURCED` (a retrieved hit, with provenance) or `NOT DETERMINABLE` (memory does not answer). Steward does not fill gaps.
_Avoid_: chatbot reply, summary, insight

**Remembered Fact**:
Text stored on purpose with `/steward-remember`. It lands in the same dataset as channel messages.
_Avoid_: Central, promotion, vault write

**Channel Memory**:
A public-channel message Steward ingested: text, user, channel, timestamp, permalink.
_Avoid_: surveillance, transcript dump, full workspace history

**Seed Doc**:
A short note ingested with `cognee.remember()` so onboarding questions have an answer that did not come from Slack.
_Avoid_: company handbook, Citadel Central

**GitHub Memory**:
An issue or pull request from `topoteretes/cognee` or `qdrant/qdrant` stored in dataset `steward`. Digest treats this as product activity per repo, not as a person record.
_Avoid_: org-wide crawl, commit firehose, GitHub App, Slack-to-GitHub identity join

**Ingest Ledger**:
Append-only JSONL of provenance rows written on every successful remember. Digest windows this file. `/steward-ask` still uses Cognee recall, not the ledger.
_Avoid_: second vector store, analytics warehouse

**Digest**:
A Grounded Answer for a time window, from the Ingest Ledger. Shape: TLDR, then Summary (Slack block, then GitHub blocks), then Attention/action. Daily is the current calendar day in `STEWARD_DIGEST_TZ`. Weekly is the current ISO week in that timezone. Every bullet is `SOURCED`, or that part stays empty.
_Avoid_: insight, recap, employee report, performance review, Person Rollup

**Source Plugin**:
A pull-since contract: origin, occurred_at, permalink, text. GitHub is the slice 1 implementation. Linear is named later, not built.
_Avoid_: marketplace, MCP host, subagent swarm

**Dataset `steward`**:
The one Cognee dataset this agent reads and writes. All quotes come from it.
_Avoid_: Central, seat:scout, per-user datasets

## Relationships

- Steward quotes dataset `steward` only. It never presents a nearest-neighbour hit as an answer if the hit does not address the question.
- Channel Memory, Remembered Facts, Seed Docs, and GitHub Memory share that dataset so `/steward-ask` can mix Slack chat with GitHub and seeded notes.
- Ask on an allowlist channel drops Channel Memory hits from off-list channels. GitHub Memory, Remembered Facts, and Seed Docs stay in play.
- Digest reads the Ingest Ledger. Slack rows in the Digest come from allowlist channels. GitHub rows are per repo. `/steward-ask` reads Cognee recall. They share writes, not the read path.
- Slice 1 does not join Slack users to GitHub logins. Digest does not group by person.
- A later Source Plugin (Linear) must return the same item shape as GitHub ingest. Slice 1 does not implement Linear.
- Slack Events only fire for channels the bot has joined. Steward lists public channels at startup and joins them.
- Steward skips bot posts, empty text, and slash-command echoes.
- Replies to slash commands are ephemeral. Ingest of public messages is silent. A scheduled Digest may post to `STEWARD_DIGEST_CHANNEL` when that channel is on the allowlist.
- Qdrant Cloud holds vectors. Cognee owns the graph and the remember/recall API. LLM calls go through OpenRouter.
- Citadel and Scout are not runtime dependencies.

## Example Dialogue

> **Dev:** "Can Steward search Masumi Central?"
> **Domain expert:** "No. Slice 1 searches dataset `steward` on this Cognee + Qdrant Cloud stack."
>
> **Dev:** "A public channel said the demo is at 9pm. Can Steward quote that?"
> **Domain expert:** "Yes, as `SOURCED`, with the Slack permalink, if that message was ingested. `/steward-ask` must run in an allowlist channel."
>
> **Dev:** "Someone asks who the CEO of Qdrant is, and nothing in the dataset says."
> **Domain expert:** "Steward says `NOT DETERMINABLE`. It does not guess from training data."
>
> **Dev:** "Can Steward post who slacked off this week?"
> **Domain expert:** "No. Digest lists `SOURCED` Slack conversation and GitHub product activity. It does not score people or join Slack to GitHub."

## Flagged Ambiguities

- "Public groups" means Slack public channels, not Slack Connect or private channels.
- "Refer to Citadel and Scout" means copy the answer-labelling rules, not call their APIs.
- "Keep an eye on each employee" is out of this slice. There is no Person Rollup and no Slack-to-GitHub identity map. Avoid the word employee in product copy.
- "Chief of staff" is pitch language. Slice 1 ships ask, remember, channel ingest, GitHub Memory, and Digest. Task assign, holidays, Linear, and private channels stay later.
- "Daily morning summary" means `/steward-digest daily` plus an APScheduler channel post if the laptop process is up. Judging is Friday after 21:00. The slash command is the demo path.
- "Anthropic key" in older notes is wrong for this effort. Cognee LLM is OpenRouter.
