# Architecture Decision Records

> Format: [MADR 4.0.0](https://adr.github.io/madr/) | Location: `docs/decisions.md`
>
> Each decision is numbered sequentially. Superseded decisions stay for context
> with a `Superseded by ADR-XXX` note.

---

## ADR-001: Python as implementation language

- **Status:** Accepted
- **Date:** 2025-07-11

### Context and Problem Statement

We need a language for a CLI tool that fetches/generates images, applies computer
vision transforms, and produces print-ready PDFs. The developer (papá) is most
productive in Python and the ecosystem for image processing and AI APIs is
strongest there.

### Decision Drivers

- Developer familiarity and velocity
- Ecosystem maturity for image processing (OpenCV, Pillow) and AI (OpenAI SDK)
- Rapid prototyping for a personal/family project
- Cross-platform support (Linux primary, macOS/Windows possible)

### Decision Outcome

**Chosen: Python 3.11+** with modern type hints (`X | None` syntax).

- **Positive:** Fastest path to working software; best-in-class libraries for
  every pipeline stage; easy for contributors to understand.
- **Negative:** Slower runtime than compiled languages (acceptable for a CLI
  tool where network I/O dominates).

---

## ADR-002: Typer for CLI framework

- **Status:** Accepted
- **Date:** 2025-07-11

### Context and Problem Statement

The tool needs a CLI interface with commands (`gerar`, `converter`, `listar`),
typed options, and user-friendly help text.

### Considered Options

1. **argparse** -- stdlib, zero deps, verbose boilerplate
2. **click** -- mature, large API surface, manual type declarations
3. **typer** -- built on click, leverages type hints for zero-boilerplate CLI

### Decision Outcome

**Chosen: Typer** (>= 0.12).

- **Positive:** Type hints drive the CLI definition; auto-generated help; rich
  error formatting via Rich; minimal code for maximum functionality.
- **Negative:** Extra dependency (click + typer + rich). Acceptable given the
  small footprint.

---

## ADR-003: Three-stage pipeline architecture

- **Status:** Accepted
- **Date:** 2025-07-11

### Context and Problem Statement

The tool performs: (1) image acquisition, (2) line-art conversion, (3) PDF
composition. These stages have no shared state and different extension patterns.

### Decision Outcome

**Chosen: Decoupled pipeline with pluggable sources.**

```
Sources (fetch) --> Lineart (convert) --> Printing (compose)
    ^                                         |
    |            pipeline.py orchestrates      |
    +------------------------------------------+
```

- `sources/` implements `ImageSource` ABC -- new sources (Stability, Gemini,
  local files) plug in without touching pipeline code.
- `lineart/` owns OpenCV processing -- swappable for ML-based conversion later.
- `printing/` owns A4 composition -- swappable for other paper sizes or formats.
- `pipeline.py` is the thin orchestrator; `cli.py` is a thinner wrapper on top.

- **Positive:** Each stage is independently testable and replaceable. The
  README already notes that a future web UI reuses `pipeline.py` unchanged.
- **Negative:** Slight indirection for a small codebase. Worthwhile given the
  planned v2 (web UI).

---

## ADR-004: OpenCV-headless for line-art conversion

- **Status:** Accepted
- **Date:** 2025-07-11

### Context and Problem Statement

Converting colour images to black-and-white line art suitable for children to
colour. Needs bilateral filtering, adaptive thresholding, morphological cleanup.

### Considered Options

1. **Pillow only** -- limited filter primitives, no adaptive threshold
2. **opencv-python** -- full GUI support, pulls in Qt/GTK
3. **opencv-python-headless** -- same algorithms, no GUI dependencies
4. **scikit-image** -- Pythonic API, slower, heavier install

### Decision Outcome

**Chosen: opencv-python-headless** (>= 4.9).

- **Positive:** Full OpenCV algorithm suite without ~200 MB of GUI libs; ideal
  for CLI/server environments; bilateral filter + adaptive threshold is the
  proven approach for colouring-book line art.
- **Negative:** NumPy array dance between Pillow and OpenCV. Manageable with
  `np.array()` / `Image.fromarray()`.

---

## ADR-005: Pillow for PDF generation (not ReportLab/WeasyPrint)

- **Status:** Accepted
- **Date:** 2025-07-11

### Context and Problem Statement

The output is a single-page PDF: one centred image on an A4 page with optional
title text. No multi-page, no tables, no vector graphics.

### Considered Options

1. **ReportLab** -- full PDF toolkit, overkill for single-page raster PDFs
2. **WeasyPrint** -- HTML-to-PDF, extreme overkill, heavy native deps
3. **Pillow `Image.save("PDF")`** -- raster PDF, zero extra deps, perfect for
   our use case

### Decision Outcome

**Chosen: Pillow's built-in PDF export.**

- **Positive:** Zero additional dependencies; A4 @ 300 DPI is natively
  supported; title rendering via `ImageDraw.text()` is sufficient.
- **Negative:** Raster-only PDF (no vector outlines). Acceptable -- the source
  images are raster and 300 DPI is print-quality.

---

## ADR-006: DuckDuckGo as free image source

- **Status:** Accepted
- **Date:** 2025-07-11

### Context and Problem Statement

Not all users have an OpenAI API key. We need a free, no-auth image source that
returns "colouring page" images from the web.

### Considered Options

1. **Google Custom Search API** -- requires API key + billing
2. **Bing Image Search API** -- requires Azure subscription
3. **DuckDuckGo via `ddgs`** -- free, no auth, SafeSearch support
4. **Unsplash API** -- free tier, but photos not colouring pages

### Decision Outcome

**Chosen: DuckDuckGo via the `ddgs` library** (>= 9.0).

- **Positive:** Zero cost; SafeSearch=on for child-safe results; no API key
  needed; sorts by image size for best resolution.
- **Negative:** Quality is variable; many results have watermarks (mitigated by
  ADR-007). Rate limiting is opaque. The `ddgs` library scrapes DDG's
  undocumented API -- may break without notice.

---

## ADR-007: Heuristic watermark detection

- **Status:** Accepted
- **Date:** 2025-07-11

### Context and Problem Statement

Web-sourced images frequently contain stock-photo watermarks that ruin the
colouring page. We need to filter these automatically.

### Decision Outcome

**Chosen: OpenCV heuristic detector** with four strategies:
1. Corner density analysis (15% margins)
2. Border density analysis (8% margins)
3. Global contour density
4. Repetitive pattern detection (4x4 grid variance)

Configurable `sensitivity` (0.0 permissive -- 1.0 strict), defaulting to 0.5.
User can bypass entirely with `--sem-filtro-watermark`.

- **Positive:** No external service or ML model needed; fast (pure OpenCV);
  catches the most common watermark patterns; user has full control.
- **Negative:** Heuristic -- false positives on busy images, false negatives on
  subtle watermarks. The 0.5 default was tuned empirically from the 0.7 that
  was "demasiado restritivo".

### Future Consideration

An ML-based detector (e.g., a small ONNX model) could replace the heuristics
when accuracy becomes critical. The `has_watermark()` function signature stays
the same -- callers won't change.

---

## ADR-008: Hatchling as build backend

- **Status:** Accepted
- **Date:** 2025-07-11

### Context and Problem Statement

We need a PEP 517/621-compliant build backend for `pyproject.toml`.

### Considered Options

1. **setuptools** -- legacy, requires `setup.py` or `setup.cfg` escape hatches
2. **flit-core** -- minimal, no plugin model
3. **hatchling** -- PyPA-endorsed, native PEP 621, plugin-ready
4. **poetry-core** -- tied to Poetry ecosystem

### Decision Outcome

**Chosen: hatchling.**

- **Positive:** First-class `pyproject.toml` support; lightweight; official PyPA
  project; integrates with `hatch` CLI for environments and matrix testing.
- **Negative:** No native lock file (mitigated by future migration to `uv` --
  see ADR-009).

---

## ADR-009: Migrate to `uv` for dependency management

- **Status:** Proposed
- **Date:** 2025-07-12

### Context and Problem Statement

The project currently uses `pip install -e ".[dev]"` with no lock file.
Builds are not reproducible -- different developers/CI runs may get different
dependency versions.

### Decision Drivers

- Reproducible builds via lock file
- CI speed (uv is 5-10x faster than pip)
- PEP 751 `pylock.toml` support for interoperability
- Single tool for Python version management + dependency resolution

### Considered Options

1. **pip + requirements.txt** -- manual lock management, no resolver guarantees
2. **pip-tools** -- `pip-compile` generates pinned requirements, mature but slow
3. **Poetry** -- lock file + resolver, slower than uv, non-standard metadata
4. **uv** -- Rust-based, 10-100x faster, native PEP 621, `uv.lock` + `pylock.toml` export

### Decision Outcome

**Chosen: uv** -- migrate from bare pip to `uv` with `uv.lock`.

- **Positive:** Deterministic builds; fastest resolver available; replaces
  `python -m venv` + `pip install` with `uv sync`; `uv run pytest` replaces
  manual venv activation; cross-platform lock file.
- **Negative:** Relatively new tool (Astral, 2024). Mitigated by broad adoption
  and PEP 751 export for fallback.

### Implementation

See `implementation.md` Phase 1.

---

## ADR-010: Adopt Ruff as sole linter and formatter

- **Status:** Proposed
- **Date:** 2025-07-12

### Context and Problem Statement

The project has no linting or formatting tools configured. Code style is
manually maintained. As the codebase grows (especially with a web UI), we need
automated enforcement.

### Decision Outcome

**Chosen: Ruff** -- replaces Black, isort, flake8, pyupgrade, and pydocstyle
with a single Rust-based tool.

Rule set:
```toml
[tool.ruff]
target-version = "py311"
line-length = 99

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "UP",   # pyupgrade
    "B",    # flake8-bugbear
    "SIM",  # flake8-simplify
    "I",    # isort
    "N",    # pep8-naming
    "S",    # flake8-bandit (security)
    "BLE",  # flake8-blind-except
]
ignore = ["BLE001"]  # intentional broad except in source error wrapping
```

- **Positive:** 10-100x faster than the tools it replaces; single config in
  `pyproject.toml`; includes security rules (bandit subset).
- **Negative:** May flag existing code on first run. One-time fix.

---

## ADR-011: Add structured logging with stdlib `logging`

- **Status:** Proposed
- **Date:** 2025-07-12

### Context and Problem Statement

The project has zero logging. Debugging issues (failed downloads, watermark
false positives, OpenAI errors) requires adding print statements ad-hoc.

### Considered Options

1. **stdlib `logging`** -- zero deps, well-understood, sufficient for a CLI tool
2. **structlog** -- structured JSON logging, better for services/observability
3. **loguru** -- pretty output, magic globals, non-standard

### Decision Outcome

**Chosen: stdlib `logging`** -- the project is a CLI tool, not a long-running
service. structlog's structured output adds complexity without clear benefit
here. Each module gets `log = logging.getLogger(__name__)`.

CLI configures the root logger based on `--verbose` flag:
- Default: `WARNING` (quiet operation)
- `--verbose`: `INFO` (progress details)
- `--debug`: `DEBUG` (full diagnostics including OpenCV params, HTTP responses)

- **Positive:** Zero dependencies; hierarchical loggers per module; users
  control verbosity; debug output available without code changes.
- **Negative:** Less structured than structlog. Acceptable for CLI scope.

---

## ADR-012: GitHub Actions for CI/CD

- **Status:** Proposed
- **Date:** 2025-07-12

### Context and Problem Statement

There is no CI. Tests only run when someone remembers to type `pytest`.

### Decision Outcome

**Chosen: GitHub Actions** with the following pipeline:

```
push/PR --> Lint (ruff) --> Type Check (pyright) --> Test (pytest + coverage)
```

Matrix: Python 3.11 + 3.12, ubuntu-22.04.

- **Positive:** Free for public repos; fast with `uv` caching; enforces quality
  gates before merge; badge in README signals project health.
- **Negative:** Vendor lock-in to GitHub. Acceptable -- the repo is on GitHub.

---

## ADR-013: Add type checking with Pyright

- **Status:** Proposed
- **Date:** 2025-07-12

### Context and Problem Statement

The codebase uses type hints but they are never statically verified. Incorrect
hints rot silently.

### Considered Options

1. **mypy** -- reference implementation, 58% typing spec conformance, plugin system
2. **pyright** -- 98% spec conformance, 2-5x faster, best IDE integration
3. **ty** -- 10-100x faster, beta, 53% spec conformance

### Decision Outcome

**Chosen: Pyright** in basic mode, progressing to standard mode.

- **Positive:** Catches real bugs; validates the existing type hints; best
  conformance to the typing spec; native VS Code integration via Pylance.
- **Negative:** Stricter than mypy -- may surface more issues initially. This
  is a feature, not a bug.

Configuration:
```toml
[tool.pyright]
pythonVersion = "3.11"
typeCheckingMode = "basic"
reportMissingTypeStubs = false
```

---

## ADR-014: Pre-commit hooks for developer experience

- **Status:** Proposed
- **Date:** 2025-07-12

### Context and Problem Statement

Without local enforcement, developers push code that fails CI lint/format
checks, wasting round-trip time.

### Decision Outcome

**Chosen: pre-commit framework** with the following hooks:

| Stage    | Hook                           | Purpose                        |
|----------|--------------------------------|--------------------------------|
| commit   | `ruff check --fix`             | Lint + auto-fix                |
| commit   | `ruff format`                  | Format                         |
| commit   | `check-toml`, `check-yaml`     | Config file syntax             |
| commit   | `check-added-large-files`      | Prevent accidental large blobs |
| commit   | `trailing-whitespace`          | Clean whitespace               |
| push     | `pytest` (fast subset)         | Smoke test before push         |

- **Positive:** Catches issues before they reach CI; auto-fixes formatting;
  fast (Ruff runs in milliseconds).
- **Negative:** Requires `pre-commit install` per clone. Documented in
  CONTRIBUTING.md.

---

## ADR-015: Web UI architecture (v2)

- **Status:** Proposed
- **Date:** 2025-07-12

### Context and Problem Statement

The README mentions "a v2 (UI web) reutiliza o pipeline sem alterações". We need
to choose a web framework that wraps the existing Python pipeline.

### Considered Options

1. **FastAPI + HTMX** -- Python backend serves HTML fragments, minimal JS,
   leverages the existing pipeline directly
2. **FastAPI + React SPA** -- separate frontend, API-driven, more complex
3. **Streamlit** -- rapid prototyping, limited customisation
4. **Gradio** -- ML-focused, good for image I/O demos
5. **Django** -- full framework, overkill for single-purpose app

### Decision Outcome

**Chosen: FastAPI + HTMX** (deferred to Phase 3 of roadmap).

- **Positive:** The pipeline stays in-process (no serialisation overhead);
  HTMX keeps the frontend minimal (no npm/webpack/bundler); FastAPI gives
  async endpoint support for long-running generation; Jinja2 templates
  are simple to maintain.
- **Negative:** HTMX is less capable than a full SPA for complex
  interactivity. Sufficient for "type prompt, see result, print PDF".

---

## ADR-016: Docker for CLI distribution

- **Status:** Accepted
- **Date:** 2025-07-12

### Context and Problem Statement

Users who want to run the tool must install Python 3.11+, create a venv,
install pip dependencies (including OpenCV which needs system libraries like
libgl1, libglib2.0), and ensure DejaVu fonts are available. This is a
significant barrier for non-developer family members or anyone on a system
where OpenCV's native deps are painful (ARM, minimal distros, Windows without
WSL).

The goal is **distribution simplification**: a single command to run the tool
on any machine that has Docker installed, with zero environment setup.

### Decision Drivers

- Users should not need Python or system libraries installed
- The tool must work identically on Linux, macOS, and Windows (via Docker Desktop)
- Output files must be accessible on the host filesystem
- OpenAI API key must be passable without baking it into the image
- Image size should be reasonable (< 500 MB)

### Considered Options

1. **PyInstaller / Nuitka binary** -- single executable, no Docker needed, but
   cross-compilation is fragile for OpenCV + NumPy; separate builds per OS/arch
2. **Docker image** -- universal runtime, multi-arch support, proven
   distribution model
3. **pipx** -- installs in isolated venv, but still requires Python + system
   deps for OpenCV
4. **Snap / Flatpak** -- Linux-only, complex packaging for Python apps

### Decision Outcome

**Chosen: Docker image** with multi-stage build, published to ghcr.io.

User experience:
```bash
# Free source (no API key needed):
docker run --rm -v ./output:/app/output ghcr.io/bhash/coloured-drawings \
    gerar "unicornio" --fonte web

# AI source:
docker run --rm -v ./output:/app/output -e OPENAI_API_KEY=sk-... \
    ghcr.io/bhash/coloured-drawings gerar "aladino"
```

- **Positive:** Works on any Docker-capable machine with zero setup; consistent
  environment (fonts, OpenCV, Python version); multi-arch builds possible via
  GitHub Actions; `docker compose` simplifies repeated use; image is ~200 MB
  (python:3.12-slim base + OpenCV deps).
- **Negative:** Requires Docker installed (common but not universal); slight
  startup overhead (~1s) vs native execution; image must be rebuilt on code
  changes. All acceptable for the distribution-simplification goal.

### Implementation

- Multi-stage Dockerfile: builder installs deps, runtime copies only what's needed
- `.dockerignore` excludes .git, tests, venv, output
- `docker-compose.yml` for convenience (mounts ./output, passes env vars)
- GitHub Actions builds + pushes to ghcr.io on tagged releases
- `ENTRYPOINT ["colorir"]` so the container behaves exactly like the CLI

---

## Decision Index

| ADR | Title                              | Status    |
|-----|------------------------------------|-----------|
| 001 | Python as implementation language   | Accepted  |
| 002 | Typer for CLI framework             | Accepted  |
| 003 | Three-stage pipeline architecture   | Accepted  |
| 004 | OpenCV-headless for line-art        | Accepted  |
| 005 | Pillow for PDF generation           | Accepted  |
| 006 | DuckDuckGo as free image source     | Accepted  |
| 007 | Heuristic watermark detection       | Accepted  |
| 008 | Hatchling as build backend          | Accepted  |
| 009 | Migrate to `uv`                     | Proposed  |
| 010 | Ruff as sole linter/formatter       | Proposed  |
| 011 | Structured logging with stdlib      | Proposed  |
| 012 | GitHub Actions for CI/CD            | Proposed  |
| 013 | Type checking with Pyright          | Proposed  |
| 014 | Pre-commit hooks                    | Proposed  |
| 015 | Web UI with FastAPI + HTMX          | Proposed  |
| 016 | Docker for CLI distribution         | Accepted  |
