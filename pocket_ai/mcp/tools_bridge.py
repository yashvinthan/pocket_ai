from pocket_ai.tools.tool_registry import tool_registry
from pocket_ai.tools.easy_tools_runtime import easy_tools

class MCPToolsBridge:
    async def run_tool(self, tool_name: str, payload: dict):
        # Check Easy Tools
        if tool_name in easy_tools.loaded_tools:
            return await easy_tools.execute_tool(tool_name, payload)
            
        # Check Dev Tools
        tool = tool_registry.get_tool(tool_name)
        if tool and tool['type'] == 'dev':
            return await tool_registry.execute_dev_plugin(tool_name, payload)
            
        return {"error": "Tool not found"}

mcp_bridge = MCPToolsBridge()
