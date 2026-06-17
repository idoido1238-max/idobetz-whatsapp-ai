"""
Intent detection service.
Maps user messages to business intents.
"""
import json
import logging
from typing import Optional
from app.services.ai.openai_service import OpenAIService

logger = logging.getLogger(__name__)

SUPPORTED_INTENTS = [
    "order_status",
    "order_cancel",
    "product_inquiry",
    "product_recommendation",
    "price_inquiry",
    "stock_inquiry",
    "cart_help",
    "payment_help",
    "shipping_info",
    "return_refund",
    "complaint",
    "compliment",
    "support_request",
    "human_agent_request",
    "greeting",
    "farewell",
    "faq",
    "general",
]


class IntentDetector:
    def __init__(self):
        self.ai = OpenAIService()

    async def detect(self, text: str, conversation_history: Optional[list] = None) -> dict:
        """
        Detect intent from user message.

        Returns:
            {
                'intent': str,
                'confidence': float,
                'sub_intent': optional str,
                'entities': dict,
                'requires_order_lookup': bool,
                'requires_product_lookup': bool,
            }
        """
        system_prompt = f"""You are an intent detection system for a Hebrew/English e-commerce chatbot.
Detect the user's intent from this list: {', '.join(SUPPORTED_INTENTS)}

Return JSON with:
- intent: one of the supported intents
- confidence: 0-1
- sub_intent: optional more specific intent
- entities: dict of extracted entities (order_id, product_name, category, etc.)
- requires_order_lookup: boolean
- requires_product_lookup: boolean
- language: "he" or "en" or "mixed"

Return ONLY valid JSON."""

        context = ""
        if conversation_history:
            last_msgs = conversation_history[-3:]
            context = "\n".join([f"{m.get('role', 'user')}: {m.get('content', '')}" for m in last_msgs])
            text = f"Context:\n{context}\n\nCurrent message: {text}"

        messages = [{"role": "user", "content": text}]
        try:
            result = await self.ai.chat(messages, system_prompt=system_prompt, temperature=0.1)
            data = json.loads(result["content"])
            return {
                "intent": data.get("intent", "general"),
                "confidence": float(data.get("confidence", 0.5)),
                "sub_intent": data.get("sub_intent"),
                "entities": data.get("entities", {}),
                "requires_order_lookup": bool(data.get("requires_order_lookup", False)),
                "requires_product_lookup": bool(data.get("requires_product_lookup", False)),
                "language": data.get("language", "he"),
            }
        except Exception as e:
            logger.error(f"Intent detection error: {e}")
            return {
                "intent": "general",
                "confidence": 0.0,
                "sub_intent": None,
                "entities": {},
                "requires_order_lookup": False,
                "requires_product_lookup": False,
                "language": "he",
            }
