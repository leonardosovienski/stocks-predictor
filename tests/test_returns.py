"""M3 — matriz de retornos mensais."""
import returns


def test_month_end_dates():
    dates = ["2024-01-10", "2024-01-31", "2024-02-15", "2024-02-29", "2024-03-01"]
    assert returns.month_end_dates(dates) == ["2024-01-31", "2024-02-29", "2024-03-01"]


def test_monthly_returns():
    mr = returns.monthly_returns(["2024-01-31", "2024-02-29", "2024-03-29"],
                                 [100.0, 110.0, 99.0])
    assert mr[0][0] == "2024-02-29" and abs(mr[0][1] - 0.10) < 1e-9
    assert abs(mr[1][1] + 0.10) < 1e-9


def test_returns_matrix():
    m = returns.returns_matrix({"A": (["2024-01-31", "2024-02-29"], [10.0, 11.0])})
    assert abs(m["A"]["2024-02-29"] - 0.10) < 1e-9
