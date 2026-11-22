# PM004_04 Runbook: ChatBot - Basics to Advance

22 Nov 2026 · Naveen Nigam

What the app is, how to run it, how to demo the five levels and what to do when something breaks. Learning prototype with demo data only; nothing it does changes a real system. Charter: [PM004_01](PM004_01_Project_Charter.md).

## 1. Summary

The app shows five chatbots side by side, from fixed rules to a goal-driven agent, all serving one fictional company, Bluewater Bank. Pick one on the left, ask a question, and every conversation is saved in the middle panel.

| # | Chatbot | What it does | Uses Claude | Try asking | Shown under the answer |
| --- | --- | --- | --- | --- | --- |
| 01 | Basic Chatbot | Guided menu: pick a topic, then follow-up buttons; typed questions matched by keyword; anything else returns the main menu | No | Click **Cards**, then **Block my card** | Follow-up buttons, mode: fixed_rules |
| 02 | Generative AI | Writes a free answer from the question alone; knows nothing about Bluewater Bank | Yes | Starter: "Draft an email to my manager asking for two days' leave next week" | "What this level did" |
| 03 | RAG | Finds matching text in `knowledge/` and answers only from it, with numbered citations and a Sources list (readable titles; click to see the passage) | Yes | "What is the leave policy?" | "What this level did": sources and match % |
| 04 | AI Automation | Keyword rules decide which demo tools to run; Claude summarises the results | Yes | "I need leave next week, check my balance" | "What this level did": tools and mock results |
| 05 | Agentic AI | Claude plans 2 to 4 steps, picks allowed demo tools, the app runs them, Claude explains and verifies | Yes | "Plan two days of leave next week and draft the email to my manager" | "What this level did": plan, tools, blocked tools, check |

**Same workflow everywhere:** every bot opens with the same five topics. In 01 a topic opens its fixed menu; in 02 to 05 it asks the same question, so you can compare answers directly. Each answer ends with follow-up buttons and **Main menu**: fixed in 01, suggested by Claude in 02 to 05.

Rule of thumb: use the simplest level that fully solves the problem (decision guide in the charter, section 6.4).

## 2. Files and what they do

| File or folder | What it is | Edit it? |
| --- | --- | --- |
| `run_windows.bat` | Double-click to start; first run asks for the key and creates `.env` | No |
| `app.py` | The server: the five chatbots, demo tools, retrieval, history, Claude calls | Only to add rules or tools (section 7) |
| `static/index.html` | The page in the browser: bot list, history, chat | Only for look and labels |
| `knowledge/*.md` | Documents the RAG bot (and tools in 04 and 05) search | Yes: add your own `.md` files |
| `.env` | Your API key, workspace ID and model (not in the repository) | Yes, in a text editor; never share it |
| `.env.example` | Template for `.env` | No |
| `chat_history.db` | Saved conversations; created on first run (not in the repository) | No; back it up |
| `tests/` | Offline test suite; Claude is replaced by a fake client | When behaviour changes |

## 3. First-time setup on Windows

1. Install Python 3.10 or newer from python.org. On the first installer screen, tick **Add Python to PATH**.
2. Download or clone this repository.
3. Double-click `run_windows.bat`.
4. Paste your Anthropic API key when asked and press Enter.
5. When asked for the workspace ID: paste it if your key needs one (starts with `wrkspc_`), otherwise press Enter.
6. Wait for the packages to install. The browser opens at http://127.0.0.1:8000; if the page shows an error, wait a few seconds and refresh.
7. Check the badge at the top right says **Claude connected ✓**. The app runs a free live test of the key when it starts; if the badge is red, click it to open **Settings**.
8. Open **02 Generative AI** and ask anything. A reply confirms the key works end to end.

The command window is the server: leave it open while you use the app.

**macOS or Linux:** `pip install -r requirements.txt`, copy `.env.example` to `.env` and fill it in, then `uvicorn app:app --reload` and open http://127.0.0.1:8000.

## 4. Daily use and settings

| Task | How |
| --- | --- |
| Start | Double-click `run_windows.bat` (no questions after the first run) |
| Stop | Close the command window, or press Ctrl+C in it |
| Switch chatbot | Click a bot in the left column; its own history appears in the middle |
| New conversation | **+ New chat** in the middle column |
| Reopen a conversation | Click it in the middle column |
| Send a message | Enter; Shift+Enter for a new line |

**Settings:** click **⚙ Settings** (top right) to paste a new key, set the workspace ID or change the model, then **Save and test**. No restart needed, and the key is never shown again in full. The values are saved in `.env`:

| Setting | What it does | Default |
| --- | --- | --- |
| `ANTHROPIC_API_KEY` | Your key from console.anthropic.com | Required |
| `ANTHROPIC_WORKSPACE_ID` | Only for keys not created inside a workspace | Blank |
| `ANTHROPIC_MODEL` | `claude-sonnet-5-5`, `claude-opus-5-5` or `claude-haiku-5-5` | `claude-sonnet-5-5` |
| `ANTHROPIC_MAX_TOKENS` | Longest reply length | 1500 |

Use Haiku for long practice sessions to keep costs low, and Sonnet or Opus for demos.

## 5. Demo script

Click the same topic in all five bots, in order, and point out what changes. The questions below can also be typed.

| Question | 01 Basic | 02 Generative AI | 03 RAG | 04 AI Automation | 05 Agentic AI |
| --- | --- | --- | --- | --- | --- |
| "What is the leave policy?" | Fixed rule: leave needs approval, ask HR | General answer; does not know your policy | Quotes the demo policy (request 5 working days ahead) and cites `leave_policy.md` | Runs leave balance (8 days, mock) and leave policy tools, then summarises | Makes a plan, picks the leave tools, explains and verifies |
| "My payment was declined, what should I do?" | No rule: fallback message | General list of common causes | Uses `payments_support.md`: details to confirm, possible causes, escalate | Searches the knowledge base and summarises | Plans the checks, searches, suggests next steps |
| "I lost my card. What should I do?" (the **Cards** topic) | Card menu: how to block it | General advice | Card policy with source [1] | Asks **Yes, block the card / No, keep it active** first; blocks the demo card only after Yes | Plans the steps, runs safe ones (e.g. a ticket), holds the block for your approval |
| "My payment keeps failing, raise a support ticket" | Fallback | Explains it cannot raise tickets | Answers from the guides, no ticket | Also creates a demo ticket (DEMO-xxxxxxxx) | May plan search, then ticket, then a check |
| "Can I take two days of leave next week? Draft the email to my manager." | Email flow rule asks for purpose, dates and tone | Drafts a generic email | Policy answer with source | Leave tools plus an email draft, marked not sent | Plans policy, balance and draft steps, then asks you to review |

**What to say at each step**
- 01 to 02: the bot now understands free text and writes, but it does not know your company.
- 02 to 03: answers now come from your own documents, with the source named.
- 03 to 04: the bot now does something through tools, not just answers.
- 04 to 05: the bot decides the steps itself; that flexibility is why real actions need human approval.

Results vary slightly between runs for modes 02 to 05.

## 6. Troubleshooting

| What you see | Likely cause | Fix |
| --- | --- | --- |
| `'python' is not recognized` | Python not installed or not on PATH | Reinstall Python and tick **Add Python to PATH** |
| Page will not load, or badge says **Start backend to connect** | Server window closed or still starting | Run `run_windows.bat` again; wait, then refresh |
| Badge says **Set up Claude** | No key saved | Click the badge, paste the key in Settings, Save and test |
| Badge says **Claude not connected · fix** | The live key test failed | Click the badge: Settings shows the exact reason and fix |
| "This key needs a workspace ID" | User-linked key (`sk-ant-usr-`) without a workspace ID | Settings > Workspace ID: paste the `wrkspc_` ID of your workspace |
| "Anthropic rejected the API key" (401) | Key mistyped, deleted or expired | Create a new key in console.anthropic.com > API keys; paste it in Settings; Save and test |
| "Your Anthropic account has no credit left" | No credit balance | Add credit in console.anthropic.com > Billing |
| "Too many requests or a usage limit was reached" (429) | Rate or spend limit reached | Wait a minute, or check limits in the Anthropic console |
| "Could not reach Anthropic" | No internet, or a proxy blocks it | Check the connection; mode 01 works offline |
| "The app's server is not responding" | The black window was closed | Run `run_windows.bat` again and refresh |
| Port 8000 already in use | App already running in another window | Close the other window, or use the one already open |
| Basic bot says no rule matches | Expected: it only knows its fixed rules | Use the demo questions, or add a rule (section 7) |
| RAG says it found nothing relevant | Question words do not appear in the knowledge files | Rephrase, or add a document |
| Old chats gone | `chat_history.db` deleted or app run from another folder | Restore the backup copy into the app folder |

## 7. Extending, safety and backup

| To do this | Change | Note |
| --- | --- | --- |
| Teach the RAG bot your own content | Add a `.md` file to `knowledge/`; separate topics with a blank line | Demo or non-sensitive content only |
| Add a Basic menu topic | Add a node to `BASIC_TREE` in `app.py` (label, answer, follow-up options, keywords), link it from a parent's options, and add it to `BASIC_MATCH_ORDER` | Keep wording exact and approved |
| Add a demo tool | Add it to `tool()` and `ALLOWED_TOOLS`, and a keyword rule in the automation branch | Mock results only |
| Change the model | `ANTHROPIC_MODEL` in `.env` | Restart |
| Run the tests | `pip install -r requirements-dev.txt` then `pytest` | No key or internet needed |

**Safety rules**
- Demo data only; never paste real client, payment or personal data.
- Tools stay mock: nothing is sent, submitted or booked.
- Actions that cannot be undone (blocking a card) always ask **Yes / No** first, in Automation and Agentic modes; the "What this level did" panel records whether you approved or declined.
- Never commit or share `.env`; it is excluded by `.gitignore`.

**Backup and reset**
- Backup: copy `chat_history.db` and `.env` somewhere safe while the app is stopped.
- Clear all chats: stop the app and delete `chat_history.db`; a new empty one is created on start.
