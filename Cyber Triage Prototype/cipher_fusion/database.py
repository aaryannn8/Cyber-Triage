import sqlite3
import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from cipher_fusion.config import config
from cipher_fusion.models import (
    CaseModel, ArtifactModel, NormalizedEventModel, EntityModel,
    RelationshipModel, ActionQueueItem, AuditLogModel
)

class Database:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or config.DATABASE_PATH
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Cases Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cases (
                    case_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    status TEXT DEFAULT 'ACTIVE',
                    sensitivity_level TEXT DEFAULT 'OFFICIAL_USE_ONLY',
                    created_at TEXT NOT NULL,
                    updated_at TEXT
                )
            """)

            # Migrations for cases table
            for col, dtype in [("sensitivity_level", "TEXT DEFAULT 'OFFICIAL_USE_ONLY'"), ("updated_at", "TEXT")]:
                try:
                    cursor.execute(f"ALTER TABLE cases ADD COLUMN {col} {dtype}")
                except sqlite3.OperationalError:
                    pass

            # Artifacts Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS artifacts (
                    artifact_id TEXT PRIMARY KEY,
                    case_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    sha256 TEXT NOT NULL,
                    upload_timestamp TEXT NOT NULL,
                    processing_status TEXT DEFAULT 'PROCESSED',
                    error_message TEXT,
                    FOREIGN KEY (case_id) REFERENCES cases (case_id) ON DELETE CASCADE
                )
            """)

            # Entities Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS entities (
                    entity_id TEXT PRIMARY KEY,
                    case_id TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    masked_value TEXT NOT NULL,
                    normalized_value_hash TEXT NOT NULL,
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    FOREIGN KEY (case_id) REFERENCES cases (case_id) ON DELETE CASCADE
                )
            """)

            # Evidence Events Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS evidence_events (
                    event_id TEXT PRIMARY KEY,
                    case_id TEXT NOT NULL,
                    source_artifact_id TEXT NOT NULL,
                    source_record_reference TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    timestamp_original TEXT NOT NULL,
                    timestamp_utc TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    entity_value_masked TEXT NOT NULL,
                    entity_value_hash TEXT NOT NULL,
                    related_entity_type TEXT,
                    related_entity_value_masked TEXT,
                    action TEXT NOT NULL,
                    amount REAL DEFAULT 0.0,
                    location TEXT,
                    confidence REAL DEFAULT 1.0,
                    extraction_method TEXT DEFAULT 'RULE_BASED',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (case_id) REFERENCES cases (case_id) ON DELETE CASCADE,
                    FOREIGN KEY (source_artifact_id) REFERENCES artifacts (artifact_id) ON DELETE CASCADE
                )
            """)

            # Relationships Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS relationships (
                    relationship_id TEXT PRIMARY KEY,
                    source_case_id TEXT DEFAULT '',
                    target_case_id TEXT DEFAULT '',
                    source_entity TEXT NOT NULL,
                    target_entity TEXT NOT NULL,
                    relationship_type TEXT NOT NULL,
                    source_artifact_id TEXT NOT NULL,
                    source_record_reference TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    matching_reason TEXT NOT NULL,
                    confidence REAL DEFAULT 1.0,
                    risk_indicators TEXT DEFAULT '[]',
                    hash TEXT DEFAULT '',
                    created_at TEXT DEFAULT ''
                )
            """)

            # Migrations for relationships table
            for col, dtype in [("source_case_id", "TEXT DEFAULT ''"), ("target_case_id", "TEXT DEFAULT ''"), ("created_at", "TEXT DEFAULT ''"), ("hash", "TEXT DEFAULT ''")]:
                try:
                    cursor.execute(f"ALTER TABLE relationships ADD COLUMN {col} {dtype}")
                except sqlite3.OperationalError:
                    pass

            # Action Queue Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS action_queue (
                    action_id TEXT PRIMARY KEY,
                    case_id TEXT NOT NULL,
                    priority_rank INTEGER NOT NULL,
                    lead_type TEXT NOT NULL,
                    masked_endpoint TEXT NOT NULL,
                    risk_score INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    last_observed_time TEXT NOT NULL,
                    linked_cases_count INTEGER NOT NULL,
                    total_amount REAL NOT NULL,
                    recommended_action TEXT NOT NULL,
                    related_artifact_ids TEXT DEFAULT '[]'
                )
            """)

            # Audit Logs Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    log_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    analyst_id TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    target_identifier TEXT NOT NULL,
                    details TEXT NOT NULL
                )
            """)
            conn.commit()

    # Case Methods
    def insert_case(self, case: CaseModel):
        with self.get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO cases (case_id, title, description, status, sensitivity_level, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (case.case_id, case.title, case.description, case.status, getattr(case, 'sensitivity_level', 'OFFICIAL_USE_ONLY'), case.created_at, getattr(case, 'updated_at', None))
            )
            conn.commit()

    def get_cases(self) -> List[CaseModel]:
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM cases ORDER BY created_at DESC").fetchall()
            return [CaseModel(**dict(row)) for row in rows]

    def get_case(self, case_id: str) -> Optional[CaseModel]:
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM cases WHERE case_id = ?", (case_id,)).fetchone()
            return CaseModel(**dict(row)) if row else None

    # Artifact Methods
    def insert_artifact(self, artifact: ArtifactModel):
        with self.get_connection() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO artifacts 
                   (artifact_id, case_id, filename, file_type, file_size, sha256, upload_timestamp, processing_status, error_message) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (artifact.artifact_id, artifact.case_id, artifact.filename, artifact.file_type.value,
                 artifact.file_size, artifact.sha256, artifact.upload_timestamp, artifact.processing_status, artifact.error_message)
            )
            conn.commit()

    def get_artifacts(self, case_id: Optional[str] = None) -> List[ArtifactModel]:
        with self.get_connection() as conn:
            if case_id:
                rows = conn.execute("SELECT * FROM artifacts WHERE case_id = ? ORDER BY upload_timestamp DESC", (case_id,)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM artifacts ORDER BY upload_timestamp DESC").fetchall()
            return [ArtifactModel(**dict(row)) for row in rows]

    # Entity Methods
    def insert_entities(self, entities: List[EntityModel]):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for e in entities:
                cursor.execute(
                    """INSERT OR REPLACE INTO entities 
                       (entity_id, case_id, entity_type, masked_value, normalized_value_hash, first_seen, last_seen)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (e.entity_id, e.case_id, e.entity_type.value if hasattr(e.entity_type, 'value') else str(e.entity_type),
                     e.masked_value, e.normalized_value_hash, e.first_seen, e.last_seen)
                )
            conn.commit()

    def get_entities(self, case_id: Optional[str] = None) -> List[EntityModel]:
        with self.get_connection() as conn:
            if case_id:
                rows = conn.execute("SELECT * FROM entities WHERE case_id = ?", (case_id,)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM entities").fetchall()
            return [EntityModel(**dict(row)) for row in rows]

    # Event Methods
    def insert_events(self, events: List[NormalizedEventModel]):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for event in events:
                cursor.execute(
                    """INSERT OR REPLACE INTO evidence_events 
                       (event_id, case_id, source_artifact_id, source_record_reference, source_type, 
                        timestamp_original, timestamp_utc, entity_type, entity_value_masked, entity_value_hash, 
                        related_entity_type, related_entity_value_masked, action, amount, location, confidence, extraction_method, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (event.event_id, event.case_id, event.source_artifact_id, event.source_record_reference, event.source_type,
                     event.timestamp_original, event.timestamp_utc, str(event.entity_type.value if hasattr(event.entity_type, 'value') else event.entity_type),
                     event.entity_value_masked, event.entity_value_hash,
                     str(event.related_entity_type.value if event.related_entity_type and hasattr(event.related_entity_type, 'value') else event.related_entity_type) if event.related_entity_type else None,
                     event.related_entity_value_masked, event.action, event.amount, event.location, event.confidence, event.extraction_method, event.created_at)
                )
            conn.commit()

    def get_events(self, case_id: Optional[str] = None) -> List[NormalizedEventModel]:
        with self.get_connection() as conn:
            if case_id:
                rows = conn.execute("SELECT * FROM evidence_events WHERE case_id = ? ORDER BY timestamp_utc ASC", (case_id,)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM evidence_events ORDER BY timestamp_utc ASC").fetchall()
            return [NormalizedEventModel(**dict(row)) for row in rows]

    # Relationship Methods
    def insert_relationships(self, relationships: List[RelationshipModel]):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for rel in relationships:
                cursor.execute(
                    """INSERT OR REPLACE INTO relationships 
                       (relationship_id, source_case_id, target_case_id, source_entity, target_entity, relationship_type, source_artifact_id, source_record_reference, timestamp, matching_reason, confidence, risk_indicators, hash, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (rel.relationship_id, getattr(rel, 'source_case_id', ''), getattr(rel, 'target_case_id', ''),
                     rel.source_entity, rel.target_entity, rel.relationship_type,
                     rel.source_artifact_id, rel.source_record_reference, rel.timestamp, rel.matching_reason,
                     rel.confidence, json.dumps(rel.risk_indicators), rel.hash, getattr(rel, 'created_at', ''))
                )
            conn.commit()

    def get_relationships(self, case_id: Optional[str] = None, mode: str = "ALL") -> List[RelationshipModel]:
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM relationships").fetchall()
            all_rels = []
            for r in rows:
                d = dict(r)
                d['risk_indicators'] = json.loads(d['risk_indicators']) if d['risk_indicators'] else []
                d['hash'] = d.get('hash', '')
                d['source_case_id'] = d.get('source_case_id', '')
                d['target_case_id'] = d.get('target_case_id', '')
                d['created_at'] = d.get('created_at', '')
                all_rels.append(RelationshipModel(**d))

            if not case_id or mode == "ALL":
                return all_rels

            if mode == "Current Case Only":
                return [
                    r for r in all_rels 
                    if (r.source_case_id == case_id and r.target_case_id in [case_id, '']) or 
                       (r.target_case_id == case_id and r.source_case_id in [case_id, '']) or
                       (not r.source_case_id and "CROSS_CASE_LINK" not in r.risk_indicators)
                ]
            elif mode == "Current Case + Related Cases":
                # Find connected cases sharing entities with active case_id
                cross_rels = [r for r in all_rels if "CROSS_CASE_LINK" in r.risk_indicators]
                connected_cases = {case_id}
                for r in cross_rels:
                    if r.source_case_id == case_id and r.target_case_id:
                        connected_cases.add(r.target_case_id)
                    elif r.target_case_id == case_id and r.source_case_id:
                        connected_cases.add(r.source_case_id)

                return [
                    r for r in all_rels 
                    if (r.source_case_id in connected_cases or r.target_case_id in connected_cases)
                ]
            elif mode == "Cross-Case Correlation":
                return [r for r in all_rels if "CROSS_CASE_LINK" in r.risk_indicators]

            return all_rels

    # Action Queue Methods
    def insert_action_items(self, items: List[ActionQueueItem]):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for item in items:
                cursor.execute(
                    """INSERT OR REPLACE INTO action_queue 
                       (action_id, case_id, priority_rank, lead_type, masked_endpoint, risk_score, reason, last_observed_time, linked_cases_count, total_amount, recommended_action, related_artifact_ids)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (item.action_id, item.case_id, item.priority_rank, item.lead_type, item.masked_endpoint,
                     item.risk_score, item.reason, item.last_observed_time, item.linked_cases_count,
                     item.total_amount, item.recommended_action, json.dumps(item.related_artifact_ids))
                )
            conn.commit()

    def get_action_items(self, case_id: Optional[str] = None) -> List[ActionQueueItem]:
        with self.get_connection() as conn:
            if case_id:
                rows = conn.execute("SELECT * FROM action_queue WHERE case_id = ? ORDER BY priority_rank ASC", (case_id,)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM action_queue ORDER BY priority_rank ASC").fetchall()
            res = []
            for r in rows:
                d = dict(r)
                d['related_artifact_ids'] = json.loads(d['related_artifact_ids']) if d['related_artifact_ids'] else []
                res.append(ActionQueueItem(**d))
            return res

    # Audit Logging Methods
    def log_audit(self, audit: AuditLogModel):
        with self.get_connection() as conn:
            conn.execute(
                """INSERT INTO audit_logs (log_id, timestamp, analyst_id, action_type, target_identifier, details)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (audit.log_id, audit.timestamp, audit.analyst_id, audit.action_type, audit.target_identifier, audit.details)
            )
            conn.commit()

    def get_audit_logs(self) -> List[AuditLogModel]:
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM audit_logs ORDER BY timestamp DESC").fetchall()
            return [AuditLogModel(**dict(row)) for row in rows]

db = Database()
