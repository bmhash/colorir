import numpy as np
from PIL import Image, ImageDraw

from coloured_drawings.lineart import to_lineart


def _sample_image() -> Image.Image:
    """Imagem sintética: círculo colorido sobre fundo claro."""
    img = Image.new("RGB", (400, 400), (240, 240, 240))
    draw = ImageDraw.Draw(img)
    draw.ellipse((80, 80, 320, 320), fill=(200, 60, 60), outline=(0, 0, 0), width=6)
    return img


def test_output_is_black_and_white():
    result = to_lineart(_sample_image())
    arr = np.array(result.convert("L"))
    unique = set(np.unique(arr))
    assert unique <= {0, 255}


def test_output_has_lines_and_white_space():
    arr = np.array(to_lineart(_sample_image()).convert("L"))
    black_ratio = (arr == 0).mean()
    assert 0.0 < black_ratio < 0.5  # tem linhas mas maioritariamente branco


def test_detail_is_clamped():
    result = to_lineart(_sample_image(), detail=99)
    assert result.size == (400, 400)
