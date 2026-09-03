from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..models import Chunk, Source
from ..storage import store

router = APIRouter(prefix="/api/sources", tags=["sources"])


@router.get("", response_model=list[Source])
def list_sources():
    return store.list_sources()


@router.get("/{source_id}", response_model=Source)
def get_source(source_id: str):
    source = store.get_source(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    return source


@router.get("/{source_id}/chunks", response_model=list[Chunk])
def get_source_chunks(source_id: str):
    return [c for c in store.list_chunks() if c.source_id == source_id]
