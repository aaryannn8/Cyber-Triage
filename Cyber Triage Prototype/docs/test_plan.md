# CIPHER-FUSION: Comprehensive Test Plan

## Test Strategy Overview
The test plan ensures 100% test coverage across normalization algorithms, entity extraction regexes, artifact ingestion parsers, graph correlation logic, fund velocity math, risk scoring breakdowns, PDF/JSON report generation, and end-to-end integration scenario.

## Test Modules & Scope

| Module | Test File | Key Test Cases Covered |
| :--- | :--- | :--- |
| **Normalization** | `tests/test_normalization.py` | - Indian phone number formats (`+91`, `0`, spaces, hyphens) -> standardized `+91XXXXXXXXXX`<br>- IPv4 subnet derivation (`198.51.100.10` -> `198.51.100.0/24`)<br>- ISO & string timestamp conversion to UTC ISO 8601<br>- Lowercasing UPI handles (`User@UPI` -> `user@upi`) and domains<br>- IMEI/IMSI separator sanitization |
| **Ingestion** | `tests/test_ingestion.py` | - SHA-256 calculation verification<br>- Handling corrupt / malformed CSV, JSON, XLSX, EML files gracefully<br>- Read-only artifact file storage verification<br>- File type validation and error reporting |
| **Extraction** | `tests/test_extraction.py` | - Regex entity extraction across 17 entity types<br>- Complaint text NLP/regex extraction (phone, bank account, UPI, amount, date)<br>- EML email header extraction (From, To, Date, Subject, Message-ID, Received IP) |
| **Correlation & Mule Analysis** | `tests/test_correlation.py` | - Shared entity SHA-256 correlation across artifacts and cases<br>- Time-window filtering (1h, 6h, 24h, 7d)<br>- Mule account metrics: Rapid forwarding (<15m), fund velocity, fund convergence (N->1), fund splitting (1->N) |
| **Risk Scoring** | `tests/test_scoring.py` | - Risk score 0-100 composition breakdown calculation<br>- Rating assignment (Low, Medium, High)<br>- Contributing reason string generation<br>- Weak source evidence score penalty |
| **Reporting** | `tests/test_reporting.py` | - PDF report generation (ReportLab) structure and table layout<br>- Mandatory legal disclaimer inclusion check<br>- JSON structured report validation against Pydantic models |
| **End-to-End Demo** | `tests/test_e2e_demo.py` | - Full multi-case scenario ("Operation UPI-Shadow") loading 7 synthetic demo files<br>- Graph node/edge count verification<br>- Mule account detection verification<br>- Golden-Hour Queue lead rank verification |

## Execution Command
To run all tests locally:
```bash
pytest tests/ -v
```
