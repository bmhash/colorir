from pathlib import Path

from PIL import Image

from coloured_drawings.printing import make_print_pdf


def _lineart() -> Image.Image:
    return Image.new("RGB", (800, 1200), "white")


def test_creates_pdf(tmp_path: Path):
    out = make_print_pdf(_lineart(), tmp_path / "print.pdf")
    assert out.exists()
    assert out.stat().st_size > 0
    assert out.read_bytes()[:5] == b"%PDF-"


def test_creates_pdf_landscape_with_title(tmp_path: Path):
    out = make_print_pdf(_lineart(), tmp_path / "p.pdf", landscape=True, title="Aladino")
    assert out.exists()
    assert out.read_bytes()[:5] == b"%PDF-"
