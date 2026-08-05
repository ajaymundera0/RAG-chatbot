# Chat With Your Documents — Complete Build Plan

A portfolio-grade RAG (Retrieval-Augmented Generation) application. Upload documents, ask questions, get answers grounded **only** in those documents — with citations back to the source and a real evaluation harness proving it works.

This plan is built for someone who can already code but is newer to AI apps. The goal is a defensible CV project that teaches the fundamentals underneath most modern AI products.

---

## 1. What you're building

A web app where a user can:

1. Upload one or more documents (PDF, `.txt`, `.md`).
2. Ask questions in a chat interface.
3. Get answers that are grounded in the uploaded documents, not the model's general knowledge.
4. See **which passage** each answer came from (citations).

And behind the scenes: a small **evaluation harness** that scores answer quality automatically, so you can prove the app works and measure when changes make it better or worse.

---

## 2. Why this project (the CV angle)

Recruiters and engineers recognize RAG instantly, and it exercises the skills that transfer to almost any AI product:

- **Embeddings & vector search** — the core mechanic behind most AI apps.
- **Chunking & retrieval strategy** — where answer quality is actually won or lost.
- **Prompt engineering inside a real pipeline** — injecting retrieved context, controlling output.
- **Streaming, API handling, cost/token awareness** — the unglamorous production skills.

Two additions lift it above "tutorial I followed":

- **Citations** → shows you actively fight hallucination.
- **Eval harness** → shows you think about *correctness*, not just wiring up an API. Almost no junior portfolio has this.

---

## 3. What you'll learn, mapped to the build

| Concept | Where it shows up | Why it matters |
|---|---|---|
| Embeddings | Turning chunks into vectors on upload | Foundation of semantic search |
| Vector databases | Storing & querying vectors | Core infra of RAG |
| Chunking strategy | Splitting documents pre-embedding | Biggest lever on answer quality |
| Retrieval (top-k, similarity) | Fetching relevant chunks per question | The "R" in RAG |
| Context injection & prompting | Building the final LLM prompt | Turns retrieval into answers |
| Streaming responses | Chat UI | Real-world UX + API handling |
| Grounding & citations | Mapping answers to sources | Hallucination control |
| Evaluation | Test set + scoring script | Engineering rigor |
| Agentic retrieval (Phase 2) | Multi-step tool use | Signals you're current |

---

## 4. Tech stack

Use what you already know wherever possible — the point is learning the AI parts, not fighting a new framework. Suggestions, not requirements:

- **Frontend:** whatever web stack you're comfortable in (React/Next.js, Vue, Svelte, or even plain HTML/JS for v1). Keep it minimal at first.
- **Backend:** Python (FastAPI) or Node (Express). Python has the richest AI ecosystem and more examples to lean on.
- **LLM API:** any major provider's chat + embeddings endpoints. Keep the provider behind a thin wrapper so you can swap it.
- **Vector store:**
  - *Start simple:* an in-memory store or a local library (e.g. FAISS, Chroma, or `sqlite-vec`). No infra to manage.
  - *Level up later:* a hosted vector DB (Pinecone, Weaviate, Qdrant, or Postgres + `pgvector`).
- **Document parsing:** a PDF text-extraction library; plain reads for `.txt`/`.md`.

> Note: AI libraries and model names move fast. Check the current official docs for whichever provider and vector store you pick rather than trusting any single tutorial's version numbers.

---

## 5. Architecture

**Ingestion pipeline (runs on upload):**

```
Upload → Extract text → Chunk → Embed each chunk → Store vectors + metadata
```

Store alongside each vector: the source filename, chunk text, and a position/page reference. You'll need that metadata for citations.

**Query pipeline (runs per question):**

```
Question → Embed question → Retrieve top-k similar chunks
        → Build prompt (question + retrieved chunks + instructions)
        → LLM generates answer → Stream to UI + attach citations
```

**The grounding instruction is critical.** Your system prompt should tell the model to answer *only* from the provided context and to say "I don't know based on these documents" when the context doesn't contain the answer. This single instruction is most of what makes RAG trustworthy.

---

## 6. Phased build plan

Ship each phase end-to-end before starting the next. A working ugly version beats a half-built elegant one.

### Phase 0 — Setup (Day 1)
- Repo, README stub, environment/secrets handling (API keys in env vars, never committed).
- "Hello world" call to the LLM API and to the embeddings API. Confirm both work.
- **Done when:** you can embed a string and get a chat completion from a script.

### Phase 1 — The ugly working version (Days 2–5)
- Ingestion: hardcode one document, extract text, chunk it (start with fixed ~500–1000 character chunks with some overlap), embed, store in an in-memory/local vector store.
- Query: take a typed question, embed it, retrieve top-k (start with k=4), stuff chunks into the prompt, return the answer.
- No UI yet — a command-line loop is fine.
- **Done when:** you can ask a question in the terminal and get a grounded answer from your document.

### Phase 2 — Make it a web app (Days 6–9)
- Minimal frontend: file upload + a chat box.
- Backend endpoints: `/upload` (runs ingestion) and `/chat` (runs query).
- Add **streaming** so answers appear token-by-token.
- Handle multiple documents and basic errors (bad file, empty result, API failure).
- **Done when:** a stranger could upload a PDF and chat with it in the browser.

### Phase 3 — Citations (Days 10–12)
- Return the retrieved chunks' metadata alongside the answer.
- In the UI, show sources under each answer (filename + page/snippet), ideally with the exact passage highlighted or expandable.
- Tighten the prompt so the model references which source supports each claim.
- **Done when:** every answer shows where it came from, and you can click through to verify.

### Phase 4 — Evaluation harness (Days 13–16) ← *the differentiator*
- Write ~20 question/expected-answer pairs based on your test documents. Cover easy lookups, multi-part questions, and questions the docs *can't* answer (to test that it correctly says "I don't know").
- Write a script that runs each question through your app and scores the output. Two common approaches:
  - **Keyword/assertion checks** for factual questions (does the answer contain the expected fact?).
  - **LLM-as-judge** — ask a model to rate whether the answer matches the expected answer. Note this is imperfect and say so; showing you *know* its limits is itself a strong signal.
- Print a summary score. Now you can measure whether changes help.
- **Done when:** you can run one command and get a score for your whole app.

### Phase 5 — Tune with data (Days 17–20)
- Use the eval to experiment *scientifically*: change chunk size, overlap, `k`, or the prompt, re-run the eval, keep what improves the score.
- Document 2–3 experiments and their results in your README. This "I measured X, changed Y, score went from A to B" story is gold in interviews.
- **Done when:** your README shows before/after numbers from real tuning.

### Phase 6 — Polish & ship
- Clean UI pass, loading states, empty states, mobile check.
- Deploy it somewhere with a public link.
- Write the README (see section 8).

---

## 7. Phase 2 (stretch): make it agentic

Once the RAG app is solid, this is the strongest "I'm current" upgrade:

- Instead of a single retrieval step, let the model **decide** to retrieve multiple times, reformulate the query, or ask a clarifying question before answering.
- Give it retrieval as a *tool* it can call in a loop, rather than a fixed step in your pipeline.
- Keep the old version working so you have a **before/after** story: "I built standard RAG, then rebuilt the query path as an agent that retrieves iteratively — here's how eval scores changed."

Other stretch ideas: conversation memory across turns, hybrid search (keyword + vector), re-ranking retrieved chunks, per-user document libraries with auth.

---

## 8. How to present it (CV + README)

**On your CV**, one line, results-first:

> Built a document Q&A app (RAG) with source citations and an automated evaluation harness; improved answer accuracy from X% to Y% by tuning retrieval and chunking.

**In the README**, include:
- A 2-sentence description + a screenshot or short demo GIF.
- The architecture diagram (reuse section 5).
- The tech stack and *why* you chose each piece.
- The evaluation section: your test set, scoring method (and its limitations), and before/after tuning results.
- "What I'd do next" — shows you know where it falls short (bigger eval set, better re-ranking, etc.).

Honesty about limitations reads as senior, not weak. Say what the eval can't catch and what you'd improve with more time.

---

## 9. Interview talking points to prepare

Be ready to explain, in your own words:

- Why RAG instead of just asking the model directly, or instead of fine-tuning.
- What embeddings are and why similarity search finds relevant chunks.
- How chunking affects quality, and the trade-offs of big vs. small chunks.
- How your citations work and how they reduce hallucination.
- How you evaluated the app and why evaluation is hard for open-ended answers.
- One concrete thing that surprised you or that you got wrong first (interviewers love this).

---

## 10. Common pitfalls to avoid

- **Skipping the eval** because it's "boring." It's the single most differentiating part — don't cut it.
- **Chunking too big or too small** and never testing alternatives. Let the eval decide.
- **Trusting the model to stay grounded without instruction.** Explicitly forbid outside knowledge in the prompt.
- **Over-engineering v1.** Get the terminal version working before touching a frontend or a hosted DB.
- **Committing API keys.** Use environment variables from day one.
- **Chasing a fancy framework** instead of learning the mechanics. Build the pieces yourself at least once so you understand what the framework hides.

---

## 11. Rough timeline summary

| Phase | Focus | Est. |
|---|---|---|
| 0 | Setup & API smoke test | ~1 day |
| 1 | Terminal RAG that works | ~4 days |
| 2 | Web app + streaming | ~4 days |
| 3 | Citations | ~3 days |
| 4 | Evaluation harness | ~4 days |
| 5 | Data-driven tuning | ~4 days |
| 6 | Polish & deploy | ~3 days |
| 2* | Agentic upgrade (stretch) | open-ended |

Roughly 3–4 weeks part-time to a strong, shippable v1. Adjust to your pace — shipping each phase matters more than hitting the day counts.

---

*Build ugly first. Ship each phase. Let the eval tell you what to improve.*
