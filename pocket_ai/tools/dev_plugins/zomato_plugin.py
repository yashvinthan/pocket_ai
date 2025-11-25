from __future__ import annotations

from typing import Any, Dict

from pocket_ai.core.logger import logger

from .plugin_base import PluginBase, ToolContext


class ZomatoPlugin(PluginBase):
    name = "zomato_connector"
    description = "Query Zomato for recommendations"
    requires_capabilities = ["network", "location"]

    async def execute(self, input_data: Dict[str, Any], context: ToolContext) -> Dict[str, Any]:
        action = input_data.get("action")

        if action == "search_food":
            cuisine = input_data.get("query", "veg")
            budget = input_data.get("max_price", 400)
            logger.info(f"Zomato: searching cuisine={cuisine} budget={budget}")
            return {
                "status": "success",
                "restaurants": [
                    {"name": "Green Theory", "item": "Veg Thali", "price": 320},
                    {"name": "Fatty Bao", "item": "Bao Combo", "price": 390},
                ],
            }

        if action == "prepare_cart":
            items = input_data.get("items", [])
            logger.info(f"Zomato: preparing cart with {len(items)} items")
            return {
                "status": "success",
                "cart_id": "zomato_cart_123",
                "deeplink": "zomato://cart/123",
            }

        return {"status": "error", "message": "Unknown action"}


