import json
import os
from typing import List, Dict, Any
from datetime import datetime, timezone
from cipher_fusion.config import config
from cipher_fusion.models import (
    ArtifactModel, NormalizedEventModel, RiskScoreBreakdown,
    ActionQueueItem, InvestigationReportModel
)

class JSONReportGenerator:
    @staticmethod
    def generate_json(
        case_id: str,
        artifacts: List[ArtifactModel],
        events: List[NormalizedEventModel],
        risk: RiskScoreBreakdown,
        action_queue: List[ActionQueueItem],
        mule_summary: Dict[str, Any],
        output_path: str,
        report_type: str = "Case-Specific",
        cross_case_authorized: bool = False,
        analyst_session: str = "ANALYST_LOCAL"
    ) -> str:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        case_events = [e for e in events if e.case_id == case_id] if report_type == "Case-Specific" else events
        case_artifacts = [a for a in artifacts if a.case_id == case_id] if report_type == "Case-Specific" else artifacts

        report_dict = {
            "case_id": case_id,
            "report_type": report_type,
            "generated_at": now_str,
            "disclaimer": config.FULL_DISCLAIMER,
            "authorization_status": "AUTHORIZED" if cross_case_authorized else "UNAUTHORIZED (High-level only)",
            "analyst_session": analyst_session,
            "artifact_inventory": [a.model_dump() for a in case_artifacts],
            "key_entities": [
                {"type": e.entity_type.value if hasattr(e.entity_type, 'value') else e.entity_type, "masked": e.entity_value_masked, "hash": e.entity_value_hash}
                for e in case_events
            ],
            "unified_timeline": [e.model_dump() for e in case_events],
            "transaction_flow_summary": mule_summary,
            "risk_score_breakdown": risk.model_dump(),
            "golden_hour_action_queue": [item.model_dump() for item in action_queue],
            "source_references": [
                {"event_id": e.event_id, "artifact_id": e.source_artifact_id, "record_ref": e.source_record_reference}
                for e in case_events
            ],
            "audit_summary": {"total_artifacts": len(case_artifacts), "total_events": len(case_events)}
        }

        if report_type == "Cross-Case":
            report_dict["warning"] = "Cross-case correlation summary. Detailed artifact access requires authorization."

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, indent=2)

        return output_path
