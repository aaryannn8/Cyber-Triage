import streamlit as st
from cipher_fusion.config import config
from cipher_fusion.models import AuditLogModel
from cipher_fusion.database import db
from datetime import datetime, timezone
import uuid

def render_header():
    st.markdown("""
        <div class="main-header">
            <div class="main-title">⚡ CIPHER-FUSION</div>
            <div class="main-subtitle">AI-Powered Unified Cyber Fraud Analysis & Digital Artifact Correlator</div>
        </div>
    """, unsafe_allow_html=True)

def render_disclaimer():
    st.markdown(f"""
        <div class="disclaimer-banner">
            ⚠️ <b>MANDATORY LEGAL DISCLAIMER</b>: {config.FULL_DISCLAIMER}
        </div>
    """, unsafe_allow_html=True)

def render_metric_card(label: str, value: str, icon: str = "📊"):
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{icon} {value}</div>
            <div class="metric-label">{label}</div>
        </div>
    """, unsafe_allow_html=True)

def log_analyst_unmask(target_identifier: str):
    log_entry = AuditLogModel(
        log_id=f"AUD-{uuid.uuid4().hex[:8].upper()}",
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        analyst_id="ANALYST_LOCAL",
        action_type="UNMASK_PII",
        target_identifier=target_identifier,
        details=f"Analyst requested unmasking display for target: {target_identifier}"
    )
    db.log_audit(log_entry)
