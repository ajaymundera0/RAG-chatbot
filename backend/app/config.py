"""
Loads environment variables once, so the rest of the app just imports `settings`.

Chat: any OpenAI-compatible endpoint (default: OpenRouter). Swapping providers
is a base URL + key + model id change, nothing more.
Embeddings: OpenAI text-embedding-3-small (requires OPENAI_API_KEY).
Vector Store: Pinecone (requires PINECONE_API_KEY).
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    CHAT_BASE_URL: str = os.getenv("CHAT_BASE_URL", "https://api.deepseek.com/v1")
    CHAT_API_KEY: str = os.getenv("CHAT_API_KEY", "")

    # Ids are provider-specific -- these are DeepSeek's own API names.
    CHAT_MODEL: str = "deepseek-v4-flash"

    # Pinned separately so the grader stays fixed while you tune CHAT_MODEL --
    # otherwise before/after scores measure two changes at once. Deliberately the
    # stronger model of the pair; same family, so watch for generous grading.
    JUDGE_MODEL: str = "deepseek-v4-pro"

    # Cloud embedding model (OpenAI)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    # Pinecone
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "rag-chatbot")

    def validate(self) -> None:
        if not self.CHAT_API_KEY:
            raise RuntimeError(
                "CHAT_API_KEY is missing. Copy .env.example to .env and add a key "
                "matching your CHAT_BASE_URL provider."
            )
        if not self.OPENAI_API_KEY:
            raise RuntimeError(
                "OPENAI_API_KEY is missing. You need it for embeddings."
            )
        if not self.PINECONE_API_KEY:
            raise RuntimeError(
                "PINECONE_API_KEY is missing. You need it for the vector database."
            )


settings = Settings()
