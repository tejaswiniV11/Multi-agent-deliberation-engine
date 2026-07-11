"""Application configuration, loaded once from the environment / .env file.

Everything tunable lives here so there are no magic constants scattered through
the code. Values are read from environment variables (populated by python-dotenv
from a local .env) with sensible defaults.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:  # pragma: no cover - only hit before dependencies install
    def load_dotenv() -> None:
        return None

load_dotenv()  # pull .env into os.environ if present


def _split(value: str) -> List[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass
class Settings:
    # --- App / server ---
    app_host: str = os.getenv("APP_HOST", "0.0.0.0")
    app_port: int = int(os.getenv("APP_PORT", "8001"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()
    cors_origins: List[str] = field(
        default_factory=lambda: _split(os.getenv("CORS_ORIGINS", "*"))
    )

    # --- Agent network ---
    agent_network: str = os.getenv("AGENT_NETWORK_NAME", "quorum")

    # BACKEND_MODE selects how we reach neuro-san:
    #   "live" -> connect to a running neuro-san server (real LLM agents)
    #   "demo" -> fully offline scripted deliberation using the real coded tools
    backend_mode: str = os.getenv("BACKEND_MODE", "demo").lower()

    # --- neuro-san server (used when backend_mode == "live") ---
    neuro_san_host: str = os.getenv("NEURO_SAN_SERVER_HOST", "localhost")
    neuro_san_port: int = int(os.getenv("NEURO_SAN_SERVER_PORT", "30011"))

    # --- LLM (neuro-san reads these itself; surfaced here for the /health page) ---
    llm_model: str = os.getenv("LLM_MODEL_NAME", "mistral-large-latest")

    @property
    def has_llm_key(self) -> bool:
        return any(
            os.getenv(k)
            for k in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "MISTRAL_API_KEY")
        )


settings = Settings()
