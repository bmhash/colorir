"""Composição de página A4 pronta a imprimir (PDF a 300 DPI via Pillow)."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

DPI = 300
A4_PORTRAIT = (2480, 3508)  # A4 a 300 DPI, em pixels
MARGIN = 150
TITLE_SIZE = 90
TITLE_GAP = 60


def make_print_pdf(
    lineart: Image.Image,
    out_path: Path,
    landscape: bool = False,
    title: str | None = None,
) -> Path:
    """Centra o desenho numa página A4 com margens e título opcional; grava PDF."""
    page_size = (A4_PORTRAIT[1], A4_PORTRAIT[0]) if landscape else A4_PORTRAIT
    page = Image.new("RGB", page_size, "white")
    draw = ImageDraw.Draw(page)

    top = MARGIN
    if title:
        font = _load_font(TITLE_SIZE)
        bbox = draw.textbbox((0, 0), title, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        draw.text(((page_size[0] - text_w) // 2, top), title, fill="black", font=font)
        top += text_h + TITLE_GAP

    box_w = page_size[0] - 2 * MARGIN
    box_h = page_size[1] - top - MARGIN
    image = lineart.convert("RGB")
    scale = min(box_w / image.width, box_h / image.height)
    new_size = (max(1, int(image.width * scale)), max(1, int(image.height * scale)))
    image = image.resize(new_size, Image.LANCZOS)

    x = (page_size[0] - new_size[0]) // 2
    y = top + (box_h - new_size[1]) // 2
    page.paste(image, (x, y))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    page.save(out_path, "PDF", resolution=DPI)
    return out_path


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for name in ("DejaVuSans-Bold.ttf", "DejaVuSans.ttf", "Arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)
