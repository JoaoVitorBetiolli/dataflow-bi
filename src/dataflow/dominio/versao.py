"""Versao publicada: conjunto consolidado disponibilizado ao Power BI."""

from dataclasses import dataclass
from datetime import datetime

from dataflow.dominio.valores import IdentificadorArquivo, PeriodoReferencia


@dataclass(frozen=True)
class VersaoPublicada:
    """Versao imutavel, ligada a carga e a tentativa de processamento que a originaram."""

    numero: int
    fonte: str
    periodo: PeriodoReferencia
    arquivo: IdentificadorArquivo
    numero_tentativa: int
    responsavel: str
    publicada_em: datetime
    total_registros: int

    def __post_init__(self) -> None:
        if self.numero < 1:
            raise ValueError("O numero da versao deve ser maior ou igual a 1.")
        if self.numero_tentativa < 1:
            raise ValueError("O numero da tentativa deve ser maior ou igual a 1.")
        if not self.responsavel.strip():
            raise ValueError("O responsavel pela publicacao e obrigatorio.")
        if self.total_registros < 0:
            raise ValueError("O total de registros nao pode ser negativo.")
