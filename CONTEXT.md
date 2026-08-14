# Steward

Steward is a Slack memory agent for HackNight. It remembers public-channel chat and a handful of seeded docs, then answers questions from that memory. The vector store is Qdrant Cloud. The memory engine is Cognee.

This is a new product. It does not call Masumi Citadel. It does not import Scout. Those two codebases are design references only: labelled answers, refuse to invent, one dataset as the quoteable memory.

## Language

**Steward**:
The Slack agent. It ingests public-channel messages, stores facts, and answers questions from Cognee memory on Qdrant Cloud.
_Avoid_: Scout, Citadel, company bot, chief of staff platform

**Org Space**:
The Slack workspace where the app is installed. Slice 1 listens to public channels Steward has joined. Private-channel allowlists are out of slice 1.
_Avoid_: Masumi Slack, company Slack

**Asker**:
Anyone who runs `/steward-ask` in that workspace.
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
A short note ingested with `cognee.add()` so onboarding questions have an answer that did not come from Slack.
_Avoid_: company handbook, Citadel Central

**Dataset `steward`**:
The one Cognee dataset this agent reads and writes. All quotes come from it.
_Avoid_: Central, seat:scout, per-user datasets

## Relationships

- Steward quotes dataset `steward` only. It never presents a nearest-neighbour hit as an answer if the hit does not address the question.
- Channel Memory and Remembered Facts and Seed Docs share that dataset so `/steward-ask` can mix Slack chat with seeded notes.
- Slack Events only fire for channels the bot has joined. Steward lists public channels at startup and joins them.
- Steward skips bot posts, empty text, and slash-command echoes.
- Replies to slash commands are ephemeral. Ingest of public messages is silent.
- Qdrant Cloud holds vectors. Cognee owns the graph and the remember/recall API.
- Citadel and Scout are not runtime dependencies.

## Example Dialogue

> **Dev:** "Can Steward search Masumi Central?"
> **Domain expert:** "No. Slice 1 searches dataset `steward` on this Cognee + Qdrant Cloud stack."
>
> **Dev:** "A public channel said the demo is at 9pm. Can Steward quote that?"
> **Domain expert:** "Yes, as `SOURCED`, with the Slack permalink, if that message was ingested."
>
> **Dev:** "Someone asks who the CEO of Qdrant is, and nothing in the dataset says."
> **Domain expert:** "Steward says `NOT DETERMINABLE`. It does not guess from training data."

## Flagged Ambiguities

- "Public groups" means Slack public channels, not Slack Connect or private channels.
- "Refer to Citadel and Scout" means copy the answer-labelling rules, not call their APIs.
- "Chief of staff" is later product intent. Slice 1 is ask, remember, and channel ingest.
