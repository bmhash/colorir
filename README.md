# colorir 🎨

Turn any idea into a printable coloring page — just type what you want to draw.

Type a prompt (e.g. `"aladino da Disney"`), and the tool fetches or generates
a coloring-book-style image and produces a print-ready A4 PDF.

## Instalação

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Para usares a fonte de IA (melhor qualidade), copia `.env.example` para `.env`
e preenche a `OPENAI_API_KEY`. A fonte `web` é gratuita e não precisa de chave.

## Utilização

```bash
# Pipeline completo com IA (requer OPENAI_API_KEY)
colorir gerar "aladino da Disney"

# Fonte gratuita: pesquisa web + conversão para line-art
colorir gerar "sereia" --fonte web

# Gerar e abrir o PDF automaticamente (WSL2, Linux, macOS)
colorir gerar "gato" --fonte web --abrir

# Opções
colorir gerar "castelo" --paisagem --sem-titulo
colorir gerar "gato" --fonte web --detalhe 3      # 1=simples, 9=detalhado
colorir gerar "cão" --titulo "O meu cão"

# Converter uma foto/imagem tua em página para colorir
colorir converter foto.jpg --abrir

# Listar desenhos já gerados
colorir listar
```

Cada desenho fica em `output/<slug>-<timestamp>/` com:

- **`original.png`** — imagem obtida/gerada
- **`lineart.png`** — versão em contornos
- **`print.pdf`** — página A4 a 300 DPI, pronta a imprimir

## Arquitetura

Pipeline em 3 estágios desacoplados (`coloured_drawings/`):

- **`sources/`** — fontes de imagem com interface comum `ImageSource` (`ai` = OpenAI gpt-image-1, `web` = pesquisa DuckDuckGo). Novas fontes adicionam-se aqui.
- **`lineart/`** — conversão para contornos (OpenCV): filtro bilateral → threshold adaptativo → limpeza → engrossamento de linhas.
- **`printing/`** — composição da página A4 e exportação PDF (Pillow).

O CLI (`cli.py`, typer) é uma camada fina sobre `pipeline.py` — a v2 (UI web)
reutiliza o pipeline sem alterações.

## Testes

```bash
pytest
```
