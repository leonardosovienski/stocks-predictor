MISSION_STATUS = COMPLETE
FINAL_MAIN_SHA = resolve `refs/heads/main` (exact SHA reported after the final commit; a commit cannot contain its own SHA)

ENGINEERING_IMPLEMENTATION_STATUS = COMPLETE
HISTORICAL_INTEGRITY_STATUS = COMPLETE
DATA_QUALITY_STATUS = PARTIAL

V2_SELECTION_STATUS = COMPLETE — baseline selected, no predictive complexity added
V2_IMPLEMENTATION_STATUS = COMPLETE
V2_FREEZE_STATUS = COMPLETE — revision 3, hash `5e1a96fab748fee69446fe46ffe2692128247060b590ff4e96c096202f7ad564`

PROSPECTIVE_INFRASTRUCTURE_STATUS = COMPLETE
SHADOW_IMPLEMENTATION_STATUS = COMPLETE
SHADOW_RUNTIME_STATUS = READY_NOT_SCHEDULED

SCIENTIFIC_VALIDATION_STATUS = PENDING_PROSPECTIVE_EVIDENCE
GIT_MAIN_INTEGRATION_STATUS = COMPLETE_LOCAL_MAIN_AFTER_FINAL_FAST_FORWARD

# Respostas finais

1. **O que V1_PRICE ensinou?** Hits abundantes não bastam: com base rate de 20,47% e seleção larga, o sistema encontra winners mesmo com lift próximo de 1. Nenhum detector passou todos os gates.
2. **Por que houve hits?** Seleção de aproximadamente 20%, taxa-base alta e exposição genérica a tendências/pullbacks. Isso é `SUPPORTED_BY_AVAILABLE_EVIDENCE`; causalidade econômica não é.
3. **Por que houve tantos false positives/misses?** Enrichment pequeno e instável, rankings abaixo do corte, gate M12+vol que removeu sinais e 55 episódios com fronteira incerta. Setor/market cap PIT não permitem explicação adicional honesta.
4. **Explicação mais sustentada para baixo lift:** base rate alta + seleção ampla + instabilidade temporal. Redundância e incerteza corporativa contribuem; causalidade setorial é `NOT_TESTABLE`.
5. **Momentum 12-1:** selecionado inalterado como baseline prospectivo; ainda não validado.
6. **Momentum 6-1:** `KEEP_AS_ANALYSIS_ONLY`, fora da V2 por menor enrichment e redundância.
7. **Reversal 21:** rejeitado; alta cobertura não sobreviveu a Holm e deteriorou na cauda.
8. **Sinais rejeitados:** 52W_HIGH, LOW_VOL_252, MOMENTUM_LOW_VOL, VOLUME_SURGE, M6/Reversal como componentes e qualquer ensemble post-hoc.
9. **Bugs corrigidos:** reconstrução dos detalhes de episódios sem reescrever V1; import/independência do shadow; artefato idempotente; ledger e outcomes append-only.
10. **Problemas de dados corrigidos:** hashes/versionamento obrigatórios, missing identity explícito, continuidade apenas por eventos aprovados, metadata de missingness e contrato de outcome intermediário.
11. **Limitações restantes:** security master/sector PIT incompleto, 2.184 saltos abertos, eventos complexos e outcomes futuros inexistentes. `DATA_QUALITY_STATUS=PARTIAL`.
12. **Há V2 defensável?** Sim, como candidato prospectivo simples; não como modelo cientificamente confirmado. A decisão foi `NO_DEFENSIBLE_V2_PREDICTIVE_CHANGE`.
13. **Arquitetura:** `BIG_WINNER_V2_MOMENTUM_12_1_BASELINE`, score 252–21, top 20%, universo PIT top 60, next-open.
14. **Por quê?** Mecanismo claro, simplicidade, menor superfície de leakage, dados existentes e falsificabilidade.
15. **Hipóteses rejeitadas:** M6, Reversal, ensembles, low-vol, 52-week high, volume, thresholds otimizados. Setor/regime foram deferidos por fonte PIT ausente, não selecionados.
16. **V2_SELECTION_FREEZE:** 2026-09-19T21:23:26-03:00, commit `101583c`, hash `57892cdfa540f57cca70737ddcdbf4bf75c643d04091b5ea7926072ad4ba24a2`.
17. **V2_FINAL_FREEZE:** revisão final 3 em 2026-09-19T22:25:00-03:00; revisões anteriores permanecem no Git e foram superseded explicitamente.
18. **Implementado:** scorer determinístico, contratos PIT/corporativos, freezes verificáveis, ledger SQLite hash-chained, correções por append, outcomes 1/3/6/12m, shadow e artifacts imutáveis.
19. **Testado:** 19 testes V2, 33 testes V1_PRICE e 18 testes V1; execução real dupla do shadow; hashes V1; compileall e diff check. A suíte ampla baseline não pôde importar 72 módulos no Python auxiliar por ausência preexistente de pytest/PyYAML/predictor_core.
20. **Proteção V1/V1_PRICE:** hashes fixos em regressão; artifacts originais não alterados. O bug detalhado de episódios é reparado em derivação nova.
21. **Prospective ledger:** SQLite com triggers que proíbem UPDATE/DELETE, hash chain, idempotency key e correction events append-only.
22. **Backfill:** toda decisão histórica recebe `development_backfill=true` e `prospective_evidence_eligible=false`.
23. **PROSPECTIVE_EVIDENCE_START:** primeira decisão com observação de mercado e geração posteriores ao freeze final; ainda `NOT_STARTED`.
24. **Shadow:** constrói universo PIT, calcula V2 congelada, persiste ranking/metadata/hash, anexa ledger e emite JSON imutável; sem capital.
25. **Shadow ativo?** Não. Implementação completa e validada, runtime `READY_NOT_SCHEDULED`.
26. **O que depende do futuro?** Novas observações pós-freeze, 12 meses de maturação, mínimo de 24 coortes e eventual confirmação/rejeição científica.
27. **Commits:** `101583c`, `861429e`, `8b73b61`, `d6f1e1e`, `7638f4c`, `6fd9c9f`, `8e42cc6` e o commit final de documentação/integridade; além dos commits preservados V1/V1_PRICE.
28. **SHA final da main:** resolvido e reportado após o commit final e fast-forward local.

# Conclusão

O melhor estado defensável hoje não é um ensemble retrospectivamente otimizado. É um baseline M12 simples, congelado, operacionalmente testado e preparado para falhar de forma visível. Nenhuma evidência histórica foi promovida a confirmação prospectiva. A única pendência científica legítima é o futuro.
