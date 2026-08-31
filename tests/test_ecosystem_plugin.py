from stocks_predictor.ecosystem_plugin import PLUGIN


def test_ecosystem_plugin_contract_shape():
    health = PLUGIN.health()
    caps = PLUGIN.capabilities()
    assert health["domain"] == "stocks"
    assert health["status"] == "WAITING"
    assert caps["domain"] == "stocks"
    assert caps["supports_prediction"] is False
    assert caps["scientific_status"] == "M0"
    assert caps["economic_status"] == "NOT_DEFINED"
    assert caps["capital_permission"] == "FORBIDDEN"
