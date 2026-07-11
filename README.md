# Coloured Drawings 🎨

Gerador de desenhos para colorir — projeto do papá e da Ninita.

Escreves palavras sugestivas (ex: `"aladino da Disney"`), a plataforma obtém/gera
um desenho estilo livro de colorir e produz um PDF A4 pronto a imprimir.

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

# Opções
colorir gerar "castelo" --paisagem --sem-titulo
colorir gerar "gato" --fonte web --detalhe 3      # 1=simples, 9=detalhado
colorir gerar "cão" --titulo "Para a Ninita"

# Converter uma foto/imagem tua em página para colorir
colorir converter foto.jpg

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
