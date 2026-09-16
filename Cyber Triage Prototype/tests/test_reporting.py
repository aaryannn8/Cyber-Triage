import os
import pytest
from cipher_fusion.models import ArtifactModel, ArtifactType, NormalizedEventModel, EntityType, ActionQueueItem
from cipher_fusion.scoring import RiskScorer
from cipher_fusion.reporting import PDFReportGenerator, JSONReportGenerator
from cipher_fusion.config import config

def test_pdf_and_json_generation(tmp_path):
    art = ArtifactModel(
        artifact_id="ART-1", case_id="CASE-TEST", filename="test.csv", file_type=ArtifactType.CDR,
        file_size=100, sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        upload_timestamp="2026-09-15T10:00:00Z"
    )
    ev = NormalizedEventModel(
        event_id="EV1", case_id="CASE-TEST", source_artifact_id="ART-1", source_record_reference="r1",
        source_type="CDR", timestamp_original="2026-09-15 10:00:00", timestamp_utc="2026-09-15T10:00:00Z",
        entity_type=EntityType.PHONE_NUMBER, entity_value_masked="+91 98****0001", entity_value_hash="hash1",
        action="CALL", amount=0.0, created_at="2026-09-15T10:00:00Z"
    )
    risk = RiskScorer.calculate_case_risk("CASE-TEST", [ev], [])
    action = ActionQueueItem(
        action_id="ACT1", case_id="CASE-TEST", priority_rank=1, lead_type="MULE",
        masked_endpoint="ACC-****0100", risk_score=80, reason="Test lead", last_observed_time="2026-09-15T10:00:00Z",
        linked_cases_count=2, total_amount=40000.0, recommended_action="Verify beneficiary", related_artifact_ids=["ART-1"]
    )

    pdf_out = os.path.join(tmp_path, "test_report.pdf")
    json_out = os.path.join(tmp_path, "test_report.json")

    PDFReportGenerator.generate_pdf("CASE-TEST", [art], [ev], risk, [action], pdf_out)
    assert os.path.exists(pdf_out)
    assert os.path.getsize(pdf_out) > 0

    JSONReportGenerator.generate_json("CASE-TEST", [art], [ev], risk, [action], {}, json_out)
    assert os.path.exists(json_out)
    assert os.path.getsize(json_out) > 0
