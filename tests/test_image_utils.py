"""Testes para utilitários de processamento de imagem."""

from PIL import Image

from coloured_drawings.image_utils import A4_PORTRAIT_300DPI, resize_for_a4


def test_resize_large_image_to_a4():
    """Imagem maior que A4 deve ser reduzida."""
    # Imagem muito grande (4K)
    large = Image.new("RGB", (3840, 2160), "white")
    result = resize_for_a4(large, landscape=False)
    
    # Deve caber em A4 portrait
    assert result.width <= A4_PORTRAIT_300DPI[0]
    assert result.height <= A4_PORTRAIT_300DPI[1]
    # Aspect ratio mantido
    original_ratio = large.width / large.height
    result_ratio = result.width / result.height
    assert abs(original_ratio - result_ratio) < 0.01


def test_resize_keeps_small_image():
    """Imagem menor que A4 não deve ser aumentada."""
    small = Image.new("RGB", (800, 600), "white")
    result = resize_for_a4(small, landscape=False)
    
    # Deve manter tamanho original (não faz upscale)
    assert result.size == (800, 600)


def test_resize_landscape_mode():
    """Modo paisagem usa dimensões A4 landscape."""
    large = Image.new("RGB", (4000, 3000), "white")
    result = resize_for_a4(large, landscape=True)
    
    # Deve caber em A4 landscape (3508×2480)
    assert result.width <= 3508
    assert result.height <= 2480


def test_resize_converts_to_rgb():
    """Sempre retorna RGB."""
    grayscale = Image.new("L", (1000, 1000), 128)
    result = resize_for_a4(grayscale)
    assert result.mode == "RGB"


def test_resize_exact_a4_size():
    """Imagem exatamente A4 não deve ser alterada."""
    exact = Image.new("RGB", A4_PORTRAIT_300DPI, "white")
    result = resize_for_a4(exact, landscape=False)
    assert result.size == A4_PORTRAIT_300DPI
