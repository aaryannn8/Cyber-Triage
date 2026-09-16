import io
import json
import uuid
import pandas as pd
from typing import List, Tuple
from datetime import datetime, timezone
from cipher_fusion.models import ArtifactModel, ArtifactType, NormalizedEventModel, EntityType
from cipher_fusion.ingestion.base import BaseIngester
from cipher_fusion.normalization import (
    normalize_phone_number, normalize_ip_address, get_ip_subnet,
    normalize_timestamp, normalize_domain
)
from cipher_fusion.security import mask_phone_number, mask_ip_address
from cipher_fusion.hashing import generate_entity_hash

class IPDRIngester(BaseIngester):
    def parse(self, filename: str, file_bytes: bytes) -> Tuple[ArtifactModel, List[NormalizedEventModel]]:
        artifact = self.create_artifact_record(filename, file_bytes, ArtifactType.IPDR)
        events = []
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        records = []
        if filename.endswith('.json'):
            raw_data = json.loads(file_bytes.decode('utf-8'))
            records = raw_data if isinstance(raw_data, list) else [raw_data]
        else:
            df = pd.read_csv(io.BytesIO(file_bytes))
            records = df.to_dict(orient='records')

        for idx, rec in enumerate(records):
            phone = str(rec.get('phone_number', '')).strip()
            ip = str(rec.get('ip_address', '')).strip()
            orig_time = str(rec.get('timestamp', ''))
            utc_time = normalize_timestamp(orig_time)
            domain = str(rec.get('destination_domain', '')).strip()
            device_id = str(rec.get('device_id', '')).strip()
            duration = float(rec.get('session_duration', 0))

            norm_phone = normalize_phone_number(phone)
            norm_ip = normalize_ip_address(ip)
            subnet = get_ip_subnet(norm_ip)
            norm_domain = normalize_domain(domain)

            if norm_phone:
                events.append(NormalizedEventModel(
                    event_id=f"EVT-{uuid.uuid4().hex[:8].upper()}",
                    case_id=self.case_id,
                    source_artifact_id=artifact.artifact_id,
                    source_record_reference=f"record_{idx + 1}",
                    source_type="IPDR",
                    timestamp_original=orig_time,
                    timestamp_utc=utc_time,
                    entity_type=EntityType.PHONE_NUMBER,
                    entity_value_masked=mask_phone_number(norm_phone),
                    entity_value_hash=generate_entity_hash(norm_phone),
                    related_entity_type=EntityType.IP_ADDRESS if norm_ip else None,
                    related_entity_value_masked=mask_ip_address(norm_ip) if norm_ip else None,
                    action="IPDR_SESSION",
                    amount=duration,
                    location=subnet,
                    confidence=1.0,
                    extraction_method="IPDR_PARSER",
                    created_at=now_str
                ))

            if norm_ip:
                events.append(NormalizedEventModel(
                    event_id=f"EVT-{uuid.uuid4().hex[:8].upper()}",
                    case_id=self.case_id,
                    source_artifact_id=artifact.artifact_id,
                    source_record_reference=f"record_{idx + 1}",
                    source_type="IPDR",
                    timestamp_original=orig_time,
                    timestamp_utc=utc_time,
                    entity_type=EntityType.IP_ADDRESS,
                    entity_value_masked=mask_ip_address(norm_ip),
                    entity_value_hash=generate_entity_hash(norm_ip),
                    related_entity_type=EntityType.DOMAIN if norm_domain else None,
                    related_entity_value_masked=norm_domain if norm_domain else None,
                    action="IPDR_DESTINATION",
                    amount=duration,
                    location=subnet,
                    confidence=1.0,
                    extraction_method="IPDR_PARSER",
                    created_at=now_str
                ))

        return artifact, events
