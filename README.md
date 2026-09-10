# Stocks Predictor

Pesquisa histórica e infraestrutura de simulação de ações da B3. A infraestrutura
para pesquisa em lote está validada em um host com disco local. **Lucro líquido
pessoal executável ou futuro ainda não foi validado.**

Comece pelo [estado atual](STOCKS_CURRENT_STATE.md), pelo [HANDOFF](HANDOFF.md) e
pelo [índice completo dos Markdown](docs/DOCUMENTATION_INDEX.md). O
[mandato integral](docs/continuation/PROMPT_AUDITORIA_INTEGRAL_20260909.md) define
o objetivo econômico e as regras de evidência.

## Uso disponível

`python -m stocks_predictor` oferece diagnóstico, inicialização de banco gerido,
ingestão COTAHIST por hash, inspeção por versão, backup e restauração em destino
novo, perfil econômico e conferência de observações datadas. No checkout,
`python main.py ops` usa a mesma entrada. Os exemplos e limites estão no
[runbook R8](docs/engineering/2026-09-10-r8/RUNBOOK.md).

Os bancos históricos são separados do banco gerido. O fluxo não combina versões
silenciosamente, não ajusta eventos corporativos automaticamente e não habilita capital.

## Ambiente e validação

- Runtime: Python `>=3.13,<3.15`, PyYAML `>=6,<7`, predictor-core `>=3.2,<4`.
- Dependências e configuração: [pyproject.toml](pyproject.toml); versões e hashes:
  [uv.lock](uv.lock). Não há um segundo arquivo de dependências ou configuração pytest.
- Produção/testes: Linux CI com Python 3.13 e 3.14. Neste Windows, somente auxiliares
  stdlib compatíveis; não criar venv, instalar Core/dependências ou alterar o EDR.
- [CI](.github/workflows/ci.yml): testes ativos e históricos, tipos, lint,
  cobertura mínima 77%, integridade, builds idênticos, wheel fora do checkout
  e scanner da árvore completa com controle sintético.

O [encerramento integrado pelo PR81](docs/continuation/2026-09-10-closure/README.md)
registra a implementação R8, sua entrega e seus limites. A
[CI232](https://github.com/leonardosovienski/stocks-predictor/actions/runs/34530909816)
do commit `bf7b3bc` aprovou 891 testes ativos, 17 históricos e 63 subtests por
versão de Python. Contagens datadas não certificam automaticamente commits posteriores.

## Dados e resultado econômico

R$5.000 é o capital confirmado. Custos pessoais, prazo e cenário fiscal permanecem
incompletos. O [consolidado R7](docs/audit/2026-09-10-r7/CONSOLIDADO.md) registra
75 itens e as dependências restantes: 50 valores líquidos, 22 datas e 28 registros
societários, com sobreposição entre grupos. H22 foi rejeitada no escopo avaliado;
H21 conserva resultado histórico condicional, sem lucro pessoal/futuro certificado.

Bancos/fontes estão em `C:\STOCKS\data` e `C:\STOCKS\work`; entregas em
`C:\STOCKS\outputs`. Um clone Git não substitui esses dados externos. Consulte
[a revisão dos arquivos](docs/maintenance/2026-09-10-files/README.md) para saber
o que foi preservado, removido e verificado. Integridade de arquivo não é
completude econômica ou certificação de disponibilidade histórica.

## Histórico e continuidade

Protocolos e resultados H1–H20/H21, relatórios negativos, fontes e o snapshot
`vendor/predictor_core` permanecem preservados. O vendor não é dependência do runtime.
O [README anterior completo](https://github.com/leonardosovienski/stocks-predictor/blob/bf7b3bc9f888dc94fd186646424159f31682b747/README.md)
continua no histórico Git. Comandos e alegações antigos devem ser lidos com a data
original; as instruções atuais ficam em [AGENTS.md](AGENTS.md).
