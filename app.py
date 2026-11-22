import os, re, json, sqlite3, uuid
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
KD = ROOT / "knowledge"


# ---------- settings: environment variables, or a local .env file next to app.py ----------
def load_env_file():
    f = ROOT / ".env"
    if not f.exists():
        return
    for line in f.read_text(encoding="utf8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


load_env_file()
MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5")
MAX_TOKENS = int(os.getenv("ANTHROPIC_MAX_TOKENS", "1500"))

app = FastAPI(title="ChatBot - Basics to advance")
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


class NewConv(BaseModel):
    bot: str


class ChatReq(BaseModel):
    conversation_id: str
    bot: str
    message: str


BOTS = {"basic", "generative", "rag", "automation", "agentic"}


# ---------- Claude ----------
def client():
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise HTTPException(503, "Configure ANTHROPIC_API_KEY on the server. See README.md.")
    headers = {}
    if os.getenv("ANTHROPIC_WORKSPACE_ID"):  # only needed for keys not created inside a workspace
        headers["anthropic-workspace-id"] = os.environ["ANTHROPIC_WORKSPACE_ID"]
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"], default_headers=headers or None)


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


def llm(system, msgs):
    try:
        r = client().messages.create(
            model=MODEL, max_tokens=MAX_TOKENS, temperature=0.3,
            system=system, messages=clean_messages(msgs),
        )
        text = "".join(b.text for b in r.content if getattr(b, "type", "") == "text").strip()
        return text or "No response was generated."
    except HTTPException:
        raise
    except anthropic.APIStatusError as e:
        detail = getattr(e, "message", "") or str(e)
        if "workspace" in detail.lower():
            detail += " — set ANTHROPIC_WORKSPACE_ID, or use a key created inside a workspace."
        raise HTTPException(502, f"Claude request failed ({e.status_code}): {detail}")
    except anthropic.APIConnectionError:
        raise HTTPException(502, "Could not reach Anthropic. Check your internet connection.")
    except Exception:
        raise HTTPException(502, "Claude request failed. Check model access and server logs.")


# ---------- storage ----------
def save(cid, role, content):
    with conn() as c:
        c.execute("INSERT INTO messages(conversation_id,role,content,created_at) VALUES(?,?,?,?)", (cid, role, content, now()))
        first = c.execute("SELECT content FROM messages WHERE conversation_id=? AND role='user' ORDER BY id LIMIT 1", (cid,)).fetchone()
        title = (first["content"][:40] + ("…" if len(first["content"]) > 40 else "")) if first else "New conversation"
        c.execute("UPDATE conversations SET title=?,updated_at=? WHERE id=?", (title, now(), cid))


def history(cid):
    with conn() as c:
        return [dict(x) for x in c.execute("SELECT role,content FROM messages WHERE conversation_id=? ORDER BY id", (cid,)).fetchall()]


# ---------- 01 Basic: fixed rules with a guided menu ----------
# Each node: button label, fixed answer, follow-up options (node ids), keywords for typed questions.
# Answers are demo content for a fictional bank and company, not real policies.
BASIC_TREE = {
    "menu": {"label": "Main menu", "answer": "Choose a topic below. This Basic bot only knows these fixed answers.",
             "options": ["hours", "branches", "cards", "leave", "email"], "keywords": ["menu", "help", "start", "hi", "hello"]},
    # top level
    "hours": {"label": "Banking hours", "answer": "This demo bank is open Monday to Friday, 9 AM to 5 PM. This is an example rule, not a real bank schedule.",
              "options": ["holidays", "cutoff", "menu"], "keywords": ["banking hours", "bank hours", "opening hours", "working hours", "open", "timing"]},
    "branches": {"label": "Branches and ATMs", "answer": "The demo bank has a fixed list of branches and ATMs. Pick what you need below.",
                 "options": ["nearest", "atm_limit", "menu"], "keywords": ["branch", "branches", "location", "locations", "atm"]},
    "cards": {"label": "Cards", "answer": "I can help with common card questions. Pick one below.",
              "options": ["block", "not_working", "menu"], "keywords": ["card", "cards"]},
    "leave": {"label": "Leave policy", "answer": "Planned leave needs manager approval and should be requested 5 working days ahead (demo rule).",
              "options": ["apply", "balance", "menu"], "keywords": ["leave policy", "leave", "vacation", "holiday leave", "time off"]},
    "email": {"label": "Write an email", "answer": "I have fixed email templates. Choose one and fill in the [brackets] yourself.",
              "options": ["leave_email", "status_email", "menu"], "keywords": ["email", "mail", "draft", "write"]},
    # second level
    "holidays": {"label": "Holiday schedule", "answer": "The demo bank is closed on weekends and national public holidays. Online banking stays available.",
                 "options": ["cutoff", "menu"], "keywords": ["holiday schedule", "public holiday", "closed"]},
    "cutoff": {"label": "Same-day payment cut-off", "answer": "Payments submitted before 2 PM on a working day are processed the same day; later ones go the next working day (demo rule).",
               "options": ["hours", "menu"], "keywords": ["cut-off", "cutoff", "same day", "same-day"]},
    "nearest": {"label": "Find nearest branch", "answer": "Use the branch locator on the demo bank's website or app and enter your PIN code. A Basic bot cannot look up your location.",
                "options": ["atm_limit", "menu"], "keywords": ["nearest", "near me", "closest"]},
    "atm_limit": {"label": "ATM withdrawal limit", "answer": "The demo daily ATM withdrawal limit is 25,000 per card. Limits on real cards vary by account.",
                  "options": ["nearest", "menu"], "keywords": ["withdrawal limit", "atm limit", "cash limit"]},
    "block": {"label": "Block my card", "answer": "Call the 24x7 helpline or use App > Cards > Block card. A Basic bot can only tell you how; blocking it for you is an action, which is level 04 AI Automation.",
              "options": ["not_working", "menu"], "keywords": ["block", "lost", "stolen"]},
    "not_working": {"label": "Card not working", "answer": "Check that the card is not expired, blocked or over its limit, and that the PIN is correct. If it still fails, contact support.",
                    "options": ["block", "menu"], "keywords": ["not working", "declined", "failed", "card error"]},
    "apply": {"label": "How do I apply?", "answer": "Apply in the HR portal: Leave > New request, choose dates and the leave type, then submit for manager approval (demo process).",
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


# ---------- 03 RAG: keyword retrieval over knowledge/*.md ----------
def retrieve(q, k=3):
    terms = set(re.findall(r"[a-z0-9]+", q.lower()))
    hits = []
    for f in KD.glob("*.md"):
        for chunk in re.split(r"\n\s*\n", f.read_text(encoding="utf8")):
            chunk = chunk.strip()
            if not chunk:
                continue
            words = set(re.findall(r"[a-z0-9]+", chunk.lower()))
            score = len(terms & words) / max(1, len(terms))
            if score > 0:
                hits.append({"score": round(score, 3), "source": f.name, "text": chunk})
    return sorted(hits, key=lambda x: x["score"], reverse=True)[:k]


# ---------- 04/05 allow-listed demo tools ----------
ALLOWED_TOOLS = {"leave_balance", "leave_policy", "search_knowledge", "create_ticket", "email_draft"}


def tool(name, args):
    if name == "leave_balance":
        return {"available_days": 8, "source": "mock demo data only; not connected to HR"}
    if name == "leave_policy":
        return {"sources": retrieve("leave policy approval balance advance")}
    if name == "search_knowledge":
        return {"results": retrieve(args.get("query", ""))}
    if name == "create_ticket":
        return {"ticket_id": "DEMO-" + uuid.uuid4().hex[:8].upper(), "status": "created in demo only", "summary": str(args.get("summary", ""))[:300]}
    if name == "email_draft":
        return {"status": "draft prepared; not sent", "subject": args.get("subject", "Draft email"), "body": args.get("body", "")[:1500]}
    return {"error": "Tool not allow-listed"}


def parse_json(text):
    """Pull the first {...} object out of a reply, even if wrapped in prose or code fences."""
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0)) if m else json.loads(text)


# ---------- routes ----------
@app.get("/", response_class=HTMLResponse)
def home():
    return (ROOT / "static/index.html").read_text(encoding="utf8")


@app.get("/api/health")
def health():
    return {"status": "ok", "provider": "Anthropic", "model": MODEL, "llm_configured": bool(os.getenv("ANTHROPIC_API_KEY"))}


@app.get("/api/basic/menu")
def basic_menu():
    return {"answer": BASIC_TREE["menu"]["answer"], "options": basic_options("menu")}


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
    msgs = [{"role": m["role"], "content": m["content"]} for m in prior if m["role"] in ("user", "assistant")] + [{"role": "user", "content": b.message}]
    meta = {"mode": b.bot, "sources": [], "tools": []}

    if b.bot == "basic":
        answer, meta["options"] = basic(b.message)
        meta["mode"] = "fixed_rules"

    elif b.bot == "generative":
        answer = llm("You are a helpful Generative AI demonstration chatbot. Answer accurately, be clear about uncertainty, and do not claim access to systems.", msgs)

    elif b.bot == "rag":
        hits = retrieve(b.message)
        meta["sources"] = [{"source": h["source"], "score": h["score"]} for h in hits]
        if not hits:
            answer = "I couldn't find relevant information in the demo knowledge base, so I won't invent a policy answer. Try asking about leave policy, payment support, or escalation."
        else:
            context = "\n\n".join("[Source: " + h["source"] + "]\n" + h["text"] for h in hits)
            answer = llm("Answer only from this retrieved context. If it does not support the answer, say so. Cite source filenames. Context:\n" + context, msgs)

    elif b.bot == "automation":
        q = b.message.lower()
        results = []
        if any(x in q for x in ["leave", "vacation", "time off"]):
            results += [{"tool": "leave_balance", "result": tool("leave_balance", {})},
                        {"tool": "leave_policy", "result": tool("leave_policy", {})}]
        if any(x in q for x in ["payment", "declined", "ticket", "support"]):
            results.append({"tool": "search_knowledge", "result": tool("search_knowledge", {"query": b.message})})
            if "ticket" in q:
                results.append({"tool": "create_ticket", "result": tool("create_ticket", {"summary": b.message})})
        if any(x in q for x in ["email", "draft", "manager"]):
            results.append({"tool": "email_draft", "result": tool("email_draft", {"subject": "Draft based on request", "body": "Please review before sending.\n\nRequest: " + b.message})})
        if not results:
            results = [{"tool": "search_knowledge", "result": tool("search_knowledge", {"query": b.message})}]
        meta["tools"] = results
        answer = llm("Summarize these tool results faithfully. Clearly state mock/demo data and never imply external systems were changed. Tools:\n" + json.dumps(results), msgs)

    else:  # agentic
        plan = llm(
            "You are an agentic AI learning demo. Make a 2-4 step plan and select relevant tools only from: "
            "leave_balance, leave_policy, search_knowledge, create_ticket, email_draft. "
            "Return JSON only, with no other text: "
            "{\"plan\":[...],\"tools\":[{\"name\":\"...\",\"args\":{}}],\"verification\":\"...\"}. "
            "Never propose real external actions.", msgs)
        try:
            obj = parse_json(plan)
        except Exception:
            obj = {"plan": ["Understand goal", "Use relevant demo tools", "Review results"], "tools": [],
                   "verification": "Could not parse a structured plan; no tools run."}
        observed = []
        for item in obj.get("tools", [])[:4]:
            if isinstance(item, dict) and item.get("name") in ALLOWED_TOOLS:
                observed.append({"tool": item["name"], "result": tool(item["name"], item.get("args") or {})})
        meta["plan"] = obj.get("plan", [])
        meta["tools"] = observed
        meta["verification"] = obj.get("verification", "")
        answer = llm("Explain the plan, tool observations and verification honestly. State what remains if unavailable. "
                     "No real-world action is taken. Plan/results:\n"
                     + json.dumps({"plan": meta["plan"], "tools": observed, "verification": meta["verification"]}), msgs)

    save(b.conversation_id, "assistant", answer)
    return {"answer": answer, "metadata": meta}
