"""
Product sync service - pulls product data from website API every hour.
No hardcoded product data - all data comes exclusively from the external API.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.product import Product, ProductCategory, ProductMedia
from app.redis_client import product_cache
from sqlalchemy import select, update

logger = logging.getLogger(__name__)


class ProductSyncService:
    """
    Syncs products from the website API into the local database.
    Runs automatically every PRODUCT_SYNC_INTERVAL_MINUTES minutes.
    All product data is sourced exclusively from the external API.
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.api_url = settings.WEBSITE_API_URL
        self.api_key = settings.WEBSITE_API_KEY
        self.headers = {
            "Authorization": f"******",
            "Content-Type": "application/json",
        }
        self._syncing = False

    async def start_scheduler(self):
        """Start the automatic product sync scheduler."""
        if not self.api_url:
            logger.warning("WEBSITE_API_URL not configured. Product sync disabled.")
            return

        self.scheduler.add_job(
            self.sync_all,
            "interval",
            minutes=settings.PRODUCT_SYNC_INTERVAL_MINUTES,
            id="product_sync",
            replace_existing=True,
            max_instances=1,
        )
        self.scheduler.start()
        logger.info(
            f"Product sync scheduler started (every {settings.PRODUCT_SYNC_INTERVAL_MINUTES} minutes)"
        )
        # Run initial sync
        await self.sync_all()

    async def stop_scheduler(self):
        """Stop the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()

    async def sync_all(self):
        """Full sync of all products and categories from API."""
        if self._syncing:
            logger.warning("Product sync already in progress, skipping...")
            return

        self._syncing = True
        try:
            logger.info("Starting product sync from website API...")
            await self.sync_categories()
            await self.sync_products()
            logger.info("Product sync completed successfully")
        except Exception as e:
            logger.error(f"Product sync failed: {e}", exc_info=True)
        finally:
            self._syncing = False

    async def sync_categories(self):
        """Sync product categories from API."""
        if not self.api_url:
            return
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.api_url}/categories",
                    headers=self.headers,
                )
                response.raise_for_status()
                categories = response.json()

            async with AsyncSessionLocal() as session:
                for cat_data in categories:
                    await self._upsert_category(session, cat_data)
                await session.commit()
            logger.info(f"Synced {len(categories)} categories")
        except Exception as e:
            logger.error(f"Category sync error: {e}")

    async def sync_products(self, page: int = 1, per_page: int = 100):
        """Sync products from API with pagination."""
        if not self.api_url:
            return
        total_synced = 0
        try:
            while True:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(
                        f"{self.api_url}/products",
                        headers=self.headers,
                        params={"page": page, "per_page": per_page},
                    )
                    response.raise_for_status()
                    data = response.json()

                products = data if isinstance(data, list) else data.get("products", data.get("items", []))
                if not products:
                    break

                async with AsyncSessionLocal() as session:
                    for product_data in products:
                        await self._upsert_product(session, product_data)
                    await session.commit()

                total_synced += len(products)
                logger.info(f"Synced page {page}: {len(products)} products (total: {total_synced})")

                # Check if there are more pages
                if isinstance(data, dict):
                    has_more = data.get("has_more", data.get("next_page", None) is not None)
                    if not has_more or len(products) < per_page:
                        break
                elif len(products) < per_page:
                    break

                page += 1

            # Clear product cache after sync
            await product_cache.delete("all_products")
            logger.info(f"Product sync complete: {total_synced} products synced")
        except Exception as e:
            logger.error(f"Product sync error: {e}")

    async def _upsert_category(self, session, cat_data: Dict[str, Any]):
        """Insert or update a category."""
        external_id = str(cat_data.get("id", ""))
        result = await session.execute(
            select(ProductCategory).where(ProductCategory.external_id == external_id)
        )
        category = result.scalar_one_or_none()

        if category:
            category.name = cat_data.get("name", category.name)
            category.name_he = cat_data.get("name_he", cat_data.get("name_hebrew", category.name_he))
            category.slug = cat_data.get("slug", category.slug)
            category.is_active = cat_data.get("is_active", True)
            category.synced_at = datetime.utcnow()
        else:
            category = ProductCategory(
                external_id=external_id,
                name=cat_data.get("name", ""),
                name_he=cat_data.get("name_he", cat_data.get("name_hebrew")),
                slug=cat_data.get("slug"),
                is_active=cat_data.get("is_active", True),
                synced_at=datetime.utcnow(),
            )
            session.add(category)

    async def _upsert_product(self, session, product_data: Dict[str, Any]):
        """Insert or update a product from API data."""
        external_id = str(product_data.get("id", ""))
        result = await session.execute(
            select(Product).where(Product.external_id == external_id)
        )
        product = result.scalar_one_or_none()

        product_dict = {
            "name": product_data.get("name", ""),
            "name_he": product_data.get("name_he", product_data.get("name_hebrew")),
            "description": product_data.get("description"),
            "description_he": product_data.get("description_he"),
            "sku": product_data.get("sku"),
            "price": float(product_data.get("price", 0)),
            "sale_price": float(p) if (p := product_data.get("sale_price")) else None,
            "stock_quantity": int(product_data.get("stock_quantity", product_data.get("stock", 0))),
            "in_stock": product_data.get("in_stock", True),
            "is_active": product_data.get("is_active", product_data.get("status") == "active", True),
            "is_featured": product_data.get("is_featured", False),
            "tags": product_data.get("tags", []),
            "specifications": product_data.get("specifications", product_data.get("attributes")),
            "thumbnail_url": product_data.get("thumbnail", product_data.get("image", {}).get("src") if isinstance(product_data.get("image"), dict) else product_data.get("image")),
            "url": product_data.get("url", product_data.get("permalink")),
            "weight": float(w) if (w := product_data.get("weight")) else None,
            "synced_at": datetime.utcnow(),
        }

        if product:
            for key, value in product_dict.items():
                setattr(product, key, value)
        else:
            product = Product(external_id=external_id, **product_dict)
            session.add(product)

    async def get_products_for_ai(self, category: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """
        Get product summary for AI context.
        Returns only generic product info (no hardcoded data).
        """
        cache_key = f"ai_products:{category}:{limit}"
        cached = await product_cache.get(cache_key)
        if cached:
            return cached

        async with AsyncSessionLocal() as session:
            query = select(Product).where(Product.is_active == True, Product.in_stock == True)
            if category:
                query = query.join(ProductCategory).where(
                    ProductCategory.name.ilike(f"%{category}%")
                )
            query = query.limit(limit)
            result = await session.execute(query)
            products = result.scalars().all()

        product_list = [
            {
                "id": str(p.id),
                "name": p.name,
                "name_he": p.name_he,
                "price": p.effective_price,
                "currency": p.currency,
                "in_stock": p.in_stock,
                "is_on_sale": p.is_on_sale,
                "thumbnail": p.thumbnail_url,
                "url": p.url,
                "tags": p.tags,
            }
            for p in products
        ]

        await product_cache.set(cache_key, product_list, ttl=300)
        return product_list
