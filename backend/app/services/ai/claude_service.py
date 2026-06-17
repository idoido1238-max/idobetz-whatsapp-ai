"""
Anthropic Claude service integration.
"""
import logging
from typing import List, Optional
import anthropic

from app.config import settings

logger = logging.getLogger(__name__)


class ClaudeService:
    def __init__(self):
        self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.ANTHROPIC_MODEL
        self.max_tokens = settings.ANTHROPIC_MAX_TOKENS

    async def chat(
        self,
        messages: List[dict],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> dict:
        """
        Send chat messages to Claude and return response.

        Returns:
            dict with 'content', 'tokens_used', 'model'
        """
        # Claude requires non-empty messages and specific format
        claude_messages = []
        for msg in messages:
            if msg["role"] in ("user", "assistant"):
                claude_messages.append({"role": msg["role"], "content": msg["content"]})

        try:
            kwargs = {
                "model": self.model,
                "max_tokens": max_tokens or self.max_tokens,
                "messages": claude_messages,
            }
            if system_prompt:
                kwargs["system"] = system_prompt

            response = await self.client.messages.create(**kwargs)
            return {
                "content": response.content[0].text,
                "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
                "model": response.model,
                "provider": "claude",
                "finish_reason": response.stop_reason,
            }
        except Exception as e:
            logger.error(f"Claude error: {e}")
            raise

    async def analyze_document(self, content: str, task: str) -> str:
        """Analyze a document with a given task."""
        messages = [{"role": "user", "content": f"Task: {task}\n\nDocument:\n{content}"}]
        result = await self.chat(messages)
        return result["content"]
