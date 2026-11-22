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
            text = "Fake Claude reply"
        return types.SimpleNamespace(content=[types.SimpleNamespace(type="text", text=text)])


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
    assert r.json()["answer"] == "Fake Claude reply"
    assert len(calls) == 1


def test_rag_cites_sources_and_refuses_without_match(env):
    _, client, calls = env
    _, r = ask(client, "rag", "What is the leave policy?")
    sources = [s["source"] for s in r.json()["metadata"]["sources"]]
    assert "leave_policy.md" in sources
    assert "leave_policy.md" in calls[-1]["system"]
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
    _, r = ask(client, "automation", "I lost my card, please block it")
    assert [t["tool"] for t in r.json()["metadata"]["tools"]] == ["block_card"]
    _, r = ask(client, "automation", "Check the status of payment PAY-1042")
    tools = r.json()["metadata"]["tools"]
    assert tools[0]["tool"] == "payment_status" and tools[0]["result"]["reference"] == "PAY-1042"


def test_what_this_level_did_is_saved_with_the_answer(env):
    _, client, _ = env
    cid, r = ask(client, "rag", "What is the leave policy?")
    assert r.json()["metadata"]["did"].startswith("Searched")
    msgs = client.get(f"/api/conversations/{cid}").json()["messages"]
    assert msgs[1]["meta"]["sources"][0]["source"] == "leave_policy.md"
