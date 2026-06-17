"""
Webhook router - handles incoming messages from WhatsApp, Messenger, Instagram,
and the embeddable website chat widget.
"""
import logging
import json
from typing import Any, Dict, Optional
from fastapi import APIRouter, Request, Response, HTTPException, BackgroundTasks
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from app.services.platforms.whatsapp import WhatsAppHandler
from app.services.platforms.messenger import MessengerHandler
from app.services.platforms.instagram import InstagramHandler
from app.services.ai.router import AIRouter
from app.services.nlp.sentiment import SentimentAnalyzer
from app.services.nlp.intent import IntentDetector
from app.services.nlp.ner import NERService
from app.services.media.voice import VoiceService
from app.services.personalization import PersonalizationService
from app.services.recommendation import RecommendationEngine
from app.services.website.order_sync import OrderSyncService
from app.utils.audit_log import audit_logger
from app.utils.hebrew import format_hebrew_message
from app.database import AsyncSessionLocal
from app.models.user import User, Platform
from app.models.conversation import Conversation, Message, MessageRole, MessageType, ConversationStatus
from sqlalchemy import select

router = APIRouter()
logger = logging.getLogger(__name__)

# Service instances
whatsapp = WhatsAppHandler()
messenger = MessengerHandler()
instagram = InstagramHandler()
ai_router = AIRouter()
sentiment_analyzer = SentimentAnalyzer()
intent_detector = IntentDetector()
ner_service = NERService()
voice_service = VoiceService()
personalization = PersonalizationService()
recommender = RecommendationEngine()
order_sync = OrderSyncService()


# ── WhatsApp ──────────────────────────────────────────────────────────────────

@router.get("/whatsapp")
async def whatsapp_verify(
    hub_mode: str = None,
    hub_verify_token: str = None,
    hub_challenge: str = None,
):
    """WhatsApp webhook verification."""
    challenge = whatsapp.verify_webhook(
        hub_mode or "",
        hub_verify_token or "",
        hub_challenge or "",
    )
    if challenge:
        return PlainTextResponse(challenge)
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/whatsapp")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    """Handle incoming WhatsApp messages."""
    body = await request.body()

    # Verify signature in production
    signature = request.headers.get("X-Hub-Signature-256", "")
    if signature and not whatsapp.verify_signature(body, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    events = whatsapp.parse_webhook(payload)
    for event in events:
        if event.get("event_type") == "message":
            background_tasks.add_task(handle_message, event, whatsapp)

    return {"status": "ok"}


# ── Messenger ────────────────────────────────────────────────────────────────

@router.get("/messenger")
async def messenger_verify(
    hub_mode: str = None,
    hub_verify_token: str = None,
    hub_challenge: str = None,
):
    challenge = messenger.verify_webhook(hub_mode or "", hub_verify_token or "", hub_challenge or "")
    if challenge:
        return PlainTextResponse(challenge)
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/messenger")
async def messenger_webhook(request: Request, background_tasks: BackgroundTasks):
    body = await request.body()
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    events = messenger.parse_webhook(payload)
    for event in events:
        if event.get("event_type") == "message":
            background_tasks.add_task(handle_message, event, messenger)

    return {"status": "ok"}


# ── Instagram ────────────────────────────────────────────────────────────────

@router.get("/instagram")
async def instagram_verify(
    hub_mode: str = None,
    hub_verify_token: str = None,
    hub_challenge: str = None,
):
    challenge = instagram.verify_webhook(hub_mode or "", hub_verify_token or "", hub_challenge or "")
    if challenge:
        return PlainTextResponse(challenge)
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/instagram")
async def instagram_webhook(request: Request, background_tasks: BackgroundTasks):
    body = await request.body()
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    events = instagram.parse_webhook(payload)
    for event in events:
        if event.get("event_type") == "message":
            background_tasks.add_task(handle_message, event, instagram)

    return {"status": "ok"}


# ── Website Chat Widget ───────────────────────────────────────────────────────

class WebsiteChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    visitor_id: Optional[str] = None
    page_url: Optional[str] = None
    user_name: Optional[str] = None


class WebsiteChatResponse(BaseModel):
    reply: str
    session_id: str
    intent: Optional[str] = None
    recommendations: list = []


@router.post("/website", response_model=WebsiteChatResponse)
async def website_chat(payload: WebsiteChatRequest):
    """
    Handle messages from the embeddable website chat widget.
    Returns a synchronous response (unlike platform webhooks which use
    background tasks) so the widget can display the reply immediately.
    """
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Empty message")

    # Build a synthetic event that reuses the same pipeline
    platform = "website"
    sender_id = payload.visitor_id or payload.session_id or "anonymous"
    session_id = payload.session_id or sender_id

    try:
        # Get / create user record for this website visitor
        user = await get_or_create_user(platform, sender_id, payload.user_name)

        # Get / create conversation session
        conv = await get_or_create_conversation(str(user.id), platform, sender_id)

        # Save the incoming user message
        await save_message(str(conv.id), MessageRole.USER, payload.message)

        # Detect intent & sentiment
        intent_result = await intent_detector.detect(payload.message)
        sentiment_result = await sentiment_analyzer.analyze(payload.message)

        # Build personalised system prompt
        user_context = await personalization.get_user_context(str(user.id))
        system_prompt = personalization.build_system_prompt(user_context)

        # Optional: enrich with order context
        extra_context = ""
        if intent_result.get("requires_order_lookup"):
            ner_result = await ner_service.extract_entities(payload.message)
            if ner_result.get("order_ids"):
                order_id = ner_result["order_ids"][0]
                order = await order_sync.get_order_by_id(str(order_id))
                if order:
                    extra_context = f"\n\nמידע הזמנה:\n{order_sync.format_order_for_message(order)}"

        # Build chat history + current message
        history = await get_conversation_history(str(conv.id), limit=10)
        messages = history + [{"role": "user", "content": payload.message + extra_context}]

        # Generate AI response
        ai_result = await ai_router.chat(messages, system_prompt=system_prompt)
        reply_text = ai_result.get("content", "מצטער, אירעה שגיאה. אנא נסה שוב.")

        # Save AI response
        await save_message(
            str(conv.id),
            MessageRole.ASSISTANT,
            reply_text,
            MessageType.TEXT,
            ai_provider=ai_result.get("provider"),
            ai_model=ai_result.get("model"),
            tokens_used=ai_result.get("tokens_used"),
            intent_detected=intent_result.get("intent"),
        )

        # Update conversation metadata
        await update_conversation(
            str(conv.id),
            intent=intent_result.get("intent"),
            sentiment=sentiment_result.get("sentiment"),
            sentiment_score=sentiment_result.get("score"),
            ai_provider=ai_result.get("provider"),
        )

        # Optional product recommendations
        rec_data: list = []
        if intent_result.get("requires_product_lookup"):
            recs = await recommender.get_recommendations(user_context, payload.message, limit=3)
            rec_data = [
                {
                    "name": r.get("name_he") or r.get("name", ""),
                    "price": r.get("price", 0),
                    "thumbnail": r.get("thumbnail"),
                    "url": r.get("url", ""),
                }
                for r in recs
            ]

        await audit_logger.log_message_received(platform, sender_id, str(conv.id))

        return WebsiteChatResponse(
            reply=format_hebrew_message(reply_text),
            session_id=session_id,
            intent=intent_result.get("intent"),
            recommendations=rec_data,
        )

    except Exception as e:
        logger.error(f"Website chat error for visitor {sender_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="שגיאה טכנית. אנא נסה שוב.")


# ── Core message handler ─────────────────────────────────────────────────────

async def handle_message(event: Dict[str, Any], platform_handler):
    """
    Core message processing pipeline:
    1. Get/create user
    2. Transcribe voice if needed
    3. Analyze intent and sentiment
    4. Build personalized context
    5. Generate AI response
    6. Send response with media if available
    7. Log analytics
    """
    platform = event.get("platform")
    sender_id = event.get("sender_id")
    content = event.get("content", "")
    message_type = event.get("message_type", "text")

    try:
        # Step 1: Get or create user
        user = await get_or_create_user(platform, sender_id, event.get("sender_name"))

        # Step 2: Get or create conversation session
        conversation = await get_or_create_conversation(str(user.id), platform, sender_id)

        # Step 3: Transcribe voice message
        if message_type in ("audio", "voice") and event.get("media_id"):
            try:
                media_url = await whatsapp.get_media_url(event["media_id"])
                from app.config import settings
                content = await voice_service.transcribe_from_url(
                    media_url, auth_token=settings.WHATSAPP_ACCESS_TOKEN
                )
                logger.info(f"Transcribed voice: {content[:100]}")
            except Exception as e:
                logger.error(f"Voice transcription failed: {e}")
                content = "[הודעת קול לא ניתנת לתמלול]"

        if not content.strip():
            return

        # Step 4: Log user message
        await save_message(str(conversation.id), MessageRole.USER, content, message_type)

        # Step 5: Analyze intent and sentiment concurrently
        intent_result = await intent_detector.detect(content)
        sentiment_result = await sentiment_analyzer.analyze(content)

        # Step 6: Build personalized context
        user_context = await personalization.get_user_context(str(user.id))
        system_prompt = personalization.build_system_prompt(user_context)

        # Step 7: Handle order status intent specially
        extra_context = ""
        if intent_result.get("requires_order_lookup"):
            entities = intent_result.get("entities", {})
            order_ids = entities.get("order_ids") or ner_service
            # Try to get order from conversation entities
            ner_result = await ner_service.extract_entities(content)
            if ner_result.get("order_ids"):
                order_id = ner_result["order_ids"][0]
                order = await order_sync.get_order_by_id(str(order_id))
                if order:
                    extra_context = f"\n\nמידע הזמנה:\n{order_sync.format_order_for_message(order)}"

        # Step 8: Get conversation history for context
        history = await get_conversation_history(str(conversation.id), limit=10)

        # Step 9: Generate AI response
        messages = history + [{"role": "user", "content": content + extra_context}]
        ai_result = await ai_router.chat(messages, system_prompt=system_prompt)
        response_text = ai_result.get("content", "מצטער, אירעה שגיאה. אנא נסה שוב.")

        # Step 10: Get product recommendations if relevant
        if intent_result.get("requires_product_lookup"):
            recommendations = await recommender.get_recommendations(
                user_context,
                content,
                limit=3,
            )
            if recommendations:
                await send_product_recommendations(platform_handler, sender_id, recommendations)

        # Step 11: Send text response
        await platform_handler.send_text(sender_id, format_hebrew_message(response_text))

        # Step 12: Save AI response
        await save_message(
            str(conversation.id),
            MessageRole.ASSISTANT,
            response_text,
            MessageType.TEXT,
            ai_provider=ai_result.get("provider"),
            ai_model=ai_result.get("model"),
            tokens_used=ai_result.get("tokens_used"),
            intent_detected=intent_result.get("intent"),
        )

        # Step 13: Update conversation analytics
        await update_conversation(
            str(conversation.id),
            intent=intent_result.get("intent"),
            sentiment=sentiment_result.get("sentiment"),
            sentiment_score=sentiment_result.get("score"),
            ai_provider=ai_result.get("provider"),
        )

        # Step 14: Audit log
        await audit_logger.log_message_received(platform, sender_id, str(conversation.id))

    except Exception as e:
        logger.error(f"Message handling error for {sender_id}: {e}", exc_info=True)
        try:
            await platform_handler.send_text(
                sender_id,
                "מצטער, אירעה שגיאה טכנית. אנא נסה שוב מאוחר יותר."
            )
        except Exception:
            pass


async def send_product_recommendations(platform_handler, sender_id: str, products: list):
    """Send product recommendations with images."""
    if not products:
        return
    for product in products[:3]:
        try:
            name = product.get("name_he") or product.get("name", "")
            price = product.get("price", 0)
            url = product.get("url", "")
            caption = f"*{name}*\n₪{price:.2f}"
            if url:
                caption += f"\n{url}"

            if product.get("thumbnail"):
                await platform_handler.send_image(
                    sender_id,
                    product["thumbnail"],
                    caption=caption,
                )
            else:
                await platform_handler.send_text(sender_id, caption)
        except Exception as e:
            logger.error(f"Failed to send product recommendation: {e}")


async def get_or_create_user(platform: str, platform_id: str, name: str = None) -> User:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(
                User.platform == Platform(platform),
                User.platform_id == platform_id,
            )
        )
        user = result.scalar_one_or_none()
        if not user:
            from app.models.user import UserProfile
            user = User(
                platform=Platform(platform),
                platform_id=platform_id,
                name=name,
                language="he",
            )
            session.add(user)
            await session.flush()
            profile = UserProfile(user_id=user.id)
            session.add(profile)
            await session.commit()
            await session.refresh(user)
            await audit_logger.log_user_created(str(user.id), platform)
        return user


async def get_or_create_conversation(user_id: str, platform: str, sender_id: str) -> Conversation:
    session_id = f"{platform}:{sender_id}"
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Conversation).where(
                Conversation.session_id == session_id,
                Conversation.status == ConversationStatus.ACTIVE,
            )
        )
        conv = result.scalar_one_or_none()
        if not conv:
            from datetime import datetime
            conv = Conversation(
                user_id=user_id,
                platform=platform,
                session_id=session_id,
                status=ConversationStatus.ACTIVE,
                started_at=datetime.utcnow(),
            )
            session.add(conv)
            await session.commit()
            await session.refresh(conv)
        return conv


async def save_message(
    conversation_id: str,
    role: MessageRole,
    content: str,
    message_type=MessageType.TEXT,
    ai_provider: str = None,
    ai_model: str = None,
    tokens_used: int = None,
    intent_detected: str = None,
) -> Message:
    async with AsyncSessionLocal() as session:
        msg = Message(
            conversation_id=conversation_id,
            role=role,
            message_type=message_type,
            content=content,
            ai_provider=ai_provider,
            ai_model=ai_model,
            tokens_used=tokens_used,
            intent_detected=intent_detected,
        )
        session.add(msg)
        await session.commit()
        return msg


async def get_conversation_history(conversation_id: str, limit: int = 10) -> list:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        messages = list(reversed(result.scalars().all()))

    return [
        {"role": msg.role.value, "content": msg.content}
        for msg in messages
        if msg.role in (MessageRole.USER, MessageRole.ASSISTANT)
    ]


async def update_conversation(
    conversation_id: str,
    intent: str = None,
    sentiment: str = None,
    sentiment_score: float = None,
    ai_provider: str = None,
):
    from datetime import datetime
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conv = result.scalar_one_or_none()
        if conv:
            if intent:
                conv.intent = intent
            if sentiment:
                conv.sentiment = sentiment
            if sentiment_score is not None:
                conv.sentiment_score = sentiment_score
            if ai_provider:
                conv.ai_provider_used = ai_provider
            conv.last_message_at = datetime.utcnow()
            conv.total_messages = (conv.total_messages or 0) + 1
            await session.commit()
