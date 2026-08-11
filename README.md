# Chat With Your Documents

Upload PDFs or text files, ask questions in a browser chat UI, and get answers grounded **only** in those documents — streamed token-by-token, with expandable citations showing the exact passage and page each answer came from.

Built as a learning + portfolio project. Full build plan: see [`PLAN.md`](PLAN.md).

## Status

Phases 0–4 complete: ingestion, retrieval, web app with streaming, citations, and an automated evaluation harness.

In progress: growing the eval set and running Phase 5 (data-driven tuning of chunk size, overlap, and `k`).

> _TODO: add a screenshot or demo GIF here._

## Stack

| Piece | Choice | Why |
|---|---|---|
| Backend | Python + FastAPI | Richest AI ecosystem; native async streaming |
| LLM | DeepSeek `v4-flash` (answers) + `v4-pro` (eval judge) | Any OpenAI-compatible provider works — swapping is a `.env` change, not a code change. Free options exist via OpenRouter, but their shared free pool returns intermittent 502s under eval load |
| Embeddings | `all-MiniLM-L6-v2` via `sentence-transformers` | Runs locally on CPU, no API key, no per-query cost |
| Vector store | Chroma (`PersistentClient`) | Local, zero infra, survives restarts |
| PDF parsing | `pypdf` | Page-level extraction, which is what makes citations possible |
| Frontend | Plain HTML/CSS/JS | No build step; the interesting problems here aren't frontend ones |

## Setup

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # then fill in your API key
```

`.env` takes a `CHAT_BASE_URL` and a matching `CHAT_API_KEY`; model ids go in `backend/app/config.py`. Any OpenAI-compatible provider works, with no code changes:

- **DeepSeek** (default) — `https://api.deepseek.com/v1`, key from https://platform.deepseek.com
- **OpenRouter** — `https://openrouter.ai/api/v1`, key from https://openrouter.ai/keys; free models exist (ids end in `:free`) but throttle under eval load

Model ids are provider-specific — the same model is `deepseek-v4-flash` on DeepSeek's own API and `deepseek/deepseek-v4-flash` on OpenRouter.

Verify both halves of the pipeline work (first run downloads the ~90MB embedding model):

```bash
python scripts/smoke_test.py
```

## Run

```bash
uvicorn backend.app.main:app --reload    # then open http://127.0.0.1:8000
```

Run all commands from the repo root — imports resolve as `backend.app.*` and paths are relative to the working directory.

There's also a terminal-only version of the pipeline, useful for debugging retrieval without the browser in the way:

```bash
python scripts/phase1_terminal.py
```

## Architecture

**Ingestion — runs once per uploaded file (`POST /upload`)**

```
PDF/txt → extract per page → chunk (~1000 chars, 100 overlap) → embed → store vector + metadata
```

Text is extracted **per page**, and each chunk carries its page number forward. That metadata is the entire basis for citations, so it has to survive chunking.

Chunking (`ingestion.py`) is a hand-written recursive splitter that tries `\n\n`, then `\n`, then `. `, then spaces, then a hard cut — so chunks land on semantic boundaries instead of mid-sentence. Overlap exists so a fact straddling a boundary survives intact in at least one chunk.

**Query — runs per question (`POST /chat`)**

```
question → embed (same model) → top-k similar chunks → build prompt → LLM → stream + citations
```

Retrieval and ingestion must use the same embedding model, or the vectors aren't comparable.

**Grounding.** The system prompt forbids outside knowledge, requires inline `[Source: file (Page X)]` citations, and mandates the exact string `"I don't know based on these documents."` when the context doesn't cover the question. Temperature is `0.0`. That instruction is most of what makes the output trustworthy — the model will happily answer from memory otherwise.

**Streaming.** The `/chat` response streams answer tokens, then a `___SOURCES___` sentinel, then a JSON blob of the retrieved chunks; the frontend splits on the sentinel to render markdown live and draw the source cards underneath. It's a custom protocol rather than true SSE — simple, but both sides must change together.

## Evaluation

```bash
python scripts/evaluate.py
```

Runs every question in `data/eval_set.json` through the real retrieval + generation path, grades each answer, and prints a pass rate.

Each run **rebuilds its own index** from a pinned document list into a separate `eval` collection, so a score depends only on the settings under test — not on whatever happens to be sitting in `chroma_db/` from earlier sessions, and without disturbing documents uploaded through the app. The retrieval knobs (`CHUNK_SIZE`, `CHUNK_OVERLAP`, `TOP_K`) are constants at the top of the script, and the summary reprints them alongside the score so a recorded run is self-describing.

**Current baseline:** 24 cases — `deepseek-v4-flash`, chunk 1000 / overlap 100 / top_k 4.

| Run | Score | Note |
|---|---|---|
| 1 | 23/24 (95.8%) | judge `max_tokens=100` |
| 2 | 24/24 (100%) | judge `max_tokens=100` |
| 3 | 12/24 (50.0%) | judge `max_tokens=100` |
| 4 | 24/24 (100%) | judge `max_tokens=2048` |

Identical pipeline, scores from 50% to 100% — a harness bug, not a retrieval one. The judge is a *reasoning* model, and its hidden reasoning tokens are billed against the same `max_tokens` budget as its answer. At 100 it usually ran out mid-thought and returned an **empty** verdict, which the parser scored as a failure. Measured directly: 6 of 8 identical judge calls came back `finish_reason='length'` with `content=''`.

Two things follow:

- **A silent grader failure looks exactly like a pipeline regression.** Run 3's failures included cases where expected and actual answers were byte-identical. The harness now raises on an empty verdict instead of counting it as a FAIL, so this can't be misread again.
- **The suite is at ceiling.** With the judge fixed, 24/24 — retrieval finds everything these questions need, including the five adversarial unanswerables. Harder questions are needed before chunk size or `k` can be meaningfully compared.

**Test set.** 24 question/expected-answer pairs over the coffee guide, grouped by what they stress:

- **Single-fact lookups** — brew temperature, decaf percentage, first crack.
- **Multi-hop synthesis** — e.g. "which species has more caffeine, and why is it used in espresso blends?", which requires joining facts from two different pages.
- **Contrarian facts** — the guide contradicts popular belief on dark-roast caffeine and fridge storage, so answering from world knowledge fails while answering from the document passes.
- **Adversarial unanswerables** — plausible coffee questions the guide never covers (caffeine per espresso *shot*, when it only states caffeine per 8oz *cup*; per-capita consumption, when it only lists production leaders). These retrieve confident-looking near-miss context, so they pass only if the app refuses rather than reaching for the nearby number.

Refusal behaviour is the easiest thing to regress when you loosen a prompt and the hardest to notice by hand, which is why a fifth of the set tests it.

**Scoring: LLM-as-judge.** A second call asks a model whether the actual answer is factually equivalent to the expected one, so paraphrases pass and only the facts matter. The judge is pinned to its own `JUDGE_MODEL` setting rather than reusing `CHAT_MODEL`, so swapping the answering model doesn't silently swap the grader too.

**Limitations, honestly:**

- The judge is itself an LLM — it can be wrong, and it shares a family of blind spots with the model it's grading.
- It scores the *answer*, not the *citation*. An answer can be right while pointing at the wrong page.
- **A reasoning judge needs headroom.** Its reasoning tokens share the `max_tokens` budget with its verdict; too small a cap silently turns every grade into a failure (see the run table above).
- **The suite is still at ceiling** at 24 cases, so it can prove the pipeline works but cannot yet rank two configurations against each other.

**Tuning results:** not yet. Growing the set from 5 to 24 cases — including multi-hop and adversarial-refusal questions — did not create headroom: the current configuration answers all of them. Producing a real before/after number needs questions this setup actually fails, which most likely means a larger corpus with cross-document distractors rather than more questions about one guide.

## What I'd do next

- Grow the eval set to ~20 cases across easy lookups, multi-part synthesis, and unanswerable questions — the suite is at ceiling and can't measure anything until it has headroom.
- Then run Phase 5 — sweep chunk size, overlap, and `k` one variable at a time, and record before/after here.
- Score citation accuracy, not just answer accuracy.
- Hybrid search (keyword + vector) and re-ranking of retrieved chunks — semantic search alone misses exact identifiers like part numbers.
- Conversation memory across turns; follow-up questions currently retrieve without any history.
- Deploy behind a public link.
