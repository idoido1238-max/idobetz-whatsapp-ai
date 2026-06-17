"""
Meta Messenger platform handler.
"""
import hashlib
import hmac
import logging
from typing import Any, Dict, List, Optional
import httpx

from app.config import settings

logger = logging.getLogger(__name__)

MESSENGER_API_BASE = "https://graph.facebook.com/v20.0"


class MessengerHandler:
    def __init__(self):
        self.page_access_token = settings.MESSENGER_PAGE_ACCESS_TOKEN
        self.app_secret = settings.MESSENGER_APP_SECRET

    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        if mode == "subscribe" and token == settings.MESSENGER_WEBHOOK_VERIFY_TOKEN:
            return challenge
        return None

    def verify_signature(self, payload: bytes, signature: str) -> bool:
        expected = hmac.new(
            self.app_secret.encode(),
            payload,
            hashlib.sha1,
        ).hexdigest()
        return hmac.compare_digest(f"sha1={expected}", signature)

    def parse_webhook(self, payload: Dict) -> List[Dict]:
        """Parse Messenger webhook payload."""
        events = []
        try:
            if payload.get("object") != "page":
                return events
            for entry in payload.get("entry", []):
                for messaging in entry.get("messaging", []):
                    sender_id = messaging.get("sender", {}).get("id")
                    if "message" in messaging:
                        msg = messaging["message"]
                        events.append({
                            "platform": "messenger",
                            "event_type": "message",
                            "sender_id": sender_id,
                            "message_id": msg.get("mid"),
                            "timestamp": messaging.get("timestamp"),
                            "message_type": "text" if "text" in msg else "attachment",
                            "content": msg.get("text", ""),
                            "attachments": msg.get("attachments", []),
                            "raw": messaging,
                        })
                    elif "postback" in messaging:
                        postback = messaging["postback"]
                        events.append({
                            "platform": "messenger",
                            "event_type": "postback",
                            "sender_id": sender_id,
                            "payload": postback.get("payload"),
                            "title": postback.get("title"),
                            "timestamp": messaging.get("timestamp"),
                        })
        except Exception as e:
            logger.error(f"Error parsing Messenger webhook: {e}")
        return events

    async def send_text(self, recipient_id: str, text: str) -> Dict:
        return await self._send_message(recipient_id, {"text": text})

    async def send_image(self, recipient_id: str, image_url: str) -> Dict:
        return await self._send_message(
            recipient_id,
            {"attachment": {"type": "image", "payload": {"url": image_url, "is_reusable": True}}},
        )

    async def send_template(self, recipient_id: str, elements: List[Dict]) -> Dict:
        return await self._send_message(
            recipient_id,
            {
                "attachment": {
                    "type": "template",
                    "payload": {"template_type": "generic", "elements": elements},
                }
            },
        )

    async def send_quick_replies(
        self, recipient_id: str, text: str, quick_replies: List[Dict]
    ) -> Dict:
        return await self._send_message(
            recipient_id,
            {"text": text, "quick_replies": quick_replies},
        )

    async def _send_message(self, recipient_id: str, message: Dict) -> Dict:
        payload = {
            "recipient": {"id": recipient_id},
            "message": message,
            "messaging_type": "RESPONSE",
        }
        url = f"{MESSENGER_API_BASE}/me/messages"
        params = {"access_token": self.page_access_token}
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, params=params)
            response.raise_for_status()
            return response.json()
