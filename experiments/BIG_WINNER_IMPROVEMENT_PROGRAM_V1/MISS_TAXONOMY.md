# Miss taxonomy

`analysis/hit_miss_map.csv` preserva 278 episódios × 7 detectores. As únicas causas atribuídas automaticamente são demonstráveis: `RANK_TOO_LOW`, `NO_SIGNAL`, `INSUFFICIENT_HISTORY`, `OUTCOME_UNCERTAINTY` e `DETECTED`. Setor e market cap ficam explicitamente `NOT_AVAILABLE_PIT`; não foram inferidos.

Foi descoberto um bug de emissão histórica: os sete JSONs detalhados de episódios V1_PRICE contêm a lista da última iteração (`VOLUME_SURGE`), embora os resumos no `FINAL_SCORECARD.json` tenham sido computados antes e permaneçam distintos/corretos. Os artifacts congelados não foram alterados; este mapa é a reconstrução corrigida com identidade nova.
