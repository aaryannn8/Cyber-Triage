# CIPHER-FUSION: Threat Model & Security Controls

## Threat Modeling Overview
CIPHER-FUSION is designed specifically for air-gapped or local secure law enforcement investigator workstation deployment. The primary security objectives are:
1. Prevent execution of malicious uploaded payloads (e.g. malicious Android APKs, script files, macros).
2. Ensure strict data privacy by masking PII/sensitive fields by default and auditing unmasking events.
3. Protect database integrity against SQL injection and tamper attempts.
4. Eliminate external data leaks by forbidding any outbound network traffic to live APIs.

## Threat Vectors & Countermeasures

| Threat Vector | Severity | Potential Impact | Security Control / Countermeasure |
| :--- | :--- | :--- | :--- |
| **Malicious Code Execution** | Critical | Malware execution via uploaded APK, macro, or script file. | Files are treated strictly as **passive data streams**. APK analysis is limited to text/JSON metadata parsing. Uploaded binaries are never unpacked, compiled, or executed. |
| **Data Leak / Outbound Exfiltration** | Critical | Unauthorized exfiltration of evidence or target PII. | Air-gapped local deployment. No network API calls to external police, telecom, bank, OSINT, or cloud endpoints. |
| **SQL Injection** | High | Database compromise, data corruption, or unauthorized deletion. | 100% parameterized queries via SQLite standard abstractions. No dynamic string concatenation in SQL queries. |
| **PII Exposure / Unauthorized Snooping** | High | Exposure of confidential phone, bank, or identity records in logs/UI. | Frontend displays masked values (`+91 98****3210`) by default. Unmasking actions require explicit analyst confirmation and are permanently recorded in the immutable audit log. |
| **Evidence Tampering / Missing Lineage** | High | Inability to establish chain of custody or verify data integrity. | SHA-256 hash computed immediately on upload. Derived events maintain strict foreign key references (`source_artifact_id`, `source_record_reference`). |
| **Over-Promising / Unsubstantiated Accusation** | Medium | Misinterpreting risk scores as legal proof of guilt or automatic conviction. | Disclaimer enforced across UI and PDF reports: *"Forensic-ready investigative summary; final investigative and legal decisions remain with authorized personnel."* Action language strictly uses verification recommendations. |

## Data Sanitization & Input Validation
- File extension & magic bytes validation prior to ingestion.
- Max file size limits enforced (default 50 MB per file).
- Path traversal protection: User-provided filenames are sanitized (`os.path.basename` enforcement). Original files stored using UUID/SHA-256 filenames.

## Audit Logging System
The `audit_logs` table logs all security-relevant analyst actions:
- Timestamp (UTC)
- Analyst ID / Session ID
- Action Type (`UPLOAD_ARTIFACT`, `ANALYZE_CASE`, `UNMASK_PII`, `GENERATE_REPORT`, `EXPORT_DATA`)
- Target Identifier / Artifact SHA-256
- Justification / Context
