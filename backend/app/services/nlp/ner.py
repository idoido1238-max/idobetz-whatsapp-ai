"""
Named Entity Recognition (NER) for Hebrew and English.
Extracts business-relevant entities from conversations.
"""
import json
import logging
from typing import Optional
from app.services.ai.openai_service import OpenAIService

logger = logging.getLogger(__name__)


class NERService:
    def __init__(self):
        self.ai = OpenAIService()

    async def extract_entities(self, text: str) -> dict:
        """
        Extract named entities from text (Hebrew/English).

        Returns:
            {
                'order_ids': list of order IDs,
                'product_names': list,
                'categories': list,
                'locations': list (cities, addresses),
                'persons': list,
                'dates': list,
                'phone_numbers': list,
                'emails': list,
                'amounts': list of monetary amounts,
            }
        """
        system_prompt = """Extract named entities from the text (supports Hebrew and English).
Return JSON with these fields:
- order_ids: list of order IDs/numbers found
- product_names: list of product names/descriptions
- categories: list of product categories
- locations: list of cities, streets, addresses
- persons: list of person names
- dates: list of dates/times
- phone_numbers: list of phone numbers
- emails: list of email addresses
- amounts: list of monetary amounts with currency

Return ONLY valid JSON."""

        messages = [{"role": "user", "content": text}]
        try:
            result = await self.ai.chat(messages, system_prompt=system_prompt, temperature=0.1)
            data = json.loads(result["content"])
            return {
                "order_ids": data.get("order_ids", []),
                "product_names": data.get("product_names", []),
                "categories": data.get("categories", []),
                "locations": data.get("locations", []),
                "persons": data.get("persons", []),
                "dates": data.get("dates", []),
                "phone_numbers": data.get("phone_numbers", []),
                "emails": data.get("emails", []),
                "amounts": data.get("amounts", []),
            }
        except Exception as e:
            logger.error(f"NER extraction error: {e}")
            return {
                "order_ids": [],
                "product_names": [],
                "categories": [],
                "locations": [],
                "persons": [],
                "dates": [],
                "phone_numbers": [],
                "emails": [],
                "amounts": [],
            }
