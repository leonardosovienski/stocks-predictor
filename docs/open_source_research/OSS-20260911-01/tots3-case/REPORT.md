# OSS-20260911-01 — X01, TOTS3, 2020-04-01 a 2020-07-01

**Caso não fechado: X01_CANONICAL_CASE_INCOMPLETE.** Esta continuação produziu um ledger cronológico de 92 dias, 62 preços brutos reconciliados com COTAHIST e um inventário de 51 registros CVM relacionados ao intervalo, incluindo apresentações fora dele. Documento validado não equivale a informação econômica utilizável. Nenhum retorno, estratégia ou confronto econômico foi calculado. X03, discovery, baseline e scoring não foram reiniciados; X05 não foi executado. DOC03 conserva seu caráter de controle majoritariamente de rejeição. IDs e estados históricos não foram promovidos ou sobrescritos.

O arquivo `ledger.jsonl` é o ledger único. Ele separa fatos documentais retrospectivamente reconstruídos, conhecimento estritamente certificado, calendário de eventos, caixa, recebíveis, quantidade econômica, custódia, preço e fórmula do valor econômico. Os campos estritos de disponibilidade permanecem nulos quando a prova falta. Não é um replay causal aprovado. `events.json`, `identity.json`, `document-inventory.json`, `prices.jsonl`, `UNKNOWNs.json` e os recibos fornecem a linhagem.

## Identidade e PIT

TOTVS S.A., CNPJ 53.113.791/0001-22, código CVM 019992, TOTS3, ações ordinárias. O FCA2019, documento83108/v1, entregue em10/05/2019, declara início da negociação em07/03/2006. Os 62 registros de cotação conferidos vinculam TOTS3 a BRTOTSACNOR8 no período. O aviso do split mantém espécie e direitos. Não foi identificada mudança de ticker ou classe nos registros inspecionados, mas cobertura negativa contínua ainda não está certificada.

O arquivo FCA2020 atual contém metadados v1/documento93408/entrega25/05/2020 e v2/documento102853/entrega13/04/2021. A tabela de valores mobiliários só contém v2. Ela foi rejeitada para todo o intervalo; não se usou o recebimento da v1 para antecipar seu conteúdo. A data de referência2020-01-01 não torna a versão2021 admissível. Fontes: [FCA2019](https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FCA/DADOS/fca_cia_aberta_2019.zip) e [FCA2020](https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FCA/DADOS/fca_cia_aberta_2020.zip); bytes, cabeçalhos e observação atual estão nos recibos.

O IPE congelado fornece **datas** de entrega, versões e protocolos, não timestamps intradiários. Publication time exato, ingestão histórica e effective decision time estrito não foram inventados. D+1 aparece apenas como limite de um cenário que pressupõe entrega pública, não como fato observado nem calendário de sessão certificado. A observação atual é registrada em UTC e nunca retrodatada. A cópia da ata no RI foi lida, mas sua igualdade de bytes com a v2/CVM ainda é UNKNOWN.

## Eventos e contabilização

| Evento | Anúncio | Direito/data-com | Ex/negociação | Crédito programado | Unidade e valor |
|---|---|---|---|---|---|
| JCP herdado |18/12/2019|23/12/2019|26/12/2019|20/05/2020|BRL0,23 por ação antiga elegível; líquido cenário0,1955|
| Dividendo |27/04/2020|27/04/2020|28/04/2020|20/05/2020|BRL0,13014413 por ação antiga segundo snapshot B3; ata arredonda0,13|
| Split3:1 |27/04/2020|30/04/2020|04/05/2020|06/05/2020|cada1 ação passa a3; crédito adicional2; sem frações e sem mudança do capital|

O JCP pertence ao titular na data de direito de2019, mesmo que sua posição de abril seja diferente. O aviso condiciona o recebimento à regularidade cadastral. Data de pagamento programada não comprova disponibilidade bancária. A convenção21/05/2020 `available_on` do painel anterior não foi promovida a recibo. O cenário15% de retenção é parâmetro herdado, não classificação fiscal do usuário.

Há uma divergência não resolvida no JCP: aviso original R$44.306.677,21 versus ata R$43.857.567,02, diferença R$449.110,19. Ambos informam R$0,23 por ação. Não se atribuiu a diferença a tesouraria sem documento. A precisão do dividendo no snapshot B3 foi preservada, mas seu primeiro instante público ainda não está demonstrado; não se corrigiu a ata silenciosamente.

Fontes primárias: aviso JCP, hash71a6957c565c04c4ba9f7768a49ce1066c6fea3a3407734b0f02636dd4fa92ea, protocolo727083/seq251858/v1; [ata do RI, página2](https://api.mziq.com/mzfilemanager/v2/d/d3be5d49-62e7-4def-a3e1-ab25ff09f153/a3258756-17dd-1705-8d9c-95ad82c485f1?origin=1), hash9276d390ea04746cd547ff46698fdb63ef3af2f6744510954a52e222dfcafc4c; aviso split, hash741865b495b248d397c051ae290b4a5a2abd337205fc4a9a03abc516ef76e9ff, protocolo756672/seq281426/v1. PDFs originais e páginas renderizadas acompanham o pacote.

No inventário constam aquisição Wealth Systems (08/04), debêntures não conversíveis (22/04), conclusão Supplier (30/04), participações relevantes, resultados, assembleias e governança. Cada registro tem status; metadados sem conteúdo certificado têm efeito econômico UNKNOWN, não zero. Os quatro downloads focados para ata/CVM e esses três eventos não produziram PDFs íntegros nas três tentativas limitadas. Erros de transporte/completude foram registrados, não aceitos como prova. O inventário IPE tampouco prova sozinho ausência de todos os eventos B3, retificações ou recebíveis herdados adicionais.

## Ledger econômico

Os parâmetros Q0, Q_JCP, Q_DIV, Q_SPLIT e C0 são independentes; não representam a carteira do usuário. O exemplo mantém posição após a data-base do split e não inclui operações. Custos ficam como parâmetro UNKNOWN, nunca zero presumido.

| Data | Fato/estado reconstruído | Quantidade e caixa |
|---|---|---|
|01/04|Abertura do intervalo; JCP anterior pode estar a receber|Q0; recebível bruto0,23×Q_JCP; C0 não informado|
|27/04|Deliberações de dividendo e split; data-com dividendo|fixar Q_DIV; split ainda não altera posição de negociação|
|28/04|Ex-dividendo|manter recebível por ação antiga; não assumir queda exata do preço|
|30/04|Data-base split|fixar Q_SPLIT|
|04/05|Negociação ex-split|quantidade econômica3×Q_SPLIT; custódia Q_SPLIT +2×Q_SPLIT pendentes|
|06/05|Crédito programado split|transferir pendente para creditado; nunca multiplicar novamente|
|20/05|Pagamento programado JCP e dividendo|somente no cenário de pagamento pontual: retirar recebíveis e adicionar o mesmo valor ao caixa|
|21/05|Data de disponibilidade modelada anteriormente|não prova crédito real; manter UNKNOWN estrito|
|25/05|Metadado FCA2020v1|não substitui conteúdo ausente por versão2021|
|01/07|Encerramento do intervalo|reconciliação documental parcial, sem promoção de gate|

Valor econômico = quantidade econômica × preço bruto contemporâneo + caixa + recebíveis, descontando somente custos ainda não debitados. Ações pendentes já incluídas na quantidade econômica não são somadas novamente como recebível. Após o split, os direitos anteriores continuam0,23×Q_JCP e0,13014413×Q_DIV, com as ressalvas de precisão/PIT. No cenário líquido pontual, a transferência é0,1955×Q_JCP+0,13014413×Q_DIV; a quantização em centavos e a disponibilidade real são UNKNOWN. Não se declarou esse cenário como realizado.

## Preços e ajuste

`prices.jsonl` conserva linha original, número da linha, hash, preço bruto, FATCOT, unidade BRL/ação e ISIN. As 62 observações do intervalo foram reconciliadas entre TXT e JSONL congelados. Não se calculou retorno, RMSE, IC ou resultado de estratégia. Dias sem registro conservam preço UNKNOWN; não foram classificados automaticamente como feriados ou preenchidos com zero.

Preço ajustado total e fator de retorno total permanecem UNKNOWN. Uma coluna separada fornece apenas transformação analítica de unidade para a base pós-split: fator1/3 antes04/05 e1 depois, com origem no aviso. Ela é retrospectiva e não entra no cálculo do patrimônio com quantidade já triplicada. FATCOT é fator de cotação, não fator de corporate action. Não se aplicou ajuste adicional de dividendo.

## UNKNOWNs e gate

`UNKNOWNs.json` lista publicação/ingestão histórica e decisão efetiva; primeira publicação da precisão do dividendo e vínculo da ata à versão CVM; divergência do agregado JCP; crédito/disponibilidade, arredondamento e retenção do beneficiário; saldos/posições/custos; conteúdo e cobertura de todos os eventos materiais; continuidade integral e conteúdo FCA2020v1; publicação das cotações e ajuste total; crédito efetivo e execução de ações pendentes.

Dos sete critérios, a mecânica do split e a lista de UNKNOWNs passam; linhagem e reprodução passam somente para a evidência disponível. Identidade contínua, completude de eventos e PIT econômico permanecem parciais. As unidades e datas programadas dos dois recebíveis estão definidas, mas liquidez efetiva não está certificada. A disciplina de não usar retrospectiva foi mantida bloqueando campos, não preenchendo lacunas.

## Contratos e regras candidatas

1. Associar conteúdo a emissor+documento+versão+hash e testar disponibilidade antes do join; reference date nunca substitui entrega.
2. Separar announcement, record, ex/trading, scheduled credit, actual credit e cash available; atraso de cadastro é classe de exceção.
3. Congelar quantidade elegível de cada recebível independentemente da posição corrente; direitos anteriores sobrevivem a venda/split sem multiplicação.
4. Representar split como conversão de unidade, mais transferência de custódia pendente; preservar valor sob preço teoricamente inverso apenas no controle analítico.
5. Liquidação de recebível é transferência para caixa; aplicar uma vez por ID. Não é receita adicional ao direito já reconhecido.
6. Preservar bruto, líquido de cenário, unidade, precisão, moeda e procedência. Divergência de totais ou precisão gera exceção, nunca ajuste silencioso.
7. Separar dado de preço bruto, normalização FATCOT e ajuste corporativo; conferir raw×quantidade da mesma unidade; não misturar adjusted+cash.
8. Cobertura deve ser por ativo/emissor/data/evento/campo/versão/disponibilidade/reprodução. Documento com hash validado e conteúdo sem PIT continua não utilizável.

As regras são candidatas extraídas deste caso incompleto, ainda sem evidência de generalização. Automatizáveis: hashes, joins por versão, rejeição de versão futura, integridade ISIN/ticker, tipos/unidades, comparação de fontes, conservação de posição/patrimônio em controles, idempotência de crédito, flags de pending, bloqueio de UNKNOWN e cobertura por calendário. Não automatizar como certeza a inferência de ausência de eventos a partir de metadados.

Próximo gate de X01: fechar a linhagem temporal dos documentos e valores deste mesmo caso, começando pela ata/aviso original com precisão do dividendo e reconciliação JCP; completar a cobertura de eventos e definir qual cenário de liquidez pode ser documentalmente sustentado. Depois, repetir o ledger uma única vez sob contratos fixos. Não escalar manualmente ativos.

Somente após esse gate, menor teste candidato: dois casos documentais já catalogados, escolhidos por estrutura e antes de olhar preços/retornos — um split inteiro com provento pendente, outro evento com fração/crédito defasado — mais uma versão futura e um pagamento duplicado injetados. Congelar regras; executar sem intervenção; exigir reconciliação dos campos necessários ou rejeição explícita das exceções. Qualquer edição manual invalida a alegação de generalização. Este teste não foi executado.

X02 pode avançar em fixtures e adapter; benchmark independente exige Linux autorizado, versões/dependências fixadas e recibos. X04 pode avançar em protocolo e controles sintéticos de fator/residual/custos; análise empírica depende da cobertura pertinente, sem declaração de alpha. Não se executaram essas frentes nesta continuação de objetivo único.

## Reprodução e preservação

`build_ledger.py` usa somente stdlib e fontes locais congeladas; `inspect_case.py`/`fill_gaps.py` são aquisição e leitura documental auxiliar, não runtime econômico. Não é necessário repetir downloads para reproduzir a reconciliação disponível. O pacote contém os arquivos necessários em `source15/` e `work/`; ajustar apenas os caminhos de entrada se extraído em outro local. Recibos mantêm caminhos canônicos e hashes originais. `manifest.json` verifica cada arquivo do pacote. Não executa código do pacote operacional nem acessa corretora.

Foram executados11 checks locais: preços brutos, contagem do split, bloqueio FCA futuro, invariância sintética, custódia pendente sem duplicação, direitos antigos sem multiplicação, liquidação conservando valor, rejeição de pagamento duplicado, ausência de valores pessoais inventados, independência do recebível herdado e preservação histórica. Isso não é revisão independente, prova de completude ou validação econômica. As três páginas materiais foram renderizadas e conferidas visualmente.
