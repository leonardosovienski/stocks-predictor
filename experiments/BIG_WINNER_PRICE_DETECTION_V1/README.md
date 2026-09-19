# BIG_WINNER_PRICE_DETECTION_V1

Experimento histórico independente e somente-preço. Ele preserva, sem alterar, o resultado `INCONCLUSIVE_DATA_QUALITY` da V1 de retorno total e responde uma pergunta diferente: se sete mecanismos price/volume já existentes enriqueciam seus rankings com ações que depois valorizavam ao menos 30% em 12 meses.

O protocolo é congelado antes dos outcomes. A ordem reproduzível é:

```powershell
$py = 'C:\Users\leona\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $py .\experiments\BIG_WINNER_PRICE_DETECTION_V1\run.py signals
& $py .\experiments\BIG_WINNER_PRICE_DETECTION_V1\run.py outcomes
& $py .\experiments\BIG_WINNER_PRICE_DETECTION_V1\run.py evaluate
& $py -m unittest discover .\experiments\BIG_WINNER_PRICE_DETECTION_V1\tests -v
```

Cada salto corporativo não resolvido afeta somente o ticker-horizonte correspondente. Unknown não vira false; os resultados incluem complete case e limites de identificação parcial.
