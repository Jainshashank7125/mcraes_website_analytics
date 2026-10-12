"""Tests for AgencyAnalyticsClient: daily-granularity chunking, rate-limit retry, partial-list safety."""
import asyncio
from datetime import date, datetime, timedelta

import httpx
import pytest

from app.services import agency_analytics_client as aac
from app.services.agency_analytics_client import (
    AgencyAnalyticsClient,
    AgencyAnalyticsRateLimited,
    MAX_DAILY_RANGE_DAYS,
    daily_date_chunks,
    _keep_daily_rows,
)


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(aac.settings, "AGENCY_ANALYTICS_API_KEY", "test-key", raising=False)

    async def no_sleep(_):
        return None

    monkeypatch.setattr(aac.asyncio, "sleep", no_sleep)
    return AgencyAnalyticsClient()


def run(coro):
    return asyncio.run(coro)


def _days(start, end):
    return (date.fromisoformat(end) - date.fromisoformat(start)).days + 1


# ---------- chunking ----------

@pytest.mark.parametrize("start,end", [
    ("2026-09-12", "2026-10-12"), ("2026-08-01", "2026-10-12"), ("2026-10-12", "2026-10-12"),
    ("2026-09-01", "2026-09-30"), ("2025-01-01", "2026-10-12"),
])
def test_chunks_are_contiguous_and_within_daily_limit(start, end):
    chunks = daily_date_chunks(start, end)
    assert chunks[0][0] == start and chunks[-1][1] == end
    assert all(_days(a, b) <= MAX_DAILY_RANGE_DAYS for a, b in chunks)
    for (_, prev_end), (next_start, _) in zip(chunks, chunks[1:]):
        assert date.fromisoformat(next_start) == date.fromisoformat(prev_end) + timedelta(days=1)


def test_chunks_empty_when_start_after_end():
    assert daily_date_chunks("2026-10-12", "2026-10-01") == []


def test_keep_daily_rows_drops_monthly_summaries():
    rows = [{"date": "2026-09"}, {"date": "2026-09-30"}, {"date": "2026-10"}, {"date": "2026-10-01"}]
    assert [r["date"] for r in _keep_daily_rows(rows, "t")] == ["2026-09-30", "2026-10-01"]


# ---------- rate-limit retry ----------

def test_request_retries_rate_limit_then_succeeds(client, monkeypatch):
    calls = {"n": 0}

    async def flaky(body):
        calls["n"] += 1
        if calls["n"] < 3:
            raise AgencyAnalyticsRateLimited("Too many requests")
        return {"results": {"rows": [1]}}

    monkeypatch.setattr(client, "_request_once", flaky)
    assert run(client._request({}))["results"]["rows"] == [1]
    assert calls["n"] == 3


def test_request_gives_up_after_max_retries(client, monkeypatch):
    calls = {"n": 0}

    async def always(body):
        calls["n"] += 1
        raise AgencyAnalyticsRateLimited("Too many requests")

    monkeypatch.setattr(client, "_request_once", always)
    with pytest.raises(AgencyAnalyticsRateLimited):
        run(client._request({}))
    assert calls["n"] == aac.RATE_LIMIT_MAX_RETRIES + 1


def test_non_rate_limit_errors_are_not_retried(client, monkeypatch):
    calls = {"n": 0}

    async def boom(body):
        calls["n"] += 1
        raise ValueError("bad request")

    monkeypatch.setattr(client, "_request_once", boom)
    with pytest.raises(ValueError):
        run(client._request({}))
    assert calls["n"] == 1


_REAL_ASYNC_CLIENT = httpx.AsyncClient


def _mock_httpx(monkeypatch, handler):
    monkeypatch.setattr(aac.httpx, "AsyncClient",
                        lambda **kw: _REAL_ASYNC_CLIENT(transport=httpx.MockTransport(handler), **kw))


def test_request_once_classifies_responses(client, monkeypatch):
    # 200 + 429 error body (what Agency Analytics actually sends) -> rate limited
    _mock_httpx(monkeypatch, lambda r: httpx.Response(200, json={
        "status": "error", "code": 429, "results": {"messages": ["Too many requests."]}}))
    with pytest.raises(AgencyAnalyticsRateLimited):
        run(client._request_once({}))

    # real HTTP 429 -> rate limited
    _mock_httpx(monkeypatch, lambda r: httpx.Response(429, text="slow down"))
    with pytest.raises(AgencyAnalyticsRateLimited):
        run(client._request_once({}))

    # empty / non-JSON body (seen with rate limiting) -> treated as transient
    _mock_httpx(monkeypatch, lambda r: httpx.Response(200, text=""))
    with pytest.raises(AgencyAnalyticsRateLimited):
        run(client._request_once({}))

    # other API error -> plain Exception, NOT retried as rate limiting
    _mock_httpx(monkeypatch, lambda r: httpx.Response(200, json={
        "status": "error", "code": 400, "results": {"messages": ["bad filter"]}}))
    with pytest.raises(Exception) as exc:
        run(client._request_once({}))
    assert not isinstance(exc.value, AgencyAnalyticsRateLimited)

    # success passes through
    _mock_httpx(monkeypatch, lambda r: httpx.Response(200, json={"status": "success", "results": {"rows": [{"date": "2026-10-01"}]}}))
    assert run(client._request_once({}))["results"]["rows"][0]["date"] == "2026-10-01"


# ---------- fetchers ----------

def _capture(client, monkeypatch):
    bodies = []

    async def fake(body):
        bodies.append(body)
        flt = {k: v for f in body["filters"] for k, v in f.items()}
        s = flt["start_date"]["$greaterthanorequal_comparison"]
        e = flt["end_date"]["$lessthanorequal_comparison"]
        n = _days(s, e)
        rows = [{"date": (date.fromisoformat(s) + timedelta(days=i)).isoformat(), "google_ranking": 5} for i in range(n)]
        return {"results": {"rows": rows}}

    monkeypatch.setattr(client, "_request", fake)
    return bodies


def _range(body):
    flt = {k: v for f in body["filters"] for k, v in f.items()}
    return flt["start_date"]["$greaterthanorequal_comparison"], flt["end_date"]["$lessthanorequal_comparison"]


def test_default_window_is_one_daily_request(client, monkeypatch):
    bodies = _capture(client, monkeypatch)
    rows = run(client.get_keyword_rankings(1))
    assert len(bodies) == 1
    s, e = _range(bodies[0])
    assert _days(s, e) == aac.DEFAULT_SYNC_LOOKBACK_DAYS <= MAX_DAILY_RANGE_DAYS
    assert e == datetime.now().strftime("%Y-%m-%d")
    assert len(rows) == aac.DEFAULT_SYNC_LOOKBACK_DAYS


def test_long_range_is_chunked_and_returns_every_day_once(client, monkeypatch):
    bodies = _capture(client, monkeypatch)
    for fetch in (client.get_keyword_rankings, client.get_campaign_rankings):
        bodies.clear()
        rows = run(fetch(1, start_date="2026-08-01", end_date="2026-10-12"))
        assert len(bodies) == 3
        assert all(_days(*_range(b)) <= MAX_DAILY_RANGE_DAYS for b in bodies)
        dates = [r["date"] for r in rows]
        assert len(dates) == len(set(dates)) == _days("2026-08-01", "2026-10-12")


def test_monthly_rows_from_api_are_never_returned(client, monkeypatch):
    async def monthly(body):
        return {"results": {"rows": [{"date": "2026-09"}, {"date": "2026-10"}]}}

    monkeypatch.setattr(client, "_request", monthly)
    assert run(client.get_keyword_rankings(1, start_date="2026-09-01", end_date="2026-09-30")) == []


def test_keyword_list_failure_raises_instead_of_returning_partial(client, monkeypatch):
    calls = {"n": 0}

    async def page(campaign_id, limit=50, offset=0):
        calls["n"] += 1
        if calls["n"] == 1:
            return [{"id": i} for i in range(500)]  # full page -> another page is requested
        raise AgencyAnalyticsRateLimited("Too many requests")

    monkeypatch.setattr(client, "get_campaign_keywords", page)
    with pytest.raises(AgencyAnalyticsRateLimited):
        run(client.get_all_campaign_keywords(1))
