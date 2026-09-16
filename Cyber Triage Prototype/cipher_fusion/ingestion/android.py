import json
import uuid
from typing import List, Tuple
from datetime import datetime, timezone
from cipher_fusion.models import ArtifactModel, ArtifactType, NormalizedEventModel, EntityType
from cipher_fusion.ingestion.base import BaseIngester
from cipher_fusion.normalization import normalize_timestamp, normalize_domain
from cipher_fusion.hashing import generate_entity_hash, calculate_sha256_bytes

class AndroidIngester(BaseIngester):
    def parse(self, filename: str, file_bytes: bytes) -> Tuple[ArtifactModel, List[NormalizedEventModel]]:
        artifact = self.create_artifact_record(filename, file_bytes, ArtifactType.ANDROID)
        events = []
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        if filename.endswith('.json'):
            meta = json.loads(file_bytes.decode('utf-8'))
        else:
            # Parse key=value TXT metadata lines
            meta = {}
            for line in file_bytes.decode('utf-8', errors='ignore').splitlines():
                if '=' in line:
                    k, v = line.split('=', 1)
                    meta[k.strip()] = v.strip()

        pkg = str(meta.get('package_name', '')).strip()
        cert = str(meta.get('certificate_hash', '')).strip()
        domains = meta.get('embedded_domains', [])
        if isinstance(domains, str):
            domains = [d.strip() for d in domains.split(',') if d.strip()]
        orig_time = str(meta.get('created_time', ''))
        utc_time = normalize_timestamp(orig_time)

        if pkg:
            events.append(NormalizedEventModel(
                event_id=f"EVT-{uuid.uuid4().hex[:8].upper()}",
                case_id=self.case_id,
                source_artifact_id=artifact.artifact_id,
                source_record_reference="android_meta_package",
                source_type="ANDROID",
                timestamp_original=orig_time,
                timestamp_utc=utc_time,
                entity_type=EntityType.APK_PACKAGE,
                entity_value_masked=pkg,
                entity_value_hash=generate_entity_hash(pkg),
                related_entity_type=EntityType.CERTIFICATE_HASH if cert else None,
                related_entity_value_masked=f"{cert[:6]}...{cert[-6:]}" if len(cert) > 12 else cert,
                action="APK_METADATA_ANALYZED",
                amount=0.0,
                location=filename,
                confidence=1.0,
                extraction_method="ANDROID_META_PARSER",
                created_at=now_str
            ))

        for dom in domains:
            norm_d = normalize_domain(dom)
            if norm_d:
                events.append(NormalizedEventModel(
                    event_id=f"EVT-{uuid.uuid4().hex[:8].upper()}",
                    case_id=self.case_id,
                    source_artifact_id=artifact.artifact_id,
                    source_record_reference="android_embedded_domain",
                    source_type="ANDROID",
                    timestamp_original=orig_time,
                    timestamp_utc=utc_time,
                    entity_type=EntityType.DOMAIN,
                    entity_value_masked=norm_d,
                    entity_value_hash=generate_entity_hash(norm_d),
                    related_entity_type=EntityType.APK_PACKAGE if pkg else None,
                    related_entity_value_masked=pkg if pkg else None,
                    action="APK_EMBEDDED_DOMAIN",
                    amount=0.0,
                    location=filename,
                    confidence=1.0,
                    extraction_method="ANDROID_META_PARSER",
                    created_at=now_str
                ))

        return artifact, events
