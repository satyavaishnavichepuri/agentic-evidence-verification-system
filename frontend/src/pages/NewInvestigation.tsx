import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Sparkles, ArrowRight } from "lucide-react";
import { endpoints } from "../api/client";

const EXAMPLES = [
  "Does intermittent fasting improve long-term cardiovascular health outcomes?",
  "Is remote work associated with lower employee productivity?",
  "Do electric vehicles have a lower lifetime carbon footprint than gasoline cars?",
];

export default function NewInvestigation() {
  const [question, setQuestion] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  async function submit() {
    if (question.trim().length < 4) {
      setError("Please enter a more complete question.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const res = await endpoints.createInvestigation(question.trim());
      navigate(`/investigations/${res.data.id}`);
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Failed to start investigation.");
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto flex max-w-3xl flex-col items-center px-8 py-20">
      <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-accent-500/15 text-accent-400">
        <Sparkles size={22} />
      </div>
      <h1 className="text-2xl font-bold tracking-tight">Start a New Investigation</h1>
      <p className="mt-2 max-w-md text-center text-sm text-ink-400">
        Ask a research question. VeriScope's agents will plan, retrieve evidence, verify
        claims, detect contradictions, and return a validated Answer Contract.
      </p>

      <div className="mt-8 w-full">
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="e.g. Does intermittent fasting improve long-term cardiovascular health outcomes?"
          rows={3}
          className="w-full resize-none rounded-xl border border-base-700 bg-base-850 px-4 py-3.5 text-sm text-ink-100 placeholder-ink-500 outline-none focus:border-accent-500/50 focus:ring-2 focus:ring-accent-500/20"
        />
        {error && <div className="mt-2 text-xs text-declined-400">{error}</div>}
        <button
          onClick={submit}
          disabled={submitting}
          className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl bg-accent-500 px-4 py-3 text-sm font-semibold text-white shadow-lg shadow-accent-500/20 transition hover:bg-accent-600 disabled:opacity-50"
        >
          {submitting ? "Launching agents..." : "Run Investigation"}
          {!submitting && <ArrowRight size={16} />}
        </button>
      </div>

      <div className="mt-10 w-full">
        <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-ink-500">
          Try an example
        </div>
        <div className="flex flex-col gap-2">
          {EXAMPLES.map((ex) => (
            <button
              key={ex}
              onClick={() => setQuestion(ex)}
              className="rounded-lg border border-base-700 bg-base-850 px-4 py-2.5 text-left text-sm text-ink-300 transition hover:border-accent-500/30 hover:text-ink-100"
            >
              {ex}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
