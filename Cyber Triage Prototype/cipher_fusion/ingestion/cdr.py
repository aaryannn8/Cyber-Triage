import io
import uuid
import pandas as pd
from typing import List, Tuple
from datetime import datetime, timezone
from cipher_fusion.models import ArtifactModel, ArtifactType, NormalizedEventModel, EntityType
from cipher_fusion.ingestion.base import BaseIngester
from cipher_fusion.normalization import normalize_phone_number, normalize_timestamp
from cipher_fusion.security import mask_phone_number
from cipher_fusion.hashing import generate_entity_hash

class CDRIngester(BaseIngester):
    def parse(self, filename: str, file_bytes: bytes) -> Tuple[ArtifactModel, List[NormalizedEventModel]]:
        artifact = self.create_artifact_record(filename, file_bytes, ArtifactType.CDR)
        events = []

        if filename.endswith('.xlsx') or filename.endswith('.xls'):
            df = pd.read_excel(io.BytesIO(file_bytes))
        else:
            df = pd.read_csv(io.BytesIO(file_bytes))

        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        for idx, row in df.iterrows():
            caller = str(row.get('caller_number', '')).strip()
            receiver = str(row.get('receiver_number', '')).strip()
            orig_time = str(row.get('timestamp', ''))
            utc_time = normalize_timestamp(orig_time)
            call_type = str(row.get('call_type', 'CALL'))
            duration = float(row.get('duration_seconds', 0))
            cell_tower = str(row.get('cell_tower', ''))

            norm_caller = normalize_phone_number(caller)
            norm_receiver = normalize_phone_number(receiver)

            if norm_caller:
                events.append(NormalizedEventModel(
                    event_id=f"EVT-{uuid.uuid4().hex[:8].upper()}",
                    case_id=self.case_id,
                    source_artifact_id=artifact.artifact_id,
                    source_record_reference=f"row_{idx + 1}",
                    source_type="CDR",
                    timestamp_original=orig_time,
                    timestamp_utc=utc_time,
                    entity_type=EntityType.PHONE_NUMBER,
                    entity_value_masked=mask_phone_number(norm_caller),
                    entity_value_hash=generate_entity_hash(norm_caller),
                    related_entity_type=EntityType.PHONE_NUMBER if norm_receiver else None,
                    related_entity_value_masked=mask_phone_number(norm_receiver) if norm_receiver else None,
                    action=f"CDR_{call_type.upper()}",
                    amount=duration,
                    location=cell_tower,
                    confidence=1.0,
                    extraction_method="CSV_PARSER",
                    created_at=now_str
                ))

        return artifact, events
