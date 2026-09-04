import sys
import sqlite3
from pathlib import Path

db_path = Path("data/stocks.db")
if not db_path.exists():
    print(f"Erro: {db_path} não existe (rode a partir da raiz do projeto, "
          "após algum ingest).")
    sys.exit(1)
conn = sqlite3.connect(db_path)

print("=== DIAGNÓSTICO SISTÊMICO DO UNIVERSO ===")

# 1. Verificar formato exato de armazenamento dos Tickers
tickers = [r[0] for r in conn.execute("SELECT DISTINCT ticker FROM prices_raw LIMIT 5")]
print(f"\n[1] Formato exato dos Tickers no banco (representação literal):")
for t in tickers:
    print(f"  - Ticker: {repr(t)} | Tamanho real: {len(t)} caracteres")

# 2. Testar a existência das grandes Blue Chips
print(f"\n[2] Verificando presença de Blue Chips icônicas:")
for target in ['PETR4', 'VALE3', 'ITUB4']:
    exact = conn.execute("SELECT COUNT(*) FROM prices_raw WHERE ticker = ?", (target,)).fetchone()[0]
    like = conn.execute("SELECT COUNT(*) FROM prices_raw WHERE ticker LIKE ?", (f"%{target}%",)).fetchone()[0]
    print(f"  - {target} -> Busca Exata: {exact} linhas | Busca por aproximação (LIKE): {like} linhas")

# 3. Testar o comportamento da query temporal do universe.py
most_frequent = conn.execute(
    "SELECT ticker, COUNT(*) as c FROM prices_raw GROUP BY ticker ORDER BY c DESC LIMIT 1"
).fetchone()

if most_frequent:
    tk, count = most_frequent
    print(f"\n[3] Ticker com maior volume de dados na base: {repr(tk)} ({count} linhas)")
    
    # Amostra do formato da data
    sample_date = conn.execute(f"SELECT date FROM prices_raw WHERE ticker=? LIMIT 1", (tk,)).fetchone()[0]
    print(f"  - Formato real da string de data no banco: {repr(sample_date)}")
    
    # Simulação da query do universe.py — precisa do MESMO filtro market_type
    # = SPOT_MARKET ("010") que rank_universe() sempre aplica (universe.py);
    # sem ele, o diagnóstico conta linhas de mercados que a query real nunca
    # vê (ex.: leilão), escondendo o motivo real de um ticker sumir do
    # universo (achado de varredura 2026-09-04).
    asof = "2024-12-30"
    vols = [r[0] for r in conn.execute(
        "SELECT volume_fin FROM prices_raw WHERE ticker=? AND date < ? "
        "AND market_type = '010' ORDER BY date",
        (tk, asof))]
    print(f"  - Executando: WHERE ticker={repr(tk)} AND date < {repr(asof)} "
          "AND market_type = '010'")
    print(f"  - Resultado: {len(vols)} registros de volume retornados.")

conn.close()
print("\n=== FIM DO DIAGNÓSTICO ===")