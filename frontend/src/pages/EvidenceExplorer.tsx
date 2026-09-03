import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { endpoints } from "../api/client";
import type { InvestigationSummary, Investigation, Claim, EvidenceItem } from "../types";
import { ClaimStatusBadge, StanceBadge } from "../components/StatusBadge";

type Row = { inv: InvestigationSummary; claim: Claim; evidence: EvidenceItem[] };

export default function EvidenceExplorer() {
  const [rows, setRows] = useState<Row[]>([]);
  const [filter, setFilter] = useState<string>("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      const summaries = (await endpoints.listInvestigations()).data;
      const full: Investigation[] = await Promise.all(
        summaries.map((s) => endpoints.getInvestigation(s.id).then((r) => r.data))
      );
      const out: Row[] = [];
      full.forEach((inv, idx) => {
        const evById: Record<string, EvidenceItem> = {};
        inv.evidence.forEach((e) => (evById[e.id] = e));
        inv.claims.forEach((claim) => {
          out.push({
            inv: summaries[idx],
            claim,
            evidence: claim.evidence_ids.map((id) => evById[id]).filter(Boolean),
          });
        });
      });
      setRows(out);
      setLoading(false);
    }
    load();
  }, []);

  const filtered = filter === "all" ? rows : rows.filter((r) => r.claim.status === filter);

  return (
    <div className="mx-auto max-w-5xl px-8 py-8">
      <h1 className="text-2xl font-bold tracking-tight">Evidence Explorer</h1>
      <p className="mt-1 text-sm text-ink-400">
        Every claim and its grounding evidence, across all investigations.
      </p>

      <div className="mt-5 flex gap-2">
        {["all", "verified", "partial", "contradicted", "unsupported"].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`rounded-full border px-3 py-1.5 text-xs font-medium capitalize transition ${
              filter === f
                ? "border-accent-500/40 bg-accent-500/15 text-accent-400"
                : "border-base-700 bg-base-850 text-ink-400 hover:text-ink-200"
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      <div className="mt-6 flex flex-col gap-3">
        {loading && <div className="text-sm text-ink-400">Loading evidence...</div>}
        {!loading && filtered.length === 0 && (
          <div className="text-sm text-ink-400">No claims match this filter.</div>
        )}
        {filtered.map((row) => (
          <div key={row.claim.id} className="panel px-5 py-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <Link
                  to={`/investigations/${row.inv.id}`}
                  className="text-[11px] font-medium uppercase tracking-wide text-accent-400 hover:underline"
                >
                  {row.inv.question}
                </Link>
                <div className="mt-1 text-sm text-ink-100">{row.claim.text}</div>
              </div>
              <ClaimStatusBadge status={row.claim.status} />
            </div>
            {row.evidence.length > 0 && (
              <div className="mt-3 flex flex-col gap-1.5 border-t border-base-700 pt-3">
                {row.evidence.map((ev) => (
                  <div key={ev.id} className="flex items-start gap-2 text-xs">
                    <StanceBadge stance={ev.stance} />
                    <div className="text-ink-400">{ev.snippet}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
