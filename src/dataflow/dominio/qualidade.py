"""Regras de qualidade aplicadas aos registros de uma carga (padrao Strategy)."""

from abc import ABC, abstractmethod
from collections.abc import Iterable, Sequence

from dataflow.dominio.ocorrencia import OcorrenciaQualidade, Severidade
from dataflow.dominio.registro import RegistroOperacional
from dataflow.dominio.valores import PeriodoReferencia


class RegraQualidade(ABC):
    """Strategy: cada regra sabe verificar um tipo de problema nos registros."""

    @abstractmethod
    def verificar(self, registros: Sequence[RegistroOperacional]) -> list[OcorrenciaQualidade]:
        """Devolve as ocorrencias encontradas pela regra."""


class CamposObrigatorios(RegraQualidade):
    """Concrete Strategy: campo obrigatorio vazio impede a publicacao."""

    def __init__(self, campos: Iterable[str]) -> None:
        self._campos = list(campos)

    def verificar(self, registros: Sequence[RegistroOperacional]) -> list[OcorrenciaQualidade]:
        return [
            OcorrenciaQualidade(
                registro.linha, campo, "campo obrigatorio vazio", Severidade.BLOQUEIO
            )
            for registro in registros
            for campo in self._campos
            if registro.campo_vazio(campo)
        ]


class SemDuplicidade(RegraQualidade):
    """Concrete Strategy: duas linhas com a mesma chave de registro sao duplicidade."""

    def verificar(self, registros: Sequence[RegistroOperacional]) -> list[OcorrenciaQualidade]:
        ocorrencias = []
        primeira_linha_da_chave = {}
        for registro in registros:
            if registro.chave in primeira_linha_da_chave:
                original = primeira_linha_da_chave[registro.chave]
                ocorrencias.append(
                    OcorrenciaQualidade(
                        registro.linha,
                        "chave",
                        f"registro duplicado da linha {original}",
                        Severidade.BLOQUEIO,
                    )
                )
            else:
                primeira_linha_da_chave[registro.chave] = registro.linha
        return ocorrencias


class DentroDoPeriodo(RegraQualidade):
    """Concrete Strategy: data fora do periodo de referencia gera apenas alerta."""

    def __init__(self, periodo: PeriodoReferencia) -> None:
        self._periodo = periodo

    def verificar(self, registros: Sequence[RegistroOperacional]) -> list[OcorrenciaQualidade]:
        return [
            OcorrenciaQualidade(
                registro.linha,
                "data",
                "data fora do periodo de referencia",
                Severidade.ALERTA,
            )
            for registro in registros
            if not self._periodo.contem(registro.chave.data)
        ]


class ValidadorQualidade:
    """Context: aplica uma lista de regras sem conhecer o detalhe de cada uma."""

    def __init__(self, regras: Iterable[RegraQualidade]) -> None:
        self._regras = list(regras)

    def validar(self, registros: Sequence[RegistroOperacional]) -> list[OcorrenciaQualidade]:
        ocorrencias: list[OcorrenciaQualidade] = []
        for regra in self._regras:
            ocorrencias.extend(regra.verificar(registros))
        return ocorrencias


def validar_registros(
    registros: Sequence[RegistroOperacional],
    periodo: PeriodoReferencia,
    campos_obrigatorios: Iterable[str],
) -> list[OcorrenciaQualidade]:
    validador = ValidadorQualidade(
        [CamposObrigatorios(campos_obrigatorios), SemDuplicidade(), DentroDoPeriodo(periodo)]
    )
    return validador.validar(registros)
