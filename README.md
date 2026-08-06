# Chat With Your Documents

A RAG (Retrieval-Augmented Generation) app: upload documents, ask questions, get answers grounded in the source material — with citations back to the exact passage.

Built as a learning + portfolio project. Full build plan: see `PLAN.md`.

## Status

🚧 Phase 0 — project setup in progress.

## Stack

- **Backend:** Python (FastAPI)
- **LLM:** Nemotron, via Hugging Face's Inference Providers router (free, OpenAI-compatible)
- **Embeddings:** local, via `sentence-transformers` (open-source, no API key, runs on CPU)
- **Vector store:** TBD (starting local/in-memory, see PLAN.md)

## Setup

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # then fill in your Hugging Face token
```

Get a free token at https://huggingface.co/settings/tokens — make sure "Make calls to Inference Providers" is enabled on it.

## Run the API smoke test

Confirms your HF token works for chat, and that local embeddings work:

```bash
python scripts/smoke_test.py
```

(First run downloads a small local embedding model — that's expected.)

## Architecture

_TBD — filled in as the pipeline is built (see PLAN.md Phase 1+)._

## Evaluation

_TBD — added in Phase 4._

## What's next

See `PLAN.md` for the full phased build plan.
