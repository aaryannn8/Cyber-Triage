import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from cipher_fusion.config import config
from cipher_fusion.models import ArtifactModel, NormalizedEventModel, RiskScoreBreakdown, ActionQueueItem

class PDFReportGenerator:
    @staticmethod
    def generate_pdf(
        case_id: str,
        artifacts: List[ArtifactModel],
        events: List[NormalizedEventModel],
        risk: RiskScoreBreakdown,
        action_queue: List[ActionQueueItem],
        output_path: str,
        relationships: Optional[List[Any]] = None
    ) -> str:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
        )

        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'DocTitle', parent=styles['Heading1'],
            fontName='Helvetica-Bold', fontSize=15, leading=18, textColor=colors.HexColor('#0F172A')
        )
        subtitle_style = ParagraphStyle(
            'DocSubtitle', parent=styles['Normal'],
            fontName='Helvetica', fontSize=8, leading=11, textColor=colors.HexColor('#475569')
        )
        section_heading = ParagraphStyle(
            'SectionHeading', parent=styles['Heading2'],
            fontName='Helvetica-Bold', fontSize=10, leading=13, textColor=colors.HexColor('#1E3A8A'),
            spaceBefore=6, spaceAfter=3
        )
        body_style = ParagraphStyle(
            'Body', parent=styles['Normal'],
            fontName='Helvetica', fontSize=7.5, leading=9.5, textColor=colors.HexColor('#1E293B')
        )
        disclaimer_style = ParagraphStyle(
            'Disclaimer', parent=styles['Normal'],
            fontName='Helvetica-Oblique', fontSize=6.5, leading=8.5, textColor=colors.HexColor('#991B1B')
        )

        elements = []

        # 1. Header & Title Block
        elements.append(Paragraph("CIPHER-FUSION: FORENSIC INVESTIGATIVE SUMMARY", title_style))
        elements.append(Paragraph(f"<b>Case ID:</b> {case_id} | <b>Generated:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')} | <b>Classification:</b> LAW ENFORCEMENT ONLY", subtitle_style))
        elements.append(Spacer(1, 4))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E1'), spaceAfter=4))

        # 2. Risk Score Banner & Reasons
        risk_color = colors.HexColor('#EF4444') if risk.rating == 'High' else (colors.HexColor('#F59E0B') if risk.rating == 'Medium' else colors.HexColor('#10B981'))
        risk_html = f"<b>Risk Score:</b> <font color='{risk_color.hexval()}'><b>{risk.total_score}/100 ({risk.rating.upper()})</b></font> | <b>Risk Reasons:</b> {'; '.join(risk.reasons[:3])}"
        elements.append(Paragraph(risk_html, body_style))
        elements.append(Spacer(1, 4))

        # 3. Artifact Inventory Table
        elements.append(Paragraph("1. ARTIFACT INVENTORY & CHAIN OF CUSTODY (SHA-256 HASHES)", section_heading))
        art_table_data = [["Artifact ID", "Type", "Filename", "SHA-256 Hash", "Status"]]
        for a in artifacts[:6]:
            hash_display = f"{a.sha256[:10]}...{a.sha256[-10:]}" if len(a.sha256) > 20 else a.sha256
            art_table_data.append([a.artifact_id, a.file_type.value, a.filename[:22], hash_display, a.processing_status])

        if not artifacts:
            art_table_data.append(["N/A", "NONE", "No artifacts uploaded", "-", "-"])

        t_art = Table(art_table_data, colWidths=[65, 50, 120, 235, 60])
        t_art.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F1F5F9')),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 7),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
            ('TOPPADDING', (0,0), (-1,-1), 1.5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 1.5),
        ]))
        elements.append(t_art)
        elements.append(Spacer(1, 4))

        # 4. Graph & Evidence Summary
        rel_list = relationships or []
        cross_case_cnt = len([r for r in rel_list if getattr(r, 'risk_indicators', []) and 'CROSS_CASE_LINK' in r.risk_indicators])
        elements.append(Paragraph(f"2. EVIDENCE GRAPH & CORRELATION SUMMARY (Total Edges: {len(rel_list)} | Cross-Case Links: {cross_case_cnt})", section_heading))

        # 5. Golden-Hour Action Queue
        elements.append(Paragraph("3. GOLDEN-HOUR ACTION QUEUE (PRIORITIZED LEADS)", section_heading))
        queue_data = [["Rank", "Lead Type", "Endpoint", "Risk", "Recommended Verification Action"]]
        for item in action_queue[:3]:
            queue_data.append([str(item.priority_rank), item.lead_type, item.masked_endpoint, str(item.risk_score), item.recommended_action[:50]])

        if len(queue_data) == 1:
            queue_data.append(["1", "N/A", "None", "0", "No high-priority leads queued."])

        t_queue = Table(queue_data, colWidths=[30, 85, 100, 35, 280])
        t_queue.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#EFF6FF')),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 7),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#DBEAFE')),
            ('TOPPADDING', (0,0), (-1,-1), 1.5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 1.5),
        ]))
        elements.append(t_queue)
        elements.append(Spacer(1, 4))

        # 6. Timeline & Source References Table
        elements.append(Paragraph("4. KEY UNIFIED TIMELINE EVENTS & SOURCE REFERENCES", section_heading))
        timeline_data = [["UTC Timestamp", "Source", "Primary Entity", "Action", "Amount", "Source Ref"]]
        for ev in events[:4]:
            amt_str = f"INR {ev.amount:,.0f}" if ev.amount > 0 else "-"
            timeline_data.append([
                ev.timestamp_utc[:19].replace("T", " "),
                ev.source_type,
                ev.entity_value_masked,
                ev.action,
                amt_str,
                ev.source_record_reference
            ])

        if len(timeline_data) == 1:
            timeline_data.append(["-", "NONE", "No events logged", "-", "-", "-"])

        t_time = Table(timeline_data, colWidths=[90, 45, 125, 115, 60, 95])
        t_time.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F8FAFC')),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 7),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
            ('TOPPADDING', (0,0), (-1,-1), 1.5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 1.5),
        ]))
        elements.append(t_time)
        elements.append(Spacer(1, 6))

        # 7. Mandatory Legal Disclaimer
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#EF4444'), spaceAfter=3))
        elements.append(Paragraph(f"<b>MANDATORY LEGAL DISCLAIMER:</b> {config.FULL_DISCLAIMER}", disclaimer_style))

        doc.build(elements)
        return output_path
