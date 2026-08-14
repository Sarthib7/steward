# Prototype: Digest message format (Slack)

Throwaway mock for [Prototype: digest message format](../tickets/08-prototype-digest-message-format.md).
Not app code. Fake but realistic `SOURCED` lines. No secrets.

Constraints baked in:

- Three parts per digest (daily and weekly): **TLDR** → **Summary** → **Attention / action required**
- Separate source blocks in Summary: Slack conversation vs GitHub product activity
- No Slack↔GitHub person linking / no cross-source Person Rollup
- Every bullet ends with a permalink, or the section says the window is empty / none
- Repos: `topoteretes/cognee`, `qdrant/qdrant`
- Placeholder channel: `#steward` (HackNight is chaotic; channel set still open)

Slack mrkdwn-ish. Cron posts the same body to a channel. Slash (`/steward-digest` or similar) can replay the same body as an ephemeral reply.

---

## Layout (both windows)

1. **TLDR** — few lines, only the important ones. Still `SOURCED` or omit the line.
2. **Summary / normal update** — fuller sourced bullets: Slack block, then GitHub blocks. Separate. No person cross-link.
3. **Attention / action required** — items that need eyes or action. `SOURCED` only. If none: say none, or omit the section (refuse-to-invent).

---

## 1. Daily Digest (example channel post)

Window: 2026-08-14 (demo TZ). Cron morning post to `#steward`.

```
*Steward daily digest — Thu 14 Aug*

*TLDR*
• Digest grounding rule locked in chat: bullets need a URL or they get dropped <https://hacknight.slack.com/archives/C0STEWARD/p1723626000987654|permalink>
• cognee: PR opened for OpenRouter model ids on the demo path <https://github.com/topoteretes/cognee/pull/4499|#4499>
• qdrant: v1.19.0 released <https://github.com/qdrant/qdrant/releases/tag/v1.19.0|v1.19.0>

*Summary*
*Slack · #steward*
• <@U0ABC111> asked how Cognee `remember` maps Slack permalinks into metadata <https://hacknight.slack.com/archives/C0STEWARD/p1723622400123456|permalink>
• Thread on digest grounding: bullets need a URL or they get dropped <https://hacknight.slack.com/archives/C0STEWARD/p1723626000987654|permalink>
• <@U0ABC222> shared a ngrok tunnel tip for the Friday demo window <https://hacknight.slack.com/archives/C0STEWARD/p1723630000555123|permalink>

*GitHub · topoteretes/cognee*
• PR opened: sync OpenRouter model ids for demo path <https://github.com/topoteretes/cognee/pull/4499|#4499>
• Issue updated: document `external_metadata` for Slack ingest <https://github.com/topoteretes/cognee/issues/4491|#4491>

*GitHub · qdrant/qdrant*
• Release published: v1.19.0 <https://github.com/qdrant/qdrant/releases/tag/v1.19.0|v1.19.0>
• PR merged: tighten payload indexing docs for cloud clusters <https://github.com/qdrant/qdrant/pull/7201|#7201>

*Attention / action required*
• Review open PR: OpenRouter model ids for demo path <https://github.com/topoteretes/cognee/pull/4499|#4499>
• Reply needed on grounding thread (URL-or-drop rule) <https://hacknight.slack.com/archives/C0STEWARD/p1723626000987654|permalink>

_Every line is SOURCED. Empty sections stay empty — Steward does not invent activity._
```

### Daily: empty Slack window (same shell)

If Slack had no remembered items in the window, omit invented chat. Keep GitHub if it has hits. TLDR and Attention stay `SOURCED`-only (or say none / omit).

```
*Steward daily digest — Thu 14 Aug*

*TLDR*
• cognee: issue updated on `external_metadata` for Slack ingest <https://github.com/topoteretes/cognee/issues/4491|#4491>

*Summary*
*Slack · #steward*
_No remembered channel activity in this window._

*GitHub · topoteretes/cognee*
• Issue updated: document `external_metadata` for Slack ingest <https://github.com/topoteretes/cognee/issues/4491|#4491>

*GitHub · qdrant/qdrant*
_No issue/PR/release updates in this window._

*Attention / action required*
_None in this window._
```

---

## 2. Weekly Digest (example channel post)

Window: ISO week 2026-W33 (Mon–Sun in digest TZ). Longer Summary OK; TLDR stays short. Still `SOURCED`-only.

```
*Steward weekly digest — week 33 (10–16 Aug)*

*TLDR*
• Kickoff: Steward slice = remember chats + ask + daily/weekly digests <https://hacknight.slack.com/archives/C0STEWARD/p1723240800111000|permalink>
• No Slack↔GitHub identity join for the hack (recorded in chat) <https://hacknight.slack.com/archives/C0STEWARD/p1723413600222000|permalink>
• qdrant: v1.19.0 released; cognee demo path PR still open <https://github.com/qdrant/qdrant/releases/tag/v1.19.0|v1.19.0> · <https://github.com/topoteretes/cognee/pull/4499|#4499>

*Summary*
*Slack · #steward*
• Kickoff: Steward slice = remember chats + ask + daily/weekly digests <https://hacknight.slack.com/archives/C0STEWARD/p1723240800111000|permalink>
• Decision recorded in chat: no Slack↔GitHub identity join for the hack <https://hacknight.slack.com/archives/C0STEWARD/p1723413600222000|permalink>
• <@U0ABC111> asked how Cognee `remember` maps Slack permalinks into metadata <https://hacknight.slack.com/archives/C0STEWARD/p1723622400123456|permalink>
• Thread on digest grounding: bullets need a URL or they get dropped <https://hacknight.slack.com/archives/C0STEWARD/p1723626000987654|permalink>
• <@U0ABC222> shared a ngrok tunnel tip for the Friday demo window <https://hacknight.slack.com/archives/C0STEWARD/p1723630000555123|permalink>

*GitHub · topoteretes/cognee*
• PR opened: sync OpenRouter model ids for demo path <https://github.com/topoteretes/cognee/pull/4499|#4499>
• Issue updated: document `external_metadata` for Slack ingest <https://github.com/topoteretes/cognee/issues/4491|#4491>
• PR closed: drop unused Anthropic-only demo branch <https://github.com/topoteretes/cognee/pull/4488|#4488>

*GitHub · qdrant/qdrant*
• Release published: v1.19.0 <https://github.com/qdrant/qdrant/releases/tag/v1.19.0|v1.19.0>
• PR merged: tighten payload indexing docs for cloud clusters <https://github.com/qdrant/qdrant/pull/7201|#7201>
• Issue opened: clarify cloud free-tier collection limits for hack demos <https://github.com/qdrant/qdrant/issues/7195|#7195>

*Attention / action required*
• Review open PR: OpenRouter model ids for demo path <https://github.com/topoteretes/cognee/pull/4499|#4499>
• Track open issue: cloud free-tier collection limits for hack demos <https://github.com/qdrant/qdrant/issues/7195|#7195>

_Weekly = same three-part shell + SOURCED rule, wider window. No cross-source person sections._
```

---

## 3. Delivery notes (slash vs cron)

| Path | Where it appears | Body |
| --- | --- | --- |
| Cron (APScheduler on laptop + ngrok) | Public post in digest channel (e.g. `#steward`) | Same text as above |
| Slash (`/steward-digest daily` / `weekly`, name TBD) | Ephemeral reply to the invoker | Same text as above |

Same body either way. Only visibility differs: channel post is shared; slash replay is private to the user who ran it.

Not in this mock (still fog / other tickets):

- Exact channel allowlist (`#steward` vs `#all-hacknight`)
- Whether weekly also has its own cron, or only daily cron + slash for both
- Digest timezone (Berlin vs UTC)
- Whether releases stay in the GitHub block by default
- Slack Block Kit (ticket says markdown sample only)
- How Steward picks TLDR vs Attention lines from the same SOURCED pool (heuristic later; this mock shows shape only)

---

## Fake IDs used here

- Slack channel id `C0STEWARD`, user ids `U0ABC111` / `U0ABC222`, message ts in permalinks: invented for shape only
- GitHub issue/PR numbers: illustrative; some urls match live shapes from research (`cognee` `#4499` / `#4491`, qdrant release `v1.19.0`); others are placeholders (`#7201`, `#7195`, `#4488`)
