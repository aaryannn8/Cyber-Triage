import email
from email import policy
import re
import uuid
from typing import List, Tuple
from datetime import datetime, timezone
from cipher_fusion.models import ArtifactModel, ArtifactType, NormalizedEventModel, EntityType
from cipher_fusion.ingestion.base import BaseIngester
from cipher_fusion.normalization import (
    normalize_email, normalize_ip_address, get_ip_subnet, normalize_timestamp
)
from cipher_fusion.security import mask_email, mask_ip_address
from cipher_fusion.hashing import generate_entity_hash

class EmailIngester(BaseIngester):
    def parse(self, filename: str, file_bytes: bytes) -> Tuple[ArtifactModel, List[NormalizedEventModel]]:
        artifact = self.create_artifact_record(filename, file_bytes, ArtifactType.EMAIL)
        events = []
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        msg = email.message_from_bytes(file_bytes, policy=policy.default)
        
        from_hdr = str(msg.get('From', ''))
        to_hdr = str(msg.get('To', ''))
        date_hdr = str(msg.get('Date', ''))
        msg_id = str(msg.get('Message-ID', ''))
        reply_to = str(msg.get('Reply-To', ''))
        received_hdrs = msg.get_all('Received') or []

        utc_time = normalize_timestamp(date_hdr)
        norm_from = normalize_email(from_hdr)
        norm_to = normalize_email(to_hdr)

        # Extract originating IP from Received headers
        originating_ip = ""
        for r in received_hdrs:
            ips = re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', str(r))
            for candidate in ips:
                norm_cand = normalize_ip_address(candidate)
                if norm_cand and not norm_cand.startswith(("127.", "10.", "192.168.")):
                    originating_ip = norm_cand
                    break
            if originating_ip:
                break

        if norm_from:
            events.append(NormalizedEventModel(
                event_id=f"EVT-{uuid.uuid4().hex[:8].upper()}",
                case_id=self.case_id,
                source_artifact_id=artifact.artifact_id,
                source_record_reference="header_from",
                source_type="EMAIL",
                timestamp_original=date_hdr,
                timestamp_utc=utc_time,
                entity_type=EntityType.EMAIL_ADDRESS,
                entity_value_masked=mask_email(norm_from),
                entity_value_hash=generate_entity_hash(norm_from),
                related_entity_type=EntityType.EMAIL_ADDRESS if norm_to else None,
                related_entity_value_masked=mask_email(norm_to) if norm_to else None,
                action="EMAIL_SENT",
                amount=0.0,
                location=msg_id,
                confidence=1.0,
                extraction_method="EML_HEADER_PARSER",
                created_at=now_str
            ))

        if originating_ip:
            subnet = get_ip_subnet(originating_ip)
            events.append(NormalizedEventModel(
                event_id=f"EVT-{uuid.uuid4().hex[:8].upper()}",
                case_id=self.case_id,
                source_artifact_id=artifact.artifact_id,
                source_record_reference="header_received_ip",
                source_type="EMAIL",
                timestamp_original=date_hdr,
                timestamp_utc=utc_time,
                entity_type=EntityType.IP_ADDRESS,
                entity_value_masked=mask_ip_address(originating_ip),
                entity_value_hash=generate_entity_hash(originating_ip),
                related_entity_type=EntityType.EMAIL_ADDRESS if norm_from else None,
                related_entity_value_masked=mask_email(norm_from) if norm_from else None,
                action="EMAIL_ORIGINATING_IP",
                amount=0.0,
                location=subnet,
                confidence=1.0,
                extraction_method="EML_HEADER_PARSER",
                created_at=now_str
            ))

        return artifact, events
