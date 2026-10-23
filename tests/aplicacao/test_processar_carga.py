from datetime import date, datetime

import pytest

from dataflow.aplicacao.processar_carga import ProcessarEPublicarCarga
from dataflow.dominio.carga import StatusCarga
from dataflow.dominio.portas import ArquivoInvalidoError
from dataflow.dominio.registro import RegistroOperacional
from dataflow.dominio.valores import ChaveRegistro, PeriodoReferencia

PERIODO = PeriodoReferencia(date(2026, 9, 1), date(2026, 9, 30))
AGORA = datetime(2026, 10, 22, 8, 0)


class LeitorFalso:
    def __init__(self, registros=None, erro=None):
        self._registros = registros or []
        self._erro = erro

    def ler(self, caminho):
        if self._erro:
            raise self._erro
        return list(self._registros)


class PublicadorFalso:
    def __init__(self):
        self.chamadas = []

    def publicar(self, numero_versao, registros):
        self.chamadas.append((numero_versao, tuple(registros)))
        return f"versao_{numero_versao}"


def criar_registro(linha, codigo, dia=date(2026, 9, 10), quantidade="1"):
    campos = {"codigo": codigo, "quantidade": quantidade}
    return RegistroOperacional(linha, ChaveRegistro("SAP", codigo, dia), campos)


def criar_arquivo(tmp_path, nome="carga.csv"):
    caminho = tmp_path / nome
    caminho.write_text("conteudo", encoding="utf-8")
    return caminho


def executar(tmp_path, leitor, nome="carga.csv"):
    publicador = PublicadorFalso()
    caso = ProcessarEPublicarCarga(leitor, publicador, relogio=lambda: AGORA)
    resultado = caso.executar(criar_arquivo(tmp_path, nome), "sap", PERIODO, "rafael", 3)
    return resultado, publicador


class TestProcessarEPublicarCarga:
    def test_carga_sem_bloqueio_e_publicada_com_os_registros_validos(self, tmp_path):
        # Arrange
        leitor = LeitorFalso([criar_registro(2, "100"), criar_registro(3, "200")])

        # Act
        resultado, publicador = executar(tmp_path, leitor)

        # Assert
        assert resultado.publicada
        assert resultado.versao.numero == 3
        assert resultado.versao.total_registros == 2
        assert resultado.versao.publicada_em == AGORA
        assert resultado.carga.status is StatusCarga.PUBLICADA
        assert len(publicador.chamadas) == 1

    def test_carga_com_bloqueio_nao_e_publicada(self, tmp_path):
        # Arrange
        leitor = LeitorFalso([criar_registro(2, "100"), criar_registro(3, "100")])

        # Act
        resultado, publicador = executar(tmp_path, leitor)

        # Assert
        assert not resultado.publicada
        assert resultado.carga.status is StatusCarga.INVALIDA
        assert any(o.bloqueante for o in resultado.ocorrencias)
        assert publicador.chamadas == []

    def test_apenas_alerta_nao_impede_a_publicacao(self, tmp_path):
        # Arrange
        leitor = LeitorFalso([criar_registro(2, "100", date(2026, 10, 1))])

        # Act
        resultado, publicador = executar(tmp_path, leitor)

        # Assert
        assert resultado.publicada
        assert len(resultado.ocorrencias) == 1
        assert len(publicador.chamadas) == 1

    def test_estrutura_invalida_nao_processa_nem_publica(self, tmp_path):
        # Arrange
        leitor = LeitorFalso(erro=ArquivoInvalidoError("Colunas obrigatorias ausentes: data."))

        # Act
        resultado, publicador = executar(tmp_path, leitor)

        # Assert
        assert not resultado.publicada
        assert "data" in resultado.erro_estrutura
        assert resultado.carga.status is StatusCarga.INVALIDA
        assert resultado.carga.processamentos == ()
        assert publicador.chamadas == []

    def test_recusa_arquivo_com_formato_diferente_de_csv_e_xlsx(self, tmp_path):
        # Arrange / Act / Assert
        with pytest.raises(ValueError, match="Formatos aceitos"):
            executar(tmp_path, LeitorFalso(), nome="carga.json")
