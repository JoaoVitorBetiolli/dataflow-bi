from dataflow.apresentacao.cli import (
    ARQUIVO_OU_ENTRADA_INVALIDA,
    CARGA_BLOQUEADA,
    SUCESSO,
    main,
    proximo_numero_de_versao,
)

CABECALHO = "origem,codigo,data,quantidade\n"


def escrever(tmp_path, linhas, cabecalho=CABECALHO):
    caminho = tmp_path / "carga.csv"
    caminho.write_text(cabecalho + linhas, encoding="utf-8")
    return caminho


def rodar(tmp_path, arquivo, inicio="2026-09-01", fim="2026-09-30"):
    argv = [
        str(arquivo),
        "--fonte",
        "SAP",
        "--inicio",
        inicio,
        "--fim",
        fim,
        "--responsavel",
        "marina",
        "--saida",
        str(tmp_path / "publicado"),
    ]
    return main(argv)


class TestCliPontaAPonta:
    def test_arquivo_valido_publica_a_versao_1(self, tmp_path, capsys):
        # Arrange
        arquivo = escrever(tmp_path, "SAP,100,2026-09-10,5\nSAP,200,2026-09-11,7\n")

        # Act
        codigo = rodar(tmp_path, arquivo)

        # Assert
        assert codigo == SUCESSO
        assert "Versao 1 publicada com 2 registros" in capsys.readouterr().out
        saida = tmp_path / "publicado" / "versao_0001.csv"
        assert len(saida.read_text(encoding="utf-8").splitlines()) == 3

    def test_segundo_envio_gera_a_versao_2(self, tmp_path):
        # Arrange
        arquivo = escrever(tmp_path, "SAP,100,2026-09-10,5\n")
        rodar(tmp_path, arquivo)

        # Act
        rodar(tmp_path, arquivo)

        # Assert
        assert (tmp_path / "publicado" / "versao_0002.csv").exists()

    def test_arquivo_com_duplicidade_e_bloqueado_e_nao_publica(self, tmp_path, capsys):
        # Arrange
        arquivo = escrever(tmp_path, "SAP,100,2026-09-10,5\nSAP,100,2026-09-10,6\n")

        # Act
        codigo = rodar(tmp_path, arquivo)

        # Assert
        assert codigo == CARGA_BLOQUEADA
        assert "[bloqueio] linha 3" in capsys.readouterr().out
        assert not (tmp_path / "publicado").exists()

    def test_arquivo_sem_coluna_obrigatoria_tem_estrutura_invalida(self, tmp_path, capsys):
        # Arrange
        arquivo = escrever(tmp_path, "SAP,100\n", cabecalho="origem,codigo\n")

        # Act
        codigo = rodar(tmp_path, arquivo)

        # Assert
        assert codigo == ARQUIVO_OU_ENTRADA_INVALIDA
        assert "Estrutura invalida" in capsys.readouterr().out

    def test_periodo_com_fim_anterior_ao_inicio_e_recusado(self, tmp_path, capsys):
        # Arrange
        arquivo = escrever(tmp_path, "SAP,100,2026-09-10,5\n")

        # Act
        codigo = rodar(tmp_path, arquivo, inicio="2026-09-30", fim="2026-09-01")

        # Assert
        assert codigo == ARQUIVO_OU_ENTRADA_INVALIDA
        assert "data final" in capsys.readouterr().out


class TestProximoNumeroDeVersao:
    def test_pasta_inexistente_comeca_na_versao_1(self, tmp_path):
        # Arrange / Act / Assert
        assert proximo_numero_de_versao(tmp_path / "nao_existe") == 1

    def test_usa_o_maior_numero_existente_e_nao_a_quantidade_de_arquivos(self, tmp_path):
        # Arrange
        pasta = tmp_path / "publicado"
        pasta.mkdir()
        (pasta / "versao_0002.csv").write_text("x", encoding="utf-8")

        # Act / Assert
        assert proximo_numero_de_versao(pasta) == 3

    def test_pasta_vazia_comeca_na_versao_1(self, tmp_path):
        # Arrange
        pasta = tmp_path / "publicado"
        pasta.mkdir()

        # Act / Assert
        assert proximo_numero_de_versao(pasta) == 1
