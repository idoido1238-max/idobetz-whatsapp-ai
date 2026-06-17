"""
OpenAI GPT-4 service integration.
"""
import logging
from typing import List, Optional
from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)


class OpenAIService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        self.temperature = settings.OPENAI_TEMPERATURE

    async def chat(
        self,
        messages: List[dict],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> dict:
        """
        Send chat messages to OpenAI and return response.

        Returns:
            dict with 'content', 'tokens_used', 'model'
        """
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                max_tokens=max_tokens or self.max_tokens,
                temperature=temperature or self.temperature,
            )
            return {
                "content": response.choices[0].message.content,
                "tokens_used": response.usage.total_tokens,
                "model": response.model,
                "provider": "openai",
                "finish_reason": response.choices[0].finish_reason,
            }
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            raise

    async def transcribe_audio(self, audio_file_path: str) -> str:
        """Transcribe audio file using Whisper API."""
        try:
            with open(audio_file_path, "rb") as audio_file:
                transcript = await self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="he",
                )
            return transcript.text
        except Exception as e:
            logger.error(f"Whisper transcription error: {e}")
            raise

    async def text_to_speech(self, text: str, voice: str = "alloy") -> bytes:
        """Convert text to speech."""
        try:
            response = await self.client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text,
            )
            return response.content
        except Exception as e:
            logger.error(f"TTS error: {e}")
            raise

    async def analyze_sentiment(self, text: str) -> dict:
        """Analyze sentiment using GPT-4."""
        messages = [
            {
                "role": "user",
                "content": f"Analyze the sentiment of this text and return JSON with 'sentiment' (positive/negative/neutral) and 'score' (0-1): {text}"
            }
        ]
        result = await self.chat(messages, temperature=0.1)
        import json
        try:
            return json.loads(result["content"])
        except json.JSONDecodeError:
            return {"sentiment": "neutral", "score": 0.5}

    async def detect_intent(self, text: str, context: Optional[str] = None) -> dict:
        """Detect user intent."""
        context_str = f"\nContext: {context}" if context else ""
        messages = [
            {
                "role": "user",
                "content": f"""Detect the intent of this message and return JSON with:
- 'intent': one of [order_status, product_inquiry, support, complaint, greeting, farewell, price_inquiry, recommendation, cart_help, general]
- 'confidence': 0-1
- 'entities': extracted named entities as dict
Message: {text}{context_str}"""
            }
        ]
        result = await self.chat(messages, temperature=0.1)
        import json
        try:
            return json.loads(result["content"])
        except json.JSONDecodeError:
            return {"intent": "general", "confidence": 0.5, "entities": {}}
