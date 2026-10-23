"""Ocorrencias de qualidade encontradas ao validar os registros de uma carga."""

from dataclasses import dataclass
from enum import Enum


class Severidade(Enum):
    """Alerta permite publicar a carga; bloqueio impede a publicacao."""

    ALERTA = "alerta"
    BLOQUEIO = "bloqueio"


@dataclass(frozen=True)
class OcorrenciaQualidade:
    """Problema encontrado em um registro, com linha, campo, motivo e severidade."""

    linha: int
    campo: str
    motivo: str
    severidade: Severidade

    def __post_init__(self) -> None:
        if self.linha < 1:
            raise ValueError("A linha da ocorrencia deve ser maior ou igual a 1.")
        if not self.campo.strip():
            raise ValueError("O campo da ocorrencia e obrigatorio.")
        if not self.motivo.strip():
            raise ValueError("O motivo da ocorrencia e obrigatorio.")

    @property
    def bloqueante(self) -> bool:
        return self.severidade is Severidade.BLOQUEIO
