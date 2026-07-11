# Implementation Guide

> Technical details for implementing each roadmap phase.
> Reference: `docs/decisions.md` for architectural rationale.
> Updated: 2025-07-12

---

## Current State Assessment

### Architecture

```
coloured_drawings/
├── cli.py              # Typer CLI (thin wrapper)
├── config.py           # Settings dataclass (env vars)
├── pipeline.py         # Orchestrator: fetch -> convert -> compose
├── image_utils.py      # A4 resize logic
├── utils.py            # slugify, output dir creation
├── lineart/
│   └── converter.py    # OpenCV: bilateral → threshold → morph → dilate
├── printing/
│   └── pdf.py          # Pillow: A4 page composition + PDF export
└── sources/
    ├── base.py         # ImageSource ABC + SourceError
    ├── ai_generator.py # OpenAI gpt-image-1
    ├── web_search.py   # DuckDuckGo + watermark filter
    └── watermark_detector.py  # OpenCV heuristics (4 strategies)
```

### Metrics

| Metric              | Value                       |
|---------------------|-----------------------------|
| Python version      | 3.12.3 (requires >= 3.11)   |
| Production LoC      | ~490 lines                  |
| Test LoC            | ~220 lines                  |
| Test count          | 19 tests, all passing       |
| Dependencies        | 8 runtime, 1 dev            |
| Build backend       | hatchling                   |
| CI/CD               | None                        |
| Linting             | None                        |
| Type checking       | None                        |
| Coverage            | Unknown (no tooling)        |
| Lock file           | None                        |

### Technical Debt

1. **No lock file** -- builds are non-deterministic
2. **No linting/formatting** -- code style is manual
3. **No type checking** -- type hints exist but are never verified
4. **No logging** -- debugging requires adding print statements
5. **No CI** -- tests only run when someone remembers
6. **Broad exception catching** -- `except Exception` hides root causes
7. **Magic numbers** -- OpenCV params scattered in function bodies
8. **No conftest.py** -- test fixtures are duplicated across files
9. **No pre-commit** -- quality checks run only in CI (when CI exists)
10. **Settings singleton pattern** -- `get_settings()` creates a new instance
    every call (harmless but wasteful)

---

## Phase 1 Implementation: Foundation & Developer Experience

### Step 1.1: Migrate to uv

**Prerequisites:** Install uv (`curl -LsSf https://astral.sh/uv/install.sh | sh`)

```bash
# From project root:
cd /home/bhash/repos/coloured-drawings

# Initialize uv project (reads existing pyproject.toml)
uv init --no-readme

# Sync dependencies (creates uv.lock)
uv sync

# Verify
uv run colorir --help
uv run pytest
```

**pyproject.toml changes:**

```toml
[project]
# ... existing fields stay ...
requires-python = ">=3.11"

[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-cov>=6.0",
    "ruff>=0.11",
    "pyright>=1.1",
    "pre-commit>=3.5",
]
```

**Note:** Move `pytest` from `[project.optional-dependencies].dev` to
`[dependency-groups].dev` (PEP 735 standard for dev tools).

**Update .gitignore:**
```
# Add:
uv.lock      # Track in git (deterministic builds)
# Keep existing entries
```

Wait -- `uv.lock` should be *committed*, not ignored. Remove any existing
ignore for it. The lock file is what guarantees reproducibility.

**Update README installation section:**
```bash
# Install uv (once)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and sync
git clone <repo-url>
cd coloured-drawings
uv sync

# Run
uv run colorir gerar "aladino da Disney"

# Or activate the venv
source .venv/bin/activate
colorir gerar "aladino da Disney"
```

---

### Step 1.2: Add Ruff configuration

**Add to `pyproject.toml`:**

```toml
[tool.ruff]
target-version = "py311"
line-length = 99
src = ["coloured_drawings", "tests"]

[tool.ruff.lint]
select = [
    "E",     # pycodestyle errors
    "W",     # pycodestyle warnings
    "F",     # pyflakes
    "UP",    # pyupgrade (modern Python syntax)
    "B",     # flake8-bugbear (common bugs)
    "SIM",   # flake8-simplify
    "I",     # isort (import sorting)
    "N",     # pep8-naming
    "S",     # bandit security checks
    "BLE",   # blind-except detection
    "T20",   # flake8-print (no print in production)
    "RET",   # return statement checks
    "TCH",   # type-checking imports
]
ignore = [
    "BLE001", # broad except (intentional in source error wrapping)
    "S603",   # subprocess calls (not used but prevent false positives)
    "T201",   # print (CLI uses typer.echo, but tests may print)
]

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S101"]  # assert is fine in tests

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

**First-time fix:**
```bash
uv run ruff check --fix .
uv run ruff format .
```

Review the diff, commit as a single "Apply Ruff formatting" commit.

---

### Step 1.3: Add Pyright configuration

**Add to `pyproject.toml`:**

```toml
[tool.pyright]
pythonVersion = "3.11"
typeCheckingMode = "basic"
include = ["coloured_drawings", "tests"]
reportMissingTypeStubs = false
reportUnknownMemberType = false
```

**Run and fix:**
```bash
uv run pyright
```

Expected issues:
- `Image.LANCZOS` deprecation (use `Image.Resampling.LANCZOS`)
- Possible `None` return from `response.data[0].b64_json`
- `Optional[str]` vs `str | None` inconsistencies (cli.py uses both)

Fix incrementally. Target: zero errors in `basic` mode.

---

### Step 1.4: Add pytest configuration

**Add to `pyproject.toml`:**

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--strict-markers --tb=short -q"
markers = [
    "slow: marks tests that hit external APIs or take >5s",
    "integration: marks tests that require network access",
]

[tool.coverage.run]
source = ["coloured_drawings"]
branch = true

[tool.coverage.report]
show_missing = true
skip_empty = true
fail_under = 80
exclude_lines = [
    "pragma: no cover",
    "if __name__ == .__main__.",
    "if TYPE_CHECKING:",
]
```

**Create `tests/conftest.py`:**

```python
"""Shared test fixtures."""

from pathlib import Path

import pytest
from PIL import Image


@pytest.fixture
def sample_image() -> Image.Image:
    """800x600 white image with a coloured circle (reusable across tests)."""
    from PIL import ImageDraw

    img = Image.new("RGB", (800, 600), "white")
    draw = ImageDraw.Draw(img)
    draw.ellipse((200, 150, 600, 450), fill=(100, 150, 200))
    return img


@pytest.fixture
def lineart_image() -> Image.Image:
    """Simple black-on-white image simulating lineart output."""
    from PIL import ImageDraw

    img = Image.new("RGB", (800, 1200), "white")
    draw = ImageDraw.Draw(img)
    draw.ellipse((100, 100, 700, 700), outline="black", width=4)
    draw.rectangle((200, 800, 600, 1100), outline="black", width=4)
    return img


@pytest.fixture
def tmp_output_dir(tmp_path: Path) -> Path:
    """Temporary output directory for pipeline tests."""
    out = tmp_path / "output"
    out.mkdir()
    return out
```

---

### Step 1.5: Add pre-commit configuration

**Create `.pre-commit-config.yaml`:**

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-toml
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=500']
      - id: check-merge-conflict

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.11.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: local
    hooks:
      - id: pyright
        name: pyright
        entry: uv run pyright
        language: system
        types: [python]
        pass_filenames: false
        stages: [pre-push]
```

**Install:**
```bash
uv run pre-commit install
uv run pre-commit install --hook-type pre-push
```

---

### Step 1.6: Add CI workflow

**Create `.github/workflows/ci.yml`:**

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read

jobs:
  quality:
    runs-on: ubuntu-22.04
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up uv
        uses: astral-sh/setup-uv@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: uv sync

      - name: Lint with Ruff
        run: uv run ruff check .

      - name: Check formatting
        run: uv run ruff format --check .

      - name: Type check with Pyright
        run: uv run pyright

      - name: Run tests with coverage
        run: |
          uv run pytest --cov --cov-report=xml --cov-report=term-missing

      - name: Upload coverage
        if: matrix.python-version == '3.12'
        uses: actions/upload-artifact@v4
        with:
          name: coverage-report
          path: coverage.xml
```

---

### Step 1.7: Add logging infrastructure

**Create/modify `coloured_drawings/log.py`:**

```python
"""Logging configuration for the CLI."""

import logging
import sys


def setup_logging(verbosity: int = 0) -> None:
    """Configure root logger based on CLI verbosity level.

    verbosity: 0 = WARNING (default), 1 = INFO (--verbose), 2 = DEBUG (--debug)
    """
    level = {0: logging.WARNING, 1: logging.INFO}.get(verbosity, logging.DEBUG)
    logging.basicConfig(
        level=level,
        format="%(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )
```

**Usage in modules (example -- `web_search.py`):**

```python
import logging

log = logging.getLogger(__name__)

# In _try_download:
log.debug("Downloading %s", url)
# ...
log.debug("Image %s rejected: too small (%dx%d)", url, *image.size)
log.debug("Image %s rejected: watermark detected", url)
log.info("Using image from %s (%dx%d)", url, *image.size)
```

**CLI integration (`cli.py`):**

```python
from coloured_drawings.log import setup_logging

# Add to app callback:
@app.callback()
def main(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show progress details"),
    debug: bool = typer.Option(False, "--debug", help="Show full debug output"),
) -> None:
    """Gerador de desenhos para colorir."""
    setup_logging(verbosity=2 if debug else (1 if verbose else 0))
```

---

### Step 1.8: Add project hygiene files

**`LICENSE` (MIT):**
```
MIT License

Copyright (c) 2025 [Your Name]

Permission is hereby granted, free of charge, to any person obtaining a copy
...
```

**`CONTRIBUTING.md`:**
```markdown
# Contributing

## Setup

    curl -LsSf https://astral.sh/uv/install.sh | sh
    git clone <repo-url>
    cd coloured-drawings
    uv sync
    uv run pre-commit install

## Development workflow

    uv run pytest                # Run tests
    uv run ruff check --fix .   # Lint + auto-fix
    uv run ruff format .        # Format
    uv run pyright              # Type check

## Before committing

Pre-commit hooks run automatically. To run manually:

    uv run pre-commit run --all-files

## Adding a new image source

1. Create `coloured_drawings/sources/your_source.py`
2. Implement the `ImageSource` interface (see `base.py`)
3. Register in `coloured_drawings/sources/__init__.py`
4. Add tests in `tests/test_your_source.py`
5. Document in README.md
```

**`CHANGELOG.md`:**
```markdown
# Changelog

All notable changes to this project will be documented in this file.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)

## [Unreleased]

### Added
- Developer tooling: Ruff, Pyright, pre-commit, CI pipeline
- Logging infrastructure with --verbose/--debug flags
- pytest-cov for coverage reporting
- CONTRIBUTING.md, LICENSE, this CHANGELOG

## [0.1.0] - 2025-07-11

### Added
- CLI commands: `gerar`, `converter`, `listar`
- AI source (OpenAI gpt-image-1)
- Web source (DuckDuckGo image search)
- Watermark detection and filtering
- OpenCV line-art conversion with configurable detail level
- A4 PDF generation at 300 DPI with optional title
- Landscape mode support
- `--sem-filtro-watermark` flag for web source
```

**`.editorconfig`:**
```ini
root = true

[*]
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true
charset = utf-8

[*.py]
indent_style = space
indent_size = 4
max_line_length = 99

[*.{toml,yaml,yml}]
indent_style = space
indent_size = 2

[*.md]
trim_trailing_whitespace = false
```

---

### Step 1.9: Docker distribution

**Files already created:**
- `Dockerfile` -- multi-stage build (builder + runtime)
- `.dockerignore` -- excludes dev artifacts
- `docker-compose.yml` -- local convenience wrapper

**Build and test locally:**
```bash
docker build -t colorir .
docker run --rm colorir --help
docker run --rm -v ./output:/app/output colorir gerar "gato" --fonte web
```

**GitHub Actions workflow for image publishing:**

Create `.github/workflows/docker.yml`:

```yaml
name: Docker

on:
  push:
    tags: ["v*"]

permissions:
  contents: read
  packages: write

jobs:
  build-and-push:
    runs-on: ubuntu-22.04
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract version from tag
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/${{ github.repository }}
          tags: |
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=raw,value=latest

      - name: Build and push
        uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          platforms: linux/amd64,linux/arm64
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

**Shell alias for Docker users (add to README):**

```bash
# Add to ~/.bashrc or ~/.zshrc for convenience:
alias colorir='docker run --rm -v "$(pwd)/output:/app/output" -e OPENAI_API_KEY colorir'

# Then use normally:
colorir gerar "unicornio" --fonte web
```

---

## Phase 1 Verification Checklist

After completing all steps, verify:

```bash
# 1. Fresh clone experience works
git clone <repo> /tmp/test-clone
cd /tmp/test-clone
uv sync
uv run colorir --help

# 2. All quality gates pass
uv run ruff check .          # Zero errors
uv run ruff format --check . # Zero changes needed
uv run pyright               # Zero errors
uv run pytest --cov          # All pass, >= 80% coverage

# 3. Pre-commit works
uv run pre-commit run --all-files  # All hooks pass

# 4. Docker works
docker build -t colorir .
docker run --rm colorir --help     # Shows CLI help
docker run --rm -v ./output:/app/output colorir gerar "teste" --fonte web

# 5. CI would pass
# (Push to a branch and verify GitHub Actions green)
```

---

## Phase 2 Implementation Notes

### Adding a new source (e.g., Stability AI)

```python
# coloured_drawings/sources/stability.py
"""Stability AI source (SDXL Turbo for line-art generation)."""

import logging

from PIL import Image

from coloured_drawings.config import get_settings
from coloured_drawings.sources.base import ImageSource, SourceError

log = logging.getLogger(__name__)


class StabilitySource(ImageSource):
    name = "stability"
    produces_lineart = True  # if generating line-art directly

    def fetch(self, prompt: str) -> Image.Image:
        log.info("Generating via Stability AI: %s", prompt)
        # Implementation here
        ...
```

Register in `sources/__init__.py`:
```python
if name == "stability":
    from coloured_drawings.sources.stability import StabilitySource
    return StabilitySource()
```

### Async migration for web source

```python
# Future: replace requests with httpx for async downloads
import httpx

async def _download_batch(urls: list[str]) -> list[Image.Image | None]:
    async with httpx.AsyncClient(timeout=15) as client:
        tasks = [client.get(url) for url in urls]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        return [_parse_response(r) for r in responses]
```

### Caching strategy

```python
# coloured_drawings/cache.py
"""Simple file-based cache for downloaded/generated images."""

import hashlib
import json
from pathlib import Path
from datetime import datetime, timedelta

CACHE_DIR = Path.home() / ".cache" / "coloured-drawings"
CACHE_TTL = timedelta(hours=24)


def cache_key(prompt: str, source: str) -> str:
    return hashlib.sha256(f"{source}:{prompt}".encode()).hexdigest()[:16]


def get_cached(prompt: str, source: str) -> Path | None:
    key = cache_key(prompt, source)
    meta_file = CACHE_DIR / f"{key}.json"
    if not meta_file.exists():
        return None
    meta = json.loads(meta_file.read_text())
    created = datetime.fromisoformat(meta["created"])
    if datetime.now() - created > CACHE_TTL:
        return None
    image_path = CACHE_DIR / meta["filename"]
    return image_path if image_path.exists() else None
```

---

## Phase 3 Implementation Notes

### FastAPI application structure

```
coloured_drawings/
├── web/
│   ├── __init__.py
│   ├── app.py          # FastAPI app factory
│   ├── routes.py       # API endpoints
│   ├── deps.py         # Dependency injection
│   ├── templates/      # Jinja2 templates
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── gallery.html
│   │   └── detail.html
│   └── static/
│       ├── style.css
│       └── htmx.min.js
```

### Dockerfile

```dockerfile
FROM python:3.12-slim AS base

# System deps for OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender1 \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY coloured_drawings/ coloured_drawings/

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "coloured_drawings.web.app:create_app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml

```yaml
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - COLORIR_OUTPUT_DIR=/data/output
    volumes:
      - output-data:/data/output
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 5s
      retries: 3

volumes:
  output-data:
```

---

## Coding Standards

### Module structure

Every module follows this pattern:

```python
"""One-line description of the module's purpose."""

import logging                    # stdlib imports first
from pathlib import Path

import numpy as np                # third-party imports
from PIL import Image

from coloured_drawings.config import get_settings  # local imports

log = logging.getLogger(__name__)


# Module-level constants
MY_CONSTANT = 42


# Public API
def public_function(...) -> ...:
    """Docstring with description, params, returns."""
    ...


# Private helpers
def _helper(...) -> ...:
    ...
```

### Error handling philosophy

```python
# DO: Catch specific exceptions, log them, re-raise as SourceError
try:
    response = client.images.generate(...)
except openai.RateLimitError as exc:
    log.warning("Rate limited by OpenAI: %s", exc)
    raise SourceError("API está sobrecarregada. Tenta novamente em 1 minuto.") from exc
except openai.AuthenticationError as exc:
    log.error("Invalid API key")
    raise SourceError("OPENAI_API_KEY inválida. Verifica o .env.") from exc

# DON'T: Bare except Exception that hides everything
try:
    ...
except Exception as exc:
    raise SourceError(f"Falha: {exc}") from exc
```

### Type hints

```python
# Use modern syntax (Python 3.11+)
def process(image: Image.Image, options: dict[str, int] | None = None) -> Path:
    ...

# Use Protocols for duck typing
from typing import Protocol

class Printable(Protocol):
    def to_pdf(self, path: Path) -> Path: ...
```

### Testing conventions

```python
# File: tests/test_<module>.py
# Naming: test_<function>_<scenario>

def test_slugify_removes_accents_and_symbols():
    """Descriptive docstring explains the scenario being tested."""
    assert slugify("Aladino da Disney!") == "aladino-da-disney"

def test_slugify_empty_input_returns_fallback():
    assert slugify("???") == "desenho"
```

---

## Dependencies (Target State after Phase 1)

### Runtime

| Package                  | Version  | Purpose                    |
|--------------------------|----------|----------------------------|
| typer                    | >= 0.12  | CLI framework              |
| pillow                   | >= 10.2  | Image processing + PDF     |
| opencv-python-headless   | >= 4.9   | Line-art conversion        |
| numpy                    | >= 1.26  | Array operations           |
| requests                 | >= 2.31  | HTTP client (web source)   |
| ddgs                     | >= 9.0   | DuckDuckGo image search    |
| openai                   | >= 1.30  | AI image generation        |
| python-dotenv            | >= 1.0   | .env file loading          |

### Development

| Package    | Version | Purpose              |
|------------|---------|----------------------|
| pytest     | >= 8.0  | Test framework       |
| pytest-cov | >= 6.0  | Coverage reporting   |
| ruff       | >= 0.11 | Lint + format        |
| pyright    | >= 1.1  | Type checking        |
| pre-commit | >= 3.5  | Git hooks framework  |

---

## Commands Reference (Target State)

```bash
# Daily development
uv sync                          # Install/update all deps
uv run colorir gerar "gato"      # Run the CLI
uv run pytest                    # Run tests
uv run pytest --cov              # Run tests with coverage
uv run ruff check --fix .        # Lint + auto-fix
uv run ruff format .             # Format code
uv run pyright                   # Type check
uv run pre-commit run --all-files # Run all hooks

# One-time setup
uv sync                          # After cloning
uv run pre-commit install        # Enable git hooks
cp .env.example .env             # Configure API keys
```
