import pytest
from cipher_fusion.models import NormalizedEventModel, EntityType
from cipher_fusion.scoring import RiskScorer
from cipher_fusion.hashing import generate_entity_hash

def test_risk_scoring_calculation():
    h1 = generate_entity_hash("+919876500001")
    ev1 = NormalizedEventModel(
        event_id="EV1", case_id="CASE-1", source_artifact_id="ART1", source_record_reference="r1",
        source_type="BANK", timestamp_original="2026-09-15 10:00:00", timestamp_utc="2026-09-15T10:00:00Z",
        entity_type=EntityType.ACCOUNT_NUMBER, entity_value_masked="ACC-****0100", entity_value_hash=h1,
        action="DEBIT", amount=30000.0, created_at="2026-09-15T10:00:00Z"
    )
    ev2 = NormalizedEventModel(
        event_id="EV2", case_id="CASE-1", source_artifact_id="ART2", source_record_reference="r2",
        source_type="CDR", timestamp_original="2026-09-15 10:05:00", timestamp_utc="2026-09-15T10:05:00Z",
        entity_type=EntityType.PHONE_NUMBER, entity_value_masked="+91 98****0001", entity_value_hash=h1,
        action="CALL", amount=0.0, created_at="2026-09-15T10:05:00Z"
    )
    risk = RiskScorer.calculate_case_risk("CASE-1", [ev1, ev2], [])
    assert risk.total_score >= 30
    assert risk.rating in ["Low", "Medium", "High"]
    assert len(risk.reasons) > 0
