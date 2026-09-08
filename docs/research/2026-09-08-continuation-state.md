# Estado reconstruído antes da nova medição

O checkout correto é a branch `fix/stocks-cvm-execution-20260907`, inicialmente
limpa em `93fa05f`. O manifesto de preservação tem o hash do recibo; 33 arquivos
selecionados (entradas do replay e banco de pesquisa) foram novamente conferidos.
Os dois bancos mantêm os hashes documentados. Não se atribui a esta checagem uma
nova verificação dos 36.998 arquivos.

A execução do código desta cópia produziu o mesmo JSON da revisão anterior:
31 entradas e 365.198 cotações validadas, lucro `null`, 1.237 intervalos sem
certificado, 356 datas de conhecimento ausentes, 36 entradas societárias ausentes.
Há 357 ocorrências de cronologia de caixa, não só as 356 datas de pagamento
ausentes. Isso será localizado; a descrição histórica não esgota os problemas.

H1–H16 permanecem fechadas nos termos históricos, H3 não foi executada. Seus
vereditos não são prova de lucro/prejuízo executável no instrumento atual.
H17 é inconclusiva por dados; H18 é controle instável; H19 trimestral é uma pista
exploratória. Não há resultado confirmatório, holdout intacto demonstrado ou
história de fills prospectivos validada. Não reabrir as famílias por novos limiares.

Há pelo menos 32 configurações e 37 avaliações históricas expostas. O histórico
pode sustentar Discovery documentada, nunca um novo teste independente por
renomeação. Esta intervenção não observa retornos e não inicia coorte prospectiva.
Protocolos, observações, ledgers e quarentenas existentes ficam preservados.
A próxima decisão irreversível seria observar uma nova configuração de retorno
ou iniciar uma coorte futura; nenhuma delas é necessária à medição escolhida.

Estão disponíveis cotações brutas/preservadas, cadastro de caixa, documentos
CVM/RI/B3, calendários fiscais e fontes de sucessores. Integridade de arquivo
não demonstra cobertura PIT, inventário completo, liquidez na abertura ou
crédito líquido por carteira. Fontes de 2026 exigem legislação datada: o cadastro
corretamente deixa líquidos não revisados como desconhecidos.

O capital informado é R$5–10 mil. Lucro mínimo e horas aceitáveis são desconhecidos.
Usaremos cenários explícitos; cada 1 ponto percentual incremental anual representa
R$50/R$100 antes de manutenção. Capacidade de mercado e diversificação não serão
inferidas de um preço de abertura. O sinal B/M pode refletir risco de empresas
baratas, e não erro de preço; risco/setor/concentração continuam confundindo a
interpretação dos diagnósticos antigos. IC, estabilidade e intervalos anteriores
não serão recalculados para escolher outra variante.

A comparação qualitativa favorece simplificar a medição (rápida, fontes existentes,
sem nova exposição a retornos). Completar H19 tem custo de fonte e integração alto;
uma nova hipótese de reação a resultados tem mecanismo plausível, porém vantagem
informacional ainda não demonstrada e exigiria novo PIT. Não é possível atribuir
probabilidades de lucro confiáveis a nenhuma delas. Prioridade heurística 0–5,
sem pretensão probabilística: simplificação 4, reconstrução integral 2, nova
hipótese 1. O protocolo separado congela métricas, cenários e regra de parada.

Próximas ações autorizadas: localizar defeitos reproduzíveis; implementar a
contabilidade necessária; executar o diagnóstico de compras; comparar os custos
recorrentes e de reconstrução; validar e registrar a decisão com Git atualizado.
Nenhuma mudança em Core/Ops é necessária.
