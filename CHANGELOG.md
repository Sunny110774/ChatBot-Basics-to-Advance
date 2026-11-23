# Changelog

## 0.9.3 - 2026-11-23
- Added **PM004_09 Presentation** (PDF, 9 slides): the problem, one slide per level, how to choose the level, what makes it ready for live use. Linked from the README.

## 0.9.2 - 2026-11-23
- **Guardrails section in every document:** the controls already built (input, grounding, action, safe failure, scope, cost and abuse, security and privacy, transparency) listed in one place, with the gaps still to close for live use (prompt-injection checks, personal-data masking, moderation, evaluation set). README and charter no longer describe guardrails as future-only.

## 0.9.1 - 2026-11-23
- Every document now states that the same bot can be rebuilt or integrated for internal employees (check leave and other policies, send out emails), with what each level would do for staff and what changes to make it real.

## 0.9.0 - 2026-11-23
- **Hosted mode for UAT and Prod** (`CHATBOT_HOSTED=1`): Settings locked and the key never shown; each browser sees only its own chats; daily caps on Claude calls for the whole app and per visitor (Basic keeps working when reached); message length limit; a footer explaining the public demo, with an environment tag (UAT).
- **Render blueprint** (`render.yaml`): UAT from the `uat` branch, Prod from `main`, free plan, Singapore region, health check, secrets entered in the dashboard.
- Runbook section 8: release flow (UAT, then Prod), rollback, hosted-mode settings and free-plan behaviour.
- 35 tests (4 new for hosted mode).

## 0.8.3 - 2026-11-23
- **Documents brought up to date with 0.8.2:** README, charter (v0.2), executive summary, runbook and workflows now describe the current app: Plan / Act / Verify, look-then-decide agent, approval for irreversible actions, numbered citations, weak-match cut-off, Automation's fixed follow-ups and cited fallback, gold agent goals, token use per answer, history cap and the 31-test suite.
- Technical and functional workflow diagrams redrawn (level 05 now three Claude calls; 04 can make none).

## 0.8.2 - 2026-11-23
- **No more emails to a manager:** the Write an email topic now drafts customer emails to the bank (payment update, missing card) in every bot, including Basic's templates and Automation's follow-ups.
- **One agent goal per topic in 05,** shown in gold under the topic's questions (for example Cards: "I lost my card. Block it and order a replacement."). The shared questions stay, so levels can still be compared like for like.
- The "Goals for the agent" strip now offers: a held payment needed today, a card lost while travelling, and 40,000 in cash today (over the ATM limit).
- The agent never orders a replacement card before the card is blocked.

## 0.8.1 - 2026-11-23
- **Agent decision is parsed robustly:** JSON is found even when wrapped in prose, code fences or followed by extra braces; the decision step has more room (800 tokens); if it still fails, the raw reply is shown in "What this level did" for diagnosis.
- **Lost card: the agent proposes blocking it** even when the user only asks what to do; it still waits for the user's approval.
- **Agent follow-ups include actions** it can take (block card, order replacement, raise ticket, draft email) when they fit.
- **Agent goals stay visible:** a "Goals for the agent" strip sits above the message box in 05 for the whole chat, instead of only on the welcome screen.

## 0.8.0 - 2026-11-23
- **Agentic AI shows Plan -> Act -> Verify on every answer** as a visible three-step strip, in plain language.
- **"Why an agent here"** note on each answer, written by the agent's decision step; it honestly says when a simpler level (03 RAG or 04 Automation) would have been enough.
- **Real Verify step:** the app checks the tools (allow-list, errors, approvals) and Claude checks the outcome against the goal (met / partly / not met) in the same reply call, so no extra call.
- **Agent goals on the 05 welcome screen** with a short explanation of why an agent is needed: a held payment that must be sorted today, a lost card while travelling, leave plus an email.
- **Token use measured on every answer:** "What this level did" shows Claude calls and input/output tokens per step (from the API's `usage` field).
- **History cap:** only the last 8 messages are re-sent (`CHATBOT_HISTORY_MESSAGES`); internal JSON steps are capped at 500 output tokens.
- **New doc: PM004_07 Token Optimisation**, with a reusable checklist for future projects.

## 0.7.0 - 2026-11-23
- **Agentic AI is now a look -> decide -> act loop.** Before, every tool in the plan ran at once, so a conditional step ("raise a ticket if unclear") ran even when the documents had already answered. Now:
  1. Claude plans and runs read-only lookups only (search, leave balance, leave policy, payment status).
  2. Claude sees the results and decides whether any action is needed (ticket, email, card), with a reason for each.
  3. Irreversible actions still wait for the user's approval.
  4. The reply is short and customer-facing; plan, lookups, decision and check move to "What this level did".
- The goal stays what the user asked; the agent no longer widens it.
- Tools are split into `READ_ONLY_TOOLS` and `ACTION_TOOLS`. One extra Claude call per question in level 05 (3 instead of 2).

## 0.6.4 - 2026-11-23
- **Automation's document fallback is now visible and cited:** when no fixed rule matches, level 04 searches the company documents (the level 03 RAG step), answers with numbered citations and a Sources list, and "What this level did" says "No fixed rule matched your message, so it fell back to searching the company documents". If nothing relevant is found it says so without calling Claude.

## 0.6.3 - 2026-11-23
- **Weak matches dropped from search:** the knowledge search keeps only passages scoring more than half as well as the best match. A question about sharing a card PIN no longer pulls in "PIN code" (postal code) from the branch passage. Applies to RAG, Automation and Agentic.
- **Automation summaries use only relevant results** and no longer list "lower-relevance" passages.

## 0.6.2 - 2026-11-22
- **Topics open a question list:** clicking a topic (for example **Cards**) in bots 02 to 05 now shows two or three questions to choose from, instead of sending a question on the user's behalf. Nothing is sent until the user picks. The questions are the same in every bot, so answers stay comparable.
- Each question was checked to retrieve its matching knowledge passage for RAG.

## 0.6.1 - 2026-11-22
- **Automation follow-ups stay on topic:** after blocking a card the buttons now offer "Order a replacement card" and "Raise a support ticket about my card", not unrelated tasks such as the leave balance. Leave leads to the email draft, payments to a support ticket.
- **New mock task `order_replacement_card`:** the replacement card Claude used to mention is now a real (mock) step with its own button.
- **No dangling offers:** Automation's summaries no longer ask questions or offer actions it cannot do; next steps appear only as buttons.
- **Declining a card block** offers only a support ticket, never a replacement for an active card.

## 0.6.0 - 2026-11-22

- **Human approval for irreversible actions:** blocking a card now asks **Yes, block the card / No, keep it active** first, in both AI Automation and Agentic AI. Declining runs nothing (no tool, no Claude call). The agent still runs its safe steps and holds only the irreversible one. The "What this level did" panel records approvals and declines.
- **Automation follow-ups are real tasks only:** level 04 now offers fixed follow-ups drawn from what its tools can actually do (leave balance, block card, payment status, support ticket, email draft), instead of open suggestions it could not carry out.
- Tests: 22 offline tests.

## 0.5.1 - 2026-11-22

- RAG citations: answers now use small numbered markers ([1], [2]) instead of file names, with a **Sources** list under the answer showing each document's readable title; click a source to see the exact passage used. One number per document.
- Retrieval no longer counts a document's title line as a passage.

## 0.5.0 - 2026-11-22

One workflow across all five bots.

- **Shared topic menu:** every bot opens with the same five topics (Banking hours, Branches and ATMs, Cards, Leave policy, Write an email). In 01 a topic opens its fixed menu branch; in 02 to 05 it sends the same question, so answers can be compared like for like.
- **Follow-up buttons in every bot:** levels 02 to 05 now end each answer with three follow-up questions suggested by Claude (in the same call, no extra cost) plus Main menu, matching the guided flow of level 01. Follow-ups are saved with the conversation.
- **Formatted answers:** Claude's Markdown (bold, lists, headings, dividers) now displays properly instead of raw symbols. Text is escaped first, so nothing in an answer can run as code.
- New endpoint `GET /api/menu?bot=<mode>`. Tests: 19 offline tests.

## 0.4.1 - 2026-11-22

- Fixed: requests failed with "`temperature` is deprecated for this model" on current Claude models. The app no longer sends a temperature setting.

## 0.4.0 - 2026-11-22

Made the five bots behave like one coherent product.

- **One shared demo company, Bluewater Bank (fictional):** the Basic menu, five rewritten knowledge files (banking hours and branches, cards, leave policy, payments support, escalation) and the demo tools all state the same facts.
- **Settings screen:** enter the API key, workspace ID and model in the app; **Save and test** runs a free live connection test. The key is saved only to `.env` and never returned to the page in full.
- **Honest status badge:** shows "Claude connected ✓" only after a real test passes; otherwise "Set up Claude" or "Claude not connected · fix". The test runs automatically at start-up.
- **Plain-English errors:** invalid or expired key, missing workspace ID, no credit, unavailable model, rate limits, outages and a closed server each explain the cause and the fix, with an Open Settings button.
- **Starter questions** for bots 02 to 05, and a **"What this level did"** panel under every AI answer (sources, tools with mock results, plan, blocked tools, final check), saved with the conversation.
- RAG ignores common words, so off-topic questions are refused without calling Claude.
- New demo tools for levels 04 and 05: `block_card` and `payment_status` (mock data).
- Tests: 16 offline tests.

## 0.3.0 - 2026-11-22

- Basic chatbot is now a guided menu: the welcome screen shows the main topics as buttons, every answer offers follow-up questions, and unrecognised questions return the main menu instead of a dead end.
- 16 demo topics: banking hours, holidays, payment cut-off, branches, ATM limit, cards (block, not working), leave policy (apply, balance) and email templates.
- New endpoint `GET /api/basic/menu`; Basic answers return their follow-up options in the metadata.
- Tests: 10 offline tests (new: menu and follow-ups).

## 0.2.0 - 2026-11-22

Moved from OpenAI to Anthropic Claude and prepared for GitHub.

- Replaced the `openai` SDK with `anthropic` (`messages.create` with a separate system prompt).
- Optional `ANTHROPIC_WORKSPACE_ID` header for keys that need one.
- Conversation turns are cleaned so they always alternate user/assistant, which fixes chats where an earlier request failed.
- Agentic plan parsing tolerates prose or code fences around the JSON.
- Real Anthropic error messages are shown in the chat (key, workspace, rate limit, connection).
- Settings can live in a local `.env` file; `run_windows.bat` creates it on first run and opens the browser.
- `CHATBOT_DB` setting so tests use a temporary database.
- Fixed: the welcome panel stayed above the first message of a new chat.
- Fixed: message box font (invalid CSS shorthand).
- Launcher runs the server without auto-reload, which on Windows could restart it mid-request ("Failed to fetch").
- Launcher detects a missing Python install (and the Microsoft Store shortcut) and explains how to fix it; also accepts the `py` launcher.
- Added: offline pytest suite for all five modes, GitHub Actions workflow, project charter, executive summary, workflows, runbook and diagrams.

## 0.1.0

First working prototype: five modes (Basic, Generative AI, RAG, AI Automation, Agentic AI), SQLite history, demo knowledge files and allow-listed mock tools, running on OpenAI.
