# nymix/report.py
from __future__ import annotations

from typing import Dict, List, Any, Tuple
from pathlib import Path
import json
import csv
import io

# -------------------------------------------------------------------
# Entrada esperada (recomendado): JSON com uma das estruturas:
#
# 1) Dict mapeando nome -> { "dominios": {tld:status}, "handles": {rede:status} }
#    {
#      "alura": {"dominios": {"com":"registered"}, "handles":{"instagram":"registered","x":"registered","tiktok":"registered"}}
#    }
#
# 2) Lista de itens com as mesmas chaves:
#    [
#      {"nome":"alura", "dominios":{"com":"registered"}, "handles":{"instagram":"registered","x":"registered","tiktok":"registered"}}
#    ]
#
# 3) Wrapper com chave "itens" ou "resultados":
#    {"itens":[ {...}, {...} ]}
#    {"resultados": { "alura": {...}, "lumora": {...} }}
#
# Campos aceitos: "dominios" ou "domínios" (ambos).
# -------------------------------------------------------------------

Row = Dict[str, Any]

def _coerce_keys(d: Dict[str, Any]) -> Dict[str, Any]:
    """Normaliza chaves 'domín(i)os' e garante estrutura mínima."""
    if not isinstance(d, dict):
        return {}
    out = dict(d)
    if "domínios" in out and "dominios" not in out:
        out["dominios"] = out.pop("domínios")
    return out

def _to_rows_from_mapping(mp: Dict[str, Any]) -> List[Row]:
    rows: List[Row] = []
    for nome, payload in mp.items():
        payload = _coerce_keys(payload or {})
        dominios = payload.get("dominios") or {}
        handles = payload.get("handles") or {}
        rows.append({"nome": nome, "dominios": dict(dominios), "handles": dict(handles)})
    return rows

def _to_rows_from_list(lst: List[Any]) -> List[Row]:
    rows: List[Row] = []
    for item in lst:
        if not isinstance(item, dict):
            continue
        item = _coerce_keys(item)
        nome = item.get("nome")
        if not nome:
            # tenta inferir a partir de chaves únicas
            # (ex.: { "alura": {...}}) — pouco comum, mas guardamos compatibilidade
            if len(item) == 1:
                k = next(iter(item.keys()))
                if isinstance(item[k], dict):
                    nome = k
                    item = _coerce_keys(item[k])
        if not nome:
            continue
        rows.append({
            "nome": nome,
            "dominios": dict(item.get("dominios") or {}),
            "handles": dict(item.get("handles") or {}),
        })
    return rows

def _load_rows_from_json(path: Path) -> List[Row]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = _coerce_keys(data)
        if "itens" in data and isinstance(data["itens"], list):
            return _to_rows_from_list(data["itens"])
        if "resultados" in data and isinstance(data["resultados"], dict):
            return _to_rows_from_mapping(data["resultados"])
        # dict direto mapeando nome -> payload
        return _to_rows_from_mapping(data)
    elif isinstance(data, list):
        return _to_rows_from_list(data)
    return []

def _load_rows_from_csv(path: Path) -> List[Row]:
    # CSV genérico: tenta ler colunas dinâmicas.
    # Esperado ao menos 'nome'; demais colunas serão levadas como
    # dominios (prefixo "dom:" ou "tld:" ou valor com ponto) e handles (prefixo "rede:" ou conhecido).
    rows: List[Row] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for line in reader:
            nome = (line.get("nome") or "").strip()
            if not nome:
                continue
            dominios: Dict[str, str] = {}
            handles: Dict[str, str] = {}
            for k, v in (line or {}).items():
                if k == "nome":
                    continue
                val = (v or "").strip()
                key = (k or "").strip().lower()
                # heurísticas simples
                if key.startswith("dom:") or key.startswith("tld:") or "." in key:
                    tld = key.replace("dom:", "").replace("tld:", "")
                    dominios[tld] = val or "unknown"
                elif key.startswith("rede:"):
                    rede = key.replace("rede:", "")
                    handles[rede] = val or "unknown"
                elif key in {"instagram", "x", "tiktok", "linkedin", "youtube"}:
                    handles[key] = val or "unknown"
                else:
                    # ignora ou armazena para futuro
                    pass
            rows.append({"nome": nome, "dominios": dominios, "handles": handles})
    return rows

def _collect_headers(rows: List[Row]) -> Tuple[List[str], List[str]]:
    tlds = set()
    redes = set()
    for r in rows:
        for tld in (r.get("dominios") or {}).keys():
            tlds.add(tld)
        for rede in (r.get("handles") or {}).keys():
            redes.add(rede)
    return sorted(tlds), sorted(redes)

def _render_markdown(rows: List[Row]) -> str:
    tlds, redes = _collect_headers(rows)
    buf = io.StringIO()
    # Cabeçalho
    headers = ["nome"] + [f"{t}" for t in tlds] + [f"{r}" for r in redes]
    buf.write("| " + " | ".join(headers) + " |\n")
    buf.write("|" + "|".join(["---"] * len(headers)) + "|\n")

    # Linhas
    for r in rows:
        line = [r["nome"]]
        for t in tlds:
            line.append((r.get("dominios") or {}).get(t, "—"))
        for rr in redes:
            line.append((r.get("handles") or {}).get(rr, "—"))
        buf.write("| " + " | ".join(line) + " |\n")
    return buf.getvalue()

def _render_csv(rows: List[Row]) -> str:
    tlds, redes = _collect_headers(rows)
    headers = ["nome"] + [f"{t}" for t in tlds] + [f"{r}" for r in redes]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=headers)
    writer.writeheader()
    for r in rows:
        row: Dict[str, str] = {"nome": r["nome"]}
        for t in tlds:
            row[t] = (r.get("dominios") or {}).get(t, "")
        for rr in redes:
            row[rr] = (r.get("handles") or {}).get(rr, "")
        writer.writerow(row)
    return buf.getvalue()

def build_report(fonte: str, formato: str = "markdown") -> str:
    """
    Lê resultados de checagem e retorna relatório em Markdown ou CSV.
    Suporta:
      - JSON (recomendado), ver formatos no cabeçalho do arquivo.
      - CSV (heurístico).
    """
    p = Path(fonte)
    if not p.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {fonte}")

    rows: List[Row] = []
    suffix = p.suffix.lower()

    if suffix == ".json":
        rows = _load_rows_from_json(p)
    elif suffix == ".csv":
        rows = _load_rows_from_csv(p)
    else:
        # tenta JSON primeiro, senão CSV
        try:
            rows = _load_rows_from_json(p)
        except Exception:
            rows = _load_rows_from_csv(p)

    if not rows:
        # Mensagem clara para facilitar troubleshooting
        raise ValueError(
            "Nenhum dado válido encontrado. "
            "Use JSON no formato recomendado (ver docstring) ou CSV com colunas: "
            "'nome' + TLDs (ex.: com, com.br) + redes (ex.: instagram, x, tiktok)."
        )

    formato = (formato or "markdown").strip().lower()
    if formato in {"md", "markdown"}:
        return _render_markdown(rows)
    elif formato == "csv":
        return _render_csv(rows)
    else:
        raise ValueError("Formato inválido. Use 'markdown' ou 'csv'.")
