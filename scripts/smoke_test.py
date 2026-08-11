"""
Phase 0 smoke test.

Confirms the two halves of the pipeline both work:
  1. Chat completions -- via Hugging Face's Inference Providers router (Nemotron)
  2. Embeddings -- run locally with sentence-transformers (no API key needed)

Run this before building anything else:
    python scripts/smoke_test.py

Note: the first run will download the local embedding model (~90MB) --
that's normal and only happens once.
"""
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from openai import OpenAI
from backend.app.config import settings


def test_chat() -> None:
    print("Testing chat completion (Hugging Face router -> Nemotron)...")
    client = OpenAI(base_url=settings.OPENROUTER_BASE_URL, api_key=settings.OPENROUTER_API_KEY)
    response = client.chat.completions.create(
        model=settings.CHAT_MODEL,
        messages=[{"role": "user", "content": "Reply with exactly: pong"}],
        max_tokens=100
    )
    reply = response.choices[0].message.content.strip()
    print(f"  Model replied: {reply!r}")
    assert reply, "Chat completion returned an empty response"
    print("  [OK] Chat completion works.\n")


def test_embeddings() -> None:
    print("Testing local embeddings (sentence-transformers)...")
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(settings.EMBEDDING_MODEL.replace("sentence-transformers/", ""))
    vector = model.encode("This is a test sentence for embeddings.")
    print(f"  Got embedding vector of length: {len(vector)}")
    assert len(vector) > 0, "Embedding was empty"
    print("  [OK] Embeddings work.\n")


def main() -> None:
    settings.validate()
    test_chat()
    test_embeddings()
    print("All smoke tests passed. You're ready to start Phase 1.")


if __name__ == "__main__":
    main()
