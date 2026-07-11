"""CLI do gerador de desenhos para colorir."""

from pathlib import Path
from typing import Optional

import typer

from coloured_drawings.config import get_settings
from coloured_drawings.sources.base import SourceError

app = typer.Typer(
    name="colorir",
    help="Gerador de desenhos para colorir — projeto do papá e da Ninita 🎨",
    no_args_is_help=True,
)


@app.command()
def gerar(
    prompt: str = typer.Argument(..., help="O que desenhar, ex: 'aladino da Disney'"),
    fonte: str = typer.Option("ai", "--fonte", "-f", help="Fonte da imagem: 'ai' ou 'web'"),
    paisagem: bool = typer.Option(False, "--paisagem", help="Página em modo paisagem"),
    sem_titulo: bool = typer.Option(False, "--sem-titulo", help="Não escrever título na página"),
    titulo: Optional[str] = typer.Option(None, "--titulo", "-t", help="Título personalizado"),
    detalhe: int = typer.Option(
        5, "--detalhe", "-d", min=1, max=9,
        help="Nível de detalhe do line-art (1=simples, 9=detalhado; só na fonte web)",
    ),
    sem_filtro_watermark: bool = typer.Option(
        False, "--sem-filtro-watermark",
        help="Aceita imagens com watermark (só fonte web)",
    ),
) -> None:
    """Gera um desenho para colorir a partir de palavras sugestivas."""
    from coloured_drawings.pipeline import generate

    page_title = None if sem_titulo else (titulo or prompt.capitalize())
    typer.echo(f"🖍️  A gerar '{prompt}' (fonte: {fonte})...")
    try:
        result = generate(prompt, source_name=fonte, landscape=paisagem,
                          title=page_title, detail=detalhe,
                          skip_watermark_check=sem_filtro_watermark)
    except SourceError as exc:
        typer.secho(f"Erro: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    typer.secho(f"✅ Pronto! PDF para imprimir: {result.pdf}", fg=typer.colors.GREEN)


@app.command()
def converter(
    ficheiro: Path = typer.Argument(..., exists=True, readable=True,
                                    help="Imagem local a converter (foto, desenho, ...)"),
    paisagem: bool = typer.Option(False, "--paisagem", help="Página em modo paisagem"),
    titulo: Optional[str] = typer.Option(None, "--titulo", "-t", help="Título na página"),
    detalhe: int = typer.Option(5, "--detalhe", "-d", min=1, max=9,
                                help="Nível de detalhe do line-art"),
) -> None:
    """Converte uma imagem tua em página para colorir."""
    from coloured_drawings.pipeline import convert_file

    typer.echo(f"🖍️  A converter '{ficheiro}'...")
    result = convert_file(ficheiro, landscape=paisagem, title=titulo, detail=detalhe)
    typer.secho(f"✅ Pronto! PDF para imprimir: {result.pdf}", fg=typer.colors.GREEN)


@app.command()
def listar() -> None:
    """Lista os desenhos já gerados."""
    output_dir = get_settings().output_dir
    if not output_dir.exists():
        typer.echo("Ainda não há desenhos. Começa com: colorir gerar \"aladino da Disney\"")
        return
    entries = sorted(d for d in output_dir.iterdir() if d.is_dir())
    if not entries:
        typer.echo("Ainda não há desenhos. Começa com: colorir gerar \"aladino da Disney\"")
        return
    for entry in entries:
        pdf = entry / "print.pdf"
        marker = "📄" if pdf.exists() else "⚠️ "
        typer.echo(f"{marker} {entry.name}")


if __name__ == "__main__":
    app()
