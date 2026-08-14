# Prototype: digest message format

- Status: closed
- Labels: `wayfinder:prototype`
- Assignee: sarthib7
- Parent: [Steward HackNight design and plan](../maps/01-steward-hacknight-design-and-plan.md)
- Blocked-by: (none)

## Question

What does a `SOURCED` Digest look like in Slack?

Produce a cheap mock (markdown sample messages, not app code) for daily and weekly. Every bullet ends with a permalink or is omitted. Empty window copy must not invent activity.

Revised scope after [Grill: Slack to GitHub identity mapping for Person Rollup](06-grill-slack-github-identity-mapping.md): **no** Slack↔GitHub identity join, **no** per-person cross-source sections. Mock separate source blocks instead:

- Slack: Channel Memory / conversation activity (when in scope for the digest window)
- GitHub: sourced product-activity summary for configured public repos (`topoteretes/cognee`, `qdrant/qdrant`)

GitHub URL shapes: [Research: GitHub REST events for a public-repo activity digest](03-research-github-rest-events-for-digest.md) is closed. Cite `html_url` (issues, PRs, optional releases).

HITL. Link the mock as an asset. Do not ship Slack Block Kit in the Steward app in this ticket.

## Comments

Identity decision closed: [Grill: Slack to GitHub identity mapping for Person Rollup](06-grill-slack-github-identity-mapping.md). Blocker cleared. Prototype unblocked with revised scope (separate source sections; no per-person cross-source rollup).

### Prototype asset (2026-08-14) — awaiting human reaction

Claimed by sarthib7. Mock written; ticket stays **open** until a human approves or requests tweaks. Do not close from agent side.

Asset: [digest-message-format.md](../prototypes/digest-message-format.md)

What it shows:

- Example daily Slack post (SOURCED Slack + GitHub blocks; empty-window copy)
- Example weekly Slack post (same shape, wider window)
- Notes: cron channel post vs ephemeral slash replay (same body)

HITL next: human reacts to the mock (approve / tweak). Parent closes this ticket after approval and adds a Decisions-so-far gist on the map.

### Resolution (2026-08-14)

Approved with tweak. Each digest (daily and weekly) uses three parts:

1. **TLDR** — few lines, only the important ones (`SOURCED` or omit)
2. **Summary / normal update** — fuller sourced bullets: Slack block + GitHub blocks, separate, no person cross-link
3. **Attention / action required** — close with items that need eyes or action (`SOURCED` only; if none, say none or omit section per refuse-to-invent)

Asset updated: [digest-message-format.md](../prototypes/digest-message-format.md)

Status: **closed**.
