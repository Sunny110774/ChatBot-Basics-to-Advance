# PM004_03 Project Plan: ChatBot - Basics to Advance

23 Nov 2026 · Naveen Nigam

PM004 was delivered in two days, 22 and 23 Nov 2026, from the move to Claude through to a live Prod release. Only sharing and feedback remain, starting with the LinkedIn post on 24 Nov 2026. This plan records the work as it actually ran, so it doubles as the baseline for later releases. The why and what are in the charter (PM004_01); stages and gates are in PM004_02.

## 1. Deliverables and WBS

PM004 produces eight deliverables; the WBS below covers 100% of the charter scope and nothing outside it.

| # | Deliverable | WBS | Gate |
| --- | --- | --- | --- |
| D1 | Charter, lifecycle framework and project plan | 1 | G0, G3 |
| D2 | App on Claude with offline test suite and Windows launcher | 2 | G0 |
| D3 | Five working levels with citations, tools, approvals and Plan/Act/Verify | 3 | G2 |
| D4 | Learning module: runbook, executive summary, workflows, token guide | 4 | G3 |
| D5 | Presentation (slides and PDF) and private interview Q&A | 4 | G3 |
| D6 | Live UAT and Prod with hosted-mode guardrails | 5 | G4 |
| D7 | Evaluation of a live scenario set | 1 | G1 |
| D8 | Public share: GitHub release, LinkedIn post, feedback | 5, 6 | G4 |

**Work breakdown structure**

1. Project management
    1. Charter (PM004_01)
    2. Lifecycle framework and project plan (PM004_02, PM004_03)
    3. Live scenario run and evaluation (PM004_10)
2. Base on Claude
    1. Move the prototype from OpenAI to Claude
    2. Offline test suite with a fake Claude client
    3. Windows launcher and settings with a live connection test
3. Five levels made real
    1. Basic: guided menu with fixed answers
    2. Shared topics, question lists and follow-up buttons in all levels
    3. RAG: numbered citations and weak-match cut-off
    4. Automation: fixed tools, cited document fallback, human approval
    5. Agentic: look, decide, act loop with Plan/Act/Verify
    6. Token use per answer and history cap
4. Learning module and documents
    1. Runbook, executive summary and workflows (PM004_04 to PM004_06)
    2. Token optimisation guide (PM004_07)
    3. Guardrails and employee-reuse sections in every document
    4. Presentation (PM004_09)
    5. Interview Q&A (PM004_08, private)
5. Release
    1. Hosted mode: locked settings, private chats, daily caps
    2. Render blueprint for UAT and Prod
    3. UAT deploy and live test
    4. Prod deploy and smoke test
    5. GitHub release v1.0.0 and profile set-up
6. Share
    1. LinkedIn post with the deck
    2. Demo video (optional)

## 2. Schedule

All build and release work finished in two days; dates are actuals taken from the commit history. Every task was short (under a day), so durations are shown as start and end dates. Owner for every row: Naveen Nigam, with Claude as build support.

| WBS ID | Task | Depends on | Start | End | Status |
| --- | --- | --- | --- | --- | --- |
| 1.1 | Charter | None | 22 Nov | 22 Nov | Done |
| 2.1 | Move prototype to Claude | 1.1 | 22 Nov | 22 Nov | Done |
| 2.2 | Offline test suite | 2.1 | 22 Nov | 22 Nov | Done |
| 2.3 | Launcher and settings with live test | 2.1 | 22 Nov | 22 Nov | Done |
| G0 | Gate: base on Claude | 2.2 | 22 Nov | 22 Nov | Passed |
| 3.1 | Basic guided menu | G0 | 22 Nov | 22 Nov | Done |
| 3.2 | Shared topics and follow-ups | 3.1 | 22 Nov | 22 Nov | Done |
| 3.3 | RAG citations and weak-match cut-off | 3.2 | 22 Nov | 23 Nov | Done |
| 3.4 | Automation tools, fallback and approval | 3.3 | 22 Nov | 23 Nov | Done |
| 3.5 | Agentic look, decide, act; Plan/Act/Verify | 3.4 | 23 Nov | 23 Nov | Done |
| 3.6 | Token use per answer; history cap | 3.5 | 23 Nov | 23 Nov | Done |
| G2 | Gate: each level real | 3.1 to 3.6 | 23 Nov | 23 Nov | Passed |
| 4.1 | Runbook, executive summary, workflows | 2.1 | 22 Nov | 23 Nov | Done |
| 4.2 | Token optimisation guide | 3.6 | 23 Nov | 23 Nov | Done |
| 4.3 | Guardrails and reuse in every document | 4.1, 4.2 | 23 Nov | 23 Nov | Done |
| 4.4 | Presentation | 4.3 | 23 Nov | 23 Nov | Done |
| 4.5 | Interview Q&A | 4.3 | 23 Nov | 23 Nov | Done |
| G3 | Gate: learning module | 4.1 to 4.5 | [TBC] | [TBC] | Owner sign-off [TBC] |
| 5.1 | Hosted mode | G2 | 23 Nov | 23 Nov | Done |
| 5.2 | Render blueprint | 5.1 | 23 Nov | 23 Nov | Done |
| 5.3 | UAT deploy and live test | 5.2 | 23 Nov | 23 Nov | Done |
| 5.4 | Prod deploy and smoke test | 5.3 | 23 Nov | 23 Nov | Done |
| 5.5 | GitHub release v1.0.0 and profile | 5.4 | 23 Nov | 23 Nov | Done |
| 1.3 | Live scenario run and evaluation | 5.3 | 23 Nov | 23 Nov | Done |
| G1 | Gate: live and verified | 2.3, 3.2, 1.3 | 23 Nov | 23 Nov | Passed |
| 1.2 | Lifecycle framework and project plan | 1.1, 5.4 | 23 Nov | 23 Nov | Done |
| 6.1 | LinkedIn post with the deck | 4.4, 5.5 | 24 Nov | 24 Nov | Planned |
| 6.2 | Demo video (optional) | 5.4 | [TBC] | [TBC] | Not started |
| G4 | Gate: share | 5.4, 5.5, 6.1 | [TBC] | [TBC] | In progress |

All dates are 2026. G1 is listed after 1.3 because its last criterion, the scenario run, came after the UAT deploy.

**Critical path:** 1.1 → 2.1 → 2.2 → G0 → 3.1 → 3.2 → 3.3 → 3.4 → 3.5 → 3.6 → G2 → 5.1 → 5.2 → 5.3 → 5.4 → 5.5 → 6.1 → G4. The next item on it is the LinkedIn post (6.1).

Dependencies and status are also tracked in the PMO - Critical Path Planner under PM004.

## 3. Resources

One person delivered PM004, with an AI assistant for build support; no other people or paid tools were needed.

| Role | Person | Skills | Allocation | Period |
| --- | --- | --- | --- | --- |
| Owner, product manager, project manager and tester | Naveen Nigam | Product and project management, banking operations, UAT | Part-time, shared with other projects | 22 Nov 2026 onwards |
| Build support: code, tests, documents | Claude (AI assistant) | Python, FastAPI, prompt design, technical writing | On request | 22 to 23 Nov 2026 |

**Tools and environments:** Python 3.12 with FastAPI and SQLite; pytest; GitHub (code, CI, releases); Render (UAT and Prod); Anthropic API with Claude Sonnet 5.5; Claude Docs and Slides for the documents and deck; a Windows PC for local runs.

## 4. Cost and budget

The only running cost is Claude API usage. The daily caps keep the worst case to about USD 3.70 a day, even if every allowed call is used. No budget was set at the start, so the baseline below is the measured run cost (PM004_07, section 5).

| Cost line | Basis | Planned | Actual |
| --- | --- | --- | --- |
| Hosting: Render, 2 services | Free plan | USD 0 | USD 0 |
| Code hosting and CI: GitHub | Free for public repositories | USD 0 | USD 0 |
| Software: Python, FastAPI, SQLite | Open source | USD 0 | USD 0 |
| Claude API: build and testing | Usage-based | Not set | [TBC] from the Anthropic console |
| Claude API: Prod, worst case | 300 calls a day at up to USD 0.0093 per call | Up to about USD 2.80 a day | [TBC] monthly from the console |
| Claude API: UAT, worst case | 100 calls a day at up to USD 0.0093 per call | Up to about USD 0.93 a day | [TBC] monthly from the console |

**Typical cost per question (measured):** USD 0 for Basic, about USD 0.0045 for RAG and USD 0.014 for the agent.

**Contingency:** a monthly spend limit set in the Anthropic console, which stops spending even if a cap or the code fails. The amount is [TBC] by the owner (charter open item).

## 5. Communication plan

PM004 is a portfolio project, so communication is about showing the work: each audience gets one channel suited to what it needs.

| Stakeholder | What they get | Channel | Frequency | Owner |
| --- | --- | --- | --- | --- |
| Recruiters and hiring managers | Live demo, deck, short project story | LinkedIn post with the PDF deck; profile Projects section | Once at launch (24 Nov 2026), then with major releases | Naveen Nigam |
| Interviewers | Two-minute explanation, demo walk-through, answers to likely questions | Live demo; Interview Q&A (PM004_08, private) | Per interview | Naveen Nigam |
| Developers and learners | Code, runbook, workflows, token guide | GitHub repository and releases | Each release | Naveen Nigam |
| Owner (self-review) | Gate results, defects, cost | This plan, PM004_02 and PM004_10 | At each gate and release | Naveen Nigam |

## 6. Quality plan

Quality is proven in three layers: offline tests on every change, a live check on UAT before Prod, and a recorded scenario run (PM004_10).

**Standards:** the guardrails in the charter (section 6.7): no answers beyond the documents for level 03; mock tools only; human approval before any irreversible action; no API key in code, chats or screenshots.

| Level | What is tested | Pass measure | Owner |
| --- | --- | --- | --- |
| Unit and integration (offline) | All five modes with a fake Claude client: routing, citations, weak-match cut-off, approvals, Plan/Act/Verify, hosted-mode caps and privacy | All 36 tests pass; GitHub Actions runs them on every push | Claude (build), Naveen Nigam (review) |
| UAT (live) | Changed levels with real questions on the UAT site | Correct, cited answers; approvals still asked; no new defect | Naveen Nigam |
| Prod smoke test | Health page and one real question | Cited answer; health shows Claude configured | Naveen Nigam |
| Scenario run | Shared questions and agent goals across all levels | Recorded in PM004_10 with tokens, cost and time | Naveen Nigam |

**AI output checks:** level 02 must not state company facts; level 03 must cite or refuse; levels 04 and 05 must ask before blocking a card; the agent must look before it acts.

**Defect log:** defects go into PM004_10 (section 4) and the changelog. Example: D1, a placeholder email draft, was found in the scenario run and fixed in 1.0.1.

## 7. Procurement

Nothing had to be bought; the only paid item is Claude API usage on the owner's own key.

| Item | Vendor | Cost | Terms | Owner | Status |
| --- | --- | --- | --- | --- | --- |
| Claude API access (Sonnet 5.5) | Anthropic | Usage-based; see section 4 | Pay as you go; monthly spend limit [TBC] | Naveen Nigam | Active |
| Web hosting, UAT and Prod | Render | USD 0 | Free plan: sleeps when idle, so the first visit can take up to a minute | Naveen Nigam | Active |
| Code hosting, CI and releases | GitHub | USD 0 | Free for public repositories | Naveen Nigam | Active |

## 8. Monitoring and control

The app monitors itself: health checks, daily caps and cost per answer. The owner reviews them at each release and whenever the demo is shared.

**Control checks (proposed tolerances)**

- **Availability:** Render's health check on `/api/health`. If Prod fails twice in a row, roll back (PM004_02, section 4).
- **Cost:** if monthly API spend passes the console limit, or a day's calls reach the cap, review the traffic before raising anything.
- **Quality:** any wrong or uncited company fact on Prod is treated as a defect, fixed through UAT, and logged in PM004_10.
- **Scope:** new levels, real integrations or real customer data are out of scope (charter section 5) and need a new charter version.

**Change log**

| Change | Impact | Decision | Date |
| --- | --- | --- | --- |
| Automation email drafts use approved templates (D1) | Patch release 1.0.1; no scope change | Approved by owner | 23 Nov 2026 |

**Issue log**

| # | Issue | Severity | Owner | Due | Status |
| --- | --- | --- | --- | --- | --- |
| I1 | Monthly API spend limit not yet set | Medium | Naveen Nigam | [TBC] | Open |
| I2 | Gate G3 owner sign-off not recorded | Low | Naveen Nigam | [TBC] | Open |

The full release history is in the repository's CHANGELOG.

## 9. Risk heat map

No charter risk sits in the red zone after delivery. The two high-impact risks (R1, R4) are mitigated in the app itself, and R2 is closed. Ratings are the charter's own, marked as proposed, and are reviewed at each gate.

| Probability \ Impact | Low | Medium | High |
| --- | --- | --- | --- |
| **High** |  | R5 Scope creep |  |
| **Medium** |  | R2 Key or setup blocks live use · R3 Weak retrieval or tool choice · R7 Material drifts between tools | R1 Levels look too similar |
| **Low** | R6 API costs grow |  | R4 Agent seen as safe for real actions |

| # | Status after delivery (23 Nov 2026) |
| --- | --- |
| R1 | Mitigated: sources, tools, Plan/Act/Verify and cost shown under every answer; PM004_10 records clear differences |
| R2 | Closed: live on UAT and Prod with the key held in Render |
| R3 | Mitigated: weak-match cut-off; fixed tools for Automation; look-before-act for the agent |
| R4 | Mitigated: all tools are mock; approval before blocking a card; stated in the app and runbook |
| R5 | Managed: real integrations and new levels sit in the backlog |
| R6 | Mitigated: daily caps, cost per answer, measured cost in PM004_07; spend limit still open (I1) |
| R7 | Managed: register in PM004_02; repo copies refreshed at each release |

## 10. Approval and baseline

Release 1.0.0 on 23 Nov 2026 is the baseline; later changes go through the change log in section 8 and the release flow in PM004_02.

| Name | Role | Decision | Date |
| --- | --- | --- | --- |
| Naveen Nigam | Owner and project manager | [TBC] | [TBC] |

**Baseline v1.0:** scope as in charter section 5; schedule as in section 2 (22 to 23 Nov 2026, sharing from 24 Nov 2026); cost as in section 4 (USD 0 fixed, API usage capped).

**Open items for this plan**

- [ ] Set the monthly API spend limit in the Anthropic console. Owner: Naveen Nigam. Due: [TBC]
- [ ] Record G3 sign-off and approve this baseline. Owner: Naveen Nigam. Due: [TBC]
- [ ] Post on LinkedIn and capture feedback for G4. Owner: Naveen Nigam. Due: 24 Nov 2026 for the post
- [ ] Fill in actual API spend from the Anthropic console at month end. Owner: Naveen Nigam. Due: 30 Nov 2026
