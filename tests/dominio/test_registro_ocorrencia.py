from datetime import date

import pytest

from dataflow.dominio.ocorrencia import OcorrenciaQualidade, Severidade
from dataflow.dominio.registro import RegistroOperacional
from dataflow.dominio.valores import ChaveRegistro


def criar_registro(linha=1, campos=None):
    chave = ChaveRegistro("SAP", "100", date(2026, 9, 1))
    return RegistroOperacional(linha, chave, campos or {})


class TestOcorrenciaQualidade:
    def test_bloqueio_e_bloqueante(self):
        # Arrange / Act
        ocorrencia = OcorrenciaQualidade(2, "codigo", "campo vazio", Severidade.BLOQUEIO)

        # Assert
        assert ocorrencia.bloqueante

    def test_alerta_nao_e_bloqueante(self):
        # Arrange / Act
        ocorrencia = OcorrenciaQualidade(2, "data", "fora do periodo", Severidade.ALERTA)

        # Assert
        assert not ocorrencia.bloqueante

    def test_aceita_primeira_linha_no_valor_limite(self):
        # Arrange / Act
        ocorrencia = OcorrenciaQualidade(1, "codigo", "campo vazio", Severidade.ALERTA)

        # Assert
        assert ocorrencia.linha == 1

    @pytest.mark.parametrize(
        ("linha", "campo", "motivo"),
        [(0, "codigo", "motivo"), (1, " ", "motivo"), (1, "codigo", "")],
    )
    def test_recusa_dados_invalidos(self, linha, campo, motivo):
        # Arrange / Act / Assert
        with pytest.raises(ValueError):
            OcorrenciaQualidade(linha, campo, motivo, Severidade.ALERTA)


class TestRegistroOperacional:
    def test_valor_de_remove_espacos(self):
        # Arrange
        registro = criar_registro(campos={"codigo": "  A1 "})

        # Act / Assert
        assert registro.valor_de("codigo") == "A1"

    def test_campo_ausente_ou_em_branco_e_vazio(self):
        # Arrange
        registro = criar_registro(campos={"codigo": "   "})

        # Act / Assert
        assert registro.campo_vazio("codigo")
        assert registro.campo_vazio("inexistente")

    def test_campo_preenchido_nao_e_vazio(self):
        # Arrange
        registro = criar_registro(campos={"codigo": "A1"})

        # Act / Assert
        assert not registro.campo_vazio("codigo")

    def test_recusa_linha_menor_que_um(self):
        # Arrange / Act / Assert
        with pytest.raises(ValueError, match="linha"):
            criar_registro(linha=0)
