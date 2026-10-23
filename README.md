# DataFlow BI

![CI](https://github.com/JoaoVitorBetiolli/dataflow-bi/actions/workflows/ci.yml/badge.svg)

Tratamento e publicação rastreável de cargas operacionais (arquivos de extração do SAP e do TMS) para alimentar os painéis de Power BI. Projeto do Checkpoint 2 de Engenharia de Software (FIAP), continuação do Checkpoint 1.

## O que o MVP faz

Recebe um arquivo CSV com a fonte e o período de referência e executa o fluxo principal:

1. valida a estrutura do arquivo (colunas obrigatórias, formato das datas e extensão);
2. aplica as regras de qualidade: campos obrigatórios, duplicidade pela chave de registro e data dentro do período;
3. registra cada ocorrência com linha, campo, motivo e severidade (alerta ou bloqueio);
4. bloqueia a publicação quando há ocorrência bloqueante;
5. sem bloqueio, publica uma versão numerada apenas com os registros válidos.

Histórias do Checkpoint 1 implementadas: **US-03** (validação da estrutura), **US-05** (duplicidades e ocorrências), **US-07** (publicação da versão), além do reenvio com preservação das tentativas (**US-06**, no domínio).

## Requisitos

- Python 3.10 ou superior
- Git

## Como rodar (máquina limpa)

```
git clone https://github.com/JoaoVitorBetiolli/dataflow-bi.git
cd dataflow-bi
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux ou macOS
pip install -e ".[dev]"
```

Publicar uma carga válida (dados fictícios em `exemplos/`):

```
python -m dataflow exemplos/carga_valida.csv --fonte SAP --inicio 2026-09-01 --fim 2026-09-30 --responsavel marina
```

Saída esperada: `Versao 1 publicada com 3 registros: publicado/versao_0001.csv`.

Carga com problemas (duplicidade, campo vazio e data fora do período):

```
python -m dataflow exemplos/carga_com_erros.csv --fonte SAP --inicio 2026-09-01 --fim 2026-09-30 --responsavel marina
```

Códigos de saída: `0` publicada, `1` carga bloqueada, `2` arquivo ou parâmetros inválidos.

Formato do CSV: colunas obrigatórias `origem`, `codigo` e `data` (AAAA-MM-DD); as demais colunas são preservadas. Os campos `codigo` e `quantidade` são obrigatórios por padrão (opção `--obrigatorios`).

## Testes

```
pytest
```

Com relatório de cobertura:

```
pytest --cov=dataflow --cov-report=term-missing
```

## Lint e formatação

O projeto usa [ruff](https://docs.astral.sh/ruff/), configurado no `pyproject.toml`.

```
ruff check .
ruff format --check .
```

Para corrigir a formatação automaticamente: `ruff format .`

## Padrões do projeto

- **Arquivos e funções:** `snake_case`, com verbo na função (`validar_registros`, `proximo_numero_de_versao`).
- **Classes:** `PascalCase`, com os nomes do glossário do Checkpoint 1 (`CargaDados`, `VersaoPublicada`, `OcorrenciaQualidade`).
- **Constantes:** `MAIUSCULAS`. Identificadores em português, sem acentos.
- **Testes:** nome descritivo do comportamento (`test_carga_com_bloqueio_nao_e_publicada`), padrão Arrange-Act-Assert e um arquivo por módulo.
- **Branches:** `tipo/descricao-curta`, como `feat/portas-e-adaptadores` ou `docs/readme`.
- **Commits:** [Conventional Commits](https://www.conventionalcommits.org/), no formato `tipo(escopo): descrição`, com os tipos `feat`, `fix`, `refactor`, `test`, `docs` e `chore`.
- **Integração:** a `main` é protegida. Todo código entra por Pull Request com ao menos 1 aprovação de outro integrante e a CI verde.

## Arquitetura (hexagonal)

| Camada | Pasta | Responsabilidade |
|---|---|---|
| Domínio | `src/dataflow/dominio` | Entidades, value objects, regras de negócio e portas (interfaces). Não importa framework nem infraestrutura. |
| Aplicação | `src/dataflow/aplicacao` | Casos de uso que orquestram o domínio. |
| Infraestrutura | `src/dataflow/infraestrutura` | Adaptadores das portas: leitor CSV e publicador em diretório. |
| Apresentação | `src/dataflow/apresentacao` | Interface de linha de comando. |

As dependências apontam sempre para o domínio. As portas `LeitorArquivo` e `PublicadorBI` ficam no domínio e são implementadas pelos adaptadores, injetados pelo construtor.

Padrão de projeto aplicado por refatoração: **Strategy** nas regras de qualidade (`src/dataflow/dominio/qualidade.py`).

## Dívida técnica

Os itens assumidos conscientemente estão em [DEBT.md](DEBT.md).

## Equipe

João Vitor Betiolli, João Victor Caitano Tabuso, João Pedro Tomas Dominguito, Luiz Gustavo Lima da Silva e Vicente Casellato Rodriguez.