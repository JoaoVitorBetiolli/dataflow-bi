from datetime import date

from dataflow.dominio.ocorrencia import Severidade
from dataflow.dominio.qualidade import validar_registros
from dataflow.dominio.registro import RegistroOperacional
from dataflow.dominio.valores import ChaveRegistro, PeriodoReferencia

PERIODO = PeriodoReferencia(date(2026, 9, 1), date(2026, 9, 30))
OBRIGATORIOS = ["codigo"]


def criar_registro(linha, codigo="100", dia=date(2026, 9, 10), campos=None):
    campos = {"codigo": codigo} if campos is None else campos
    return RegistroOperacional(linha, ChaveRegistro("SAP", codigo, dia), campos)


def validar(registros):
    return validar_registros(registros, PERIODO, OBRIGATORIOS)


class TestValidarRegistros:
    def test_registros_validos_nao_geram_ocorrencias(self):
        # Arrange
        registros = [criar_registro(1, "100"), criar_registro(2, "200")]

        # Act
        ocorrencias = validar(registros)

        # Assert
        assert ocorrencias == []

    def test_campo_obrigatorio_vazio_gera_bloqueio_com_linha_e_campo(self):
        # Arrange
        registros = [criar_registro(1), criar_registro(2, "200", campos={"codigo": "  "})]

        # Act
        ocorrencias = validar(registros)

        # Assert
        assert len(ocorrencias) == 1
        assert ocorrencias[0].linha == 2
        assert ocorrencias[0].campo == "codigo"
        assert ocorrencias[0].severidade is Severidade.BLOQUEIO

    def test_chave_repetida_gera_bloqueio_apontando_a_linha_original(self):
        # Arrange
        registros = [criar_registro(1, "100"), criar_registro(2, "100")]

        # Act
        ocorrencias = validar(registros)

        # Assert
        assert len(ocorrencias) == 1
        assert ocorrencias[0].linha == 2
        assert "linha 1" in ocorrencias[0].motivo
        assert ocorrencias[0].bloqueante

    def test_mesmo_codigo_em_datas_diferentes_nao_e_duplicidade(self):
        # Arrange
        registros = [
            criar_registro(1, "100", date(2026, 9, 10)),
            criar_registro(2, "100", date(2026, 9, 11)),
        ]

        # Act / Assert
        assert validar(registros) == []

    def test_data_fora_do_periodo_gera_alerta_e_nao_bloqueio(self):
        # Arrange
        registros = [criar_registro(1, "100", date(2026, 10, 1))]

        # Act
        ocorrencias = validar(registros)

        # Assert
        assert len(ocorrencias) == 1
        assert ocorrencias[0].severidade is Severidade.ALERTA
        assert not ocorrencias[0].bloqueante

    def test_datas_nos_limites_do_periodo_sao_aceitas(self):
        # Arrange
        registros = [
            criar_registro(1, "100", date(2026, 9, 1)),
            criar_registro(2, "200", date(2026, 9, 30)),
        ]

        # Act / Assert
        assert validar(registros) == []

    def test_varios_problemas_no_mesmo_lote_sao_todos_registrados(self):
        # Arrange
        registros = [
            criar_registro(1, "100"),
            criar_registro(2, "100"),
            criar_registro(3, "300", date(2026, 8, 31)),
        ]

        # Act
        ocorrencias = validar(registros)

        # Assert
        assert sorted((o.linha, o.campo) for o in ocorrencias) == [(2, "chave"), (3, "data")]
