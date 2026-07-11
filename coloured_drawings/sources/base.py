"""Interface comum a todas as fontes de imagem."""

from abc import ABC, abstractmethod

from PIL import Image


class SourceError(Exception):
    """Erro amigável de uma fonte de imagem (mostrado ao utilizador sem traceback)."""


class ImageSource(ABC):
    """Fonte de imagem base. Novas fontes (Stability, Gemini, ...) implementam isto."""

    name: str = "base"
    #: True se a fonte já devolve line-art pronta a colorir (salta a conversão OpenCV)
    produces_lineart: bool = False

    @abstractmethod
    def fetch(self, prompt: str) -> Image.Image:
        """Obtém uma imagem RGB a partir do prompt. Lança SourceError em caso de falha."""
