# nymix/checks/handles.py
from __future__ import annotations

from typing import Dict, List
import httpx
import re

# Mapeia rede -> padrão de URL para perfil
REDES_BASE = {
    "instagram": "https://www.instagram.com/{handle}/",
    "x": "https://x.com/{handle}",
    "tiktok": "https://www.tiktok.com/@{handle}",
}

# Handles válidos (bem permissivo; evita espaços e caracteres claramente inválidos)
_VALID_HANDLE = re.compile(r"^[a-zA-Z0-9._-]{1,30}$")

def _san(handle: str) -> str:
    """Normaliza o handle: trim + lower + remove espaços internos."""
    h = (handle or "").strip().lower().replace(" ", "")
    return h

def _is_valid(handle: str) -> bool:
    return bool(_VALID_HANDLE.match(handle))

def check_handles(
    nomes: List[str],
    redes: List[str],
    timeout: float = 6.0,
) -> Dict[str, Dict[str, str]]:
    """
    Checa disponibilidade básica de handles nas redes informadas.
    Retorna: {nome: {rede: status}}, status ∈ {"available","registered","unknown"}.
    Regras:
      - 404 => available
      - 200/301/302 => registered
      - outros / exceções => unknown
    """
    resultados: Dict[str, Dict[str, str]] = {}

    headers = {
        # User-Agent simples para evitar bloqueios óbvios
        "User-Agent": "Mozilla/5.0 (compatible; Nymix/0.1; +https://github.com/bogeabr/nymix)"
    }

    # follow_redirects=True pois algumas redes redirecionam perfis inexistentes
    with httpx.Client(timeout=timeout, follow_redirects=True, headers=headers) as client:
        for nome in nomes:
            h = _san(nome)
            resultados[nome] = {}
            for rede in redes:
                rkey = rede.lower().strip()
                base = REDES_BASE.get(rkey)

                # Rede não suportada
                if not base:
                    resultados[nome][rkey] = "unknown"
                    continue

                # Handle evidentemente inválido
                if not _is_valid(h):
                    resultados[nome][rkey] = "unknown"
                    continue

                url = base.format(handle=h)
                try:
                    resp = client.get(url)
                    sc = resp.status_code

                    if sc == 404:
                        status = "available"
                    elif sc in (200, 301, 302):
                        # Alguns 200 podem ser página "not found" custom — heurística simples:
                        # Se a rede retornar página genérica 'not found' com 200, difícil padronizar sem parsing.
                        status = "registered"
                    else:
                        status = "unknown"

                    resultados[nome][rkey] = status
                except Exception:
                    resultados[nome][rkey] = "unknown"

    return resultados
