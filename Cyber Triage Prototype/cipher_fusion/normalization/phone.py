import re

def normalize_phone_number(raw_phone: str) -> str:
    """
    Normalizes Indian and international phone numbers into standard E.164-like format (+91XXXXXXXXXX).
    """
    if not raw_phone:
        return ""
    
    clean = re.sub(r'[^\d+]', '', str(raw_phone).strip())
    if not clean:
        return ""

    if clean.startswith("+"):
        digits = clean[1:]
        if digits.startswith("91") and len(digits) == 12:
            return f"+{digits}"
        return f"+{digits}"
    
    # Check digits only
    if clean.startswith("0") and len(clean) == 11:
        clean = clean[1:]
    
    if clean.startswith("91") and len(clean) == 12:
        return f"+{clean}"
    
    if len(clean) == 10 and clean[0] in "6789":
        return f"+91{clean}"
    
    return f"+{clean}"
