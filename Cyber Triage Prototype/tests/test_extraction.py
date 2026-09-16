import pytest
from cipher_fusion.extraction import EntityExtractor
from cipher_fusion.models import EntityType

def test_entity_extractor_text():
    text = """
    Victim was contacted on +919876500001 and instructed to send INR 42000 to fraud-demo@upi.
    The victim downloaded app from suspicious-demo.test hosted at 198.51.100.10.
    Account debited: ACC-100200300. Complaint registered: CMP-2026-8801.
    """
    entities = EntityExtractor.extract_from_text(text)
    types = [e["type"] for e in entities]
    values = [e["value"] for e in entities]

    assert EntityType.PHONE_NUMBER in types
    assert "+919876500001" in values
    assert EntityType.UPI_ID in types
    assert "fraud-demo@upi" in values
    assert EntityType.IP_ADDRESS in types
    assert "198.51.100.10" in values
    assert EntityType.DOMAIN in types
    assert "suspicious-demo.test" in values
    assert EntityType.COMPLAINT_ID in types
