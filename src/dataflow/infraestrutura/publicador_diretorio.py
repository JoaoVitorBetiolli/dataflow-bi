"""Adaptador que publica cada versao como um arquivo CSV em um diretorio."""

import csv
from collections.abc import Sequence
from pathlib import Path

from dataflow.dominio.registro import RegistroOperacional


class PublicadorEmDiretorio:
    """Implementa a porta PublicadorBI gravando versao_NNNN.csv no diretorio de destino."""

    def __init__(self, diretorio: Path) -> None:
        self._diretorio = Path(diretorio)

    def publicar(self, numero_versao: int, registros: Sequence[RegistroOperacional]) -> Path:
        self._diretorio.mkdir(parents=True, exist_ok=True)
        destino = self._diretorio / f"versao_{numero_versao:04d}.csv"
        colunas = sorted({campo for registro in registros for campo in registro.campos})
        with destino.open("w", newline="", encoding="utf-8") as arquivo:
            escritor = csv.DictWriter(arquivo, fieldnames=colunas)
            escritor.writeheader()
            for registro in registros:
                escritor.writerow(dict(registro.campos))
        return destino
