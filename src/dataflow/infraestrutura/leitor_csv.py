"""Adaptador que le arquivos CSV e entrega registros do dominio."""

import csv
from datetime import date
from pathlib import Path

from dataflow.dominio.portas import ArquivoInvalidoError
from dataflow.dominio.registro import RegistroOperacional
from dataflow.dominio.valores import ChaveRegistro

COLUNAS_DA_CHAVE = ("origem", "codigo", "data")


class LeitorCsv:
    """Implementa a porta LeitorArquivo para arquivos CSV com cabecalho."""

    def ler(self, caminho: Path) -> list[RegistroOperacional]:
        with Path(caminho).open(newline="", encoding="utf-8") as arquivo:
            leitor = csv.DictReader(arquivo)
            ausentes = [c for c in COLUNAS_DA_CHAVE if c not in (leitor.fieldnames or [])]
            if ausentes:
                raise ArquivoInvalidoError(f"Colunas obrigatorias ausentes: {', '.join(ausentes)}.")
            return [self._converter(linha, campos) for linha, campos in enumerate(leitor, start=2)]

    @staticmethod
    def _converter(linha: int, campos: dict[str, str]) -> RegistroOperacional:
        try:
            chave = ChaveRegistro(
                campos["origem"], campos["codigo"], date.fromisoformat(campos["data"])
            )
        except ValueError as erro:
            raise ArquivoInvalidoError(f"Linha {linha}: {erro}") from erro
        return RegistroOperacional(linha, chave, campos)
