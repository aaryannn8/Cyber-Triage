import json
import uuid
from typing import List, Tuple
from datetime import datetime, timezone
from cipher_fusion.models import ArtifactModel, ArtifactType, NormalizedEventModel, EntityType
from cipher_fusion.ingestion.base import BaseIngester
from cipher_fusion.normalization import normalize_timestamp
from cipher_fusion.hashing import generate_entity_hash
from cipher_fusion.extraction import EntityExtractor

class ComplaintIngester(BaseIngester):
    def parse(self, filename: str, file_bytes: bytes) -> Tuple[ArtifactModel, List[NormalizedEventModel]]:
        artifact = self.create_artifact_record(filename, file_bytes, ArtifactType.COMPLAINT)
        events = []
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        if filename.endswith('.json'):
            comp_data = json.loads(file_bytes.decode('utf-8'))
        else:
            text_content = file_bytes.decode('utf-8', errors='ignore')
            comp_data = {
                "complaint_id": f"CMP-{uuid.uuid4().hex[:6].upper()}",
                "case_id": self.case_id,
                "timestamp": now_str,
                "complaint_text": text_content,
                "reported_amount": 0.0,
                "location": "UNKNOWN"
            }

        complaint_id = str(comp_data.get('complaint_id', f"CMP-{uuid.uuid4().hex[:6].upper()}")).strip()
        orig_time = str(comp_data.get('timestamp', ''))
        utc_time = normalize_timestamp(orig_time)
        text = str(comp_data.get('complaint_text', ''))
        amount = float(comp_data.get('reported_amount', 0.0))
        location = str(comp_data.get('location', ''))

        # Add primary complaint entity event
        events.append(NormalizedEventModel(
            event_id=f"EVT-{uuid.uuid4().hex[:8].upper()}",
            case_id=self.case_id,
            source_artifact_id=artifact.artifact_id,
            source_record_reference="complaint_header",
            source_type="COMPLAINT",
            timestamp_original=orig_time,
            timestamp_utc=utc_time,
            entity_type=EntityType.COMPLAINT_ID,
            entity_value_masked=complaint_id,
            entity_value_hash=generate_entity_hash(complaint_id),
            related_entity_type=None,
            related_entity_value_masked=None,
            action="COMPLAINT_FILED",
            amount=amount,
            location=location,
            confidence=1.0,
            extraction_method="COMPLAINT_PARSER",
            created_at=now_str
        ))

        # Extract nested entities mentioned in narrative
        extracted = EntityExtractor.extract_from_text(text)
        for item in extracted:
            events.append(NormalizedEventModel(
                event_id=f"EVT-{uuid.uuid4().hex[:8].upper()}",
                case_id=self.case_id,
                source_artifact_id=artifact.artifact_id,
                source_record_reference="complaint_narrative",
                source_type="COMPLAINT",
                timestamp_original=orig_time,
                timestamp_utc=utc_time,
                entity_type=item["type"],
                entity_value_masked=item["value"],
                entity_value_hash=generate_entity_hash(item["value"]),
                related_entity_type=EntityType.COMPLAINT_ID,
                related_entity_value_masked=complaint_id,
                action="NARRATIVE_MENTION",
                amount=amount,
                location=location,
                confidence=0.85,
                extraction_method="REGEX_EXTRACTOR",
                created_at=now_str
            ))

        return artifact, events
