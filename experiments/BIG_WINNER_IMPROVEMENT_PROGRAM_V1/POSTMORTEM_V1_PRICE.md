# Post-mortem V1_PRICE

Status das afirmações abaixo: `SUPPORTED_BY_AVAILABLE_EVIDENCE`, salvo indicação.

V1_PRICE mostrou que detectar muitos episódios não equivale a enriquecer uma seleção. A taxa-base complete-case foi 20,47% nos seis detectores amplos; selecionar aproximadamente 20% do universo permite muitos hits mesmo com lift próximo de 1. `MOMENTUM_12_1` teve precision 22,97% e lift 1,122; `MOMENTUM_6_1`, 22,32% e 1,090; `REVERSAL_21`, 22,83% e 1,115. Nenhum passou simultaneamente estabilidade temporal, Holm, identificação parcial e cauda confirmatória.

Decomposição do baixo lift:

- taxa-base alta e seleção larga explicam hits abundantes sem grande informação incremental;
- instabilidade anual é observada: M12 ficou abaixo de lift 1 em 2018, 2019, 2021, 2022 e 2025, mas acima em 2017, 2020, 2023 e 2024;
- M12 e M6 têm Jaccard mensal médio 0,421, indicando redundância material, mas não identidade;
- 2.184 saltos corporativos abertos geraram unknowns e limites externos largos;
- setor, market cap PIT e identidade corporativa completa não estão disponíveis para atribuição causal; explicações setoriais permanecem `NOT_TESTABLE`;
- causalidade econômica, alpha e lucro permanecem `NOT_SUPPORTED` por ser estudo apenas de preço.

O principal mecanismo plausível é persistência de tendência longa, mas a evidência é frágil e condicionada no tempo. A V2 não adiciona componentes post-hoc: congela M12 como baseline prospectivo falsificável.
