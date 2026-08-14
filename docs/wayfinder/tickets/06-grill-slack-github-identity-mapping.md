# Grill: Slack to GitHub identity mapping for Person Rollup

- Status: closed
- Labels: `wayfinder:grilling`
- Assignee: sarthib7
- Parent: [Steward HackNight design and plan](../maps/01-steward-hacknight-design-and-plan.md)
- Blocked-by: (none)

## Question

How should Person Rollup join Slack users to GitHub logins so per-person Digest sections are honest?

Standing constraint: Digests include org activity rollup **and** per-person sections. Prior art in `CONTEXT.md` says slice 1 does not join `slack:<user_id>` to `github:<login>`. That may change.

Options to grill (not a closed list):

- No join: two keys per human, sections stay by origin.
- Remembered Facts as the mapping, quoted when present.
- A small env or config map for the hack (Slack user id to GitHub login).
- Display-name heuristics (reject unless the operator accepts false merges).

HITL. Do not answer for the operator. This ticket blocks [Prototype: digest message format](08-prototype-digest-message-format.md).

## Comments

### Resolution (2026-08-14)

**No Slack↔GitHub identity mapping for HackNight.** Digests and ask treat sources separately.

Operator gist (paraphrase): GitHub digest can be **just a summary** of product/repo activity for Qdrant + Cognee, not Slack↔GitHub person linking. Slack at HackNight is **chaotic** with many attendees, not a clean employee-watch surface. Core product for the hack: **remember chats**; people **ask Steward** about chat plus GitHub product (qdrant/cognee).

Recorded split:

- Slack → Channel Memory / ask about conversation
- GitHub → sourced product-activity summary for configured public repos (`topoteretes/cognee`, `qdrant/qdrant`)

Person Rollup across Slack+GitHub is **out of scope** for this map's HackNight slice (deferred / Out of scope on the parent map). Standing Notes item "rollup + per-person" from charting is **superseded** for HackNight by this answer; see map Notes correction.
