from typing import Dict, Any
from .plugin_base import PluginBase, ToolContext
from pocket_ai.core.logger import logger

class SwiggyPlugin(PluginBase):
    name = "swiggy_connector"
    description = "Search for food and prepare orders on Swiggy"
    requires_capabilities = ["network", "location"]

    async def execute(self, input_data: Dict[str, Any], context: ToolContext) -> Dict[str, Any]:
        action = input_data.get("action")
        
        if action == "search_food":
            query = input_data.get("query")
            max_price = input_data.get("max_price", 500)
            logger.info(f"Swiggy: Searching for '{query}' under ₹{max_price}")
            
            # Mock Results
            return {
                "status": "success",
                "restaurants": [
                    {"name": "A2B", "item": "Idli Sambar", "price": 120, "rating": 4.5},
                    {"name": "Saravana Bhavan", "item": "Mini Tiffin", "price": 180, "rating": 4.3}
                ]
            }
            
        elif action == "prepare_cart":
            items = input_data.get("items", [])
            logger.info(f"Swiggy: Preparing cart with {len(items)} items")
            return {
                "status": "success",
                "cart_id": "cart_999",
                "deeplink": "swiggy://cart/999",
                "message": "Cart ready. Open Swiggy to pay."
            }
            
        return {"status": "error", "message": "Unknown action"}
