"""M2+ — Analista somente-leitura (IA consultiva). NÃO tem dependência do pipeline.

Regras invioláveis (§9b do design):
- NUNCA escreve no banco.
- NUNCA resolve quarentena — sugere apenas.
- Saída vai para reports/ai/ com data, como artefato descartável.
- Deletar este arquivo não quebra nenhum teste do sistema de previsão.
"""
raise NotImplementedError("M2+")
