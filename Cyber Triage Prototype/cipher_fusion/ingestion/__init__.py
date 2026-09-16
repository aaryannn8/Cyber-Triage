from typing import Tuple, List
from cipher_fusion.models import ArtifactModel, ArtifactType, NormalizedEventModel
from cipher_fusion.ingestion.cdr import CDRIngester
from cipher_fusion.ingestion.ipdr import IPDRIngester
from cipher_fusion.ingestion.bank import BankIngester
from cipher_fusion.ingestion.email import EmailIngester
from cipher_fusion.ingestion.android import AndroidIngester
from cipher_fusion.ingestion.chat import ChatIngester
from cipher_fusion.ingestion.complaint import ComplaintIngester

def ingest_file(case_id: str, file_type: ArtifactType, filename: str, file_bytes: bytes) -> Tuple[ArtifactModel, List[NormalizedEventModel]]:
    """Master ingestion dispatcher router for all 7 supported artifact types."""
    if file_type == ArtifactType.CDR:
        return CDRIngester(case_id).parse(filename, file_bytes)
    elif file_type == ArtifactType.IPDR:
        return IPDRIngester(case_id).parse(filename, file_bytes)
    elif file_type == ArtifactType.BANK:
        return BankIngester(case_id).parse(filename, file_bytes)
    elif file_type == ArtifactType.EMAIL:
        return EmailIngester(case_id).parse(filename, file_bytes)
    elif file_type == ArtifactType.ANDROID:
        return AndroidIngester(case_id).parse(filename, file_bytes)
    elif file_type == ArtifactType.CHAT:
        return ChatIngester(case_id).parse(filename, file_bytes)
    elif file_type == ArtifactType.COMPLAINT:
        return ComplaintIngester(case_id).parse(filename, file_bytes)
    else:
        raise ValueError(f"Unsupported artifact type: {file_type}")
