from datetime import datetime, timezone
import re

DATE_FORMATS = [
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%Y/%m/%d %H:%M:%S",
    "%d-%m-%Y %H:%M:%S",
    "%d/%m/%Y %H:%M:%S",
    "%Y-%m-%d",
    "%a, %d %b %Y %H:%M:%S %z",
    "%d %b %Y %H:%M:%S",
]

def normalize_timestamp(raw_time: str) -> str:
    """Converts a raw date/time string into a normalized UTC ISO 8601 string."""
    if not raw_time:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    clean_str = str(raw_time).strip()
    
    # Try parsing common formats
    for fmt in DATE_FORMATS:
        try:
            dt = datetime.strptime(clean_str, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            continue
            
    # Fallback to current time if unparseable
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
