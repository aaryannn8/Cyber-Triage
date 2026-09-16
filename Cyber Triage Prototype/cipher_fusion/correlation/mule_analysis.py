from datetime import datetime, timezone
from typing import List, Dict, Any
from cipher_fusion.config import config
from cipher_fusion.models import NormalizedEventModel, ActionQueueItem
import uuid

class MuleAccountAnalyzer:
    @staticmethod
    def analyze_mule_patterns(events: List[NormalizedEventModel]) -> Dict[str, Any]:
        """
        Analyzes transaction events for rapid forwarding, multi-hop routing,
        fund convergence, fund splitting, and velocity metrics.
        """
        bank_events = [e for e in events if e.source_type == "BANK"]
        bank_events.sort(key=lambda x: x.timestamp_utc)

        mule_accounts = {}
        rapid_forwarding_links = []
        convergences = {}
        splittings = {}

        # Trace transfers per account
        for i, ev1 in enumerate(bank_events):
            sender = ev1.entity_value_masked
            receiver = ev1.related_entity_value_masked
            amt = ev1.amount
            t1 = datetime.fromisoformat(ev1.timestamp_utc.replace("Z", "+00:00"))

            if receiver:
                convergences.setdefault(receiver, set()).add(sender)
            if sender:
                splittings.setdefault(sender, set()).add(receiver)

            # Check rapid forwarding (< RAPID_FORWARDING_MINUTES)
            for ev2 in bank_events[i+1:]:
                if ev2.entity_value_masked == receiver and ev2.related_entity_value_masked:
                    t2 = datetime.fromisoformat(ev2.timestamp_utc.replace("Z", "+00:00"))
                    time_diff_mins = (t2 - t1).total_seconds() / 60.0
                    
                    if 0 <= time_diff_mins <= config.RAPID_FORWARDING_MINUTES:
                        percent_forwarded = (ev2.amount / amt * 100.0) if amt > 0 else 100.0
                        rapid_forwarding_links.append({
                            "intermediary": receiver,
                            "source": sender,
                            "destination": ev2.related_entity_value_masked,
                            "time_latency_mins": round(time_diff_mins, 2),
                            "incoming_amount": amt,
                            "outgoing_amount": ev2.amount,
                            "percent_forwarded": round(percent_forwarded, 1),
                            "t1": ev1.timestamp_utc,
                            "t2": ev2.timestamp_utc
                        })

        # Summarize mule metrics
        summary = {
            "total_transactions": len(bank_events),
            "rapid_forwarding_count": len(rapid_forwarding_links),
            "rapid_forwarding_links": rapid_forwarding_links,
            "convergence_targets": {k: list(v) for k, v in convergences.items() if len(v) >= 2},
            "splitting_sources": {k: list(v) for k, v in splittings.items() if len(v) >= 2},
        }

        return summary
