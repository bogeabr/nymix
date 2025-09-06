from __future__ import annotations

import dns.resolver
from typing import Dict, List


def check_domains(
    nomes: List[str],
    tlds: List[str],
    timeout: float = 6.0,
) -> Dict[str, Dict[str, str]]:
    """
    Checa disponibilidade básica de domínios por DNS.
    Retorna dict: {nome: {tld: status}}
    Status = "available" | "registered" | "unknown"
    """
    resultados: Dict[str, Dict[str, str]] = {}

    resolver = dns.resolver.Resolver(configure=True)
    resolver.lifetime = timeout
    resolver.timeout = timeout

    for nome in nomes:
        resultados[nome] = {}
        for tld in tlds:
            dominio = f"{nome.lower()}.{tld}"
            try:
                # Se resolve algum registro A/AAAA, consideramos registrado
                answers = resolver.resolve(dominio, "A")
                if answers:
                    resultados[nome][tld] = "registered"
                    continue
            except dns.resolver.NXDOMAIN:
                resultados[nome][tld] = "available"
                continue
            except dns.resolver.NoAnswer:
                # Pode estar registrado mas sem A record → tratamos como unknown
                resultados[nome][tld] = "unknown"
                continue
            except dns.exception.Timeout:
                resultados[nome][tld] = "unknown"
                continue
            except Exception:
                resultados[nome][tld] = "unknown"
                continue

            # fallback se não caiu em nenhum caso
            resultados[nome][tld] = "unknown"

    return resultados
