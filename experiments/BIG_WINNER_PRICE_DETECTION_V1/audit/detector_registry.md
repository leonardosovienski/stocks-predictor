# Detector registry

| Detector | Regra histórica | Direção | Fidelity |
|---|---|---|---|
| MOMENTUM_12_1 | retorno 252-21 | maior | SEMANTICALLY_EQUIVALENT |
| MOMENTUM_6_1 | retorno 126-21 | maior | SEMANTICALLY_EQUIVALENT |
| LOW_VOL_252 | desvio-padrão de 252 retornos | menor | SEMANTICALLY_EQUIVALENT |
| REVERSAL_21 | retorno de 21 sessões | menor | SEMANTICALLY_EQUIVALENT |
| MOMENTUM_LOW_VOL | gate top-40% momentum, depois baixa vol | maior (score=-vol) | SEMANTICALLY_EQUIVALENT |
| 52W_HIGH | preço/máxima 252 sessões | maior | SEMANTICALLY_EQUIVALENT |
| VOLUME_SURGE | média 21/média 252 - 1 | maior | EXACT |

Todos eram mecanismos julgados antes desta avaliação. Direção, seleção top-20% e desempate por ticker foram congelados antes dos labels.
