# Chat With Your Documents

A RAG (Retrieval-Augmented Generation) app: upload documents, ask questions, get answers grounded in the source material — with citations back to the exact passage.

Built as a learning + portfolio project. Full build plan: see `PLAN.md`.

## Status

🚧 Phase 0 — project setup in progress.

## Stack

- **Backend:** Python (FastAPI)
- **LLM:** OpenAI (chat completions)
- **Embeddings:** OpenAI (embeddings API)
- **Vector store:** TBD (starting local/in-memory, see PLAN.md)

## Setup

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # then fill in your API key
```

## Run the API smoke test

Confirms your OpenAI API key works for both chat and embeddings before building anything else:

```bash
python scripts/smoke_test.py
```

## Architecture

_TBD — filled in as the pipeline is built (see PLAN.md Phase 1+)._

## Evaluation

_TBD — added in Phase 4._

## What's next

See `PLAN.md` for the full phased build plan.
