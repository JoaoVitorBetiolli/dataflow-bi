"""Processamento: uma tentativa de aplicar as regras de qualidade sobre uma carga."""

from dataclasses import dataclass

from dataflow.dominio.ocorrencia import OcorrenciaQualidade
from dataflow.dominio.servicos import ResultadoValidacao


@dataclass(frozen=True)
class Processamento:
    """Tentativa numerada de processar o arquivo de uma carga."""

    numero: int
    resultado: ResultadoValidacao

    def __post_init__(self) -> None:
        if self.numero < 1:
            raise ValueError("O numero da tentativa deve ser maior ou igual a 1.")

    @property
    def possui_bloqueio(self) -> bool:
        return self.resultado.possui_bloqueio

    @property
    def total_validos(self) -> int:
        return len(self.resultado.registros_validos)

    @property
    def ocorrencias(self) -> tuple[OcorrenciaQualidade, ...]:
        return self.resultado.ocorrencias
