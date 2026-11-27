# relations-pipeline

Extracts entities and relations from documents against an ontology, stores them
per document in Weaviate, then consolidates them across the corpus into final
collections and a Neo4j graph. Python library:

- **Phase A, per document:** `relations_pipeline.ingest_document(doc, use_case)`:
  coreference → chunking → extraction per chunk → resolution within the document
  → a description and an embedding per entity and relation → upsert.
- **Phase B, per corpus:** `relations_pipeline.consolidate(use_case)`:
  dedup clusters of entities and relations (`nlp-dedup`) → merged, re-described
  nodes and edges → final Weaviate collections and Neo4j.

`use_case` names an ontology in `config/ontologies/` (e.g. `financial_flows`).

It holds no model. Every NLP step is a call to a shared service on `wiig-net`,
so whatever runs this library must be on that network.

## Settings (environment)

| Variable | Default | |
|---|---|---|
| `EXTRACT_URL` | `http://wiig-extract:8000` | `/coref`, `/ner`, `/resolve` |
| `SUMMARIZE_URL` | `http://wiig-summarize:8000` | descriptions |
| `VECTORIZER_URL`, `VECTORIZER_MODEL` | `http://wiig-embed:8089/embed`, `bge-m3` | |
| `WEAVIATE_URL` | `http://weaviate:8080` | the pipeline's own Weaviate; also read by `nlp-dedup` |
| `NEO4J_*` | see `relations_pipeline/neo4j_io.py` | Phase B |
| `ONTOLOGY_DIR` | `config/ontologies` | |
| `OLLAMA_HOST` | `http://ollama_high:11434` | `nlp-dedup`'s adjudicator |

## Tests

```sh
pip install -e ../nlp-dedup -e '.[test]' && pytest
```

## History

This repo was `nlp_service`, which bundled the NLP modules, an HTTP API over
them, and two pipelines. It was split on 2026-11-27:

| What | Now |
|---|---|
| ner, coref, resolver | `wiig-extract` (shared service) |
| summarizer | `wiig-summarize` |
| nli | `wiig-nli` |
| geotagger | `wiig-geotag` |
| dedup | `nlp-dedup` (library) |
| news pipeline | `news-pipeline` |
| relation pipeline | this repo |

Design notes: [docs/relations-pipeline.md](docs/relations-pipeline.md), `docs/specs/`.
