"""Value objects do dominio: conceitos sem identidade propria, definidos pelos seus valores."""

from dataclasses import dataclass
from datetime import date

EXTENSOES_ACEITAS = (".csv", ".xlsx")


@dataclass(frozen=True)
class PeriodoReferencia:
    """Intervalo de datas ao qual os dados de uma carga se referem."""

    inicio: date
    fim: date

    def __post_init__(self) -> None:
        if self.fim < self.inicio:
            raise ValueError("A data final do periodo nao pode ser anterior a data inicial.")

    def contem(self, data: date) -> bool:
        return self.inicio <= data <= self.fim


@dataclass(frozen=True)
class ChaveRegistro:
    """Chave de negocio (origem, codigo e data) usada para detectar duplicidade."""

    origem: str
    codigo: str
    data: date

    def __post_init__(self) -> None:
        origem = self.origem.strip().upper()
        codigo = self.codigo.strip()
        if not origem:
            raise ValueError("A origem da chave de registro e obrigatoria.")
        if not codigo:
            raise ValueError("O codigo da chave de registro e obrigatorio.")
        object.__setattr__(self, "origem", origem)
        object.__setattr__(self, "codigo", codigo)


@dataclass(frozen=True)
class IdentificadorArquivo:
    """Identifica o arquivo de extracao recebido por nome e hash."""

    nome: str
    hash_arquivo: str

    def __post_init__(self) -> None:
        if not self.nome.strip():
            raise ValueError("O nome do arquivo e obrigatorio.")
        if not self.hash_arquivo.strip():
            raise ValueError("O hash do arquivo e obrigatorio.")
        if not self.nome.lower().endswith(EXTENSOES_ACEITAS):
            formatos = ", ".join(EXTENSOES_ACEITAS)
            raise ValueError(f"Formato nao aceito. Formatos aceitos: {formatos}.")
