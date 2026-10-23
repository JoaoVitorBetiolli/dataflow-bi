"""Portas do dominio: contratos que o mundo externo precisa cumprir."""

from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

from dataflow.dominio.registro import RegistroOperacional


class ArquivoInvalidoError(ValueError):
    """O arquivo recebido nao tem a estrutura esperada."""


class LeitorArquivo(Protocol):
    """Porta de entrada: transforma um arquivo de extracao em registros do dominio."""

    def ler(self, caminho: Path) -> list[RegistroOperacional]: ...


class PublicadorBI(Protocol):
    """Porta de saida: disponibiliza uma versao dos registros validos ao Power BI."""

    def publicar(self, numero_versao: int, registros: Sequence[RegistroOperacional]) -> Path: ...
