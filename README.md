# Nymix — gerador e verificador de nomes

CLI para gerar nomes e checar disponibilidade básica de domínios, handles e abrir a busca do INPI.

## Instalação

Clone o repositório e instale com [Poetry](https://python-poetry.org/):

```bash
git clone https://github.com/bogeabr/nymix.git
cd nymix
poetry install
```

## Uso

Ajuda geral:

```bash
poetry run nymix --help
```

Gerar nomes:

```bash
poetry run nymix generate -t tech -t tolkien --qtd 10
```

Checar domínios e redes:

```bash
poetry run nymix check -n elyra -n lumora
```

Abrir busca do INPI:

```bash
poetry run nymix inpi "elyra"
```

Gerar relatório:

```bash
poetry run nymix report resultados.json --formato markdown -o RELATORIO.md
```

## Licença

MIT © 2025 bogeabr

---
