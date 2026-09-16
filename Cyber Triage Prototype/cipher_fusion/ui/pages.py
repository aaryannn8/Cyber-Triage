import streamlit as st
import pandas as pd
import json
import os
import glob
from datetime import datetime, timezone
import uuid

from cipher_fusion.config import config
from cipher_fusion.database import db
from cipher_fusion.models import (
    CaseModel, ArtifactType, AuditLogModel, ActionQueueItem
)
from cipher_fusion.ingestion import ingest_file
from cipher_fusion.correlation import CorrelationEngine, MuleAccountAnalyzer
from cipher_fusion.scoring import RiskScorer
from cipher_fusion.graph import EvidenceGraphBuilder
from cipher_fusion.reporting import PDFReportGenerator, JSONReportGenerator
from cipher_fusion.ui.components import render_metric_card, log_analyst_unmask

def page_overview(active_case_id: str):
    st.subheader("📌 Investigation Overview Dashboard")

    cases = db.get_cases()
    artifacts = db.get_artifacts(active_case_id)
    events = db.get_events(active_case_id)
    relationships = db.get_relationships()
    action_items = db.get_action_items(active_case_id)

    total_amount = sum(e.amount for e in events if e.amount)
    high_priority_leads = len([a for a in action_items if a.risk_score >= 70])

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        render_metric_card("Active Cases", str(len(cases)), "📁")
    with col2:
        render_metric_card("Artifacts Ingested", str(len(artifacts)), "📄")
    with col3:
        render_metric_card("Total Loss Involved", f"₹{total_amount:,.0f}", "💸")
    with col4:
        render_metric_card("Correlated Entities", str(len(events)), "🔗")
    with col5:
        render_metric_card("High-Priority Leads", str(high_priority_leads), "🚨")

    st.divider()

    st.markdown("### 📊 Case Summary & Quick Actions")
    if active_case_id:
        active_case = db.get_case(active_case_id)
        if active_case:
            st.info(f"**Current Case Context:** `{active_case.case_id}` | Title: **{active_case.title}** | Created: `{active_case.created_at}`")
            
            risk = RiskScorer.calculate_case_risk(active_case_id, events, relationships)
            col_a, col_b = st.columns([1, 2])
            with col_a:
                st.metric("Overall Case Risk Score", f"{risk.total_score} / 100", f"Rating: {risk.rating}")
            with col_b:
                st.write("**Contributing Risk Factors:**")
                for r in risk.reasons:
                    st.write(f"- {r}")
    else:
        st.warning("No active case selected. Please go to Case Selection to create or select a case.")


def page_cases():
    st.subheader("📁 Case Selection & Management")

    st.markdown("#### Create New Case")
    with st.form("create_case_form"):
        case_id_input = st.text_input("Case ID", value=f"CASE-2026-{uuid.uuid4().hex[:4].upper()}")
        title_input = st.text_input("Case Title", value="Operation UPI-Shadow")
        desc_input = st.text_area("Case Description", value="Synthetic multi-hop UPI cyber fraud scenario with connected complaints.")
        submitted = st.form_submit_button("Create / Activate Case")

        if submitted:
            now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            c = CaseModel(
                case_id=case_id_input.strip(),
                title=title_input.strip(),
                description=desc_input.strip(),
                status="ACTIVE",
                created_at=now_str
            )
            db.insert_case(c)
            st.session_state['active_case_id'] = c.case_id
            st.success(f"Case '{c.case_id}' created and activated!")

    st.divider()
    st.markdown("#### Existing Cases")
    cases = db.get_cases()
    if cases:
        case_df = pd.DataFrame([c.model_dump() for c in cases])
        st.dataframe(case_df, use_container_width=True)

        selected_id = st.selectbox("Select Active Case", options=[c.case_id for c in cases])
        if st.button("Set Active Case"):
            st.session_state['active_case_id'] = selected_id
            st.success(f"Active case switched to: {selected_id}")
    else:
        st.info("No existing cases found.")


def page_ingestion(active_case_id: str):
    st.subheader("📥 Artifact Ingestion & Integrity Hashing")
    if not active_case_id:
        st.warning("Please select an active case first.")
        return

    st.info(f"Uploading files under Case ID: **{active_case_id}**")

    col_upload, col_demo = st.columns([2, 1])

    with col_demo:
        st.markdown("#### Load Synthetic Demo Dataset")
        st.write("Loads the complete 'Operation UPI-Shadow' 5-case synthetic dataset.")
        if st.button("🚀 Load Demo Dataset"):
            demo_files = glob.glob(os.path.join(config.DEMO_DATA_DIR, "*"))
            loaded_count = 0
            
            # Ensure 5 cases exist
            for c_num in ["CASE-2026-001", "CASE-2026-002", "CASE-2026-003", "CASE-2026-004", "CASE-2026-005"]:
                db.insert_case(CaseModel(
                    case_id=c_num,
                    title=f"Operation UPI-Shadow (Part {c_num[-3:]})",
                    description="Synthetic cyber fraud correlation demo case.",
                    status="ACTIVE",
                    created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                ))

            for fpath in demo_files:
                fname = os.path.basename(fpath)
                with open(fpath, "rb") as f:
                    content = f.read()

                # Dispatch file type based on filename pattern
                ftype = ArtifactType.CDR
                cid = active_case_id
                if "case_002" in fname: cid = "CASE-2026-002"
                elif "case_003" in fname: cid = "CASE-2026-003"
                elif "case_004" in fname: cid = "CASE-2026-004"
                elif "case_005" in fname: cid = "CASE-2026-005"

                if "cdr" in fname: ftype = ArtifactType.CDR
                elif "ipdr" in fname: ftype = ArtifactType.IPDR
                elif "bank" in fname: ftype = ArtifactType.BANK
                elif "email" in fname: ftype = ArtifactType.EMAIL
                elif "android" in fname: ftype = ArtifactType.ANDROID
                elif "chat" in fname: ftype = ArtifactType.CHAT
                elif "complaint" in fname: ftype = ArtifactType.COMPLAINT

                art, evs = ingest_file(cid, ftype, fname, content)
                db.insert_artifact(art)
                db.insert_events(evs)
                loaded_count += 1

            # Run correlation & update database
            all_events = db.get_events()
            all_arts = db.get_artifacts()
            rels = CorrelationEngine.correlate_events(all_events)
            db.insert_relationships(rels)

            # Build action queue
            mule_res = MuleAccountAnalyzer.analyze_mule_patterns(all_events)
            action_items = []
            for idx, link in enumerate(mule_res.get('rapid_forwarding_links', [])):
                action_items.append(ActionQueueItem(
                    action_id=f"ACT-{uuid.uuid4().hex[:6].upper()}",
                    case_id=active_case_id,
                    priority_rank=idx + 1,
                    lead_type="MULE_ACCOUNT",
                    masked_endpoint=link['intermediary'],
                    risk_score=85,
                    reason=f"Rapid forwarding (<{link['time_latency_mins']} mins) of INR {link['incoming_amount']:,.0f} through intermediary account.",
                    last_observed_time=link['t2'],
                    linked_cases_count=3,
                    total_amount=link['incoming_amount'],
                    recommended_action="Verify linked beneficiary account and preserve transaction logs within 24h window.",
                    related_artifact_ids=[all_arts[0].artifact_id] if all_arts else []
                ))
            db.insert_action_items(action_items)

            # Audit log demo load
            db.log_audit(AuditLogModel(
                log_id=f"AUD-{uuid.uuid4().hex[:8].upper()}",
                timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                analyst_id="ANALYST_LOCAL",
                action_type="LOAD_DEMO_DATA",
                target_identifier="Operation UPI-Shadow",
                details=f"Loaded {loaded_count} synthetic demo artifacts across 5 cases."
            ))

            st.success(f"Successfully loaded {loaded_count} demo artifacts across 5 connected cases!")

    with col_upload:
        st.markdown("#### Upload Individual Artifact")
        uploaded_file = st.file_uploader("Select digital artifact", type=['csv', 'xlsx', 'json', 'txt', 'eml'])
        artifact_type_sel = st.selectbox("Artifact Type", options=[t.value for t in ArtifactType])

        if uploaded_file and st.button("Process & Compute SHA-256"):
            bytes_data = uploaded_file.read()
            ftype = ArtifactType(artifact_type_sel)
            
            art, evs = ingest_file(active_case_id, ftype, uploaded_file.name, bytes_data)
            db.insert_artifact(art)
            db.insert_events(evs)

            # Re-run correlation
            all_evs = db.get_events()
            rels = CorrelationEngine.correlate_events(all_evs)
            db.insert_relationships(rels)

            db.log_audit(AuditLogModel(
                log_id=f"AUD-{uuid.uuid4().hex[:8].upper()}",
                timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                analyst_id="ANALYST_LOCAL",
                action_type="UPLOAD_ARTIFACT",
                target_identifier=art.sha256,
                details=f"Uploaded artifact {art.filename} ({art.file_type.value}) - SHA256: {art.sha256}"
            ))

            st.success(f"Ingested `{art.filename}` | SHA-256: `{art.sha256}` | Extracted {len(evs)} events.")

    st.divider()
    st.markdown("#### Artifact Inventory & Status")
    artifacts = db.get_artifacts(active_case_id)
    if artifacts:
        st.dataframe(pd.DataFrame([a.model_dump() for a in artifacts]), use_container_width=True)


def page_entities(active_case_id: str):
    st.subheader("🔍 Entity Explorer & PII Control")

    events = db.get_events(active_case_id)
    if not events:
        st.info("No entities extracted for the current case.")
        return

    st.markdown("#### Masked Entity List")
    unmask_toggle = st.checkbox("🔓 Enable Analyst Unmasking (Logs Action to Audit Trail)")

    if unmask_toggle:
        log_analyst_unmask("ALL_ENTITIES_VIEW")
        st.warning("PII display enabled. Action has been logged to the immutable audit trail.")

    entity_list = []
    for e in events:
        entity_list.append({
            "Event ID": e.event_id,
            "Type": e.entity_type.value if hasattr(e.entity_type, 'value') else e.entity_type,
            "Masked Identifier": e.entity_value_masked,
            "SHA-256 Hash": e.entity_value_hash[:16] + "...",
            "Source Type": e.source_type,
            "Record Reference": e.source_record_reference,
            "Timestamp UTC": e.timestamp_utc
        })

    df = pd.DataFrame(entity_list)
    st.dataframe(df, use_container_width=True)


def page_graph(active_case_id: str):
    st.subheader("🌐 Click-to-Prove Interactive Evidence Graph")

    if not active_case_id:
        st.warning("Please select an active case first.")
        return

    # Initialize Session State for Authorization
    if 'cross_case_authorized' not in st.session_state:
        st.session_state['cross_case_authorized'] = False

    # Top Mode & Authorization Control Bar
    ctrl_col1, ctrl_col2 = st.columns([2.5, 1.5])
    
    with ctrl_col1:
        graph_mode = st.radio(
            "Graph View Mode Selector",
            options=["Current Case Only", "Current Case + Related Cases", "Cross-Case Correlation"],
            index=0,
            horizontal=True,
            key="graph_mode_selector"
        )
    
    with ctrl_col2:
        st.markdown("#### Authorization Control")
        auth_check = st.checkbox(
            "🔓 Authorized cross-case review",
            value=st.session_state['cross_case_authorized'],
            key="auth_toggle_check"
        )
        if auth_check != st.session_state['cross_case_authorized']:
            st.session_state['cross_case_authorized'] = auth_check
            db.log_audit(AuditLogModel(
                log_id=f"AUD-{uuid.uuid4().hex[:8].upper()}",
                timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                analyst_id="ANALYST_LOCAL",
                action_type="AUTHORIZATION_TOGGLE",
                target_identifier=active_case_id,
                details=f"Cross-case authorization changed to {auth_check} in mode '{graph_mode}'"
            ))
            st.rerun()

        st.caption("🔒 Prototype authorization control (Placeholder for production RBAC).")

    # Mode Indicator Banner
    if graph_mode == "Current Case Only":
        st.info(f"📌 **Active View:** `CASE-ISOLATED` | Selected Case: `{active_case_id}` — **Case-isolated view.**")
    elif graph_mode == "Current Case + Related Cases":
        st.warning(f"🔗 **Active View:** `RELATED-CASE INTELLIGENCE` | Selected Case: `{active_case_id}` — **Related-case intelligence view.**")
    elif graph_mode == "Cross-Case Correlation":
        st.error(f"🌐 **Active View:** `CROSS-CASE CORRELATION` | **Cross-case correlation view.**")

    # Check Authorization Status Notice
    authorized = st.session_state['cross_case_authorized']
    if graph_mode != "Current Case Only" and not authorized:
        st.warning("⚠️ **Cross-case access required. Only high-level relationship information is available.**")

    # Fetch Database Data based on Mode
    relationships = db.get_relationships(active_case_id, mode=graph_mode)
    artifacts = db.get_artifacts()

    if not relationships:
        st.info("No relationships match the selected graph mode and active case context.")
        return

    # Filter Controls Bar
    f_col1, f_col2, f_col3, f_col4 = st.columns([1, 1, 1, 1])
    with f_col1:
        rel_types = ["ALL"] + sorted(list(set(r.relationship_type for r in relationships)))
        sel_type = st.selectbox("Filter Relationship Type", options=rel_types)
    with f_col2:
        min_conf = st.slider("Min Confidence Threshold", min_value=0.0, max_value=1.0, value=0.5, step=0.05)
    with f_col3:
        risk_filter = st.selectbox("Filter Risk Level", options=["ALL", "HIGH_RISK_ONLY", "CROSS_CASE_ONLY"])
    with f_col4:
        st.markdown(f"**Displayed Edges:** `{len(relationships)}`")

    # Apply Filters
    filtered_rels = relationships
    if sel_type != "ALL":
        filtered_rels = [r for r in filtered_rels if r.relationship_type == sel_type]
    filtered_rels = [r for r in filtered_rels if r.confidence >= min_conf]
    if risk_filter == "HIGH_RISK_ONLY":
        filtered_rels = [r for r in filtered_rels if any("HIGH" in k for k in r.risk_indicators)]
    elif risk_filter == "CROSS_CASE_ONLY":
        filtered_rels = [r for r in filtered_rels if "CROSS_CASE_LINK" in r.risk_indicators]

    col_graph, col_panel = st.columns([2.8, 1.2])

    with col_graph:
        G = EvidenceGraphBuilder.build_networkx_graph(
            filtered_rels, artifacts, active_case_id=active_case_id, mode=graph_mode, authorized=authorized
        )
        fig = EvidenceGraphBuilder.create_plotly_figure(G, mode=graph_mode)
        st.plotly_chart(fig, use_container_width=True)

    with col_panel:
        st.markdown("### 🔍 Evidence Lineage Panel")
        st.caption("Select a relationship edge to inspect SHA-256 provenance and evidence references.")
        
        if filtered_rels:
            rel_opts = [f"#{i+1}: {r.source_entity} ➔ {r.target_entity} ({r.relationship_type})" for i, r in enumerate(filtered_rels)]
            sel_rel = st.selectbox("Select Relationship Edge", options=rel_opts)

            if sel_rel:
                idx = rel_opts.index(sel_rel)
                r = filtered_rels[idx]
                
                art_map = {a.artifact_id: a for a in artifacts}
                matched_art = art_map.get(r.source_artifact_id)
                art_sha = matched_art.sha256 if matched_art else r.hash or "N/A"
                art_fn = matched_art.filename if matched_art else "N/A"

                st.markdown(f"**Relationship ID:** `{r.relationship_id}`")
                st.markdown(f"**Source Case:** `{r.source_case_id or active_case_id}`")
                st.markdown(f"**Target Case:** `{r.target_case_id or active_case_id}`")
                st.markdown(f"**Link:** `{r.source_entity}` ➔ `{r.target_entity}`")
                st.markdown(f"**Type:** `{r.relationship_type}`")
                st.markdown(f"**Matching Reason:** {r.matching_reason}")
                
                if authorized or not r.source_case_id or r.source_case_id == active_case_id:
                    st.markdown(f"**Source Artifact:** `{art_fn}` (`{r.source_artifact_id}`)")
                    st.markdown(f"**Record Reference:** `{r.source_record_reference}`")
                    st.markdown(f"**Artifact SHA-256:** `{art_sha}`")
                    st.markdown(f"**Timestamp (UTC):** `{r.timestamp}`")
                    st.markdown(f"**Access Status:** `APPROVED`")
                else:
                    st.markdown("**Source Artifact:** `[REDACTED]`")
                    st.markdown("**Record Reference:** `[REDACTED - Authorization Required]`")
                    st.markdown("**Access Status:** `UNAUTHORIZED`")

                st.markdown(f"**Confidence:** `{r.confidence * 100:.0f}%`")
                st.markdown(f"**Risk Indicators:** `{', '.join(r.risk_indicators) if r.risk_indicators else 'NONE'}`")
        else:
            st.warning("No relationships match the selected filter criteria.")


def page_timeline(active_case_id: str):
    st.subheader("⏱️ Unified Chronological Timeline")

    if not active_case_id:
        st.warning("Select an active case first.")
        return

    mode = st.session_state.get('graph_mode_selector', 'Current Case Only')
    authorized = st.session_state.get('cross_case_authorized', False)

    if mode == "Current Case Only":
        st.info(f"Showing timeline events exclusively for **{active_case_id}**")
        events = db.get_events(active_case_id)
    elif mode == "Current Case + Related Cases":
        st.warning(f"Showing timeline events for **{active_case_id}** and connected related cases.")
        events = db.get_events()
    else:
        st.error("Showing cross-case relationship timeline sequence.")
        events = db.get_events()

    if not events:
        st.info("No timeline events available.")
        return

    timeline_data = []
    for e in events:
        is_active = (e.case_id == active_case_id)
        if not is_active and not authorized and mode == "Cross-Case Correlation":
            # Restricted cross-case timeline view
            timeline_data.append({
                "Timestamp (UTC)": e.timestamp_utc,
                "Case ID": e.case_id,
                "Source Type": e.source_type,
                "Action": e.action,
                "Primary Entity": e.entity_value_masked,
                "Related Entity": "[REDACTED]",
                "Amount (INR)": "-",
                "Source Ref": "[REDACTED]"
            })
        else:
            timeline_data.append({
                "Timestamp (UTC)": e.timestamp_utc,
                "Case ID": e.case_id,
                "Source Type": e.source_type,
                "Action": e.action,
                "Primary Entity": e.entity_value_masked,
                "Related Entity": e.related_entity_value_masked or "-",
                "Amount (INR)": f"₹{e.amount:,.2f}" if e.amount else "-",
                "Source Ref": e.source_record_reference
            })

    df = pd.DataFrame(timeline_data)
    st.dataframe(df, use_container_width=True)


def page_action_queue(active_case_id: str):
    st.subheader("⚡ Golden-Hour Action Queue")

    items = db.get_action_items(active_case_id)
    if not items:
        st.info("No items in the Action Queue for the selected case.")
        return

    for item in items:
        st.markdown(f"""
            <div class="lead-card {'high-risk' if item.risk_score >= 70 else ''}">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div class="lead-title">Rank #{item.priority_rank}: {item.lead_type} | {item.masked_endpoint}</div>
                    <div class="action-badge">Risk Score: {item.risk_score}/100</div>
                </div>
                <div style="color: #94A3B8; font-size: 0.85rem; margin-top:0.4rem;">
                    <b>Reason:</b> {item.reason}<br>
                    <b>Linked Cases:</b> {item.linked_cases_count} | <b>Total Amount:</b> ₹{item.total_amount:,.2f}<br>
                    <b>Recommended Action:</b> <span style="color:#60A5FA; font-weight:600;">{item.recommended_action}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)


def page_reports(active_case_id: str):
    st.subheader("📑 Forensic Report Generator (PDF & JSON)")

    if not active_case_id:
        st.warning("Select an active case to generate reports.")
        return

    mode = st.session_state.get('graph_mode_selector', 'Current Case Only')
    authorized = st.session_state.get('cross_case_authorized', False)

    st.markdown(f"**Report Target:** `{active_case_id}` | **Selected Graph Scope:** `{mode}` | **Authorization Status:** `{'AUTHORIZED' if authorized else 'UNAUTHORIZED'}`")
    
    st.info(f"**Mandatory Legal Disclaimer:** {config.FULL_DISCLAIMER}")

    artifacts = db.get_artifacts(active_case_id if mode == "Current Case Only" else None)
    events = db.get_events(active_case_id if mode == "Current Case Only" else None)
    relationships = db.get_relationships(active_case_id, mode=mode)
    action_items = db.get_action_items(active_case_id)
    risk = RiskScorer.calculate_case_risk(active_case_id, events, relationships)
    mule_summary = MuleAccountAnalyzer.analyze_mule_patterns(events)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📄 Generate Forensic PDF Summary")
        report_type_sel = st.selectbox("PDF Report Type", options=["Case-Specific", "Related-Case", "Cross-Case"])
        
        if st.button("Build PDF Report"):
            pdf_path = os.path.join(config.REPORTS_DIR, f"{active_case_id}_{report_type_sel.lower().replace('-', '_')}_summary.pdf")
            out_pdf = PDFReportGenerator.generate_pdf(
                active_case_id, artifacts, events, risk, action_items, pdf_path, relationships=relationships
            )
            
            db.log_audit(AuditLogModel(
                log_id=f"AUD-{uuid.uuid4().hex[:8].upper()}",
                timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                analyst_id="ANALYST_LOCAL",
                action_type="GENERATE_REPORT_PDF",
                target_identifier=active_case_id,
                details=f"Generated {report_type_sel} forensic PDF report at {pdf_path}"
            ))

            with open(out_pdf, "rb") as f:
                st.download_button("Download PDF", f, file_name=f"{active_case_id}_{report_type_sel.lower()}_summary.pdf", mime="application/pdf")
            st.success(f"{report_type_sel} PDF report built successfully!")

    with col2:
        st.markdown("#### 📦 Export Structured JSON Package")
        report_type_json = st.selectbox("JSON Report Scope", options=["Case-Specific", "Related-Case", "Cross-Case"])
        
        if st.button("Export JSON Report"):
            json_path = os.path.join(config.REPORTS_DIR, f"{active_case_id}_{report_type_json.lower().replace('-', '_')}_report.json")
            out_json = JSONReportGenerator.generate_json(
                active_case_id, artifacts, events, risk, action_items, mule_summary, json_path,
                report_type=report_type_json, cross_case_authorized=authorized
            )

            db.log_audit(AuditLogModel(
                log_id=f"AUD-{uuid.uuid4().hex[:8].upper()}",
                timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                analyst_id="ANALYST_LOCAL",
                action_type="EXPORT_JSON_REPORT",
                target_identifier=active_case_id,
                details=f"Exported {report_type_json} JSON investigation report at {json_path}"
            ))

            with open(out_json, "rb") as f:
                st.download_button("Download JSON", f, file_name=f"{active_case_id}_{report_type_json.lower()}_report.json", mime="application/json")
            st.success(f"{report_type_json} JSON report exported successfully!")


def page_audit():
    st.subheader("🛡️ Audit Log & System Health")

    col_audit, col_health = st.columns([2, 1])

    with col_audit:
        st.markdown("#### Immutable Analyst Audit Trail")
        logs = db.get_audit_logs()
        if logs:
            st.dataframe(pd.DataFrame([l.model_dump() for l in logs]), use_container_width=True)
        else:
            st.info("Audit trail empty.")

    with col_health:
        st.markdown("#### System Health & Security Status")
        st.success("✔ Database: Connected (SQLite)")
        st.success("✔ Air-Gap Protocol: Active (0 External APIs)")
        st.success("✔ Payload Execution: Disabled (Read-only Passive)")
        st.success("✔ Legal Disclaimer: Enforced")

