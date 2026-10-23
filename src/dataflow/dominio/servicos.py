"""Servicos do dominio que coordenam as portas e as regras de qualidade."""

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from dataflow.dominio.ocorrencia import OcorrenciaQualidade
from dataflow.dominio.portas import LeitorArquivo
from dataflow.dominio.qualidade import validar_registros
from dataflow.dominio.registro import RegistroOperacional
from dataflow.dominio.valores import PeriodoReferencia


@dataclass(frozen=True)
class ResultadoValidacao:
    """Registros lidos e ocorrencias encontradas na validacao de um arquivo."""

    registros: tuple[RegistroOperacional, ...]
    ocorrencias: tuple[OcorrenciaQualidade, ...]

    @property
    def possui_bloqueio(self) -> bool:
        return any(ocorrencia.bloqueante for ocorrencia in self.ocorrencias)

    @property
    def registros_validos(self) -> tuple[RegistroOperacional, ...]:
        linhas_bloqueadas = {o.linha for o in self.ocorrencias if o.bloqueante}
        return tuple(r for r in self.registros if r.linha not in linhas_bloqueadas)


class ValidadorDeArquivo:
    """Le um arquivo pela porta LeitorArquivo e aplica as regras de qualidade."""

    def __init__(self, leitor: LeitorArquivo) -> None:
        self._leitor = leitor

    def validar(
        self,
        caminho: Path,
        periodo: PeriodoReferencia,
        campos_obrigatorios: Iterable[str],
    ) -> ResultadoValidacao:
        registros = self._leitor.ler(caminho)
        ocorrencias = validar_registros(registros, periodo, campos_obrigatorios)
        return ResultadoValidacao(tuple(registros), tuple(ocorrencias))
