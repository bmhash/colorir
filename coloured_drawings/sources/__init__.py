"""Fontes de imagem: cada fonte implementa a interface ImageSource."""

from coloured_drawings.sources.base import ImageSource, SourceError


def get_source(name: str) -> ImageSource:
    """Devolve a fonte de imagem pelo nome ('ai' ou 'web')."""
    if name == "ai":
        from coloured_drawings.sources.ai_generator import AIGeneratorSource

        return AIGeneratorSource()
    if name == "web":
        from coloured_drawings.sources.web_search import WebSearchSource

        return WebSearchSource()
    raise SourceError(f"Fonte desconhecida: '{name}'. Usa 'ai' ou 'web'.")
