import pytest
from cipher_fusion.models import NormalizedEventModel, EntityType
from cipher_fusion.correlation import CorrelationEngine, MuleAccountAnalyzer
from cipher_fusion.hashing import generate_entity_hash

def test_exact_hash_correlation():
    h1 = generate_entity_hash("+919876500001")
    ev1 = NormalizedEventModel(
        event_id="EV1", case_id="CASE-1", source_artifact_id="ART1", source_record_reference="r1",
        source_type="CDR", timestamp_original="2026-09-15 10:00:00", timestamp_utc="2026-09-15T10:00:00Z",
        entity_type=EntityType.PHONE_NUMBER, entity_value_masked="+91 98****0001", entity_value_hash=h1,
        action="CALL", amount=0.0, created_at="2026-09-15T10:00:00Z"
    )
    ev2 = NormalizedEventModel(
        event_id="EV2", case_id="CASE-2", source_artifact_id="ART2", source_record_reference="r2",
        source_type="CHAT", timestamp_original="2026-09-15 11:00:00", timestamp_utc="2026-09-15T11:00:00Z",
        entity_type=EntityType.PHONE_NUMBER, entity_value_masked="+91 98****0001", entity_value_hash=h1,
        action="CHAT", amount=0.0, created_at="2026-09-15T11:00:00Z"
    )
    rels = CorrelationEngine.correlate_events([ev1, ev2])
    assert len(rels) == 1
    assert rels[0].relationship_type == "SHARED_IDENTIFIER"
    assert "CROSS_CASE_LINK" in rels[0].risk_indicators

def test_rapid_forwarding_mule_analysis():
    h_acc1 = generate_entity_hash("ACC-100")
    h_acc2 = generate_entity_hash("ACC-888")
    h_acc3 = generate_entity_hash("ACC-999")

    ev1 = NormalizedEventModel(
        event_id="EV1", case_id="CASE-1", source_artifact_id="ART1", source_record_reference="r1",
        source_type="BANK", timestamp_original="2026-09-15 10:00:00", timestamp_utc="2026-09-15T10:00:00Z",
        entity_type=EntityType.ACCOUNT_NUMBER, entity_value_masked="ACC-****0100", entity_value_hash=h_acc1,
        related_entity_type=EntityType.ACCOUNT_NUMBER, related_entity_value_masked="ACC-****0888",
        action="DEBIT", amount=40000.0, created_at="2026-09-15T10:00:00Z"
    )
    ev2 = NormalizedEventModel(
        event_id="EV2", case_id="CASE-1", source_artifact_id="ART1", source_record_reference="r2",
        source_type="BANK", timestamp_original="2026-09-15 10:10:00", timestamp_utc="2026-09-15T10:10:00Z",
        entity_type=EntityType.ACCOUNT_NUMBER, entity_value_masked="ACC-****0888", entity_value_hash=h_acc2,
        related_entity_type=EntityType.ACCOUNT_NUMBER, related_entity_value_masked="ACC-****0999",
        action="DEBIT", amount=40000.0, created_at="2026-09-15T10:10:00Z"
    )

    res = MuleAccountAnalyzer.analyze_mule_patterns([ev1, ev2])
    assert res['rapid_forwarding_count'] == 1
    assert res['rapid_forwarding_links'][0]['time_latency_mins'] == 10.0

def test_correlation_engine_upi_shadow_dataset():
    import glob, os
    from cipher_fusion.config import config
    from cipher_fusion.models import ArtifactType
    from cipher_fusion.ingestion import ingest_file

    demo_files = glob.glob(os.path.join(config.DEMO_DATA_DIR, "*"))
    all_events = []

    for fpath in demo_files:
        fname = os.path.basename(fpath)
        with open(fpath, "rb") as f:
            content = f.read()

        cid = "CASE-2026-001"
        if "case_002" in fname: cid = "CASE-2026-002"
        elif "case_003" in fname: cid = "CASE-2026-003"
        elif "case_004" in fname: cid = "CASE-2026-004"
        elif "case_005" in fname: cid = "CASE-2026-005"

        ftype = ArtifactType.CDR
        if "cdr" in fname: ftype = ArtifactType.CDR
        elif "ipdr" in fname: ftype = ArtifactType.IPDR
        elif "bank" in fname: ftype = ArtifactType.BANK
        elif "email" in fname: ftype = ArtifactType.EMAIL
        elif "android" in fname: ftype = ArtifactType.ANDROID
        elif "chat" in fname: ftype = ArtifactType.CHAT
        elif "complaint" in fname: ftype = ArtifactType.COMPLAINT

        _, evs = ingest_file(cid, ftype, fname, content)
        all_events.extend(evs)

    relationships = CorrelationEngine.correlate_events(all_events)
    assert len(relationships) >= 5, "Expected relationships to be generated from demo dataset"

    # Verify that EVERY relationship contains required lineage & metadata
    for rel in relationships:
        assert rel.source_artifact_id and rel.source_artifact_id.startswith("ART-"), f"Missing source_artifact_id: {rel}"
        assert rel.source_record_reference, f"Missing source_record_reference: {rel}"
        assert rel.matching_reason and len(rel.matching_reason) > 5, f"Unexplained relationship found: {rel}"
        assert 0.0 <= rel.confidence <= 1.0, f"Invalid confidence value: {rel}"
        assert len(rel.hash) == 64, f"Missing or invalid 64-char SHA-256 hash: {rel}"

