from pocket_ai.core.policy_engine import policy_engine
from pocket_ai.ai.openai_gateway import openai_gateway
from pocket_ai.vision.privacy_filter import privacy_filter

class OnlineVision:
    async def analyze(self, image_bytes: bytes, prompt: str):
        if not policy_engine.can_use_cloud("vision_query"):
            return "Cloud vision blocked."
            
        safe_image = privacy_filter.process_image(image_bytes)
        return await openai_gateway.vision_query(safe_image, prompt)

vision_online = OnlineVision()
