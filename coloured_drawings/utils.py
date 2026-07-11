"""Utilitários partilhados."""

import re
import unicodedata
from datetime import datetime
from pathlib import Path


def slugify(text: str, max_length: int = 40) -> str:
    """Converte texto livre num slug seguro para nomes de pastas."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return text[:max_length].strip("-") or "desenho"


def make_output_dir(base: Path, prompt: str) -> Path:
    """Cria um diretório único para o desenho: <slug>-<timestamp>."""
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = base / f"{slugify(prompt)}-{stamp}"
    out.mkdir(parents=True, exist_ok=True)
    return out
