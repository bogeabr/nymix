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
Checar domínios e redes (nome único ou arquivo, TLD único ou arquivo):

```
# Nome único + TLD único
poetry run nymix check -n elyra --tld com

# Lista de nomes + lista de TLDs
poetry run nymix check -a nomes.txt --tlds tlds.txt

# Com export JSON para gerar relatório depois
poetry run nymix check -n elyra --tld com --json saida.json


Abrir busca do INPI:

```bash
poetry run nymix inpi "elyra"

```

## Gerar relatório:

```md
Gerar relatório (a partir de um JSON exportado pelo `check`):
```

```bash
poetry run nymix report saida.json --formato markdown -o RELATORIO.md
poetry run nymix report saida.json --formato csv -o RELATORIO.csv
```

## Licença

MIT © 2025 bogeabr

---
