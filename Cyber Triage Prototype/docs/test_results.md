# CIPHER-FUSION: Correlation Engine & Lineage Test Results

## Test Suite Execution Summary
- **Target Component**: Correlation Engine & Lineage Provenance
- **Dataset**: Operation UPI-Shadow Synthetic Dataset (5 connected cases, 7 multi-format artifacts)
- **Test Engine**: `pytest 9.1.1` (Python 3.13)
- **Total Test Cases**: 17
- **Passed**: 17 (100%)
- **Failed**: 0
- **Execution Time**: 7.14 seconds

## Detailed Correlation Relationship Verification

The correlation engine was tested against the full Operation UPI-Shadow synthetic dataset. For 100% of generated relationship edges, the output strictly includes:

1. `source_artifact_id`: Valid artifact reference starting with `ART-`.
2. `source_record_reference`: Row index, line number, or message ID (e.g., `row_1`, `record_1`, `header_from`).
3. `matching_reason`: Explicit non-empty rule explanation string (e.g., `Exact shared identifier (phone_number) across cases CASE-2026-001 and CASE-2026-002`).
4. `confidence`: Floating point value in range `0.0 <= confidence <= 1.0`.
5. `hash`: Valid 64-character SHA-256 hash string for the matching entity identifier.

Zero unexplained relationships were accepted or generated.

## Full Unit Test Suite Summary Table

| Domain | Test Module | Test Case | Status | Lineage & Correlation Validation |
| :--- | :--- | :--- | :--- | :--- |
| **Correlation** | `tests/test_correlation.py` | `test_correlation_engine_upi_shadow_dataset` | PASSED | Verifies `source_artifact_id`, `source_record_reference`, `matching_reason`, `confidence`, and `hash` on all generated relationships. |
| **Correlation** | `tests/test_correlation.py` | `test_exact_hash_correlation` | PASSED | Validates SHA-256 hash matching across cross-case CDR/chat records. |
| **Correlation** | `tests/test_correlation.py` | `test_rapid_forwarding_mule_analysis` | PASSED | Validates fund velocity, rapid forwarding (<15m), and multi-hop transfer metrics. |
| **Database** | `tests/test_database.py` | `test_database_crud` | PASSED | Verifies SQLite schema creation, column migration (`hash`), and CRUD queries. |
| **E2E Scenario** | `tests/test_e2e_demo.py` | `test_e2e_operation_upi_shadow` | PASSED | End-to-end multi-case scenario execution with 7 demo files across 5 cases. |
| **Extraction** | `tests/test_extraction.py` | `test_entity_extractor_text` | PASSED | Regex & rule-based entity extraction from free text complaints and chats. |
| **Hashing** | `tests/test_hashing.py` | `test_calculate_sha256_bytes` | PASSED | Deterministic byte array SHA-256 computation. |
| **Hashing** | `tests/test_hashing.py` | `test_calculate_sha256_file` | PASSED | SHA-256 computation on passive file objects. |
| **Hashing** | `tests/test_hashing.py` | `test_generate_entity_hash` | PASSED | Normalized value SHA-256 hashing. |
| **Ingestion** | `tests/test_ingestion.py` | `test_cdr_ingestion` | PASSED | CDR CSV parsing and artifact model generation. |
| **Ingestion** | `tests/test_ingestion.py` | `test_bank_ingestion` | PASSED | Bank CSV transaction parsing and debit/credit event creation. |
| **Normalization** | `tests/test_normalization.py` | `test_phone_normalization` | PASSED | Indian phone standardizer (+91 format). |
| **Normalization** | `tests/test_normalization.py` | `test_ip_and_subnet_normalization` | PASSED | IPv4 validation & /24 subnet derivation. |
| **Normalization** | `tests/test_normalization.py` | `test_timestamp_normalization` | PASSED | UTC ISO 8601 timestamp conversion. |
| **Normalization** | `tests/test_normalization.py` | `test_identifier_normalization` | PASSED | Lowercasing UPI, emails, domains, and IMEI cleaning. |
| **Reporting** | `tests/test_reporting.py` | `test_pdf_and_json_generation` | PASSED | ReportLab 1-page PDF & JSON report generation. |
| **Risk Scoring** | `tests/test_scoring.py` | `test_risk_scoring_calculation` | PASSED | Transparent 0–100 risk score composition breakdown. |
