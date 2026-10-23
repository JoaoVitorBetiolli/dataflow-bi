from datetime import date

import pytest

from dataflow.dominio.valores import ChaveRegistro, IdentificadorArquivo, PeriodoReferencia


class TestPeriodoReferencia:
    def test_aceita_periodo_com_fim_posterior_ao_inicio(self):
        # Arrange
        inicio, fim = date(2026, 9, 1), date(2026, 9, 30)

        # Act
        periodo = PeriodoReferencia(inicio, fim)

        # Assert
        assert periodo.inicio == inicio
        assert periodo.fim == fim

    def test_aceita_periodo_de_um_unico_dia_no_valor_limite(self):
        # Arrange
        dia = date(2026, 9, 17)

        # Act
        periodo = PeriodoReferencia(dia, dia)

        # Assert
        assert periodo.contem(dia)

    def test_recusa_fim_anterior_ao_inicio(self):
        # Arrange
        inicio, fim = date(2026, 9, 30), date(2026, 9, 1)

        # Act / Assert
        with pytest.raises(ValueError, match="data final"):
            PeriodoReferencia(inicio, fim)

    def test_contem_datas_nos_limites_do_periodo(self):
        # Arrange
        periodo = PeriodoReferencia(date(2026, 9, 1), date(2026, 9, 30))

        # Act / Assert
        assert periodo.contem(date(2026, 9, 1))
        assert periodo.contem(date(2026, 9, 30))

    def test_nao_contem_data_fora_do_periodo(self):
        # Arrange
        periodo = PeriodoReferencia(date(2026, 9, 1), date(2026, 9, 30))

        # Act / Assert
        assert not periodo.contem(date(2026, 8, 31))
        assert not periodo.contem(date(2026, 10, 1))


class TestChaveRegistro:
    def test_normaliza_origem_e_codigo(self):
        # Arrange / Act
        chave = ChaveRegistro("  sap ", " 123 ", date(2026, 9, 1))

        # Assert
        assert chave.origem == "SAP"
        assert chave.codigo == "123"

    def test_chaves_com_mesmos_valores_sao_iguais(self):
        # Arrange
        a = ChaveRegistro("SAP", "123", date(2026, 9, 1))
        b = ChaveRegistro("sap", "123", date(2026, 9, 1))

        # Act / Assert
        assert a == b
        assert hash(a) == hash(b)

    def test_chaves_com_codigo_diferente_sao_diferentes(self):
        # Arrange
        a = ChaveRegistro("SAP", "123", date(2026, 9, 1))
        b = ChaveRegistro("SAP", "124", date(2026, 9, 1))

        # Act / Assert
        assert a != b

    @pytest.mark.parametrize(
        ("origem", "codigo", "mensagem"),
        [("", "123", "origem"), ("   ", "123", "origem"), ("SAP", "", "codigo")],
    )
    def test_recusa_campos_obrigatorios_vazios(self, origem, codigo, mensagem):
        # Arrange / Act / Assert
        with pytest.raises(ValueError, match=mensagem):
            ChaveRegistro(origem, codigo, date(2026, 9, 1))


class TestIdentificadorArquivo:
    @pytest.mark.parametrize("nome", ["carga.csv", "carga.xlsx", "CARGA.CSV"])
    def test_aceita_formatos_csv_e_xlsx(self, nome):
        # Arrange / Act
        arquivo = IdentificadorArquivo(nome, "abc123")

        # Assert
        assert arquivo.nome == nome

    def test_recusa_formato_diferente_de_csv_e_xlsx(self):
        # Arrange / Act / Assert
        with pytest.raises(ValueError, match="Formatos aceitos"):
            IdentificadorArquivo("carga.json", "abc123")

    def test_recusa_hash_vazio(self):
        # Arrange / Act / Assert
        with pytest.raises(ValueError, match="hash"):
            IdentificadorArquivo("carga.csv", "  ")

    def test_recusa_nome_vazio(self):
        # Arrange / Act / Assert
        with pytest.raises(ValueError, match="nome"):
            IdentificadorArquivo("", "abc123")
