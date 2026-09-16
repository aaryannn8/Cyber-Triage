import re

def normalize_ip_address(raw_ip: str) -> str:
    """Validates and cleans IPv4 address string."""
    if not raw_ip:
        return ""
    clean = str(raw_ip).strip()
    match = re.search(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', clean)
    if match:
        parts = match.group(0).split(".")
        if all(0 <= int(p) <= 255 for p in parts):
            return ".".join(str(int(p)) for p in parts)
    return ""

def get_ip_subnet(ip: str, prefix_len: int = 24) -> str:
    """Derives IPv4 /24 subnet string."""
    norm = normalize_ip_address(ip)
    if not norm:
        return ""
    parts = norm.split(".")
    if len(parts) == 4 and prefix_len == 24:
        return f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
    return ""
