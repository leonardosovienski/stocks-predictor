"""Adapter mínimo do Stocks/RJ para o registry do ecosystem-predictor.

A linha RJ ainda está em pesquisa. O adapter não transforma M0 em readiness,
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
            "version": "0.1.0",
            "details": {
                "mode": "research",
                "active_line": "predictor-rj",
                "adapter": "plugin-v1",
            },
        }

    def capabilities(self) -> dict[str, object]:
        return {
            "domain": self.domain,
            "supports_prediction": False,
            "supports_settlement": False,
            "supports_collection": False,
            "scientific_status": "M0",
            "predictive_status": "NOT_TESTED_REAL_DATA",
            "economic_status": "NOT_DEFINED",
            "capital_permission": "FORBIDDEN",
            "extra": {
                "mode": "research",
                "active_line": "predictor-rj",
                "source_of_scientific_truth": "STOCKS_CURRENT_STATE.md",
            },
        }


PLUGIN = StocksPredictorPlugin()
