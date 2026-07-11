"""Common interface for all image sources."""

from abc import ABC, abstractmethod

from PIL import Image


class SourceError(Exception):
    """User-friendly error from an image source (displayed without traceback)."""


class ImageSource(ABC):
    """Base image source. New sources (Stability, Gemini, ...) implement this."""

    name: str = "base"
    #: True if the source already returns print-ready line-art (skips OpenCV conversion)
    produces_lineart: bool = False

    @abstractmethod
    def fetch(self, prompt: str) -> Image.Image:
        """Fetch an RGB image from the prompt. Raises SourceError on failure."""
