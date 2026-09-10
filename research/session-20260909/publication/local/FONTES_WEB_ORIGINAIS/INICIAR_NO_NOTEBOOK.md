# Iniciar o Stocks Predictor no Codex do notebook

Exemplo para notebook Windows. Ajuste os caminhos se escolher outra pasta.

1. Copie a pasta inteira STOCKS_MIGRACAO_MAIN_20260908 para C:\Stocks\STOCKS_MIGRACAO_MAIN_20260908. Ela deve conter DADOS_STOCKS.zip, DADOS_STOCKS.json, CODIGO_MAIN.bundle, DEPENDENCIAS e os demais arquivos. Reserve pelo menos 36 GB livres antes de copiar e restaurar. O ZIP sozinho não basta.
2. Com Git disponível, se ainda não houver checkout no notebook, execute no PowerShell:

```powershell
git clone --branch main https://github.com/leonardosovienski/stocks-predictor.git C:\Stocks\codigo
```

3. No Codex, adicione C:\Stocks\codigo como projeto local. Em Edit project / Add folder, anexe também C:\Stocks e mantenha codigo como pasta principal. Isso fornece o contexto do repositório e acesso à pasta de migração e ao destino dos dados. Inicie uma nova tarefa em modo Local, na main.
4. Cole a mensagem abaixo. Se os caminhos forem diferentes, substitua-os antes de enviar. O Codex pode executar a restauração; não extraia o ZIP de dados pelo Explorer, pois ele usa objetos deduplicados e precisa do restaurador do projeto.

O modo Local trabalha na pasta atual do projeto, e a pasta principal define as operações Git e a descoberta de AGENTS.md. Fontes: [documentação oficial OpenAI sobre projetos](https://learn.chatgpt.com/docs/projects) e [ambientes do Codex](https://learn.chatgpt.com/docs/environments/modes).

## Mensagem para colar

```text
Estou continuando o Stocks Predictor em outro computador. Não dependa do chat antigo. Sua primeira tarefa é concluir a migração e validar o projeto neste notebook.

Caminhos neste computador:
- Código: C:\Stocks\codigo
- Pacote completo: C:\Stocks\STOCKS_MIGRACAO_MAIN_20260908
- Destino dos dados: C:\Stocks\dados

O repositório é https://github.com/leonardosovienski/stocks-predictor, somente branch main. O último estado transferido foi 99f8751. Se houver commits posteriores, identifique-os e preserve-os; não faça reset nem recrie branches antigas.

Leia AGENTS.md, docs/DESIGN.md inteiro, o início de HANDOFF.md, STOCKS_CURRENT_STATE.md, docs/continuation/MIGRACAO_MAIN.md e MIGRACAO_VERIFICADA.json. No pacote, leia LEIA_PRIMEIRO.md e ENTREGA_FINAL.json. Os caminhos antigos C:\Users\Superleo13 e as referências à branch fix são históricos: use o mapeamento de migração, sem reescrever fontes ou manifestos para trocar caminhos.

Execute a restauração com tools/data_transfer.py, verificando DADOS_STOCKS.zip junto de DADOS_STOCKS.json. Use um destino novo; se os dados já existirem, confira o recibo e a integridade sem sobrescrever. Não publique bancos e dados brutos no GitHub.

Confira sistema e arquitetura. Use Python 3.13 global, sem venv nem instalação do Core via pip. Configure as bibliotecas fornecidas conforme o guia, priorizando Core 3.2.0 de DEPENDENCIAS/research-runtime. O Core 3.1.0 da cópia das bibliotecas globais não deve prevalecer. Se faltar um pré-requisito ou houver incompatibilidade de sistema, informe exatamente qual.

Valide os bancos em somente leitura, rode a suíte apropriada em ambiente limpo e reproduza a auditoria de fontes 14. Os 777 testes e os 25 bancos verificados são resultados do PC antigo: reporte o que efetivamente verificar aqui.

Estado preservado: fontes 14 validadas, ainda separadas da entrada canônica 13; faltam 24 datas, 52 líquidos, 28 entradas societárias e 1.248 inventários completos. Lucro e projeção continuam null/BLOCKED_MISSING_EVIDENCE. H1–H20 congeladas; contagens administrativas 53/55. Não observe novos retornos reais nem execute scripts históricos automaticamente.

Preserve fontes, bancos, ledgers e quarentenas. Use cópias temporárias nos testes. Não coordene outros agentes, envie ordens ou contrate serviços. Execute os passos rotineiros de migração sem pedir confirmação repetida.

Ao terminar, informe os caminhos efetivos, commit, versões Python/Core, verificações realizadas, falhas restantes e a próxima tarefa concreta para continuar a pesquisa. Não afirme que a migração ou os testes passaram sem executar as verificações neste computador.
```
