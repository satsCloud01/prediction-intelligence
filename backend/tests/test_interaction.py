"""Interaction session and chat tests."""

import pytest
from tests.conftest import (
    start_session, create_project, add_seed, build_graph, generate_agents,
)

pytestmark = pytest.mark.asyncio


class TestListSessions:
    async def test_list_sessions_empty(self, client):
        p = await create_project(client, {"name": "Empty Sessions"})
        r = await client.get(f"/api/interaction/{p['id']}/sessions")
        assert r.status_code == 200
        assert isinstance(r.json(), list)


class TestStartSession:
    async def test_start_agent_session(self, client):
        p = await create_project(client, {"name": "Agent Session Test"})
        await add_seed(client, p["id"])
        await build_graph(client, p["id"])
        await generate_agents(client, p["id"])
        agents = (await client.get(f"/api/agents/{p['id']}")).json()
        aid = agents[0]["id"]
        s = await start_session(client, p["id"], agent_persona_id=aid, session_type="agent")
        assert s["session_type"] == "agent"
        assert "session_id" in s

    async def test_start_analyst_session(self, client):
        p = await create_project(client, {"name": "Analyst Session"})
        s = await start_session(client, p["id"], session_type="analyst")
        assert s["session_type"] == "analyst"

    async def test_start_session_project_not_found(self, client):
        r = await client.post("/api/interaction/sessions", json={
            "project_id": 99999, "session_type": "analyst",
        })
        assert r.status_code == 404

    async def test_session_appears_in_list(self, client):
        p = await create_project(client, {"name": "Session List Check"})
        s = await start_session(client, p["id"], session_type="analyst")
        sessions = (await client.get(f"/api/interaction/{p['id']}/sessions")).json()
        sids = [sess["id"] for sess in sessions]
        assert s["session_id"] in sids

    async def test_session_list_has_required_fields(self, client):
        p = await create_project(client, {"name": "Session Fields"})
        await start_session(client, p["id"], session_type="analyst")
        sessions = (await client.get(f"/api/interaction/{p['id']}/sessions")).json()
        required = {"id", "session_type", "agent_name", "message_count", "created_at"}
        for sess in sessions:
            assert required.issubset(sess.keys())


class TestChat:
    async def test_chat_returns_response(self, client):
        p = await create_project(client, {"name": "Chat Response"})
        s = await start_session(client, p["id"], session_type="analyst")
        r = await client.post("/api/interaction/chat", json={
            "session_id": s["session_id"], "message": "What is your analysis?",
        })
        assert r.status_code == 200
        assert "response" in r.json()
        assert len(r.json()["response"]) > 0

    async def test_chat_mock_provider(self, client):
        p = await create_project(client, {"name": "Chat Mock"})
        s = await start_session(client, p["id"], session_type="analyst")
        r = await client.post("/api/interaction/chat", json={
            "session_id": s["session_id"], "message": "Hello",
        })
        assert r.json()["llm_provider"] == "mock"

    async def test_chat_session_not_found(self, client):
        r = await client.post("/api/interaction/chat", json={
            "session_id": 99999, "message": "Hello",
        })
        assert r.status_code == 404

    async def test_chat_messages_persist(self, client):
        p = await create_project(client, {"name": "Chat Persist"})
        s = await start_session(client, p["id"], session_type="analyst")
        sid = s["session_id"]
        await client.post("/api/interaction/chat", json={
            "session_id": sid, "message": "First message",
        })
        msgs = (await client.get(f"/api/interaction/sessions/{sid}/messages")).json()
        assert len(msgs) >= 2  # user + assistant

    async def test_chat_preserves_history(self, client):
        p = await create_project(client, {"name": "Chat History"})
        s = await start_session(client, p["id"], session_type="analyst")
        sid = s["session_id"]
        await client.post("/api/interaction/chat", json={
            "session_id": sid, "message": "Message one",
        })
        await client.post("/api/interaction/chat", json={
            "session_id": sid, "message": "Message two",
        })
        msgs = (await client.get(f"/api/interaction/sessions/{sid}/messages")).json()
        assert len(msgs) >= 4  # 2 user + 2 assistant

    async def test_chat_user_role_correct(self, client):
        p = await create_project(client, {"name": "Chat Roles"})
        s = await start_session(client, p["id"], session_type="analyst")
        sid = s["session_id"]
        await client.post("/api/interaction/chat", json={
            "session_id": sid, "message": "Test role",
        })
        msgs = (await client.get(f"/api/interaction/sessions/{sid}/messages")).json()
        roles = [m["role"] for m in msgs]
        assert "user" in roles
        assert "assistant" in roles

    async def test_chat_message_content_matches(self, client):
        p = await create_project(client, {"name": "Chat Content"})
        s = await start_session(client, p["id"], session_type="analyst")
        sid = s["session_id"]
        await client.post("/api/interaction/chat", json={
            "session_id": sid, "message": "Unique test content XYZ123",
        })
        msgs = (await client.get(f"/api/interaction/sessions/{sid}/messages")).json()
        user_msgs = [m for m in msgs if m["role"] == "user"]
        assert any("Unique test content XYZ123" in m["content"] for m in user_msgs)

    async def test_session_message_count_updates(self, client):
        p = await create_project(client, {"name": "Chat Count"})
        s = await start_session(client, p["id"], session_type="analyst")
        sid = s["session_id"]
        await client.post("/api/interaction/chat", json={
            "session_id": sid, "message": "Count test",
        })
        sessions = (await client.get(f"/api/interaction/{p['id']}/sessions")).json()
        sess = next((x for x in sessions if x["id"] == sid), None)
        assert sess is not None
        assert sess["message_count"] >= 2
