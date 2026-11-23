"""ChatBot - Basics to Advance: five chatbots, one per stage of AI evolution.

All five work on one fictional company, Bluewater Bank, so their answers can be compared
like for like: the same questions, the same knowledge files and the same demo tools.
"""
import os, re, json, sqlite3, uuid, contextvars
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import anthropic

ROOT = Path(__file__).parent
DB = Path(os.getenv("CHATBOT_DB", str(ROOT / "chat_history.db")))  # override for tests
ENV_FILE = Path(os.getenv("CHATBOT_ENV", str(ROOT / ".env")))      # override for tests
KD = ROOT / "knowledge"
MODELS = ["claude-sonnet-5-5", "claude-haiku-5-5", "claude-opus-5-5"]
MAX_TOKENS = int(os.getenv("ANTHROPIC_MAX_TOKENS", "1500"))  # cap for answers the user reads
JSON_MAX_TOKENS = 800  # cap for short internal JSON steps (agent plan and decision)
HISTORY_MESSAGES = int(os.getenv("CHATBOT_HISTORY_MESSAGES", "8"))  # only the most recent turns are re-sent to Claude


# ---------- settings: .env file next to app.py, editable from the in-app Settings screen ----------
def load_env_file():
    if not ENV_FILE.exists():
        return
    for line in ENV_FILE.read_text(encoding="utf8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def save_env(values):
    """Update or add KEY=value lines in .env, keeping any other lines as they are."""
    lines = ENV_FILE.read_text(encoding="utf8").splitlines() if ENV_FILE.exists() else []
    done = set()
    for i, line in enumerate(lines):
        k = line.split("=", 1)[0].strip()
        if k in values:
            lines[i] = f"{k}={values[k]}"
            done.add(k)
    lines += [f"{k}={v}" for k, v in values.items() if k not in done]
    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf8")
    for k, v in values.items():
        os.environ[k] = v


def model():
    return os.getenv("ANTHROPIC_MODEL") or MODELS[0]


def key_hint():
    k = os.getenv("ANTHROPIC_API_KEY", "")
    return f"{k[:10]}...{k[-4:]}" if len(k) > 16 else ""


load_env_file()
LAST_CHECK = {"status": "untested", "message": "Connection not tested yet.", "checked_at": None}

app = FastAPI(title="ChatBot - Basics to Advance")
app.mount("/static", StaticFiles(directory=str(ROOT / "static")), name="static")


def now():
    return datetime.now(timezone.utc).isoformat()


def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


with conn() as c:
    c.execute("CREATE TABLE IF NOT EXISTS conversations(id TEXT PRIMARY KEY,bot TEXT,title TEXT,created_at TEXT,updated_at TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY AUTOINCREMENT,conversation_id TEXT,role TEXT,content TEXT,created_at TEXT)")
    cols = [r["name"] for r in c.execute("PRAGMA table_info(messages)").fetchall()]
    if "meta" not in cols:  # older databases: add the column that stores "what this level did"
        c.execute("ALTER TABLE messages ADD COLUMN meta TEXT")


class NewConv(BaseModel):
    bot: str


class ChatReq(BaseModel):
    conversation_id: str
    bot: str
    message: str


class SettingsReq(BaseModel):
    api_key: Optional[str] = ""
    workspace_id: Optional[str] = ""
    model: Optional[str] = ""


BOTS = {"basic", "generative", "rag", "automation", "agentic"}


# ---------- Claude connection and plain-English errors ----------
class ClaudeError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status, self.message = status, message


FIX_KEY = "Open Settings (top right), paste a new key from console.anthropic.com > API keys, and click Save and test."


def friendly(e):
    """Turn an Anthropic SDK error into a reason plus the exact fix."""
    if isinstance(e, ClaudeError):
        return e
    if isinstance(e, anthropic.APIConnectionError):
        return ClaudeError(502, "Could not reach Anthropic. Check your internet connection, then try again.")
    if isinstance(e, anthropic.APIStatusError):
        code = getattr(e, "status_code", 0)
        detail = (getattr(e, "message", "") or str(e))
        low = detail.lower()
        if code == 401:
            return ClaudeError(401, "Anthropic rejected the API key: it is mistyped, deleted or expired. " + FIX_KEY)
        if "workspace" in low:
            return ClaudeError(400, "This key needs a workspace ID. Open Settings and paste your workspace ID (it starts with wrkspc_), or create the key inside a workspace.")
        if "credit" in low or "billing" in low:
            return ClaudeError(402, "Your Anthropic account has no credit left. Add credit in console.anthropic.com > Billing, then try again.")
        if code == 403:
            return ClaudeError(403, "This key is not allowed to use this model or workspace. Check the workspace ID in Settings, or choose another model.")
        if code == 404:
            return ClaudeError(404, f"The model '{model()}' is not available to this key. Choose another model in Settings.")
        if code == 429:
            return ClaudeError(429, "Too many requests or a usage limit was reached. Wait a minute, or check limits in console.anthropic.com.")
        if code >= 500:
            return ClaudeError(503, "Anthropic is busy or unavailable right now. Try again in a minute.")
        return ClaudeError(502, f"Claude request failed ({code}): {detail}")
    return ClaudeError(502, "Claude request failed for an unexpected reason. Check the server window for details.")


def client():
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise ClaudeError(400, "No API key is set. Open Settings (top right), paste your Anthropic API key and click Save and test.")
    headers = {}
    if os.getenv("ANTHROPIC_WORKSPACE_ID"):  # needed for user-linked keys (sk-ant-usr-...)
        headers["anthropic-workspace-id"] = os.environ["ANTHROPIC_WORKSPACE_ID"]
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"], default_headers=headers or None)


def record_check(ok, message):
    LAST_CHECK.update(status="ok" if ok else "failed", message=message, checked_at=now())
    return dict(LAST_CHECK)


def test_connection():
    """A real but free check: count the tokens of a one-word message (no answer is generated)."""
    try:
        c = client()
        msgs = [{"role": "user", "content": "ping"}]
        try:
            c.messages.count_tokens(model=model(), messages=msgs)
        except AttributeError:  # very old SDKs have no token counting; fall back to a 1-token reply
            c.messages.create(model=model(), max_tokens=1, messages=msgs)
        return record_check(True, f"Connected to Claude ({model()}).")
    except Exception as e:
        return record_check(False, friendly(e).message)


def clean_messages(msgs):
    """Claude needs turns that alternate user/assistant and start with the user.
    Merge repeats (e.g. a user message saved before a failed request)."""
    out = []
    for m in msgs:
        if m["role"] not in ("user", "assistant") or not str(m["content"]).strip():
            continue
        if out and out[-1]["role"] == m["role"]:
            out[-1]["content"] += "\n\n" + m["content"]
        else:
            out.append({"role": m["role"], "content": m["content"]})
    while out and out[0]["role"] != "user":
        out.pop(0)
    return out


USAGE = contextvars.ContextVar("usage", default=None)  # token use of the current request, one entry per Claude call


def llm(system, msgs, max_tokens=None, step="answer"):
    try:
        r = client().messages.create(model=model(), max_tokens=max_tokens or MAX_TOKENS,
                                     system=system, messages=clean_messages(msgs))
        text = "".join(b.text for b in r.content if getattr(b, "type", "") == "text").strip()
        u, log = getattr(r, "usage", None), USAGE.get()
        if log is not None:
            log.append({"step": step, "input": int(getattr(u, "input_tokens", 0) or 0), "output": int(getattr(u, "output_tokens", 0) or 0)})
        if LAST_CHECK["status"] != "ok":
            record_check(True, f"Connected to Claude ({model()}).")
        return text or "No response was generated."
    except Exception as e:
        err = friendly(e)
        if err.status in (400, 401, 402, 403, 404):  # setup problems, not passing outages
            record_check(False, err.message)
        raise HTTPException(err.status, err.message)


# ---------- storage ----------
def save(cid, role, content, meta=None):
    with conn() as c:
        c.execute("INSERT INTO messages(conversation_id,role,content,created_at,meta) VALUES(?,?,?,?,?)",
                  (cid, role, content, now(), json.dumps(meta) if meta else None))
        first = c.execute("SELECT content FROM messages WHERE conversation_id=? AND role='user' ORDER BY id LIMIT 1", (cid,)).fetchone()
        title = (first["content"][:40] + ("…" if len(first["content"]) > 40 else "")) if first else "New conversation"
        c.execute("UPDATE conversations SET title=?,updated_at=? WHERE id=?", (title, now(), cid))


def history(cid):
    with conn() as c:
        rows = c.execute("SELECT role,content,meta FROM messages WHERE conversation_id=? ORDER BY id", (cid,)).fetchall()
    return [{"role": r["role"], "content": r["content"], "meta": json.loads(r["meta"]) if r["meta"] else None} for r in rows]


# ---------- 01 Basic: fixed rules with a guided menu ----------
# Each node: button label, fixed answer, follow-up options (node ids), keywords for typed questions.
# Answers are demo content for a fictional bank and company, not real policies.
BASIC_TREE = {
    "menu": {"label": "Main menu", "answer": "Welcome to Bluewater Bank (a fictional demo company). Choose a topic below; this Basic bot only knows these fixed answers.",
             "options": ["hours", "branches", "cards", "leave", "email"], "keywords": ["menu", "help", "start", "hi", "hello"]},
    # top level
    "hours": {"label": "Banking hours", "answer": "Bluewater Bank branches are open Monday to Friday, 9 AM to 5 PM. Online banking is available 24x7.",
              "options": ["holidays", "cutoff", "menu"], "keywords": ["banking hours", "bank hours", "opening hours", "working hours", "open", "timing"]},
    "branches": {"label": "Branches and ATMs", "answer": "Bluewater Bank has a fixed list of branches and ATMs. Pick what you need below.",
                 "options": ["nearest", "atm_limit", "menu"], "keywords": ["branch", "branches", "location", "locations", "atm"]},
    "cards": {"label": "Cards", "answer": "I can help with common card questions. Pick one below.",
              "options": ["block", "not_working", "menu"], "keywords": ["card", "cards"]},
    "leave": {"label": "Leave policy", "answer": "Planned leave needs manager approval and should be requested 5 working days ahead.",
              "options": ["apply", "balance", "menu"], "keywords": ["leave policy", "leave", "vacation", "holiday leave", "time off"]},
    "email": {"label": "Write an email", "answer": "I have fixed email templates. Choose one and fill in the [brackets] yourself.",
              "options": ["leave_email", "status_email", "menu"], "keywords": ["email", "mail", "draft", "write"]},
    # second level
    "holidays": {"label": "Holiday schedule", "answer": "Bluewater Bank branches are closed on weekends and national public holidays. Online banking stays available.",
                 "options": ["cutoff", "menu"], "keywords": ["holiday schedule", "public holiday", "closed"]},
    "cutoff": {"label": "Same-day payment cut-off", "answer": "Payments submitted before 2 PM on a working day are processed the same day; later ones go the next working day.",
               "options": ["hours", "menu"], "keywords": ["cut-off", "cutoff", "same day", "same-day"]},
    "nearest": {"label": "Find nearest branch", "answer": "Use the branch locator on the Bluewater Bank website or app and enter your PIN code. A Basic bot cannot look up your location.",
                "options": ["atm_limit", "menu"], "keywords": ["nearest", "near me", "closest"]},
    "atm_limit": {"label": "ATM withdrawal limit", "answer": "The daily ATM withdrawal limit is 25,000 per card.",
                  "options": ["nearest", "menu"], "keywords": ["withdrawal limit", "atm limit", "cash limit"]},
    "block": {"label": "Block my card", "answer": "Call the 24x7 helpline or use App > Cards > Block card. A Basic bot can only tell you how; blocking it for you is an action, which is level 04 AI Automation.",
              "options": ["not_working", "menu"], "keywords": ["block", "lost", "stolen"]},
    "not_working": {"label": "Card not working", "answer": "Check that the card is not expired, blocked or over its limit, and that the PIN is correct. If it still fails, contact support.",
                    "options": ["block", "menu"], "keywords": ["not working", "declined", "failed", "card error"]},
    "apply": {"label": "How do I apply?", "answer": "Apply in the HR portal: Leave > New request, choose dates and the leave type, then submit for manager approval.",
              "options": ["balance", "leave_email", "menu"], "keywords": ["apply", "how do i apply", "request leave"]},
    "balance": {"label": "My leave balance", "answer": "A Basic bot cannot see your balance: that needs a lookup in the HR system, which is what level 04 AI Automation adds.",
                "options": ["apply", "menu"], "keywords": ["balance", "how many days", "remaining"]},
    "leave_email": {"label": "Leave request email", "answer": "Subject: Leave request: [dates]\n\nHi [manager],\n\nI would like to take leave from [start date] to [end date] for [reason]. [Colleague] has agreed to cover urgent work, and my current tasks are up to date.\n\nCould you please approve?\n\nThanks,\n[Your name]",
                    "options": ["status_email", "apply", "menu"], "keywords": ["leave email", "leave mail", "leave request email"]},
    "status_email": {"label": "Status update email", "answer": "Subject: Status update: [project] ([date])\n\nHi [name],\n\nDone: [what was completed]\nNext: [what happens next]\nRisks or help needed: [any blockers]\n\nRegards,\n[Your name]",
                     "options": ["leave_email", "menu"], "keywords": ["status email", "status update", "update email"]},
}
# Typed questions: check specific (second-level) topics before broad ones.
BASIC_MATCH_ORDER = ["leave_email", "status_email", "holidays", "cutoff", "nearest", "atm_limit", "block", "not_working",
                     "apply", "balance", "hours", "branches", "cards", "leave", "email", "menu"]


def basic_options(node_id):
    return [BASIC_TREE[o]["label"] for o in BASIC_TREE[node_id]["options"]]


def basic(q):
    """Return (answer, follow-up option labels). Buttons send their label; typed text is matched by keywords."""
    s = q.lower().strip()
    for nid, node in BASIC_TREE.items():
        if s == node["label"].lower():
            return node["answer"], basic_options(nid)
    for nid in BASIC_MATCH_ORDER:
        words = re.findall(r"[a-z0-9-]+", s)
        for k in BASIC_TREE[nid]["keywords"]:
            if (" " in k and k in s) or (" " not in k and k in words):
                return BASIC_TREE[nid]["answer"], basic_options(nid)
    return ("No matching rule is configured, so this Basic bot cannot answer that question. Choose one of the topics below.",
            basic_options("menu"))


# ---------- shared topic menu: the same five topics and questions in every bot ----------
# Clicking a topic shows its questions; the user picks one. The questions are the same in bots 02-05,
# so their answers can be compared like for like. In bot 01 the topic opens its fixed menu branch instead.
TOPICS = [
    {"label": "Banking hours", "questions": ["What are Bluewater Bank's banking hours?",
                                             "What is the same-day payment cut-off?",
                                             "Is online banking available at weekends?"]},
    {"label": "Branches and ATMs", "questions": ["How do I find the nearest branch?",
                                                 "What is the ATM withdrawal limit?"]},
    {"label": "Cards", "questions": ["I lost my card. What should I do?",
                                     "My card is not working. What can I check?",
                                     "Can I share my card PIN or OTP with bank staff?"]},
    {"label": "Leave policy", "questions": ["Can I take two days of leave next week?",
                                            "What is my leave balance?",
                                            "How much notice do I need to give for leave?"]},
    {"label": "Write an email", "questions": ["Draft an email to my manager asking for two days' leave next week.",
                                              "Draft an email asking for an update on payment PAY-1042."]},
]
# Goals where the next step depends on what the agent finds: this is where an agent earns its extra cost.
AGENT_GOALS = [
    "My payment PAY-1042 hasn't arrived and I need it sorted today.",
    "I lost my card while travelling. Sort it out.",
    "Plan two days of leave next week and draft the email to my manager.",
]
MENU_INTRO = "Choose a topic, then a question. Every bot offers the same questions, so you can compare what each level adds."
FOLLOW_UPS = ("\n\nAfter your answer, add one final line in exactly this format: "
              "FOLLOW-UPS: <question 1> | <question 2> | <question 3>. "
              "Give three short follow-up questions (at most 12 words each) that the user might ask next about Bluewater Bank, "
              "written as the user would ask them, and suitable for this assistant to handle.")


def split_follow_ups(text):
    """Remove the FOLLOW-UPS line Claude adds and return (answer, up to 3 follow-up questions)."""
    m = re.search(r"(?:\A|\n)[ \t]*\**[ \t]*FOLLOW[- ]?UPS?[ \t]*\**[ \t]*:\s*(.+?)\s*$", text, re.I | re.S)
    if not m:
        return text.strip(), []
    qs = [q.strip(" -*•\"'") for q in re.split(r"\s*\|\s*|\n+", m.group(1)) if q.strip(" -*•\"'")]
    return text[:m.start()].rstrip(), qs[:3]


# ---------- 03 RAG: keyword retrieval over knowledge/*.md ----------
STOPWORDS = set("""a an and are as at be been but by can could do does for from has have how i if in is it its
me my of on or our please should so than that the their them then there these they this to us was we were what
when where which who why will with would you your about any into just not also more most some such only very""".split())


def words(text):
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOPWORDS and len(w) > 1}


MIN_RELATIVE_SCORE = 0.5  # drop weak matches: keep passages scoring more than half as well as the best one


def retrieve(q, k=3):
    """Rank blank-line-separated chunks by how many of the question's content words they contain.
    Weak matches (one shared word, e.g. 'PIN' in 'PIN code') are dropped so they never reach the answer."""
    terms = words(q)
    hits = []
    if not terms:
        return hits
    for f in sorted(KD.glob("*.md")):
        for chunk in re.split(r"\n\s*\n", f.read_text(encoding="utf8")):
            chunk = chunk.strip()
            if not chunk or chunk.startswith("#"):  # skip empty chunks and document titles
                continue
            score = len(terms & words(chunk)) / len(terms)
            if score > 0:
                hits.append({"score": score, "source": f.name, "text": chunk})
    hits = sorted(hits, key=lambda x: x["score"], reverse=True)
    keep = [h for h in hits if h is hits[0] or h["score"] > hits[0]["score"] * MIN_RELATIVE_SCORE][:k]
    return [dict(h, score=round(h["score"], 3)) for h in keep]


def doc_title(filename):
    """Readable title from a knowledge file's first heading, e.g. 'Bluewater Bank: cards'."""
    try:
        first = (KD / filename).read_text(encoding="utf8").splitlines()[0]
    except (OSError, IndexError):
        return filename
    return re.sub(r"\s*\(fictional demo company\)\s*$", "", first.lstrip("# ").strip()) or filename


def number_sources(hits):
    """Group passages by document and number the documents [1], [2], ... in order of relevance."""
    docs = []
    for h in hits:
        d = next((x for x in docs if x["source"] == h["source"]), None)
        if not d:
            d = {"n": len(docs) + 1, "source": h["source"], "title": doc_title(h["source"]), "score": h["score"], "passages": []}
            docs.append(d)
        d["passages"].append(h["text"])
    return docs


# ---------- 04/05 allow-listed demo tools (mock data; nothing outside the app changes) ----------
READ_ONLY_TOOLS = {"leave_balance", "leave_policy", "search_knowledge", "payment_status"}  # look: change nothing
ACTION_TOOLS = {"create_ticket", "email_draft", "block_card", "order_replacement_card"}      # act: change something (mock)
ALLOWED_TOOLS = READ_ONLY_TOOLS | ACTION_TOOLS


def tool(name, args):
    if name == "leave_balance":
        return {"available_days": 8, "source": "mock HR data for the demo employee"}
    if name == "leave_policy":
        return {"sources": retrieve("leave policy notice approval apply balance")}
    if name == "search_knowledge":
        return {"results": retrieve(args.get("query", ""))}
    if name == "create_ticket":
        return {"ticket_id": "DEMO-" + uuid.uuid4().hex[:8].upper(), "status": "created in demo only", "summary": str(args.get("summary", ""))[:300]}
    if name == "email_draft":
        return {"status": "draft prepared; not sent", "subject": args.get("subject", "Draft email"), "body": str(args.get("body", ""))[:1500]}
    if name == "block_card":
        return {"status": "card marked as blocked in the demo only; no real card was changed",
                "card": "demo card ending 4417"}
    if name == "order_replacement_card":
        return {"status": "replacement card ordered in the demo only; no real card was ordered",
                "card": "replacement for demo card ending 4417", "delivery": "5-7 working days to the registered address (mock)"}
    if name == "payment_status":
        ref = str(args.get("reference") or "").upper() or "not provided"
        return {"reference": ref, "status": "held for a routine fraud-prevention check (mock data)",
                "expected": "released or returned within 1 working day", "note": "mock lookup; not a real payment system"}
    return {"error": "Tool not allow-listed"}


def parse_json(text):
    """Find the first complete JSON object in a reply, even if wrapped in prose or code fences,
    or followed by extra text that contains braces."""
    dec = json.JSONDecoder()
    for i, ch in enumerate(text):
        if ch == "{":
            try:
                obj, _ = dec.raw_decode(text[i:])
                if isinstance(obj, dict):
                    return obj
            except ValueError:
                continue
    raise ValueError("no JSON object found")


def payment_ref(text):
    m = re.search(r"\b(PAY-?\d{3,})\b", text, re.I)
    return m.group(1).upper().replace("PAY", "PAY-").replace("PAY--", "PAY-") if m else ""


def automation_tools(q, text):
    """Fixed rules decide which tools run: the defining trait of automation (steps known in advance)."""
    results = []
    if any(x in q for x in ["leave", "vacation", "time off", "holiday"]):
        results += [{"tool": "leave_balance", "result": tool("leave_balance", {})},
                    {"tool": "leave_policy", "result": tool("leave_policy", {})}]
    if "card" in q and "replacement" in q:
        results.append({"tool": "order_replacement_card", "result": tool("order_replacement_card", {})})
    elif "card" in q and any(x in q for x in ["block", "lost", "stolen", "freeze"]):
        results.append({"tool": "block_card", "result": tool("block_card", {})})
    if "payment" in q and any(x in q for x in ["status", "where", "track", "stuck", "pay-", "check"]):
        results.append({"tool": "payment_status", "result": tool("payment_status", {"reference": payment_ref(text)})})
    elif any(x in q for x in ["payment", "declined", "support"]):
        results.append({"tool": "search_knowledge", "result": tool("search_knowledge", {"query": text})})
    if "ticket" in q:
        results.append({"tool": "create_ticket", "result": tool("create_ticket", {"summary": text})})
    if any(x in q for x in ["email", "mail", "draft"]):
        results.append({"tool": "email_draft", "result": tool("email_draft", {"subject": "Draft based on request", "body": "Please review before sending.\n\nRequest: " + text})})
    return results


# ---------- human approval for actions that cannot be undone ----------
NEEDS_APPROVAL = {"block_card": "block the demo card ending 4417. A blocked card cannot be unblocked; a replacement would be ordered"}
APPROVE = {"block_card": "Yes, block the card"}
DECLINE = {"block_card": "No, keep it active"}

# What the Automation bot can actually do: its follow-ups only offer these tasks.
AUTOMATION_TASKS = {
    "leave_balance": "What is my leave balance?",
    "block_card": "I lost my card, please block it",
    "order_replacement_card": "Order a replacement card",
    "payment_status": "Check the status of payment PAY-1042",
    "create_ticket": "Raise a support ticket for a failed payment",
    "card_ticket": "Raise a support ticket about my card",
    "email_draft": "Draft an email to my manager about my leave",
}
# The natural next steps after each task, so follow-ups stay on the same topic.
NEXT_TASKS = {
    "leave_balance": ["email_draft"],
    "leave_policy": ["email_draft"],
    "email_draft": ["leave_balance"],
    "block_card": ["order_replacement_card", "card_ticket"],
    "order_replacement_card": ["card_ticket"],
    "payment_status": ["create_ticket"],
    "create_ticket": ["payment_status"],
    "card_ticket": [],
    "search_knowledge": [],
}
# If the user says No to an action, offer only steps that still make sense without it.
AFTER_DECLINE = {"block_card": ["card_ticket"]}


def automation_follow_ups(done):
    """Fixed follow-ups: real tasks on the same topic as the ones just done, then the main menu."""
    out = []
    for name in done:
        for nxt in NEXT_TASKS.get(name, []):
            if nxt not in done and AUTOMATION_TASKS[nxt] not in out:
                out.append(AUTOMATION_TASKS[nxt])
    return out[:3] + ["Main menu"]


TOOL_NAMES = {"search_knowledge": "company documents", "leave_balance": "leave balance", "leave_policy": "leave policy",
              "payment_status": "payment status", "create_ticket": "raised a support ticket", "email_draft": "drafted an email",
              "block_card": "block the card", "order_replacement_card": "ordered a replacement card"}


def plain(names):
    return ", ".join(TOOL_NAMES.get(n, n) for n in names)


def finish_verify(answer, meta):
    """Take Claude's VERIFY line out of the answer and put it in the Verify step."""
    m = re.search(r"(?:\A|\n)[ \t]*\**[ \t]*VERIFY[ \t]*\**[ \t]*:\s*(.+?)\s*(?=\n|$)", answer, re.I)
    result, reason = "not reported", "Claude did not report a goal check."
    if m:
        parts = [p.strip(" *") for p in m.group(1).split("|", 1)]
        result = parts[0].lower() if parts[0].lower() in ("met", "partly", "not met") else "partly"
        reason = parts[1] if len(parts) > 1 else ""
        answer = (answer[:m.start()] + answer[m.end():]).strip()
    meta["verify"].update(result=result, reason=reason)
    meta["verification"] = f"Goal {result}" + (f": {reason}" if reason else "")
    meta["workflow"][-1]["detail"] = f"Goal {result}" + (f": {reason}" if reason else "")
    return answer


def pending_approval(prior):
    """The action the last assistant answer asked the user to approve, if any."""
    for m in reversed(prior):
        if m["role"] == "assistant":
            return (m.get("meta") or {}).get("awaiting")
    return None


def approval_reply(text, action):
    t = text.strip().lower()
    if t == APPROVE[action].lower() or t in {"yes", "y", "confirm", "approve", "yes please", "go ahead"}:
        return "approve"
    if t == DECLINE[action].lower() or t in {"no", "n", "cancel", "stop", "don't", "do not"}:
        return "decline"
    return None


# ---------- routes ----------
@app.get("/", response_class=HTMLResponse)
def home():
    return (ROOT / "static/index.html").read_text(encoding="utf8")


@app.get("/api/health")
def health():
    return {"status": "ok", "provider": "Anthropic", "model": model(),
            "llm_configured": bool(os.getenv("ANTHROPIC_API_KEY")), "connection": dict(LAST_CHECK)}


@app.get("/api/settings")
def get_settings():
    return {"key_set": bool(os.getenv("ANTHROPIC_API_KEY")), "key_hint": key_hint(),
            "workspace_id": os.getenv("ANTHROPIC_WORKSPACE_ID", ""), "model": model(), "models": MODELS}


@app.post("/api/settings")
def put_settings(b: SettingsReq):
    values = {}
    key = (b.api_key or "").strip()
    if key:
        if not key.startswith("sk-ant-") or len(key) < 30 or " " in key:
            raise HTTPException(400, "That does not look like an Anthropic API key. It should start with sk-ant- and have no spaces.")
        values["ANTHROPIC_API_KEY"] = key
    ws = (b.workspace_id or "").strip()
    if ws and not ws.startswith("wrkspc_"):
        raise HTTPException(400, "The workspace ID should start with wrkspc_. Leave it empty if your key does not need one.")
    values["ANTHROPIC_WORKSPACE_ID"] = ws
    if b.model:
        if b.model not in MODELS:
            raise HTTPException(400, "Unknown model.")
        values["ANTHROPIC_MODEL"] = b.model
    save_env(values)
    LAST_CHECK.update(status="untested", message="Settings saved; connection not tested yet.", checked_at=None)
    return get_settings()


@app.post("/api/settings/test")
def settings_test():
    return test_connection()


@app.get("/api/basic/menu")
def basic_menu():
    return {"answer": BASIC_TREE["menu"]["answer"], "options": basic_options("menu")}


@app.get("/api/menu")
def menu(bot: str = "basic"):
    """Topic menu for any bot. Basic sends the topic label (opens its menu branch); in AI bots a topic opens its list of shared questions."""
    if bot == "basic":
        return {"answer": BASIC_TREE["menu"]["answer"], "topics": [{"label": l, "send": l} for l in basic_options("menu") if l != "Main menu"]}
    out = {"answer": MENU_INTRO, "topics": [{"label": t["label"], "questions": t["questions"]} for t in TOPICS]}
    if bot == "agentic":
        out["goals"] = AGENT_GOALS
    return out


@app.get("/api/conversations")
def conversations(bot: Optional[str] = None):
    with conn() as c:
        if bot in BOTS:
            rows = c.execute("SELECT * FROM conversations WHERE bot=? ORDER BY updated_at DESC", (bot,)).fetchall()
        else:
            rows = c.execute("SELECT * FROM conversations ORDER BY updated_at DESC").fetchall()
    return [dict(r) for r in rows]


@app.post("/api/conversations")
def create(body: NewConv):
    if body.bot not in BOTS:
        raise HTTPException(400, "Unknown bot")
    cid = str(uuid.uuid4())
    ts = now()
    with conn() as c:
        c.execute("INSERT INTO conversations VALUES(?,?,?,?,?)", (cid, body.bot, "New conversation", ts, ts))
    return {"id": cid, "bot": body.bot, "title": "New conversation", "created_at": ts, "updated_at": ts}


@app.get("/api/conversations/{cid}")
def get_conv(cid):
    with conn() as c:
        conv = c.execute("SELECT * FROM conversations WHERE id=?", (cid,)).fetchone()
    if not conv:
        raise HTTPException(404, "Conversation not found")
    return {"conversation": dict(conv), "messages": history(cid)}


@app.post("/api/chat")
def chat(b: ChatReq):
    if b.bot not in BOTS:
        raise HTTPException(400, "Unknown bot")
    if not b.message.strip():
        raise HTTPException(400, "Empty message")
    with conn() as c:
        conv = c.execute("SELECT * FROM conversations WHERE id=?", (b.conversation_id,)).fetchone()
    if not conv:
        raise HTTPException(404, "Conversation not found")
    if conv["bot"] != b.bot:
        raise HTTPException(400, "Conversation belongs to a different bot")

    save(b.conversation_id, "user", b.message)
    prior = history(b.conversation_id)[:-1]
    msgs = [{"role": m["role"], "content": m["content"]} for m in prior[-HISTORY_MESSAGES:]] + [{"role": "user", "content": b.message}]
    usage_log = []
    USAGE.set(usage_log)
    q = b.message.lower()
    meta = {"mode": b.bot, "sources": [], "tools": []}

    if b.bot == "basic":
        answer, meta["options"] = basic(b.message)
        meta["mode"] = "fixed_rules"
        meta["did"] = "Matched your message to a fixed rule. No AI model was used."

    elif b.bot == "generative":
        answer = llm("You are the Generative AI demo assistant for Bluewater Bank, a fictional bank. "
                     "Answer helpfully from general knowledge only. You have no access to Bluewater Bank's documents, "
                     "systems or customer data, so never state its policies, balances or statuses as facts; "
                     "say when an answer would need company information." + FOLLOW_UPS, msgs)
        meta["did"] = "Claude answered from your question and this chat only. No company documents, no tools."

    elif b.bot == "rag":
        hits = retrieve(b.message)
        docs = number_sources(hits)
        meta["sources"] = [{"n": d["n"], "title": d["title"], "source": d["source"], "score": d["score"],
                            "passages": [p[:400] for p in d["passages"]]} for d in docs]
        files = len(list(KD.glob("*.md")))
        if not hits:
            answer = ("I couldn't find anything about that in Bluewater Bank's documents, so I won't guess. "
                      "Try asking about leave, payments, cards, branches, banking hours or escalation.")
            meta["did"] = f"Searched {files} knowledge files and found nothing relevant, so Claude was not called."
        else:
            context = "\n\n".join(f"[{d['n']}] {d['title']}\n" + "\n".join(d["passages"]) for d in docs)
            answer = llm("You answer questions for Bluewater Bank (fictional) using ONLY the numbered sources below. "
                         "If they do not contain the answer, say so plainly. After each fact, cite its source number in square brackets, "
                         "for example [1] or [1][2]. Never cite file names and do not add a list of sources; the app shows them." + FOLLOW_UPS
                         + " The follow-up questions must be answerable from Bluewater Bank's documents.\n\nContext:\n" + context, msgs)
            meta["did"] = f"Searched {files} knowledge files, picked the {len(hits)} best-matching passages from {len(docs)} document(s), and told Claude to answer only from them and cite them by number."

    elif b.bot in ("automation", "agentic") and pending_approval(prior) and approval_reply(b.message, pending_approval(prior)):
        # The user is answering an approval request from the previous turn.
        action = pending_approval(prior)
        if approval_reply(b.message, action) == "decline":
            answer = "Understood. Nothing was changed: the card stays active."
            meta["did"] = f"You declined the action ({action}), so it was not run. No AI model was used for this reply."
            meta["declined"] = [action]
            meta["options"] = ([AUTOMATION_TASKS[t] for t in AFTER_DECLINE.get(action, [])] if b.bot == "automation" else []) + ["Main menu"]
        else:
            results = [{"tool": action, "result": tool(action, {})}]
            meta["tools"] = results
            meta["approved"] = [action]
            answer = llm(f"You are Bluewater Bank's {'AI Automation' if b.bot == 'automation' else 'Agentic AI'} demo. The user has just approved this action, "
                         "and it has been carried out in the demo. Confirm what was done, based only on the tool result, and say clearly that it is mock "
                         "demo data and no real card or system was changed. Do not ask a question or offer further actions; the app shows the next steps as buttons."
                         "\n\nTool result:\n" + json.dumps(results), msgs)
            meta["did"] = f"You approved the action, so the app ran {action} (mock), then Claude confirmed the result."
            if b.bot == "automation":
                meta["options"] = automation_follow_ups({action})

    elif b.bot == "automation":
        results = automation_tools(q, b.message)
        held = [r["tool"] for r in results if r["tool"] in NEEDS_APPROVAL]
        if not results:
            # No fixed rule matched: fall back to the document search (the RAG step from level 03), with citations.
            hits = retrieve(b.message)
            docs = number_sources(hits)
            meta["tools"] = [{"tool": "search_knowledge", "result": {"passages_found": len(hits)}}]
            meta["sources"] = [{"n": d["n"], "title": d["title"], "source": d["source"], "score": d["score"],
                                "passages": [p[:400] for p in d["passages"]]} for d in docs]
            meta["fallback"] = True
            if not hits:
                answer = ("None of my fixed rules matched that, and Bluewater Bank's documents don't cover it either, so I won't guess. "
                          "I can check your leave balance, block or replace a card, check a payment, raise a ticket or draft an email.")
                meta["did"] = "No fixed rule matched your message, so it searched the company documents as a fallback. Nothing relevant was found, so Claude was not called."
            else:
                context = "\n\n".join(f"[{d['n']}] {d['title']}\n" + "\n".join(d["passages"]) for d in docs)
                answer = llm("You are Bluewater Bank's AI Automation demo (a fictional bank). No automated task matched the user's message, "
                             "so answer it using ONLY the numbered sources below. If they do not contain the answer, say so plainly. "
                             "After each fact, cite its source number in square brackets, for example [1]. Never cite file names and do not add "
                             "a list of sources; the app shows them. Do not ask a question or offer any further action.\n\nContext:\n" + context, msgs)
                meta["did"] = (f"No fixed rule matched your message, so it fell back to searching the company documents (the level 03 RAG step), "
                               f"found {len(hits)} relevant passage(s) in {len(docs)} document(s), and Claude answered from them with numbered citations.")
            meta["options"] = automation_follow_ups(set())
        elif held:
            action = held[0]
            meta["awaiting"] = action
            meta["tools"] = [r for r in results if r["tool"] not in NEEDS_APPROVAL]
            answer = (f"Before I do this, please confirm: I will {NEEDS_APPROVAL[action]}. "
                      "This is a demo, so nothing real will change, but a real bank would always ask first.")
            meta["did"] = f"Fixed rules picked {action}, which cannot be undone, so the app paused and asked for your approval instead of running it."
            meta["options"] = [APPROVE[action], DECLINE[action]]
        else:
            meta["tools"] = results
            answer = llm("You are Bluewater Bank's AI Automation demo. Summarise these tool results for the user, faithfully. "
                         "Say clearly that the data is mock demo data and that nothing in a real system was changed. "
                         "Use only results that answer the user's question and ignore the rest without mentioning them. "
                         "Do not ask a question or offer any further action; the app shows the next steps as buttons.\n\nTools:\n" + json.dumps(results), msgs)
            meta["did"] = "Fixed rules chose the tools from keywords in your message, ran them, then Claude summarised the results."
            done = {r["tool"] for r in results}
            if "card" in q and "create_ticket" in done:  # a card ticket stays on the card topic
                done = (done - {"create_ticket"}) | {"card_ticket"}
            meta["options"] = automation_follow_ups(done)

    else:  # agentic: look -> decide -> act -> answer
        # 1. Plan and look: Claude plans and picks READ-ONLY lookups. Nothing changes yet.
        plan = llm(
            "You are Bluewater Bank's Agentic AI demo (a fictional bank). The goal is exactly what the user asked: do not widen it. "
            "Make a short plan (2-4 steps) and pick the READ-ONLY lookups needed first, only from: "
            "search_knowledge (args: query, use the user's own words), leave_balance, leave_policy, payment_status (args: reference). "
            "Actions (tickets, emails, card changes) are decided later, after you see the lookup results. "
            "Return JSON only, with no other text: "
            "{\"goal\":\"...\",\"plan\":[...],\"lookups\":[{\"name\":\"...\",\"args\":{}}]}.", msgs, JSON_MAX_TOKENS, "plan")
        try:
            obj = parse_json(plan)
        except Exception:
            obj = {"plan": ["Understand the question", "Look it up", "Answer"], "lookups": []}
        observed, skipped = [], []
        for item in (obj.get("lookups") or obj.get("tools") or [])[:3]:
            name = item.get("name") if isinstance(item, dict) else None
            if name in READ_ONLY_TOOLS:
                observed.append({"tool": name, "step": "look", "result": tool(name, item.get("args") or {})})
            elif name:
                skipped.append(str(name))  # not allowed in the look step (unknown tool, or an action planned too early)
        if not observed:  # always look at the documents at least once
            observed.append({"tool": "search_knowledge", "step": "look", "result": tool("search_knowledge", {"query": b.message})})
        goal = str(obj.get("goal") or b.message)

        # 2. Decide: Claude sees what the lookups returned and decides whether any action is really needed.
        decision_raw = llm(
            "You are Bluewater Bank's Agentic AI demo. Below are the user's goal and what the read-only lookups returned. "
            "Decide whether any action is needed. Available actions: create_ticket (args: summary), email_draft (args: subject, body), "
            "block_card, order_replacement_card. Take an action ONLY if the user asked for it, or the goal clearly cannot be met without it "
            "(for example, a reported lost or stolen card must be blocked: propose block_card even if the user only asked what to do, because "
            "it is never run without the user's approval, so proposing it is safe). Never raise a ticket or draft an email for a question the lookups "
            "already answer. Stay within the user's question. Also explain honestly, in one or two plain sentences for a non-technical viewer, "
            "why this request did or did not need an agent: what depended on judging the results (choosing or skipping actions, combining "
            "several lookups, deciding the next step). If a simpler level would have been enough, say which one (03 RAG for a plain document "
            "question, 04 Automation for a fixed task). Return the decision as JSON only, with no other text: "
            "{\"actions\":[{\"name\":\"...\",\"args\":{},\"reason\":\"...\"}],\"why_agent\":\"...\"}. Keep each reason and why_agent short, "
            "and use plain double-quoted JSON strings with no line breaks inside them."
            "\n\nGoal: " + goal + "\n\nLookup results:\n" + json.dumps(observed), msgs, JSON_MAX_TOKENS, "decide")
        try:
            decision = parse_json(decision_raw)
        except Exception:
            decision = {"actions": [], "why_agent": "The agent's decision could not be read, so it safely took no action."}
            meta["decision_raw"] = decision_raw[:600]  # shown in the panel so a failure can be diagnosed
        acted, held, reasons = [], [], []
        for item in (decision.get("actions") or [])[:2]:
            name = item.get("name") if isinstance(item, dict) else None
            if name in NEEDS_APPROVAL:
                held.append(name)  # never run without the user's approval
                reasons.append(f"{name}: {item.get('reason', '')} (waiting for your approval)")
            elif name in ACTION_TOOLS:
                acted.append({"tool": name, "step": "act", "result": tool(name, item.get("args") or {})})
                reasons.append(f"{name}: {item.get('reason', '')}")
            elif name:
                skipped.append(str(name))
        meta["plan"] = obj.get("plan", [])
        meta["tools"] = observed + acted
        meta["skipped"] = skipped
        meta["decision"] = "; ".join(reasons) if reasons else "No action needed: the lookups answer the question."
        meta["why_agent"] = str(decision.get("why_agent") or "")
        if held:
            meta["awaiting"] = held[0]
        # App-side checks for the Verify step; Claude adds its own goal check in the answer (VERIFY line).
        checks = ["Every tool used is on the allow-list" + (f" ({len(skipped)} blocked)" if skipped else "")]
        failed = [t["tool"] for t in observed + acted if isinstance(t["result"], dict) and "error" in t["result"]]
        checks.append(f"Tool errors: {', '.join(failed)}" if failed else "All tools that ran returned a result")
        if held:
            checks.append(f"{held[0]} cannot be undone, so it is waiting for your approval")
        meta["verify"] = {"result": "", "reason": "", "checks": checks}
        looked = plain(t["tool"] for t in observed)
        did_act = plain(t["tool"] for t in acted) or "no action needed"
        meta["workflow"] = [
            {"step": "Plan", "detail": f"{len(meta['plan'])} steps towards: {goal[:120]}"},
            {"step": "Act", "detail": f"Checked {looked}, then decided: {did_act}" + (f"; asked your approval to {plain([held[0]])}" if held else "")},
            {"step": "Verify", "detail": ""},
        ]

        # 3. Answer: a short, customer-facing reply. Internals stay in the "What this level did" panel.
        verify_note = (" Then verify the outcome against the goal: add a line in exactly this format, before any other final line: "
                       "VERIFY: <met|partly|not met> | <one short sentence saying why>.")
        approval_note = (f" One step was NOT run because it cannot be undone: {NEEDS_APPROVAL[held[0]]}. "
                         "End the reply by asking the user to approve it." + verify_note + " Do not add follow-up questions."
                         if held else verify_note + FOLLOW_UPS + " At least one follow-up must be an action the agent can take for the user, "
                         "phrased as a request (for example 'Block my card', 'Order a replacement card', 'Raise a support ticket', "
                         "'Draft an email to my manager'), when one fits the topic and has not been done yet.")
        answer = llm("You are Bluewater Bank's Agentic AI demo (a fictional bank). Write a short, clear reply to the user, under 120 words "
                     "(longer only for a drafted email). Answer only what the user asked, using only the results below. Do not mention tools, "
                     "file names, scores, plans or internal steps; the app shows them separately. If an action was taken, say what was done. "
                     "Add one short sentence that this is demo data and nothing real was changed." + approval_note
                     + "\n\nGoal: " + goal + "\n\nResults:\n" + json.dumps({"lookups": observed, "actions": acted, "awaiting_approval": held}), msgs,
                     step="answer + verify")
        if held:
            meta["options"] = [APPROVE[held[0]], DECLINE[held[0]]]
        meta["did"] = ("Plan: Claude set the goal and planned. Act: it ran read-only lookups first, looked at the results, then decided whether any action was needed: "
                       + ("it took the action(s) below" if acted else "none was") + (", and paused one that cannot be undone until you approve it" if held else "")
                       + ". Verify: the app checked the tools, and Claude checked the outcome against the goal.")

    meta["usage"] = {"calls": len(usage_log), "input": sum(u["input"] for u in usage_log),
                     "output": sum(u["output"] for u in usage_log), "steps": usage_log}
    if b.bot != "basic":
        answer, follow = split_follow_ups(answer)
        if b.bot == "agentic" and "verify" in meta:
            answer = finish_verify(answer, meta)
        if "options" not in meta:  # fixed options (approvals, automation tasks) take priority
            meta["options"] = (follow + ["Main menu"]) if follow else ["Main menu"]
    save(b.conversation_id, "assistant", answer, meta)
    return {"answer": answer, "metadata": meta}
