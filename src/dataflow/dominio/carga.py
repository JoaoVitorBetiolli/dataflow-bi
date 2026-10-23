"""Carga de dados: agregado que controla o fluxo de validacao, processamento e publicacao."""

from datetime import datetime
from enum import Enum

from dataflow.dominio.processamento import Processamento
from dataflow.dominio.servicos import ResultadoValidacao
from dataflow.dominio.valores import IdentificadorArquivo, PeriodoReferencia
from dataflow.dominio.versao import VersaoPublicada


class StatusCarga(Enum):
    RECEBIDA = "Recebida"
    APTA_A_PROCESSAR = "Apta a processar"
    INVALIDA = "Invalida"
    APTA_A_PUBLICAR = "Apta a publicar"
    PUBLICADA = "Publicada"


class OperacaoInvalidaError(Exception):
    """A operacao nao e permitida no estado atual da carga."""


class CargaDados:
    """Conjunto formado por arquivo, fonte e periodo, que percorre o fluxo ate a publicacao."""

    def __init__(
        self,
        fonte: str,
        periodo: PeriodoReferencia,
        arquivo: IdentificadorArquivo,
        responsavel: str,
    ) -> None:
        if not fonte.strip():
            raise ValueError("A fonte da carga e obrigatoria.")
        if not responsavel.strip():
            raise ValueError("O responsavel pela carga e obrigatorio.")
        self.fonte = fonte.strip().upper()
        self.periodo = periodo
        self.arquivo = arquivo
        self.responsavel = responsavel.strip()
        self._status = StatusCarga.RECEBIDA
        self._processamentos: list[Processamento] = []

    @property
    def status(self) -> StatusCarga:
        return self._status

    @property
    def processamentos(self) -> tuple[Processamento, ...]:
        return tuple(self._processamentos)

    def validar_estrutura(self, estrutura_valida: bool) -> None:
        if self._status is not StatusCarga.RECEBIDA:
            raise OperacaoInvalidaError("So uma carga recebida pode ter a estrutura validada.")
        self._status = StatusCarga.APTA_A_PROCESSAR if estrutura_valida else StatusCarga.INVALIDA

    def processar(self, resultado: ResultadoValidacao) -> Processamento:
        if self._status is not StatusCarga.APTA_A_PROCESSAR:
            raise OperacaoInvalidaError(
                "Carga com estrutura invalida ou ainda nao validada nao pode ser processada."
            )
        processamento = Processamento(len(self._processamentos) + 1, resultado)
        self._processamentos.append(processamento)
        self._status = (
            StatusCarga.INVALIDA if processamento.possui_bloqueio else StatusCarga.APTA_A_PUBLICAR
        )
        return processamento

    def reenviar_arquivo(self, arquivo: IdentificadorArquivo) -> None:
        if self._status is not StatusCarga.INVALIDA:
            raise OperacaoInvalidaError("So uma carga invalida pode receber um arquivo corrigido.")
        self.arquivo = arquivo
        self._status = StatusCarga.RECEBIDA

    def publicar(
        self, numero_versao: int, responsavel: str, publicada_em: datetime
    ) -> VersaoPublicada:
        if self._status is not StatusCarga.APTA_A_PUBLICAR:
            raise OperacaoInvalidaError("Somente uma carga apta a publicar pode ser publicada.")
        ultimo = self._processamentos[-1]
        if ultimo.possui_bloqueio:
            raise OperacaoInvalidaError("Carga com ocorrencia bloqueante nao pode ser publicada.")
        versao = VersaoPublicada(
            numero=numero_versao,
            fonte=self.fonte,
            periodo=self.periodo,
            arquivo=self.arquivo,
            numero_tentativa=ultimo.numero,
            responsavel=responsavel,
            publicada_em=publicada_em,
            total_registros=ultimo.total_validos,
        )
        self._status = StatusCarga.PUBLICADA
        return versao
