export type SourceType = "seed" | "upload" | "web";
export type Stance = "supports" | "contradicts" | "neutral";
export type ClaimStatus = "verified" | "partial" | "contradicted" | "unsupported";
export type ContractStatus = "VERIFIED" | "PARTIAL" | "DECLINED";
export type AgentName =
  | "planner"
  | "research"
  | "evidence"
  | "verification"
  | "contradiction"
  | "contract_validator";
export type AgentStepStatus = "pending" | "running" | "done" | "failed";
export type InvestigationStatus =
  | "planning"
  | "researching"
  | "verifying"
  | "complete"
  | "failed";

export interface Source {
  id: string;
  title: string;
  type: SourceType;
  url?: string | null;
  filename?: string | null;
  published?: string | null;
  retrieved_at: string;
}

export interface Chunk {
  id: string;
  source_id: string;
  text: string;
  stance_hint?: Stance | null;
}

export interface DocumentSummary {
  source: Source;
  chunk_count: number;
  preview: string;
}

export interface SubQuestion {
  id: string;
  text: string;
}

export interface EvidenceItem {
  id: string;
  claim_id: string;
  source_id: string;
  chunk_id: string;
  snippet: string;
  relevance_score: number;
  stance: Stance;
}

export interface Claim {
  id: string;
  subquestion_id: string;
  text: string;
  status: ClaimStatus;
  evidence_ids: string[];
  confidence: number;
  rationale: string;
}

export interface Contradiction {
  id: string;
  claim_ids: string[];
  description: string;
  evidence_ids: string[];
}

export interface AnswerContract {
  investigation_id: string;
  question: string;
  scope: string;
  status: ContractStatus;
  summary: string;
  claims: Claim[];
  citations: string[];
  missing_evidence: string[];
  contradictions: Contradiction[];
  validation_errors: string[];
  generated_at: string;
}

export interface AgentStep {
  id: string;
  investigation_id: string;
  agent: AgentName;
  status: AgentStepStatus;
  message: string;
  started_at?: string | null;
  finished_at?: string | null;
  duration_ms?: number | null;
}

export interface GraphNode {
  id: string;
  kind: "question" | "claim" | "evidence" | "source";
  label: string;
  status?: string | null;
}

export interface GraphEdge {
  source: string;
  target: string;
}

export interface EvidenceGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface Investigation {
  id: string;
  question: string;
  status: InvestigationStatus;
  subquestions: SubQuestion[];
  claims: Claim[];
  evidence: EvidenceItem[];
  contradictions: Contradiction[];
  contract?: AnswerContract | null;
  agent_trace: AgentStep[];
  created_at: string;
  updated_at: string;
  is_seed: boolean;
}

export interface InvestigationSummary {
  id: string;
  question: string;
  status: InvestigationStatus;
  contract_status?: ContractStatus | null;
  claim_count: number;
  created_at: string;
}

export interface AgentRunView {
  id: string;
  investigation_id: string;
  investigation_question: string;
  agent: AgentName;
  status: AgentStepStatus;
  message: string;
  started_at?: string | null;
  finished_at?: string | null;
  duration_ms?: number | null;
}

export interface AgentMonitorSummary {
  gemini_enabled: boolean;
  postgres_enabled: boolean;
  total_runs: number;
  by_agent: Record<string, number>;
  by_status: Record<string, number>;
}
