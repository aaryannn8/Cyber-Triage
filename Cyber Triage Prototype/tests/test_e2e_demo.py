import glob
import os
import pytest
from cipher_fusion.config import config
from cipher_fusion.models import ArtifactType, CaseModel
from cipher_fusion.database import db
from cipher_fusion.ingestion import ingest_file
from cipher_fusion.correlation import CorrelationEngine, MuleAccountAnalyzer
from cipher_fusion.scoring import RiskScorer
from cipher_fusion.reporting import PDFReportGenerator, JSONReportGenerator

def test_e2e_operation_upi_shadow(tmp_path):
    # 1. Setup cases
    case_ids = ["CASE-2026-001", "CASE-2026-002", "CASE-2026-003", "CASE-2026-004", "CASE-2026-005"]
    for cid in case_ids:
        db.insert_case(CaseModel(case_id=cid, title=f"Demo {cid}", created_at="2026-09-15T10:00:00Z"))

    # 2. Ingest synthetic demo dataset
    demo_files = glob.glob(os.path.join(config.DEMO_DATA_DIR, "*"))
    assert len(demo_files) >= 7, "Demo directory missing synthetic files."

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
        db.insert_artifact(art)
        db.insert_events(evs)

    # 3. Correlate across all cases
    all_evs = db.get_events()
    all_arts = db.get_artifacts()
    rels = CorrelationEngine.correlate_events(all_evs)
    db.insert_relationships(rels)

    assert len(all_evs) >= 10
    assert len(rels) >= 3

    # 4. Verify cross-case links
    cross_case_links = [r for r in rels if "CROSS_CASE_LINK" in r.risk_indicators]
    assert len(cross_case_links) >= 1, "Expected cross-case correlation links!"

    # 5. Mule Analysis
    mule_res = MuleAccountAnalyzer.analyze_mule_patterns(all_evs)
    assert mule_res['rapid_forwarding_count'] >= 1, "Expected rapid forwarding link!"

    # 6. Risk Score & PDF/JSON Export
    risk = RiskScorer.calculate_case_risk("CASE-2026-001", db.get_events("CASE-2026-001"), rels)
    assert risk.total_score >= 50

    pdf_out = os.path.join(tmp_path, "CASE-2026-001_report.pdf")
    json_out = os.path.join(tmp_path, "CASE-2026-001_report.json")
    PDFReportGenerator.generate_pdf("CASE-2026-001", all_arts, all_evs, risk, [], pdf_out)
    JSONReportGenerator.generate_json("CASE-2026-001", all_arts, all_evs, risk, [], mule_res, json_out)

    assert os.path.exists(pdf_out) and os.path.getsize(pdf_out) > 0
    assert os.path.exists(json_out) and os.path.getsize(json_out) > 0
