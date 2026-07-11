"""Image processing utilities."""

from PIL import Image

# A4 resolution at 300 DPI (ideal for printing)
A4_PORTRAIT_300DPI = (2480, 3508)
A4_LANDSCAPE_300DPI = (3508, 2480)


def resize_for_a4(image: Image.Image, landscape: bool = False) -> Image.Image:
    """Resize image to optimal A4 resolution at 300 DPI.

    - If the image is larger than A4, scale down preserving aspect ratio
    - If smaller, keep original size (upscaling degrades quality)
    - Always returns RGB
    """
    target = A4_LANDSCAPE_300DPI if landscape else A4_PORTRAIT_300DPI
    img = image.convert("RGB")

    # Only downscale if larger than A4
    scale = min(target[0] / img.width, target[1] / img.height)

    if scale >= 1.0:
        return img

    # Resize preserving aspect ratio
    new_size = (int(img.width * scale), int(img.height * scale))
    return img.resize(new_size, Image.LANCZOS)
