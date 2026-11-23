"""Offline tests for all five chatbot modes.

Claude is replaced by a fake client, so the suite runs without an API key or
internet access and never spends API credit.
"""
import importlib
import json
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class FakeMessages:
    """Stands in for client.messages and records every call."""

    def __init__(self, calls):
        self.calls = calls

    def count_tokens(self, **kw):
        return types.SimpleNamespace(input_tokens=1)

    def create(self, **kw):
        self.calls.append(kw)
        assert "temperature" not in kw  # deprecated on current Claude models
        roles = [m["role"] for m in kw["messages"]]
        # Claude requires alternating turns that start with the user
        assert roles[0] == "user"
        assert all(a != b for a, b in zip(roles, roles[1:])), roles
        if "Return JSON only" in kw["system"]:
            plan = {
                "plan": ["Check balance", "Check policy"],
                "tools": [{"name": "leave_balance", "args": {}}, {"name": "delete_everything", "args": {}}],
                "verification": "Balance covers the requested days",
            }
            text = "Here is the plan:\n```json\n" + json.dumps(plan) + "\n```"
        else:
            text = "Fake Claude reply" + ("\n\nFOLLOW-UPS: Next one? | Next two? | Next three?" if "FOLLOW-UPS" in kw["system"] else "")
        return types.SimpleNamespace(content=[types.SimpleNamespace(type="text", text=text)],
                                     usage=types.SimpleNamespace(input_tokens=100, output_tokens=20))


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("CHATBOT_DB", str(tmp_path / "test.db"))
    monkeypatch.setenv("CHATBOT_ENV", str(tmp_path / ".env"))
    monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("ANTHROPIC_WORKSPACE_ID", "wrkspc_test")
    sys.modules.pop("app", None)
    app = importlib.import_module("app")
    calls = []

    def fake_client(**kw):
        assert kw["default_headers"]["anthropic-workspace-id"].startswith("wrkspc_")  # sent when set
        return types.SimpleNamespace(messages=FakeMessages(calls))

    monkeypatch.setattr(app.anthropic, "Anthropic", fake_client)
    from fastapi.testclient import TestClient

    return app, TestClient(app.app), calls


def ask(client, bot, message, cid=None):
    if cid is None:
        cid = client.post("/api/conversations", json={"bot": bot}).json()["id"]
    r = client.post("/api/chat", json={"conversation_id": cid, "bot": bot, "message": message})
    return cid, r


def test_health_and_page(env):
    _, client, _ = env
    h = client.get("/api/health").json()
    assert h["provider"] == "Anthropic" and h["llm_configured"] is True
    assert "Learning with Naveen" in client.get("/").text


def test_basic_uses_rules_only(env):
    _, client, calls = env
    _, r = ask(client, "basic", "What are the banking hours?")
    assert r.status_code == 200
    assert "Monday" in r.json()["answer"] and "Bluewater" in r.json()["answer"]
    assert r.json()["metadata"]["options"] == ["Holiday schedule", "Same-day payment cut-off", "Main menu"]
    _, r = ask(client, "basic", "Tell me a joke")
    assert "No matching rule" in r.json()["answer"]
    assert "Banking hours" in r.json()["metadata"]["options"]  # falls back to the main menu
    assert calls == []  # Basic never calls Claude


def test_basic_menu_follow_ups(env):
    _, client, calls = env
    menu = client.get("/api/basic/menu").json()
    assert menu["options"] == ["Banking hours", "Branches and ATMs", "Cards", "Leave policy", "Write an email"]
    cid, r = ask(client, "basic", "Cards")  # a button click sends its label
    assert "Block my card" in r.json()["metadata"]["options"]
    _, r = ask(client, "basic", "Block my card", cid)
    assert "level 04" in r.json()["answer"]
    _, r = ask(client, "basic", "Start a new mail")  # typed text matched by keyword
    assert "Leave request email" in r.json()["metadata"]["options"]
    assert calls == []


def test_generative_calls_claude(env):
    _, client, calls = env
    _, r = ask(client, "generative", "Draft an email")
    assert r.json()["answer"] == "Fake Claude reply"  # FOLLOW-UPS line removed from the answer
    assert r.json()["metadata"]["options"] == ["Next one?", "Next two?", "Next three?", "Main menu"]
    assert len(calls) == 1


def test_rag_cites_sources_and_refuses_without_match(env):
    _, client, calls = env
    _, r = ask(client, "rag", "What is the leave policy?")
    src = r.json()["metadata"]["sources"]
    assert src[0]["n"] == 1 and src[0]["source"] == "leave_policy.md"
    assert src[0]["title"] == "Bluewater Bank: leave policy for employees"  # readable title, not a file name
    assert "[1] Bluewater Bank: leave policy for employees" in calls[-1]["system"]
    assert "leave_policy.md" not in calls[-1]["system"]  # Claude cites numbers, never file names
    assert len({s["source"] for s in src}) == len(src)  # one number per document
    assert not any(p.startswith("#") for s in src for p in s["passages"])  # titles are not passages
    n = len(calls)
    _, r = ask(client, "rag", "zzqx")
    assert "couldn't find" in r.json()["answer"]
    assert len(calls) == n  # no Claude call when nothing is retrieved


def test_automation_runs_allow_listed_tools(env):
    _, client, _ = env
    _, r = ask(client, "automation", "I need leave, raise a ticket and draft an email to my manager")
    tools = [t["tool"] for t in r.json()["metadata"]["tools"]]
    assert tools == ["leave_balance", "leave_policy", "create_ticket", "email_draft"]


def test_agentic_ignores_tools_not_on_allow_list(env):
    _, client, _ = env
    _, r = ask(client, "agentic", "Plan my leave for 3 days")
    meta = r.json()["metadata"]
    assert meta["plan"] == ["Check balance", "Check policy"]
    assert [t["tool"] for t in meta["tools"]] == ["leave_balance"]


def test_history_is_saved_and_reopened(env):
    _, client, _ = env
    cid, _ = ask(client, "generative", "first question")
    ask(client, "generative", "follow up", cid)
    conv = client.get(f"/api/conversations/{cid}").json()
    assert [m["role"] for m in conv["messages"]] == ["user", "assistant", "user", "assistant"]
    assert conv["conversation"]["title"].startswith("first question")


def test_failed_turn_is_merged_on_retry(env, monkeypatch):
    app, client, calls = env

    class Boom:
        def create(self, **kw):
            import httpx
            raise app.anthropic.APIConnectionError(request=httpx.Request("POST", "https://api.anthropic.com"))

    good = app.anthropic.Anthropic
    monkeypatch.setattr(app.anthropic, "Anthropic", lambda **kw: types.SimpleNamespace(messages=Boom()))
    cid, r = ask(client, "generative", "first")
    assert r.status_code == 502
    monkeypatch.setattr(app.anthropic, "Anthropic", good)
    _, r = ask(client, "generative", "second", cid)
    assert r.status_code == 200
    assert calls[-1]["messages"] == [{"role": "user", "content": "first\n\nsecond"}]


def test_missing_key_gives_clear_error(env, monkeypatch):
    _, client, _ = env
    monkeypatch.delenv("ANTHROPIC_API_KEY")
    _, r = ask(client, "generative", "hello")
    assert r.status_code == 400
    assert "No API key is set" in r.json()["detail"]


def _status_error(app, code, message):
    import httpx
    req = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    resp = httpx.Response(code, request=req)
    cls = {401: app.anthropic.AuthenticationError, 400: app.anthropic.BadRequestError}.get(code, app.anthropic.APIStatusError)
    return cls(message, response=resp, body=None)


def test_invalid_key_gives_plain_fix_and_marks_connection_failed(env, monkeypatch):
    app, client, _ = env

    class Bad:
        def create(self, **kw):
            raise _status_error(app, 401, "invalid x-api-key")

        def count_tokens(self, **kw):
            raise _status_error(app, 401, "invalid x-api-key")

    monkeypatch.setattr(app.anthropic, "Anthropic", lambda **kw: types.SimpleNamespace(messages=Bad()))
    _, r = ask(client, "generative", "hello")
    assert r.status_code == 401
    assert "rejected the API key" in r.json()["detail"] and "Settings" in r.json()["detail"]
    assert client.get("/api/health").json()["connection"]["status"] == "failed"
    t = client.post("/api/settings/test").json()
    assert t["status"] == "failed" and "rejected the API key" in t["message"]


def test_workspace_and_credit_errors_are_explained(env):
    app, _, _ = env
    assert "workspace ID" in app.friendly(_status_error(app, 400, "This API key is not scoped to a workspace")).message
    assert "credit" in app.friendly(_status_error(app, 400, "Your credit balance is too low")).message


def test_settings_save_test_and_never_return_the_key(env):
    app, client, _ = env
    r = client.post("/api/settings", json={"api_key": "not-a-key", "workspace_id": "", "model": ""})
    assert r.status_code == 400
    r = client.post("/api/settings", json={"api_key": "sk-ant-usr-" + "x" * 40 + "ABCD", "workspace_id": "wrkspc_123", "model": "claude-haiku-5-5"})
    body = r.json()
    assert body["key_set"] and body["key_hint"].endswith("ABCD") and "x" * 40 not in json.dumps(body)
    assert body["workspace_id"] == "wrkspc_123" and body["model"] == "claude-haiku-5-5"
    env_text = open(app.ENV_FILE).read()
    assert "ANTHROPIC_WORKSPACE_ID=wrkspc_123" in env_text
    t = client.post("/api/settings/test").json()
    assert t["status"] == "ok"
    assert client.get("/api/health").json()["connection"]["status"] == "ok"


def test_rag_refuses_off_topic_without_calling_claude(env):
    _, client, calls = env
    _, r = ask(client, "rag", "What is the capital of France?")
    assert "won't guess" in r.json()["answer"]
    assert calls == []


def test_shared_company_tools(env):
    _, client, _ = env
    cid, r = ask(client, "automation", "I lost my card, please block it")
    meta = r.json()["metadata"]
    assert meta["awaiting"] == "block_card" and meta["tools"] == []  # not run before approval
    assert meta["options"] == ["Yes, block the card", "No, keep it active"]
    _, r = ask(client, "automation", "Yes, block the card", cid)
    meta = r.json()["metadata"]
    assert [t["tool"] for t in meta["tools"]] == ["block_card"] and meta["approved"] == ["block_card"]
    assert meta["options"] == ["Order a replacement card", "Raise a support ticket about my card", "Main menu"]  # same topic only
    _, r = ask(client, "automation", "Check the status of payment PAY-1042")
    tools = r.json()["metadata"]["tools"]
    assert tools[0]["tool"] == "payment_status" and tools[0]["result"]["reference"] == "PAY-1042"


def test_what_this_level_did_is_saved_with_the_answer(env):
    _, client, _ = env
    cid, r = ask(client, "rag", "What is the leave policy?")
    assert r.json()["metadata"]["did"].startswith("Searched")
    msgs = client.get(f"/api/conversations/{cid}").json()["messages"]
    assert msgs[1]["meta"]["sources"][0]["source"] == "leave_policy.md"


def test_same_topic_menu_in_every_bot(env):
    _, client, _ = env
    basic = client.get("/api/menu?bot=basic").json()
    labels = [t["label"] for t in basic["topics"]]
    assert labels == ["Banking hours", "Branches and ATMs", "Cards", "Leave policy", "Write an email"]
    for bot in ["generative", "rag", "automation", "agentic"]:
        m = client.get("/api/menu?bot=" + bot).json()
        assert [t["label"] for t in m["topics"]] == labels  # same topics everywhere
    qs = [t["questions"] for t in client.get("/api/menu?bot=rag").json()["topics"]]
    assert qs == [t["questions"] for t in client.get("/api/menu?bot=agentic").json()["topics"]]  # same questions
    assert all(2 <= len(q) <= 3 for q in qs)  # a topic opens a short list; nothing is sent until the user picks


def test_follow_ups_saved_and_rag_refusal_offers_menu(env):
    _, client, _ = env
    cid, r = ask(client, "rag", "What is the leave policy?")
    assert r.json()["metadata"]["options"][-1] == "Main menu"
    assert client.get(f"/api/conversations/{cid}").json()["messages"][1]["meta"]["options"][0] == "Next one?"
    _, r = ask(client, "rag", "What is the capital of France?")
    assert r.json()["metadata"]["options"] == ["Main menu"]


def test_split_follow_ups_formats(env):
    app, _, _ = env
    assert app.split_follow_ups("A\n\n**FOLLOW-UPS:** x? | y? | z? | w?") == ("A", ["x?", "y?", "z?"])
    assert app.split_follow_ups("No list") == ("No list", [])
    assert app.split_follow_ups("Use *care*\n\nFOLLOW-UPS: a? | b? | c?")[0] == "Use *care*"  # keeps closing asterisk


def test_declining_an_action_runs_nothing(env):
    _, client, calls = env
    cid, _ = ask(client, "automation", "My card was stolen, block it")
    n = len(calls)
    _, r = ask(client, "automation", "No, keep it active", cid)
    meta = r.json()["metadata"]
    assert meta["declined"] == ["block_card"] and meta["tools"] == [] and len(calls) == n  # no tool, no Claude call
    assert meta["options"] == ["Raise a support ticket about my card", "Main menu"]  # no replacement for an active card


def test_automation_follow_ups_stay_on_topic(env):
    app, client, _ = env
    _, r = ask(client, "automation", "What is my leave balance?")
    opts = r.json()["metadata"]["options"]
    assert opts == ["Draft an email to my manager about my leave", "Main menu"]  # on topic, never cards or payments
    _, r = ask(client, "automation", "Order a replacement card")
    meta = r.json()["metadata"]
    assert [t["tool"] for t in meta["tools"]] == ["order_replacement_card"]  # no approval needed, nothing irreversible
    assert meta["options"] == ["Raise a support ticket about my card", "Main menu"]
    _, r = ask(client, "automation", "Raise a support ticket about my card")
    meta = r.json()["metadata"]
    assert "create_ticket" in [t["tool"] for t in meta["tools"]] and meta["options"] == ["Main menu"]


class ScriptedAgent:
    """Fake Claude for the agent loop: a fixed plan, a fixed decision, then the normal fake reply."""

    def __init__(self, calls, plan, decision):
        self.inner, self.plan, self.decision = FakeMessages(calls), plan, decision

    def create(self, **kw):
        if "Return JSON only" in kw["system"]:
            self.inner.calls.append(kw)
            return types.SimpleNamespace(content=[types.SimpleNamespace(type="text", text=json.dumps(self.plan))])
        if "Return the decision as JSON only" in kw["system"]:
            self.inner.calls.append(kw)
            return types.SimpleNamespace(content=[types.SimpleNamespace(type="text", text=json.dumps(self.decision))])
        return self.inner.create(**kw)

    def count_tokens(self, **kw):
        return types.SimpleNamespace(input_tokens=1)


def test_agent_never_blocks_a_card_without_approval(env, monkeypatch):
    app, client, calls = env
    agent = ScriptedAgent(calls, {"goal": "Deal with a lost card", "plan": ["Look up the card policy", "Act"],
                                  "lookups": [{"name": "search_knowledge", "args": {"query": "lost card"}}]},
                          {"actions": [{"name": "block_card", "reason": "card reported lost"},
                                       {"name": "create_ticket", "args": {"summary": "lost card"}, "reason": "record the loss"}],
                           "goal_met": "partly", "check": "Card block waits for approval"})
    monkeypatch.setattr(app.anthropic, "Anthropic", lambda **kw: types.SimpleNamespace(messages=agent))
    cid, r = ask(client, "agentic", "I lost my card, sort it out")
    meta = r.json()["metadata"]
    assert meta["awaiting"] == "block_card"
    assert [(t["step"], t["tool"]) for t in meta["tools"]] == [("look", "search_knowledge"), ("act", "create_ticket")]
    assert meta["options"][0] == "Yes, block the card"  # the safe step ran, the irreversible one waits
    _, r = ask(client, "agentic", "yes", cid)
    assert r.json()["metadata"]["approved"] == ["block_card"]


def test_agent_looks_before_it_acts(env, monkeypatch):
    app, client, calls = env
    # The plan tries to raise a ticket up front; the look step must not run it.
    agent = ScriptedAgent(calls, {"goal": "Banking hours", "plan": ["Search", "Raise a ticket if unclear"],
                                  "lookups": [{"name": "search_knowledge", "args": {"query": "banking hours"}},
                                              {"name": "create_ticket", "args": {"summary": "confirm hours"}}]},
                          {"actions": [], "goal_met": "yes", "check": "The documents give the hours"})
    monkeypatch.setattr(app.anthropic, "Anthropic", lambda **kw: types.SimpleNamespace(messages=agent))
    _, r = ask(client, "agentic", "What are Bluewater Bank's banking hours?")
    meta = r.json()["metadata"]
    assert [t["tool"] for t in meta["tools"]] == ["search_knowledge"]  # answered, so no ticket was raised
    assert meta["skipped"] == ["create_ticket"] and meta["decision"].startswith("No action needed")
    assert len(calls) == 3  # plan, decide, answer
    assert "Do not mention tools, file names, scores" in calls[-1]["system"]


def test_weak_matches_are_dropped(env):
    app, _, _ = env
    hits = app.retrieve("Can I share my card PIN or OTP with bank staff?")
    assert [h["source"] for h in hits] == ["cards.md"]  # 'PIN code' (postal code) and 'the PIN is correct' are not relevant
    assert [h["source"] for h in app.retrieve("I lost my card. What should I do?")] == ["cards.md"]


def test_automation_falls_back_to_cited_document_search(env):
    _, client, calls = env
    _, r = ask(client, "automation", "Can I share my card PIN or OTP with bank staff?")
    meta = r.json()["metadata"]
    assert meta["fallback"] and "No fixed rule matched" in meta["did"]
    assert [s["n"] for s in meta["sources"]] == [1] and meta["sources"][0]["source"] == "cards.md"  # numbered, like level 03
    n = len(calls)
    _, r = ask(client, "automation", "What is the capital of France?")
    meta = r.json()["metadata"]
    assert meta["sources"] == [] and "won't guess" in r.json()["answer"] and len(calls) == n  # nothing found: no Claude call


def test_agent_shows_plan_act_verify_and_why(env, monkeypatch):
    app, client, calls = env
    agent = ScriptedAgent(calls, {"goal": "Payment PAY-1042 sorted today", "plan": ["Check the payment", "Decide", "Answer"],
                                  "lookups": [{"name": "payment_status", "args": {"reference": "PAY-1042"}}]},
                          {"actions": [{"name": "create_ticket", "args": {"summary": "PAY-1042 held"}, "reason": "user needs it today"}],
                           "why_agent": "The payment was held, so the agent had to judge whether to escalate."})
    real = agent.inner.create
    agent.inner.create = lambda **kw: types.SimpleNamespace(content=[types.SimpleNamespace(type="text", text=(
        "Your payment is held for a routine check. I raised ticket DEMO-1.\n\nVERIFY: partly | Escalated, but release depends on the check."
        "\n\nFOLLOW-UPS: Check again? | Draft an email? | Main menu?"))], usage=types.SimpleNamespace(input_tokens=300, output_tokens=60)) \
        if "short, clear reply" in kw["system"] else real(**kw)
    monkeypatch.setattr(app.anthropic, "Anthropic", lambda **kw: types.SimpleNamespace(messages=agent))
    _, r = ask(client, "agentic", "My payment PAY-1042 hasn't arrived and I need it sorted today.")
    body = r.json()
    meta = body["metadata"]
    assert [w["step"] for w in meta["workflow"]] == ["Plan", "Act", "Verify"]
    assert meta["workflow"][1]["detail"] == "Checked payment status, then decided: raised a support ticket"
    assert meta["verify"]["result"] == "partly" and meta["workflow"][2]["detail"].startswith("Goal partly")
    assert "VERIFY" not in body["answer"] and "FOLLOW-UPS" not in body["answer"]  # both lines moved out of the reply
    assert meta["why_agent"].startswith("The payment was held")
    assert meta["usage"]["calls"] == 3 and meta["usage"]["input"] == 300  # plan and decide scripted without usage


def test_token_usage_and_history_cap(env, monkeypatch):
    app, client, calls = env
    _, r = ask(client, "generative", "hello")
    assert r.json()["metadata"]["usage"] == {"calls": 1, "input": 100, "output": 20,
                                             "steps": [{"step": "answer", "input": 100, "output": 20}]}
    _, r = ask(client, "basic", "Banking hours")
    assert r.json()["metadata"]["usage"]["calls"] == 0  # rules only: no tokens
    monkeypatch.setattr(app, "HISTORY_MESSAGES", 2)
    cid, _ = ask(client, "generative", "one")
    for q in ["two", "three", "four"]:
        ask(client, "generative", q, cid)
    assert len(calls[-1]["messages"]) == 3  # last 2 saved messages + the new question


def test_agent_goals_on_welcome(env):
    _, client, _ = env
    assert len(client.get("/api/menu?bot=agentic").json()["goals"]) == 3
    assert "goals" not in client.get("/api/menu?bot=rag").json()
