# GitHub REST events for a public-repo activity digest

Date: 2026-08-14
Ticket: Research: GitHub REST events for a public-repo activity digest

## Verdict

Monitor `topoteretes/cognee` and `qdrant/qdrant` (both public). For v1, poll `GET /repos/{owner}/{repo}/issues` with `sort=updated`, `state=all` (or `open`), optional `since=`, and `per_page` up to 100. That one call already returns issues and pull requests; distinguish PRs by the `pull_request` key. Cite `html_url` as the SOURCED permalink. Optional second call for HackNight depth: `GET /repos/{owner}/{repo}/releases` (one page). Prefer a PAT (5,000 req/hour). Unauthenticated (60 req/hour per IP) still works for two-repo digest polling if each run stays at a few requests. Skip commit firehose and org events for v1. No GitHub App or webhooks required for v1.

Docs cited with `apiVersion=2022-11-28` where linked. Live doc pages also show header examples with `X-GitHub-Api-Version: 2026-03-10`.

## Evidence

### Repo identities (public?)

**VERIFIED** via `GET https://api.github.com/repos/topoteretes/cognee` and live page `https://github.com/topoteretes/cognee`:

- `full_name`: `topoteretes/cognee`
- `private`: false
- `visibility`: `public`
- `html_url`: `https://github.com/topoteretes/cognee`

**VERIFIED** via `GET https://api.github.com/repos/qdrant/qdrant` and live page `https://github.com/qdrant/qdrant`:

- `full_name`: `qdrant/qdrant`
- `private`: false
- `visibility`: `public`
- `html_url`: `https://github.com/qdrant/qdrant`

Candidate `topoteretes/cognee` matches. Candidate `qdrant/qdrant` matches. No alternate Cognee owner/name checked beyond this pair.

### List issues (includes PRs?)

**Endpoint:** `GET /repos/{owner}/{repo}/issues`

Source: [REST API endpoints for issues](https://docs.github.com/en/rest/issues/issues?apiVersion=2022-11-28)

**VERIFIED** docs quote:

> GitHub's REST API considers every pull request an issue, but not every issue is a pull request. For this reason, "Issues" endpoints may return both issues and pull requests in the response. You can identify pull requests by the pull_request key. Be aware that the id of a pull request returned from "Issues" endpoints will be an issue id. To find out the pull request id, use the "List pull requests" endpoint.

**VERIFIED** docs also say under List repository issues:

> List issues in a repository. Only open issues will be listed.

Same page documents `state` with values `open`, `closed`, `all` (default `open`), plus `since`, `sort`, `direction`, `per_page` (max 100, default 30).

**INFERRED:** the `state` query parameter controls open vs closed vs all. The "Only open issues will be listed" line describes the default when `state` is omitted.

**VERIFIED** live sample `GET /repos/topoteretes/cognee/issues?per_page=2&state=open` (unauthenticated):

- Item with `pull_request` present: `html_url` `https://github.com/topoteretes/cognee/pull/4499`, and nested `pull_request.html_url` the same.
- Item without `pull_request`: `html_url` `https://github.com/topoteretes/cognee/issues/4491`.

So one issues list is enough for both issues and PRs for a sourced digest. Separate `GET /repos/{owner}/{repo}/pulls` is optional if you want PR-only fields; pulls docs say PRs are a type of issue and shared assignee/label/milestone actions go through issues endpoints ([pulls](https://docs.github.com/en/rest/pulls/pulls?apiVersion=2022-11-28)).

### Other endpoints (commits, events, releases)

| Endpoint | Path | Role for digest | Permalink field(s) |
| --- | --- | --- | --- |
| Issues (+ PRs) | `GET /repos/{owner}/{repo}/issues` | **v1 primary** | `html_url`; for PRs also `pull_request.html_url` |
| Pulls | `GET /repos/{owner}/{repo}/pulls` | Optional PR-only filter | `html_url` |
| Releases | `GET /repos/{owner}/{repo}/releases` | **Worth second call** (version milestones) | `html_url` |
| Repo events | `GET /repos/{owner}/{repo}/events` | Mixed stream; latency caveat | Nested `html_url` by event type (schema shares public events shape) |
| Commits | `GET /repos/{owner}/{repo}/commits` | Extra breadth / firehose | `html_url` |
| Org events | `GET /orgs/{org}/events` | Extra breadth across org | Nested `html_url` by event type |

**Releases** ([docs](https://docs.github.com/en/rest/releases/releases?apiVersion=2022-11-28)):

> This returns a list of releases, which does not include regular Git tags that have not been associated with a release.

> Information about published releases are available to everyone.

Schema includes required `html_url`. **VERIFIED** live: `https://github.com/qdrant/qdrant/releases/tag/v1.19.0`.

**Commits** ([docs](https://docs.github.com/en/rest/commits/commits?apiVersion=2022-11-28)): `GET /repos/{owner}/{repo}/commits` with `since` / `until`, `per_page` max 100. Schema includes `html_url`. **VERIFIED** live: `https://github.com/qdrant/qdrant/commit/74f3e85b9473c62560006c043e13737ce6b48412`. Busy default branches produce high volume. Good for depth only if the digest wants "what landed on main", not for a default HackNight slice.

**Repo events** ([docs](https://docs.github.com/en/rest/activity/events?apiVersion=2022-11-28)):

> The timeline will include up to 300 events. Only events created within the past 30 days will be included. Events older than 30 days will not be included (even if the total number of events in the timeline is less than 300).

> This API is not built to serve real-time use cases. Depending on the time of day, event latency can be anywhere from 30s to 6h.

Events support ETag polling: 304 does not consume the primary rate limit; obey `X-Poll-Interval`. Useful if Steward polls continuously. For a single digest-at-run-time fetch, issues (+ optional releases) are clearer to cite.

**Org events** `GET /orgs/{org}/events`: covers the whole org (`topoteretes`, `qdrant`), not only the two monitored repos. Extra breadth for v1.

**Depth vs breadth for HackNight**

- Worth second endpoint: **releases** (one page per repo). Clear version story and stable `html_url`.
- Skip for v1: **commits** (firehose), **org events** (cross-repo noise), optional **pulls** if issues already return PRs.
- Repo **events** only if you want a mixed push/star/fork/issue stream and accept 30s–6h latency plus 30-day / 300-event caps.

### Rate limits (unauthenticated vs PAT)

Source: [Rate limits for the REST API](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api?apiVersion=2022-11-28)

**VERIFIED** docs quotes:

> You can make unauthenticated requests if you are only fetching public data. Unauthenticated requests are associated with the originating IP address, not with the user or application that made the request.

> The primary rate limit for unauthenticated requests is 60 requests per hour.

> You can use a personal access token to make API requests.

> All of these requests count towards your personal rate limit of 5,000 requests per hour.

Secondary limits also apply (concurrent requests, points per minute). Docs: most REST `GET` requests cost 1 point toward the secondary "points per minute" budget.

**Two-repo digest at run time (INFERRED request budget):**

| Mode | Requests per digest | Fits unauthenticated 60/h? | Fits PAT 5,000/h? |
| --- | --- | --- | --- |
| Issues only, 1 page × 2 repos | 2 | Yes (many digests/hour) | Yes |
| Issues + releases, 1 page each × 2 | 4 | Yes | Yes |
| Issues + releases + events × 2 | 6 | Yes if digest is infrequent | Yes |
| Issues + commits many pages × 2 | Can climb fast | Risky on shared IP | Still fine if capped |

**Verdict on auth:** PAT polling is usable and preferred. Unauthenticated also works for public data if Steward shares an IP carefully and keeps each digest to a handful of GETs. GitHub App / webhooks not required for v1.

Check status with response headers (`x-ratelimit-*`) or `GET /rate_limit` (primary check does not count against the primary limit per rate-limit docs).

### URL fields usable as SOURCED permalinks

Prefer browser HTML URLs, not `api.github.com` URLs.

| Source | Field | Example (VERIFIED live) |
| --- | --- | --- |
| Issue | `html_url` | `https://github.com/topoteretes/cognee/issues/4491` |
| PR via issues list | `html_url` or `pull_request.html_url` | `https://github.com/topoteretes/cognee/pull/4499` |
| Release | `html_url` | `https://github.com/qdrant/qdrant/releases/tag/v1.19.0` |
| Commit | `html_url` | `https://github.com/qdrant/qdrant/commit/74f3e85b9473c62560006c043e13737ce6b48412` |
| Events | nested `html_url` in payload objects | Depends on event type; not determined for every type in this note |

Do not cite `url` (API) as the human SOURCED link.

### Pagination and suggested v1 cap

Source: [Using pagination in the REST API](https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api?apiVersion=2022-11-28)

**VERIFIED** docs:

> For most endpoints, the maximum value of `per_page` is `100`.

> You can use the `link` header from the response to request additional pages of data.

Issues / pulls / commits / releases: `per_page` max 100, default 30. Events default `per_page` 30 for repo events (public events default 15).

**Suggested v1 cap (INFERRED for Steward digest):**

1. Per repo: one `GET .../issues?sort=updated&direction=desc&state=all&per_page=30` (or 100). Optional `since=` set to last digest time.
2. Do not follow `link` beyond page 1 in v1 unless `since` is unset and you need more history. Cap at 1 page (30 or 100 items) per repo.
3. Optional: one `GET .../releases?per_page=5` (or 10) per repo. Cap at 1 page.
4. Hard stop: at most ~4–6 core GETs per digest run for two repos. Stay well under 60/h even unauthenticated.

## Blind spots

- Exact secondary rate-limit headroom under concurrent HackNight tooling on the same IP: not measured beyond docs.
- Whether Steward digest cadence is once per HackNight vs continuous: not specified; math above assumes infrequent digest runs.
- Event payload permalink shapes for every event type: not enumerated here.
- Fine-grained PAT scopes required for public read: not determined from these pages alone (public unauthenticated read works without a token).
- Doc note "Only open issues will be listed" vs `state=all`: both appear on the same live page; live `state=open` verified; `state=all` not separately sample-fetched in this session.
- Alternate Cognee forks or renamed owners: not searched.

## One-line gist for the map

v1: poll issues (includes PRs via pull_request) plus optional releases on topoteretes/cognee and qdrant/qdrant; PAT preferred, unauthenticated OK for few GETs per digest.
