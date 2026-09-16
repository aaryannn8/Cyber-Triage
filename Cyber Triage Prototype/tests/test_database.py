import os
import pytest
from datetime import datetime, timezone
from cipher_fusion.database import Database
from cipher_fusion.models import (
    CaseModel, ArtifactModel, ArtifactType, NormalizedEventModel, 
    EntityType, RelationshipModel, AuditLogModel
)

def test_database_crud(tmp_path):
    db_file = os.path.join(tmp_path, "test_db.sqlite3")
    test_db = Database(db_file)

    # 1. Insert Case
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    c = CaseModel(case_id="CASE-DB-1", title="Database Unit Test Case", created_at=now_str)
    test_db.insert_case(c)
    retrieved_case = test_db.get_case("CASE-DB-1")
    assert retrieved_case is not None
    assert retrieved_case.title == "Database Unit Test Case"

    # 2. Insert Artifact
    art = ArtifactModel(
        artifact_id="ART-DB-1", case_id="CASE-DB-1", filename="db_test.csv",
        file_type=ArtifactType.CDR, file_size=500, sha256="1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
        upload_timestamp=now_str
    )
    test_db.insert_artifact(art)
    arts = test_db.get_artifacts("CASE-DB-1")
    assert len(arts) == 1
    assert arts[0].sha256.startswith("123456")

    # 3. Insert Events
    ev = NormalizedEventModel(
        event_id="EV-DB-1", case_id="CASE-DB-1", source_artifact_id="ART-DB-1",
        source_record_reference="row_1", source_type="CDR", timestamp_original=now_str,
        timestamp_utc=now_str, entity_type=EntityType.PHONE_NUMBER, entity_value_masked="+91 98****0001",
        entity_value_hash="hash123", action="CALL", amount=0.0, created_at=now_str
    )
    test_db.insert_events([ev])
    evs = test_db.get_events("CASE-DB-1")
    assert len(evs) == 1
    assert evs[0].event_id == "EV-DB-1"

    # 4. Insert Audit Log
    audit = AuditLogModel(
        log_id="AUD-DB-1", timestamp=now_str, analyst_id="ANALYST_TEST",
        action_type="TEST_ACTION", target_identifier="TARGET-1", details="Database unit test entry"
    )
    test_db.log_audit(audit)
    logs = test_db.get_audit_logs()
    assert len(logs) >= 1
    assert logs[0].analyst_id == "ANALYST_TEST"
