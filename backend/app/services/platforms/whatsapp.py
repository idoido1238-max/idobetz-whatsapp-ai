"""
WhatsApp Business API handler.
Handles incoming webhooks, message parsing, and sending messages.
"""
import hashlib
import hmac
import json
import logging
from typing import Any, Dict, List, Optional
import httpx

from app.config import settings

logger = logging.getLogger(__name__)

WHATSAPP_API_BASE = f"https://graph.facebook.com/{settings.WHATSAPP_API_VERSION}"


class WhatsAppHandler:
    def __init__(self):
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.access_token = settings.WHATSAPP_ACCESS_TOKEN
        self.api_base = WHATSAPP_API_BASE

    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """Verify WhatsApp webhook."""
        if mode == "subscribe" and token == settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN:
            return challenge
        return None

    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify webhook payload signature."""
        expected = hmac.new(
            settings.WHATSAPP_ACCESS_TOKEN.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(f"sha256={expected}", signature)

    def parse_webhook(self, payload: Dict) -> List[Dict]:
        """
        Parse WhatsApp webhook payload.
        Returns list of normalized message events.
        """
        events = []
        try:
            for entry in payload.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})

                    # Process messages
                    for message in value.get("messages", []):
                        sender = message.get("from")
                        contact = next(
                            (c for c in value.get("contacts", []) if c.get("wa_id") == sender),
                            {}
                        )
                        events.append({
                            "platform": "whatsapp",
                            "event_type": "message",
                            "sender_id": sender,
                            "sender_name": contact.get("profile", {}).get("name", ""),
                            "message_id": message.get("id"),
                            "timestamp": message.get("timestamp"),
                            "message_type": message.get("type"),
                            "content": self._extract_content(message),
                            "media_id": self._extract_media_id(message),
                            "raw": message,
                        })

                    # Process status updates
                    for status in value.get("statuses", []):
                        events.append({
                            "platform": "whatsapp",
                            "event_type": "status",
                            "message_id": status.get("id"),
                            "status": status.get("status"),
                            "timestamp": status.get("timestamp"),
                            "recipient_id": status.get("recipient_id"),
                        })
        except Exception as e:
            logger.error(f"Error parsing WhatsApp webhook: {e}")
        return events

    def _extract_content(self, message: Dict) -> str:
        """Extract text content from message."""
        msg_type = message.get("type")
        if msg_type == "text":
            return message.get("text", {}).get("body", "")
        elif msg_type == "image":
            return message.get("image", {}).get("caption", "")
        elif msg_type == "document":
            return message.get("document", {}).get("caption", "")
        elif msg_type == "audio":
            return ""  # Will be transcribed
        elif msg_type == "voice":
            return ""  # Will be transcribed
        elif msg_type == "location":
            loc = message.get("location", {})
            return f"Location: {loc.get('latitude')}, {loc.get('longitude')}"
        elif msg_type == "button":
            return message.get("button", {}).get("text", "")
        elif msg_type == "interactive":
            interactive = message.get("interactive", {})
            if interactive.get("type") == "button_reply":
                return interactive.get("button_reply", {}).get("title", "")
            elif interactive.get("type") == "list_reply":
                return interactive.get("list_reply", {}).get("title", "")
        return ""

    def _extract_media_id(self, message: Dict) -> Optional[str]:
        """Extract media ID if present."""
        msg_type = message.get("type")
        for media_key in ["image", "video", "audio", "document", "voice", "sticker"]:
            if msg_type == media_key:
                return message.get(media_key, {}).get("id")
        return None

    async def send_text(self, to: str, text: str) -> Dict:
        """Send a text message."""
        return await self._send_message(to, {"type": "text", "text": {"body": text}})

    async def send_template(
        self,
        to: str,
        template_name: str,
        language_code: str = "he",
        components: Optional[List[Dict]] = None,
    ) -> Dict:
        """Send a template message."""
        template_data: Dict[str, Any] = {
            "name": template_name,
            "language": {"code": language_code},
        }
        if components:
            template_data["components"] = components
        return await self._send_message(to, {"type": "template", "template": template_data})

    async def send_image(self, to: str, image_url: str, caption: str = "") -> Dict:
        """Send an image message."""
        return await self._send_message(
            to,
            {
                "type": "image",
                "image": {"link": image_url, "caption": caption},
            },
        )

    async def send_document(self, to: str, document_url: str, filename: str, caption: str = "") -> Dict:
        """Send a document (PDF, etc.)."""
        return await self._send_message(
            to,
            {
                "type": "document",
                "document": {"link": document_url, "filename": filename, "caption": caption},
            },
        )

    async def send_interactive_buttons(
        self, to: str, body_text: str, buttons: List[Dict]
    ) -> Dict:
        """Send interactive button message."""
        return await self._send_message(
            to,
            {
                "type": "interactive",
                "interactive": {
                    "type": "button",
                    "body": {"text": body_text},
                    "action": {
                        "buttons": [
                            {"type": "reply", "reply": {"id": btn["id"], "title": btn["title"]}}
                            for btn in buttons[:3]  # WhatsApp max 3 buttons
                        ]
                    },
                },
            },
        )

    async def send_interactive_list(
        self, to: str, body_text: str, button_text: str, sections: List[Dict]
    ) -> Dict:
        """Send interactive list message."""
        return await self._send_message(
            to,
            {
                "type": "interactive",
                "interactive": {
                    "type": "list",
                    "body": {"text": body_text},
                    "action": {
                        "button": button_text,
                        "sections": sections,
                    },
                },
            },
        )

    async def mark_as_read(self, message_id: str) -> Dict:
        """Mark message as read."""
        return await self._send_message(
            None,
            None,
            extra={
                "messaging_product": "whatsapp",
                "status": "read",
                "message_id": message_id,
            },
        )

    async def _send_message(
        self,
        to: Optional[str],
        message_data: Optional[Dict],
        extra: Optional[Dict] = None,
    ) -> Dict:
        """Send a message via WhatsApp API."""
        if extra:
            payload = extra
        else:
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to,
                **message_data,
            }

        url = f"{self.api_base}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()

    async def get_media_url(self, media_id: str) -> str:
        """Get download URL for a media file."""
        url = f"{self.api_base}/{media_id}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json().get("url", "")

    async def download_media(self, media_url: str) -> bytes:
        """Download media file content."""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(media_url, headers=headers)
            response.raise_for_status()
            return response.content
