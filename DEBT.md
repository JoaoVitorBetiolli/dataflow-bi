# Registro de dívida técnica

Itens assumidos conscientemente durante o Checkpoint 2. Prioridade: **Alta**, **Média** ou **Baixa**.

## D-01 — Leitor aborta o arquivo inteiro na primeira linha inválida

- **O que é:** uma data ou chave inválida em uma linha faz o leitor recusar o arquivo todo, em vez de registrar uma ocorrência só para aquele registro (critério da US-04).
- **Onde está:** `src/dataflow/infraestrutura/leitor_csv.py`, método `_converter`.
- **Por que foi assumido:** priorizamos a validação de estrutura (US-03) e a publicação (US-07) no prazo do checkpoint.
- **Impacto:** o analista descobre um problema de formato por vez, a cada reenvio.
- **Prioridade:** Média.
- **Custo de conviver:** cada ciclo de correção custa um reenvio completo; cresce com o tamanho do arquivo.

## D-02 — Atributos públicos e mutáveis na `CargaDados`

- **O que é:** `fonte`, `periodo` e `arquivo` podem ser alterados de fora da classe, o que permite burlar as regras de estado.
- **Onde está:** `src/dataflow/dominio/carga.py`, método `__init__`.
- **Por que foi assumido:** simplicidade no primeiro incremento; hoje só um caso de uso usa a classe.
- **Impacto:** código futuro poderia trocar o arquivo sem passar por `reenviar_arquivo`.
- **Prioridade:** Média.
- **Custo de conviver:** baixo hoje, mas aumenta a cada novo chamador. A correção é transformar os atributos em propriedades somente leitura.

## D-03 — Severidade de data fora do período definida sem validação do negócio

- **O que é:** registro com data fora do período de referência gera apenas alerta; o Checkpoint 1 não define se deveria bloquear.
- **Onde está:** `src/dataflow/dominio/qualidade.py`, regra `DentroDoPeriodo`.
- **Por que foi assumido:** escolhemos a opção menos restritiva para não travar cargas por uma regra ainda não confirmada.
- **Impacto:** registros fora do período podem chegar ao Power BI.
- **Prioridade:** Média.
- **Custo de conviver:** risco de número indevido em um indicador; a troca é de uma linha (`Severidade.BLOQUEIO`).

## D-04 — Sem autenticação nem perfis de acesso

- **O que é:** a US-01 não foi implementada; o responsável é informado como texto livre na linha de comando.
- **Onde está:** ausente; `--responsavel` em `src/dataflow/apresentacao/cli.py`.
- **Por que foi assumido:** o checkpoint pede 3 histórias Must have bem testadas, e autenticação exigiria banco de usuários.
- **Impacto:** não há controle de quem publica, e os requisitos RNF-03 e RNF-04 não são atendidos.
- **Prioridade:** Alta.
- **Custo de conviver:** inviável para uso real; qualquer pessoa pode se passar por outra na trilha de auditoria.

## D-05 — Sem persistência de cargas e sem histórico consultável

- **O que é:** só as versões publicadas são gravadas (arquivos CSV); cargas, tentativas e ocorrências existem apenas em memória durante a execução (US-08 e RF-12 não implementadas).
- **Onde está:** `src/dataflow/infraestrutura/publicador_diretorio.py` e ausência de um repositório de cargas.
- **Por que foi assumido:** banco de dados está fora do escopo do checkpoint.
- **Impacto:** a rastreabilidade do RNF-06 fica incompleta e não é possível reconstruir a origem de uma versão antiga.
- **Prioridade:** Alta.
- **Custo de conviver:** alto para auditoria; a arquitetura hexagonal já permite acrescentar um repositório sem mexer no domínio.

## D-06 — Formato `.xlsx` aceito na extensão, mas sem leitor

- **O que é:** `IdentificadorArquivo` aceita `.csv` e `.xlsx`, mas só existe o `LeitorCsv`.
- **Onde está:** `src/dataflow/dominio/valores.py` (`EXTENSOES_ACEITAS`) e `src/dataflow/infraestrutura/leitor_csv.py`.
- **Por que foi assumido:** a extensão segue o Checkpoint 1; o leitor de XLSX exigiria uma biblioteca extra.
- **Impacto:** um `.xlsx` passa pela checagem de extensão e falha na leitura com uma mensagem pouco clara.
- **Prioridade:** Média.
- **Custo de conviver:** confusão para o usuário; resolve-se com um novo adaptador da porta `LeitorArquivo`.

## D-07 — CI testa apenas o Python 3.12

- **O que é:** o `pyproject.toml` aceita Python 3.10 ou superior, mas a CI roda em uma única versão.
- **Onde está:** `.github/workflows/ci.yml`, passo `setup-python`.
- **Por que foi assumido:** manter o pipeline simples e rápido (abaixo de 5 minutos).
- **Impacto:** uma incompatibilidade com 3.10 ou 3.11 passaria despercebida.
- **Prioridade:** Baixa.
- **Custo de conviver:** baixo; uma matriz de versões resolve com poucas linhas.