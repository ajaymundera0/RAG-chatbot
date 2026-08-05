"""
Phase 0 smoke test.

Confirms your OpenAI API key works for BOTH:
  1. Chat completions (the "generation" half of RAG)
  2. Embeddings (the "retrieval" half of RAG)

Run this before building anything else:
    python scripts/smoke_test.py
"""
import sys
import os

# Allow running this script directly from the project root
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from openai import OpenAI
from backend.app.config import settings


def test_chat(client: OpenAI) -> None:
    print("Testing chat completion...")
    response = client.chat.completions.create(
        model=settings.CHAT_MODEL,
        messages=[{"role": "user", "content": "Reply with exactly: pong"}],
        max_tokens=10,
    )
    reply = response.choices[0].message.content.strip()
    print(f"  Model replied: {reply!r}")
    assert reply, "Chat completion returned an empty response"
    print("  ✅ Chat completion works.\n")


def test_embeddings(client: OpenAI) -> None:
    print("Testing embeddings...")
    response = client.embeddings.create(
        model=settings.EMBEDDING_MODEL,
        input="This is a test sentence for embeddings.",
    )
    vector = response.data[0].embedding
    print(f"  Got embedding vector of length: {len(vector)}")
    assert len(vector) > 0, "Embedding response was empty"
    print("  ✅ Embeddings work.\n")


def main() -> None:
    settings.validate()
    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    test_chat(client)
    test_embeddings(client)

    print("All smoke tests passed. You're ready to start Phase 1.")


if __name__ == "__main__":
    main()
