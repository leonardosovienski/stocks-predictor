"""Camada de rede unificada do core: is_transient + with_retry.

Testada sem httpx instalado (o core importa httpx LAZY) — prova que consumidores
stdlib-first vendorizam o net.py sem a dependência pesada.
"""
import asyncio

import pytest

from predictor_core import net


class _HttpErr(Exception):
    def __init__(self, status):
        super().__init__(f"erro {status}")
        self.status_code = status


def test_is_transient_by_status():
    assert net.is_transient(_HttpErr(503)) is True
    assert net.is_transient(_HttpErr(429)) is True
    assert net.is_transient(_HttpErr(404)) is False


def test_is_transient_by_marker():
    assert net.is_transient(Exception("model overloaded, try again")) is True
    assert net.is_transient(Exception("invalid api key")) is False


def test_daily_quota_is_not_transient():
    # tem 'requests per day' (quota diária) — retry não ajuda, NÃO reententar
    assert net.is_transient(Exception("429 requests per day exceeded")) is False


def test_with_retry_recovers_after_transient():
    calls = {"n": 0}

    @net.with_retry(attempts=3, base_delay=0, max_delay=0)
    async def flaky():
        calls["n"] += 1
        if calls["n"] < 2:
            raise _HttpErr(503)
        return "ok"

    assert asyncio.run(flaky()) == "ok"
    assert calls["n"] == 2


def test_with_retry_gives_up_on_non_transient():
    @net.with_retry(attempts=3, base_delay=0, max_delay=0)
    async def boom():
        raise _HttpErr(404)

    with pytest.raises(_HttpErr):
        asyncio.run(boom())
