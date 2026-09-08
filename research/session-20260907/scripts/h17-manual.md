# Executar a H17

Este pacote executa **um diagnóstico exploratório da H17 com preços históricos**.
Não envia ordens nem usa credenciais. Os dados estão incluídos; não há download
ou instalação de dependências na execução. Requer Python 3.13.

1. Extraia o ZIP inteiro para uma pasta.
2. Abra um terminal nessa pasta e execute:

```powershell
py -3.13 rodar_h17.py
```

O resultado fica em `results/h17-DATA-HORA.json`. Cada execução cria um arquivo
novo; resultados anteriores não são substituídos. Para conferir os arquivos sem
calcular o resultado:

```powershell
py -3.13 rodar_h17.py --verify-only
```

O programa verifica os hashes do pacote antes de calcular. `INCONCLUSIVE_DATA_QUALITY`
é um diagnóstico concluído com dados insuficientes para um veredito econômico;
não é erro de instalação. Uma exceção ou saída diferente de zero indica falha de
execução e deve ser investigada.

## O que está sendo testado

Direção fixa: accruals baixos, `(lucro consolidado − fluxo de caixa operacional) /
ativo total`, quintil inferior de emissores selecionados por liquidez histórica.
Fontes contábeis e vínculos com códigos respeitam a disponibilidade dos documentos
CVM. Os retornos de preço usam abertura posterior ao sinal e ajustes de base
das ações. O protocolo integral está em `protocol.json` e o registro anterior à
observação em `registration.md`.

Os 96 meses de sinais vão de janeiro de 2018 a dezembro de 2025. Os dois primeiros
não atingem o mínimo de 20 empresas com dados contábeis públicos utilizáveis.
O último período de retorno termina na abertura de fevereiro de 2026.

## Conteúdo e limites

`data/quotes.db`: 387.101 cotações de 195 códigos, copiadas sem alterar preços.
`data/snapshots.json`: universo e documentos públicos de cada decisão mensal.
`data/events.json`: eventos, fontes e cruzamentos. `sources/`: respostas originais
dos provedores de eventos, com metadados e hashes. `data/identity/`: ISIN extraído
do COTAHIST e hashes dos arquivos originais. `audit/`: primeira execução, código
anterior e justificativa da correção mecânica. `manifest.json`: lacre dos inputs
e código da execução corrigida.

Os scripts em `preparation-record/` documentam o preparo no workspace original.
Para reconstruir tudo desde os arquivos brutos, são necessários os arquivos
COTAHIST originais e os ZIPs CVM da entrega anterior, que não estão duplicados
neste pacote. Isso não impede repetir offline o diagnóstico com os inputs lacrados.

A comparação só-preço omite dividendos/JCP e não modela negociação de direitos,
entrega efetiva de bonificações, tributação ou execução com R$5–10 mil. As métricas
com observações disponíveis e meses completos sofrem seleção por disponibilidade
futura. Não representam lucro líquido executável. H18/H19 não são executadas
por este pacote: precisam da base histórica de capitalização por classe de ação.
