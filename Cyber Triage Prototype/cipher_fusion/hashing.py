import hashlib
from typing import Union, BinaryIO

def calculate_sha256_bytes(data: bytes) -> str:
    """Calculate SHA-256 hash of a byte string."""
    return hashlib.sha256(data).hexdigest()

def calculate_sha256_file(file_obj: Union[str, BinaryIO]) -> str:
    """Calculate SHA-256 hash of a file path or file-like object."""
    hasher = hashlib.sha256()
    if isinstance(file_obj, str):
        with open(file_obj, 'rb') as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
    else:
        # Save position if seekable
        pos = file_obj.tell() if hasattr(file_obj, 'tell') and file_obj.seekable() else None
        while chunk := file_obj.read(8192):
            hasher.update(chunk)
        if pos is not None:
            file_obj.seek(pos)
    return hasher.hexdigest()

def generate_entity_hash(normalized_value: str) -> str:
    """Generate deterministic SHA-256 hash for an entity's normalized value."""
    if not normalized_value:
        return ""
    clean_val = normalized_value.strip().lower()
    return hashlib.sha256(clean_val.encode('utf-8')).hexdigest()
