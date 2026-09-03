"""
Thin, optional Gemini wrapper.

Every agent that can use an LLM calls `generate_json` or `generate_text`
here and ALWAYS has a deterministic non-LLM fallback path in the
calling agent. This module never raises out to callers -- on any
failure (no key, network error, bad response) it returns None so the
agent silently falls back to its heuristic. This is what makes
"zero API keys" a real guarantee rather than a degraded mode.
"""
from __future__ import annotations

import json
import re
from typing import Optional

from .config import settings

_client_ready = False
_model = None

if settings.gemini_enabled:
    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.GEMINI_API_KEY)
        _model = genai.GenerativeModel(settings.GEMINI_MODEL)
        _client_ready = True
        print(f"[veriscope] Gemini enabled ({settings.GEMINI_MODEL}).")
    except Exception as exc:  # noqa: BLE001
        print(f"[veriscope] Gemini configured but failed to initialize: {exc}")
        _client_ready = False


def gemini_available() -> bool:
    return _client_ready


def generate_text(prompt: str, system: Optional[str] = None) -> Optional[str]:
    if not _client_ready:
        return None
    try:
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        response = _model.generate_content(full_prompt)
        return (response.text or "").strip()
    except Exception as exc:  # noqa: BLE001
        print(f"[veriscope] Gemini call failed, using fallback heuristic: {exc}")
        return None


def generate_json(prompt: str, system: Optional[str] = None) -> Optional[dict | list]:
    """Ask Gemini for strict JSON and parse it defensively."""
    text = generate_text(
        prompt,
        system=(system or "") + "\nRespond with ONLY valid JSON. No markdown fences, no prose.",
    )
    if not text:
        return None
    # strip markdown fences if the model added them anyway
    cleaned = re.sub(r"^```(json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"(\{.*\}|\[.*\])", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                return None
        return None
