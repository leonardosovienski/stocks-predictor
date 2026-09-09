# H21 — atualização de fontes e condições operacionais

Rodada documental de 09/09/2026, pré-registrada em
[protocolo próprio](2026-09-09-h21-source-closure-protocol.json).
A série de preços foi atualizada e conferida. Custos e eventos ganharam fontes
identificadas, condições de aplicação e lacunas explícitas. **A cobertura histórica
de eventos e o custo líquido integral continuam incompletos.**
Não houve nova hipótese, variante econômica, cálculo de retorno ou operação.

## O que ficou resolvido

| Item | Resultado e limite |
|---|---|
| Cotações recentes | 171 pregões de 2026 até 08/09; 109 novos, formando 2.159 registros desde 2018 |
| Sobreposição | 62 pregões idênticos nos campos extraídos e nas linhas originais |
| Calendário | Nenhum dia faltante/inesperado em 2026; quarta-feira de cinzas abre parcialmente e 09/07 é pregão |
| Arquivo B3 | ZIP completo com SHA-256 e CRC conferidos; captura truncada anterior rejeitada e preservada |
| Corretora | XP registrada como preferência; Rico comparada como alternativa de custo para ETFs |
| Custos | Tarifas B3, corretagem condicional, adicionais, impostos sobre serviços e custódia separados |
| Eventos | Regulamentos, demonstrações e comunicado de incorporação conferidos, sem transformar permissões ou propostas em eventos executados |

O livro H21 permanece em 02/01/2018–01/04/2026, com 2.050 cotações e lote 10.
A nova série é uma fonte separada: **não estende o resultado histórico**.
O cadastro atual da B3 mostra lote de negociação 1; a data histórica dessa
mudança não foi comprovada. Lote 10 permanece múltiplo válido do lote atual.

O anual de 2026 veio da [B3 COTAHIST](https://bvmf.bmfbovespa.com.br/InstDados/SerHist/COTAHIST_A2026.ZIP),
com fechamento até 08/09. A primeira transferência ficou incompleta apesar do
status de transporte concluído. O restante foi recuperado por intervalo com ETag;
o arquivo montado tem 74.185.998 bytes, SHA-256
`b352157a252a9a31aed1be3a3f55d043785517d652f65ac715892cf2ddaa839a`.
A leitura integral de 2.725.181 registros validou o CRC do membro.
O [calendário oficial](https://www.b3.com.br/pt_br/noticias/calendario-de-negociacao-da-b3-confira-o-funcionamento-da-bolsa-em-2026.htm)
foi comparado também com os dias efetivamente presentes na fonte.
O calendário de 2018–2025 não foi recertificado nesta rodada.

## XP e alternativa

Na [página de custos XP](https://www.xpi.com.br/custos-operacionais/), a seção
de ETF informa 0,04% mais R$276,09 para **criação/destruição de cotas**.
Essa cobrança do mercado primário não foi aplicada à compra comum em bolsa.
A seção “Fundos Listados” mostra corretagem zero no autoatendimento com
condição de cliente independente sem assessor. O enquadramento do BOVA11
e a elegibilidade da conta não ficaram expressamente confirmados;
`secondary_bova11_brokerage_brl` permanece `null`.

A [Rico](https://www.rico.com.vc/custos/) exibe ETFs explicitamente com corretagem
zero em ordens digitais do próprio cliente. Ambas as páginas informam adicional
operacional de 5,9% sobre corretagem, emolumentos e liquidação. A Rico ainda
explicita o gross-up de ISS/PIS/COFINS sobre corretagem e taxas operacionais.
Esses adicionais impedem equiparar corretagem zero a custo total zero.
As abas foram conferidas no navegador porque a extração textual mistura produtos.
Os recibos são observações autorais da interface, sem HTML original preservado;
as tentativas diretas que receberam HTTP403 também foram mantidas.

**Decisão:** manter XP como preferência. Rico pode ser alternativa se a condição
efetiva da XP cobrar corretagem de ETF; os dados não sustentam troca ou superioridade
geral. A Rico pertence ao mesmo grupo XP. Capital real, horizonte, tolerância
de perda, canal e vínculo com assessor não foram informados.
Essas páginas foram observadas em 09/09: não comprovam tarifas conhecidas em
08/09 nem custos vigentes durante todo o livro histórico.

## Componentes de custo verificáveis

A [tabela B3 V5](https://b3.com.br/data/files/5C/A6/C9/20/75F30A105BF9020AAC094EA8/Tarifacao_Equities_V5.0_PT.pdf),
vigente desde 01/09/2026, diferencia mercado contínuo de leilões de abertura
e fechamento. Para operação comum, sem day trade, na primeira faixa de
ADTV mensal do investidor até R$3 milhões:

| Percentual por lado sobre o volume | Contínuo | Leilão de abertura/fechamento |
|---|---:|---:|
| Negociação | 0,00500% | 0,00700% |
| CCP | 0,02240% | 0,02240% |
| Transferência vigente | 0,00260% | 0,00260% |
| Soma apenas B3 | 0,03000% | 0,03200% |

Páginas PDF 9 e 11, conferidas visualmente. A transferência segue mecanismo
anual baseado no mercado; não é outra faixa de ADTV pessoal.
Consolidação, alocação por preço médio/fase e truncamento seguem seção 1.4.
A base dos adicionais da corretora precisa ser reconciliada com a nota efetiva,
inclusive a correspondência entre nomes antigos e CCP/transferência atuais.
Não há cálculo novo de custo total ou substituição dos 18/36 bp congelados.
V4 foi preservada como versão anterior; V5 não foi aplicada retroativamente a 2018.

A custódia B3 usa agregação por investidor no mesmo custodiante e faixas
progressivas. A isenção abaixo de R$26.471,77 não pode ser atribuída ao usuário
sem conhecer seus outros ativos. Custódia própria zero da corretora não resolve
esse dado. O programa de relacionamento varejo com vigência em 08/09 cobre
futuros, sem desconto presumido para BOVA11 à vista.

Taxas internas já descontadas no patrimônio do fundo não devem ser deduzidas
novamente das cotações. Spread, slippage, execução em leilão e condições da
conta continuam desconhecidos. Cotação de abertura não comprova uma execução.

## Eventos: evidência e cobertura

Foram identificados dois cadastros relevantes na B3: fundo 990 e classe 19674.
Consultar só um perde documentos. Consultas anuais devolveram registros que
consultas de vários anos omitiram silenciosamente; respostas vazias dessas
consultas amplas foram rejeitadas como prova de ausência.
A lista atual de eventos não traz pagamentos, bonificações ou subscrições,
mas não informa janela histórica e não basta para certificar todo o intervalo.

O [regulamento atual](https://www.blackrock.com/br/literature/bylaws/ishares-bova11-brl-regulamento-2026-ptbr.pdf),
seção 6.6, permite amortização em dinheiro sem reduzir o número de cotas;
6.7 também prevê resgate compulsório. O artigo 34 da versão anterior permitia
amortização em condições específicas. Uma permissão não prova ocorrência.

O [demonstrativo de 2018](https://documentos-fundos.b3.com.br/documents/d/guest/BOVA_2018-06-12T12-49-36-740-pdf)
foi recuperado pelo arquivo B3 e cotejado com o catálogo CVM anterior à migração
para FNET. O [demonstrativo de 2026](https://www.blackrock.com/br/literature/annual-financial-statements/ishares-bova11-brl-demonstrativos-financeiros-2026-ptbr.pdf)
inclui o exercício encerrado em março de 2026 e o comparativo de 2025.
As tabelas patrimoniais não exibem linha separada de amortização.
Criação/resgate de cotas nesses demonstrativos são fluxos do fundo no mercado
primário, não alteração obrigatória da posição de cada comprador na bolsa.
A política incorpora resultados ao patrimônio: dividendos das ações da carteira
não são uma segunda receita em dinheiro do detentor de BOVA11.
Isso é suporte documental limitado aos períodos examinados.

A [convocação de incorporação](https://www.blackrock.com/br/literature/shareholder-letters/ishares-bova11-brl-convocacao-agc-incorporacao-ptbr.pdf)
propôs absorver o fundo de CNPJ 11.455.378/0001-04. O
[comunicado de 21/01/2026](https://www.blackrock.com/br/literature/shareholder-letters/ishares-bova11-brl-sumariodecisoesmerger3-ptbr.pdf)
informa que a assembleia de 08/01 não foi instalada por falta de votos escritos.
Nenhum ajuste de cotas ou incorporação executada foi inferido.
Há divergências entre datas de rótulos, texto e convocação; foram registradas
sem corrigir silenciosamente os documentos.

**Ainda não certificado:** cobertura contínua dos originais de abril/2018 a
março/2024, leitura integral de todos os avisos de fundo/classe, direitos após
a venda e eventos de abril/2026 até o cutoff. Não preencher uma lista de eventos
desconhecida com `[]`: os campos permanecem `null` e `full_interval_certified=false`.

## Entrega, orçamento e validação

- [Entradas operacionais estruturadas](2026-09-09-h21-operational-inputs.json):
  condições, unidades, fontes e campos desconhecidos, sem configurar negociações.
- [Inventário de fontes](2026-09-09-h21-source-inventory.json):
  URLs, horários, hashes, falhas e resultado da reconciliação.
- [Reprodução da atualização](../../research/session-20260909/source_closure/README.md):
  script stdlib e limites de uso.

Fontes originais e tentativas ficam em
`C:\STOCKS\work\h21-source-closure-20260909`, incluindo `normalized-v1` e
`normalized-v2`. A segunda revisão acrescenta proveniência, com preços idênticos.
Os 77 registros de aquisição direta incluem um HEAD registrado posteriormente.
O contador não inclui navegação, busca ou redirecionamentos e não comprova
um limite sobre todas as requisições HTTP. Bytes de transporte retidos:
82.716.664; arquivo recomposto e cópias derivadas não contam como novo download.
Coleta e normalização encerradas às 20:11:20 UTC, antes de 20:20.

Validação local rejeitou hash divergente, ZIP truncado e calendário com fechamento
falso em 09/07; nenhum desses casos gerou saída aceita. A série final passou
as verificações descritas acima. A CI canônica Linux é conferida por SHA no PR
e novamente no commit integrado; seu recibo final fica em
`C:\STOCKS\outputs\ENTREGA_FONTES_H21_20260909.json`.
Ruff/Pyright/pytest canônicos não cobrem este auxiliar de pesquisa; os casos reais
e negativos locais são evidência separada.

H1–H20/H21, bancos, ledgers, arquivo de migração e entregas anteriores foram
preservados. Houve exposição incidental a tabelas de desempenho nos documentos
e sites; não existe holdout intacto. Lucro executável e lucro futuro continuam
`null`. O plano futuro já registrado segue sem observações ou processo ativo.
