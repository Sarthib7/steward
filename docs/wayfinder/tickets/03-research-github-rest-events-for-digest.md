# Research: GitHub REST events for a public-repo activity digest

- Status: closed
- Labels: `wayfinder:research`
- Assignee: research-agent
- Parent: [Steward HackNight design and plan](../maps/01-steward-hacknight-design-and-plan.md)
- Blocked-by: (none)

## Question

For the **public** Cognee and Qdrant GitHub repos (confirm the exact `owner/name` pairs), which GitHub REST endpoints give activity that a sourced Digest can cite under a PAT and under unauthenticated rate limits?

Need:

- Endpoints (issues, pull requests, commits, releases, events, or other) and the URL fields that can appear as `SOURCED` permalinks.
- Whether `GET /repos/{owner}/{repo}/issues` already includes pull requests (`pull_request` key).
- Rate limits: unauthenticated versus PAT, and whether two-repo polling at digest time stays under those limits.
- What is worth a second endpoint for HackNight depth versus what is extra breadth (commit firehose, org events).
- Pagination and a sane cap for v1.

Cite live GitHub REST docs. Do not propose a GitHub App or webhooks for v1 unless the docs make PAT polling unusable.

## Comments

### Resolution (charting session, 2026-08-14)

Public repos: `topoteretes/cognee`, `qdrant/qdrant`. v1 poll `GET /repos/{owner}/{repo}/issues` (`sort=updated`, optional `since`, `per_page` ≤100). That list includes pull requests (`pull_request` key). Cite `html_url`. Optional second call: releases. Skip commit firehose and org events for v1. PAT 5,000/h preferred; unauthenticated 60/h still fits a few GETs per two-repo digest. No GitHub App or webhooks required for v1.

Note: [docs/wayfinder/research/github-rest-events-for-digest.md](../research/github-rest-events-for-digest.md)
