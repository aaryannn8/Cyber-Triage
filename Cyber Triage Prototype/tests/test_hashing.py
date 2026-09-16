import io
import pytest
from cipher_fusion.hashing import calculate_sha256_bytes, calculate_sha256_file, generate_entity_hash

def test_calculate_sha256_bytes():
    data = b"CIPHER-FUSION-TEST-DATA"
    hash_str = calculate_sha256_bytes(data)
    assert len(hash_str) == 64
    assert hash_str == calculate_sha256_bytes(data)

def test_calculate_sha256_file():
    data = b"SAMPLE-FILE-CONTENT-12345"
    f = io.BytesIO(data)
    hash_str = calculate_sha256_file(f)
    assert len(hash_str) == 64
    assert hash_str == calculate_sha256_bytes(data)

def test_generate_entity_hash():
    h1 = generate_entity_hash("+919876500001")
    h2 = generate_entity_hash(" +919876500001 ")
    h3 = generate_entity_hash("USER@UPI")
    h4 = generate_entity_hash("user@upi")
    assert h1 == h2
    assert h3 == h4
    assert len(h1) == 64
