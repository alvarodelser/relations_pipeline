"""The shared NLP services the relations pipeline calls, over HTTP on wiig-net.

Each object keeps the call shape the orchestrator used when these were in-process modules
(`coref.resolve_pronouns`, `ner.run`, `resolver.resolve`, `summarizer.summarize`), so the
orchestrator and its tests only changed their imports. Errors surface as httpx.HTTPError, which
the orchestrator already turns into {"status": "error", "stage": ...}.

  EXTRACT_URL     wiig-extract     POST /coref, /ner, /resolve
  SUMMARIZE_URL   wiig-summarize   POST /summarize
"""
import os

import httpx

from .types import ExtractionSchema, NerResponse, ResolveResponse

EXTRACT_URL = os.environ.get("EXTRACT_URL", "http://wiig-extract:8000").rstrip("/")
SUMMARIZE_URL = os.environ.get("SUMMARIZE_URL", "http://wiig-summarize:8000").rstrip("/")
# Extraction runs a large model per chunk; the services' own Ollama timeouts are up to 180 s.
TIMEOUT = float(os.environ.get("NLP_SERVICES_TIMEOUT", "600"))

_http = httpx.Client(timeout=TIMEOUT)


def _post(url: str, body: dict) -> dict:
    r = _http.post(url, json=body)
    r.raise_for_status()
    return r.json()


class _Coref:
    def resolve_pronouns(self, text: str) -> str:
        return _post(f"{EXTRACT_URL}/coref", {"text": text})["text"]


class _Ner:
    def run(self, text: str, schema: ExtractionSchema) -> NerResponse:
        return NerResponse.model_validate(
            _post(f"{EXTRACT_URL}/ner", {"text": text, "schema": schema.model_dump()}))


class _Resolver:
    def resolve(self, entities: list[dict], relations: list[dict]) -> ResolveResponse:
        return ResolveResponse.model_validate(
            _post(f"{EXTRACT_URL}/resolve", {"entities": entities, "relations": relations}))


class _Summarizer:
    def summarize(self, profile: str, fields: dict) -> dict:
        return _post(f"{SUMMARIZE_URL}/summarize", {"profile": profile, "fields": fields})["result"]


coref = _Coref()
ner = _Ner()
resolver = _Resolver()
summarizer = _Summarizer()
