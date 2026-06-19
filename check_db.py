import sqlite3

def main():
    conn = None
    try:
        conn = sqlite3.connect('data/stocks.db')
        cursor = conn.cursor()
        print("=== ÚLTIMAS DECISÕES DO MOTOR ===")

        query = '''
            SELECT asof, ticker, signal_value, rank
            FROM decisions
            ORDER BY asof DESC
            LIMIT 15
        '''
        cursor.execute(query)
        rows = cursor.fetchall()
        if not rows:
            print("O motor NUNCA gerou uma decisão em todo o backtest.")
        else:
            for row in rows:
                asof, ticker, signal_value, rank = row
                try:
                    sv = float(signal_value)
                    print(f"Data: {asof} | Ativo: {ticker} | Sinal: {sv:.4f} | Rank: {rank}")
                except Exception:
                    print(f"Data: {asof} | Ativo: {ticker} | Sinal: {signal_value} | Rank: {rank}")

    except Exception as e:
        print(f"Erro ao ler banco: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == '__main__':
    main()
