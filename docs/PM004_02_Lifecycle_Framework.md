# PM004_02 Lifecycle Framework: ChatBot - Basics to Advance

23 Nov 2026 · Naveen Nigam

This framework sets the stages every phase and every release of PM004 passes through, and the gates that close the phases in the charter (PM004_01, sections 7 and 8). PM004 ran all five phases in two days, 22 and 23 Nov 2026. Gates G0 to G2 passed, G3 waits for owner sign-off, and G4 closes once feedback from the LinkedIn post and demo is captured.

## 1. Lifecycle at a glance

Each phase, and each later release, moves through six stages in order. The gate in stage 5 decides whether the next phase starts.

1. **Define:** fix the scope of the phase or release.
2. **Design:** decide how it will work, including guardrails.
3. **Build:** change the code and the documents together.
4. **Test:** offline tests, then a live check on UAT.
5. **Gate review:** compare the evidence with the gate criteria; pass, pass with conditions, or hold.
6. **Release and learn:** promote to Prod, smoke-test, record the version and lessons.

Lessons and defects from stage 6 feed the Define stage of the next phase. Example: the evaluation run (PM004_10) found a weak email draft, which became release 1.0.1.

## 2. Stage detail

A stage is finished only when its exit check is met; its outputs become the evidence shown at the gate.

| Stage | Purpose | Key activities | Outputs | Exit check |
| --- | --- | --- | --- | --- |
| 1 Define | Fix the scope | Confirm objectives from PM004_01; list the user problem or defect; agree what is out of scope | Short scope note or changelog entry | The owner agrees the scope |
| 2 Design | Decide how it works | Choose the minimum level that solves it; place approval points; set data, cost and safety guardrails | Design notes in the workflows (PM004_06) and runbook (PM004_04) | Every write or irreversible action has an approval point and a mock or test path |
| 3 Build | Make the change | Code, prompts and documents changed together; one commit per change with a clear message | Commits on the `uat` branch | Code and documents describe the same behaviour |
| 4 Test | Prove it works safely | Offline test suite with a fake Claude client; live check on UAT with real questions; check citations, refusals and approvals | Green test run; UAT notes or an evaluation entry (PM004_10) | All tests pass; the UAT check shows no new defect |
| 5 Gate review | Decide go or no-go | Compare evidence with the gate criteria in section 3 | Gate result recorded in this document | Owner decision recorded |
| 6 Release and learn | Go live in a controlled way | Promote `uat` to `main` (Prod); smoke-test Prod; tag the version; update the changelog | Release note (CHANGELOG), GitHub release, live link | Prod health check passes and one real question answers correctly |

## 3. Phase gates and results

Five gates close the five charter phases; three have passed, one waits for sign-off and one for feedback. Criteria come from PM004_01 section 8.

| Gate | Closes | Evidence | Result | Date |
| --- | --- | --- | --- | --- |
| G0 | Phase 0: Base on Claude | Prototype moved from OpenAI to Claude; offline tests pass for all 5 modes | Passed | 22 Nov 2026 |
| G1 | Phase 1: Live and verified | All 5 modes answer live with a real key; history reopens; scenario set run and captured (PM004_10) | Passed | 23 Nov 2026 |
| G2 | Phase 2: Each level real | Rules only (01); live generation (02); cited answers and refusal when nothing matches (03); tools called, shown and approved (04); Plan, Act and Verify shown (05) | Passed (release 0.8.2) | 23 Nov 2026 |
| G3 | Phase 3: Learning module | Runbook, executive summary, workflows, token guide and presentation done and matching the app | Evidence ready; owner sign-off [TBC] | [TBC] |
| G4 | Phase 4: Share | Prod link live; GitHub release v1.0.0; LinkedIn post; feedback captured | In progress: link and release done 23 Nov 2026; post planned 24 Nov 2026; feedback [TBC] | [TBC] |

A gate result is pass, pass with conditions (each with an owner and a due date), or hold.

## 4. Release flow and versioning

Every change reaches Prod only through UAT. Each environment deploys automatically from its own branch on Render.

| Environment | Branch | Address | Daily Claude-call cap |
| --- | --- | --- | --- |
| Local | Any | http://127.0.0.1 (your PC) | None (your own key) |
| UAT | `uat` | https://chatbot-basics-to-advance-uat.onrender.com | 100 |
| Prod | `main` | https://chatbot-basics-to-advance.onrender.com | 300 |

**Steps for a release**

1. Run the offline tests locally; all must pass.
2. Commit to `uat` and push; Render redeploys UAT.
3. Check UAT: health page, one question per changed level, approvals still asked.
4. Point `main` at the tested `uat` commit and push; Render redeploys Prod.
5. Smoke-test Prod: health page, then one real question with a cited answer.
6. Update the changelog and create the GitHub release (tag `vX.Y.Z`).

**Versions** follow major.minor.patch: patch for a fix (1.0.1), minor for a new capability (1.1.0), major for a breaking change.

**Rollback:** redeploy the previous commit from the Render dashboard, or revert the commit and push. Keys and caps live in Render's environment settings, not in the code, so a rollback never touches secrets.

## 5. Document register

All documents use the name PM004_NN_Document_Name, numbered in creation order. Each lives as a Claude Doc and, except 08, as a copy in the repository's `docs` folder.

| Code | Document | Status | Where |
| --- | --- | --- | --- |
| PM004_01 | Project Charter | Draft v0.2 | Doc and repo |
| PM004_02 | Lifecycle Framework (this document) | Current | Doc and repo |
| PM004_03 | Project Plan | Current | Doc and repo |
| PM004_04 | Runbook | Current | Doc and repo |
| PM004_05 | Executive Summary | Current | Doc and repo |
| PM004_06 | Workflows | Current | Doc and repo |
| PM004_07 | Token Optimisation | Current, with measured cost | Doc and repo |
| PM004_08 | Interview Q&A | Current | Private doc only |
| PM004_09 | Presentation | Current (9 slides) | Slides and PDF in repo |
| PM004_10 | Evaluation | Current | Doc and repo |

The repository is the source of truth for code; the Claude Docs are the source of truth for documents, and the repo copies are refreshed at each release.

## 6. Governance

Naveen Nigam decides at every gate and release; Claude (AI assistant) builds, tests and documents on request. With one owner, the controls are kept light but written down.

| Area | How it works |
| --- | --- |
| Decisions | The owner approves scope, gate results and each promotion to Prod |
| Change control | Every change is a commit with a clear message and a changelog entry; anything that adds a write or irreversible action needs an approval point and a test first |
| Quality | No release without a green offline test run and a UAT check (section 4) |
| Cost | Daily call caps per environment and per visitor; cost per answer shown in the app; measured cost recorded in PM004_07 |
| Security | API keys only in Render or the local `.env`, never in code, chats or screenshots; settings locked on the public demo |
| Risks | Charter risks R1 to R7 (PM004_01 section 10) are reviewed at each gate; status is in the project plan (PM004_03) |

**Reuse for future projects:** keep the six stages, the UAT-then-Prod flow and the release checklist as they are. Change only the gate criteria and the document register.
