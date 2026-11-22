# Changelog

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
