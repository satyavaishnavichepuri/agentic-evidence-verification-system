"""
Builds the Question -> Claim -> Evidence -> Source graph shown in the
Investigation Workspace and Evidence Explorer.
"""
from __future__ import annotations

from .models import EvidenceGraph, GraphEdge, GraphNode, Investigation
from .storage import store


def build_evidence_graph(inv: Investigation) -> EvidenceGraph:
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []

    q_id = f"question:{inv.id}"
    nodes.append(GraphNode(id=q_id, kind="question", label=inv.question))

    evidence_by_id = {e.id: e for e in inv.evidence}
    seen_sources: set[str] = set()

    for claim in inv.claims:
        nodes.append(
            GraphNode(id=claim.id, kind="claim", label=claim.text, status=claim.status.value)
        )
        edges.append(GraphEdge(source=q_id, target=claim.id))

        for eid in claim.evidence_ids:
            item = evidence_by_id.get(eid)
            if not item:
                continue
            label = item.snippet[:90] + ("..." if len(item.snippet) > 90 else "")
            nodes.append(
                GraphNode(id=item.id, kind="evidence", label=label, status=item.stance.value)
            )
            edges.append(GraphEdge(source=claim.id, target=item.id))

            if item.source_id not in seen_sources:
                seen_sources.add(item.source_id)
                source = store.get_source(item.source_id)
                title = source.title if source else item.source_id
                nodes.append(GraphNode(id=item.source_id, kind="source", label=title))
            edges.append(GraphEdge(source=item.id, target=item.source_id))

    return EvidenceGraph(nodes=nodes, edges=edges)
