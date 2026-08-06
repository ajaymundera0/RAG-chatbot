"""
Loads environment variables once, so the rest of the app just imports `settings`.

Chat: Hugging Face Inference Providers router (OpenAI-compatible), serving Nemotron.
Embeddings: local, via sentence-transformers -- no API key needed.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    HF_TOKEN: str = os.getenv("HF_TOKEN", "")
    HF_BASE_URL: str = "https://router.huggingface.co/v1"

    # Chat model served through the HF router (adjust if you pick a different one)
    CHAT_MODEL: str = "nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B-NVFP4:together"

    # Local embedding model -- small, fast, runs on CPU, no key required
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    def validate(self) -> None:
        if not self.HF_TOKEN:
            raise RuntimeError(
                "HF_TOKEN is missing. Copy .env.example to .env and add your token "
                "from https://huggingface.co/settings/tokens"
            )


settings = Settings()
