"""Watermark detection in images using OpenCV heuristics."""

import cv2
import numpy as np
from PIL import Image


def has_watermark(image: Image.Image, sensitivity: float = 0.7) -> bool:
    """Detect if an image has a visible watermark.

    sensitivity: 0.0 (permissive) to 1.0 (strict). Default 0.7 is balanced.

    Heuristics:
    - Text contours concentrated in corners/edges
    - Abnormally high contour density
    - Repetitive patterns (diagonal watermarks)
    """
    rgb = np.array(image.convert("RGB"))
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    h, w = gray.shape

    # Detect edges (more robust than simple threshold)
    edges = cv2.Canny(gray, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Create contour mask
    contour_mask = np.zeros_like(gray)
    cv2.drawContours(contour_mask, contours, -1, 255, 1)

    # 1. Analyze corners (15% of each side)
    margin = 0.15
    corners = [
        contour_mask[: int(h * margin), : int(w * margin)],
        contour_mask[: int(h * margin), int(w * (1 - margin)) :],
        contour_mask[int(h * (1 - margin)) :, : int(w * margin)],
        contour_mask[int(h * (1 - margin)) :, int(w * (1 - margin)) :],
    ]

    corner_densities = [np.mean(c > 0) for c in corners]
    max_corner = max(corner_densities)

    # Calibrated threshold: typical watermarks have ~1-2% corner density
    # Sensitivity adjusts from 0.5% (permissive) to 2.0% (strict)
    corner_threshold = 0.005 + 0.015 * sensitivity
    if max_corner > corner_threshold:
        return True

    # 2. Analyze borders (8% of each side)
    border_margin = 0.08
    borders = [
        contour_mask[: int(h * border_margin), :],
        contour_mask[int(h * (1 - border_margin)) :, :],
        contour_mask[:, : int(w * border_margin)],
        contour_mask[:, int(w * (1 - border_margin)) :],
    ]

    border_densities = [np.mean(b > 0) for b in borders]
    max_border = max(border_densities)

    # Border watermarks have ~3-6% density
    border_threshold = 0.02 + 0.05 * sensitivity
    if max_border > border_threshold:
        return True

    # 3. Global density (diagonal watermarks covering the image)
    global_density = np.mean(contour_mask > 0)
    # Clean images have ~0.2%, diagonal watermarks ~0.5-1%
    global_threshold = 0.003 + 0.007 * sensitivity
    if global_density > global_threshold:
        return True

    # 4. Detect repetitive patterns in 4×4 grid
    grid_size = 4
    cell_h, cell_w = h // grid_size, w // grid_size
    cells = []
    for i in range(grid_size):
        for j in range(grid_size):
            cell = contour_mask[i * cell_h : (i + 1) * cell_h, j * cell_w : (j + 1) * cell_w]
            cells.append(np.mean(cell > 0))

    # Repetitive pattern: low variance + non-trivial density
    if len(cells) > 0:
        std = np.std(cells)
        mean = np.mean(cells)
        # Very low variance with moderate density = repetitive pattern
        if std < 0.015 and 0.03 < mean < 0.20:
            return True

    return False
