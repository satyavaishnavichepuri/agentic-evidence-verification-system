import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { PlusCircle, Sparkles, Database } from "lucide-react";
import { endpoints } from "../api/client";
import type { InvestigationSummary } from "../types";
import { ContractStatusBadge } from "../components/StatusBadge";

export default function Dashboard() {
  const [items, setItems] = useState<InvestigationSummary[]>([]);
  const [health, setHealth] = useState<{ gemini_enabled: boolean; postgres_enabled: boolean } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([endpoints.listInvestigations(), endpoints.health()])
      .then(([inv, h]) => {
        setItems(inv.data);
        setHealth(h.data);
      })
      .finally(() => setLoading(false));
  }, []);

  const counts = {
    total: items.length,
    verified: items.filter((i) => i.contract_status === "VERIFIED").length,
    partial: items.filter((i) => i.contract_status === "PARTIAL").length,
    declined: items.filter((i) => i.contract_status === "DECLINED").length,
  };

  return (
    <div className="mx-auto max-w-6xl px-8 py-8">
      <div className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
          <p className="mt-1 text-sm text-ink-400">
            Overview of every investigation and its Answer Contract outcome.
          </p>
        </div>
        <Link
          to="/new"
          className="flex items-center gap-2 rounded-lg bg-accent-500 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-accent-500/20 transition hover:bg-accent-600"
        >
          <PlusCircle size={16} />
          New Investigation
        </Link>
      </div>

      {health && (
        <div className="mb-6 flex gap-3">
          <div className={`flex items-center gap-2 rounded-lg border px-3 py-1.5 text-xs font-medium ${health.gemini_enabled ? "border-accent-500/30 bg-accent-500/10 text-accent-400" : "border-base-700 bg-base-850 text-ink-400"}`}>
            <Sparkles size={13} />
            Gemini {health.gemini_enabled ? "enabled" : "off (demo heuristics)"}
          </div>
          <div className={`flex items-center gap-2 rounded-lg border px-3 py-1.5 text-xs font-medium ${health.postgres_enabled ? "border-accent-500/30 bg-accent-500/10 text-accent-400" : "border-base-700 bg-base-850 text-ink-400"}`}>
            <Database size={13} />
            Postgres {health.postgres_enabled ? "enabled" : "off (in-memory)"}
          </div>
        </div>
      )}

      <div className="mb-8 grid grid-cols-4 gap-4">
        <StatCard label="Total Investigations" value={counts.total} />
        <StatCard label="Verified" value={counts.verified} className="text-verified-400" />
        <StatCard label="Partial" value={counts.partial} className="text-partial-400" />
        <StatCard label="Declined" value={counts.declined} className="text-declined-400" />
      </div>

      <div className="panel overflow-hidden">
        <div className="border-b border-base-700 px-5 py-3 text-sm font-semibold text-ink-200">
          Recent Investigations
        </div>
        {loading ? (
          <div className="px-5 py-8 text-center text-sm text-ink-400">Loading...</div>
        ) : items.length === 0 ? (
          <div className="px-5 py-8 text-center text-sm text-ink-400">
            No investigations yet. Start one to see the pipeline in action.
          </div>
        ) : (
          <div className="divide-y divide-base-700">
            {items.map((inv) => (
              <Link
                key={inv.id}
                to={`/investigations/${inv.id}`}
                className="flex items-center justify-between gap-4 px-5 py-4 transition hover:bg-base-800/60"
              >
                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm font-medium text-ink-100">{inv.question}</div>
                  <div className="mt-1 text-xs text-ink-400">
                    {inv.claim_count} claim(s) · {new Date(inv.created_at).toLocaleString()} ·{" "}
                    <span className="capitalize">{inv.status}</span>
                  </div>
                </div>
                {inv.contract_status ? (
                  <ContractStatusBadge status={inv.contract_status} />
                ) : (
                  <span className="text-xs text-ink-400">running...</span>
                )}
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({ label, value, className = "text-ink-100" }: { label: string; value: number; className?: string }) {
  return (
    <div className="panel px-5 py-4">
      <div className={`text-3xl font-bold ${className}`}>{value}</div>
      <div className="mt-1 text-xs font-medium text-ink-400">{label}</div>
    </div>
  );
}
