import pytest
from cipher_fusion.normalization import (
    normalize_phone_number, normalize_ip_address, get_ip_subnet,
    normalize_timestamp, normalize_email, normalize_upi, normalize_domain, normalize_imei
)

def test_phone_normalization():
    assert normalize_phone_number("9876543210") == "+919876543210"
    assert normalize_phone_number("09876543210") == "+919876543210"
    assert normalize_phone_number("+91 98765-43210") == "+919876543210"
    assert normalize_phone_number("919876543210") == "+919876543210"

def test_ip_and_subnet_normalization():
    assert normalize_ip_address(" 198.51.100.10 ") == "198.51.100.10"
    assert get_ip_subnet("198.51.100.10") == "198.51.100.0/24"
    assert normalize_ip_address("999.999.999.999") == ""

def test_timestamp_normalization():
    ts = normalize_timestamp("2026-09-15 10:15:00")
    assert ts.startswith("2026-09-15T10:15:00")
    assert ts.endswith("Z")

def test_identifier_normalization():
    assert normalize_email(" User@Example.Test ") == "user@example.test"
    assert normalize_upi(" Fraud-Demo@UPI ") == "fraud-demo@upi"
    assert normalize_domain("https://suspicious-demo.test/phish") == "suspicious-demo.test"
    assert normalize_imei(" 864201 - 04 - 123456 - 9 ") == "864201041234569"
