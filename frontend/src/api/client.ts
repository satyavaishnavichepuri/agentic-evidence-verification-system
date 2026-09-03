import axios from "axios";
import type {
  AgentMonitorSummary,
  AgentRunView,
  AnswerContract,
  DocumentSummary,
  EvidenceGraph,
  Investigation,
  InvestigationSummary,
  Source,
} from "../types";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const api = axios.create({ baseURL: API_URL });

export interface HealthResponse {
  status: string;
  gemini_enabled: boolean;
  postgres_enabled: boolean;
}

export const endpoints = {
  health: () => api.get<HealthResponse>("/api/health"),

  listInvestigations: () => api.get<InvestigationSummary[]>("/api/investigations"),
  getInvestigation: (id: string) => api.get<Investigation>(`/api/investigations/${id}`),
  createInvestigation: (question: string) =>
    api.post<Investigation>("/api/investigations", { question }),
  getInvestigationGraph: (id: string) =>
    api.get<EvidenceGraph>(`/api/investigations/${id}/graph`),

  listDocuments: () => api.get<DocumentSummary[]>("/api/documents"),
  uploadDocument: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api.post<DocumentSummary>("/api/documents/upload", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  listSources: () => api.get<Source[]>("/api/sources"),

  listAgentRuns: () => api.get<AgentRunView[]>("/api/agents/runs"),
  agentStatus: () => api.get<AgentMonitorSummary>("/api/agents/status"),
};

export type { AnswerContract };
