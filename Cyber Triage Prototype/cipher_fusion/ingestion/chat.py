import json
import uuid
from typing import List, Tuple
from datetime import datetime, timezone
from cipher_fusion.models import ArtifactModel, ArtifactType, NormalizedEventModel, EntityType
from cipher_fusion.ingestion.base import BaseIngester
from cipher_fusion.normalization import normalize_phone_number, normalize_timestamp
from cipher_fusion.security import mask_phone_number
from cipher_fusion.hashing import generate_entity_hash
from cipher_fusion.extraction import EntityExtractor

class ChatIngester(BaseIngester):
    def parse(self, filename: str, file_bytes: bytes) -> Tuple[ArtifactModel, List[NormalizedEventModel]]:
        artifact = self.create_artifact_record(filename, file_bytes, ArtifactType.CHAT)
        events = []
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        records = []
        if filename.endswith('.json'):
            raw_data = json.loads(file_bytes.decode('utf-8'))
            records = raw_data if isinstance(raw_data, list) else [raw_data]
        else:
            lines = file_bytes.decode('utf-8', errors='ignore').splitlines()
            for idx, line in enumerate(lines):
                if line.strip():
                    records.append({
                        "message_id": f"msg_{idx+1}",
                        "timestamp": now_str,
                        "sender": "UNKNOWN",
                        "message_text": line.strip()
                    })

        for rec in records:
            msg_id = str(rec.get('message_id', f"msg_{uuid.uuid4().hex[:4]}"))
            orig_time = str(rec.get('timestamp', ''))
            utc_time = normalize_timestamp(orig_time)
            sender = str(rec.get('sender', '')).strip()
            text = str(rec.get('message_text', '')).strip()

            norm_sender = normalize_phone_number(sender)

            if norm_sender:
                events.append(NormalizedEventModel(
                    event_id=f"EVT-{uuid.uuid4().hex[:8].upper()}",
                    case_id=self.case_id,
                    source_artifact_id=artifact.artifact_id,
                    source_record_reference=msg_id,
                    source_type="CHAT",
                    timestamp_original=orig_time,
                    timestamp_utc=utc_time,
                    entity_type=EntityType.PHONE_NUMBER,
                    entity_value_masked=mask_phone_number(norm_sender),
                    entity_value_hash=generate_entity_hash(norm_sender),
                    related_entity_type=None,
                    related_entity_value_masked=None,
                    action="CHAT_SENT",
                    amount=0.0,
                    location=msg_id,
                    confidence=1.0,
                    extraction_method="CHAT_PARSER",
                    created_at=now_str
                ))

            # Extract entities from chat text body
            extracted = EntityExtractor.extract_from_text(text)
            for item in extracted:
                events.append(NormalizedEventModel(
                    event_id=f"EVT-{uuid.uuid4().hex[:8].upper()}",
                    case_id=self.case_id,
                    source_artifact_id=artifact.artifact_id,
                    source_record_reference=msg_id,
                    source_type="CHAT",
                    timestamp_original=orig_time,
                    timestamp_utc=utc_time,
                    entity_type=item["type"],
                    entity_value_masked=item["value"],
                    entity_value_hash=generate_entity_hash(item["value"]),
                    related_entity_type=EntityType.PHONE_NUMBER if norm_sender else None,
                    related_entity_value_masked=mask_phone_number(norm_sender) if norm_sender else None,
                    action="CHAT_MENTION",
                    amount=0.0,
                    location=msg_id,
                    confidence=0.9,
                    extraction_method="REGEX_EXTRACTOR",
                    created_at=now_str
                ))

        return artifact, events
