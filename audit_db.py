import sys
import sqlite3
from pathlib import Path

# Windows/cp1252 (default do stdout lá, não UTF-8) quebra em qualquer
# emoji/acento antes mesmo do print de erro — mesmo padrão do main.py.
# CLAUDE.md documenta esse exato pitfall ("já mordeu"); achado de
# varredura 2026-09-04.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

db_path = Path("data/stocks.db")

if not db_path.exists():
    print("❌ Erro: O arquivo data/stocks.db não foi encontrado neste diretório!")
    exit(1)

print(True and "--- INICIANDO AUDITORIA DO BANCO DE DADOS ---")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Listar todas as tabelas existentes
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in cursor.fetchall()]

print(f"\n[Tabelas Encontradas]: {len(tables)}")
print("-" * 50)

# 2. Contar linhas de cada tabela para checar integridade
for table in tables:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f" Tabela: {table:<25} | Total de Linhas: {count:,}")

# 3. Tentar ler os metadados da tabela principal de preços se ela existir
if "prices_raw" in tables:
    print("\n" + "-" * 50)
    print("[Análise Temporal de prices_raw]")
    try:
        # Detecta o nome da coluna de data dinamicamente
        cursor.execute("PRAGMA table_info(prices_raw)")
        cols = [c[1] for c in cursor.fetchall()]
        date_col = next((c for c in cols if "data" in c.lower() or "date" in c.lower()), None)
        
        if date_col:
            cursor.execute(f"SELECT MIN({date_col}), MAX({date_col}) FROM prices_raw")
            data_min, data_max = cursor.fetchone()
            print(f" Amostra Inicia em: {data_min}")
            print(f" Amostra Termina em: {data_max}")
    except Exception as e:
        print(f" ⚠️ Não foi possível extrair a janela temporal: {e}")

conn.close()
print("\n--- AUDITORIA CONCLUÍDA ---")