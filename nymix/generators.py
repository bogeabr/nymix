from __future__ import annotations

import random
import pathlib
from typing import List, Optional


def _carregar_blacklist(path: Optional[str]) -> set[str]:
    if not path:
        return set()
    p = pathlib.Path(path)
    if not p.exists():
        return set()
    return {line.strip().lower() for line in p.read_text(encoding="utf-8").splitlines() if line.strip()}


def generate_names(
    temas: List[str],
    quantidade: int,
    min_len: int = 4,
    max_len: int = 8,
    permitir_hifen: bool = False,
    blacklist_path: Optional[str] = None,
) -> List[str]:
    """
    Gera nomes simples com base em temas e heurísticas básicas.
    """

    # Radicais básicos (pode evoluir depois com heurísticas mais inteligentes)
    radicais_base = [
        "ly", "ra", "no", "mi", "ka", "to", "zen", "lux", "el", "va", "mo", "ri", "na", "go"
    ]

    # Adiciona temas como radicais extras
    radicais_tema = [t[:3].lower() for t in temas if t]  # pega prefixos de temas
    radicais = radicais_base + radicais_tema

    blacklist = _carregar_blacklist(blacklist_path)

    nomes: set[str] = set()
    tentativas = 0
    max_tentativas = quantidade * 20  # limite pra evitar loop infinito

    while len(nomes) < quantidade and tentativas < max_tentativas:
        tentativas += 1

        # Combina 2 a 3 radicais
        partes = random.sample(radicais, k=random.choice([2, 3]))
        nome = "".join(partes).capitalize()

        # Regras de tamanho
        if not (min_len <= len(nome) <= max_len):
            continue

        # Adiciona hífen opcional
        if permitir_hifen and random.random() < 0.2:
            meio = len(nome) // 2
            nome = nome[:meio] + "-" + nome[meio:]

        # Blacklist
        if any(bad in nome.lower() for bad in blacklist):
            continue

        nomes.add(nome)

    return sorted(nomes)
