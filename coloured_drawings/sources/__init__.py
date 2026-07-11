"""Image sources: each source implements the ImageSource interface."""

from coloured_drawings.sources.base import ImageSource, SourceError


def get_source(name: str, **kwargs) -> ImageSource:
    """Return an image source by name ('ai' or 'web')."""
    if name == "ai":
        from coloured_drawings.sources.ai_generator import AIGeneratorSource

        return AIGeneratorSource()
    if name == "web":
        from coloured_drawings.sources.web_search import WebSearchSource

        return WebSearchSource(**kwargs)
    raise SourceError(f"Fonte desconhecida: '{name}'. Usa 'ai' ou 'web'.")
