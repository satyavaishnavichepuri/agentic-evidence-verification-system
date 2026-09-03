"""
Central configuration for VeriScope AI.

Everything here is optional. With a completely empty .env (or no .env
at all) the app runs in full DEMO MODE: no Gemini calls, in-memory
storage only. Setting GEMINI_API_KEY and/or DATABASE_URL upgrades the
same code paths transparently -- no feature flags to flip by hand.
"""
import os
from dotenv import load_dotenv

load_dotenv()


def _split_csv(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


class Settings:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip()
    DATABASE_URL: str = os.getenv("DATABASE_URL", "").strip()
    CORS_ORIGINS: list[str] = _split_csv(
        os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    )
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))

    @property
    def gemini_enabled(self) -> bool:
        return bool(self.GEMINI_API_KEY)

    @property
    def postgres_enabled(self) -> bool:
        return bool(self.DATABASE_URL)


settings = Settings()
