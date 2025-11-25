import asyncio
import json

from pocket_ai.core.config import get_config
from pocket_ai.mcp.server import mcp_server


async def _call(tool, args):
    return await mcp_server.handle_request(
        "tools/call",
        {"name": tool, "arguments": args},
    )


def test_mcp_status():
    get_config().mcp.require_auth = False
    response = asyncio.run(_call("assistant_status", {}))
    payload = json.loads(response["content"][0]["text"])
    assert "profile" in payload


def test_mcp_list_tools():
    get_config().mcp.require_auth = False
    tools = asyncio.run(mcp_server.handle_request("tools/list", {}))
    assert isinstance(tools["tools"], list)


