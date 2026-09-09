"""
End-to-end integration tests. No real API keys are required, and no real network fetch is performed.

Two external dependencies are replaced:
- LLM        -> ReplayChatCompletionClient with scripted replies.
- Live fetch -> fake search_flights returning prepared page text.

The tests run main_advanced.run() and verify seven paths:
  1. date_is_flexible=False + critic review
  2. date_is_flexible=True with three bounded parallel paths + critic skipped
  3. fetch failure -> NO_DATA, no fabricated data
  4. parser returns invalid content -> readable failure fallback, not an uncaught traceback
  5. non-strict date format + date_is_flexible=True -> degrade to one path without crashing
  6. the past part of a date window is clipped
  7. three fetches are actually concurrent, not serial

Run: python test_integration.py
"""

import asyncio
import io
import contextlib
import json

from autogen_core.models import ModelFamily, ModelInfo
from autogen_ext.models.replay import ReplayChatCompletionClient

import fanout
import main_advanced
from tools import _condense, _slice_around_prices

MODEL_INFO = ModelInfo(
    vision=False, function_calling=True, json_output=True,
    family=ModelFamily.UNKNOWN, structured_output=True,
)

PASS, FAIL = [], []


def check(name: str, condition: bool, detail: str = "") -> None:
    (PASS if condition else FAIL).append(name)
    print(f"  {'PASS' if condition else 'FAIL'} {name}" + (f" -- {detail}" if detail and not condition else ""))


FAKE_PAGE_NOISE = "\n".join(f"navigation filter airline time stop baggage item{i}" for i in range(1200))
FAKE_PAGE = _slice_around_prices(
    _condense(
        FAKE_PAGE_NOISE
        + "\nAlaska Airlines\n7:00 am - 3:32 pm\n5h 32m nonstop\n$179\n"
        + "JetBlue\n6:00 am - 2:29 pm\n5h 29m nonstop\n$186\n"
        + FAKE_PAGE_NOISE
    )
)


def make_fake_search(fail: bool = False):
    calls = []

    async def fake_search_flights(departure, destination, date, return_date=None):
        calls.append(date)
        if fail:
            return (
                f"Search URL: https://www.kayak.com/flights/{departure}-{destination}/{date}\n\n"
                "Page content:\n[browserbase_fetch error] Fetch failed: TimeoutError('timeout')"
            )
        return (
            f"Search URL: https://www.kayak.com/flights/{departure}-{destination}/{date}\n\n"
            f"Page content:\n{FAKE_PAGE}"
        )

    return fake_search_flights, calls


def parsed_query_json(flexible: bool, budget=200.0) -> str:
    return json.dumps(
        {
            "departure_iata": "SFO",
            "destination_iata": "JFK",
            "date": "2026-11-05",
            "date_window_start": "2026-11-03" if flexible else None,
            "date_window_end": "2026-11-09" if flexible else None,
            "return_date": None,
            "budget_usd": budget,
            "cabin": None,
            "other_preferences": None,
            "date_is_flexible": flexible,
        }
    )


REPORT_OK = json.dumps(
    {
        "origin": "SFO", "destination": "JFK", "date": "2026-11-05",
        "within_budget": True,
        "options": [{
            "airline": "Alaska Airlines", "departure_time": "7:00 am", "arrival_time": "3:32 pm",
            "duration": "5h 32m", "price_usd": 179.0, "stops": "nonstop",
            "source_strategy": "Strategy A: exact date", "booking_url": None,
        }],
        "notes": "Found options within budget.",
    },
    ensure_ascii=False,
)

REPORT_NO_DATA = json.dumps(
    {
        "origin": "SFO", "destination": "JFK", "date": "2026-11-05",
        "within_budget": False, "options": [], "notes": "Fetch failed; no real flight data was available.",
    },
    ensure_ascii=False,
)


async def run_pipeline(responses, fail_fetch=False):
    """Run main_advanced.run() once and return captured stdout plus requested fetch dates."""
    client = ReplayChatCompletionClient(responses, model_info=MODEL_INFO)
    fake_search, calls = make_fake_search(fail=fail_fetch)

    original_build, original_search = main_advanced.build_model_client, fanout.search_flights
    main_advanced.build_model_client = lambda: client
    fanout.search_flights = fake_search
    try:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            await main_advanced.run("Find flights from SFO to JFK on November 5 within a $200 budget")
        return buf.getvalue(), calls
    finally:
        main_advanced.build_model_client = original_build
        fanout.search_flights = original_search


async def case_fixed_date_with_critic():
    print("\n[Integration 1] date_is_flexible=False, one search path, critic review")
    out, calls = await run_pipeline([
        parsed_query_json(flexible=False),
        "Extracted results: Alaska $179 nonstop; JetBlue $186 nonstop",
        "Candidates: 1. Alaska $179  2. JetBlue $186",
        "budget_critic_agent",
        "APPROVED Both are within the $200 budget.",
        REPORT_OK,
    ])
    check("one fetch was launched", len(calls) == 1, f"actual {calls}")
    check("fetch used the user-specified date", calls == ["2026-11-05"], str(calls))
    check("printed dynamic decision 1", "dynamic decision 1" in out and "planned 1 search path" in out)
    check("printed actual path", "Actual SelectorGroupChat path" in out)
    check("recognized critic review", "chose critic review" in out)
    check("printed structured report", "Final structured report (FlightSearchReport)" in out)
    check("report includes a real airline", "Alaska Airlines" in out)
    check("printed staged token usage", "Token usage (advanced point 4: observability)" in out)
    check("printed actual model-client total", "Actual model-client total" in out)
    check("printed orchestration cost", "dynamic orchestration cost" in out)
    check("pipeline was not interrupted", "Run interrupted" not in out)


async def case_flexible_date_skip_critic():
    print("\n[Integration 2] date_is_flexible=True, three bounded parallel paths, critic skipped")
    out, calls = await run_pipeline([
        parsed_query_json(flexible=True, budget=None),
        "Extracted results A: Alaska $179 nonstop",
        "Extracted results B: JetBlue $186 nonstop",
        "Extracted results C: Delta $191 nonstop",
        "Candidates: 1. Alaska $179  2. JetBlue $186",
        "summarizer_agent",
        REPORT_OK,
    ])
    check("three fetches were launched", len(calls) == 3, f"actual {calls}")
    check("range plan kept start, preferred date, and end", calls == ["2026-11-03", "2026-11-05", "2026-11-09"], str(calls))
    check("printed bounded three-path decision", "planned 3 search path" in out)
    check("recognized critic skip", "skipped critic review" in out)
    check("actual path has no critic", "budget_critic_agent" not in out.split("Actual SelectorGroupChat path: ")[1].split("\n")[0])
    check("printed structured report", "Final structured report (FlightSearchReport)" in out)
    check("pipeline was not interrupted", "Run interrupted" not in out)


async def case_fetch_failed():
    print("\n[Integration 3] fetch failure -> NO_DATA, no fabricated data")
    out, calls = await run_pipeline([
        parsed_query_json(flexible=False),
        "Strategy A did not return flight data: fetch timed out.",
        "No usable candidate flights.",
        "budget_critic_agent",
        "NO_DATA Source data is missing, so reranking cannot help.",
        REPORT_NO_DATA,
    ], fail_fetch=True)
    check("debug output showed fetch failure", "[browserbase_fetch error]" in out)
    check("printed structured report", "Final structured report (FlightSearchReport)" in out)
    check("report options are empty", '"options": []' in out)
    check("within_budget is false", '"within_budget": false' in out)
    check("pipeline was not interrupted", "Run interrupted" not in out)


async def case_parser_returns_garbage():
    """Invalid parser content must be caught by the top-level readable fallback."""
    print("\n[Integration 4] parser returns invalid content -> readable fallback")
    raised = None
    try:
        out, calls = await run_pipeline(["this is not JSON"])
    except Exception as exc:  # noqa: BLE001
        raised, out, calls = exc, "", []

    check("run() did not re-raise to caller", raised is None, f"raised {type(raised).__name__}: {raised}")
    check("printed readable interruption", "Run interrupted" in out, out[-300:])
    check("mentioned exception type", "ValidationError" in out, out[-300:])
    check("printed common-cause table", "Common causes" in out)
    check("did not continue to fetch", calls == [], str(calls))


async def case_bad_date_format():
    """Regression: flexible date with non-strict ISO format should degrade to one path."""
    print("\n[Integration 5] non-strict date + flexible=True -> one path, no crash")
    bad_parsed = json.dumps({
        "departure_iata": "SFO", "destination_iata": "JFK",
        "date": "2026-11-5",
        "return_date": None, "budget_usd": None, "cabin": None,
        "other_preferences": None, "date_is_flexible": True,
    })
    out, calls = await run_pipeline([
        bad_parsed,
        "Extracted results: Alaska $179 nonstop",
        "Candidates: 1. Alaska $179",
        "summarizer_agent",
        REPORT_OK,
    ])
    check("did not crash", "Run interrupted" not in out, out[-300:])
    check("degraded to one fetch", len(calls) == 1, f"actual {calls}")
    check("printed degradation note", "Flexible-date planning produced one usable date" in out)
    check("still produced structured report", "Final structured report (FlightSearchReport)" in out)


async def case_past_date():
    """The past part of a window is clipped, leaving only today's valid path."""
    print("\n[Integration 6] past part of date window is clipped")
    import datetime as _dt

    today = _dt.date.today().isoformat()
    parsed = json.dumps({
        "departure_iata": "SFO", "destination_iata": "JFK",
        "date": today,
        "date_window_start": (_dt.date.today() - _dt.timedelta(days=2)).isoformat(),
        "date_window_end": today,
        "return_date": None, "budget_usd": None, "cabin": None,
        "other_preferences": None, "date_is_flexible": True,
    })
    out, calls = await run_pipeline([
        parsed,
        "Extracted results: Alaska $179 nonstop",
        "Candidates: 1. Alaska $179",
        "summarizer_agent",
        REPORT_OK,
    ])
    check("did not crash", "Run interrupted" not in out, out[-300:])
    check("searched only one path", calls == [today], f"actual {calls}")


async def case_really_parallel():
    """Validate that all planned fetches overlap rather than running serially."""
    print("\n[Integration 7] three fetches are actually concurrent")
    inflight = {"now": 0, "peak": 0}

    async def timed_search(departure, destination, date, return_date=None):
        inflight["now"] += 1
        inflight["peak"] = max(inflight["peak"], inflight["now"])
        await asyncio.sleep(0.05)
        inflight["now"] -= 1
        return f"Search URL: x\n\nPage content:\n{FAKE_PAGE}"

    client = ReplayChatCompletionClient([
        parsed_query_json(flexible=True, budget=None),
        "Extracted results A: Alaska $179",
        "Extracted results B: JetBlue $186",
        "Extracted results C: Delta $191",
        "Candidates: 1. Alaska $179",
        "summarizer_agent",
        REPORT_OK,
    ], model_info=MODEL_INFO)

    orig_build, orig_search = main_advanced.build_model_client, fanout.search_flights
    main_advanced.build_model_client = lambda: client
    fanout.search_flights = timed_search
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            await main_advanced.run("SFO to JFK around November 5")
    finally:
        main_advanced.build_model_client = orig_build
        fanout.search_flights = orig_search

    check("three fetches overlapped with peak concurrency 3", inflight["peak"] == 3, f"peak {inflight['peak']}")


async def main():
    print("=" * 70)
    print("FlightFinder Pro Advanced - end-to-end integration tests with fake LLM and fake fetch")
    print("=" * 70)

    await case_fixed_date_with_critic()
    await case_flexible_date_skip_critic()
    await case_fetch_failed()
    await case_parser_returns_garbage()
    await case_bad_date_format()
    await case_past_date()
    await case_really_parallel()

    print("\n" + "=" * 70)
    print(f"Passed {len(PASS)} checks, failed {len(FAIL)} checks")
    if FAIL:
        for name in FAIL:
            print(f"  FAIL {name}")
        raise SystemExit(1)
    print("All checks passed")


if __name__ == "__main__":
    asyncio.run(main())
