"""
Hebrew text utilities.
Handles RTL direction, mixed Hebrew/English text, and Hebrew formatting.
"""
import re


def is_hebrew(text: str) -> bool:
    """Check if text contains Hebrew characters."""
    hebrew_pattern = re.compile(r'[\u0590-\u05FF]')
    return bool(hebrew_pattern.search(text))


def wrap_rtl(text: str) -> str:
    """
    Wrap Hebrew text with RTL direction markers.
    English words within Hebrew text are wrapped in LTR spans.
    """
    if not is_hebrew(text):
        return text
    return f'\u202B{text}\u202C'


def format_hebrew_message(text: str) -> str:
    """
    Format a Hebrew message for WhatsApp/Messenger.
    Adds proper RTL markers and handles English words.
    """
    if not is_hebrew(text):
        return text

    # Add RTL mark at start for Hebrew text
    rtl_mark = '\u200F'
    return f"{rtl_mark}{text}"


def format_currency_hebrew(amount: float, currency: str = "ILS") -> str:
    """Format currency amount in Hebrew style."""
    symbol_map = {
        "ILS": "₪",
        "USD": "$",
        "EUR": "€",
    }
    symbol = symbol_map.get(currency, currency)
    formatted = f"{amount:,.2f}"
    if currency == "ILS":
        return f"₪{formatted}"
    return f"{formatted} {symbol}"


def format_order_status_hebrew(status: str) -> str:
    """Translate order status to Hebrew."""
    status_map = {
        "pending": "ממתין לאישור",
        "confirmed": "אושר",
        "processing": "בהכנה",
        "shipped": "נשלח",
        "out_for_delivery": "בדרך אליך",
        "delivered": "נמסר",
        "cancelled": "בוטל",
        "refunded": "הוחזר",
    }
    return status_map.get(status.lower(), status)


def format_date_hebrew(date) -> str:
    """Format date in Hebrew/Israeli style (DD/MM/YYYY)."""
    if hasattr(date, 'strftime'):
        return date.strftime("%d/%m/%Y")
    return str(date)


def split_hebrew_english(text: str) -> list:
    """
    Split text into Hebrew and English segments.
    Returns list of (text, is_rtl) tuples.
    """
    # Pattern to detect Hebrew words
    pattern = re.compile(r'([\u0590-\u05FF\u200F\u200E\u202A-\u202E\s]+|[^\u0590-\u05FF\u200F\u200E\u202A-\u202E]+)')
    segments = []
    for match in pattern.finditer(text):
        segment = match.group()
        if segment.strip():
            segments.append((segment, is_hebrew(segment)))
    return segments


def truncate_hebrew(text: str, max_length: int = 100) -> str:
    """Truncate text while respecting word boundaries."""
    if len(text) <= max_length:
        return text
    truncated = text[:max_length].rsplit(' ', 1)[0]
    return f"{truncated}..."
