# Reprodução local das correções

Use o Python 3.13 global e as dependências já disponíveis no projeto. Não instalar a wheel ou criar venv. A wheel fornecida foi extraída e testada como diretório de importação. A cópia dos arquivos `stocks_predictor/` identifica exatamente o código testado.

`AUDITAR_PRONTIDAO.ps1 -OutputFile CAMINHO_NOVO.json` verifica as fontes locais e grava as pendências H20. **Saída 2 é o resultado esperado de cobertura incompleta; lucro não é emitido.** `REPRODUZIR_VERIFICADO.ps1 -OutputFile OUTRO_CAMINHO_NOVO.json` reproduz a comparação antiga protegida; o resultado continua sendo um diagnóstico de marcações.

Ambos usam a raiz durável especificada nos scripts. Se os arquivos da pesquisa original não estiverem disponíveis nessa raiz, a reprodução deve parar; os scripts não baixam, reconstroem ou aprovam fontes. A comparação antiga exige os extratos históricos e seus hashes originais. Os arquivos de saída precisam ser novos.

Para os testes completos no checkout, com PYTHONPATH incluindo o checkout e os diretórios existentes `work/runtime` e `work/checks`, executar:

```powershell
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
py -3.13 -m pytest tests research/session-20260908/h20-profit-test/test_h20_profit_comparison.py research/session-20260908/chat-review/test_h20_evidence_integrity.py -q
```

A árvore Git precisa estar limpa e commitada, pois o Core vincula os atestados sintéticos à versão do código. Não desativar esse requisito. `verify_remediation.py` registra a validação adicional desta etapa e suas saídas; cria diretórios novos e não deve ser repetido sobre os mesmos nomes já existentes. Os testes em `tests/` são dados sintéticos e podem ser executados contra o código ou a wheel extraída. Não são projeções de lucro.

Os executores anteriores são acervo histórico. Os caminhos indicados acima são os atuais. O protocolo, o relatório, os logs, a observação de prontidão e o manifesto acompanham o pacote.
