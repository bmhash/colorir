"""Fonte de imagem por pesquisa web (DuckDuckGo) — gratuita, qualidade variável."""

import io

import requests
from PIL import Image

from coloured_drawings.sources.base import ImageSource, SourceError

MIN_SIDE = 800  # resolução mínima para impressão decente (A4 @ 300 DPI = 2480×3508)
MAX_RESULTS = 20
TIMEOUT = 15


class WebSearchSource(ImageSource):
    name = "web"
    produces_lineart = False

    def fetch(self, prompt: str) -> Image.Image:
        try:
            from ddgs import DDGS
        except ImportError as exc:
            raise SourceError("Pacote 'ddgs' não instalado. Corre: pip install ddgs") from exc

        query = f"{prompt} desenho para colorir coloring page"
        try:
            with DDGS() as ddgs:
                results = list(
                    ddgs.images(query, safesearch="on", max_results=MAX_RESULTS, size="Large")
                )
        except Exception as exc:  # noqa: BLE001
            raise SourceError(f"Falha na pesquisa web: {exc}") from exc

        if not results:
            raise SourceError(f"Nenhuma imagem encontrada para '{prompt}'. Tenta outras palavras.")

        # Ordena por tamanho reportado (maiores primeiro) para tentar alta resolução
        results.sort(key=lambda r: (r.get("width", 0) or 0) * (r.get("height", 0) or 0), reverse=True)

        for result in results:
            image = self._try_download(result.get("image", ""))
            if image is not None:
                return image

        raise SourceError(
            "Não consegui descarregar nenhuma imagem utilizável. Tenta outras palavras."
        )

    @staticmethod
    def _try_download(url: str) -> Image.Image | None:
        if not url:
            return None
        try:
            resp = requests.get(
                url,
                timeout=TIMEOUT,
                headers={"User-Agent": "Mozilla/5.0 (coloured-drawings)"},
            )
            resp.raise_for_status()
            image = Image.open(io.BytesIO(resp.content))
            image.load()
        except Exception:  # noqa: BLE001 — tenta o próximo resultado
            return None
        if min(image.size) < MIN_SIDE:
            return None
        return image.convert("RGB")
