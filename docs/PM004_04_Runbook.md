# PM004_04 Runbook: ChatBot - Basics to Advance

23 Nov 2026 · Naveen Nigam

What the app is, how to run it, how to demo the five levels and what to do when something breaks. Learning prototype with demo data only; nothing it does changes a real system. Charter: [PM004_01](PM004_01_Project_Charter.md).

## 1. Summary

The app shows five chatbots side by side, from fixed rules to a goal-driven agent, all serving one fictional company, Bluewater Bank. Pick one on the left, ask a question, and every conversation is saved in the middle panel.

| # | Chatbot | What it does | Uses Claude | Try asking | Shown under the answer |
| --- | --- | --- | --- | --- | --- |
| 01 | Basic Chatbot | Guided menu: pick a topic, then follow-up buttons; typed questions matched by keyword; anything else returns the main menu | No | Click **Cards**, then **Block my card** | Follow-up buttons, mode: fixed_rules |
| 02 | Generative AI | Writes a free answer from the question alone; knows nothing about Bluewater Bank | Yes | Starter: "Draft an email to the bank asking for an update on payment PAY-1042" | "What this level did" |
| 03 | RAG | Finds matching text in `knowledge/` and answers only from it, with numbered citations and a Sources list (readable titles; click to see the passage) | Yes | "What is the leave policy?" | "What this level did": sources and match % |
| 04 | AI Automation | Keyword rules decide which demo tools to run; Claude summarises the results. No rule matched: a cited document search. Irreversible actions ask Yes / No first | Yes | Cards → "I lost my card. What should I do?" | "What this level did": tools, mock results, approval |
| 05 | Agentic AI | Plan, Act, Verify: Claude plans, runs read-only lookups, looks at the results, then decides whether any action is needed and checks the outcome against the goal; irreversible actions wait for approval | Yes | A gold goal, e.g. "My payment PAY-1042 is stuck. Check it and draft a complaint email to the bank" | Plan / Act / Verify steps and "Why an agent here" under every answer; the panel adds lookups, decision and checks |

**Same workflow everywhere:** every bot opens with the same five topics. In 01 a topic opens its fixed menu; in 02 to 05 it opens the same short list of questions to pick from, so you can compare answers directly. Each answer ends with follow-up buttons and **Main menu**: fixed in 01; suggested by Claude in 02, 03 and 05 (in 05 including actions the agent can take); in 04 fixed next steps on the same topic (after a card block: order a replacement card or raise a card ticket). In 05 each topic also shows one gold **agent goal**, and the three "Goals for the agent" stay above the message box.

**Cost:** every AI answer shows its Claude calls and input/output tokens in "What this level did"; use it to compare what each level costs. See [PM004_07 Token Optimisation](PM004_07_Token_Optimisation.md).

Rule of thumb: use the simplest level that fully solves the problem (decision guide in the charter, section 6.4).

**The same bot can be rebuilt or integrated for internal employees.** Bluewater Bank's customers are the demo audience, but the five-level design works just as well as an employee assistant: pointed at internal HR and policy documents and internal systems, it lets staff check leave and other policies and send out emails.

| Level | For employees, it would… |
| --- | --- |
| 01 Basic | Answer fixed HR and IT FAQs: holidays, office hours, how to request leave |
| 02 Generative AI | Help draft emails, messages and summaries |
| 03 RAG | Answer leave, travel, expense and IT policy questions from the company's own policies, with the policy cited |
| 04 AI Automation | Check a leave balance, raise an HR or IT ticket, draft an email to a manager for review |
| 05 Agentic AI | Handle goals such as "Plan two days off next week and draft the request": check balance, notice rule and team calendar, then ask the employee to approve before anything is sent |

The demo already contains the employee side as mock tools (leave balance, leave policy, email drafts), so moving to internal use means swapping in the company's documents and connecting the HR system, ticketing tool and email, behind company sign-in, with human approval kept before anything is sent or submitted.

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
| `CHATBOT_HISTORY_MESSAGES` | How many recent messages are re-sent to Claude each turn | 8 |

Use Haiku for long practice sessions to keep costs low, and Sonnet or Opus for demos.

## 5. Demo script

Click the same topic in all five bots, in order, and point out what changes. The questions below can also be typed.

| Question | 01 Basic | 02 Generative AI | 03 RAG | 04 AI Automation | 05 Agentic AI |
| --- | --- | --- | --- | --- | --- |
| "What is the leave policy?" | Fixed rule: leave needs approval, ask HR | General answer; does not know your policy | Quotes the demo policy (request 5 working days ahead) and cites `leave_policy.md` | Runs leave balance (8 days, mock) and leave policy tools, then summarises | Looks up balance and policy, decides no action is needed, verifies; may say a lower level would have done |
| "My payment was declined, what should I do?" | No rule: fallback message | General list of common causes | Uses `payments_support.md`: details to confirm, possible causes, escalate | Searches the knowledge base and summarises | Searches the guides, decides whether a ticket is needed, verifies |
| "I lost my card. What should I do?" (the **Cards** topic) | Card menu: how to block it | General advice | Card policy with source [1] | Asks **Yes, block the card / No, keep it active** first; blocks the demo card only after Yes | Checks the card rules, proposes blocking the card and waits for your Yes; shows Plan / Act / Verify |
| "My payment keeps failing, raise a support ticket" | Fallback | Explains it cannot raise tickets | Answers from the guides, no ticket | Also creates a demo ticket (DEMO-xxxxxxxx) | Looks first, raises the ticket because you asked, then verifies |
| "My payment PAY-1042 is stuck. Check it and draft a complaint email to the bank." (05 gold goal) | Payment update email template | Drafts a generic email | Payment guidance with source, no status | Payment status and an email draft, marked not sent | Checks the status first, then drafts an email that quotes it, and verifies |

**What to say at each step**
- 01 to 02: the bot now understands free text and writes, but it does not know your company.
- 02 to 03: answers now come from your own documents, with the source named.
- 03 to 04: the bot now does something through tools, not just answers.
- 04 to 05: the agent looks before it acts, decides its next step from what it found, verifies the result and says why an agent was (or was not) needed. That flexibility is why real actions still need your approval. Try a gold goal to see it earn its extra cost.

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
| "Why an agent here: the agent's decision could not be read" | Claude's decision reply was not valid JSON, so the agent safely did nothing | Ask again; the raw reply is shown in "What this level did" for diagnosis |
| Old chats gone | `chat_history.db` deleted or app run from another folder | Restore the backup copy into the app folder |

## 7. Extending, safety and backup

| To do this | Change | Note |
| --- | --- | --- |
| Teach the RAG bot your own content | Add a `.md` file to `knowledge/`; separate topics with a blank line | Demo or non-sensitive content only |
| Add a Basic menu topic | Add a node to `BASIC_TREE` in `app.py` (label, answer, follow-up options, keywords), link it from a parent's options, and add it to `BASIC_MATCH_ORDER` | Keep wording exact and approved |
| Add a demo tool | Add it to `tool()` and to `READ_ONLY_TOOLS` (only looks) or `ACTION_TOOLS` (changes something); add irreversible ones to `NEEDS_APPROVAL`; add a keyword rule for level 04 | Mock results only |
| Rebuild it for internal employees | Replace `knowledge/` with HR and policy documents, change the topics and Basic menu to employee questions, and connect the mock tools (leave balance, ticket, email draft) to the real HR system, ticketing tool and email | Add company sign-in; keep approval before anything is sent or submitted |
| Change the model | `ANTHROPIC_MODEL` in `.env` | Restart |
| Run the tests | `pip install -r requirements-dev.txt` then `pytest` | No key or internet needed |

**Guardrails**

**Guardrails are built in, enforced in code and covered by tests; they are not left to the prompt alone.** These are the controls that keep a live AI system safe, grounded and affordable.

| Type | Guardrail in this app |
| --- | --- |
| Input | Message length limit on the public demo; empty messages and unknown bots rejected |
| Grounding | RAG answers only from retrieved passages, cites each one, and refuses when nothing relevant is found; weak matches are dropped |
| Action | Tool allow-list; read-only tools run first and actions only after the decision step; Yes / No approval before anything irreversible; a No runs nothing |
| Safe failure | If the agent's plan or decision cannot be read, it takes no action and shows the raw reply |
| Scope | The agent may not widen the user's goal or raise tickets the documents already answer |
| Cost and abuse | Daily caps on Claude calls (whole app and per visitor), history cap, output token caps |
| Security and privacy | API key only on the server; Settings locked on the public demo; each visitor sees only their own chats; demo data and mock tools only |
| Transparency | "What this level did" shows sources, tools, decision, checks and cost for every answer |

**Not built yet (next for any live use):** prompt-injection checks on document text, masking of personal data before it reaches the model, moderation of inputs and outputs, and an automated evaluation set.

**Safety rules**
- Demo data only; never paste real client, payment or personal data.
- Tools stay mock: nothing is sent, submitted or booked.
- Actions that cannot be undone (blocking a card) always ask **Yes / No** first, in Automation and Agentic modes; the "What this level did" panel records whether you approved or declined.
- Never commit or share `.env`; it is excluded by `.gitignore`.

**Backup and reset**
- Backup: copy `chat_history.db` and `.env` somewhere safe while the app is stopped.
- Clear all chats: stop the app and delete `chat_history.db`; a new empty one is created on start.

## 8. Deployment: UAT and Prod

Both environments run on Render's free plan from this repository, defined in `render.yaml`: **UAT** deploys from the `uat` branch and **Prod** from `main`.

| Step | How |
| --- | --- |
| Release a change | Push to `uat`; Render deploys UAT automatically |
| Test on UAT | Run the demo script (section 5) on the UAT link; the footer shows the **UAT** tag |
| Promote to Prod | Merge `uat` into `main`; Render deploys Prod automatically |
| Roll back | Revert the commit on `main` (or redeploy the previous deploy in Render) |
| Secrets | `ANTHROPIC_API_KEY` and `ANTHROPIC_WORKSPACE_ID` are entered once in the Render dashboard; never in the repository |

**Hosted mode** (`CHATBOT_HOSTED=1`, set by `render.yaml`) makes a public link safe:

| Protection | Setting | UAT | Prod |
| --- | --- | --- | --- |
| Settings screen locked; key never shown | `CHATBOT_HOSTED` | On | On |
| Each browser sees only its own chats (cookie) | `CHATBOT_HOSTED` | On | On |
| Claude calls per day, whole app | `CHATBOT_DAILY_CLAUDE_CALLS` | 100 | 300 |
| Claude calls per day, per visitor | `CHATBOT_VISITOR_DAILY_CALLS` | 40 | 40 |
| Longest message | `CHATBOT_MAX_MESSAGE_CHARS` | 1,000 | 1,000 |

When a cap is reached the AI bots say so politely and Basic keeps working; caps reset at midnight UTC. Also set a monthly spend limit in the Anthropic console as a second guard.

**Free-plan behaviour:** the service sleeps after 15 minutes without visitors and the first visit then takes up to a minute to wake; chats are deleted whenever the service restarts or redeploys. Both are acceptable for a demo; a paid instance removes them.

