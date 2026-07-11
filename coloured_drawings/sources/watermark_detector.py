"""Detecção de watermarks em imagens usando heurísticas OpenCV."""

import cv2
import numpy as np
from PIL import Image


def has_watermark(image: Image.Image, sensitivity: float = 0.7) -> bool:
    """Deteta se uma imagem tem watermark visível.
    
    sensitivity: 0.0 (permissivo) a 1.0 (rigoroso). Default 0.7 é equilibrado.
    
    Heurísticas:
    - Contornos de texto concentrados nos cantos/bordas
    - Densidade de contornos anormalmente alta
    - Padrões repetitivos (watermarks diagonais)
    """
    rgb = np.array(image.convert("RGB"))
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    h, w = gray.shape
    
    # Deteta contornos (mais robusto que threshold simples)
    edges = cv2.Canny(gray, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Cria máscara de contornos
    contour_mask = np.zeros_like(gray)
    cv2.drawContours(contour_mask, contours, -1, 255, 1)
    
    # 1. Analisa cantos (15% de cada lado)
    margin = 0.15
    corners = [
        contour_mask[: int(h * margin), : int(w * margin)],
        contour_mask[: int(h * margin), int(w * (1 - margin)) :],
        contour_mask[int(h * (1 - margin)) :, : int(w * margin)],
        contour_mask[int(h * (1 - margin)) :, int(w * (1 - margin)) :],
    ]
    
    corner_densities = [np.mean(c > 0) for c in corners]
    max_corner = max(corner_densities)
    
    # Threshold calibrado: watermarks típicos têm ~1-2% de densidade no canto
    # Sensibilidade ajusta de 0.5% (permissivo) a 2.0% (rigoroso)
    corner_threshold = 0.005 + 0.015 * sensitivity
    if max_corner > corner_threshold:
        return True
    
    # 2. Analisa bordas (8% de cada lado)
    border_margin = 0.08
    borders = [
        contour_mask[: int(h * border_margin), :],
        contour_mask[int(h * (1 - border_margin)) :, :],
        contour_mask[:, : int(w * border_margin)],
        contour_mask[:, int(w * (1 - border_margin)) :],
    ]
    
    border_densities = [np.mean(b > 0) for b in borders]
    max_border = max(border_densities)
    
    # Watermarks em bordas têm ~3-6% de densidade
    border_threshold = 0.02 + 0.05 * sensitivity
    if max_border > border_threshold:
        return True
    
    # 3. Densidade global (watermarks diagonais cobrindo a imagem)
    global_density = np.mean(contour_mask > 0)
    # Imagens limpas têm ~0.2%, watermarks diagonais ~0.5-1%
    global_threshold = 0.003 + 0.007 * sensitivity
    if global_density > global_threshold:
        return True
    
    # 4. Deteta padrões repetitivos em grid 4×4
    grid_size = 4
    cell_h, cell_w = h // grid_size, w // grid_size
    cells = []
    for i in range(grid_size):
        for j in range(grid_size):
            cell = contour_mask[i * cell_h : (i + 1) * cell_h, j * cell_w : (j + 1) * cell_w]
            cells.append(np.mean(cell > 0))
    
    # Padrão repetitivo: baixa variância + densidade não-trivial
    if len(cells) > 0:
        std = np.std(cells)
        mean = np.mean(cells)
        # Variância muito baixa com densidade moderada = padrão repetitivo
        if std < 0.015 and 0.03 < mean < 0.20:
            return True
    
    return False
