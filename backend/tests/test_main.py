"""
Tests for Idobetz AI Bot backend.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient


# ── Config tests ──────────────────────────────────────────────────────────────

def test_config_defaults():
    """Test that config has reasonable defaults."""
    from app.config import Settings
    settings = Settings()
    assert settings.ENV in ("development", "production", "test")
    assert settings.OPENAI_MODEL == "gpt-4o"
    assert settings.AI_PROVIDER in ("openai", "claude", "ollama", "consensus")
    assert settings.RATE_LIMIT_PER_MINUTE > 0


# ── Hebrew utilities tests ────────────────────────────────────────────────────

def test_is_hebrew_with_hebrew_text():
    from app.utils.hebrew import is_hebrew
    assert is_hebrew("שלום עולם") is True


def test_is_hebrew_with_english_text():
    from app.utils.hebrew import is_hebrew
    assert is_hebrew("Hello world") is False


def test_is_hebrew_with_mixed_text():
    from app.utils.hebrew import is_hebrew
    assert is_hebrew("שלום Hello") is True


def test_format_currency_hebrew():
    from app.utils.hebrew import format_currency_hebrew
    result = format_currency_hebrew(49.99, "ILS")
    assert "49.99" in result
    assert "₪" in result


def test_format_order_status_hebrew():
    from app.utils.hebrew import format_order_status_hebrew
    assert format_order_status_hebrew("shipped") == "נשלח"
    assert format_order_status_hebrew("delivered") == "נמסר"
    assert format_order_status_hebrew("pending") == "ממתין לאישור"


def test_truncate_hebrew():
    from app.utils.hebrew import truncate_hebrew
    short = "שלום"
    assert truncate_hebrew(short, 100) == short
    long_text = "א " * 60
    result = truncate_hebrew(long_text, 10)
    assert len(result) <= 13  # max_length + "..."


# ── Order model tests ─────────────────────────────────────────────────────────

def test_order_full_address():
    """Test order full_address property."""
    from app.models.order import Order
    order = Order()
    order.shipping_street = "רחוב הרצל 5"
    order.shipping_city = "תל אביב"
    order.shipping_postal_code = "6120101"
    order.shipping_country = "Israel"

    address = order.full_address
    assert "תל אביב" in address
    assert "רחוב הרצל 5" in address


def test_order_full_address_empty():
    """Test order full_address when fields are empty."""
    from app.models.order import Order
    order = Order()
    order.shipping_street = None
    order.shipping_city = None
    order.shipping_postal_code = None
    order.shipping_country = None
    # Should not raise
    address = order.full_address
    assert isinstance(address, str)


# ── Product model tests ───────────────────────────────────────────────────────

def test_product_effective_price_no_sale():
    """Test product effective price without sale."""
    from app.models.product import Product
    product = Product()
    product.price = 100.0
    product.sale_price = None
    assert product.effective_price == 100.0


def test_product_effective_price_with_sale():
    """Test product effective price with sale."""
    from app.models.product import Product
    product = Product()
    product.price = 100.0
    product.sale_price = 75.0
    assert product.effective_price == 75.0


def test_product_is_on_sale():
    """Test product is_on_sale flag."""
    from app.models.product import Product
    product = Product()
    product.price = 100.0
    product.sale_price = 75.0
    assert product.is_on_sale is True


def test_product_not_on_sale():
    from app.models.product import Product
    product = Product()
    product.price = 100.0
    product.sale_price = None
    assert product.is_on_sale is False


# ── WhatsApp handler tests ────────────────────────────────────────────────────

def test_whatsapp_parse_text_message():
    """Test parsing a WhatsApp text message webhook."""
    from app.services.platforms.whatsapp import WhatsAppHandler
    handler = WhatsAppHandler()

    payload = {
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "from": "972501234567",
                        "id": "wamid.test123",
                        "timestamp": "1234567890",
                        "type": "text",
                        "text": {"body": "שלום, מה מצב ההזמנה שלי?"},
                    }],
                    "contacts": [{
                        "wa_id": "972501234567",
                        "profile": {"name": "ישראל ישראלי"},
                    }],
                }
            }]
        }]
    }

    events = handler.parse_webhook(payload)
    assert len(events) == 1
    assert events[0]["platform"] == "whatsapp"
    assert events[0]["event_type"] == "message"
    assert events[0]["sender_id"] == "972501234567"
    assert events[0]["content"] == "שלום, מה מצב ההזמנה שלי?"
    assert events[0]["sender_name"] == "ישראל ישראלי"


def test_whatsapp_parse_voice_message():
    """Test parsing a WhatsApp voice message."""
    from app.services.platforms.whatsapp import WhatsAppHandler
    handler = WhatsAppHandler()

    payload = {
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "from": "972501234567",
                        "id": "wamid.voice123",
                        "timestamp": "1234567890",
                        "type": "audio",
                        "audio": {"id": "media_id_abc"},
                    }],
                    "contacts": [],
                }
            }]
        }]
    }

    events = handler.parse_webhook(payload)
    assert len(events) == 1
    assert events[0]["message_type"] == "audio"
    assert events[0]["media_id"] == "media_id_abc"


def test_whatsapp_parse_status_update():
    """Test parsing a WhatsApp status update."""
    from app.services.platforms.whatsapp import WhatsAppHandler
    handler = WhatsAppHandler()

    payload = {
        "entry": [{
            "changes": [{
                "value": {
                    "statuses": [{
                        "id": "wamid.test123",
                        "status": "delivered",
                        "timestamp": "1234567890",
                        "recipient_id": "972501234567",
                    }],
                    "messages": [],
                }
            }]
        }]
    }

    events = handler.parse_webhook(payload)
    assert len(events) == 1
    assert events[0]["event_type"] == "status"
    assert events[0]["status"] == "delivered"


def test_whatsapp_verify_webhook():
    """Test WhatsApp webhook verification."""
    from app.services.platforms.whatsapp import WhatsAppHandler
    handler = WhatsAppHandler()

    # Valid verification
    result = handler.verify_webhook(
        "subscribe",
        "idobetz_verify_token",
        "challenge_123",
    )
    assert result == "challenge_123"

    # Invalid token
    result = handler.verify_webhook("subscribe", "wrong_token", "challenge_123")
    assert result is None


# ── Intent detection tests ────────────────────────────────────────────────────

def test_intent_detector_supported_intents():
    """Test that supported intents list is comprehensive."""
    from app.services.nlp.intent import SUPPORTED_INTENTS
    required_intents = [
        "order_status", "product_inquiry", "support_request",
        "greeting", "farewell", "complaint",
    ]
    for intent in required_intents:
        assert intent in SUPPORTED_INTENTS


# ── Campaign model tests ──────────────────────────────────────────────────────

def test_campaign_status_values():
    """Test campaign status enum values."""
    from app.models.campaign import CampaignStatus
    assert CampaignStatus.DRAFT == "draft"
    assert CampaignStatus.RUNNING == "running"
    assert CampaignStatus.COMPLETED == "completed"


def test_campaign_type_values():
    """Test campaign type enum values."""
    from app.models.campaign import CampaignType
    assert CampaignType.BROADCAST == "broadcast"
    assert CampaignType.BIRTHDAY == "birthday"
    assert CampaignType.ABANDONED_CART == "abandoned_cart"


# ── Personalization tests ─────────────────────────────────────────────────────

def test_personalization_birthday_check():
    """Test birthday detection."""
    from app.services.personalization import PersonalizationService
    from datetime import datetime

    service = PersonalizationService()
    today = datetime.utcnow()

    # Birthday today
    birthday = datetime(2000, today.month, today.day)
    assert service._is_birthday(birthday) is True

    # Birthday not today
    other_month = 1 if today.month != 1 else 2
    not_birthday = datetime(2000, other_month, 15)
    assert service._is_birthday(not_birthday) is False

    # No birthday set
    assert service._is_birthday(None) is False


def test_personalization_system_prompt_vip():
    """Test VIP user system prompt generation."""
    from app.services.personalization import PersonalizationService
    service = PersonalizationService()

    context = {
        "name": "יוסי",
        "tier": "vip",
        "is_vip": True,
        "loyalty_points": 500,
        "language": "he",
        "is_birthday": False,
        "is_new_customer": False,
        "purchase_count": 10,
        "recent_orders": [],
    }

    prompt = service.build_system_prompt(context)
    assert "יוסי" in prompt
    assert "VIP" in prompt


def test_personalization_system_prompt_birthday():
    """Test birthday prompt."""
    from app.services.personalization import PersonalizationService
    service = PersonalizationService()

    context = {
        "name": "שרה",
        "tier": "standard",
        "is_vip": False,
        "loyalty_points": 50,
        "language": "he",
        "is_birthday": True,
        "is_new_customer": False,
        "purchase_count": 3,
        "recent_orders": [],
    }

    prompt = service.build_system_prompt(context)
    assert "🎂" in prompt or "יום הולדת" in prompt


# ── Order sync tests ──────────────────────────────────────────────────────────

def test_order_format_for_message():
    """Test order message formatting with full address."""
    from app.services.website.order_sync import OrderSyncService
    from app.models.order import Order, OrderStatus

    service = OrderSyncService()
    order = Order()
    order.external_order_id = "12345"
    order.status = OrderStatus.SHIPPED
    order.total_amount = 249.90
    order.shipping_street = "רחוב דיזנגוף 100"
    order.shipping_city = "תל אביב"
    order.shipping_postal_code = "6423214"
    order.shipping_country = "Israel"
    order.tracking_number = "TRK987654"
    order.carrier = "DHL"
    order.estimated_delivery = None

    message = service.format_order_for_message(order)
    assert "12345" in message
    assert "תל אביב" in message
    assert "TRK987654" in message
    assert "₪" in message


# ── QR code tests ─────────────────────────────────────────────────────────────

def test_qr_code_generation():
    """Test QR code generation returns bytes."""
    from app.services.media.qr_code import QRCodeService
    service = QRCodeService()
    qr_bytes = service.generate("https://idobetz.co.il")
    assert isinstance(qr_bytes, bytes)
    assert len(qr_bytes) > 0
    # PNG magic bytes
    assert qr_bytes[:4] == b'\x89PNG'


def test_qr_code_whatsapp():
    """Test WhatsApp QR code generation."""
    from app.services.media.qr_code import QRCodeService
    service = QRCodeService()
    qr_bytes = service.generate_whatsapp_qr("972501234567", "שלום")
    assert isinstance(qr_bytes, bytes)
    assert len(qr_bytes) > 0
