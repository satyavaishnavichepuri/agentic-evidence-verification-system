import { useEffect, useRef, useState } from "react";
import { UploadCloud, FileText, Globe, Database } from "lucide-react";
import { endpoints } from "../api/client";
import type { DocumentSummary } from "../types";

const TYPE_ICON: Record<string, any> = { seed: Database, upload: FileText, web: Globe };

export default function KnowledgeBase() {
  const [docs, setDocs] = useState<DocumentSummary[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  function refresh() {
    endpoints.listDocuments().then((res) => setDocs(res.data));
  }

  useEffect(refresh, []);

  async function handleFile(file: File) {
    setUploading(true);
    setError(null);
    try {
      await endpoints.uploadDocument(file);
      refresh();
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Upload failed.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="mx-auto max-w-4xl px-8 py-8">
      <h1 className="text-2xl font-bold tracking-tight">Knowledge Base</h1>
      <p className="mt-1 text-sm text-ink-400">
        The corpus every investigation retrieves from -- seeded demo sources plus anything you upload.
      </p>

      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          const file = e.dataTransfer.files?.[0];
          if (file) handleFile(file);
        }}
        onClick={() => inputRef.current?.click()}
        className="mt-6 flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed border-base-700 bg-base-850 px-6 py-10 text-center transition hover:border-accent-500/40"
      >
        <UploadCloud size={28} className="text-accent-400" />
        <div className="text-sm font-medium text-ink-200">
          {uploading ? "Uploading and indexing..." : "Click or drag a PDF / TXT / MD file here"}
        </div>
        <div className="text-xs text-ink-500">It will be chunked and added to the RAG index immediately.</div>
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.txt,.md"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleFile(file);
            e.target.value = "";
          }}
        />
      </div>
      {error && <div className="mt-2 text-xs text-declined-400">{error}</div>}

      <div className="mt-8 text-xs font-semibold uppercase tracking-wide text-ink-500">
        Documents ({docs.length})
      </div>
      <div className="mt-3 flex flex-col gap-2">
        {docs.map((d) => {
          const Icon = TYPE_ICON[d.source.type] || FileText;
          return (
            <div key={d.source.id} className="panel flex items-start gap-3 px-4 py-3.5">
              <div className="mt-0.5 text-ink-400">
                <Icon size={16} />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <div className="truncate text-sm font-medium text-ink-100">{d.source.title}</div>
                  <span className="shrink-0 rounded-full border border-base-600 bg-base-800 px-2 py-0.5 text-[10px] uppercase text-ink-400">
                    {d.source.type}
                  </span>
                </div>
                <div className="mt-1 truncate text-xs text-ink-400">{d.preview}</div>
                <div className="mt-1 text-[11px] text-ink-500">{d.chunk_count} chunk(s) indexed</div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
