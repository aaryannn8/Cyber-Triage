import networkx as nx
import plotly.graph_objects as go
from typing import List, Dict, Any, Tuple, Optional
from cipher_fusion.models import NormalizedEventModel, RelationshipModel, ArtifactModel

# Color Map by Node Category & Entity Type
NODE_COLOR_MAP = {
    "selected_case": "#3B82F6",    # Blue: selected-case nodes
    "related_case": "#F97316",     # Orange: related-case nodes
    "shared_entity": "#8B5CF6",    # Purple: shared-entity nodes
    "case_node": "#64748B",        # Gray: case nodes in cross-case mode
    "high_risk": "#EF4444",        # Red: high-priority indicators
    "verified": "#10B981",         # Green: verified data relationships
    "possible": "#F59E0B",         # Yellow: possible relationships
    "DEFAULT": "#3B82F6"
}

ENTITY_TYPE_COLORS = {
    "phone_number": "#3B82F6",
    "account_number": "#10B981",
    "upi_id": "#8B5CF6",
    "ip_address": "#F59E0B",
    "ip_subnet": "#D97706",
    "device_id": "#EC4899",
    "apk_package": "#EF4444",
    "domain": "#6366F1",
    "complaint_id": "#64748B",
    "email_address": "#06B6D4",
    "DEFAULT": "#94A3B8"
}

class EvidenceGraphBuilder:
    @staticmethod
    def build_networkx_graph(
        relationships: List[RelationshipModel], 
        artifacts: List[ArtifactModel],
        active_case_id: Optional[str] = None,
        mode: str = "Current Case Only",
        authorized: bool = False
    ) -> nx.DiGraph:
        G = nx.DiGraph()
        artifact_hash_map = {a.artifact_id: a.sha256 for a in artifacts}

        # Filter relationships based on graph mode
        if active_case_id and mode == "Current Case Only":
            filtered_rels = [
                r for r in relationships
                if (r.source_case_id == active_case_id and r.target_case_id in [active_case_id, '']) or
                   (r.target_case_id == active_case_id and r.source_case_id in [active_case_id, '']) or
                   (not r.source_case_id and "CROSS_CASE_LINK" not in r.risk_indicators)
            ]
        elif active_case_id and mode == "Current Case + Related Cases":
            cross_rels = [r for r in relationships if "CROSS_CASE_LINK" in r.risk_indicators]
            connected_cases = {active_case_id}
            for r in cross_rels:
                if r.source_case_id == active_case_id and r.target_case_id:
                    connected_cases.add(r.target_case_id)
                elif r.target_case_id == active_case_id and r.source_case_id:
                    connected_cases.add(r.source_case_id)

            filtered_rels = [
                r for r in relationships
                if (r.source_case_id in connected_cases or r.target_case_id in connected_cases)
            ]
        elif mode == "Cross-Case Correlation":
            filtered_rels = [r for r in relationships if "CROSS_CASE_LINK" in r.risk_indicators or r.source_case_id != r.target_case_id]
            if not filtered_rels:
                filtered_rels = relationships
        else:
            filtered_rels = relationships

        if mode == "Cross-Case Correlation":
            # Mode 3: Build high-level Case-to-Shared-Entity Graph
            for rel in filtered_rels:
                src_case = rel.source_case_id or active_case_id or "CASE-PRIMARY"
                tgt_case = rel.target_case_id or "CASE-RELATED"
                shared_entity = rel.source_entity

                # Add Case nodes
                if not G.has_node(src_case):
                    G.add_node(src_case, label=src_case, category="case_node", node_type="Case")
                if not G.has_node(tgt_case):
                    G.add_node(tgt_case, label=tgt_case, category="case_node", node_type="Case")

                # Add Shared Entity node
                if not G.has_node(shared_entity):
                    G.add_node(shared_entity, label=shared_entity, category="shared_entity", node_type="Shared Entity")

                # Add edges Case -> Shared Entity
                G.add_edge(
                    src_case, shared_entity,
                    relationship_id=rel.relationship_id,
                    relationship_type=rel.relationship_type,
                    matching_reason=rel.matching_reason,
                    source_artifact_id=rel.source_artifact_id,
                    source_record_reference=rel.source_record_reference if authorized else "[REDACTED - Authorization Required]",
                    timestamp=rel.timestamp,
                    confidence=rel.confidence,
                    artifact_sha256=artifact_hash_map.get(rel.source_artifact_id, "N/A") if authorized else "[REDACTED]",
                    risk_indicators=rel.risk_indicators,
                    source_case=src_case,
                    target_case=tgt_case
                )
                G.add_edge(
                    shared_entity, tgt_case,
                    relationship_id=f"{rel.relationship_id}-REVERSE",
                    relationship_type=rel.relationship_type,
                    matching_reason=rel.matching_reason,
                    source_artifact_id=rel.source_artifact_id,
                    source_record_reference=rel.source_record_reference if authorized else "[REDACTED - Authorization Required]",
                    timestamp=rel.timestamp,
                    confidence=rel.confidence,
                    artifact_sha256=artifact_hash_map.get(rel.source_artifact_id, "N/A") if authorized else "[REDACTED]",
                    risk_indicators=rel.risk_indicators,
                    source_case=src_case,
                    target_case=tgt_case
                )
            return G

        # Modes 1 & 2: Entity Graph Construction
        shared_entities = set()
        if mode == "Current Case + Related Cases":
            for rel in relationships:
                if "CROSS_CASE_LINK" in rel.risk_indicators:
                    shared_entities.add(rel.source_entity)
                    shared_entities.add(rel.target_entity)

        for rel in filtered_rels:
            src = rel.source_entity
            tgt = rel.target_entity
            art_sha = artifact_hash_map.get(rel.source_artifact_id, "N/A")

            # Determine category for src and tgt
            src_cat = "selected_case"
            if src in shared_entities:
                src_cat = "shared_entity"
            elif rel.source_case_id and rel.source_case_id != active_case_id:
                src_cat = "related_case"

            tgt_cat = "selected_case"
            if tgt in shared_entities:
                tgt_cat = "shared_entity"
            elif rel.target_case_id and rel.target_case_id != active_case_id:
                tgt_cat = "related_case"

            if not G.has_node(src):
                G.add_node(src, label=src, category=src_cat, case_id=rel.source_case_id or active_case_id)
            if not G.has_node(tgt):
                G.add_node(tgt, label=tgt, category=tgt_cat, case_id=rel.target_case_id or active_case_id)

            G.add_edge(
                src, tgt,
                relationship_id=rel.relationship_id,
                relationship_type=rel.relationship_type,
                matching_reason=rel.matching_reason,
                source_artifact_id=rel.source_artifact_id,
                source_record_reference=rel.source_record_reference if (authorized or not rel.source_case_id or rel.source_case_id == active_case_id) else "[REDACTED - Authorization Required]",
                timestamp=rel.timestamp,
                confidence=rel.confidence,
                artifact_sha256=art_sha,
                risk_indicators=rel.risk_indicators,
                source_case=rel.source_case_id or active_case_id,
                target_case=rel.target_case_id or active_case_id
            )

        return G

    @staticmethod
    def create_plotly_figure(G: nx.DiGraph, mode: str = "Current Case Only") -> go.Figure:
        if len(G.nodes) == 0:
            fig = go.Figure()
            fig.update_layout(
                title=dict(text="No graph data available for current case and filters.", font=dict(color="#94A3B8")),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
            )
            return fig

        pos = nx.spring_layout(G, k=0.6, iterations=50, seed=42)

        edge_x, edge_y = [], []
        edge_text = []
        annotations = []

        for edge in G.edges(data=True):
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            data = edge[2]
            rel_type = data.get('relationship_type', 'LINK')
            edge_text.append(f"<b>{rel_type}</b><br>{data.get('matching_reason')}<br>Confidence: {data.get('confidence', 1.0)*100:.0f}%")

            if rel_type in ["TRANSFER_TO", "CALLED", "EMAILED", "CONNECTED_IP", "INSTALLED_ON"]:
                ax = x0 + (x1 - x0) * 0.7
                ay = y0 + (y1 - y0) * 0.7
                annotations.append(dict(
                    x=ax, y=ay,
                    ax=x0, ay=y0,
                    xref='x', yref='y', axref='x', ayref='y',
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1.2,
                    arrowwidth=1.5,
                    arrowcolor='#94A3B8'
                ))

        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=1.5, color='#64748B'),
            hoverinfo='text',
            text=edge_text,
            mode='lines',
            showlegend=False
        )

        # Categorize nodes for distinct scatter traces & legend
        categories = {}
        for node, data in G.nodes(data=True):
            cat = data.get("category", "selected_case")
            categories.setdefault(cat, []).append(node)

        category_labels = {
            "selected_case": "Selected Case Entities (Blue)",
            "related_case": "Related Case Entities (Orange)",
            "shared_entity": "Shared Cross-Case Entities (Purple)",
            "case_node": "Case Nodes (Gray)",
            "high_risk": "High Risk Endpoints (Red)"
        }

        data_traces = [edge_trace]

        for cat, nodes in categories.items():
            nx_vals, ny_vals, labels, hover_texts = [], [], [], []
            for n in nodes:
                x, y = pos[n]
                nx_vals.append(x)
                ny_vals.append(y)
                labels.append(n)
                hover_texts.append(f"<b>{n}</b><br>Category: {cat}<br>Connections: {G.degree(n)}")

            color = NODE_COLOR_MAP.get(cat, NODE_COLOR_MAP["DEFAULT"])
            size = 26 if cat in ["shared_entity", "case_node"] else 20

            data_traces.append(go.Scatter(
                x=nx_vals, y=ny_vals,
                mode='markers+text',
                hoverinfo='text',
                text=labels,
                textposition="top center",
                hovertext=hover_texts,
                name=category_labels.get(cat, cat.title()),
                marker=dict(
                    color=color,
                    size=size,
                    line=dict(width=2, color='#0F172A')
                )
            ))

        fig = go.Figure(
            data=data_traces,
            layout=go.Layout(
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom", y=1.02,
                    xanchor="right", x=1,
                    font=dict(color="#E2E8F0", size=10),
                    bgcolor="rgba(15, 23, 42, 0.7)"
                ),
                hovermode='closest',
                margin=dict(b=20, l=10, r=10, t=50),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=600,
                annotations=annotations
            )
        )
        return fig
