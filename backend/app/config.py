"""
Loads environment variables once, so the rest of the app just imports `settings`.

Chat: any OpenAI-compatible endpoint (default: OpenRouter). Swapping providers
is a base URL + key + model id change, nothing more.
Embeddings: local, via sentence-transformers -- no API key needed.
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

    # Local embedding model -- small, fast, runs on CPU, no key required.
    # Changing this invalidates every stored vector: wipe chroma_db/ and re-ingest.
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    def validate(self) -> None:
        if not self.CHAT_API_KEY:
            raise RuntimeError(
                "CHAT_API_KEY is missing. Copy .env.example to .env and add your key "
                "from https://openrouter.ai/keys"
            )


settings = Settings()
