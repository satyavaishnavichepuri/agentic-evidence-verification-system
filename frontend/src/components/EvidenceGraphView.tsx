import { useEffect, useState } from "react";
import { endpoints } from "../api/client";
import type { EvidenceGraph, GraphNode } from "../types";

const KIND_COLOR: Record<string, string> = {
  question: "border-accent-500/40 bg-accent-500/10 text-accent-300",
  claim: "border-base-600 bg-base-800 text-ink-100",
  evidence: "border-base-700 bg-base-850 text-ink-300",
  source: "border-base-600 bg-base-800 text-ink-200",
};

export default function EvidenceGraphView({ investigationId }: { investigationId: string }) {
  const [graph, setGraph] = useState<EvidenceGraph | null>(null);

  useEffect(() => {
    endpoints.getInvestigationGraph(investigationId).then((res) => setGraph(res.data));
  }, [investigationId]);

  if (!graph) return <div className="text-xs text-ink-400">Loading graph...</div>;

  const byKind = (kind: string): GraphNode[] => graph.nodes.filter((n) => n.kind === kind);
  const childrenOf = (id: string) => graph.edges.filter((e) => e.source === id).map((e) => e.target);

  const questionNode = byKind("question")[0];
  const claims = byKind("claim");

  return (
    <div className="flex flex-col gap-4 text-xs">
      <div className="text-[11px] text-ink-500">
        Question → Claim → Evidence → Source. {graph.nodes.length} nodes, {graph.edges.length} edges.
      </div>
      {questionNode && (
        <div className={`rounded-lg border px-3 py-2 font-medium ${KIND_COLOR.question}`}>
          {questionNode.label}
        </div>
      )}
      <div className="flex flex-col gap-3 border-l-2 border-base-700 pl-3">
        {claims.map((claim) => {
          const evidenceIds = childrenOf(claim.id);
          return (
            <div key={claim.id} className="flex flex-col gap-2">
              <div className={`rounded-lg border px-3 py-2 ${KIND_COLOR.claim}`}>
                <div className="mb-1 text-[10px] uppercase tracking-wide text-ink-500">
                  Claim · {claim.status}
                </div>
                {claim.label}
              </div>
              <div className="ml-3 flex flex-col gap-2 border-l-2 border-base-700 pl-3">
                {evidenceIds.length === 0 && (
                  <div className="text-[11px] text-ink-500">No linked evidence.</div>
                )}
                {evidenceIds.map((evId) => {
                  const evNode = graph.nodes.find((n) => n.id === evId);
                  if (!evNode) return null;
                  const sourceIds = childrenOf(evId);
                  return (
                    <div key={evId} className="flex flex-col gap-1.5">
                      <div className={`rounded-md border px-2.5 py-1.5 ${KIND_COLOR.evidence}`}>
                        <span className="mr-1.5 rounded bg-base-700 px-1 py-0.5 text-[9px] uppercase text-ink-400">
                          {evNode.status}
                        </span>
                        {evNode.label}
                      </div>
                      <div className="ml-3 flex flex-col gap-1 border-l-2 border-base-700 pl-3">
                        {sourceIds.map((srcId) => {
                          const srcNode = graph.nodes.find((n) => n.id === srcId);
                          if (!srcNode) return null;
                          return (
                            <div key={srcId} className={`rounded-md border px-2.5 py-1.5 ${KIND_COLOR.source}`}>
                              {srcNode.label}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
