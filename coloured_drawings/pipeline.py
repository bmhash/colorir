"""Orquestração do pipeline: aquisição → line-art → PDF pronto a imprimir."""

from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from coloured_drawings.config import get_settings
from coloured_drawings.image_utils import resize_for_a4
from coloured_drawings.lineart import to_lineart
from coloured_drawings.printing import make_print_pdf
from coloured_drawings.sources import get_source
from coloured_drawings.utils import make_output_dir


@dataclass(frozen=True)
class PipelineResult:
    out_dir: Path
    original: Path
    lineart: Path
    pdf: Path


def generate(
    prompt: str,
    source_name: str = "ai",
    landscape: bool = False,
    title: str | None = None,
    detail: int = 5,
) -> PipelineResult:
    """Pipeline completo a partir de um prompt de texto."""
    source = get_source(source_name)
    image = source.fetch(prompt)
    image = resize_for_a4(image, landscape=landscape)
    out_dir = make_output_dir(get_settings().output_dir, prompt)
    return _finish(image, out_dir, skip_conversion=source.produces_lineart,
                   landscape=landscape, title=title, detail=detail)


def convert_file(
    input_path: Path,
    landscape: bool = False,
    title: str | None = None,
    detail: int = 5,
) -> PipelineResult:
    """Converte uma imagem local (foto/desenho) em página para colorir."""
    image = Image.open(input_path).convert("RGB")
    image = resize_for_a4(image, landscape=landscape)
    out_dir = make_output_dir(get_settings().output_dir, input_path.stem)
    return _finish(image, out_dir, skip_conversion=False,
                   landscape=landscape, title=title, detail=detail)


def _finish(
    image: Image.Image,
    out_dir: Path,
    skip_conversion: bool,
    landscape: bool,
    title: str | None,
    detail: int,
) -> PipelineResult:
    original_path = out_dir / "original.png"
    image.save(original_path)

    lineart = image if skip_conversion else to_lineart(image, detail=detail)
    lineart_path = out_dir / "lineart.png"
    lineart.save(lineart_path)

    pdf_path = make_print_pdf(lineart, out_dir / "print.pdf", landscape=landscape, title=title)
    return PipelineResult(out_dir=out_dir, original=original_path,
                          lineart=lineart_path, pdf=pdf_path)
