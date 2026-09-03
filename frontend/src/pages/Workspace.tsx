import { useEffect, useRef, useState, type ReactNode } from "react";
import { useParams } from "react-router-dom";
import {
  Loader2, CheckCircle2, XCircle, Clock, FileText, Link2, ShieldCheck, AlertTriangle,
} from "lucide-react";
import { endpoints } from "../api/client";
import type { Investigation, AgentStepStatus, EvidenceItem } from "../types";
import { ContractStatusBadge, ClaimStatusBadge, StanceBadge } from "../components/StatusBadge";
import EvidenceGraphView from "../components/EvidenceGraphView";

const AGENT_LABELS: Record<string, string> = {
  planner: "Planner",
  research: "Research / RAG",
  evidence: "Evidence",
  verification: "Verification",
  contradiction: "Contradiction",
  contract_validator: "Contract Validator",
};

function StepIcon({ status }: { status: AgentStepStatus }) {
  if (status === "done") return <CheckCircle2 size={14} className="text-verified-400" />;
  if (status === "failed") return <XCircle size={14} className="text-declined-400" />;
  if (status === "running") return <Loader2 size={14} className="animate-spin text-accent-400" />;
  return <Clock size={14} className="text-ink-500" />;
}

export default function Workspace() {
  const { id } = useParams<{ id: string }>();
  const [inv, setInv] = useState<Investigation | null>(null);
  const [tab, setTab] = useState<"graph" | "sources">("sources");
  const pollRef = useRef<number | null>(null);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;

    async function load() {
      const res = await endpoints.getInvestigation(id!);
      if (cancelled) return;
      setInv(res.data);
      if (res.data.status === "complete" || res.data.status === "failed") {
        if (pollRef.current) window.clearInterval(pollRef.current);
      }
    }
    load();
    pollRef.current = window.setInterval(load, 1200);
    return () => {
      cancelled = true;
      if (pollRef.current) window.clearInterval(pollRef.current);
    };
  }, [id]);

  if (!inv) {
    return <div className="p-8 text-sm text-ink-400">Loading investigation...</div>;
  }

  const evidenceById: Record<string, EvidenceItem> = {};
  inv.evidence.forEach((e) => (evidenceById[e.id] = e));
  const running = inv.status !== "complete" && inv.status !== "failed";

  return (
    <div className="grid h-full grid-cols-[320px_1fr_380px]">
      {/* LEFT: question, subquestions, agent progress */}
      <div className="flex flex-col overflow-y-auto scrollbar-thin border-r border-base-700 bg-base-900 px-5 py-6">
        <div className="text-xs font-semibold uppercase tracking-wide text-ink-500">Question</div>
        <div className="mt-2 text-sm font-medium leading-snug text-ink-100">{inv.question}</div>

        <div className="mt-6 text-xs font-semibold uppercase tracking-wide text-ink-500">
          Subquestions ({inv.subquestions.length})
        </div>
        <div className="mt-2 flex flex-col gap-2">
          {inv.subquestions.length === 0 && (
            <div className="text-xs text-ink-500">Planner has not run yet...</div>
          )}
          {inv.subquestions.map((sq, i) => (
            <div key={sq.id} className="rounded-lg border border-base-700 bg-base-850 px-3 py-2 text-xs text-ink-300">
              <span className="mr-1.5 font-mono text-ink-500">{i + 1}.</span>
              {sq.text}
            </div>
          ))}
        </div>

        <div className="mt-6 text-xs font-semibold uppercase tracking-wide text-ink-500">
          Agent Progress
        </div>
        <div className="mt-2 flex flex-col gap-1.5">
          {inv.agent_trace.map((step) => (
            <div key={step.id} className="flex items-start gap-2 rounded-lg px-2 py-1.5 hover:bg-base-800/60">
              <div className="mt-0.5">
                <StepIcon status={step.status} />
              </div>
              <div className="min-w-0 flex-1">
                <div className="text-xs font-medium text-ink-200">{AGENT_LABELS[step.agent] || step.agent}</div>
                <div className="truncate text-[11px] text-ink-500">{step.message}</div>
              </div>
              {step.duration_ms != null && (
                <div className="shrink-0 text-[10px] text-ink-500">{step.duration_ms}ms</div>
              )}
            </div>
          ))}
          {running && (
            <div className="flex items-center gap-2 px-2 py-1.5 text-xs text-accent-400">
              <Loader2 size={13} className="animate-spin" />
              Pipeline running...
            </div>
          )}
        </div>
      </div>

      {/* CENTER: answer, findings, answer contract */}
      <div className="overflow-y-auto scrollbar-thin px-8 py-6">
        {!inv.contract ? (
          <div className="flex h-full flex-col items-center justify-center gap-3 text-ink-400">
            <Loader2 size={22} className="animate-spin text-accent-400" />
            <div className="text-sm">Agents are researching and verifying your question...</div>
          </div>
        ) : (
          <>
            <div className="mb-6 flex items-center justify-between">
              <h1 className="text-lg font-bold tracking-tight">Answer</h1>
              <ContractStatusBadge status={inv.contract.status} size="lg" />
            </div>

            <div className="panel mb-6 px-5 py-4">
              <div className="text-sm leading-relaxed text-ink-100">{inv.contract.summary}</div>
            </div>

            <div className="mb-3 text-xs font-semibold uppercase tracking-wide text-ink-500">
              Findings ({inv.claims.length})
            </div>
            <div className="mb-6 flex flex-col gap-3">
              {inv.claims.map((claim) => (
                <div key={claim.id} className="panel px-4 py-3.5">
                  <div className="flex items-start justify-between gap-3">
                    <div className="text-sm text-ink-100">{claim.text}</div>
                    <ClaimStatusBadge status={claim.status} size="sm" />
                  </div>
                  <div className="mt-2 text-xs text-ink-400">{claim.rationale}</div>
                  <div className="mt-2 flex items-center gap-3">
                    <div className="text-[11px] text-ink-500">
                      Confidence: <span className="font-mono text-ink-300">{(claim.confidence * 100).toFixed(0)}%</span>
                    </div>
                    <div className="text-[11px] text-ink-500">
                      {claim.evidence_ids.length} evidence item(s)
                    </div>
                  </div>
                  {claim.evidence_ids.length > 0 && (
                    <div className="mt-3 flex flex-col gap-1.5 border-t border-base-700 pt-3">
                      {claim.evidence_ids.map((eid) => {
                        const ev = evidenceById[eid];
                        if (!ev) return null;
                        return (
                          <div key={eid} className="flex items-start gap-2 text-xs">
                            <StanceBadge stance={ev.stance} />
                            <div className="text-ink-400">{ev.snippet}</div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Answer Contract detail */}
            <div className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-ink-500">
              <ShieldCheck size={13} />
              Answer Contract
            </div>
            <div className="panel mb-6 divide-y divide-base-700">
              <ContractRow label="Scope">{inv.contract.scope}</ContractRow>
              <ContractRow label="Citations">
                {inv.contract.citations.length > 0
                  ? `${inv.contract.citations.length} source(s) cited`
                  : "No sources cited"}
              </ContractRow>
              <ContractRow label="Missing Evidence">
                {inv.contract.missing_evidence.length === 0 ? (
                  <span className="text-ink-500">None -- all findings sufficiently supported.</span>
                ) : (
                  <ul className="flex flex-col gap-1.5">
                    {inv.contract.missing_evidence.map((m, i) => (
                      <li key={i} className="flex items-start gap-1.5 text-partial-400">
                        <AlertTriangle size={12} className="mt-0.5 shrink-0" />
                        <span className="text-ink-300">{m}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </ContractRow>
              <ContractRow label="Validation">
                {inv.contract.validation_errors.length === 0 ? (
                  <span className="flex items-center gap-1.5 text-verified-400">
                    <CheckCircle2 size={13} /> Contract passed code-based Pydantic validation.
                  </span>
                ) : (
                  <ul className="flex flex-col gap-1">
                    {inv.contract.validation_errors.map((e, i) => (
                      <li key={i} className="flex items-start gap-1.5 text-declined-400">
                        <XCircle size={12} className="mt-0.5 shrink-0" /> {e}
                      </li>
                    ))}
                  </ul>
                )}
              </ContractRow>
            </div>
          </>
        )}
      </div>

      {/* RIGHT: sources, evidence, contradictions */}
      <div className="flex flex-col overflow-y-auto scrollbar-thin border-l border-base-700 bg-base-900 px-5 py-6">
        <div className="mb-3 flex gap-1 rounded-lg bg-base-850 p-1">
          <button
            onClick={() => setTab("sources")}
            className={`flex-1 rounded-md px-2 py-1.5 text-xs font-medium transition ${tab === "sources" ? "bg-accent-500/20 text-accent-400" : "text-ink-400"}`}
          >
            Sources & Contradictions
          </button>
          <button
            onClick={() => setTab("graph")}
            className={`flex-1 rounded-md px-2 py-1.5 text-xs font-medium transition ${tab === "graph" ? "bg-accent-500/20 text-accent-400" : "text-ink-400"}`}
          >
            Evidence Graph
          </button>
        </div>

        {tab === "sources" ? (
          <>
            <div className="text-xs font-semibold uppercase tracking-wide text-ink-500">
              Contradictions ({inv.contradictions.length})
            </div>
            <div className="mt-2 flex flex-col gap-2">
              {inv.contradictions.length === 0 && (
                <div className="text-xs text-ink-500">No contradictions detected.</div>
              )}
              {inv.contradictions.map((c) => (
                <div key={c.id} className="rounded-lg border border-contradicted-500/30 bg-contradicted-950 px-3 py-2.5 text-xs text-ink-200">
                  {c.description}
                </div>
              ))}
            </div>

            <div className="mt-6 text-xs font-semibold uppercase tracking-wide text-ink-500">
              Evidence ({inv.evidence.length})
            </div>
            <div className="mt-2 flex flex-col gap-2">
              {inv.evidence.map((ev) => (
                <div key={ev.id} className="rounded-lg border border-base-700 bg-base-850 px-3 py-2.5">
                  <div className="mb-1 flex items-center justify-between">
                    <StanceBadge stance={ev.stance} />
                    <span className="text-[10px] text-ink-500">rel {(ev.relevance_score * 100).toFixed(0)}%</span>
                  </div>
                  <div className="text-xs text-ink-300">{ev.snippet}</div>
                  <div className="mt-1.5 flex items-center gap-1 text-[10px] text-ink-500">
                    <FileText size={10} /> {ev.source_id}
                  </div>
                </div>
              ))}
            </div>
          </>
        ) : (
          <EvidenceGraphView investigationId={inv.id} />
        )}
      </div>
    </div>
  );
}

function ContractRow({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="grid grid-cols-[110px_1fr] gap-3 px-5 py-3.5">
      <div className="flex items-start gap-1.5 text-xs font-semibold text-ink-400">
        <Link2 size={11} className="mt-0.5" />
        {label}
      </div>
      <div className="text-xs leading-relaxed text-ink-300">{children}</div>
    </div>
  );
}
