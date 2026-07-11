# colorir 🎨

Turn any idea into a printable coloring page — just type what you want to draw.

Type a prompt (e.g. `"aladino da Disney"`), and the tool fetches or generates
a coloring-book-style image and produces a print-ready A4 PDF.

> [Leia em Portugues](README.pt.md)

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

To use the AI source (better quality), copy `.env.example` to `.env` and fill in
your `OPENAI_API_KEY`. The `web` source is free and requires no API key.

### Docker (recommended)

```bash
docker build -t colorir .
docker run --rm -v ./output:/app/output colorir gerar "unicornio" --fonte web
```

## Usage

```bash
# Full pipeline with AI (requires OPENAI_API_KEY)
colorir gerar "aladino da Disney"

# Free source: web search + line-art conversion
colorir gerar "sereia" --fonte web

# Generate and auto-open the PDF (WSL2, Linux, macOS, Windows)
colorir gerar "gato" --fonte web --abrir

# Options
colorir gerar "castelo" --paisagem --sem-titulo
colorir gerar "gato" --fonte web --detalhe 3      # 1=simple, 9=detailed
colorir gerar "cão" --titulo "My dog"

# Convert a local photo/image to coloring page
colorir converter photo.jpg --abrir

# List previously generated drawings
colorir listar
```

Each drawing is saved to `output/<slug>-<timestamp>/` containing:

- **`original.png`** — fetched/generated image
- **`lineart.png`** — line-art version (contours only)
- **`print.pdf`** — A4 page at 300 DPI, ready to print

## Architecture

3-stage decoupled pipeline (`coloured_drawings/`):

- **`sources/`** — image sources with a common `ImageSource` interface (`ai` = OpenAI gpt-image-1, `web` = DuckDuckGo search). New sources plug in here.
- **`lineart/`** — line-art conversion (OpenCV): bilateral filter → adaptive threshold → cleanup → line thickening.
- **`printing/`** — A4 page composition and PDF export (Pillow).

The CLI (`cli.py`, typer) is a thin layer over `pipeline.py` — a future web UI can
reuse the pipeline without changes.

## Tests

```bash
pytest
```

## Security

See [docs/security-audit.md](docs/security-audit.md) for the full security review.

Key protections:
- SSRF guard blocks private/loopback IPs on image downloads
- Docker runs as non-root with `cap_drop: ALL` and read-only filesystem
- Dependency lock file (`uv.lock`) with hash-pinned versions
- Symlink-safe file writes
- Image dimension and download size limits
