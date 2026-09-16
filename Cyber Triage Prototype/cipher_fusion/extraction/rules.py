import re
from typing import List, Dict, Any
from cipher_fusion.models import EntityType
from cipher_fusion.normalization import (
    normalize_phone_number, normalize_ip_address, get_ip_subnet,
    normalize_email, normalize_upi, normalize_domain, normalize_imei
)

class EntityExtractor:
    @staticmethod
    def extract_from_text(text: str) -> List[Dict[str, Any]]:
        """Extracts structured entities from free text narratives or chat messages."""
        results = []
        if not text:
            return results

        # 1. Phone numbers (10 to 12 digits, optional +91 or 0)
        phone_matches = re.findall(r'\b(?:\+?91[\-\s]?)?[6-9]\d{9}\b', text)
        for p in set(phone_matches):
            norm = normalize_phone_number(p)
            if norm:
                results.append({"type": EntityType.PHONE_NUMBER, "value": norm, "raw": p})

        # 2. UPI Handles
        upi_matches = re.findall(r'\b[a-zA-Z0-9\.\-_]+@[a-zA-Z]{2,10}\b', text)
        for u in set(upi_matches):
            if not u.endswith((".com", ".test", ".org", ".net", ".in")):
                norm = normalize_upi(u)
                results.append({"type": EntityType.UPI_ID, "value": norm, "raw": u})
            else:
                norm = normalize_email(u)
                results.append({"type": EntityType.EMAIL_ADDRESS, "value": norm, "raw": u})

        # 3. IP Addresses
        ip_matches = re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', text)
        for ip in set(ip_matches):
            norm = normalize_ip_address(ip)
            if norm:
                results.append({"type": EntityType.IP_ADDRESS, "value": norm, "raw": ip})
                subnet = get_ip_subnet(norm)
                if subnet:
                    results.append({"type": EntityType.IP_SUBNET, "value": subnet, "raw": ip})

        # 4. Domains / URLs
        url_matches = re.findall(r'https?://[^\s/$.?#].[^\s]*|\b[a-zA-Z0-9\.\-]+\.[a-zA-Z]{2,6}\b', text)
        for url in set(url_matches):
            if "@" not in url:
                norm_d = normalize_domain(url)
                if norm_d and len(norm_d.split(".")) >= 2:
                    results.append({"type": EntityType.DOMAIN, "value": norm_d, "raw": url})

        # 5. Bank Account Numbers (8 to 18 digits with prefix or context)
        acc_matches = re.findall(r'\b(?:ACC|A/C|ACCT|ACCOUNT)?[\s\-\:]*([0-9]{9,18})\b', text, re.IGNORECASE)
        for acc in set(acc_matches):
            results.append({"type": EntityType.ACCOUNT_NUMBER, "value": acc, "raw": acc})

        # 6. Complaint IDs
        comp_matches = re.findall(r'\b(?:CASE|CMP|COMP|NCRP)[\-\s]*[0-9A-Z]{4,12}\b', text, re.IGNORECASE)
        for c in set(comp_matches):
            results.append({"type": EntityType.COMPLAINT_ID, "value": c.upper(), "raw": c})

        return results
