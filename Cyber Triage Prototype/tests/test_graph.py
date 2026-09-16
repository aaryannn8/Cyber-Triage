import pytest
import networkx as nx
from cipher_fusion.models import RelationshipModel, ArtifactModel, ArtifactType
from cipher_fusion.graph import EvidenceGraphBuilder

def test_build_networkx_graph_directional():
    art = ArtifactModel(
        artifact_id="ART-1", case_id="CASE-1", filename="cdr.csv", file_type=ArtifactType.CDR,
        file_size=200, sha256="abc123sha256", upload_timestamp="2026-09-15T10:00:00Z"
    )
    rel1 = RelationshipModel(
        relationship_id="REL-1", source_entity="+91 98****0001", target_entity="+91 98****1111",
        relationship_type="CALLED", source_artifact_id="ART-1", source_record_reference="row_1",
        timestamp="2026-09-15T10:00:00Z", matching_reason="CDR call log", confidence=1.0, hash="abc123hash"
    )
    rel2 = RelationshipModel(
        relationship_id="REL-2", source_entity="ACC-****0100", target_entity="ACC-****0888",
        relationship_type="TRANSFER_TO", source_artifact_id="ART-1", source_record_reference="row_2",
        timestamp="2026-09-15T10:30:00Z", matching_reason="Bank transfer", confidence=1.0, hash="def456hash"
    )

    G = EvidenceGraphBuilder.build_networkx_graph([rel1, rel2], [art])

    assert isinstance(G, nx.DiGraph)
    assert len(G.nodes) == 4
    assert len(G.edges) == 2
    assert G.has_edge("+91 98****0001", "+91 98****1111")
    assert G.has_edge("ACC-****0100", "ACC-****0888")

    edge_data = G.get_edge_data("ACC-****0100", "ACC-****0888")
    assert edge_data['relationship_type'] == "TRANSFER_TO"
    assert edge_data['artifact_sha256'] == "abc123sha256"
    assert edge_data['source_record_reference'] == "row_2"

def test_create_plotly_figure():
    G = nx.DiGraph()
    G.add_edge("+91 98****0001", "+91 98****1111", relationship_type="CALLED", matching_reason="CDR call log", confidence=1.0)
    fig = EvidenceGraphBuilder.create_plotly_figure(G)
    assert fig is not None
    assert len(fig.data) == 2
    assert len(fig.layout.annotations) == 1
