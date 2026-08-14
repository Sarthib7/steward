# Steward HackNight design and plan

- Status: open
- Labels: `wayfinder:map`
- Assignee: (unclaimed)
- Parent: (none)
- Blocked-by: (none)

## Destination

A HackNight-ready design and implementation plan for Steward: Memory (ask, remember, channel ingest), GitHub activity in that memory, daily morning Digest and weekly Digest, then hand off to build. This map plans. It does not ship app code.

## Notes

Domain: Slack company steward for HackNight (Cognee memory, Qdrant vectors). Ubiquitous language is in [`CONTEXT.md`](../../../CONTEXT.md). Prior art to revise after this map clears: [`docs/superpowers/specs/2026-08-14-steward-slice1-design.md`](../../superpowers/specs/2026-08-14-steward-slice1-design.md). That draft is not final truth.

Skills after the map is clear: `superpowers:brainstorming`, then `superpowers:writing-plans`. While planning and later building: `ponytail`. Every session: read `CONTEXT.md` first.

Prefer depth over breadth. HackNight judging rewards one path that works end to end.

Refer to tickets by **name** (title), not bare numbers or ids.

### Standing decisions from charting grilling

These came from grilling before this map existed. They are constraints, not closed tickets. Closed tickets on this map live under Decisions so far.

1. Demo must prove Memory (ask, remember, channel ingest), GitHub activity in that memory, daily morning Digest, and weekly Digest.
2. **Superseded for HackNight** (was: Person Rollup with org activity rollup **and** per-person sections in Digests, watching Cognee/Qdrant GitHubs plus major Slack messages). That charting constraint assumed Slack↔GitHub person linking or dual-key per-person sections. [Grill: Slack to GitHub identity mapping for Person Rollup](../tickets/06-grill-slack-github-identity-mapping.md) closed it: **no** identity mapping; Digests treat sources separately (Slack conversation / Channel Memory vs GitHub product-activity summary for configured public repos). Cross-source Person Rollup is Out of scope for this HackNight slice. Not an HR surveillance product (unchanged).
3. Digest delivery: scheduled cron posts to a channel, and a slash (`/steward-digest` or similar) to regenerate or replay.
4. GitHub auth for the hack: PAT, or public unauthenticated rate-limited access, for the Cognee and Qdrant **public** repos.
5. Digest grounding: a bullet is `SOURCED` (permalink or commit URL) or it is omitted. Do not invent. Same trust rule as the ask path.
6. Stack: Slack agent, Cognee brain, Qdrant vectors. Base v1 on the cognee-demo-slack shape. Do not build full Cognee OAuth `/cognee-link` for v1.
7. Linear is a post-hack Source Plugin. Not HackNight.
8. Chonkie, Twelve Labs, and Gemini Embedding are optional later. Not core v1.

Charting grilling used "Monday demo". [Research: HackNight submission constraints](../tickets/04-research-hacknight-submission-constraints.md) found the live README judges Friday after 21:00 and dropped the Monday wording. Standing destination is still a HackNight-ready plan. Clock for cron and demo is the Friday window.

Cognee LLM for this effort is OpenRouter, not Anthropic. Vectors stay on Qdrant Cloud. Confirmed on [Task: confirm Qdrant Cloud cluster and Anthropic key](../tickets/09-task-confirm-qdrant-and-anthropic.md). Prior art in the slice-1 draft still names Anthropic; that draft is not final truth.

### Frontier (2026-08-14)

Empty. All child tickets closed. Remaining Not yet specified items are design-time defaults. The plan may pick them. No new tickets. Ready to hand off: revise the slice-1 design from Decisions so far, then `superpowers:writing-plans`. Do not write the design or the implementation plan in this map file.

## Decisions so far

- [Research: Cognee remember, add, and recall APIs for Slack and custom text provenance](../tickets/02-research-cognee-remember-add-recall-apis.md): Permanent `remember` + `recall`; pin demo `@dev` (`1.5.0.dev1`); no bare http(s) as `data`; permalink in `external_metadata` and/or body.
- [Research: GitHub REST events for a public-repo activity digest](../tickets/03-research-github-rest-events-for-digest.md): Poll issues (PRs included) on `topoteretes/cognee` and `qdrant/qdrant`; cite `html_url`; PAT preferred, unauth OK for a few GETs.
- [Research: HackNight submission constraints](../tickets/04-research-hacknight-submission-constraints.md): Friday 21:00 folder `YOURPROJECTNAME` plus Google form with run-proof; Monday dropped; depth over breadth; official OAuth Slack app optional.
- [Grill: cron host for Monday demo](../tickets/05-grill-cron-host-for-monday-demo.md): Laptop + ngrok; APScheduler inside FastAPI while the laptop is on; Slack URLs on the ngrok tunnel; Friday demo-day uptime, not a cloud host.
- [Task: confirm Qdrant Cloud cluster and Anthropic key](../tickets/09-task-confirm-qdrant-and-anthropic.md): Qdrant Cloud available; Cognee LLM is OpenRouter, not Anthropic.
- [Grill: Slack to GitHub identity mapping for Person Rollup](../tickets/06-grill-slack-github-identity-mapping.md): No Slack↔GitHub join for HackNight; Digests/ask keep Slack and GitHub separate; cross-source Person Rollup out of scope.
- [Prototype: digest message format](../tickets/08-prototype-digest-message-format.md): Approved TLDR → Summary (Slack + GitHub separate) → Attention/action required; SOURCED-only; none/omit if empty.
- [Grill: which Slack channels count as major](../tickets/07-grill-major-slack-channels.md): Join all public for ingest; ask, digest, and replies only on an operator allowlist; off-list slash gets a short ephemeral refuse.

## Not yet specified

Design-time leftovers. Not blocking tickets. The design and plan may pick defaults.

- How "major" Slack **messages** are filtered for ingest and Digest (length, threads, reactions) beyond skip bots, empty text, and slash echoes. Channel set is closed on [Grill: which Slack channels count as major](../tickets/07-grill-major-slack-channels.md).
- Rate-limit fallback if joining every public channel hits Slack limits (backoff, skip failed joins).
- Env shape for `topoteretes/cognee` and `qdrant/qdrant`: one comma list, two vars, or hardcoded for the hack.
- Optional GitHub **releases** poll. [Research: GitHub REST events for a public-repo activity digest](../tickets/03-research-github-rest-events-for-digest.md) already set issues (PRs included) as v1; releases were optional extra.
- Whether weekly Digest also has a scheduled cron post, or only daily cron plus slash for both windows. Host is [Grill: cron host for Monday demo](../tickets/05-grill-cron-host-for-monday-demo.md).
- Digest timezone (Berlin event vs draft `UTC`). README does not name a TZ.

## Out of scope

- Linear integration for HackNight (plugin slot later).
- Source Plugin field list for Linear after the hack (named slot only in this plan).
- Full Cognee SaaS Slack OAuth and per-user `/cognee-link`.
- Multimodal embeddings for v1 (Chonkie, Twelve Labs, Gemini Embedding 2).
- Masumi Citadel and Scout as runtime dependencies.
- Private-channel ingest and DM ingest as memory (reopen only with a new ticket). Public-channel ask/digest **allowlist** is in scope; see [Grill: which Slack channels count as major](../tickets/07-grill-major-slack-channels.md).
- Invite-only ingest (bot joins only when invited). Operator chose join-all public for ingest instead.
- How `Sarthib7/steward` becomes the `YOURPROJECTNAME` folder on `qdrant-labs/Cognee_Qdrant_slack_bot` (open PR vs form GitHub URL). Submit-after-build. Constraints already on [Research: HackNight submission constraints](../tickets/04-research-hacknight-submission-constraints.md).
- Person Rollup across Slack+GitHub (identity join or merged per-person Digest sections) for this HackNight slice. Closed ticket: [Grill: Slack to GitHub identity mapping for Person Rollup](../tickets/06-grill-slack-github-identity-mapping.md). Sources stay separate.
