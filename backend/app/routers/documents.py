from __future__ import annotations

import io

from fastapi import APIRouter, File, HTTPException, UploadFile

from ..models import DocumentSummary, Source, SourceType
from ..rag import add_document_chunks
from ..storage import store

router = APIRouter(prefix="/api/documents", tags=["documents"])

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md"}
MAX_FILE_BYTES = 15 * 1024 * 1024  # 15MB


def _extract_text(filename: str, raw: bytes) -> str:
    lower = filename.lower()
    if lower.endswith(".pdf"):
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(raw))
        text_parts = []
        for page in reader.pages:
            try:
                text_parts.append(page.extract_text() or "")
            except Exception:  # noqa: BLE001
                continue
        return "\n".join(text_parts)
    # .txt / .md / anything else: treat as plain text
    return raw.decode("utf-8", errors="ignore")


@router.post("/upload", response_model=DocumentSummary, status_code=201)
async def upload_document(file: UploadFile = File(...)):
    filename = file.filename or "upload.txt"
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type '{ext}'. Use PDF, TXT, or MD.")

    raw = await file.read()
    if len(raw) > MAX_FILE_BYTES:
        raise HTTPException(status_code=400, detail="File too large (15MB limit).")

    text = _extract_text(filename, raw)
    if not text.strip():
        raise HTTPException(status_code=400, detail="No extractable text found in file.")

    source = Source(title=filename, type=SourceType.UPLOAD, filename=filename)
    store.save_source(source)
    chunks = add_document_chunks(source.id, text)

    if not chunks:
        raise HTTPException(status_code=400, detail="File produced no usable text chunks.")

    preview = chunks[0].text[:220] + ("..." if len(chunks[0].text) > 220 else "")
    return DocumentSummary(source=source, chunk_count=len(chunks), preview=preview)


@router.get("", response_model=list[DocumentSummary])
def list_documents():
    sources = store.list_sources()
    chunks = store.list_chunks()
    result = []
    for s in sources:
        s_chunks = [c for c in chunks if c.source_id == s.id]
        if not s_chunks:
            continue
        preview = s_chunks[0].text[:220] + ("..." if len(s_chunks[0].text) > 220 else "")
        result.append(DocumentSummary(source=s, chunk_count=len(s_chunks), preview=preview))
    return result
