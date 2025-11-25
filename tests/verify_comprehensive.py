import asyncio
import sys
import os
import time
import shutil
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pocket_ai.core.config import get_config, Config
from pocket_ai.core.policy_engine import policy_engine
from pocket_ai.core.storage import storage
from pocket_ai.mcp.server import mcp_server

async def list_tools():
    res = await mcp_server.handle_request("tools/list", {})
    return res["tools"]

async def call_tool(name, args):
    return await mcp_server.handle_request("tools/call", {"name": name, "arguments": args})

async def test_policy_engine():
    print("\n--- Testing Policy Engine ---")
    config = get_config()
    print(f"Current Profile: {config.profile}")
    
    # Test 1: Cloud Access (Should be False for OFFLINE_ONLY)
    can_cloud = policy_engine.can_use_cloud("speech_recognition")
    print(f"Can use cloud speech? {can_cloud}")
    if config.profile == "OFFLINE_ONLY" and can_cloud:
        print("[FAIL] Cloud allowed in OFFLINE_ONLY mode")
    elif config.profile == "OFFLINE_ONLY" and not can_cloud:
        print("[PASS] Cloud correctly blocked")
        
    # Test 2: Capability Check
    can_net = policy_engine.can_use_capability("network", "test_plugin")
    print(f"Can use network? {can_net}")
    if can_net:
        print("[PASS] Capability check functional")

async def test_storage():
    print("\n--- Testing Storage ---")
    
    # Test 1: Store and Retrieve
    test_data = {"foo": "bar", "timestamp": time.time()}
    storage.store("system", "test_key", test_data)
    
    retrieved = storage.retrieve("system", "test_key")
    print(f"Stored: {test_data}")
    print(f"Retrieved: {retrieved}")
    
    if retrieved and retrieved.get("foo") == "bar":
        print("[PASS] Data persistence working")
    else:
        print("[FAIL] Data retrieval failed")

    # Test 2: TTL Purge (Mocking time or using short TTL)
    # We'll just verify the method runs without error for now
    try:
        storage.purge_expired()
        print("[PASS] TTL purge executed")
    except Exception as e:
        print(f"[FAIL] TTL purge error: {e}")

async def test_mcp_server():
    print("\n--- Testing MCP Server ---")
    
    # Test 1: List Tools
    tools = await list_tools()
    print(f"Found {len(tools)} tools")
    tool_names = [t['name'] for t in tools]
    print(f"Tools: {tool_names}")
    
    if "assistant_status" in tool_names and "run_easy_tool" in tool_names:
        print("[PASS] Core MCP tools present")
    else:
        print("[FAIL] Missing core MCP tools")
        
    # Test 2: Call Tool (Assistant Status)
    try:
        result = await call_tool("assistant_status", {})
        print(f"Status Result: {result}")
        if "content" in result:
            print("[PASS] assistant_status tool execution successful")
        else:
            print("[FAIL] assistant_status returned unexpected format")
    except Exception as e:
        print(f"[FAIL] Tool execution error: {e}")

async def main():
    print("=== POCKET-AI COMPREHENSIVE VERIFICATION ===")
    await test_policy_engine()
    await test_storage()
    await test_mcp_server()
    print("\n=== VERIFICATION COMPLETE ===")

if __name__ == "__main__":
    asyncio.run(main())
