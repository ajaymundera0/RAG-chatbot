"""
Loads environment variables once, so the rest of the app just imports `settings`.

Chat: OpenRouter (OpenAI-compatible), serving Nemotron.
Embeddings: local, via sentence-transformers -- no API key needed.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    # Chat model served through OpenRouter
    CHAT_MODEL: str = "nvidia/nemotron-3-ultra-550b-a55b"

    # Local embedding model -- small, fast, runs on CPU, no key required
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    def validate(self) -> None:
        if not self.OPENROUTER_API_KEY:
            raise RuntimeError(
                "OPENROUTER_API_KEY is missing. Copy .env.example to .env and add your token "
                "from https://openrouter.ai/keys"
            )


settings = Settings()
