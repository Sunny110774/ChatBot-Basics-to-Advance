# Changelog

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
