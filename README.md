# 🤖 Idobetz AI Bot - מערכת בוט AI מרובת פלטפורמות

<div dir="rtl">

מערכת בוט AI מלאה עם תמיכה ב-WhatsApp, Messenger, Instagram, ועם אינטגרציה לאתר idobetz.co.il.

</div>

## 🏗️ ארכיטקטורה

```
idobetz-whatsapp-ai/
├── backend/                    # FastAPI Python Backend
│   ├── app/
│   │   ├── main.py             # FastAPI app entry point
│   │   ├── config.py           # Settings (Pydantic)
│   │   ├── database.py         # SQLAlchemy async
│   │   ├── redis_client.py     # Redis caching
│   │   ├── models/             # Database models
│   │   │   ├── user.py         # User, UserProfile, LoyaltyTransaction
│   │   │   ├── conversation.py # Conversation, Message
│   │   │   ├── order.py        # Order, OrderItem
│   │   │   ├── product.py      # Product, ProductCategory (from API only)
│   │   │   ├── campaign.py     # Campaign, Template
│   │   │   └── analytics.py    # AnalyticsEvent, ABTest
│   │   ├── routers/            # API endpoints
│   │   │   ├── webhooks.py     # WhatsApp/Messenger/Instagram webhooks
│   │   │   ├── admin.py        # Admin dashboard API
│   │   │   ├── campaigns.py    # Campaign management
│   │   │   ├── analytics.py    # Analytics endpoints
│   │   │   ├── products.py     # Product sync endpoints
│   │   │   ├── orders.py       # Order endpoints
│   │   │   ├── users.py        # User management + GDPR
│   │   │   └── auth.py         # JWT authentication
│   │   ├── services/
│   │   │   ├── ai/             # AI providers
│   │   │   │   ├── openai_service.py   # OpenAI GPT-4o
│   │   │   │   ├── claude_service.py   # Anthropic Claude
│   │   │   │   ├── ollama_service.py   # Local LLM (private mode)
│   │   │   │   └── router.py           # AI routing + consensus
│   │   │   ├── platforms/      # Messaging platforms
│   │   │   │   ├── whatsapp.py         # WhatsApp Business API
│   │   │   │   ├── messenger.py        # Meta Messenger
│   │   │   │   └── instagram.py        # Instagram DM
│   │   │   ├── nlp/            # Natural Language Processing
│   │   │   │   ├── sentiment.py        # Sentiment analysis (Hebrew)
│   │   │   │   ├── intent.py           # Intent detection
│   │   │   │   └── ner.py              # Named entity recognition
│   │   │   ├── website/        # Website integration
│   │   │   │   ├── product_sync.py     # Auto product sync (hourly)
│   │   │   │   ├── order_sync.py       # Real-time order sync
│   │   │   │   └── visitor_tracker.py  # Privacy-compliant tracking
│   │   │   ├── media/          # Media handling
│   │   │   │   ├── voice.py            # Whisper transcription + TTS
│   │   │   │   └── qr_code.py          # QR code generation
│   │   │   ├── personalization.py      # User personalization engine
│   │   │   ├── recommendation.py       # Smart product recommendations
│   │   │   └── campaign_service.py     # Campaign management
│   │   ├── middleware/
│   │   │   ├── rate_limiter.py  # Redis-based rate limiting
│   │   │   └── auth.py          # JWT auth middleware
│   │   └── utils/
│   │       ├── hebrew.py        # Hebrew/RTL utilities
│   │       └── audit_log.py     # GDPR-compliant audit logs
│   ├── migrations/              # Alembic database migrations
│   ├── tests/                   # Pytest tests
│   ├── requirements.txt
│   ├── Dockerfile
│   └── alembic.ini
├── frontend/
│   ├── admin-dashboard/         # React Admin Dashboard (Vite + Tailwind)
│   │   └── src/
│   │       ├── App.jsx          # Main app + routing
│   │       ├── pages/
│   │       │   ├── Dashboard.jsx    # Overview stats + charts
│   │       │   ├── Conversations.jsx # Live conversation viewer
│   │       │   ├── Campaigns.jsx    # Campaign management
│   │       │   ├── Analytics.jsx    # Analytics + charts
│   │       │   ├── Products.jsx     # Product catalog
│   │       │   ├── Users.jsx        # User management
│   │       │   └── Login.jsx        # Admin login
│   │       └── components/
│   │           └── Sidebar.jsx  # Navigation sidebar (RTL)
│   └── chat-widget/             # Embeddable website chat widget
│       └── src/
│           └── ChatWidget.jsx   # Self-contained React widget
├── docker-compose.yml           # Development setup
├── docker-compose.prod.yml      # Production setup
├── .env.example                 # Environment variables template
└── README.md
```

## ✨ Features

- **OpenAI GPT-4o + Claude 3.5 Sonnet** - Dual AI with automatic fallback
- **Consensus Mode** - Multiple AIs vote for best response
- **WhatsApp, Messenger, Instagram** - Full webhook handling
- **Website Integration** - Auto product & order sync from API
- **Order Tracking** - "אני רואה את ההזמנה שלך לתל אביב, רחוב הרצל 5..."
- **Hebrew RTL** - Full Hebrew support throughout
- **Voice Transcription** - Whisper API for voice messages
- **Personalization** - VIP tiers, birthday offers, churn prediction
- **Campaign Management** - Broadcast, scheduled, abandoned cart, birthday
- **Admin Dashboard** - React RTL dashboard with analytics
- **Chat Widget** - Embeddable website widget
- **GDPR Compliance** - Audit logs, data deletion
- **Rate Limiting** - Redis-based protection
- **Docker** - Full containerized setup

> **📝 Note:** No product names or specific product data is hardcoded.
> All product data comes exclusively from the website API integration.

## 🚀 Quick Start

### 1. Clone & Setup

```bash
git clone https://github.com/idoido1238-max/idobetz-whatsapp-ai
cd idobetz-whatsapp-ai
cp .env.example .env
# Edit .env with your API keys
```

### 2. Docker (Recommended)

```bash
docker-compose up -d
```

Services:
- Backend API: http://localhost:8000
- Admin Dashboard: http://localhost:3000
- API Docs: http://localhost:8000/api/docs

### 3. Manual Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

## 📱 Webhook Configuration

### WhatsApp Business API
Set webhook URL: `https://your-domain.com/api/v1/webhooks/whatsapp`
Verify token: value from `WHATSAPP_WEBHOOK_VERIFY_TOKEN`

### Meta Messenger
Set webhook URL: `https://your-domain.com/api/v1/webhooks/messenger`
Verify token: value from `MESSENGER_WEBHOOK_VERIFY_TOKEN`

### Instagram
Set webhook URL: `https://your-domain.com/api/v1/webhooks/instagram`
Verify token: value from `INSTAGRAM_WEBHOOK_VERIFY_TOKEN`

## 🌐 Website Integration

Connect your website API to enable automatic product & order sync:

```env
WEBSITE_API_URL=https://idobetz.co.il/wp-json/wc/v3
WEBSITE_API_KEY=ck_your_woocommerce_api_key
PRODUCT_SYNC_INTERVAL_MINUTES=60
ORDER_SYNC_INTERVAL_MINUTES=5
```

Products sync **automatically every hour**. No hardcoded product data - everything comes from the API.

## 🧠 AI Configuration

```env
# Dual AI routing
AI_PROVIDER=openai        # Primary: openai | claude | ollama | consensus
AI_FALLBACK_PROVIDER=claude  # Fallback on failure

# Consensus mode: queries multiple AIs and picks best response
AI_PROVIDER=consensus
```

## 📊 Admin Dashboard

Access at http://localhost:3000 with credentials from `.env`:

| Page | Description |
|------|-------------|
| Dashboard | Overview: users, conversations, sentiment, intents |
| Conversations | Live conversation viewer with chat history |
| Campaigns | Create/activate/pause/schedule campaigns |
| Analytics | Charts: messages/day, user growth, response times |
| Products | View synced products from website API |
| Users | User management with tier system |
| Settings | System status and feature flags |

## 📦 Embed Chat Widget

Add to your website HTML:

```html
<script>
  window.IDOBETZ_API_URL = 'https://your-api-domain.com';
</script>
<div id="idobetz-chat"></div>
<script type="module">
  import { default as ChatWidget } from './chat-widget.js';
  import React from 'react';
  import ReactDOM from 'react-dom/client';
  ReactDOM.createRoot(document.getElementById('idobetz-chat')).render(
    React.createElement(ChatWidget, {
      botName: 'Idobetz AI',
      welcomeMessage: 'שלום! 👋 איך אוכל לעזור?',
      collectEmail: true,
    })
  );
</script>
```

## 🎯 Campaign Types

| Type | Hebrew | Trigger |
|------|--------|---------|
| `broadcast` | שידור | Manual activation |
| `scheduled` | מתוזמן | Scheduled time |
| `abandoned_cart` | עגלה נטושה | Cart abandonment |
| `birthday` | יום הולדת | User birthday |
| `reengagement` | החזרת לקוחות | Inactivity |
| `loyalty_reward` | פרס נאמנות | Points milestone |
| `reorder_reminder` | תזכורת הזמנה | Time since last order |

## 🔐 Security

- JWT authentication for admin API
- Rate limiting (Redis-based)
- Webhook signature verification
- GDPR-compliant user deletion (anonymization)
- Audit logging for all data access
- No secrets in code - all via environment variables

## 🌐 Hebrew RTL Support

- All Hebrew text uses proper RTL direction markers
- English words within Hebrew text handled correctly
- WhatsApp message formatting with RTL
- Admin dashboard is full RTL with Hebrew UI

## 📈 Loyalty Tiers

| Tier | Benefits |
|------|----------|
| Standard | Basic service |
| Silver 🥈 | Priority support |
| Gold ⭐ | Special offers |
| Platinum 💎 | VIP treatment |
| VIP 👑 | Premium service + personal greeting |

## 🧪 Running Tests

```bash
cd backend
pip install pytest pytest-asyncio qrcode Pillow
pytest tests/ -v
```

## 📋 Environment Variables

See [`.env.example`](.env.example) for all configuration options with descriptions.

## 🚢 Production Deployment

```bash
# Build and deploy with production config
docker-compose -f docker-compose.prod.yml up -d

# Run database migrations
docker-compose exec backend alembic upgrade head
```

---

**Built with ❤️ for idobetz.co.il**
