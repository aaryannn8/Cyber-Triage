# CIPHER-FUSION: System Architecture Document

## Executive Overview
CIPHER-FUSION is an AI-assisted, rule-backed digital artifact correlation and cyber fraud intelligence engine built for authorized law-enforcement analysts. It transforms disparate evidence sources into structured evidence events, directional graphs, fund-flow timelines, and actionable Golden-Hour queues.

## High-Level Architecture Diagram

```
+-----------------------------------------------------------------------+
|                            USER INTERFACE                             |
|       (Streamlit Dashboard: Overview, Graph, Timeline, Queue, PDF)    |
+-----------------------------------------------------------------------+
                                    |
                                    v
+-----------------------------------------------------------------------+
|                         APPLICATION CONTROLLER                        |
|        (State Management, Case Context, Audit Logger, Security)       |
+-----------------------------------------------------------------------+
                                    |
            +-----------------------+-----------------------+
            |                                               |
            v                                               v
+-----------------------+                       +-----------------------+
|   INGESTION LAYER     |                       |   CORRELATION ENGINE  |
|  - Read-Only Uploads  |                       |  - Shared Hash Engine |
|  - SHA-256 Hashing    |                       |  - Cross-Entity Link  |
|  - Parsers (CDR, Bank,|                       |  - Time-Window Engine |
|    IPDR, EML, Chat,   |                       |  - Mule/Velocity Math |
|    Android, Complaint)|                       |  - Risk Score (0-100) |
+-----------------------+                       +-----------------------+
            |                                               |
            v                                               v
+-----------------------------------------------------------------------+
|                       NORMALIZATION & EXTRACTION                      |
|  - Phone Standardizer (+91), IP /24 Subnet, ISO-UTC Timestamps        |
|  - Rule-Based Regex Extraction for 17 Entity Types                    |
|  - Deterministic Salted Hashing & Masking                             |
+-----------------------------------------------------------------------+
                                    |
                                    v
+-----------------------------------------------------------------------+
|                          SQLITE STORAGE LAYER                         |
|   (artifacts, events, entities, relationships, action_queue, audit_log)|
+-----------------------------------------------------------------------+
```

## System Components

### 1. Ingestion Engine (`cipher_fusion/ingestion/`)
- Accepts 7 supported format types:
  1. CDR (CSV / Excel)
  2. IPDR (CSV / JSON)
  3. Bank / UPI Transactions (CSV / Excel)
  4. Email Headers (EML parse only)
  5. Android Metadata (JSON / TXT)
  6. Chat Exports (JSON / TXT)
  7. Complaint Text (JSON / TXT)
- Computes SHA-256 hash immediately upon file receipt before reading contents.
- Stores raw files in read-only local storage (`data/uploads/` or in SQLite binary storage).

### 2. Normalization & Extraction Engine (`cipher_fusion/normalization/`, `cipher_fusion/extraction/`)
- Phone Normalization: Converts Indian formats (e.g. `09876543210`, `98765-43210`, `919876543210`) into standardized `+919876543210`.
- IP Normalization: Derives `/24` subnets (e.g. `198.51.100.10` -> subnet `198.51.100.0/24`).
- Timestamp Normalization: Converts localized/string dates into UTC ISO 8601 strings.
- Identifier Cleaning: Lowercases email addresses, UPI handles (`user@upi`), domains (`suspicious-demo.test`).
- Deterministic Masking: Displays `+91 98****3210` or `ACC-****5678` while using SHA-256 hashes for correlation matching.

### 3. Database Layer (`cipher_fusion/database.py`)
- SQLite database storing structured records:
  - `cases`: Case ID, title, status, timestamps.
  - `artifacts`: Hash, filename, format, size, upload timestamp, processing status.
  - `evidence_events`: Normalized schema with source record pointers.
  - `entities`: Extracted entities with masked display values and SHA-256 hashes.
  - `relationships`: Source entity, target entity, link type, confidence, matching reason, artifact references.
  - `action_queue`: Ranked leads with recommended verification actions.
  - `audit_logs`: Timestamped analyst action records.

### 4. Correlation & Mule Account Engine (`cipher_fusion/correlation/`)
- **Shared Identifier Correlation**: Connects entities sharing exact SHA-256 hashes.
- **Cross-Entity Correlation**: Links phone<->IMEI, phone<->complaint, UPI<->account, account<->transaction, IP<->device, APK<->domain, EML<->IP.
- **Time-Window Linking**: Configurable time proximity matching (1h, 6h, 24h default, 7d).
- **Mule Account Metrics**:
  - Multi-hop transfer tracing.
  - Fund velocity calculation (receipt-to-forwarding latency, percentage forwarded, total volume).
  - Fund convergence (N victim accounts -> 1 beneficiary account).
  - Fund splitting (1 account -> N beneficiary accounts).
  - Configurable thresholds (Rapid forwarding < 15 mins, Repeated entity ≥ 3 cases, High-value transfer ≥ ₹25,000, High velocity ≥ 2 hops / 30 mins).

### 5. Risk Scoring Engine (`cipher_fusion/scoring/`)
- Transparent 0–100 risk score breakdown:
  - Transaction Recency (0-20 pts)
  - Number of Linked Cases (0-20 pts)
  - Fund Velocity & Rapid Forwarding (0-20 pts)
  - Repeated Telecom / Device Identifiers (0-15 pts)
  - Shared IP / Subnet Indicators (0-10 pts)
  - Suspicious APK / Domain Indicators (0-10 pts)
  - Weak / Single Source Evidence Penalty (-5 to 0 pts)
- Displays Low (0-39), Medium (40-69), High (70-100) labels with clear bulleted contributing reasons.

### 6. Golden-Hour Action Queue (`cipher_fusion/ui/pages.py`)
- Automatically generates ranked leads based on risk score, fund velocity, and multi-case links.
- Uses responsible action language ("Verify linked beneficiary account", "Preserve CDR entries within 24h window", "Validate device and SIM associations").

### 7. Report Generator (`cipher_fusion/reporting/`)
- **PDF Report Generator**: Uses ReportLab to build a formatted 1-page forensic summary PDF with artifact hashes, key entities, timeline, transaction chain, action queue, and mandatory legal disclaimers.
- **JSON Exporter**: Structured machine-readable export adhering to Pydantic models.

## Key Architectural Principles
- **Read-Only Artifacts**: Original files are never mutated. Derived data points link back via `source_artifact_id` and `source_record_reference`.
- **Explainable Analytics**: No black-box AI outputs. All edges and recommendations display exact matching rules and artifact pointers.
- **Privacy & Masking**: Frontend hides full PII by default unless explicitly unmasked by authorized analysts (tracked in audit log).
- **Offline & Local Execution**: Zero external API dependencies (no live bank, telecom, police, or OSINT calls).
