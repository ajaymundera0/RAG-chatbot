"""
Loads environment variables once, so the rest of the app just imports `settings`.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    CHAT_MODEL: str = "gpt-4o-mini"          # good default: cheap + capable, fine for RAG
    EMBEDDING_MODEL: str = "text-embedding-3-small"  # good default: cheap + solid quality

    def validate(self) -> None:
        if not self.OPENAI_API_KEY:
            raise RuntimeError(
                "OPENAI_API_KEY is missing. Copy .env.example to .env and add your key."
            )


settings = Settings()
