"""Adapter mínimo do Stocks para o registry do ecosystem-predictor.

A linha H21 ainda está em pesquisa condicional. O adapter não transforma testes em prontidão,
não cria sinal econômico e não autoriza capital.
"""

from __future__ import annotations


class StocksPredictorPlugin:
    name = "stocks-predictor"
    domain = "stocks"

    def health(self) -> dict[str, object]:
        return {
            "domain": self.domain,
            "status": "WAITING",
            "version": "0.2.0",
            "details": {
                "mode": "research",
                "active_line": "H21_BOVA11_CONDITIONAL_RESEARCH",
                "adapter": "plugin-v1",
            },
        }

    def capabilities(self) -> dict[str, object]:
        return {
            "domain": self.domain,
            "supports_prediction": False,
            "supports_settlement": False,
            "supports_collection": False,
            "scientific_status": "DISCOVERY_INCONCLUSIVE",
            "predictive_status": "NO_VALIDATED_NET_EDGE",
            "economic_status": "NO_GO",
            "capital_permission": "FORBIDDEN",
            "extra": {
                "mode": "research",
                "active_line": "H21_BOVA11_CONDITIONAL_RESEARCH",
                "net_historical_replay_complete": False,
                "historical_lines_preserved": ["H1-H20", "predictor-rj"],
                "source_of_scientific_truth": "STOCKS_CURRENT_STATE.md",
            },
        }


PLUGIN = StocksPredictorPlugin()
