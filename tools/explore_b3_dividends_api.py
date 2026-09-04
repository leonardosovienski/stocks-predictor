"""Script AD-HOC (não faz parte do pacote) — explora o endpoint de proventos
da B3 (`sistemaswebb3-listados.b3.com.br`) pra UM ticker, pra confirmar
formato/cobertura antes de desenhar uma ingestão real (fonte alternativa
pra 2023-2026, onde a CVM/FRE não tem mais o dataset — ver HANDOFF
2026-09-04).

NÃO decide nem ingere nada — só imprime a resposta crua pra revisão
humana. Baseado em padrões documentados publicamente para essa API (não
verificado neste sandbox — rede bloqueada para b3.com.br).

Uso: python tools/explore_b3_dividends_api.py PETR4
"""
import base64
import json
import sys
import urllib.request

BASE = "https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall"


def _b64(payload: dict) -> str:
    return base64.b64encode(json.dumps(payload).encode()).decode()


def fetch_corporate_actions(ticker: str):
    """Tenta alguns padrões de endpoint documentados publicamente para
    'Dividendos e Outros Eventos Corporativos' — nenhum verificado nesta
    sessão (sem rede). Imprime o que der certo, ou o erro de cada
    tentativa, para você decidir qual (se algum) é o real."""
    attempts = [
        ("GetListedSupplementCash",
         f"{BASE}/GetListedSupplementCash/{_b64({'issuingCompany': ticker, 'language': 'pt-br'})}"),
        ("GetDetail",
         f"{BASE}/GetDetail/{_b64({'issuingCompany': ticker, 'language': 'pt-br'})}"),
    ]
    for name, url in attempts:
        print(f"\n=== tentativa: {name} ===\n{url}")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read().decode("utf-8", errors="replace")
                print(f"status {resp.status}, {len(body)} bytes")
                print(body[:2000])
        except Exception as e:
            print(f"FALHOU: {e!r}")


if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "PETR4"
    fetch_corporate_actions(ticker)
