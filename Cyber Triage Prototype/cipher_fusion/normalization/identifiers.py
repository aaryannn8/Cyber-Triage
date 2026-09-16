import re

def normalize_email(email: str) -> str:
    """Lowercases and trims email address."""
    if not email:
        return ""
    clean = str(email).strip().lower()
    match = re.search(r'[\w\.\+\-]+@[\w\.\-]+\.\w+', clean)
    return match.group(0) if match else clean

def normalize_upi(upi: str) -> str:
    """Lowercases and trims UPI VPA handle (e.g., fraud-demo@upi)."""
    if not upi:
        return ""
    clean = str(upi).strip().lower()
    return clean

def normalize_domain(domain_or_url: str) -> str:
    """Strips protocol/path and lowercases domain name."""
    if not domain_or_url:
        return ""
    clean = str(domain_or_url).strip().lower()
    clean = re.sub(r'^https?://', '', clean)
    clean = clean.split('/')[0].split(':')[0]
    return clean

def normalize_imei(imei: str) -> str:
    """Removes whitespace and hyphens from IMEI/IMSI numbers."""
    if not imei:
        return ""
    return re.sub(r'[\s\-]', '', str(imei).strip())
