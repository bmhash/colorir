# Project: coloured-drawings

## Quick Reference

- **Language:** Python 3.11+ (currently running 3.12.3)
- **Build backend:** hatchling
- **CLI entry point:** `colorir` (via `coloured_drawings.cli:app`)
- **Package manager:** pip (migrating to uv -- see docs/roadmap.md Phase 1)

## Verification Commands

```bash
# Run tests
.venv/bin/python -m pytest --tb=short -q

# Run a single test file
.venv/bin/python -m pytest tests/test_lineart.py -v

# Run the CLI
.venv/bin/python -m coloured_drawings.cli --help
```

## Project Structure

```
coloured_drawings/       # Main package
├── cli.py               # Typer CLI commands (gerar, converter, listar)
├── config.py            # Settings from environment variables
├── pipeline.py          # Pipeline orchestrator
├── image_utils.py       # A4 resize logic
├── utils.py             # slugify, output dir helpers
├── lineart/             # OpenCV line-art conversion
├── printing/            # A4 PDF composition (Pillow)
└── sources/             # Image sources (AI, web) with ImageSource ABC
tests/                   # pytest tests (19 tests)
docs/                    # decisions.md, roadmap.md, implementation.md
output/                  # Generated drawings (gitignored)
```

## Key Patterns

- **Pipeline:** `sources/ -> lineart/ -> printing/` (orchestrated by pipeline.py)
- **Plugin interface:** `ImageSource` ABC in `sources/base.py`
- **Error handling:** `SourceError` exception for user-friendly CLI errors
- **Config:** Frozen dataclass loaded from env vars via python-dotenv

## Documentation

- `docs/decisions.md` -- Architecture Decision Records (MADR 4.0)
- `docs/roadmap.md` -- Strategic roadmap with phases
- `docs/implementation.md` -- Technical implementation guide
