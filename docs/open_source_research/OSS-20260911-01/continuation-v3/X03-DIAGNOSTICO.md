# X03 — mecanismo de UNC02 e encerramento delimitado

Continuação da mesma rodada. [Protocolo fixado antes do replay](X03-G1-diagnostic.json), [recibo](UNC02-diagnostic-receipt.json), [1000 linhas de replay](UNC02-replay-rows.jsonl). Nenhuma seed nova, troca de parâmetro, método substituto ou dado de mercado. As contagens462/464/359/462 foram reproduzidas exatamente. Não sobrescrevemos o recibo anterior nem aprovamos calibração retroativamente.

## Diagnóstico por causa

|Causa|Evidência e conclusão|
|---|---|
|Erro de implementação do gate|Não encontrado no caminho testado. Média/desvio calculados separadamente com fsum concordam com economic_gate até5,56e−17. Inclusão da fronteira do intervalo não muda nenhum resultado.|
|Controle/oráculo construído incorretamente|Não encontrado. X inicial tem variância estacionária1/(1−phi²); inovações normais com variância1; burn-in200 não introduz viés de inicialização. Média por pesos das inovações, sem recorrência AR direta, confere até2,78e−17. Variância por soma de covariâncias e por recursão de covariância do acumulado concorda exatamente em float.|
|Dependência temporal|Causa estrutural da subcobertura IID em phi0,5. Var(média)=0,00791551; o cálculo IID substitui por s²/504. Razão populacional aproximada de erros padrão1,733; largura IID observada/oráculo0,5765. Oráculo recupera103 casos e perde0:359→462.|
|Tamanho da sérieT=504|Para phi0, a cobertura teórica de1,96 com sigma estimado é Student-t503:94,9453%, versus95,0004% do oráculo. Diferença de0,055 ponto percentual, incapaz de explicar sozinha os2,6 pontos observados. Para phi0,5, tamanho efetivo da média é cerca de168 observações IID pela variância; aumentarT mantendo dependência não torna correta a fórmula IID.|
|Monte CarloM=500|O erro padrão de cobertura perto de95% é0,975 ponto percentual; margem normal aproximada1,91 ponto. O lote teve variância empírica dos z do oráculo1,13 e36/38 falhas. São caudas incomuns, porém compatíveis com a distribuição conhecida sob a hipótese de replicações pseudoindependentes. Não é prova de defeito da fórmula.|
|Falhas do controle e oráculo em conjunto|Sementes/inovações são emparelhadas entrephi. Correlação dos z=0,999316;36 falhas de oráculo são compartilhadas. Não são duas confirmações independentes de erro.|
|Critério|“95% dentro do Wilson observado” é uma triagem com erro tipoI, não demonstração determinística de calibração. Exigir que vários controles passem sem plano conjunto pode produzir alarmes por acaso. O critério original era aplicável como alerta e foi corretamente marcado FAIL; era insuficiente para distinguir defeito de flutuação ou certificar precisão estreita.|
|Outra causa|Não foi feito teste universal do PRNG nem prova de independência entre sementes. Os p-valores binomiais pressupõem o modelo ideal/pseudoindependente. Não há evidência localizada de erro de RNG, mas não eliminamos toda causa imaginável. Não abrimos campanha de seeds.|

## Probabilidades e interpretação

Sob o oráculo gaussiano, cobertura esperada95,0004%. ParaM=500, a faixa central binomial95% é465..484 coberturas. Observamos464(phi0) e462(phi0,5). P-valores bilaterais exatos por ordenação de probabilidades:0,030445 e0,013165. O IID em phi0 tem p=0,013772 sob Student-t503. Portanto a falha pontual ao nível5% é real como resultado do critério; não deve ser ocultada dizendo apenas “é ruído”.

Como diagnóstico posterior, Bonferroni para os quatro painéis fornece0,121780;0,052660;0,055087 nos controles citados. Não cruza5% nessa família, mas essa correção NÃO foi o critério original e NÃO aprova retrospectivamente nenhum painel. A forte correlação também impede tratar os testes como independentes. O resumo correto é: construção matemática correta no caminho verificado; controles caíram em uma região rara do Monte Carlo; aplicação IID sob dependência tem inadequação estrutural demonstrada.

O substituto idealizado que usa a variância marginal conhecida mas ignora covariâncias teria cobertura normal aproximada74,283% paraphi0,5. Isso explica a escala da queda; não é previsão exata da cobertura do intervalo com desvio amostral aleatório. Não prometemos explicar71,8% como constante teórica: é359/500 deste lote, com flutuação amostral. Não confundir diagnóstico pós-observação com novo teste confirmatório.

## Stop rule aplicada

Encerrar após um replay das mesmas1000 séries se contagens, cálculo independente de média/variância, aritmética do gate, fronteiras e decomposição das mudanças de cobertura passarem. Todos passaram dentro das tolerâncias previamente fixadas. A causa da inadequação IID e a explicação probabilística limitada dos controles ficaram estabelecidas; **diagnóstico UNC02 encerrado no escopo**. Não aumentarM ou trocar seeds nesta continuação. Nenhum bootstrap/HAC/conformal aprovado. Uma futura validação precisa definir tolerância prática, precisão Monte Carlo e decisão conjunta antes do teste; por exemplo precisão±1p.p. exigiria cerca de1825 replicações pelo cálculo normal preliminar, não autorização para rodá-las agora.

X03 ainda não fornece um método de inferência validado para labels reais deX05, purga/embargo específicos ou multiplicidade da busca. Encerrar este diagnóstico evita investigação infinita e libera atenção para o gargalo documental deX01.
