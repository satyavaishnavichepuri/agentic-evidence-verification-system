"""
Storage layer.

Default: pure in-memory Python dicts (InMemoryStore). Nothing to
install, nothing to configure, resets on restart.

Optional: if DATABASE_URL is set, PostgresStore persists the exact
same records as JSON blobs in one key-value table
(veriscope_kv(key TEXT PRIMARY KEY, value JSONB)). This keeps the
data model identical in both modes -- Postgres is a durability
upgrade, not a schema fork. Everything still round-trips through the
same Pydantic models, so agent code never needs to know which backend
is active.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from .config import settings
from .models import Chunk, Investigation, Source


class BaseStore:
    """Interface implemented by InMemoryStore and PostgresStore."""

    # investigations
    def save_investigation(self, inv: Investigation) -> None: ...
    def get_investigation(self, inv_id: str) -> Optional[Investigation]: ...
    def list_investigations(self) -> List[Investigation]: ...

    # sources / chunks (knowledge base + RAG corpus)
    def save_source(self, source: Source) -> None: ...
    def get_source(self, source_id: str) -> Optional[Source]: ...
    def list_sources(self) -> List[Source]: ...
    def save_chunks(self, chunks: List[Chunk]) -> None: ...
    def list_chunks(self) -> List[Chunk]: ...


class InMemoryStore(BaseStore):
    def __init__(self) -> None:
        self._investigations: Dict[str, Investigation] = {}
        self._sources: Dict[str, Source] = {}
        self._chunks: Dict[str, Chunk] = {}

    def save_investigation(self, inv: Investigation) -> None:
        self._investigations[inv.id] = inv

    def get_investigation(self, inv_id: str) -> Optional[Investigation]:
        return self._investigations.get(inv_id)

    def list_investigations(self) -> List[Investigation]:
        return sorted(
            self._investigations.values(), key=lambda i: i.created_at, reverse=True
        )

    def save_source(self, source: Source) -> None:
        self._sources[source.id] = source

    def get_source(self, source_id: str) -> Optional[Source]:
        return self._sources.get(source_id)

    def list_sources(self) -> List[Source]:
        return sorted(self._sources.values(), key=lambda s: s.retrieved_at, reverse=True)

    def save_chunks(self, chunks: List[Chunk]) -> None:
        for c in chunks:
            self._chunks[c.id] = c

    def list_chunks(self) -> List[Chunk]:
        return list(self._chunks.values())


class PostgresStore(BaseStore):
    """
    Simple JSON-blob persistence on top of Postgres. Used only when
    DATABASE_URL is configured. Falls back to raising a clear error at
    startup if the driver/connection isn't actually reachable -- the
    caller (build_store) catches that and stays on InMemoryStore so
    the app never hard-fails just because Postgres enhancement was
    misconfigured.
    """

    def __init__(self, database_url: str) -> None:
        from sqlalchemy import create_engine, text

        self._engine = create_engine(database_url, pool_pre_ping=True)
        with self._engine.begin() as conn:
            conn.execute(text(
                """
                CREATE TABLE IF NOT EXISTS veriscope_kv (
                    key TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    value JSONB NOT NULL
                )
                """
            ))
        with self._engine.connect() as conn:
            conn.execute(text("SELECT 1"))

    def _put(self, key: str, kind: str, value: dict) -> None:
        from sqlalchemy import text
        import json as _json

        with self._engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO veriscope_kv (key, kind, value)
                    VALUES (:key, :kind, CAST(:value AS JSONB))
                    ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
                    """
                ),
                {"key": key, "kind": kind, "value": _json.dumps(value)},
            )

    def _get(self, key: str) -> Optional[dict]:
        from sqlalchemy import text

        with self._engine.connect() as conn:
            row = conn.execute(
                text("SELECT value FROM veriscope_kv WHERE key = :key"), {"key": key}
            ).fetchone()
            return row[0] if row else None

    def _list(self, kind: str) -> List[dict]:
        from sqlalchemy import text

        with self._engine.connect() as conn:
            rows = conn.execute(
                text("SELECT value FROM veriscope_kv WHERE kind = :kind"), {"kind": kind}
            ).fetchall()
            return [r[0] for r in rows]

    def save_investigation(self, inv: Investigation) -> None:
        self._put(f"investigation:{inv.id}", "investigation", inv.model_dump(mode="json"))

    def get_investigation(self, inv_id: str) -> Optional[Investigation]:
        data = self._get(f"investigation:{inv_id}")
        return Investigation.model_validate(data) if data else None

    def list_investigations(self) -> List[Investigation]:
        items = [Investigation.model_validate(d) for d in self._list("investigation")]
        return sorted(items, key=lambda i: i.created_at, reverse=True)

    def save_source(self, source: Source) -> None:
        self._put(f"source:{source.id}", "source", source.model_dump(mode="json"))

    def get_source(self, source_id: str) -> Optional[Source]:
        data = self._get(f"source:{source_id}")
        return Source.model_validate(data) if data else None

    def list_sources(self) -> List[Source]:
        items = [Source.model_validate(d) for d in self._list("source")]
        return sorted(items, key=lambda s: s.retrieved_at, reverse=True)

    def save_chunks(self, chunks: List[Chunk]) -> None:
        for c in chunks:
            self._put(f"chunk:{c.id}", "chunk", c.model_dump(mode="json"))

    def list_chunks(self) -> List[Chunk]:
        return [Chunk.model_validate(d) for d in self._list("chunk")]


def build_store() -> BaseStore:
    if settings.postgres_enabled:
        try:
            store = PostgresStore(settings.DATABASE_URL)
            print("[veriscope] Postgres storage enabled.")
            return store
        except Exception as exc:  # noqa: BLE001
            print(f"[veriscope] Postgres unavailable ({exc}); falling back to in-memory store.")
    print("[veriscope] Using in-memory storage (demo mode).")
    return InMemoryStore()


store: BaseStore = build_store()
