"""Registro operacional: uma linha do arquivo que representa um evento da operacao."""

from collections.abc import Mapping
from dataclasses import dataclass

from dataflow.dominio.valores import ChaveRegistro


@dataclass(frozen=True)
class RegistroOperacional:
    """Linha do arquivo de extracao, identificada pela sua chave de registro."""

    linha: int
    chave: ChaveRegistro
    campos: Mapping[str, str]

    def __post_init__(self) -> None:
        if self.linha < 1:
            raise ValueError("A linha do registro deve ser maior ou igual a 1.")

    def valor_de(self, campo: str) -> str:
        return (self.campos.get(campo) or "").strip()

    def campo_vazio(self, campo: str) -> bool:
        return not self.valor_de(campo)
