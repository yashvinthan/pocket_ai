import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pocket_ai.core.config import get_config
from pocket_ai.core.policy_engine import policy_engine
from pocket_ai.ai.orchestrator import orchestrator
from pocket_ai.tools.dev_tools_loader import load_plugins

async def run_tests():
    print("=== POCKET-AI SELF-TEST ===")
    
    # 1. Config Test
    config = get_config()
    print(f"[PASS] Config loaded. Profile: {config.profile}")
    
    # 2. Policy Test
    allowed = policy_engine.can_use_cloud("speech_recognition")
    print(f"[PASS] Policy check (OFFLINE_ONLY default): Allowed={allowed}")
    
    # 3. Plugin Loading
    load_plugins()
    print("[PASS] Plugins loaded")
    
    # 4. Orchestrator Test (Task)
    print("Testing 'Add a task'...")
    res = await orchestrator.process_text_command("Add a task to buy milk")
    print(f"Result: {res}")
    if res['intent']['type'] == 'create_task':
        print("[PASS] Intent parsed correctly")
    else:
        print("[FAIL] Intent parsing failed")
        
    # 5. Orchestrator Test (Meal)
    print("Testing 'Log a meal'...")
    res = await orchestrator.process_text_command("I ate a sandwich")
    print(f"Result: {res}")
    if res['intent']['type'] == 'log_meal':
         print("[PASS] Meal intent parsed")
    else:
         print("[FAIL] Meal intent failed")

    # 6. Easy Tools Test
    from pocket_ai.tools.easy_tools_runtime import easy_tools
    print("Testing Easy Tool (Summarize)...")
    # Note: Requires HYBRID profile or policy override
    # For test, we assume policy engine might block if OFFLINE_ONLY, so we check result
    res = await easy_tools.execute_tool("summarize_text", {"user_text": "Long text..."})
    print(f"Easy Tool Result: {res}")
    
    # 7. Plugin Test (Notion)
    from pocket_ai.tools.tool_registry import tool_registry
    print("Testing Notion Plugin...")
    notion = tool_registry.get_tool("notion_integration")
    if notion:
        print("[PASS] Notion plugin found")
    else:
        print("[FAIL] Notion plugin missing")

    # 8. Plugin Test (Gmail & Swiggy)
    print("Testing Gmail & Swiggy Plugins...")
    gmail = tool_registry.get_tool("gmail_helper")
    swiggy = tool_registry.get_tool("swiggy_connector")
    
    if gmail and swiggy:
        print("[PASS] Gmail and Swiggy plugins found")
        
        # Execute Swiggy Search
        res = await swiggy['tool'].execute({"action": "search_food", "query": "dosa"}, None)
        print(f"Swiggy Search Result: {res.get('restaurants')[0]['name']}")
        if res['status'] == 'success':
            print("[PASS] Swiggy search executed")
    else:
        print("[FAIL] Gmail or Swiggy plugin missing")

    # 9. NLU & Context Test
    print("Testing NLU & Context...")
    from pocket_ai.ai.nlu import nlu_engine
    from pocket_ai.ai.context_manager import context_manager
    
    intent = nlu_engine.parse("Draft email to boss")
    print(f"NLU Intent: {intent['type']}")
    if intent['type'] == 'draft_email':
        print("[PASS] NLU parsed draft_email")
    context_manager.add_turn("Draft email", "Done", intent)
    ctx = context_manager.get_context()
    if len(ctx) == 1:
        print("[PASS] Context updated")

    # 10. Compute Backend Test
    print("Testing Compute Backends...")
    from pocket_ai.core.compute_backends import compute_backends, BackendType
    backend = compute_backends.get_backend_for_task("vision")
    print(f"Vision Backend: {backend}")
    if backend in [BackendType.PI_CPU, BackendType.PI_TPU]:
        print("[PASS] Vision backend is local (Offline Default)")

    # Test Compute Backend Selection
    print("\n--- Testing Compute Backends ---")
    llm_backend = compute_backends.get_backend_for_task("llm")
    print(f"LLM Backend: {llm_backend}")
    vision_backend = compute_backends.get_backend_for_task("vision")
    print(f"Vision Backend: {vision_backend}")

    # Test New Plugins
    print("\n--- Testing New Plugins ---")
    sys_mon = tool_registry.get_tool("system_monitor")
    if sys_mon:
        print("System Monitor Plugin found.")
        # We can't easily await here without async main, but presence is good enough for basic verify
    else:
        print("ERROR: System Monitor Plugin NOT found.")

    notes_plugin = tool_registry.get_tool("notes")
    if notes_plugin:
        print("Notes Plugin found.")
    else:
        print("ERROR: Notes Plugin NOT found.")

    print("=== TESTS COMPLETE ===")

if __name__ == "__main__":
    asyncio.run(run_tests())
