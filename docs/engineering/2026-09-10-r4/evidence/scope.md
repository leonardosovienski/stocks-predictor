# Engenharia R4 — escopo antes das mudanças

Base: 0e9c48a87ff67bbd8d71fe5b9156799ba9bd8807 (main limpa, PR74 integrado).
Pedido: corrigir erros, melhorar infraestrutura e otimizar o projeto.

Trabalho individual. Sem novas hipóteses econômicas, coleta de mercado, ordens,
automação recorrente, instalações Windows ou alteração dos acervos congelados.

Prioridades encontradas por leitura de código:
1. Carga COTAHIST mantém o arquivo inteiro em memória, conta duplicatas ignoradas
   como inserções, ignora conflitos de conteúdo e faz commit da transação alheia.
2. Argumentos de universo/paper podem criar/migrar banco antes da rejeição.
3. Falha de migração não fecha conexão; diagnóstico de status depende do Core ausente.
4. CI não trava lock, não tem timeout/concurrency, só testa3.13 embora suporte3.14,
   suprime erros de tipo de argumentos e mede cobertura sem mínimo efetivo.

Critérios: regressões que falhem antes; ingestão incremental com memória limitada,
atomicidade e preservação de bytes existentes; benchmark fixo sintético (sem medir
retorno) antes/depois; igualdade do replay H21; suite/Linux/Core e wheel por SHA;
recibos congelados mantidos; merge após checks. Aumento de abrangência dos checks
pode exigir correções de tipagem, não desligar diagnósticos para obter verde.

Benchmark previsto: fluxo gerado de100mil cotações,95%fora do filtro spot, mesmos
dados e banco sintético em memória,3repetições por versão. Medir tempo e picoPython
separadamente; nenhuma promessa prévia de aceleração. Verificar contagens e digest
das linhas inseridas. Também provar rollback após falha tardia do iterador.
