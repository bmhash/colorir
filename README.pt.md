# colorir 🎨

Transforma qualquer ideia numa pagina para colorir — basta escrever o que queres desenhar.

Escreves um prompt (ex: `"aladino da Disney"`), a ferramenta obtém ou gera uma
imagem estilo livro de colorir e produz um PDF A4 pronto a imprimir.

> [Read in English](README.md)

## Instalacao

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Para usares a fonte de IA (melhor qualidade), copia `.env.example` para `.env`
e preenche a `OPENAI_API_KEY`. A fonte `web` e gratuita e nao precisa de chave.

### Docker (recomendado)

```bash
docker build -t colorir .
docker run --rm -v ./output:/app/output colorir gerar "unicornio" --fonte web
```

## Utilizacao

```bash
# Pipeline completo com IA (requer OPENAI_API_KEY)
colorir gerar "aladino da Disney"

# Fonte gratuita: pesquisa web + conversao para line-art
colorir gerar "sereia" --fonte web

# Gerar e abrir o PDF automaticamente (WSL2, Linux, macOS, Windows)
colorir gerar "gato" --fonte web --abrir

# Opcoes
colorir gerar "castelo" --paisagem --sem-titulo
colorir gerar "gato" --fonte web --detalhe 3      # 1=simples, 9=detalhado
colorir gerar "cao" --titulo "O meu cao"

# Converter uma foto/imagem em pagina para colorir
colorir converter foto.jpg --abrir

# Listar desenhos ja gerados
colorir listar
```

Cada desenho fica em `output/<slug>-<timestamp>/` com:

- **`original.png`** — imagem obtida/gerada
- **`lineart.png`** — versao em contornos
- **`print.pdf`** — pagina A4 a 300 DPI, pronta a imprimir

## Arquitetura

Pipeline em 3 estagios desacoplados (`coloured_drawings/`):

- **`sources/`** — fontes de imagem com interface comum `ImageSource` (`ai` = OpenAI gpt-image-1, `web` = pesquisa DuckDuckGo). Novas fontes adicionam-se aqui.
- **`lineart/`** — conversao para contornos (OpenCV): filtro bilateral → threshold adaptativo → limpeza → engrossamento de linhas.
- **`printing/`** — composicao da pagina A4 e exportacao PDF (Pillow).

O CLI (`cli.py`, typer) e uma camada fina sobre `pipeline.py` — uma futura UI web
reutiliza o pipeline sem alteracoes.

## Testes

```bash
pytest
```

