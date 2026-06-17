"""
Sentiment analysis service.
Supports Hebrew and English text.
"""
import logging
from typing import Optional
from app.services.ai.openai_service import OpenAIService

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """
    Sentiment analysis using GPT-4 for Hebrew/English support.
    """

    def __init__(self):
        self.ai = OpenAIService()

    async def analyze(self, text: str) -> dict:
        """
        Analyze sentiment of text.

        Returns:
            {
                'sentiment': 'positive' | 'negative' | 'neutral',
                'score': float 0-1,
                'confidence': float 0-1,
                'emotions': list of detected emotions
            }
        """
        system_prompt = """You are a sentiment analysis expert for Hebrew and English text.
Analyze the sentiment and return a JSON object with:
- sentiment: "positive", "negative", or "neutral"
- score: number 0-1 (1 = most positive)
- confidence: number 0-1
- emotions: array of detected emotions from ["joy", "anger", "sadness", "fear", "surprise", "disgust", "trust", "anticipation"]
Return ONLY valid JSON."""

        messages = [{"role": "user", "content": text}]
        try:
            result = await self.ai.chat(messages, system_prompt=system_prompt, temperature=0.1)
            import json
            data = json.loads(result["content"])
            return {
                "sentiment": data.get("sentiment", "neutral"),
                "score": float(data.get("score", 0.5)),
                "confidence": float(data.get("confidence", 0.5)),
                "emotions": data.get("emotions", []),
            }
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            return {
                "sentiment": "neutral",
                "score": 0.5,
                "confidence": 0.0,
                "emotions": [],
            }

    def score_to_label(self, score: float) -> str:
        """Convert numeric score to label."""
        if score >= 0.7:
            return "positive"
        elif score <= 0.3:
            return "negative"
        return "neutral"
