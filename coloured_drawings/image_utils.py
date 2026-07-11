"""Utilitários de processamento de imagem."""

from PIL import Image

# Resolução A4 a 300 DPI (ideal para impressão)
A4_PORTRAIT_300DPI = (2480, 3508)
A4_LANDSCAPE_300DPI = (3508, 2480)


def resize_for_a4(image: Image.Image, landscape: bool = False) -> Image.Image:
    """Redimensiona imagem para resolução ideal A4 a 300 DPI.
    
    - Se a imagem for maior que A4, reduz mantendo aspect ratio
    - Se for menor, mantém o tamanho original (upscaling degrada qualidade)
    - Retorna sempre RGB
    """
    target = A4_LANDSCAPE_300DPI if landscape else A4_PORTRAIT_300DPI
    img = image.convert("RGB")
    
    # Calcula se precisa redimensionar (só se for maior que A4)
    scale = min(target[0] / img.width, target[1] / img.height)
    
    if scale >= 1.0:
        # Imagem já é menor ou igual a A4 — mantém original
        return img
    
    # Redimensiona mantendo aspect ratio
    new_size = (int(img.width * scale), int(img.height * scale))
    return img.resize(new_size, Image.LANCZOS)
