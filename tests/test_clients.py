"""The HTTP clients send wiig-extract and wiig-summarize the bodies their APIs take and hand
back the objects the orchestrator reads."""
import httpx

from relations_pipeline import clients
from relations_pipeline.types import ExtractionSchema


def _fake(monkeypatch, reply):
    seen = {}

    def post(url, json):
        seen["url"], seen["json"] = url, json
        return httpx.Response(200, json=reply, request=httpx.Request("POST", url))
    monkeypatch.setattr(clients._http, "post", post)
    return seen


def test_coref(monkeypatch):
    seen = _fake(monkeypatch, {"text": "Ana pagó. Ana firmó."})
    assert clients.coref.resolve_pronouns("Ana pagó. Ella firmó.") == "Ana pagó. Ana firmó."
    assert seen["url"].endswith("/coref")


def test_ner_sends_schema_and_parses_response(monkeypatch):
    schema = ExtractionSchema(entity_types=[{"name": "PERSON"}], relation_types=[])
    seen = _fake(monkeypatch, {"request_id": None, "entities": [
        {"name": "Ana", "mention_text": "Ana", "type": "PERSON", "evidence_text": "Ana pagó.",
         "confidence": 0.9}], "relations": []})
    r = clients.ner.run("Ana pagó.", schema)
    assert r.entities[0].name == "Ana"
    assert seen["url"].endswith("/ner") and seen["json"]["schema"]["entity_types"][0]["name"] == "PERSON"


def test_resolve_parses_response(monkeypatch):
    _fake(monkeypatch, {"entities": [{"id": "0", "canonical_name": "Ana", "names": ["Ana"],
                                      "type": "PERSON", "evidence": ["Ana pagó."]}],
                        "relations": []})
    r = clients.resolver.resolve([{"name": "Ana", "type": "PERSON", "evidence": "Ana pagó."}], [])
    assert r.entities[0].canonical_name == "Ana"


def test_summarize(monkeypatch):
    seen = _fake(monkeypatch, {"result": {"description": "d"}})
    assert clients.summarizer.summarize("entity_desc", {"name": "Ana"}) == {"description": "d"}
    assert seen["json"]["profile"] == "entity_desc"
