"""Interface de linha de comando do DataFlow BI."""

import argparse
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from dataflow.aplicacao.processar_carga import (
    CAMPOS_OBRIGATORIOS_PADRAO,
    ProcessarEPublicarCarga,
    ResultadoExecucao,
)
from dataflow.dominio.valores import PeriodoReferencia
from dataflow.infraestrutura.leitor_csv import LeitorCsv
from dataflow.infraestrutura.publicador_diretorio import PublicadorEmDiretorio

SUCESSO = 0
CARGA_BLOQUEADA = 1
ARQUIVO_OU_ENTRADA_INVALIDA = 2


def montar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m dataflow",
        description="Valida um arquivo CSV e publica uma versao para o Power BI.",
    )
    parser.add_argument("arquivo", type=Path, help="arquivo CSV de extracao")
    parser.add_argument("--fonte", required=True, help="fonte de dados, por exemplo SAP ou TMS")
    parser.add_argument("--inicio", required=True, type=date.fromisoformat, help="AAAA-MM-DD")
    parser.add_argument("--fim", required=True, type=date.fromisoformat, help="AAAA-MM-DD")
    parser.add_argument("--responsavel", required=True, help="quem esta enviando a carga")
    parser.add_argument("--saida", type=Path, default=Path("publicado"), help="pasta das versoes")
    parser.add_argument(
        "--obrigatorios",
        nargs="+",
        default=list(CAMPOS_OBRIGATORIOS_PADRAO),
        help="campos obrigatorios alem da chave",
    )
    return parser


def proximo_numero_de_versao(diretorio: Path) -> int:
    if not diretorio.exists():
        return 1
    numeros = [
        int(sufixo)
        for arquivo in diretorio.glob("versao_*.csv")
        if (sufixo := arquivo.stem.removeprefix("versao_")).isdigit()
    ]
    return max(numeros, default=0) + 1


def relatar(resultado: ResultadoExecucao) -> int:
    if resultado.erro_estrutura:
        print(f"Estrutura invalida: {resultado.erro_estrutura}")
        return ARQUIVO_OU_ENTRADA_INVALIDA
    for ocorrencia in resultado.ocorrencias:
        print(
            f"[{ocorrencia.severidade.value}] linha {ocorrencia.linha}, "
            f"campo {ocorrencia.campo}: {ocorrencia.motivo}"
        )
    if resultado.versao is None:
        print("Carga bloqueada: corrija o arquivo e envie novamente.")
        return CARGA_BLOQUEADA
    print(
        f"Versao {resultado.versao.numero} publicada com "
        f"{resultado.versao.total_registros} registros: {resultado.destino}"
    )
    return SUCESSO


def main(argv: Sequence[str] | None = None) -> int:
    args = montar_parser().parse_args(argv)
    try:
        periodo = PeriodoReferencia(args.inicio, args.fim)
        caso_de_uso = ProcessarEPublicarCarga(
            LeitorCsv(), PublicadorEmDiretorio(args.saida), args.obrigatorios
        )
        resultado = caso_de_uso.executar(
            args.arquivo,
            args.fonte,
            periodo,
            args.responsavel,
            proximo_numero_de_versao(args.saida),
        )
    except (ValueError, OSError) as erro:
        print(f"Erro: {erro}")
        return ARQUIVO_OU_ENTRADA_INVALIDA
    return relatar(resultado)
