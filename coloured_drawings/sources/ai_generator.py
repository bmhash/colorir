"""Fonte de imagem por IA (OpenAI gpt-image-1) — gera diretamente line-art para colorir."""

import base64
import io

from PIL import Image

from coloured_drawings.config import get_settings
from coloured_drawings.sources.base import ImageSource, SourceError

PROMPT_TEMPLATE = (
    "A children's coloring book page of {subject}. "
    "Black and white line art only, thick clean bold outlines, no shading, "
    "no gray tones, no color, pure white background, large simple shapes "
    "with plenty of open space, suitable for a young child to color with crayons."
)


class AIGeneratorSource(ImageSource):
    name = "ai"
    produces_lineart = True

    def fetch(self, prompt: str) -> Image.Image:
        settings = get_settings()
        if not settings.openai_api_key:
            raise SourceError(
                "Falta a OPENAI_API_KEY. Copia .env.example para .env e preenche a chave, "
                "ou usa a fonte gratuita: --fonte web"
            )
        try:
            from openai import OpenAI

            client = OpenAI(api_key=settings.openai_api_key)
            response = client.images.generate(
                model=settings.ai_model,
                prompt=PROMPT_TEMPLATE.format(subject=prompt),
                size="1024x1536",
                quality="medium",
                n=1,
            )
        except Exception as exc:  # noqa: BLE001 — erro amigável para o CLI
            raise SourceError(f"Falha na geração por IA: {exc}") from exc

        b64 = response.data[0].b64_json
        if not b64:
            raise SourceError("A API não devolveu imagem. Tenta novamente.")
        image = Image.open(io.BytesIO(base64.b64decode(b64)))
        return image.convert("RGB")
