import uuid
from typing import List, Dict, Any
from datetime import datetime, timezone
from cipher_fusion.models import NormalizedEventModel, RelationshipModel
from cipher_fusion.config import config

class CorrelationEngine:
    @staticmethod
    def correlate_events(all_events: List[NormalizedEventModel]) -> List[RelationshipModel]:
        relationships = []
        seen = set()

        # Group events by hash for exact match correlation
        events_by_hash: Dict[str, List[NormalizedEventModel]] = {}
        for ev in all_events:
            events_by_hash.setdefault(ev.entity_value_hash, []).append(ev)

        # 1. Shared Exact Identifier Correlation (across artifacts and cases)
        for h, ev_list in events_by_hash.items():
            if len(ev_list) > 1:
                base_ev = ev_list[0]
                for other_ev in ev_list[1:]:
                    key = tuple(sorted([base_ev.event_id, other_ev.event_id]))
                    if key not in seen:
                        seen.add(key)
                        
                        same_case = (base_ev.case_id == other_ev.case_id)
                        case_note = f"in case {base_ev.case_id}" if same_case else f"across cases {base_ev.case_id} and {other_ev.case_id}"
                        reason = f"Exact shared identifier ({base_ev.entity_type.value}) {case_note}"
                        
                        risk_tags = ["SHARED_IDENTIFIER"]
                        if not same_case:
                            risk_tags.append("CROSS_CASE_LINK")

                        relationships.append(RelationshipModel(
                            relationship_id=f"REL-{uuid.uuid4().hex[:8].upper()}",
                            source_case_id=base_ev.case_id,
                            target_case_id=other_ev.case_id,
                            source_entity=base_ev.entity_value_masked,
                            target_entity=other_ev.entity_value_masked,
                            relationship_type="SHARED_IDENTIFIER",
                            source_artifact_id=other_ev.source_artifact_id,
                            source_record_reference=other_ev.source_record_reference,
                            timestamp=other_ev.timestamp_utc,
                            matching_reason=reason,
                            confidence=1.0,
                            risk_indicators=risk_tags,
                            hash=h,
                            created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                        ))

        # 2. Cross-Entity Direct Links from Event Records (e.g. Phone -> IP, Account -> Account, Phone -> Receiver)
        for ev in all_events:
            if ev.related_entity_value_masked:
                rel_type = "LINKED_TO"
                if ev.source_type == "BANK":
                    rel_type = "TRANSFER_TO"
                elif ev.source_type == "CDR":
                    rel_type = "CALLED"
                elif ev.source_type == "IPDR":
                    rel_type = "CONNECTED_IP"
                elif ev.source_type == "EMAIL":
                    rel_type = "EMAILED"
                elif ev.source_type == "ANDROID":
                    rel_type = "INSTALLED_ON"

                reason = f"Direct relationship extracted from {ev.source_type} record ({ev.source_record_reference})"
                risk_tags = ["DIRECT_RECORD_LINK"]
                if ev.amount >= config.HIGH_VALUE_TRANSACTION_THRESHOLD:
                    risk_tags.append("HIGH_VALUE_TRANSACTION")

                relationships.append(RelationshipModel(
                    relationship_id=f"REL-{uuid.uuid4().hex[:8].upper()}",
                    source_case_id=ev.case_id,
                    target_case_id=ev.case_id,
                    source_entity=ev.entity_value_masked,
                    target_entity=ev.related_entity_value_masked,
                    relationship_type=rel_type,
                    source_artifact_id=ev.source_artifact_id,
                    source_record_reference=ev.source_record_reference,
                    timestamp=ev.timestamp_utc,
                    matching_reason=reason,
                    confidence=ev.confidence,
                    risk_indicators=risk_tags,
                    hash=ev.entity_value_hash,
                    created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                ))

        return relationships
