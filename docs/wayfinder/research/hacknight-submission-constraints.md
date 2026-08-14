# HackNight submission constraints

Date: 2026-08-14
Ticket: Research: HackNight submission constraints

Provenance: VERIFIED quotes are from pages fetched this session. INFERRED is reasoning from those quotes. `not determined` means the source did not say.

Sources fetched this session:

- `https://raw.githubusercontent.com/qdrant-labs/Cognee_Qdrant_slack_bot/main/README.md` (HEAD `633a470`, tree is README only)
- Same README at `05dc27c` and `d4b417e` (Monday wording)
- GitHub API: repo metadata, recursive tree, commits, issues, pulls, forks, wiki, missing `.github` and `CONTRIBUTING.md` (404)
- Submission form: `https://docs.google.com/forms/d/e/1FAIpQLScxLDtI5jsnwOSxKkBzo3PFYgbWT4n8mEYudcd8YtjaWHpElw/viewform`
- Starter: `https://raw.githubusercontent.com/qdrant-labs/cognee-demo-slack/main/README.md` plus `requirements.txt`, `.env.example`, `slack-manifest.yaml`, `.claude/skills/cognee-slack-bot/SKILL.md`, skill `assets/` copies
- Official Slack docs: `https://docs.cognee.ai/integrations/slack-integration`
- Event pages: `https://luma.com/cognee-m078`, `https://www.createwith.com/event/berlin-give-your-slack-a-memory-a-cognee-and-qdrant-hack-night-aug-2026`
- Observed PR: `https://github.com/qdrant-labs/Cognee_Qdrant_slack_bot/pull/1`
- `https://raw.githubusercontent.com/qdrant/skills/main/README.md` (resource only, no HackNight rules)

Not fetched: Notion Slack SDK page (timed out). Claude.ai Qdrant deep-dive artifact. ngrok docs. Slack apps dashboard. Qdrant product docs. Event Slack (`#all-hacknight`, `#support`). Form owner timezone setting.

## Verdict

Steward is a valid HackNight entry if it runs tonight, lands in a named folder on `qdrant-labs/Cognee_Qdrant_slack_bot`, and is filed through the Google form with a public GitHub URL plus proof of a working run.

Judges score a live same-day demo. Depth of one working path beats extra half-built work. Slack plus GitHub plus a digest is an official idea, not a reject. Do not wait for Monday. The live README dropped "ready to use on Monday". Judging is Friday after 21:00. A Monday-only cron will not fire before that. Trigger the digest by hand for the demo.

The official Cognee OAuth Slack app is neither required nor forbidden. The HackNight README points at the slash-command starter first.

## Evidence

### Judging criteria (quoted)

VERIFIED. Live README (`main` / `633a470`, fetched 2026-08-14):

> **The judgement will happen same day after submission deadline at 9PM**
>
> | Criterion | Points |
> |---|---|
> | Your project runs and is ready to use | 5 |
> | Depth of the stack, not breadth | 0–5 |
> | Complexity of your project (subagents, additional tooling, etc.) | 0–5 |
> | Novel application | 0–5 |
>
> **Demos:** the top 5 projects demo in front of the audience, and the audience picks the winner via [Slido](https://app.sli.do/event/sXC8CqpmCsbrEX93g7JeE2).
>
> > "Depth, not breadth" is the one people most often get wrong. One integration that genuinely works end to end beats five that half-work.

Numeric weights: 5 for a running project (not a 0-5 range). 0-5 each for depth, complexity, novel application. Max 20 if every row is maxed. INFERRED from the table. The README does not state a total.

Same README, submitting step 1:

> Make sure your project **runs**: a judge should be able to use it.

VERIFIED. The linked form adds a hard gate and a ranking line that the README table does not repeat:

> Submissions close at 21:00. Five finalists are announced shortly after.Keep it short — we read every entry in about fifteen minutes, so brevity helps you.

> The question your demo answers — write it out word for word
> Not a description of your project. The actual question you type into it.

> Why can't keyword search answer that question?
> One or two sentences. This is the main thing we rank on.

> Proof it runs — link to a screenshot or a short screen recording
> The answer coming back, on your build. No proof of a working run, no finalist slot.

> GitHub repo URL
> Public, or add us as collaborators. We spot-check and use this for tiebreaks.

INFERRED: two ranking stories sit side by side. README table weights "runs / depth / complexity / novel". Form text says the keyword-search rationale is "the main thing we rank on". Both bind because the README lists the form as **Final submission form**.

VERIFIED. Luma (`https://luma.com/cognee-m078`):

> 21:00 PM - Project Submission Deadline – finalist selection
> 21:15 PM - Finalist presentations & judging
>
> You will have 2 minutes to present a demo in which you:
> Present your idea - Explain what memory problem you solved and how you used Cognee and Qdrant to do it
> Run a live demo - Show your build in action, solving something a plain search or a stateless bot couldn't

INFERRED: judges (form plus README points) pick a top 5. Audience Slido vote picks the winner among those five. The README says the audience picks the winner. It does not say the audience scores the four-point table.

### Submission shape (folder, PR, files)

VERIFIED. Live README **Submitting**:

> 1. Make sure your project **runs**: a judge should be able to use it.
> 2. Create a folder with your project in the repo with YOURPROJECTNAME
> 3. Submit via the [final submission form](...).
> 4. If you're in the top 5, get ready to pitch: the audience votes on [Slido](...).

Folder name: `YOURPROJECTNAME`. No charset or kebab-case rule. No required files inside the folder (no README, LICENSE, or test named as required).

PR target: the README never says "open a pull request". VERIFIED. GitHub API recursive tree of `qdrant-labs/Cognee_Qdrant_slack_bot` HEAD is one blob: `README.md`. No write-access path is documented.

INFERRED from observed behavior: without write access, the folder gets into "the repo" by a PR to `qdrant-labs:main`. PR #1 (open, `fdddf`, 2026-08-14) does that. Project folder is `decision-ledger/`. Base is `qdrant-labs:main` (`633a470`). Body: "Submission for the Cognee x Qdrant HackNight. Project lives in `decision-ledger/`."

A second fork (`fotiDim/Cognee_Qdrant_slack_bot`) exists and was pushed. No PR from that fork was in `pulls?state=all` at fetch time. Its tree is not a `YOURPROJECTNAME/` app folder. Do not treat it as the required shape.

Form-required fields (VERIFIED from the viewform fetch): Email, Team name, Who is presenting, GitHub repo URL, the demo question word for word, why keyword search cannot answer it, proof link (screenshot or short screen recording), What did you use. Optional: anything broken.

Demo recording: the form requires a screenshot **or** a short screen recording as proof. The README does not require a video file in the GitHub folder. Top 5 then run a live 2-minute demo (Luma). No "upload a demo.mp4 into the PR" rule was found.

### Stack and starter rules

VERIFIED. HackNight README does not pin Cognee or Qdrant versions. It does not say "you must use Cognee and Qdrant and Slack" in a rules list. The title is `HackNight: Cognee & Qdrant`. Resources assume Slack (ngrok, Slack apps dashboard, Cognee Slack demo, Slack integration docs).

Form "What did you use?" lists Cognee, Qdrant, Agentic SKILLs, Something else. The question is marked required. Checkbox "must check all" vs "at least one" is not determined from the HTML-to-markdown conversion.

Luma demo script tells finalists to explain "how you used Cognee and Qdrant". INFERRED: using both is expected for a competitive pitch. A missing Cognee or Qdrant path is not written as an automatic reject in the README.

Starter repo, listed first under Resources as **Cognee Slack Demo Project**:

> Minimal Slack bot: `/cognee-remember ` stores it in Cognee memory,
> `/cognee-ask ` recalls it. One shared memory dataset for the whole
> workspace — no per-user account linking, no OAuth, no bot token needed since
> replies go back directly in the slash-command response.

Starter `requirements.txt`:

> cognee[fastembed] @ git+https://github.com/topoteretes/cognee.git@dev

Starter README install note:

> pip3 install --no-deps --ignore-requires-python cognee-community-vector-adapter-qdrant==0.4.0

Starter skill checkpoint:

> expect Version: 1.5.0.dev1 (or later dev)
> The demo requires the dev branch (`1.5.0.dev*`), not the PyPI release.

Starter `.env.example` sets `VECTOR_DB_PROVIDER=qdrant` and `VECTOR_DATASET_DATABASE_HANDLER=qdrant`. Cloud or local Qdrant. `ENABLE_BACKEND_ACCESS_CONTROL=false`.

These pins bind the starter, not the HackNight README. Steward may follow them. The event README does not require that exact git pin.

Official Cognee Slack docs (linked from the HackNight README):

> **Pre-release only.** This integration first shipped in **`cognee==1.5.0.dev1`** and is not in any stable release yet.

> This integration is for self-hosted Cognee deployments — you create and own the Slack app [...] It is a **separate app from the cloud/SaaS Slack integration** [...] do not point one at the other's server.

Qdrant SKILLS (`https://github.com/qdrant/skills`) is a linked resource. Its README is agent-skill docs. It contains no HackNight submission rules. VERIFIED.

### Deadline / Monday logistics

VERIFIED. Live README: judging is "same day after submission deadline at 9PM". Form: "Submissions close at 21:00." Luma: 21:00 submission, 21:15 finalist presentations, 21:45 awards, 22:00 wrap. Event date on Luma/createwith: Friday 14 August 2026. Venue: Berlin.

Timezone on the README and form is not determined. Luma location is Berlin. GitHub commit timestamps on the README are `+0200`. INFERRED: 21:00 means 21:00 in Berlin (CEST) unless Slack announces otherwise.

Monday wording is gone from live `main`.

VERIFIED. README at `d4b417e` and still at `05dc27c` (2026-08-14T15:00:42Z):

> | Your project runs and is ready to use on Monday | 5 |

> 1. Make sure your project **runs** — a judge should be able to use it on Monday.

That older README also had no "Create a folder..." step and no "same day ... 9PM" line.

VERIFIED. Commit `633a470` (2026-08-14T16:21:12Z, Andrei Cristea) is the live text. Monday is removed. Same-day 9PM is added. Folder step is added.

Createwith scraped "17:00 UTC". That conflicts with a Berlin 17:00-22:00 evening. Treat as a directory scrape, not as the deadline TZ. Luma and the venue are the better clock.

Cron / demo script implication (INFERRED): do not host the digest cron for "Monday so a judge can use it then". Judging is tonight. A weekly job that only fires Monday will not run before 21:00 Friday. Keep a manual slash command or one-shot script that posts the digest during the 18:00-21:00 hack window and during a 2-minute pitch.

Event Slack may still post a TZ or a form close time. That channel was not fetched.

### Starter vs official Cognee Slack app

HackNight README lists both, starter first:

> **Cognee Slack Demo Project**: https://github.com/qdrant-labs/cognee-demo-slack (with the claude skill to set it up)
> **Cognee Slack integration docs**: https://docs.cognee.ai/integrations/slack-integration#slack

VERIFIED contrast:

| | Starter `cognee-demo-slack` | Official self-hosted Slack integration |
|---|---|---|
| App name in manifest | Cognee Demo Bot | Cognee |
| Commands | `/cognee-ask`, `/cognee-remember` | those two plus `/cognee-link` |
| OAuth | none | required (`SLACK_CLIENT_ID`, secret, redirect, frontend Connect) |
| Bot token / `chat:write` | not needed | yes |
| Memory | one shared `slack` dataset | per-person after `/cognee-link` |
| Shortcuts / Share buttons | skipped | Remember this, Share/Discard |
| Request path | FastAPI `/api/v1/slack/commands` in the demo `app.py` | Cognee backend `/api/v1/slack/commands` plus events and interactive |

Starter README **Skipped for this demo**:

> `/cognee-link` per-user account linking — everyone shares one `slack`
> dataset instead. Add per-user OAuth + encrypted token storage if you need
> private-per-person memory.

Starter skill:

> Per-user memory — everyone shares one `slack` dataset. Real per-person memory needs the
> `/cognee-link` OAuth flow from the official integration docs.

Official docs also warn: do not mix this app with the **cloud/SaaS** Slack integration. That is a third app. The HackNight README never mentions the cloud Slack app.

VERIFIED: nothing in the HackNight README, form, or starter says the official OAuth app is required. Nothing says it is forbidden. Using it is extra complexity (README complexity row names "subagents, additional tooling, etc."). It also adds OAuth and a frontend, which can fail in a 3-hour window.

INFERRED: the intended on-ramp is the starter slash-command app. Official OAuth is optional if Steward needs per-user memory.

### Fit of memory + GitHub + digests

VERIFIED. Live README **Project ideas** (starting points, not a menu):

> - **Onboarding buddy**: seed it with a handful of docs, then let a new joiner ask the questions they'd otherwise DM three people about.
> - **Slack + one more source**: add GitHub issues or meeting notes via `cognee.add()` so a Slack question can be answered from a source that isn't Slack.
> - **Weekly digest**: cluster what was remembered this week and post a summary.

Also: "feel free to go somewhere else entirely."

Nothing in the README, form, starter, or official Slack docs rejects a memory bot that also ingests GitHub and posts a daily or weekly digest.

What would hurt that slice:

- Breadth without depth. Quote again: "One integration that genuinely works end to end beats five that half-work." Shipping Slack remember/ask plus GitHub plus daily plus weekly as four thin paths can lose the 0-5 depth row. INFERRED.
- A digest that only exists as a Monday cron. Live rules judge Friday night. INFERRED.
- No proof of a working run on the form. Hard reject for finalist slot. VERIFIED.
- Keyword-searchable demo question. Form ranks "why keyword search cannot answer that". A digest that is only a dump of issue titles is weaker than a question that needs graph or cross-source memory. INFERRED from form text.
- Missing Cognee or Qdrant in the pitch. Luma asks finalists to say how they used both. INFERRED.

What rewards it:

- GitHub-as-second-source is the second listed idea, with `cognee.add()`.
- Weekly digest is the third listed idea.
- Complexity row names extra tooling. A real GitHub ingest plus a digest job can score here if the Slack path still runs. INFERRED.
- Form checkbox "Agentic SKILLs" matches Luma's "compile the patterns you find into agentic SKILLs". Not required in the README submitting list. Optional signal.

Daily vs weekly: README says weekly. Daily is not forbidden ("go somewhere else entirely"). A daily digest is extra surface. Prefer one digest path that actually posts. INFERRED from the depth quote.

## Blind spots

- Event Slack (`#all-hacknight`) can still change the deadline, TZ, or folder rule after this fetch. Not read.
- Form checkbox semantics (must tick Cognee and Qdrant vs any of the four) not determined.
- Whether the GitHub folder PR must be merged before 21:00, or an open PR plus the form URL is enough: not determined. README says create a folder in the repo. PR #1 is still open.
- Whether `YOURPROJECTNAME` must match the form team name: not determined.
- Notion Slack Integration SDK page: fetch timed out. Contents not determined.
- Cloud/SaaS Cognee Slack app: mentioned only as "do not mix" in official docs. Not a HackNight rule.
- createwith "17:00 UTC" vs Berlin evening: not reconciled.
- Audience Slido vs judge table: how points become "top 5" is not written.

## One-line gist for the map

Same-day 21:00 Berlin judging, folder YOURPROJECTNAME on qdrant-labs/Cognee_Qdrant_slack_bot plus the Google form with run-proof; Monday dropped; depth of one Slack+Cognee+Qdrant path beats extra half-built work; official OAuth Slack app optional.
