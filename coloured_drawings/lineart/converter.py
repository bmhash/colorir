"""Image to coloring-book line-art conversion (OpenCV)."""

import cv2
import numpy as np
from PIL import Image


def to_lineart(image: Image.Image, detail: int = 5, line_thickness: int = 2) -> Image.Image:
    """Convert an RGB image to black contours on white background.

    detail: 1 (few details, thick lines) to 9 (many details).
    line_thickness: line thickening in pixels (good for small children).
    """
    detail = max(1, min(9, detail))
    rgb = np.array(image.convert("RGB"))
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

    # Smooth textures while preserving edges
    gray = cv2.bilateralFilter(gray, d=9, sigmaColor=75, sigmaSpace=75)

    # Larger blockSize => less detail; maps detail 1-9 to blocks 31..15
    block_size = 33 - 2 * detail
    edges = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY,
        blockSize=block_size,
        C=8,
    )

    # Remove small noise (black specks): open the inverted mask
    inverted = cv2.bitwise_not(edges)
    kernel = np.ones((3, 3), np.uint8)
    inverted = cv2.morphologyEx(inverted, cv2.MORPH_OPEN, kernel)

    # Thicken lines
    if line_thickness > 1:
        thick_kernel = np.ones((line_thickness, line_thickness), np.uint8)
        inverted = cv2.dilate(inverted, thick_kernel, iterations=1)

    result = cv2.bitwise_not(inverted)
    return Image.fromarray(result).convert("RGB")
