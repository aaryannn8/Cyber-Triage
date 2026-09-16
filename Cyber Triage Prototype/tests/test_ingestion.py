import pytest
from cipher_fusion.models import ArtifactType
from cipher_fusion.ingestion import ingest_file

def test_cdr_ingestion():
    csv_bytes = b"caller_number,receiver_number,timestamp,duration_seconds,cell_tower,call_type\n+919876500001,+919876511111,2026-09-15 10:15:00,120,TOWER-1,VOICE"
    art, events = ingest_file("CASE-TEST", ArtifactType.CDR, "test_cdr.csv", csv_bytes)
    assert art.file_type == ArtifactType.CDR
    assert len(art.sha256) == 64
    assert len(events) >= 1
    assert events[0].source_type == "CDR"

def test_bank_ingestion():
    bank_csv = b"transaction_id,timestamp,sender_account,receiver_account,upi_id,amount,bank_reference,transaction_type\nTXN-1,2026-09-15 10:30:00,ACC-100,ACC-200,test@upi,5000.0,UTR-1,UPI"
    art, events = ingest_file("CASE-TEST", ArtifactType.BANK, "test_bank.csv", bank_csv)
    assert art.file_type == ArtifactType.BANK
    assert len(events) >= 2
