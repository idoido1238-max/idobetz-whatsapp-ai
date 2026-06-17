"""
Application configuration using Pydantic Settings.
"""
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, field_validator


class Settings(BaseSettings):
    # App
    ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me-in-production"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    ALLOWED_HOSTS: List[str] = ["*"]

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./idobetz_dev.db"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_SESSION_TTL: int = 86400  # 24 hours

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_MAX_TOKENS: int = 2048
    OPENAI_TEMPERATURE: float = 0.7

    # Anthropic (Claude)
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"
    ANTHROPIC_MAX_TOKENS: int = 2048

    # Ollama (Local LLM)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"
    OLLAMA_ENABLED: bool = False

    # AI Routing
    AI_PROVIDER: str = "openai"  # openai | claude | ollama | consensus
    AI_FALLBACK_PROVIDER: str = "claude"
    AI_CONSENSUS_THRESHOLD: float = 0.7

    # WhatsApp Business API
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_BUSINESS_ACCOUNT_ID: str = ""
    WHATSAPP_ACCESS_TOKEN: str = ""
    WHATSAPP_WEBHOOK_VERIFY_TOKEN: str = "idobetz_verify_token"
    WHATSAPP_API_VERSION: str = "v20.0"

    # Meta Messenger
    MESSENGER_PAGE_ACCESS_TOKEN: str = ""
    MESSENGER_APP_SECRET: str = ""
    MESSENGER_WEBHOOK_VERIFY_TOKEN: str = "idobetz_messenger_verify"

    # Instagram
    INSTAGRAM_ACCESS_TOKEN: str = ""
    INSTAGRAM_APP_SECRET: str = ""
    INSTAGRAM_WEBHOOK_VERIFY_TOKEN: str = "idobetz_instagram_verify"

    # Website Integration
    WEBSITE_API_URL: str = ""
    WEBSITE_API_KEY: str = ""
    PRODUCT_SYNC_INTERVAL_MINUTES: int = 60
    ORDER_SYNC_INTERVAL_MINUTES: int = 5

    # AWS S3 (Media Storage)
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_BUCKET_NAME: str = ""
    AWS_REGION: str = "us-east-1"

    # JWT
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000

    # Sentry (optional)
    SENTRY_DSN: Optional[str] = None

    # Admin
    ADMIN_EMAIL: str = "admin@idobetz.co.il"
    ADMIN_PASSWORD: str = "change-me"

    # Loyalty
    LOYALTY_POINTS_PER_PURCHASE: int = 10
    LOYALTY_POINTS_PER_REFERRAL: int = 50

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
