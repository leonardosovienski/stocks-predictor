# Conferência dos arquivos e Markdown — 10/09/2026

Revisão da pasta `C:\STOCKS`, do checkout e dos Markdown versionados, a pedido do
usuário. Base: `bf7b3bc9f888dc94fd186646424159f31682b747`. A inspeção inicial
enumerou 9.968 arquivos/19.092.147.396 bytes fora dos diretórios `.git`, incluindo
1.562 arquivos versionados, 129 Markdown no Git e 37 Markdown locais externos.
Isso é uma população de arquivos, não quantidade de fontes independentes.

## Correções e limpeza

- README, AGENTS, estado atual e HANDOFF passaram a apresentar somente a orientação
  corrente. O diário de 4.483 linhas e as versões completas anteriores continuam
  no [commit original](https://github.com/leonardosovienski/stocks-predictor/tree/bf7b3bc9f888dc94fd186646424159f31682b747),
  sem perda de protocolos ou resultados. Não é necessário duplicar o diário na entrada diária.
- O [índice documental](../../DOCUMENTATION_INDEX.md) agora enumera todos os Markdown
  rastreados, com links clicáveis e classificação. A CI rejeita índice desatualizado,
  arquivo obrigatório ausente, link local novo quebrado e diferença de maiúsculas/minúsculas.
- `requirements.txt` foi removido: declarava apenas PyYAML, omitindo Core e o limite
  superior aprovado. Dependências estão em `pyproject.toml` e `uv.lock`.
- `pytest.ini` foi removido: duplicava a configuração e sobrepunha o bloco pytest
  do `pyproject.toml`. Os padrões explícitos eram os padrões nativos do pytest;
  a configuração canônica mantém `tests/` e o relatório de resultados `-ra`.
- 32 caches Python (365.770 bytes) foram retirados do checkout e arquivados de forma
  reversível em `C:\STOCKS\work\file-review-20260910\cache-quarantine`, com hashes
  conferidos. A revisão automática bloqueou a exclusão definitiva sem motivo específico.
  O recibo de limpeza registra os caminhos e hashes; esses arquivos não são código,
  fonte ou evidência congelada.
  Caches encontrados dentro de pacotes históricos foram preservados.
- O guia `C:\STOCKS\COMECE_AQUI.md` e o README de dados locais passam a apontar para
  R7/R8 e esta navegação, sem tratar os estados R1/R2 como se fossem atuais.

## Referências históricas

A varredura inicial encontrou 402 links locais e 78 destinos sem arquivo diretamente
naquele caminho. Um era o CSV histórico `reports/splits_candidates.csv`, mencionado
no antigo HANDOFF como derivado gitignored com 440 linhas. Não foi localizado no
acervo examinado e não é necessário à operação R8. Não foi criado um arquivo vazio
nem gerada uma suposta cópia original para ocultar a ausência.

As outras 77 ocorrências estão em oito cópias históricas da publicação de 09/09.
Seus links continuam relativos ao local original; os bytes estão lacrados pelo
manifesto de publicação. O [mapa explícito](historical-links.json) conserva documento,
linha, alvo, hash da cópia e localização correspondente no Git. A referência ao
CSV também aparece numa dessas cópias e mantém a classificação de derivado não preservado.
O checker não exclui pastas inteiras: qualquer desvio do conjunto exato falha.

As sete duplas de Markdown idênticos correspondem a relatórios e entregas históricas.
Foram mantidas porque seus caminhos participam de publicações, recibos e reprodução.
Não são cópias de trabalho descartáveis.

## O que precisa permanecer

| Conteúdo | Função / localização |
|---|---|
| `stocks_predictor`, `tests`, `tools`, workflow, configuração e lock | Código executável, controles e reprodução no Git |
| Protocolos, trials, relatórios, sessões e vendor histórico | Evidência e semântica congeladas; vendor não é runtime |
| `C:\STOCKS\data\recovery-r2\objects` | 1.392 objetos recuperados, identificados por hash, incluindo os 12 bancos do catálogo |
| `C:\STOCKS\DADOS_STOCKS.zip` e partes `.001/.002` | Originais da migração; preservados mesmo com redundância física |
| Fontes13/14 e revisão15, arquivos adquiridos e recibos | Proveniência e entradas de cada resultado; não mesclar nem apagar versões |
| `C:\STOCKS\outputs` | Entregas verificadas, incluindo ZIP R8 de 53 membros e manifestos |
| `C:\STOCKS\work` | Pesquisa, tentativas, normalizações, logs, recibos e fontes novas; não apagar em bloco |
| `data/.gitkeep`, `reports/.gitkeep`, `tests/__init__.py` | Estrutura e inicialização; arquivos vazios legítimos |

Arquivos vazios de respostas HTTP e logs sem mensagens também documentam tentativas;
não foram apagados por tamanho. WAL/SHM não são lixo genérico e não entram na limpeza.
Um clone Git contém os componentes de software versionados; não contém todos os
dados externos, documentos de terceiros ou backups locais. A revisão não autoriza
redistribuição indiscriminada de fontes nem certifica completude econômica.

## Conferência reproduzível

```text
python tools/check_project_files.py
python tools/check_project_files.py --write-index
python tools/verify_operational_evidence.py
python tools/audit_registry.py
python research/session-20260910/final_review/verify.py --local
git fsck --full --no-dangling
```

`--write-index` serve para uma alteração deliberada da população de Markdown;
revisar seu diff e commitar. Os demais comandos verificam seu escopo sem instalar
Core neste Windows. Suíte e builds completos seguem a CI Linux 3.13/3.14.
O checker inclui links inline/imagens e referências explícitas, fora de blocos de
código; verifica o caminho versionado, não disponibilidade de URLs externas ou âncoras.

[Recibo local](local-review.json) registra inventário, preservação, limpeza e
qualificações. Os verificadores R3/R6/R7/R8 e do encerramento continuam obrigatórios.
Os ensaios do novo checker incluem arquivo faltante, diferença de caixa, referências,
diretórios, caminhos com espaços e exemplos que não devem virar links.

O mandato econômico permanece aberto: faltam dados de eventos/caixa, custos e
premissas pessoais, além da observação prospectiva. Ter os arquivos de software e
seus hashes corretos não demonstra lucro nem elimina essas lacunas.
