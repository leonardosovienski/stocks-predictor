# Stocks Predictor — correções e fontes revisadas

**As correções de código passaram nos testes. A base melhorou, mas a comprovação de lucro continua bloqueada. Ainda existem pendências de dados; não seria correto declarar que todas foram resolvidas.**

| Verificação | Antes da reconstrução | Revisão 12 |
|---|---:|---:|
| Direitos de proventos originais preservados | 778 | 778 |
| Direitos sem data de pagamento | 356 | 37 |
| Direitos originais sem valor líquido | 389 | 64 |
| Linhas de pagamento sem líquido, contando parcelas | 389 | 66 |
| Cronogramas parcelados reconciliados nesta reconstrução | 0 | 9, com 32 parcelas |
| Eventos societários integrados | 0 | 8 |
| Eventos societários ainda exigidos | 36 | 28 |

Foram resolvidas 319 datas ausentes. Os 778 direitos resultam em 801 linhas de pagamento após a separação de parcelas. Os grupos de pendências se sobrepõem: não devem ser somados. A auditoria confere 788 arquivos, incluindo 753 arquivos primários e 1 relatório local derivado, além de 365.198 cotações.

## O que foi corrigido

- O parser preserva créditos B3 sem data de aprovação em uma lista separada de registros incompletos. Mantém os 3.202 créditos completos já extraídos e recupera 3.665 incompletos nos mesmos 163 documentos. Esses registros não são associados automaticamente a declarações de proventos.
- Parcelamentos conservam o direito original e impedem pagar novamente o total agregado. As diferenças literais de arredondamento ficam explícitas. Foram reconciliados, entre outros, os sete pagamentos da CPFL em 2025 e os dois dividendos da antiga BR Distribuidora em 2020.
- Avisos originais e retificações são ligados pela identidade do evento. Foram retiradas duas associações provisórias erradas entre JCP e dividendos; os arquivos anteriores continuam preservados. Duas datas TIM foram corrigidas com o aviso posterior da companhia.
- Tabelas presentes como imagens foram conferidas visualmente nos PDFs originais. Isso recuperou informações de CPFL, Telefônica, Aliansce e Grupo Soma que a extração de texto não mostrava.
- O relatório local reconstruído deixou de ser contado como fonte primária. Hash confirma integridade; não prova sozinho origem, veracidade ou completude.
- A atualização Selic sobre proventos recebeu tratamento separado, com período documentado e regra de retenção para pessoa física. Os líquidos de 2026 tratados nesta revisão representam retenção no pagamento; não resolvem eventual imposto mínimo anual pessoal.
- Os oito desdobramentos inteiros conservam quantidade proporcional e custo fiscal total. Os demais eventos não receberam termos ou bases inventados.

A publicação original da Telefônica confirma o pagamento da restituição de capital em 15/07/2025; a data foi incorporada, mas a tributação e a base fiscal continuam pendentes. A reapresentação versão 2 na CVM esclarece que o pagamento da Vibra anteriormente indicado para 2026 está agendado para 15/09/2027. Pagamento agendado não equivale a dinheiro recebido. [Telefônica: comunicado original](https://api.mziq.com/mzfilemanager/v2/d/24165f81-24d6-4648-bf9f-66712905d5a2/95055a57-421c-0f90-4b03-811356da6775?origin=1), [Vibra: versão 2](https://www.rad.cvm.gov.br/ENET/frmDownloadDocumento.aspx?Tela=ext&descTipo=IPE&CodigoInstituicao=1&numProtocolo=1494351&numSequencia=1019057&numVersao=2).

## O que continua bloqueando o resultado econômico

Restam 37 datas e 66 líquidos de pagamentos derivados, além de 28 entradas societárias. Há avisos que trazem apenas prazo máximo, documentos históricos que não foram recuperados, divergências de valores, devolução de capital dependente de base fiscal e eventos com frações, sucessores ou novas classes de ações. Prazos máximos não foram tratados como datas efetivas.

Nenhum dos 1.248 intervalos exigidos tem inventário integral certificado. Encontrar pagamentos conhecidos não demonstra que nenhum outro provento ocorreu. A revisão identificou, por exemplo, duas atualizações monetárias da BR Distribuidora em 2020 que não constam dos 778 direitos congelados. Elas foram registradas como lacuna de inventário. A SLC em 2019 tem data confirmada, mas as unidades antes/depois do desdobramento ainda precisam de reconciliação.

Também permanecem os requisitos de arredondamento do caixa na corretora, tratamento de frações e revisão H20 vinculada à versão final das fontes. O calendário congelado termina em 01/04/2026; não acrescentei pregões futuros presumidos. Parte dos campos de disponibilidade permanece bloqueada. O primeiro sinal de 2018 continua sem cobertura suficiente. Não retirei períodos ou empresas para melhorar artificialmente o resultado.

**Lucro líquido histórico e projeção de lucro futuro permanecem desconhecidos.** Não há holdout intacto. Foram preservados H1–H20, a contagem administrativa 53/55 e as observações anteriores. Nenhuma nova avaliação de retorno, ordem, serviço pago, instalação, agente adicional ou escrita em bancos protegidos ocorreu nesta revisão. O protocolo de aquisição de fontes não autoriza um novo teste de retorno: ele ainda exigirá evidência completa e pré-inscrição vinculada ao hash final.

## Validação e reprodução

- **714 testes passaram**, sem avisos, no Python global 3.13, em 116,34s: 697 regulares e 17 arquivados.
- **145 testes passaram na wheel extraída fora do checkout**, em 0,75s. A primeira tentativa dessa suíte parou porque testes antigos usam importação de módulo sem o nome do pacote; o caminho do ambiente de teste foi corrigido para apontar à própria wheel, preservando o log inicial e sem mudar o runtime.
- Ruff e Pyright passaram; os módulos de fontes foram incluídos no escopo permanente do Pyright.
- Cinco tentativas de adulteração foram rejeitadas: alteração de fonte, exclusão de direito, alteração do bruto com novo manifesto, liberação indevida do inventário e promoção de relatório derivado a fonte primária.
- O pacote portátil verificou seus 856 arquivos e reproduziu a auditoria **byte a byte**, com Python 3.13 em modo isolado, sem instalar a wheel, sem rede e sem importar código do checkout.

Código testado: `6e54e5d9c5187a9f555c60d67894334cfdb996be`.

Manifesto das fontes: `b9dfab5fb2dc67f7fcdd71f52b325a3a1d442917c116f514fd09f11926876f7e`.

SHA256 da auditoria: `fdaf20300e47ca4b42e1e99cea46ffc80ecf4efaac4f0f80f6f39e917b4d105a`.

O ZIP contém fontes locais, baseline preservada, revisão, wheel, histórico e comando `REPRODUZIR_FONTES.py`. Depois de extrair, execute `py -3.13 -I REPRODUZIR_FONTES.py --output auditoria-reproduzida.json`. O código de saída 0 significa reprodução correta da auditoria; o resultado econômico continua `BLOCKED_MISSING_EVIDENCE`.

Arquivos complementares: `PENDENCIAS_STOCKS.json` lista os bloqueios concretos; `VALIDACAO_FONTES_12.json` registra os testes e hashes; `PRONTIDAO_FONTES_12.json` contém a auditoria completa. A conferência foi feita pelo mesmo agente, sem revisão científica independente.
