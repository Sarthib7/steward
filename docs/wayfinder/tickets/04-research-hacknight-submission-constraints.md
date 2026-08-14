# Research: HackNight submission constraints

- Status: closed
- Labels: `wayfinder:research`
- Assignee: research-agent
- Parent: [Steward HackNight design and plan](../maps/01-steward-hacknight-design-and-plan.md)
- Blocked-by: (none)

## Question

From the [qdrant-labs/Cognee_Qdrant_slack_bot](https://github.com/qdrant-labs/Cognee_Qdrant_slack_bot) README and any rules it links: what constraints bind the Steward submission?

Need:

- Judging criteria and weights (project runs, depth not breadth, stack complexity, novel application, or whatever the README actually says).
- Submission shape: folder name, PR target, required files, demo recording.
- Stack rules: must use Cognee and Qdrant and Slack; pins; starter versus official Cognee Slack OAuth app.
- Monday / deadline logistics that change cron host or demo script.
- Anything that would reject a memory + GitHub + daily/weekly Digest slice, or that rewards it.

Quote the README. Do not summarise without quotes.

## Comments

### Resolution (charting session, 2026-08-14)

Live README (fetched this session): judging same day after 9PM. Submission is a `YOURPROJECTNAME` folder on `qdrant-labs/Cognee_Qdrant_slack_bot` plus the Google form with a public GitHub URL and proof of a run. Criteria: runs (5), depth not breadth (0–5), complexity (0–5), novel (0–5). Quote: "One integration that genuinely works end to end beats five that half-work." Monday wording is gone from live `main`. Official Cognee OAuth Slack app is optional; starter slash-command app is listed first. Slack + GitHub + weekly digest are listed project ideas, not rejects. Parent also fetched the live README and confirmed the 9PM / folder / form / depth quote.

Note: [docs/wayfinder/research/hacknight-submission-constraints.md](../research/hacknight-submission-constraints.md)
