from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class ArtifactType(str, Enum):
    CDR = "CDR"
    IPDR = "IPDR"
    BANK = "BANK"
    EMAIL = "EMAIL"
    ANDROID = "ANDROID"
    CHAT = "CHAT"
    COMPLAINT = "COMPLAINT"

class EntityType(str, Enum):
    PHONE_NUMBER = "phone_number"
    ACCOUNT_NUMBER = "account_number"
    UPI_ID = "upi_id"
    TRANSACTION_ID = "transaction_id"
    IP_ADDRESS = "ip_address"
    IP_SUBNET = "ip_subnet"
    IMEI = "imei"
    IMSI = "imsi"
    MAC_ADDRESS = "mac_address"
    DEVICE_ID = "device_id"
    APK_PACKAGE = "apk_package"
    CERTIFICATE_HASH = "certificate_hash"
    URL = "url"
    DOMAIN = "domain"
    EMAIL_ADDRESS = "email_address"
    LOCATION = "location"
    COMPLAINT_ID = "complaint_id"

class CaseModel(BaseModel):
    case_id: str
    title: str
    description: Optional[str] = ""
    status: str = "ACTIVE"
    sensitivity_level: str = "OFFICIAL_USE_ONLY"
    created_at: str
    updated_at: Optional[str] = None

    @property
    def case_title(self) -> str:
        return self.title

class ArtifactModel(BaseModel):
    artifact_id: str
    case_id: str
    filename: str
    file_type: ArtifactType
    file_size: int
    sha256: str
    upload_timestamp: str
    processing_status: str = "PROCESSED"
    error_message: Optional[str] = None

    @property
    def original_filename(self) -> str:
        return self.filename

    @property
    def file_hash_sha256(self) -> str:
        return self.sha256

    @property
    def uploaded_at(self) -> str:
        return self.upload_timestamp

    @property
    def source_type(self) -> str:
        return self.file_type.value if hasattr(self.file_type, 'value') else str(self.file_type)

class EntityModel(BaseModel):
    entity_id: str
    case_id: str
    entity_type: EntityType
    masked_value: str
    normalized_value_hash: str
    first_seen: str
    last_seen: str

class NormalizedEventModel(BaseModel):
    event_id: str
    case_id: str
    source_artifact_id: str
    source_record_reference: str
    source_type: str
    timestamp_original: str
    timestamp_utc: str
    entity_type: EntityType
    entity_value_masked: str
    entity_value_hash: str
    related_entity_type: Optional[EntityType] = None
    related_entity_value_masked: Optional[str] = None
    action: str
    amount: Optional[float] = 0.0
    location: Optional[str] = None
    confidence: float = 1.0
    extraction_method: str = "RULE_BASED"
    created_at: str

    @property
    def artifact_id(self) -> str:
        return self.source_artifact_id

    @property
    def event_type(self) -> str:
        return self.entity_type.value if hasattr(self.entity_type, 'value') else str(self.entity_type)

    @property
    def entity_id(self) -> str:
        return self.entity_value_masked

    @property
    def related_entity_id(self) -> Optional[str]:
        return self.related_entity_value_masked

class RelationshipModel(BaseModel):
    relationship_id: str
    source_case_id: str = ""
    target_case_id: str = ""
    source_entity: str
    target_entity: str
    relationship_type: str
    source_artifact_id: str
    source_record_reference: str
    timestamp: str
    matching_reason: str
    confidence: float = 1.0
    risk_indicators: List[str] = Field(default_factory=list)
    hash: str = ""
    created_at: str = ""

    @property
    def source_entity_id(self) -> str:
        return self.source_entity

    @property
    def target_entity_id(self) -> str:
        return self.target_entity

    @property
    def artifact_hash(self) -> str:
        return self.hash

class ActionQueueItem(BaseModel):
    action_id: str
    case_id: str
    priority_rank: int
    lead_type: str
    masked_endpoint: str
    risk_score: int
    reason: str
    last_observed_time: str
    linked_cases_count: int
    total_amount: float
    recommended_action: str
    related_artifact_ids: List[str] = Field(default_factory=list)

class RiskScoreBreakdown(BaseModel):
    total_score: int
    rating: str  # Low, Medium, High
    recency_score: int  # 0-20
    linked_cases_score: int  # 0-20
    fund_velocity_score: int  # 0-20
    telecom_device_score: int  # 0-15
    shared_ip_subnet_score: int  # 0-10
    apk_domain_score: int  # 0-10
    evidence_penalty: int  # -5 to 0
    reasons: List[str]
    confidence: float
    requires_human_verification: bool = True

class AuditLogModel(BaseModel):
    log_id: str
    timestamp: str
    analyst_id: str = "ANALYST_LOCAL"
    action_type: str
    target_identifier: str
    details: str

class InvestigationReportModel(BaseModel):
    case_id: str
    generated_at: str
    disclaimer: str
    artifact_inventory: List[ArtifactModel]
    key_entities: List[Dict[str, Any]]
    unified_timeline: List[NormalizedEventModel]
    transaction_flow_summary: Dict[str, Any]
    risk_score_breakdown: RiskScoreBreakdown
    golden_hour_action_queue: List[ActionQueueItem]
    source_references: List[Dict[str, Any]]
    audit_summary: Dict[str, Any]

