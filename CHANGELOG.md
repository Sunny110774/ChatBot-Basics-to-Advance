# Changelog

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
