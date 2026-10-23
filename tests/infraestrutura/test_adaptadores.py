from datetime import date

import pytest

from dataflow.dominio.portas import ArquivoInvalidoError
from dataflow.dominio.registro import RegistroOperacional
from dataflow.dominio.valores import ChaveRegistro
from dataflow.infraestrutura.leitor_csv import LeitorCsv
from dataflow.infraestrutura.publicador_diretorio import PublicadorEmDiretorio


def escrever(caminho, texto):

    caminho.write_text(texto, encoding="utf-8")

    return caminho


class TestLeitorCsv:
    def test_le_registros_com_numero_de_linha_a_partir_de_2(self, tmp_path):

        # Arrange

        arquivo = escrever(
            tmp_path / "carga.csv",
            "origem,codigo,data,quantidade\nsap,100,2026-09-10,5\nsap,200,2026-09-11,7\n",
        )

        # Act

        registros = LeitorCsv().ler(arquivo)

        # Assert

        assert [r.linha for r in registros] == [2, 3]

        assert registros[0].chave == ChaveRegistro("SAP", "100", date(2026, 9, 10))

        assert registros[1].valor_de("quantidade") == "7"

    def test_recusa_arquivo_sem_coluna_obrigatoria(self, tmp_path):

        # Arrange

        arquivo = escrever(tmp_path / "carga.csv", "origem,codigo\nsap,100\n")

        # Act / Assert

        with pytest.raises(ArquivoInvalidoError, match="data"):
            LeitorCsv().ler(arquivo)

    def test_recusa_data_em_formato_nao_reconhecido(self, tmp_path):

        # Arrange

        arquivo = escrever(tmp_path / "carga.csv", "origem,codigo,data\nsap,100,10/09/2026\n")

        # Act / Assert

        with pytest.raises(ArquivoInvalidoError, match="Linha 2"):
            LeitorCsv().ler(arquivo)


class TestPublicadorEmDiretorio:
    def test_grava_a_versao_com_nome_numerado_e_somente_os_registros_recebidos(self, tmp_path):

        # Arrange

        registro = RegistroOperacional(
            2,
            ChaveRegistro("SAP", "100", date(2026, 9, 10)),
            {"origem": "SAP", "codigo": "100", "data": "2026-09-10"},
        )

        publicador = PublicadorEmDiretorio(tmp_path / "publicado")

        # Act

        destino = publicador.publicar(7, [registro])

        # Assert

        assert destino.name == "versao_0007.csv"

        linhas = destino.read_text(encoding="utf-8").splitlines()

        assert linhas == ["codigo,data,origem", "100,2026-09-10,SAP"]
