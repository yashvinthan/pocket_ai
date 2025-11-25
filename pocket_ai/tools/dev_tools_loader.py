import importlib
import pkgutil
import os
from pocket_ai.tools.tool_registry import tool_registry
from pocket_ai.tools.dev_plugins.plugin_base import PluginBase
from pocket_ai.core.logger import logger

def load_plugins():
    # For this prototype, we'll manually register the Todoist plugin
    # In a real app, we'd walk the directory and import dynamically
    
    from pocket_ai.tools.dev_plugins.gmail_plugin import GmailPlugin
    from pocket_ai.tools.dev_plugins.google_calendar_plugin import GoogleCalendarPlugin
    from pocket_ai.tools.dev_plugins.notes_plugin import NotesPlugin
    from pocket_ai.tools.dev_plugins.notion_plugin import NotionPlugin
    from pocket_ai.tools.dev_plugins.slack_plugin import SlackBridgePlugin
    from pocket_ai.tools.dev_plugins.swiggy_plugin import SwiggyPlugin
    from pocket_ai.tools.dev_plugins.system_monitor_plugin import SystemMonitorPlugin
    from pocket_ai.tools.dev_plugins.todoist_plugin import TodoistPlugin
    from pocket_ai.tools.dev_plugins.zomato_plugin import ZomatoPlugin

    plugins = [
        TodoistPlugin(),
        NotionPlugin(),
        GoogleCalendarPlugin(),
        GmailPlugin(),
        SwiggyPlugin(),
        ZomatoPlugin(),
        SlackBridgePlugin(),
        SystemMonitorPlugin(),
        NotesPlugin(),
    ]

    for plugin in plugins:
        tool_registry.register_dev_plugin(plugin.name, plugin)
    
    logger.info(f"Loaded {len(plugins)} plugins")

