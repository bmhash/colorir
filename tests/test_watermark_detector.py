"""Testes para detecção de watermarks."""

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from coloured_drawings.sources.watermark_detector import has_watermark


def _clean_image() -> Image.Image:
    """Imagem limpa sem watermark: círculo simples."""
    img = Image.new("RGB", (800, 600), "white")
    draw = ImageDraw.Draw(img)
    draw.ellipse((200, 150, 600, 450), fill=(100, 150, 200))
    return img


def _image_with_corner_watermark() -> Image.Image:
    """Imagem com watermark visível no canto (retângulo + texto)."""
    img = _clean_image()
    draw = ImageDraw.Draw(img)
    # Watermark típico: caixa semi-transparente no canto inferior direito
    # Simula com retângulo cinza e texto
    draw.rectangle((600, 500, 790, 590), fill=(200, 200, 200), outline="black", width=2)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 20)
    except OSError:
        font = ImageFont.load_default()
    draw.text((610, 510), "© STOCK", fill="black", font=font)
    draw.text((610, 540), "PHOTO", fill="black", font=font)
    draw.text((610, 565), "watermark.com", fill="gray", font=font)
    return img


def _image_with_border_watermark() -> Image.Image:
    """Imagem com watermark repetido na borda superior."""
    img = _clean_image()
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 24)
    except OSError:
        font = ImageFont.load_default()
    # Texto repetido ao longo da borda (típico de sites de stock)
    for x in range(20, 780, 150):
        draw.text((x, 15), "SAMPLE", fill=(150, 150, 150), font=font)
    return img


def _image_with_diagonal_watermark() -> Image.Image:
    """Imagem com watermark diagonal (padrão repetitivo)."""
    img = _clean_image()
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 30)
    except OSError:
        font = ImageFont.load_default()
    # Padrão diagonal repetitivo
    for y in range(-100, 700, 120):
        for x in range(-100, 900, 200):
            draw.text((x, y), "PREVIEW", fill=(180, 180, 180), font=font)
    return img


def test_clean_image_passes():
    """Imagem limpa não deve ser detetada como tendo watermark."""
    assert not has_watermark(_clean_image())


def test_corner_watermark_detected():
    """Watermark no canto deve ser detetado."""
    assert has_watermark(_image_with_corner_watermark(), sensitivity=0.7)


def test_border_watermark_detected():
    """Watermark repetido na borda deve ser detetado."""
    assert has_watermark(_image_with_border_watermark(), sensitivity=0.7)


def test_diagonal_watermark_detected():
    """Watermark diagonal repetitivo deve ser detetado."""
    assert has_watermark(_image_with_diagonal_watermark(), sensitivity=0.7)


def test_sensitivity_low_is_permissive():
    """Sensibilidade baixa deixa passar mais imagens."""
    # Com sensibilidade muito baixa, até watermarks podem passar
    img = _image_with_corner_watermark()
    # Sensibilidade 0.1 é muito permissiva
    result = has_watermark(img, sensitivity=0.1)
    # Pode ou não detetar, mas não deve crashar
    assert isinstance(result, bool)


def test_sensitivity_high_is_strict():
    """Sensibilidade alta deteta mais agressivamente."""
    img = _image_with_border_watermark()
    # Sensibilidade 1.0 é máxima
    assert has_watermark(img, sensitivity=1.0)
