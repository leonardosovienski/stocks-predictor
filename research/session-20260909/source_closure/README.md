# Reprodução da atualização de fontes H21

Este auxiliar verifica a nova fonte B3; não executa backtest nem negociações.
Resultado e fontes: [relatório](../../../docs/research/2026-09-09-h21-source-closure.md).
Executado no Python 3.12.14 já fornecido pelo ambiente, com stdlib e o parser
`stocks_predictor.cotahist` do checkout. Não exige instalar Core ou dependências.

No Windows, manter todos os argumentos dentro de `C:\STOCKS`. Exemplo no PowerShell,
usando uma variável `$stocksPython` que aponte para o Python auxiliar já instalado:

```powershell
& $stocksPython -B C:\STOCKS\stocks-predictor\research\session-20260909\source_closure\reconcile_quotes.py C:\STOCKS\work\h21-source-closure-20260909\raw\COTAHIST_A2026.complete.ZIP C:\STOCKS\work\h21\inputs C:\STOCKS\work\h21-source-closure-20260909\calendar-2026.json C:\STOCKS\work\h21-source-closure-20260909\reproduction
```

O destino deve ser novo. A rodada de 09/09 já consumiu suas duas revisões de
normalização; este comando é instrução de reprodução posterior, não uma terceira
rodada já autorizada ou executada. Recibos e calendário ficam junto das fontes.
Nenhum download é feito pelo auxiliar.

Verifica hash da fonte e dos dois arquivos H21 preservados, CRC na leitura integral,
identidade/ISIN, moeda, fator, OHLC, volume, duplicatas, calendário de 2026 e
sobreposição em campos e linhas originais. Revisões detectadas são reportadas e
isoladas na nova série; não são aplicadas ao livro congelado.
A série combinada conserva hashes da base anterior e declara que seu calendário
anterior a 2026 não foi recertificado. Dados adquiridos em 09/09 não são sinal
conhecido em datas passadas. Eventos permanecem não certificados.

Saída esperada: 171 cotações de 2026, 109 adicionais, 62 idênticas na sobreposição
e 2.159 combinadas; nenhum retorno calculado. Validação negativa local e comparação
das revisões estão em `work\h21-source-closure-20260909\local-validation.json`.
Fontes brutas não foram incorporadas ao pacote de produção ou republicadas no Git.
