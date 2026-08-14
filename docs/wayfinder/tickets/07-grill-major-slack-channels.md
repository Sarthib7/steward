# Grill: which Slack channels count as major

- Status: closed
- Labels: `wayfinder:grilling`
- Assignee: sarthib7
- Parent: [Steward HackNight design and plan](../maps/01-steward-hacknight-design-and-plan.md)
- Blocked-by: (none)

## Question

Which Slack channels does Steward ingest, and which of those count as "major" for Digest?

Standing constraint: watch major Slack messages for the hack, not private channels or DMs as memory.

Options to grill:

- Join every public channel at startup (draft design).
- A named allowlist of channels.
- Only channels where a human invites the bot.

"Major" might mean the channel set, a message filter (length, threads, reactions), or both. Message-level filters that stay vague after this grill stay in the map's Not yet specified.

HITL. Do not answer for the operator.

## Comments

### Resolution (2026-08-14)

Operator chose hybrid **B**: join all public channels for ingest coverage (as designed), but digest and ask only from an allowlist. Extra: Steward replies only in operator-chosen channel(s).

Binding split:

- **Ingest:** Steward may list and join public channels at startup. Channel Memory covers those public channels. Private channels and DMs stay out of memory (unchanged Out of scope).
- **Ask, digest, answers:** constrained to an operator-configured **allowlist** of channels. `/steward-ask`, digest (slash replay and cron post target), and Steward replies run only there. Digest and ask draw from allowlist Channel Memory.
- **Off-allowlist slash:** refuse with a short ephemeral, equivalent to `Steward isn't enabled here`.

"Major" for this hack is that allowlist. Invite-only ingest and private-channel allowlists stay rejected. Message-level filters (length, threads, reactions) were not decided here.
