"""Central configuration: environment variables and defaults."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    openai_api_key: str = field(default_factory=lambda: os.environ.get("OPENAI_API_KEY", ""))
    ai_model: str = field(default_factory=lambda: os.environ.get("COLORIR_AI_MODEL", "gpt-image-1"))
    output_dir: Path = field(
        default_factory=lambda: Path(os.environ.get("COLORIR_OUTPUT_DIR", "output"))
    )


def get_settings() -> Settings:
    return Settings()
