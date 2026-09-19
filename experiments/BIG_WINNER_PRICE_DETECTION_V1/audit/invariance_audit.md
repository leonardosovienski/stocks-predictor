# Ranking invariance audit

Momentum 12-1, momentum 6-1, reversão 21, volatilidade de retornos e proximidade da máxima de 52 semanas são invariantes a uma reescala positiva uniforme da janela histórica. `MOMENTUM_LOW_VOL` herda essas invariâncias. Volume surge não depende da escala de preço. Testes sintéticos verificam scores e ranking; portanto retrieval posterior de um ajuste futuro que apenas reescala toda a janela não bloqueia PIT.
