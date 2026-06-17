"""
Smart recommendation engine.
Recommends products based on conversation context, user history, and available inventory.
All recommendations use data from website API only - no hardcoded products.
"""
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy import select, func

from app.database import AsyncSessionLocal
from app.models.product import Product, ProductCategory
from app.services.ai.openai_service import OpenAIService
from app.redis_client import product_cache

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    Generates smart product recommendations from live website data.
    Uses AI to match products to conversation context.
    """

    def __init__(self):
        self.ai = OpenAIService()

    async def get_recommendations(
        self,
        user_context: Dict[str, Any],
        conversation_context: str,
        limit: int = 3,
    ) -> List[Dict]:
        """
        Get personalized product recommendations.

        Args:
            user_context: User profile and history
            conversation_context: Recent conversation text
            limit: Number of recommendations

        Returns:
            List of product dicts from live database
        """
        # Get available products from DB
        available_products = await self._get_available_products(limit=50)
        if not available_products:
            return []

        # Use AI to rank products by relevance
        ranked = await self._rank_products_with_ai(
            available_products, conversation_context, user_context, limit
        )
        return ranked

    async def get_similar_products(self, product_id: str, limit: int = 3) -> List[Dict]:
        """Get similar products to a given product."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Product).where(Product.id == product_id)
            )
            product = result.scalar_one_or_none()
            if not product:
                return []

            # Get products in same category
            query = (
                select(Product)
                .where(
                    Product.category_id == product.category_id,
                    Product.id != product.id,
                    Product.is_active == True,
                    Product.in_stock == True,
                )
                .limit(limit)
            )
            result = await session.execute(query)
            similar = list(result.scalars().all())

        return [self._format_product(p) for p in similar]

    async def get_trending_products(self, limit: int = 5) -> List[Dict]:
        """Get trending/featured products."""
        cache_key = f"trending:{limit}"
        cached = await product_cache.get(cache_key)
        if cached:
            return cached

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Product)
                .where(Product.is_active == True, Product.in_stock == True, Product.is_featured == True)
                .limit(limit)
            )
            products = list(result.scalars().all())

        formatted = [self._format_product(p) for p in products]
        await product_cache.set(cache_key, formatted, ttl=300)
        return formatted

    async def get_on_sale_products(self, limit: int = 5) -> List[Dict]:
        """Get products currently on sale."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Product)
                .where(
                    Product.is_active == True,
                    Product.in_stock == True,
                    Product.sale_price.isnot(None),
                )
                .limit(limit)
            )
            products = list(result.scalars().all())

        return [self._format_product(p) for p in products]

    async def _get_available_products(self, category: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """Get available products from database."""
        async with AsyncSessionLocal() as session:
            query = (
                select(Product)
                .where(Product.is_active == True, Product.in_stock == True)
            )
            if category:
                query = query.join(ProductCategory).where(
                    ProductCategory.name.ilike(f"%{category}%")
                )
            query = query.limit(limit)
            result = await session.execute(query)
            products = list(result.scalars().all())

        return [self._format_product(p) for p in products]

    async def _rank_products_with_ai(
        self,
        products: List[Dict],
        conversation: str,
        user_context: Dict,
        limit: int,
    ) -> List[Dict]:
        """Use AI to rank products by relevance to conversation."""
        if not products:
            return []

        # Build product list for AI (names + tags only)
        product_summary = "\n".join([
            f"{i+1}. {p['name']} - ₪{p['price']} - {', '.join(p.get('tags', []))}"
            for i, p in enumerate(products[:20])
        ])

        preferred = user_context.get("preferred_categories", [])
        user_info = f"הלקוח מעוניין ב: {', '.join(preferred)}" if preferred else ""

        prompt = f"""בהתבסס על השיחה הבאה, דרג את המוצרים הכי רלוונטיים (החזר רק מספרים מ-1 עד {len(products[:20])}, מופרדים בפסיקים, מהכי רלוונטי לפחות):

שיחה: {conversation[:500]}
{user_info}

מוצרים:
{product_summary}

החזר רק {limit} מספרים מופרדים בפסיקים:"""

        messages = [{"role": "user", "content": prompt}]
        try:
            result = await self.ai.chat(messages, temperature=0.3)
            indices_str = result["content"].strip()
            indices = [int(x.strip()) - 1 for x in indices_str.split(",") if x.strip().isdigit()]
            indices = [i for i in indices if 0 <= i < len(products)][:limit]
            return [products[i] for i in indices]
        except Exception as e:
            logger.error(f"AI ranking error: {e}")
            return products[:limit]

    def _format_product(self, product: Product) -> Dict:
        """Format product for response."""
        return {
            "id": str(product.id),
            "external_id": product.external_id,
            "name": product.name,
            "name_he": product.name_he,
            "price": product.effective_price,
            "original_price": product.price,
            "is_on_sale": product.is_on_sale,
            "currency": product.currency,
            "in_stock": product.in_stock,
            "thumbnail": product.thumbnail_url,
            "url": product.url,
            "tags": product.tags or [],
            "sku": product.sku,
        }
