"""Regras de qualidade aplicadas aos registros de uma carga."""

from collections.abc import Iterable, Sequence

from dataflow.dominio.ocorrencia import OcorrenciaQualidade, Severidade
from dataflow.dominio.registro import RegistroOperacional
from dataflow.dominio.valores import PeriodoReferencia


def validar_registros(
    registros: Sequence[RegistroOperacional],
    periodo: PeriodoReferencia,
    campos_obrigatorios: Iterable[str],
) -> list[OcorrenciaQualidade]:
    obrigatorios = list(campos_obrigatorios)
    ocorrencias = []
    primeira_linha_da_chave = {}
    for registro in registros:
        for campo in obrigatorios:
            if registro.campo_vazio(campo):
                ocorrencias.append(
                    OcorrenciaQualidade(
                        registro.linha, campo, "campo obrigatorio vazio", Severidade.BLOQUEIO
                    )
                )
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
        if not periodo.contem(registro.chave.data):
            ocorrencias.append(
                OcorrenciaQualidade(
                    registro.linha,
                    "data",
                    "data fora do periodo de referencia",
                    Severidade.ALERTA,
                )
            )
    return ocorrencias
