"""Conversão de imagens para line-art estilo livro de colorir (OpenCV)."""

import cv2
import numpy as np
from PIL import Image


def to_lineart(image: Image.Image, detail: int = 5, line_thickness: int = 2) -> Image.Image:
    """Converte uma imagem RGB em contornos pretos sobre fundo branco.

    detail: 1 (poucos detalhes, linhas grossas) a 9 (muitos detalhes).
    line_thickness: engrossamento das linhas em pixels (bom para crianças pequenas).
    """
    detail = max(1, min(9, detail))
    rgb = np.array(image.convert("RGB"))
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

    # Suaviza texturas mantendo os contornos
    gray = cv2.bilateralFilter(gray, d=9, sigmaColor=75, sigmaSpace=75)

    # blockSize maior => menos detalhe; mapeia detail 1-9 para blocos 31..15
    block_size = 33 - 2 * detail
    edges = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY,
        blockSize=block_size,
        C=8,
    )

    # Remove ruído pequeno (specks pretos): abre a máscara invertida
    inverted = cv2.bitwise_not(edges)
    kernel = np.ones((3, 3), np.uint8)
    inverted = cv2.morphologyEx(inverted, cv2.MORPH_OPEN, kernel)

    # Engrossa as linhas
    if line_thickness > 1:
        thick_kernel = np.ones((line_thickness, line_thickness), np.uint8)
        inverted = cv2.dilate(inverted, thick_kernel, iterations=1)

    result = cv2.bitwise_not(inverted)
    return Image.fromarray(result).convert("RGB")
