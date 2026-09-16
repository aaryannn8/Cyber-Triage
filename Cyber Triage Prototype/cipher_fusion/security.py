import re
from typing import Optional

def mask_phone_number(phone: str) -> str:
    """Mask phone number keeping country code and last 4 digits visible."""
    if not phone:
        return ""
    clean = re.sub(r'[\s\-]', '', phone)
    if len(clean) >= 10:
        prefix = clean[:-4]
        suffix = clean[-4:]
        if len(prefix) > 4:
            masked_prefix = prefix[:3] + "*" * (len(prefix) - 3)
        else:
            masked_prefix = "*" * len(prefix)
        return f"{masked_prefix}{suffix}"
    return "****"

def mask_account_number(account: str) -> str:
    """Mask account number keeping only last 4 digits visible."""
    if not account:
        return ""
    clean = re.sub(r'[\s\-]', '', account)
    if len(clean) > 4:
        return f"ACC-****{clean[-4:]}"
    return "ACC-****"

def mask_upi_id(upi: str) -> str:
    """Mask UPI handle e.g. user@upi -> us**@upi."""
    if not upi or "@" not in upi:
        return "upi@****"
    parts = upi.split("@", 1)
    username, handle = parts[0], parts[1]
    if len(username) <= 2:
        masked_user = username[0] + "*" if username else "*"
    else:
        masked_user = username[:2] + "*" * (len(username) - 2)
    return f"{masked_user}@{handle}"

def mask_email(email: str) -> str:
    """Mask email address e.g. victim@example.test -> vi****@example.test."""
    if not email or "@" not in email:
        return "****@****"
    user, domain = email.split("@", 1)
    if len(user) <= 2:
        masked_user = user[0] + "*"
    else:
        masked_user = user[:2] + "*" * (len(user) - 2)
    return f"{masked_user}@{domain}"

def mask_ip_address(ip: str) -> str:
    """Mask IPv4 address e.g. 198.51.100.10 -> 198.51.***.***."""
    if not ip:
        return ""
    parts = ip.split(".")
    if len(parts) == 4:
        return f"{parts[0]}.{parts[1]}.***.***"
    return "***.***.***.***"

def mask_imei(imei: str) -> str:
    """Mask IMEI/IMSI keeping first 6 TAC and last 1 check digit visible."""
    clean = re.sub(r'[\s\-]', '', str(imei))
    if len(clean) >= 15:
        return f"{clean[:6]}********{clean[-1]}"
    elif len(clean) > 4:
        return f"{clean[:3]}****{clean[-1]}"
    return "****"

def mask_identifier(entity_type: str, raw_value: str) -> str:
    """Generic masking dispatcher based on entity type."""
    if not raw_value:
        return ""
    val = str(raw_value).strip()
    etype = str(entity_type).lower()
    
    if "phone" in etype:
        return mask_phone_number(val)
    elif "account" in etype:
        return mask_account_number(val)
    elif "upi" in etype:
        return mask_upi_id(val)
    elif "email" in etype:
        return mask_email(val)
    elif "ip_address" in etype:
        return mask_ip_address(val)
    elif "imei" in etype or "imsi" in etype:
        return mask_imei(val)
    elif "device" in etype:
        return f"DEV-****{val[-4:]}" if len(val) >= 4 else "DEV-****"
    elif "mac" in etype:
        parts = val.split(":")
        return f"{parts[0]}:{parts[1]}:**:**:**:{parts[-1]}" if len(parts) == 6 else "**:**:**:**:**:**"
    elif "cert" in etype or "sha256" in etype:
        return f"{val[:6]}...{val[-6:]}" if len(val) >= 12 else val
    return val
