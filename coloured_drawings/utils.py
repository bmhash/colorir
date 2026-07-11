"""Shared utilities."""

import re
import unicodedata
from datetime import datetime
from pathlib import Path


def slugify(text: str, max_length: int = 40) -> str:
    """Convert free text into a filesystem-safe slug for directory names."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return text[:max_length].strip("-") or "desenho"


def make_output_dir(base: Path, prompt: str) -> Path:
    """Create a unique output directory: <slug>-<timestamp>."""
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = base / f"{slugify(prompt)}-{stamp}"
    out.mkdir(parents=True, exist_ok=True)
    return out
