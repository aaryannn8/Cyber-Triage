import streamlit as st

st.set_page_config(
    page_title="CIPHER-FUSION | Cyber Fraud Analysis & Digital Artifact Correlator",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

from cipher_fusion.ui import (
    CUSTOM_CSS, render_header, render_disclaimer,
    page_overview, page_cases, page_ingestion, page_entities,
    page_graph, page_timeline, page_action_queue, page_reports, page_audit
)
from cipher_fusion.database import db

# Inject Custom CSS Theme
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Render Global Header & Mandatory Disclaimer
render_header()
render_disclaimer()

# Initialize Session State
if 'active_case_id' not in st.session_state:
    existing_cases = db.get_cases()
    if existing_cases:
        st.session_state['active_case_id'] = existing_cases[0].case_id
    else:
        st.session_state['active_case_id'] = "CASE-2026-001"

active_case_id = st.session_state['active_case_id']

# Sidebar Navigation
st.sidebar.markdown("## ⚡ CIPHER-FUSION")
st.sidebar.markdown(f"**Active Case:** `{active_case_id}`")
st.sidebar.divider()

selected_tab = st.sidebar.radio(
    "Navigation Menu",
    options=[
        "📌 Overview",
        "📁 Case Management",
        "📥 Artifact Ingestion",
        "🔍 Entity Explorer",
        "🌐 Evidence Graph",
        "⏱️ Timeline",
        "⚡ Golden-Hour Queue",
        "📑 Reports Generator",
        "🛡️ Audit Log & Health"
    ]
)

st.sidebar.divider()
st.sidebar.caption("🔒 Law Enforcement Local Prototype | Zero External APIs")

# Router Dispatch
if selected_tab == "📌 Overview":
    page_overview(active_case_id)
elif selected_tab == "📁 Case Management":
    page_cases()
elif selected_tab == "📥 Artifact Ingestion":
    page_ingestion(active_case_id)
elif selected_tab == "🔍 Entity Explorer":
    page_entities(active_case_id)
elif selected_tab == "🌐 Evidence Graph":
    page_graph(active_case_id)
elif selected_tab == "⏱️ Timeline":
    page_timeline(active_case_id)
elif selected_tab == "⚡ Golden-Hour Queue":
    page_action_queue(active_case_id)
elif selected_tab == "📑 Reports Generator":
    page_reports(active_case_id)
elif selected_tab == "🛡️ Audit Log & Health":
    page_audit()
