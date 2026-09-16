import os
import uuid
from typing import List, Tuple
from datetime import datetime, timezone
from cipher_fusion.models import ArtifactModel, ArtifactType, NormalizedEventModel
from cipher_fusion.hashing import calculate_sha256_bytes

class BaseIngester:
    def __init__(self, case_id: str):
        self.case_id = case_id

    def create_artifact_record(self, filename: str, file_bytes: bytes, file_type: ArtifactType) -> ArtifactModel:
        artifact_id = f"ART-{uuid.uuid4().hex[:8].upper()}"
        sha256_hash = calculate_sha256_bytes(file_bytes)
        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        return ArtifactModel(
            artifact_id=artifact_id,
            case_id=self.case_id,
            filename=os.path.basename(filename),
            file_type=file_type,
            file_size=len(file_bytes),
            sha256=sha256_hash,
            upload_timestamp=now_utc,
            processing_status="PROCESSED"
        )
