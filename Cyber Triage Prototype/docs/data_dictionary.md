# CIPHER-FUSION: Data Dictionary & Data Models

## 1. Supported Artifact Types & Fields

### CDR (Call Detail Records)
- `caller_number`: String (Phone number initiating call)
- `receiver_number`: String (Phone number receiving call)
- `timestamp`: String (Original localized timestamp)
- `duration_seconds`: Integer (Call duration in seconds)
- `cell_tower`: String (Cell tower / BTS location ID)
- `call_type`: String (`VOICE`, `SMS`, `INCOMING`, `OUTGOING`)

### IPDR (IP Detail Records)
- `phone_number`: String (Subscriber phone number)
- `ip_address`: String (IPv4 address assigned)
- `timestamp`: String (Session timestamp)
- `destination_domain`: String (Destination hostname / domain)
- `device_id`: String (Device hardware identifier)
- `session_duration`: Integer (Session duration in seconds)

### Bank / UPI Transactions
- `transaction_id`: String (Unique bank transaction ID)
- `timestamp`: String (Transaction timestamp)
- `sender_account`: String (Debited account number)
- `receiver_account`: String (Credited account number)
- `upi_id`: String (VPA / UPI handle e.g. `user@upi`)
- `amount`: Float (Transaction currency amount in INR)
- `bank_reference`: String (UTR / Bank reference number)
- `transaction_type`: String (`UPI_PAY`, `IMPS`, `NEFT`, `ATM_WITHDRAWAL`)

### Email Headers (EML)
- `From`: String (Header From address)
- `To`: String (Header To address)
- `Date`: String (Header Date string)
- `Subject`: String (Email subject line)
- `Message-ID`: String (Unique RFC 822 Message-ID)
- `Received`: String (Parsed hop headers)
- `Reply-To`: String (Reply-To email address)
- `originating_ip`: String (Extracted client IP address)

### Android System / App Metadata
- `package_name`: String (Application package name e.g. `com.fake.bank`)
- `app_name`: String (Display app name)
- `permissions`: List[String] (Requested app permissions)
- `certificate_hash`: String (APK Signing Certificate SHA-256)
- `embedded_domains`: List[String] (Domains extracted from DEX strings)
- `sha256`: String (APK file SHA-256 hash)
- `file_name`: String (APK filename)
- `created_time`: String (File creation timestamp)

### Chat Exports
- `message_id`: String (Chat message identifier)
- `timestamp`: String (Message timestamp)
- `sender`: String (Phone number or display handle)
- `receiver`: String (Recipient handle/group)
- `message_text`: String (Raw message content)
- `attachment_name`: String (Optional attachment filename)

### Complaint Text
- `complaint_id`: String (Unique complaint reference number)
- `case_id`: String (Associated police case ID)
- `timestamp`: String (Filing timestamp)
- `complaint_text`: String (Narrative description of incident)
- `reported_amount`: Float (Financial loss amount)
- `location`: String (Victim city/state/pincode)

---

## 2. Core Normalized Database Tables

### `cases`
- `case_id` (TEXT PRIMARY KEY): e.g. `CASE-2026-UPI-SHADOW`
- `title` (TEXT): Case title
- `description` (TEXT): Overview summary
- `status` (TEXT): `ACTIVE`, `ARCHIVED`, `CLOSED`
- `created_at` (TEXT): UTC timestamp ISO 8601

### `artifacts`
- `artifact_id` (TEXT PRIMARY KEY): Unique UUID
- `case_id` (TEXT FOREIGN KEY): Linked case
- `filename` (TEXT): Original filename
- `file_type` (TEXT): `CDR`, `IPDR`, `BANK`, `EML`, `ANDROID`, `CHAT`, `COMPLAINT`
- `file_size` (INTEGER): Size in bytes
- `sha256` (TEXT): Calculated SHA-256 hash
- `upload_timestamp` (TEXT): UTC timestamp
- `processing_status` (TEXT): `PENDING`, `PROCESSED`, `FAILED`
- `error_message` (TEXT): Exception trace if failed

### `evidence_events`
- `event_id` (TEXT PRIMARY KEY): Unique event UUID
- `case_id` (TEXT FOREIGN KEY): Associated case ID
- `source_artifact_id` (TEXT FOREIGN KEY): Originating artifact
- `source_record_reference` (TEXT): Row index, line number, or message ID
- `source_type` (TEXT): CDR, Bank, IPDR, etc.
- `timestamp_original` (TEXT): Raw input timestamp
- `timestamp_utc` (TEXT): Converted UTC ISO 8601 string
- `entity_type` (TEXT): Primary entity type
- `entity_value_masked` (TEXT): Masked display string
- `entity_value_hash` (TEXT): Deterministic SHA-256 hash of normalized value
- `related_entity_type` (TEXT): Secondary entity type
- `related_entity_value_masked` (TEXT): Secondary entity masked value
- `action` (TEXT): e.g., `CALL_MADE`, `FUNDS_TRANSFERRED`, `IP_CONNECTED`, `APP_INSTALLED`
- `amount` (REAL): Transaction amount if applicable
- `location` (TEXT): Tower/City/IP subnet
- `confidence` (REAL): 0.0 to 1.0 confidence score
- `extraction_method` (TEXT): `REGEX`, `JSON_PARSER`, `CSV_ROW`
- `created_at` (TEXT): UTC timestamp

### `relationships`
- `relationship_id` (TEXT PRIMARY KEY)
- `source_entity` (TEXT): Masked value or hash
- `target_entity` (TEXT): Masked value or hash
- `relationship_type` (TEXT): `SHARED_PHONE`, `TRANSFER_TO`, `CONNECTED_IP`, `INSTALLED_APK`, etc.
- `source_artifact_id` (TEXT)
- `source_record_reference` (TEXT)
- `timestamp` (TEXT)
- `matching_reason` (TEXT): Plain text explanation of correlation
- `confidence` (REAL)
- `risk_indicators` (TEXT): JSON array of risk tags

### `action_queue`
- `action_id` (TEXT PRIMARY KEY)
- `case_id` (TEXT)
- `priority_rank` (INTEGER)
- `lead_type` (TEXT): `MULE_ACCOUNT`, `REPEATED_PHONE`, `SUSPICIOUS_APK`, `SHARED_SUBNET`
- `masked_endpoint` (TEXT)
- `risk_score` (INTEGER)
- `reason` (TEXT)
- `last_observed_time` (TEXT)
- `linked_cases_count` (INTEGER)
- `total_amount` (REAL)
- `recommended_action` (TEXT)
- `related_artifact_ids` (TEXT)

### `audit_logs`
- `log_id` (TEXT PRIMARY KEY)
- `timestamp` (TEXT)
- `analyst_id` (TEXT)
- `action_type` (TEXT)
- `target_identifier` (TEXT)
- `details` (TEXT)
