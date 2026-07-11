"""Fonte de imagem por pesquisa web (DuckDuckGo) — gratuita, qualidade variável."""

import io
import ipaddress
import socket
from urllib.parse import urlparse

import requests
from PIL import Image

from coloured_drawings.sources.base import ImageSource, SourceError
from coloured_drawings.sources.watermark_detector import has_watermark

MIN_SIDE = 600  # resolução mínima (691×960 já é suficiente para A4 com resize)
MAX_SIDE = 8000  # máximo seguro (evita decompression bombs)
MAX_RESPONSE_BYTES = 50_000_000  # 50 MB max download
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
        if not _is_safe_url(url):
            return None
        try:
            resp = requests.get(
                url,
                timeout=TIMEOUT,
                headers={"User-Agent": "Mozilla/5.0 (coloured-drawings)"},
                stream=True,
            )
            resp.raise_for_status()
            # Enforce response size limit before reading body
            content_length = int(resp.headers.get("content-length", 0) or 0)
            if content_length > MAX_RESPONSE_BYTES:
                return None
            # Read with size cap (content-length can be spoofed)
            chunks = []
            total = 0
            for chunk in resp.iter_content(chunk_size=65536):
                total += len(chunk)
                if total > MAX_RESPONSE_BYTES:
                    return None
                chunks.append(chunk)
            data = b"".join(chunks)
            image = Image.open(io.BytesIO(data))
            image.load()
        except Exception:  # noqa: BLE001 — tenta o próximo resultado
            return None
        # Dimension safety check (avoid decompression bombs)
        if max(image.size) > MAX_SIDE:
            return None
        if min(image.size) < MIN_SIDE:
            return None
        # Rejeita imagens com watermark visível (a menos que skip_watermark_check=True)
        if not skip_watermark_check and has_watermark(image, sensitivity=WATERMARK_SENSITIVITY):
            return None
        return image.convert("RGB")


def _is_safe_url(url: str) -> bool:
    """Block requests to private/internal networks (SSRF protection)."""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        hostname = parsed.hostname
        if not hostname:
            return False
        # Block known cloud metadata endpoints
        if hostname in (
            "169.254.169.254",
            "metadata.google.internal",
            "metadata.ec2.internal",
        ):
            return False
        # Resolve and check all IPs
        for info in socket.getaddrinfo(hostname, parsed.port or 443):
            ip = ipaddress.ip_address(info[4][0])
            if ip.is_private or ip.is_loopback or ip.is_link_local:
                return False
        return True
    except Exception:  # noqa: BLE001
        return False
