"""Reserved for the Etapa B adapter (C24.1 ``adapter_paths``).

Empty in Etapa A. Rules (checked by tests/conformance/test_import_closure.py):
nothing outside this package imports it; nothing reachable from the ``stocks-research``
entrypoint imports it; an adapter may call the domain only through the public
``adapter_api`` (``stocks_predictor.research_runner.Circuit.submit_request``).
"""
