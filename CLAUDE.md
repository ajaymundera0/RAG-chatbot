# CLAUDE.md

RAG app: upload PDFs/text, ask questions, get answers grounded only in the uploaded docs with inline citations. `PLAN.md` is the phased build plan; `README.md` is user-facing setup.

## Commands

```bash
pip install -r requirements.txt
cp .env.example .env                              # then add CHAT_API_KEY

python scripts/smoke_test.py                      # verify chat provider + local embeddings
python scripts/phase1_terminal.py                 # terminal RAG loop over data/sample.txt
python scripts/evaluate.py                        # LLM-as-judge eval over data/eval_set.json
uvicorn backend.app.main:app --reload             # API + frontend at http://127.0.0.1:8000
```

Run everything from the repo root — modules import as `backend.app.*` and paths (`data/`, `frontend/`) are relative to CWD.

There is no test framework. `scripts/smoke_test.py` (asserts) and `scripts/evaluate.py` (pass rate) are the checks.

## Architecture

Single flow, one module per stage:

`ingestion.py` → `vector_store.py` → `chat.py`, wired together by `main.py`.

- **`config.py`** — all env/model config on one `settings` singleton. `settings.validate()` fails fast if API keys are missing. Chat goes through any OpenAI-compatible endpoint (default OpenRouter); embeddings run via Pinecone Inference API (`multilingual-e5-large`). `JUDGE_MODEL` is deliberately separate from `CHAT_MODEL` so eval comparisons hold a fixed grader.
- **`ingestion.py`** — `load_document()` accepts a file-like object and returns one dict per PDF page (`{text, metadata: {page}}`); `.txt` collapses to a single page-1 dict. `chunk_text()` is a hand-rolled recursive splitter over `["\n\n", "\n", ". ", " ", ""]` with overlap, and it copies page metadata onto every chunk. Page numbers are what make citations work — keep metadata flowing through any change here.
- **`vector_store.py`** — Pinecone Serverless client. `search()` returns `[{text, metadata, distance}]`, which is the shape the rest of the app expects.
- **`chat.py`** — `generate_answer()` (blocking, used by eval) and `stream_answer()` (SSE, used by the API) build the same prompt: strict context-only system prompt, `temperature=0.0`, and the exact fallback string `"I don't know based on these documents."` — the eval set asserts on it, so don't reword it. The two functions duplicate their prompt; edit both. Providers can return HTTP 200 with an error payload and no `choices`, so `generate_answer` checks for that explicitly.
- **`main.py`** — `/upload` (process in-memory, chunk at size 1000 / overlap 100, index) and `/chat` (retrieve top_k, stream). The frontend is mounted at `/` **last** so API routes win.

Streaming protocol (custom, not real SSE): `stream_answer` yields answer tokens, then the literal `\n\n___SOURCES___\n`, then a JSON dump of the retrieved chunks. `frontend/script.js` splits on that sentinel to render the citations panel. Changing the sentinel or the trailing JSON breaks the UI.

Frontend is plain HTML/CSS/JS in `frontend/` — no build step.

## Notes

- Chunk sizes differ per entry point (terminal script 2000/500, API 1000/100) — intentional, small sample vs. real PDFs.
- Uploads are processed entirely in memory via the `UploadFile` stream; they do not touch the disk. This allows the app to be deployed to read-only environments like Vercel.
- `evaluate.py` rebuilds its own `eval` collection from `EVAL_DOCS` on every run, and never touches the app's main index.
- `.env` is gitignored. Never commit a real `CHAT_API_KEY` or `PINECONE_API_KEY`.
