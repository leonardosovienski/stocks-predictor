"""ST-F001 regression: the IANA time zone used by External Intelligence resolves on every OS.

On Windows there is no system time zone database; without the tzdata distribution
`ZoneInfo("America/Sao_Paulo")` raised at import time and took the operational
entrypoint (python -m stocks_predictor) and External Intelligence down.
"""

import importlib
from importlib.metadata import requires
from zoneinfo import ZoneInfo


def test_sao_paulo_time_zone_resolves():
    assert ZoneInfo("America/Sao_Paulo").key == "America/Sao_Paulo"


def test_operational_entrypoint_and_external_intelligence_import():
    importlib.import_module("stocks_predictor.external_intelligence")
    importlib.import_module("stocks_predictor.operations")


def test_tzdata_is_a_declared_runtime_dependency():
    assert any(item.split(";")[0].replace(" ", "").startswith("tzdata") for item in requires("stocks-predictor") or [])
