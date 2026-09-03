import { CheckCircle2, AlertTriangle, XCircle, GitCompareArrows, HelpCircle } from "lucide-react";
import type { ClaimStatus, ContractStatus, Stance } from "../types";

const CONTRACT_STYLES: Record<ContractStatus, string> = {
  VERIFIED: "bg-verified-950 text-verified-400 border-verified-500/30",
  PARTIAL: "bg-partial-950 text-partial-400 border-partial-500/30",
  DECLINED: "bg-declined-950 text-declined-400 border-declined-500/30",
};

const CLAIM_STYLES: Record<ClaimStatus, string> = {
  verified: "bg-verified-950 text-verified-400 border-verified-500/30",
  partial: "bg-partial-950 text-partial-400 border-partial-500/30",
  contradicted: "bg-contradicted-950 text-contradicted-400 border-contradicted-500/30",
  unsupported: "bg-declined-950 text-declined-400 border-declined-500/30",
};

const CLAIM_ICON: Record<ClaimStatus, any> = {
  verified: CheckCircle2,
  partial: AlertTriangle,
  contradicted: GitCompareArrows,
  unsupported: HelpCircle,
};

const CONTRACT_ICON: Record<ContractStatus, any> = {
  VERIFIED: CheckCircle2,
  PARTIAL: AlertTriangle,
  DECLINED: XCircle,
};

export function ContractStatusBadge({ status, size = "md" }: { status: ContractStatus; size?: "sm" | "md" | "lg" }) {
  const Icon = CONTRACT_ICON[status];
  const sizeCls = size === "lg" ? "text-sm px-3.5 py-1.5 gap-2" : size === "sm" ? "text-[11px] px-2 py-0.5 gap-1" : "text-xs px-2.5 py-1 gap-1.5";
  return (
    <span className={`inline-flex items-center rounded-full border font-semibold tracking-wide ${CONTRACT_STYLES[status]} ${sizeCls}`}>
      <Icon size={size === "lg" ? 15 : 13} />
      {status}
    </span>
  );
}

export function ClaimStatusBadge({ status, size = "md" }: { status: ClaimStatus; size?: "sm" | "md" }) {
  const Icon = CLAIM_ICON[status];
  const sizeCls = size === "sm" ? "text-[11px] px-2 py-0.5 gap-1" : "text-xs px-2.5 py-1 gap-1.5";
  return (
    <span className={`inline-flex items-center rounded-full border font-medium capitalize ${CLAIM_STYLES[status]} ${sizeCls}`}>
      <Icon size={12} />
      {status}
    </span>
  );
}

const STANCE_STYLES: Record<Stance, string> = {
  supports: "text-verified-400 bg-verified-950 border-verified-500/30",
  contradicts: "text-contradicted-400 bg-contradicted-950 border-contradicted-500/30",
  neutral: "text-ink-400 bg-base-800 border-base-600",
};

export function StanceBadge({ stance }: { stance: Stance }) {
  return (
    <span className={`inline-flex items-center rounded-md border px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${STANCE_STYLES[stance]}`}>
      {stance}
    </span>
  );
}
