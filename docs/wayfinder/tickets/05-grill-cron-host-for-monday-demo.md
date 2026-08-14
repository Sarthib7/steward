# Grill: cron host for Monday demo

- Status: closed
- Labels: `wayfinder:grilling`
- Assignee: sarthib7
- Parent: [Steward HackNight design and plan](../maps/01-steward-hacknight-design-and-plan.md)
- Blocked-by: (none)

## Question

Where does the scheduled Digest cron run for this HackNight: laptop plus ngrok, a cloud host, or slash-only with cron as best-effort on whoever's laptop is awake?

Standing constraint from charting: Digest delivery is **both** scheduled cron posts to a channel **and** `/steward-digest` (or similar) to regenerate or replay. Daily morning Digest and weekly Digest are both in the demo. This ticket decides the **host**, not whether cron exists.

Correction from [Research: HackNight submission constraints](04-research-hacknight-submission-constraints.md): the live README judges **Friday after 21:00**, not Monday. A Monday-only cron will not fire before that. Grill the host for **tonight's** demo window, and whether slash/manual replay is the proof path if cron cannot run.

HITL. Do not answer for the operator.

## Comments

Charting note (not a resolution): [Research: HackNight submission constraints](04-research-hacknight-submission-constraints.md) found judging Friday after 21:00. Title still says Monday because that was the charting name. Grill against the live Friday clock.

### Resolution (2026-08-14)

Operator chose **A: Laptop + ngrok**. APScheduler/cron runs inside the FastAPI process while the demo machine is on. Slack request URLs point at the ngrok HTTPS tunnel.

HackNight live README judges Friday after 21:00, not Monday. Ticket title still says Monday. The clock constraint is demo-day uptime of the laptop, not a cloud host.
