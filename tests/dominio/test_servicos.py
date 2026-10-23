from datetime import date
from pathlib import Path

from dataflow.dominio.registro import RegistroOperacional
from dataflow.dominio.servicos import ValidadorDeArquivo
from dataflow.dominio.valores import ChaveRegistro, PeriodoReferencia

PERIODO = PeriodoReferencia(date(2026, 9, 1), date(2026, 9, 30))


class LeitorFalso:
    """Adaptador falso: devolve registros em memoria, sem arquivo, banco ou servidor."""

    def __init__(self, registros):
        self._registros = registros

    def ler(self, caminho: Path):
        return list(self._registros)


def criar_registro(linha, codigo, dia=date(2026, 9, 10)):
    return RegistroOperacional(linha, ChaveRegistro("SAP", codigo, dia), {"codigo": codigo})


def validar_com(registros):
    validador = ValidadorDeArquivo(LeitorFalso(registros))
    return validador.validar(Path("qualquer.csv"), PERIODO, ["codigo"])


class TestValidadorDeArquivo:
    def test_arquivo_sem_problemas_nao_possui_bloqueio(self):
        # Arrange
        registros = [criar_registro(2, "100"), criar_registro(3, "200")]

        # Act
        resultado = validar_com(registros)

        # Assert
        assert not resultado.possui_bloqueio
        assert resultado.registros_validos == tuple(registros)

    def test_duplicidade_bloqueia_e_exclui_apenas_a_linha_repetida(self):
        # Arrange
        registros = [criar_registro(2, "100"), criar_registro(3, "100")]

        # Act
        resultado = validar_com(registros)

        # Assert
        assert resultado.possui_bloqueio
        assert [r.linha for r in resultado.registros_validos] == [2]

    def test_apenas_alerta_nao_bloqueia_e_mantem_o_registro(self):
        # Arrange
        registros = [criar_registro(2, "100", date(2026, 10, 1))]

        # Act
        resultado = validar_com(registros)

        # Assert
        assert len(resultado.ocorrencias) == 1
        assert not resultado.possui_bloqueio
        assert len(resultado.registros_validos) == 1

    def test_arquivo_vazio_nao_gera_ocorrencias(self):
        # Arrange / Act
        resultado = validar_com([])

        # Assert
        assert resultado.ocorrencias == ()
        assert resultado.registros_validos == ()
