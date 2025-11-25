from typing import Dict, Any
import psutil
import platform
from .plugin_base import PluginBase, ToolContext

class SystemMonitorPlugin(PluginBase):
    name = "system_monitor"
    description = "Get system resource usage (CPU, RAM, Disk)"
    requires_capabilities = ["system_diagnostics"]

    async def execute(self, input_data: Dict[str, Any], context: ToolContext) -> Dict[str, Any]:
        action = input_data.get("action", "all")
        
        result = {
            "system": platform.system(),
            "release": platform.release(),
        }

        if action in ["cpu", "all"]:
            result["cpu_percent"] = psutil.cpu_percent(interval=0.1)
            result["cpu_count"] = psutil.cpu_count()

        if action in ["memory", "all"]:
            mem = psutil.virtual_memory()
            result["memory_total_gb"] = round(mem.total / (1024**3), 2)
            result["memory_available_gb"] = round(mem.available / (1024**3), 2)
            result["memory_percent"] = mem.percent

        if action in ["disk", "all"]:
            disk = psutil.disk_usage('/')
            result["disk_total_gb"] = round(disk.total / (1024**3), 2)
            result["disk_free_gb"] = round(disk.free / (1024**3), 2)
            result["disk_percent"] = disk.percent

        return result
