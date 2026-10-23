from dataclasses import FrozenInstanceError
from datetime import date, datetime

import pytest

from dataflow.dominio.carga import CargaDados, OperacaoInvalidaError, StatusCarga
from dataflow.dominio.ocorrencia import OcorrenciaQualidade, Severidade
from dataflow.dominio.registro import RegistroOperacional
from dataflow.dominio.servicos import ResultadoValidacao
from dataflow.dominio.valores import ChaveRegistro, IdentificadorArquivo, PeriodoReferencia

PERIODO = PeriodoReferencia(date(2026, 9, 1), date(2026, 9, 30))
AGORA = datetime(2026, 10, 22, 8, 0)


def criar_carga():
    return CargaDados("sap", PERIODO, IdentificadorArquivo("carga.csv", "hash1"), "marina")


def criar_registro(linha=2):
    chave = ChaveRegistro("SAP", str(linha), date(2026, 9, 10))
    return RegistroOperacional(linha, chave, {})


def resultado_valido():
    return ResultadoValidacao((criar_registro(2), criar_registro(3)), ())


def resultado_com_bloqueio():
    bloqueio = OcorrenciaQualidade(3, "chave", "registro duplicado", Severidade.BLOQUEIO)
    return ResultadoValidacao((criar_registro(2), criar_registro(3)), (bloqueio,))


def criar_carga_apta_a_processar():
    carga = criar_carga()
    carga.validar_estrutura(True)
    return carga


class TestEstadoInicialEEstrutura:
    def test_carga_nova_nasce_recebida_e_normaliza_a_fonte(self):
        # Arrange / Act
        carga = criar_carga()

        # Assert
        assert carga.status is StatusCarga.RECEBIDA
        assert carga.fonte == "SAP"

    def test_estrutura_valida_deixa_a_carga_apta_a_processar(self):
        # Arrange
        carga = criar_carga()

        # Act
        carga.validar_estrutura(True)

        # Assert
        assert carga.status is StatusCarga.APTA_A_PROCESSAR

    def test_estrutura_invalida_deixa_a_carga_invalida(self):
        # Arrange
        carga = criar_carga()

        # Act
        carga.validar_estrutura(False)

        # Assert
        assert carga.status is StatusCarga.INVALIDA

    def test_recusa_fonte_e_responsavel_vazios(self):
        # Arrange / Act / Assert
        arquivo = IdentificadorArquivo("carga.csv", "hash1")
        with pytest.raises(ValueError, match="fonte"):
            CargaDados(" ", PERIODO, arquivo, "marina")
        with pytest.raises(ValueError, match="responsavel"):
            CargaDados("SAP", PERIODO, arquivo, "")


class TestRegraCargaInvalidaNaoPodeSerProcessada:
    def test_nao_processa_carga_ainda_nao_validada(self):
        # Arrange
        carga = criar_carga()

        # Act / Assert
        with pytest.raises(OperacaoInvalidaError, match="nao pode ser processada"):
            carga.processar(resultado_valido())

    def test_nao_processa_carga_com_estrutura_invalida(self):
        # Arrange
        carga = criar_carga()
        carga.validar_estrutura(False)

        # Act / Assert
        with pytest.raises(OperacaoInvalidaError, match="nao pode ser processada"):
            carga.processar(resultado_valido())

    def test_processamento_sem_bloqueio_deixa_a_carga_apta_a_publicar(self):
        # Arrange
        carga = criar_carga_apta_a_processar()

        # Act
        processamento = carga.processar(resultado_valido())

        # Assert
        assert processamento.numero == 1
        assert carga.status is StatusCarga.APTA_A_PUBLICAR


class TestRegraBloqueioImpedePublicacao:
    def test_processamento_com_bloqueio_deixa_a_carga_invalida(self):
        # Arrange
        carga = criar_carga_apta_a_processar()

        # Act
        carga.processar(resultado_com_bloqueio())

        # Assert
        assert carga.status is StatusCarga.INVALIDA

    def test_carga_com_bloqueio_nao_pode_ser_publicada(self):
        # Arrange
        carga = criar_carga_apta_a_processar()
        carga.processar(resultado_com_bloqueio())

        # Act / Assert
        with pytest.raises(OperacaoInvalidaError, match="apta a publicar"):
            carga.publicar(1, "rafael", AGORA)

    def test_reenvio_preserva_a_tentativa_anterior_e_cria_nova_tentativa(self):
        # Arrange
        carga = criar_carga_apta_a_processar()
        carga.processar(resultado_com_bloqueio())

        # Act
        carga.reenviar_arquivo(IdentificadorArquivo("corrigido.csv", "hash2"))
        carga.validar_estrutura(True)
        carga.processar(resultado_valido())

        # Assert
        assert [p.numero for p in carga.processamentos] == [1, 2]
        assert carga.processamentos[0].possui_bloqueio
        assert carga.status is StatusCarga.APTA_A_PUBLICAR

    def test_so_carga_invalida_aceita_arquivo_corrigido(self):
        # Arrange
        carga = criar_carga()

        # Act / Assert
        with pytest.raises(OperacaoInvalidaError, match="invalida"):
            carga.reenviar_arquivo(IdentificadorArquivo("corrigido.csv", "hash2"))


class TestRegraVersaoPublicadaPreservaOrigemEEImutavel:
    def test_publicar_gera_versao_ligada_a_carga_e_a_tentativa(self):
        # Arrange
        carga = criar_carga_apta_a_processar()
        carga.processar(resultado_valido())

        # Act
        versao = carga.publicar(5, "rafael", AGORA)

        # Assert
        assert versao.numero == 5
        assert versao.responsavel == "rafael"
        assert versao.numero_tentativa == 1
        assert versao.total_registros == 2
        assert versao.arquivo.hash_arquivo == "hash1"
        assert carga.status is StatusCarga.PUBLICADA

    def test_total_de_registros_exclui_linhas_bloqueadas_da_ultima_tentativa(self):
        # Arrange
        carga = criar_carga_apta_a_processar()
        carga.processar(resultado_com_bloqueio())
        carga.reenviar_arquivo(IdentificadorArquivo("corrigido.csv", "hash2"))
        carga.validar_estrutura(True)
        carga.processar(ResultadoValidacao((criar_registro(2),), ()))

        # Act
        versao = carga.publicar(1, "rafael", AGORA)

        # Assert
        assert versao.numero_tentativa == 2
        assert versao.total_registros == 1

    def test_versao_publicada_nao_pode_ser_alterada(self):
        # Arrange
        carga = criar_carga_apta_a_processar()
        carga.processar(resultado_valido())
        versao = carga.publicar(1, "rafael", AGORA)

        # Act / Assert
        with pytest.raises(FrozenInstanceError):
            versao.numero = 99

    def test_carga_ja_publicada_nao_pode_ser_publicada_de_novo(self):
        # Arrange
        carga = criar_carga_apta_a_processar()
        carga.processar(resultado_valido())
        carga.publicar(1, "rafael", AGORA)

        # Act / Assert
        with pytest.raises(OperacaoInvalidaError):
            carga.publicar(2, "rafael", AGORA)

    @pytest.mark.parametrize(
        ("numero", "responsavel"),
        [(0, "rafael"), (1, "  ")],
    )
    def test_versao_recusa_numero_ou_responsavel_invalidos(self, numero, responsavel):
        # Arrange
        carga = criar_carga_apta_a_processar()
        carga.processar(resultado_valido())

        # Act / Assert
        with pytest.raises(ValueError):
            carga.publicar(numero, responsavel, AGORA)
