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

    def create(self, **kw):
        self.calls.append(kw)
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
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("ANTHROPIC_WORKSPACE_ID", "wrkspc_test")
    sys.modules.pop("app", None)
    app = importlib.import_module("app")
    calls = []

    def fake_client(**kw):
        assert kw["default_headers"] == {"anthropic-workspace-id": "wrkspc_test"}
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
    assert "Monday" in r.json()["answer"]
    _, r = ask(client, "basic", "Tell me a joke")
    assert "No matching rule" in r.json()["answer"]
    assert calls == []  # Basic never calls Claude


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
    assert tools == ["leave_balance", "leave_policy", "search_knowledge", "create_ticket", "email_draft"]


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
    assert r.status_code == 503
    assert "ANTHROPIC_API_KEY" in r.json()["detail"]
