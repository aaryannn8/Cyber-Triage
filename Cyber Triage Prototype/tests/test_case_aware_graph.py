import pytest
import os
import json
import glob
from datetime import datetime, timezone
from cipher_fusion.database import Database
from cipher_fusion.models import (
    CaseModel, ArtifactType, RelationshipModel, AuditLogModel
)
from cipher_fusion.ingestion import ingest_file
from cipher_fusion.correlation import CorrelationEngine, MuleAccountAnalyzer
from cipher_fusion.graph import EvidenceGraphBuilder
from cipher_fusion.scoring import RiskScorer
from cipher_fusion.reporting import PDFReportGenerator, JSONReportGenerator
from cipher_fusion.config import config

@pytest.fixture
def setup_test_db(tmp_path):
    test_db_path = str(tmp_path / "test_case_aware.db")
    test_db = Database(db_path=test_db_path)
    
    # Insert 5 test cases
    cases = ["CASE-2026-001", "CASE-2026-002", "CASE-2026-003", "CASE-2026-004", "CASE-2026-005"]
    for c_id in cases:
        test_db.insert_case(CaseModel(
            case_id=c_id,
            title=f"Test Case {c_id}",
            description="Synthetic test case",
            status="ACTIVE",
            created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        ))
    
    # Ingest demo data into test DB
    demo_files = glob.glob(os.path.join(config.DEMO_DATA_DIR, "*"))
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

        art, evs = ingest_file(cid, ftype, fname, content)
        test_db.insert_artifact(art)
        test_db.insert_events(evs)

    all_evs = test_db.get_events()
    rels = CorrelationEngine.correlate_events(all_evs)
    test_db.insert_relationships(rels)
    
    return test_db


def test_1_case_specific_graph_isolation(setup_test_db):
    test_db = setup_test_db
    rels = test_db.get_relationships("CASE-2026-001", mode="Current Case Only")
    arts = test_db.get_artifacts()
    
    G = EvidenceGraphBuilder.build_networkx_graph(rels, arts, active_case_id="CASE-2026-001", mode="Current Case Only")
    
    # CASE-2026-005 entities must NOT exist in CASE-2026-001 isolated graph
    for node in G.nodes():
        assert "CASE-2026-005" not in str(node)
        assert "+919876599999" not in str(node)
        assert "unrelated-demo.test" not in str(node)


def test_2_related_case_filtering(setup_test_db):
    test_db = setup_test_db
    rels = test_db.get_relationships("CASE-2026-001", mode="Current Case + Related Cases")
    arts = test_db.get_artifacts()
    
    G = EvidenceGraphBuilder.build_networkx_graph(rels, arts, active_case_id="CASE-2026-001", mode="Current Case + Related Cases")
    
    # Check that connected entities exist in the graph
    node_labels = list(G.nodes())
    assert any("+919876500001" in n for n in node_labels)  # shared phone (CASE-001 & CASE-002)


def test_3_unrelated_case_exclusion(setup_test_db):
    test_db = setup_test_db
    rels = test_db.get_relationships("CASE-2026-001", mode="Current Case + Related Cases")
    arts = test_db.get_artifacts()
    
    G = EvidenceGraphBuilder.build_networkx_graph(rels, arts, active_case_id="CASE-2026-001", mode="Current Case + Related Cases")
    
    # CASE-2026-005 must be strictly excluded
    for node in G.nodes():
        assert "+919876599999" not in str(node)
        assert "unrelated-demo.test" not in str(node)


def test_4_cross_case_authorization(setup_test_db):
    test_db = setup_test_db
    rels = test_db.get_relationships("CASE-2026-001", mode="Cross-Case Correlation")
    arts = test_db.get_artifacts()
    
    # Unauthorized graph
    G_unauth = EvidenceGraphBuilder.build_networkx_graph(rels, arts, active_case_id="CASE-2026-001", mode="Cross-Case Correlation", authorized=False)
    for u, v, data in G_unauth.edges(data=True):
        assert "REDACTED" in data['source_record_reference']
        
    # Authorized graph
    G_auth = EvidenceGraphBuilder.build_networkx_graph(rels, arts, active_case_id="CASE-2026-001", mode="Cross-Case Correlation", authorized=True)
    for u, v, data in G_auth.edges(data=True):
        assert "REDACTED" not in data['source_record_reference']


def test_5_case_specific_timeline(setup_test_db):
    test_db = setup_test_db
    c1_events = test_db.get_events("CASE-2026-001")
    for ev in c1_events:
        assert ev.case_id == "CASE-2026-001"


def test_6_case_specific_reports(setup_test_db, tmp_path):
    test_db = setup_test_db
    c1_arts = test_db.get_artifacts("CASE-2026-001")
    c1_events = test_db.get_events("CASE-2026-001")
    rels = test_db.get_relationships("CASE-2026-001", mode="Current Case Only")
    action_items = test_db.get_action_items("CASE-2026-001")
    risk = RiskScorer.calculate_case_risk("CASE-2026-001", c1_events, rels)
    mule_summary = MuleAccountAnalyzer.analyze_mule_patterns(c1_events)
    
    json_out = str(tmp_path / "case_001_report.json")
    JSONReportGenerator.generate_json("CASE-2026-001", c1_arts, c1_events, risk, action_items, mule_summary, json_out, report_type="Case-Specific")
    
    with open(json_out, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    assert data['case_id'] == "CASE-2026-001"
    assert "CASE-2026-005" not in json.dumps(data)


def test_7_cross_case_report(setup_test_db, tmp_path):
    test_db = setup_test_db
    all_arts = test_db.get_artifacts()
    all_events = test_db.get_events()
    rels = test_db.get_relationships("CASE-2026-001", mode="Cross-Case Correlation")
    action_items = test_db.get_action_items("CASE-2026-001")
    risk = RiskScorer.calculate_case_risk("CASE-2026-001", all_events, rels)
    mule_summary = MuleAccountAnalyzer.analyze_mule_patterns(all_events)
    
    json_out = str(tmp_path / "cross_case_report.json")
    JSONReportGenerator.generate_json("CASE-2026-001", all_arts, all_events, risk, action_items, mule_summary, json_out, report_type="Cross-Case", cross_case_authorized=False)
    
    with open(json_out, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    assert data['report_type'] == "Cross-Case"
    assert "warning" in data


def test_8_provenance_verification(setup_test_db):
    test_db = setup_test_db
    rels = test_db.get_relationships()
    assert len(rels) > 0
    for r in rels:
        assert r.source_artifact_id != ""
        assert r.source_record_reference != ""
        assert r.matching_reason != ""
        assert r.confidence > 0.0


def test_9_risk_separation(setup_test_db):
    test_db = setup_test_db
    c1_events = test_db.get_events("CASE-2026-001")
    c5_events = test_db.get_events("CASE-2026-005")
    rels = test_db.get_relationships()
    
    risk1 = RiskScorer.calculate_case_risk("CASE-2026-001", c1_events, rels)
    risk5 = RiskScorer.calculate_case_risk("CASE-2026-005", c5_events, rels)
    
    assert risk1.total_score != risk5.total_score


def test_10_audit_logging(setup_test_db):
    test_db = setup_test_db
    log = AuditLogModel(
        log_id="AUD-TEST-100",
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        analyst_id="ANALYST_TEST",
        action_type="TEST_ACTION",
        target_identifier="CASE-2026-001",
        details="Tested audit logging"
    )
    test_db.log_audit(log)
    logs = test_db.get_audit_logs()
    assert any(l.log_id == "AUD-TEST-100" for l in logs)
