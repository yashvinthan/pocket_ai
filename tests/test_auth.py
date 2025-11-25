import asyncio

import pytest
from fastapi.testclient import TestClient

from pocket_ai.ai.orchestrator import orchestrator
from pocket_ai.core.config import get_config
from pocket_ai.core.secrets_manager import secrets_manager
from pocket_ai.mcp.server import mcp_server
from pocket_ai.ui.api import app


@pytest.fixture
def api_client(monkeypatch):
    cfg = get_config()
    cfg.api.require_auth = True
    secrets_manager._secrets["api_auth_token"] = "test-api-token"  # type: ignore[attr-defined]

    async def _fake_process(text: str):
        return {"transcript": text, "response_text": "ok", "intent": {"type": "free"}}

    monkeypatch.setattr(orchestrator, "process_text_command", _fake_process)
    return TestClient(app)


def test_api_rejects_missing_token(api_client):
    resp = api_client.post("/command", json={"text": "ping"})
    assert resp.status_code == 401


def test_api_accepts_valid_token(api_client):
    resp = api_client.post(
        "/command",
        json={"text": "ping"},
        headers={"X-Pocket-Key": "test-api-token"},
    )
    assert resp.status_code == 200
    assert resp.json()["transcript"] == "ping"


def test_mcp_auth_enforced(monkeypatch):
    cfg = get_config()
    monkeypatch.setattr(cfg.mcp, "require_auth", True)
    secrets_manager._secrets["mcp_auth_token"] = "mcp-token"  # type: ignore[attr-defined]

    with pytest.raises(PermissionError):
        asyncio.run(
            mcp_server.handle_request(
                "tools/call",
                {"name": "assistant_status", "arguments": {}},
            )
        )

    result = asyncio.run(
        mcp_server.handle_request(
            "tools/call",
            {"name": "assistant_status", "arguments": {}, "auth_token": "mcp-token"},
        )
    )
    assert "content" in result

