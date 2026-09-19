# Data contract

Fonte imutável: objeto SQLite SHA-256 `a22739794ba4a43a11544338d4a91e14cb6a0b1f7b132ab460f96d3359f63cf4`, COTAHIST 2016-01-04 a 2026-08-27. A data da observação OHLCV é `prices_raw.date`; `inserted_at` é recuperação posterior e não substitui o tempo da observação de mercado. Chaves `(date,ticker)` de mercado à vista não têm duplicatas e `quote_factor` é positivo.

O experimento nunca escreve no banco. Universo, sinais e outcomes são materializados em artefatos separados e hashados.
