"""
AI Router - intelligently routes requests to the appropriate AI provider.
Supports OpenAI, Claude, Ollama, and Consensus mode.
"""
import logging
from typing import List, Optional

from app.config import settings
from app.services.ai.openai_service import OpenAIService
from app.services.ai.claude_service import ClaudeService
from app.services.ai.ollama_service import OllamaService

logger = logging.getLogger(__name__)


class AIRouter:
    """
    Routes AI requests to the appropriate provider based on configuration.
    Supports fallback and consensus modes.
    """

    def __init__(self):
        self.openai = OpenAIService()
        self.claude = ClaudeService()
        self.ollama = OllamaService()
        self.primary = settings.AI_PROVIDER
        self.fallback = settings.AI_FALLBACK_PROVIDER

    async def chat(
        self,
        messages: List[dict],
        system_prompt: Optional[str] = None,
        provider: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> dict:
        """
        Route chat request to the appropriate AI provider with fallback.
        """
        provider = provider or self.primary

        if provider == "consensus":
            return await self._consensus_chat(messages, system_prompt, temperature, max_tokens)

        return await self._chat_with_fallback(
            provider, messages, system_prompt, temperature, max_tokens
        )

    async def _chat_with_fallback(
        self,
        provider: str,
        messages: List[dict],
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: Optional[int],
    ) -> dict:
        """Try primary provider, fall back on failure."""
        try:
            return await self._route_to_provider(provider, messages, system_prompt, temperature, max_tokens)
        except Exception as e:
            logger.warning(f"Primary provider '{provider}' failed: {e}. Falling back to '{self.fallback}'")
            try:
                result = await self._route_to_provider(
                    self.fallback, messages, system_prompt, temperature, max_tokens
                )
                result["fallback_used"] = True
                return result
            except Exception as e2:
                logger.error(f"Fallback provider '{self.fallback}' also failed: {e2}")
                raise RuntimeError(f"All AI providers failed. Last error: {e2}")

    async def _route_to_provider(
        self,
        provider: str,
        messages: List[dict],
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: Optional[int],
    ) -> dict:
        """Route to specific provider."""
        if provider == "openai":
            return await self.openai.chat(messages, system_prompt, temperature, max_tokens)
        elif provider == "claude":
            return await self.claude.chat(messages, system_prompt, temperature, max_tokens)
        elif provider == "ollama":
            if not settings.OLLAMA_ENABLED:
                raise ValueError("Ollama is not enabled")
            return await self.ollama.chat(messages, system_prompt, temperature, max_tokens)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    async def _consensus_chat(
        self,
        messages: List[dict],
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: Optional[int],
    ) -> dict:
        """
        Consensus mode: query multiple AIs and pick the best response.
        Uses simple voting/scoring to determine winner.
        """
        results = []
        providers = ["openai", "claude"]

        for p in providers:
            try:
                result = await self._route_to_provider(p, messages, system_prompt, temperature, max_tokens)
                results.append(result)
            except Exception as e:
                logger.warning(f"Consensus: provider {p} failed: {e}")

        if not results:
            raise RuntimeError("All consensus providers failed")

        if len(results) == 1:
            results[0]["consensus"] = False
            return results[0]

        # Simple consensus: use the longer, more detailed response
        best = max(results, key=lambda r: len(r.get("content", "")))
        best["consensus"] = True
        best["consensus_providers"] = [r["provider"] for r in results]
        return best

    async def transcribe_audio(self, audio_file_path: str) -> str:
        """Transcribe audio using Whisper (OpenAI)."""
        return await self.openai.transcribe_audio(audio_file_path)

    async def text_to_speech(self, text: str, voice: str = "alloy") -> bytes:
        """Convert text to speech."""
        return await self.openai.text_to_speech(text, voice)

    async def analyze_sentiment(self, text: str) -> dict:
        """Analyze sentiment."""
        return await self.openai.analyze_sentiment(text)

    async def detect_intent(self, text: str, context: Optional[str] = None) -> dict:
        """Detect user intent."""
        return await self.openai.detect_intent(text, context)
