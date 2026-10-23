"""Caso de uso: processar uma carga e, sem bloqueios, publicar a versao."""

import hashlib
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from dataflow.dominio.carga import CargaDados
from dataflow.dominio.ocorrencia import OcorrenciaQualidade
from dataflow.dominio.portas import ArquivoInvalidoError, LeitorArquivo, PublicadorBI
from dataflow.dominio.servicos import ValidadorDeArquivo
from dataflow.dominio.valores import IdentificadorArquivo, PeriodoReferencia
from dataflow.dominio.versao import VersaoPublicada

CAMPOS_OBRIGATORIOS_PADRAO = ("codigo", "quantidade")


@dataclass(frozen=True)
class ResultadoExecucao:
    """O que aconteceu com a carga: publicada, bloqueada ou com estrutura invalida."""

    carga: CargaDados
    versao: VersaoPublicada | None = None
    destino: Path | None = None
    ocorrencias: tuple[OcorrenciaQualidade, ...] = ()
    erro_estrutura: str | None = None

    @property
    def publicada(self) -> bool:
        return self.versao is not None


class ProcessarEPublicarCarga:
    """Orquestra leitura, validacao, processamento e publicacao de uma carga."""

    def __init__(
        self,
        leitor: LeitorArquivo,
        publicador: PublicadorBI,
        campos_obrigatorios: Sequence[str] = CAMPOS_OBRIGATORIOS_PADRAO,
        relogio: Callable[[], datetime] = datetime.now,
    ) -> None:
        self._leitor = leitor
        self._publicador = publicador
        self._campos_obrigatorios = tuple(campos_obrigatorios)
        self._relogio = relogio

    def executar(
        self,
        caminho: Path,
        fonte: str,
        periodo: PeriodoReferencia,
        responsavel: str,
        numero_versao: int,
    ) -> ResultadoExecucao:
        caminho = Path(caminho)
        hash_arquivo = hashlib.sha256(caminho.read_bytes()).hexdigest()
        arquivo = IdentificadorArquivo(caminho.name, hash_arquivo)
        carga = CargaDados(fonte, periodo, arquivo, responsavel)

        validador = ValidadorDeArquivo(self._leitor)
        try:
            resultado = validador.validar(caminho, periodo, self._campos_obrigatorios)
        except ArquivoInvalidoError as erro:
            carga.validar_estrutura(False)
            return ResultadoExecucao(carga, erro_estrutura=str(erro))

        carga.validar_estrutura(True)
        processamento = carga.processar(resultado)
        if processamento.possui_bloqueio:
            return ResultadoExecucao(carga, ocorrencias=processamento.ocorrencias)

        versao = carga.publicar(numero_versao, responsavel, self._relogio())
        destino = self._publicador.publicar(versao.numero, resultado.registros_validos)
        return ResultadoExecucao(carga, versao, destino, processamento.ocorrencias)
