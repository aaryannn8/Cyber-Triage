import io
import uuid
import pandas as pd
from typing import List, Tuple
from datetime import datetime, timezone
from cipher_fusion.models import ArtifactModel, ArtifactType, NormalizedEventModel, EntityType
from cipher_fusion.ingestion.base import BaseIngester
from cipher_fusion.normalization import normalize_timestamp, normalize_upi
from cipher_fusion.security import mask_account_number, mask_upi_id
from cipher_fusion.hashing import generate_entity_hash

class BankIngester(BaseIngester):
    def parse(self, filename: str, file_bytes: bytes) -> Tuple[ArtifactModel, List[NormalizedEventModel]]:
        artifact = self.create_artifact_record(filename, file_bytes, ArtifactType.BANK)
        events = []

        if filename.endswith('.xlsx') or filename.endswith('.xls'):
            df = pd.read_excel(io.BytesIO(file_bytes))
        else:
            df = pd.read_csv(io.BytesIO(file_bytes))

        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        for idx, row in df.iterrows():
            tx_id = str(row.get('transaction_id', f"TX-{idx+1}")).strip()
            orig_time = str(row.get('timestamp', ''))
            utc_time = normalize_timestamp(orig_time)
            sender = str(row.get('sender_account', '')).strip()
            receiver = str(row.get('receiver_account', '')).strip()
            upi_id = str(row.get('upi_id', '')).strip()
            amount = float(row.get('amount', 0.0))
            bank_ref = str(row.get('bank_reference', '')).strip()
            tx_type = str(row.get('transaction_type', 'TRANSFER')).strip()

            norm_upi = normalize_upi(upi_id) if upi_id else ""

            # Event 1: Sender Account
            if sender:
                events.append(NormalizedEventModel(
                    event_id=f"EVT-{uuid.uuid4().hex[:8].upper()}",
                    case_id=self.case_id,
                    source_artifact_id=artifact.artifact_id,
                    source_record_reference=f"row_{idx + 1}",
                    source_type="BANK",
                    timestamp_original=orig_time,
                    timestamp_utc=utc_time,
                    entity_type=EntityType.ACCOUNT_NUMBER,
                    entity_value_masked=mask_account_number(sender),
                    entity_value_hash=generate_entity_hash(sender),
                    related_entity_type=EntityType.ACCOUNT_NUMBER if receiver else None,
                    related_entity_value_masked=mask_account_number(receiver) if receiver else None,
                    action=f"BANK_{tx_type.upper()}_DEBIT",
                    amount=amount,
                    location=bank_ref,
                    confidence=1.0,
                    extraction_method="BANK_PARSER",
                    created_at=now_str
                ))

            # Event 2: UPI Handle event if present
            if norm_upi:
                events.append(NormalizedEventModel(
                    event_id=f"EVT-{uuid.uuid4().hex[:8].upper()}",
                    case_id=self.case_id,
                    source_artifact_id=artifact.artifact_id,
                    source_record_reference=f"row_{idx + 1}",
                    source_type="BANK",
                    timestamp_original=orig_time,
                    timestamp_utc=utc_time,
                    entity_type=EntityType.UPI_ID,
                    entity_value_masked=mask_upi_id(norm_upi),
                    entity_value_hash=generate_entity_hash(norm_upi),
                    related_entity_type=EntityType.ACCOUNT_NUMBER if receiver else None,
                    related_entity_value_masked=mask_account_number(receiver) if receiver else None,
                    action="UPI_PAYMENT",
                    amount=amount,
                    location=tx_id,
                    confidence=1.0,
                    extraction_method="BANK_PARSER",
                    created_at=now_str
                ))

        return artifact, events
