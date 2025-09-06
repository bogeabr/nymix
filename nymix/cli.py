from __future__ import annotations
import json
from pathlib import Path


from typing import Optional, List
import importlib.metadata as ilmd
import webbrowser

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Nymix — gerador e verificador de nomes (domínios, redes e INPI assistido).",
)
console = Console()

# ---------------------------------------------------------------------------
# Opção global: --version
# ---------------------------------------------------------------------------

def _version_callback(value: bool):
    if value:
        try:
            version = ilmd.version("nymix")
        except ilmd.PackageNotFoundError:
            # fallback quando rodando localmente sem instalar o pacote
            version = "0.1.0"
        console.print(f"[bold]nymix[/] v{version}")
        raise typer.Exit()

@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        callback=_version_callback,
        help="Mostra a versão do Nymix e sai.",
        is_eager=True,
    )
):
    """
    CLI do Nymix. Use subcomandos: [generate|check|report|inpi].
    """


# ---------------------------------------------------------------------------
# Subcomando: generate (lógica em generators.py)
# ---------------------------------------------------------------------------

@app.command("generate")
def cmd_generate(
    tema: List[str] = typer.Option(
        None,
        "--tema",
        "-t",
        help="Temas para guiar a geração (use várias flags para múltiplos). Ex.: -t tech -t tolkien",
    ),
    quantidade: int = typer.Option(
        20, "--qtd", "-q", min=1, max=500, help="Quantidade de nomes a gerar."
    ),
    min_len: int = typer.Option(4, "--min", help="Tamanho mínimo (caracteres)."),
    max_len: int = typer.Option(8, "--max", help="Tamanho máximo (caracteres)."),
    permitir_hifen: bool = typer.Option(
        False, "--permitir-hifen", help="Permite hífen nos nomes gerados."
    ),
    blacklist: Optional[str] = typer.Option(
        None,
        "--blacklist",
        help="Caminho para arquivo com radicais proibidos (um por linha).",
    ),
):
    """
    Gera nomes com base em temas e heurísticas simples.
    """
    try:
        from .generators import generate_names  # type: ignore
    except Exception:
        console.print(
            "[yellow]A lógica de geração ainda será implementada em [bold]generators.py[/].[/]\n"
            "Este comando apenas demonstra a interface por enquanto."
        )
        _preview_table = Table(title="Prévia da configuração")
        _preview_table.add_column("Chave")
        _preview_table.add_column("Valor")
        _preview_table.add_row("temas", ", ".join(tema or []) or "—")
        _preview_table.add_row("quantidade", str(quantidade))
        _preview_table.add_row("min_len", str(min_len))
        _preview_table.add_row("max_len", str(max_len))
        _preview_table.add_row("permitir_hifen", str(permitir_hifen))
        _preview_table.add_row("blacklist", blacklist or "—")
        console.print(_preview_table)
        raise typer.Exit(code=0)

    names = generate_names(
        temas=tema or [],
        quantidade=quantidade,
        min_len=min_len,
        max_len=max_len,
        permitir_hifen=permitir_hifen,
        blacklist_path=blacklist,
    )

    table = Table(title="Nomes gerados")
    table.add_column("#")
    table.add_column("nome", style="bold")
    for i, n in enumerate(names, start=1):
        table.add_row(str(i), n)
    console.print(table)


# ---------------------------------------------------------------------------
# Subcomando: check (agora: -n/--nome singular OU -a/--arquivo)
# ---------------------------------------------------------------------------

@app.command("check")
def cmd_check(
    nome: Optional[str] = typer.Option(
        None,
        "--nome",
        "-n",
        help="Um único nome para checagem. Ex.: -n elyra",
    ),
    arquivo: Optional[str] = typer.Option(
        None,
        "--arquivo",
        "-a",
        help="Arquivo com um nome por linha (plural).",
    ),
    tld: Optional[str] = typer.Option(
        None,
        "--tld",
        help="Um único TLD para checar. Ex.: --tld com",
    ),
    tlds: Optional[str] = typer.Option(
        None,
        "--tlds",
        help="Arquivo com vários TLDs (um por linha).",
    ),
    rede: List[str] = typer.Option(
        ["instagram", "x", "tiktok"],
        "--rede",
        help="Redes a checar (use várias flags). Padrão: instagram, x, tiktok",
    ),
    timeout: float = typer.Option(6.0, "--timeout", help="Timeout por requisição (s)."),
    json_saida: Optional[str] = typer.Option(
        None,
        "--json",
        help="Se informado, salva o resultado bruto em JSON (para usar no 'report').",
    ),
):
    """
    Checa disponibilidade básica de domínios e handles.
    Nome → singular (-n) ou arquivo (-a).
    TLD → singular (--tld) ou arquivo (--tlds).
    """

    # Validação: nomes
    if (nome is None and arquivo is None) or (nome and arquivo):
        console.print(
            "[red]Informe exatamente uma fonte de nomes:[/] "
            "[bold]--nome[/] (singular) [blue]ou[/] [bold]--arquivo[/] (plural)."
        )
        raise typer.Exit(code=2)

    nomes: List[str] = []
    if nome:
        nomes = [nome.strip()]
    else:
        p = Path(arquivo)  # type: ignore[arg-type]
        if not p.exists():
            console.print(f"[red]Arquivo não encontrado:[/] {arquivo}")
            raise typer.Exit(code=2)
        with p.open("r", encoding="utf-8") as f:
            nomes = [line.strip() for line in f if line.strip()]

    # Validação: TLDs
    if (tld is None and tlds is None) or (tld and tlds):
        console.print(
            "[red]Informe exatamente uma fonte de TLDs:[/] "
            "[bold]--tld[/] (singular) [blue]ou[/] [bold]--tlds[/] (plural)."
        )
        raise typer.Exit(code=2)

    tld_list: List[str] = []
    if tld:
        tld_list = [tld.strip()]
    else:
        p = Path(tlds)  # type: ignore[arg-type]
        if not p.exists():
            console.print(f"[red]Arquivo não encontrado:[/] {tlds}")
            raise typer.Exit(code=2)
        with p.open("r", encoding="utf-8") as f:
            tld_list = [line.strip() for line in f if line.strip()]

    # Import das rotinas
    try:
        from .checks.domain import check_domains  # type: ignore
        from .checks.handles import check_handles  # type: ignore
    except Exception:
        table = Table(title="Prévia da checagem")
        table.add_column("Chave")
        table.add_column("Valor")
        if arquivo:
            table.add_row("arquivo_nomes", arquivo)
            table.add_row("qtd_nomes", str(len(nomes)))
        else:
            table.add_row("nome", nomes[0])
        if tlds:
            table.add_row("arquivo_tlds", tlds)
            table.add_row("qtd_tlds", str(len(tld_list)))
        else:
            table.add_row("tld", tld_list[0])
        table.add_row("redes", ", ".join(rede))
        table.add_row("timeout", f"{timeout:.1f}s")
        console.print(table)
        raise typer.Exit(code=0)

    # Execução real
    dom_result = check_domains(nomes, tld_list, timeout=timeout)
    handles_result = check_handles(nomes, rede, timeout=timeout)

    # Empacota resultado para export opcional
    combined = {
        n: {
            "dominios": dom_result.get(n, {}),
            "handles": handles_result.get(n, {}),
        }
        for n in nomes
    }
    if json_saida:
        payload = {"resultados": combined}
        Path(json_saida).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        console.print(f"[green]JSON salvo em:[/] {json_saida}")

    table = Table(title="Resultados (resumo)")
    table.add_column("nome", style="bold")
    table.add_column("domínios")
    table.add_column("handles")
    for n in nomes:
        d = dom_result.get(n, {})
        h = handles_result.get(n, {})
        d_sum = ", ".join(f"{k}:{v}" for k, v in d.items()) if d else "—"
        h_sum = ", ".join(f"{k}:{v}" for k, v in h.items()) if h else "—"
        table.add_row(n, d_sum, h_sum)
    console.print(table)


# ---------------------------------------------------------------------------
# Subcomando: report (lógica em report.py)
# ---------------------------------------------------------------------------

@app.command("report")
def cmd_report(
    fonte: str = typer.Argument(
        ...,
        help="Caminho do arquivo JSON/CSV com resultados de check (ou outro formato aceito).",
    ),
    formato: str = typer.Option(
        "markdown",
        "--formato",
        "-f",
        help="Formato de saída: markdown|csv",
        case_sensitive=False,
    ),
    saida: Optional[str] = typer.Option(
        None, "--saida", "-o", help="Arquivo de saída (opcional)."
    ),
):
    """
    Gera relatório (Markdown/CSV) a partir de resultados de checagem.
    """
    try:
        from .report import build_report  # type: ignore
    except Exception:
        console.print(
            "[yellow]A construção de relatórios será implementada em [bold]report.py[/].[/]\n"
            "Por ora, este comando mostra apenas a configuração pretendida."
        )
        table = Table(title="Prévia do relatório")
        table.add_column("Chave")
        table.add_column("Valor")
        table.add_row("fonte", fonte)
        table.add_row("formato", formato)
        table.add_row("saida", saida or "—")
        console.print(table)
        raise typer.Exit(code=0)

    content = build_report(fonte, formato=formato)
    if saida:
        from pathlib import Path
        Path(saida).write_text(content, encoding="utf-8")
        console.print(f"[green]Relatório gravado em:[/] {saida}")
    else:
        console.print(content)


# ---------------------------------------------------------------------------
# Subcomando: inpi (por enquanto aqui; pode ser movido para inpi.py)
# ---------------------------------------------------------------------------

@app.command("inpi")
def cmd_inpi(
    termo: Optional[str] = typer.Argument(
        None, help="Termo para abrir na busca do INPI (classes 35 e 42 sugeridas)."
    ),
    abrir: bool = typer.Option(
        True, "--abrir/--nao-abrir", help="Abre o navegador automaticamente."
    ),
):
    """
    Abre a busca oficial do INPI para conferência manual (sem scraping).
    """
    if termo:
        url = "https://busca.inpi.gov.br/pePI/jsp/marcas/Pesquisa_classe_basica.jsp"
        console.print(
            "[blue]Abrindo página de busca de marcas do INPI.[/]\n"
            f"Termo sugerido para pesquisa: [bold]{termo}[/]"
        )
    else:
        url = "https://busca.inpi.gov.br/pePI/"
        console.print("[blue]Abrindo portal de buscas do INPI.[/]")

    console.print(f"[dim]{url}[/]")
    if abrir:
        try:
            webbrowser.open(url, new=2)
            console.print("[green]Navegador acionado.[/]")
        except Exception as e:
            console.print(f"[red]Falha ao abrir o navegador:[/] {e}")


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app()
