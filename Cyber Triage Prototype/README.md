# CIPHER-FUSION
### AI-Powered Unified Cyber Fraud Analysis & Digital Artifact Correlator

> **Mandatory Disclaimer**: Forensic-ready investigative summary generated from supplied synthetic artifacts. Findings require review and verification by authorized personnel. This prototype does not independently establish identity, intent, guilt, or legal admissibility.

---

## 📌 Overview

**CIPHER-FUSION** is a local, offline web application designed for authorized law-enforcement investigators to ingest, parse, normalize, and correlate fragmented digital artifacts from cyber-fraud cases. It combines rule-based deterministic correlation, graph analytics, fund-flow velocity tracking, explainable risk scoring, and a Golden-Hour Action Queue to convert chaotic evidence into structured investigative leads.

---

## 🎯 Key Features

- **7 Ingestion Formats Supported**:
  1. Call Detail Records (CDR - CSV/Excel)
  2. IP Detail Records (IPDR - CSV/JSON)
  3. Bank & UPI Transactions (CSV/Excel)
  4. Email Headers (EML parse only)
  5. Android App Metadata (JSON/TXT)
  6. Chat Transcripts (JSON/TXT)
  7. Police Complaint Narratives (JSON/TXT)
- **Automatic Read-Only Hashing**: Computes SHA-256 hashes immediately upon upload to preserve chain-of-custody.
- **Normalizers & 17 Entity Types**: Standardizes Indian phone numbers (+91), IP subnets (/24), ISO-UTC timestamps, UPI/email handles, IMEI/IMSI identifiers, and APK package details.
- **Case-Aware Interactive Evidence Graph**:
  - **Mode 1 (`Current Case Only`)**: Isolated graph displaying entities and relationships belonging exclusively to the active case. Unrelated cases are strictly excluded.
  - **Mode 2 (`Current Case + Related Cases`)**: Includes active case and connected cases sharing verified identifiers (highlighted in Orange/Purple).
  - **Mode 3 (`Cross-Case Correlation`)**: High-level bipartite view of Case Nodes (Gray) and Shared Entity Nodes (Purple).
  - **Authorization Placeholder**: Integrates analyst authorization controls for cross-case evidence disclosure, backed by immutable audit trail logging.
- **Mule-Account & Fund Velocity Engine**: Automatically highlights rapid forwarding (<15m), multi-hop transfers, fund convergence (N victim accounts -> 1 beneficiary), fund splitting (1 account -> N beneficiaries), and high-value transfers (≥₹25,000).
- **Explainable 0–100 Risk Score**: Transparent scoring breakdown across 7 dimensions (recency, case links, fund velocity, telecom reuse, IP subnet, APK domain, evidence weight).
- **Golden-Hour Action Queue**: Prioritized investigative actions (e.g. *"Verify linked beneficiary account"*, *"Preserve CDR entries within 24h window"*).
- **1-Page Forensic PDF & JSON Export**: Instant PDF summary with audit hash table and mandatory legal disclaimers.
- **PII Masking & Analyst Audit Logging**: Masks sensitive data by default (`+91 98****3210`); logs analyst unmask requests and export actions in a permanent audit log.

---

## 🚀 Quick Start Instructions

### Prerequisites
- Python 3.11 or higher
- pip package manager

### 1. Installation
Clone or navigate to the project directory and install required dependencies:
```bash
pip install -r requirements.txt
```

### 2. Run the Web Application
Launch the Streamlit web app:
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

### 3. Run Automated Tests
Execute unit and end-to-end tests:
```bash
pytest tests/ -v
```

---

## 🎬 Demo Scenario: "Operation UPI-Shadow"

The repository includes synthetic data for a 5-case cyber fraud scenario in `data/demo/`:
- **Scenario**: A victim receives a fake banking call (CDR), installs a malicious APK (Android metadata), and loses ₹42,000 via a UPI transfer. Funds move through 2 mule accounts within 12 minutes. IPDR logs and complaint narratives connect 4 additional victim cases sharing phone numbers, IP subnets, UPI handles, and APK domains.

**Steps to Demo**:
1. Open the **Case Selection** tab in CIPHER-FUSION and select `"Operation UPI-Shadow"`.
2. Navigate to **Artifact Ingestion** and click **"Load Demo Dataset"**.
3. View the SHA-256 hashes and normalized records.
4. Explore the **Evidence Graph**, **Timeline**, **Mule Account Analysis**, and **Golden-Hour Action Queue**.
5. Go to **Reports** and generate the 1-page Forensic PDF summary.

---

## 🏗️ Project Architecture

```
cipher-fusion/
├── app.py                     # Streamlit Application Entrypoint
├── requirements.txt           # Python Dependencies
├── cipher_fusion/
│   ├── config.py              # Configuration & Thresholds
│   ├── database.py            # SQLite Database Abstraction
│   ├── models.py              # Pydantic Schemas & Constants
│   ├── security.py            # Masking, Hashing & Audit Log
│   ├── ingestion/             # 7 Artifact Parsers & Loaders
│   ├── normalization/         # Standardizers (Phone, IP, Time)
│   ├── extraction/            # Entity Extractors
│   ├── correlation/           # Correlation Engine & Mule Logic
│   ├── graph/                 # NetworkX / Plotly Graph Builders
│   ├── scoring/               # 0-100 Risk Score Breakdown Logic
│   ├── reporting/             # ReportLab PDF & JSON Generator
│   └── ui/                    # Streamlit Tabs & Custom CSS
├── data/
│   ├── demo/                  # Synthetic Demo Files (5 cases)
│   └── uploads/               # Local Read-Only Storage
├── docs/                      # Architecture, Threat Model, Data Dict, Test Plan
└── tests/                     # Unit & E2E Test Suite
```

---

## ⚠ Important Limitations

- **Synthetic Data**: Prototype uses purely synthetic or anonymized sample data.
- **Offline Local Prototype**: Does not connect to live police, telecom, bank, or government databases (CFCFRMS, NCRP, OSINT).
- **Human Verification Required**: Does not establish legal guilt, identify criminal suspects conclusively, or issue legal orders.
- **Metadata Analysis Only**: Does not execute APK binaries, macros, or dynamic malware samples.
