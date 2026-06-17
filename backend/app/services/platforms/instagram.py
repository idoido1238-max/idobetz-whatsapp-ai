"""
Instagram DM platform handler.
"""
import hashlib
import hmac
import logging
from typing import Dict, List, Optional
import httpx

from app.config import settings

logger = logging.getLogger(__name__)

INSTAGRAM_API_BASE = "https://graph.facebook.com/v20.0"


class InstagramHandler:
    def __init__(self):
        self.access_token = settings.INSTAGRAM_ACCESS_TOKEN
        self.app_secret = settings.INSTAGRAM_APP_SECRET

    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        if mode == "subscribe" and token == settings.INSTAGRAM_WEBHOOK_VERIFY_TOKEN:
            return challenge
        return None

    def verify_signature(self, payload: bytes, signature: str) -> bool:
        expected = hmac.new(
            self.app_secret.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(f"sha256={expected}", signature)

    def parse_webhook(self, payload: Dict) -> List[Dict]:
        """Parse Instagram webhook payload."""
        events = []
        try:
            if payload.get("object") != "instagram":
                return events
            for entry in payload.get("entry", []):
                for messaging in entry.get("messaging", []):
                    sender_id = messaging.get("sender", {}).get("id")
                    if "message" in messaging:
                        msg = messaging["message"]
                        events.append({
                            "platform": "instagram",
                            "event_type": "message",
                            "sender_id": sender_id,
                            "message_id": msg.get("mid"),
                            "timestamp": messaging.get("timestamp"),
                            "message_type": "text" if "text" in msg else "attachment",
                            "content": msg.get("text", ""),
                            "attachments": msg.get("attachments", []),
                            "raw": messaging,
                        })
        except Exception as e:
            logger.error(f"Error parsing Instagram webhook: {e}")
        return events

    async def send_text(self, recipient_id: str, text: str) -> Dict:
        return await self._send_message(
            recipient_id,
            {"text": text},
        )

    async def send_image(self, recipient_id: str, image_url: str) -> Dict:
        return await self._send_message(
            recipient_id,
            {"attachment": {"type": "image", "payload": {"url": image_url}}},
        )

    async def _send_message(self, recipient_id: str, message: Dict) -> Dict:
        payload = {
            "recipient": {"id": recipient_id},
            "message": message,
        }
        url = f"{INSTAGRAM_API_BASE}/me/messages"
        params = {"access_token": self.access_token}
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, params=params)
            response.raise_for_status()
            return response.json()
