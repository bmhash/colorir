# Roadmap

> Strategic development plan for **coloured-drawings**.
> Updated: 2025-07-12 | Current version: 0.1.0

---

## Vision

A delightful tool for parents and children to create printable colouring pages
from any idea -- typed as a prompt, snapped as a photo, or picked from a
gallery. CLI-first, with a simple web UI for non-technical family members.

---

## Versioning Strategy

| Version | Milestone                  | Target          |
|---------|----------------------------|-----------------|
| 0.1.0   | CLI MVP (current)          | Done            |
| 0.2.0   | Developer tooling + quality gates | Phase 1  |
| 0.3.0   | Enhanced pipeline + UX     | Phase 2         |
| 0.4.0   | Web UI (v2)                | Phase 3         |
| 1.0.0   | Production-ready release   | Phase 4         |

---

## Phase 1: Foundation & Developer Experience (v0.2.0)

**Goal:** Make the project maintainable, reproducible, and contribution-ready.

### 1.1 Dependency Management

- [ ] Migrate from bare `pip` to **uv** (ADR-009)
- [ ] Generate `uv.lock` for deterministic builds
- [ ] Add `uv run` scripts to replace manual venv activation
- [ ] Document migration in README

### 1.2 Code Quality Tooling

- [ ] Add **Ruff** configuration to `pyproject.toml` (ADR-010)
- [ ] Run `ruff check --fix` + `ruff format` on entire codebase
- [ ] Add **Pyright** configuration (ADR-013), fix any type errors
- [ ] Configure **pre-commit** hooks (ADR-014)

### 1.3 CI/CD Pipeline

- [ ] Create `.github/workflows/ci.yml` (ADR-012)
  - Lint (ruff) --> Type check (pyright) --> Test (pytest --cov)
  - Matrix: Python 3.11, 3.12
  - Cache: uv dependencies
- [ ] Add coverage reporting with `pytest-cov` (target: 80%)
- [ ] Add **Dependabot** for automated dependency updates
- [ ] Add CI status badge to README

### 1.4 Project Hygiene

- [ ] Add `LICENSE` (MIT)
- [ ] Add `CONTRIBUTING.md` with setup instructions
- [ ] Add `CHANGELOG.md` (Keep a Changelog format)
- [ ] Create `conftest.py` with shared fixtures
- [ ] Add `[tool.pytest.ini_options]` to `pyproject.toml`
- [ ] Add `.editorconfig` for consistent formatting

### 1.5 Logging

- [ ] Add stdlib `logging` to all modules (ADR-011)
- [ ] Add `--verbose` / `--debug` flags to CLI
- [ ] Log watermark detection decisions at DEBUG level
- [ ] Log HTTP requests/responses at DEBUG level

### 1.6 Docker Distribution (ADR-016)

- [x] Create multi-stage `Dockerfile` (python:3.12-slim + OpenCV deps + fonts)
- [x] Create `.dockerignore` (exclude .git, tests, venv, output)
- [x] Create `docker-compose.yml` for local convenience
- [ ] Add GitHub Actions workflow for image build + push to ghcr.io on tags
- [ ] Add multi-arch build (linux/amd64 + linux/arm64)
- [ ] Document Docker usage in README
- [ ] Add `colorir` shell alias helper for Docker users

**Definition of Done:** `uv sync && uv run pytest` works from a fresh clone;
CI passes on every push; Ruff + Pyright produce zero errors;
`docker build -t colorir . && docker run --rm colorir --help` works.

---

## Phase 2: Enhanced Pipeline & UX (v0.3.0)

**Goal:** Better image quality, more sources, improved user experience.

### 2.1 Image Quality Improvements

- [ ] Add configurable `line_thickness` to CLI (currently hardcoded at 2)
- [ ] Add `--estilo` option: `simples` (children) vs `detalhado` (adults)
- [ ] Investigate bilateral filter parameter auto-tuning based on image content
- [ ] Add optional upscaling for small web images (Real-ESRGAN or similar)
- [ ] Support transparent PNG output (in addition to RGB)

### 2.2 New Image Sources

- [ ] Add **Stability AI** source (SDXL for line-art generation)
- [ ] Add **Google Gemini** source (Imagen 3)
- [ ] Add **local file gallery** source (scan a directory of images)
- [ ] Add source fallback chain: try AI, fall back to web if API fails

### 2.3 CLI UX Enhancements

- [ ] Add `colorir batch` command for generating multiple pages at once
- [ ] Add `colorir favoritos` command to re-generate from a saved list
- [ ] Add progress bars for long operations (Rich progress)
- [ ] Add `--formato` option: A4, A5, Letter, custom dimensions
- [ ] Add `--abrir` flag to auto-open the PDF after generation
- [ ] Improve error messages with suggestions (typo correction for prompts)

### 2.4 PDF Enhancements

- [ ] Support multi-page PDF (batch of drawings in one file)
- [ ] Add page numbering for multi-page PDFs
- [ ] Add decorative border options (simple frame, dashed border, none)
- [ ] Support custom fonts via `--fonte-texto` option
- [ ] Add watermark with child's name as a subtle footer

### 2.5 Caching & Performance

- [ ] Add result caching (skip re-download for same prompt within 24h)
- [ ] Add async HTTP with `httpx` for parallel image downloads (web source)
- [ ] Cache OpenCV intermediate results for repeated conversions

### 2.6 Testing Improvements

- [ ] Add property-based tests with **Hypothesis** for image utils
- [ ] Add integration tests (full pipeline with mocked HTTP)
- [ ] Add snapshot/golden tests for lineart output consistency
- [ ] Reach 90% coverage target

**Definition of Done:** New sources work; batch generation produces a multi-page
PDF booklet; CLI has progress feedback; tests cover all new features.

---

## Phase 3: Web UI (v0.4.0)

**Goal:** Non-technical family members can generate colouring pages from a
browser without touching the terminal. (ADR-015)

### 3.1 Backend (FastAPI)

- [ ] Create `coloured_drawings/web/` module
- [ ] `/api/generate` endpoint wrapping `pipeline.generate()`
- [ ] `/api/convert` endpoint wrapping `pipeline.convert_file()`
- [ ] `/api/gallery` endpoint listing `output/` contents
- [ ] Background task queue for long-running generation (FastAPI BackgroundTasks)
- [ ] Server-sent events (SSE) for generation progress
- [ ] Serve static files and PDF downloads

### 3.2 Frontend (HTMX + Jinja2)

- [ ] Landing page: prompt input + source selector + generate button
- [ ] Gallery page: grid of previously generated drawings with thumbnails
- [ ] Detail page: original / lineart / PDF side-by-side with download links
- [ ] Real-time progress indicator during generation (SSE + HTMX swap)
- [ ] Mobile-responsive layout (CSS Grid/Flexbox, no JS framework)
- [ ] Print button that opens PDF in browser print dialog

### 3.3 Deployment

- [ ] Create `Dockerfile` (Python 3.12-slim + system deps for OpenCV)
- [ ] Create `docker-compose.yml` for local development
- [ ] Add health check endpoint (`/health`)
- [ ] Document deployment options (Docker, Railway, Fly.io)
- [ ] Add environment variable documentation for production

### 3.4 Security (Web)

- [ ] Rate limiting on generation endpoints
- [ ] Input sanitisation for prompts (max length, no injection)
- [ ] CORS configuration
- [ ] File upload size limits for `/api/convert`
- [ ] Optional basic auth for family-only access

**Definition of Done:** Family members can open a URL, type "unicornio", and
download a ready-to-print PDF. Docker deployment works with a single command.

---

## Phase 4: Production Polish (v1.0.0)

**Goal:** Stability, observability, and release automation for a v1.0.

### 4.1 Stability

- [ ] Error recovery: retry failed downloads with exponential backoff
- [ ] Graceful degradation: if AI source fails, suggest web source
- [ ] Input validation hardening (path traversal prevention, file type checks)
- [ ] Memory profiling for large image processing
- [ ] Add timeouts to all external API calls

### 4.2 Observability

- [ ] Structured JSON logging for web server mode
- [ ] Request tracing with correlation IDs
- [ ] Metrics: generation count, source success/failure rates, latency
- [ ] Optional Sentry integration for error tracking

### 4.3 Release Automation

- [ ] Semantic versioning with **python-semantic-release**
- [ ] Auto-generate CHANGELOG from conventional commits
- [ ] Publish to PyPI on tagged releases
- [ ] GitHub Releases with changelog body
- [ ] Docker image published to GitHub Container Registry

### 4.4 Documentation

- [ ] API documentation with OpenAPI (auto-generated by FastAPI)
- [ ] Architecture diagrams (Mermaid in docs/)
- [ ] User guide for the web UI (with screenshots)
- [ ] Developer guide: how to add a new image source

### 4.5 Internationalisation

- [ ] Extract UI strings to resource files
- [ ] Support Portuguese (current) + English
- [ ] CLI `--lingua` / web language switcher
- [ ] Locale-aware page sizes (A4 for EU, Letter for US)

**Definition of Done:** Published on PyPI; Docker image available; CI/CD
fully automated; documentation comprehensive; version 1.0.0 tag created.

---

## Backlog (Future Consideration)

These are ideas that may become phases beyond 1.0:

- **Mobile app** (React Native / Flutter) wrapping the web API
- **Collaborative colouring** -- share pages with other families
- **AI style transfer** -- "draw like Van Gogh" line-art styles
- **Augmented reality** -- colour detection via phone camera
- **Marketplace** -- community-shared prompt libraries
- **Print service integration** -- order physical colouring books
- **Accessibility** -- high-contrast line art for visually impaired children
- **Offline mode** -- bundled models for generation without internet
- **Template system** -- reusable page layouts (borders, headers, activity pages)

---

## Progress Tracking

This roadmap is the source of truth for what we're building and why.
Each phase corresponds to a minor version bump. Items are checked off as
they're completed and committed. See `docs/decisions.md` for the "why"
behind major choices.

```
Current focus: Phase 1 (Foundation & Developer Experience)
```
