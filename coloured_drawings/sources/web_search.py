"""Fonte de imagem por pesquisa web (DuckDuckGo) — gratuita, qualidade variável."""

import io

import requests
from PIL import Image

from coloured_drawings.sources.base import ImageSource, SourceError
from coloured_drawings.sources.watermark_detector import has_watermark

MIN_SIDE = 600  # resolução mínima (691×960 já é suficiente para A4 com resize)
MAX_RESULTS = 20
TIMEOUT = 15
WATERMARK_SENSITIVITY = 0.5  # 0.5 = equilibrado (0.7 era demasiado restritivo)


class WebSearchSource(ImageSource):
    name = "web"
    produces_lineart = False

    def __init__(self, skip_watermark_check: bool = False):
        self.skip_watermark_check = skip_watermark_check

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
        def _size(r):
            try:
                w = int(r.get("width", 0) or 0)
                h = int(r.get("height", 0) or 0)
                return w * h
            except (ValueError, TypeError):
                return 0
        results.sort(key=_size, reverse=True)

        for result in results:
            image = self._try_download(result.get("image", ""), self.skip_watermark_check)
            if image is not None:
                return image

        raise SourceError(
            f"Não consegui encontrar imagens sem watermark para '{prompt}'. "
            "Tenta: (1) outras palavras, (2) --fonte ai (melhor qualidade), "
            "ou (3) --sem-filtro-watermark (aceita watermarks)."
        )

    @staticmethod
    def _try_download(url: str, skip_watermark_check: bool = False) -> Image.Image | None:
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
        # Rejeita imagens com watermark visível (a menos que skip_watermark_check=True)
        if not skip_watermark_check and has_watermark(image, sensitivity=WATERMARK_SENSITIVITY):
            return None
        return image.convert("RGB")
