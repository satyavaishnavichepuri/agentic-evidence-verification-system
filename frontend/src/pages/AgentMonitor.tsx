import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { CheckCircle2, XCircle, Loader2, Clock, Sparkles, Database } from "lucide-react";
import { endpoints } from "../api/client";
import type { AgentRunView, AgentMonitorSummary, AgentStepStatus } from "../types";

const AGENT_LABELS: Record<string, string> = {
  planner: "Planner",
  research: "Research / RAG",
  evidence: "Evidence",
  verification: "Verification",
  contradiction: "Contradiction",
  contract_validator: "Contract Validator",
};

function StatusIcon({ status }: { status: AgentStepStatus }) {
  if (status === "done") return <CheckCircle2 size={14} className="text-verified-400" />;
  if (status === "failed") return <XCircle size={14} className="text-declined-400" />;
  if (status === "running") return <Loader2 size={14} className="animate-spin text-accent-400" />;
  return <Clock size={14} className="text-ink-500" />;
}

export default function AgentMonitor() {
  const [runs, setRuns] = useState<AgentRunView[]>([]);
  const [summary, setSummary] = useState<AgentMonitorSummary | null>(null);

  useEffect(() => {
    function load() {
      endpoints.listAgentRuns().then((r) => setRuns(r.data));
      endpoints.agentStatus().then((r) => setSummary(r.data));
    }
    load();
    const t = window.setInterval(load, 3000);
    return () => window.clearInterval(t);
  }, []);

  return (
    <div className="mx-auto max-w-5xl px-8 py-8">
      <h1 className="text-2xl font-bold tracking-tight">Agent Monitor</h1>
      <p className="mt-1 text-sm text-ink-400">
        Live log of every agent execution across all investigations.
      </p>

      {summary && (
        <div className="mt-5 grid grid-cols-4 gap-4">
          <div className="panel px-4 py-3.5">
            <div className="text-2xl font-bold text-ink-100">{summary.total_runs}</div>
            <div className="mt-1 text-xs text-ink-400">Total agent runs</div>
          </div>
          <div className="panel flex items-center gap-2 px-4 py-3.5">
            <Sparkles size={16} className={summary.gemini_enabled ? "text-accent-400" : "text-ink-500"} />
            <div>
              <div className="text-sm font-semibold text-ink-100">{summary.gemini_enabled ? "Enabled" : "Off"}</div>
              <div className="text-xs text-ink-400">Gemini enhancement</div>
            </div>
          </div>
          <div className="panel flex items-center gap-2 px-4 py-3.5">
            <Database size={16} className={summary.postgres_enabled ? "text-accent-400" : "text-ink-500"} />
            <div>
              <div className="text-sm font-semibold text-ink-100">{summary.postgres_enabled ? "Enabled" : "In-memory"}</div>
              <div className="text-xs text-ink-400">Storage backend</div>
            </div>
          </div>
          <div className="panel px-4 py-3.5">
            <div className="flex flex-wrap gap-1.5">
              {Object.entries(summary.by_status).map(([k, v]) => (
                <span key={k} className="rounded-full border border-base-600 bg-base-800 px-2 py-0.5 text-[10px] text-ink-300">
                  {k}: {v}
                </span>
              ))}
            </div>
            <div className="mt-1.5 text-xs text-ink-400">Runs by status</div>
          </div>
        </div>
      )}

      <div className="panel mt-6 divide-y divide-base-700">
        {runs.length === 0 && (
          <div className="px-5 py-8 text-center text-sm text-ink-400">No agent runs yet.</div>
        )}
        {runs.map((r) => (
          <Link
            key={r.id}
            to={`/investigations/${r.investigation_id}`}
            className="flex items-start gap-3 px-5 py-3.5 transition hover:bg-base-800/60"
          >
            <div className="mt-0.5">
              <StatusIcon status={r.status} />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-ink-100">{AGENT_LABELS[r.agent] || r.agent}</span>
                <span className="text-[10px] uppercase tracking-wide text-ink-500">{r.status}</span>
                {r.duration_ms != null && (
                  <span className="text-[10px] text-ink-500">{r.duration_ms}ms</span>
                )}
              </div>
              <div className="mt-0.5 truncate text-xs text-ink-400">{r.message}</div>
              <div className="mt-0.5 truncate text-[11px] text-ink-500">on: {r.investigation_question}</div>
            </div>
            <div className="shrink-0 text-[11px] text-ink-500">
              {r.started_at ? new Date(r.started_at).toLocaleTimeString() : ""}
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
