"""
Offline orchestration tests. No real API keys are required.

ReplayChatCompletionClient replaces all LLM replies with scripted responses, then runs SelectorGroupChat
end to end to verify that each path completes correctly.

Run: python test_offline.py
"""

import asyncio
import datetime
import json
import os

from autogen_core.models import ModelFamily, ModelInfo
from autogen_ext.models.replay import ReplayChatCompletionClient

from agents_advanced import _critic_verdict, build_advanced_team, make_candidate_func, make_selector_func
from fanout import plan_search_dates
from schemas import FlightSearchReport, ParsedQuery
from tools import _condense, _slice_around_prices, PRICE_PATTERN, kayak_search_url

MODEL_INFO = ModelInfo(
    vision=False,
    function_calling=True,
    json_output=True,
    family=ModelFamily.UNKNOWN,
    structured_output=True,
)

PASS, FAIL = [], []


def check(name: str, condition: bool, detail: str = "") -> None:
    (PASS if condition else FAIL).append(name)
    print(f"  {'PASS' if condition else 'FAIL'} {name}" + (f" -- {detail}" if detail and not condition else ""))


def report(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False)


GOOD_REPORT = report(
    {
        "origin": "SFO",
        "destination": "JFK",
        "date": "2026-11-05",
        "within_budget": True,
        "options": [
            {
                "airline": "Alaska Airlines",
                "departure_time": "7:00 am",
                "arrival_time": "3:32 pm",
                "duration": "5h 32m",
                "price_usd": 179.0,
                "stops": "nonstop",
                "source_strategy": "Strategy A: exact date",
                "booking_url": None,
            }
        ],
        "notes": "Found options within budget.",
    }
)

NO_DATA_REPORT = report(
    {
        "origin": "SFO",
        "destination": "JFK",
        "date": "2026-11-05",
        "within_budget": False,
        "options": [],
        "notes": "Fetch failed; no real flight data was available.",
    }
)

TASK = "User preferences: budget 200.0 USD, cabin unspecified, other preferences: none\n\n[Strategy A: 2026-11-05 exact date] Alaska $179"


async def run_team(responses):
    client = ReplayChatCompletionClient(responses, model_info=MODEL_INFO)
    team = build_advanced_team(client)
    result = await team.run(task=TASK)
    return result, [m.source for m in result.messages]


async def scenario_skip_critic():
    """No user preferences -> model skips critic and finalizes directly."""
    print("\n[Scenario 1] Model skips critic review (merge -> summarizer)")
    result, path = await run_team(
        [
            "Candidate flights: 1. Alaska Airlines $179 nonstop",
            "summarizer_agent",
            GOOD_REPORT,
        ]
    )
    check("Correct path when critic is skipped", path == ["user", "merge_ranker_agent", "summarizer_agent"], str(path))
    check("Final message is FlightSearchReport", isinstance(result.messages[-1].content, FlightSearchReport))


async def scenario_with_critic_approved():
    """Model chooses critic review -> critic APPROVED -> final summary."""
    print("\n[Scenario 2] Critic review passes on the first try")
    result, path = await run_team(
        [
            "Candidate flights: 1. Alaska Airlines $179 nonstop",
            "budget_critic_agent",
            "APPROVED Candidates satisfy the $200 budget.",
            GOOD_REPORT,
        ]
    )
    check(
        "Correct path with critic review",
        path == ["user", "merge_ranker_agent", "budget_critic_agent", "summarizer_agent"],
        str(path),
    )
    check("Final message is FlightSearchReport", isinstance(result.messages[-1].content, FlightSearchReport))


async def scenario_retry_once():
    """Critic RETRY once -> rerank -> critic APPROVED -> final summary."""
    print("\n[Scenario 3] Critic retry loop")
    result, path = await run_team(
        [
            "Candidate flights: 1. Delta $297 nonstop",
            "budget_critic_agent",
            "RETRY All candidates exceed the $200 budget; relax to $300.",
            "Reranked candidates: 1. Delta $297 after relaxed budget",
            "budget_critic_agent",
            "APPROVED Budget was relaxed; this is the closest option.",
            GOOD_REPORT,
        ]
    )
    expected = [
        "user",
        "merge_ranker_agent",
        "budget_critic_agent",
        "merge_ranker_agent",
        "budget_critic_agent",
        "summarizer_agent",
    ]
    check("Correct path with exactly one retry", path == expected, str(path))
    check("Final message is FlightSearchReport", isinstance(result.messages[-1].content, FlightSearchReport))


async def scenario_retry_capped():
    """Two RETRY verdicts -> second one is capped and summary is forced."""
    print("\n[Scenario 4] Retry cap stops the second RETRY")
    result, path = await run_team(
        [
            "Candidate flights: 1. Delta $297",
            "budget_critic_agent",
            "RETRY Over budget; relax to $300.",
            "Reranked candidates: 1. Delta $297",
            "budget_critic_agent",
            "RETRY Still not good; relax to $400.",
            NO_DATA_REPORT,
        ]
    )
    expected = [
        "user",
        "merge_ranker_agent",
        "budget_critic_agent",
        "merge_ranker_agent",
        "budget_critic_agent",
        "summarizer_agent",
    ]
    check("Second RETRY is capped and summary is reached", path == expected, str(path))
    check("Final message is FlightSearchReport", isinstance(result.messages[-1].content, FlightSearchReport))


async def scenario_no_data():
    """Fetch failure -> critic NO_DATA -> no reranking."""
    print("\n[Scenario 5] NO_DATA does not trigger reranking")
    result, path = await run_team(
        [
            "No search path returned real flight data.",
            "budget_critic_agent",
            "NO_DATA Source data is missing, so reranking cannot help.",
            NO_DATA_REPORT,
        ]
    )
    check(
        "NO_DATA goes directly to summarizer",
        path == ["user", "merge_ranker_agent", "budget_critic_agent", "summarizer_agent"],
        str(path),
    )
    final = result.messages[-1].content
    check("Report options are empty", isinstance(final, FlightSearchReport) and final.options == [])
    check("within_budget is False", isinstance(final, FlightSearchReport) and final.within_budget is False)


async def scenario_model_misbehaves():
    """Regression test: model ignores candidate_func and chooses merge_ranker_agent again."""
    print("\n[Scenario 6] Regression: fallback catches out-of-range speaker selection")
    result, path = await run_team(
        [
            "Candidate flights: 1. Alaska Airlines $179",
            "merge_ranker_agent",
            "Reranked again: 1. Alaska Airlines $179",
            "APPROVED Satisfies the budget.",
            GOOD_REPORT,
        ]
    )
    check("Workflow does not deadlock and reaches summarizer", "summarizer_agent" in path, str(path))
    check("Final message is still FlightSearchReport", isinstance(result.messages[-1].content, FlightSearchReport))
    check("Consecutive merge fallback prevents a third merge turn", path.count("merge_ranker_agent") == 2, str(path))
    print(f"     Actual path: {' -> '.join(path)}")


def unit_tests():
    print("\n[Unit tests] Pure function logic")

    check("_critic_verdict: standard RETRY", _critic_verdict("RETRY relax budget") == "RETRY")
    check("_critic_verdict: Markdown bold", _critic_verdict("**RETRY** relax budget") == "RETRY")
    check("_critic_verdict: lowercase", _critic_verdict("retry relax budget") == "RETRY")
    check("_critic_verdict: Markdown heading", _critic_verdict("### RETRY relax budget") == "RETRY")
    check("_critic_verdict: quote marker", _critic_verdict("> RETRY relax budget") == "RETRY")
    check("_critic_verdict: leading newline", _critic_verdict("\n\nRETRY relax") == "RETRY")
    check("_critic_verdict: NO_DATA", _critic_verdict("NO_DATA no data") == "NO_DATA")
    check("_critic_verdict: APPROVED", _critic_verdict("APPROVED good") == "APPROVED")
    check("_critic_verdict: unknown defaults to APPROVED", _critic_verdict("I will check") == "APPROVED")
    check("_critic_verdict: non-string input does not crash", _critic_verdict(None) == "APPROVED")

    sel = make_selector_func()

    class M:
        def __init__(self, source, content=""):
            self.source = source
            self.content = content

    check("selector: empty messages -> merge_ranker", sel([]) == "merge_ranker_agent")
    check("selector: user -> merge_ranker", sel([M("user")]) == "merge_ranker_agent")
    check("selector: after merge -> None for model decision", sel([M("user"), M("merge_ranker_agent")]) is None)
    check(
        "selector: consecutive merge -> fallback to critic",
        sel([M("user"), M("merge_ranker_agent"), M("merge_ranker_agent")]) == "budget_critic_agent",
    )
    check(
        "selector: consecutive merge after critic -> fallback to summarizer",
        sel([M("user"), M("merge_ranker_agent"), M("budget_critic_agent", "RETRY x"), M("merge_ranker_agent"), M("merge_ranker_agent")]) == "summarizer_agent",
    )
    check(
        "selector: first critic RETRY -> merge",
        sel([M("user"), M("merge_ranker_agent"), M("budget_critic_agent", "RETRY relax")]) == "merge_ranker_agent",
    )
    check(
        "selector: second critic RETRY -> capped",
        sel([M("user"), M("merge_ranker_agent"), M("budget_critic_agent", "RETRY a"), M("merge_ranker_agent"), M("budget_critic_agent", "RETRY b")]) == "summarizer_agent",
    )
    check(
        "selector: NO_DATA -> summarizer",
        sel([M("user"), M("merge_ranker_agent"), M("budget_critic_agent", "NO_DATA no data")]) == "summarizer_agent",
    )
    check("selector: after summarizer -> None", sel([M("summarizer_agent")]) is None)

    cand = make_candidate_func()
    check(
        "candidate: after merge, candidates exclude merge itself",
        "merge_ranker_agent" not in cand([M("merge_ranker_agent")]),
    )
    check("candidate: never returns an empty list", all(len(cand(ms)) > 0 for ms in ([], [M("user")], [M("summarizer_agent")])) )

    fixed_today = datetime.date(2026, 10, 1)
    check(
        "date planner: exact request stays one path",
        plan_search_dates("2026-11-05", include_flex_date=False, today=fixed_today) == ["2026-11-05"],
    )
    check(
        "date planner: explicit range is capped and keeps preferred date",
        plan_search_dates("2026-11-05", "2026-11-03", "2026-11-09", True, 3, fixed_today)
        == ["2026-11-03", "2026-11-05", "2026-11-09"],
    )
    check(
        "date planner: short range searches every date",
        plan_search_dates("2026-11-04", "2026-11-03", "2026-11-05", True, 3, fixed_today)
        == ["2026-11-03", "2026-11-04", "2026-11-05"],
    )
    check(
        "date planner: missing window falls back to plus/minus one day",
        plan_search_dates("2026-11-05", include_flex_date=True, today=fixed_today)
        == ["2026-11-04", "2026-11-05", "2026-11-06"],
    )
    check(
        "date planner: past part of a window is clipped",
        plan_search_dates("2026-10-06", "2026-09-28", "2026-10-07", True, 3, fixed_today)
        == ["2026-10-01", "2026-10-06", "2026-10-07"],
    )
    check(
        "date planner: reversed window degrades to preferred date",
        plan_search_dates("2026-11-05", "2026-11-09", "2026-11-03", True, 3, fixed_today)
        == ["2026-11-05"],
    )

    check(
        "kayak_search_url: one-way",
        kayak_search_url("SFO", "JFK", "2026-11-05") == "https://www.kayak.com/flights/SFO-JFK/2026-11-05?currency=USD",
    )
    check(
        "kayak_search_url: round trip",
        "/2026-11-05/2026-11-12?" in kayak_search_url("SFO", "JFK", "2026-11-05", "2026-11-12"),
    )

    noise = "\n".join(f"navigation filter item {i} airline time stop baggage" for i in range(1500))
    page = noise + "\nAlaska Airlines\n7:00 am - 3:32 pm\n5h 32m nonstop\n$179\nJetBlue\n$186\n" + noise
    condensed = _condense(page)
    old_way = condensed[:8000]
    new_way = _slice_around_prices(condensed)
    check("pitfall 1 reproduction: top truncation misses prices", len(PRICE_PATTERN.findall(old_way)) == 0)
    check("pitfall 1 fix: price-anchored slice keeps flights", len(PRICE_PATTERN.findall(new_way)) == 2)
    check("slice result is not too long", len(new_way) <= 8000 + 400)
    check("_slice_around_prices: short text is preserved", "Alaska" in _slice_around_prices("Alaska $179"))
    check("_slice_around_prices: empty string does not crash", isinstance(_slice_around_prices(""), str))
    check("_condense: empty string does not crash", _condense("") == "")
    check("_condense: image syntax is removed", "![" not in _condense("![logo](https://x.com/a.png)\nAlaska $179"))
    check("_condense: links keep visible text only", _condense("[Sign in](https://kayak.com/signin?a=1)") == "Sign in")

    q = ParsedQuery(departure_iata="SFO", destination_iata="JFK", date="2026-11-05", date_is_flexible=True)
    check(
        "ParsedQuery constructs with correct defaults",
        q.budget_usd is None and q.date_is_flexible is True and q.date_window_start is None,
    )
    q_range = ParsedQuery(
        departure_iata="SFO", destination_iata="JFK", date="2026-11-05",
        date_window_start="2026-11-03", date_window_end="2026-11-09", date_is_flexible=True,
    )
    check("ParsedQuery carries an explicit date window", q_range.date_window_end == "2026-11-09")
    r = FlightSearchReport(origin="SFO", destination="JFK", date="2026-11-05", within_budget=False, options=[], notes="x")
    check("FlightSearchReport constructs", r.options == [])


async def browserbase_tests():
    """Validate browserbase_fetch paths with fake Browserbase and fake Playwright."""
    print("\n[Fetch-layer tests] Fake browser checks")
    import tools as tools_mod

    saved = os.environ.pop("BROWSERBASE_API_KEY", None)
    no_key = await tools_mod.browserbase_fetch("https://example.com")
    check("missing key returns readable error", no_key.startswith("[browserbase_fetch error]"))
    os.environ["BROWSERBASE_API_KEY"] = "fake-key-for-test"

    closed = {"count": 0}

    class FakePage:
        def __init__(self, html, body_text):
            self._html, self._body = html, body_text

        async def goto(self, *a, **k): return None
        async def wait_for_timeout(self, ms): return None
        async def evaluate(self, script): return self._body
        async def content(self): return self._html

    class FakeBrowser:
        def __init__(self, page):
            self.contexts = [type("Ctx", (), {"pages": [page]})()]

        async def close(self):
            closed["count"] += 1

    def make_fake_playwright(page):
        class FakeChromium:
            async def connect_over_cdp(self, url): return FakeBrowser(page)
        class FakePW:
            chromium = FakeChromium()
        class Ctx:
            async def __aenter__(self): return FakePW()
            async def __aexit__(self, *a): return False
        return lambda: Ctx()

    class FakeBB:
        def __init__(self, api_key=None):
            self.sessions = type("S", (), {"create": lambda _s, **k: type("R", (), {"connect_url": "ws://fake"})()})()

    import browserbase as bb_mod

    orig_bb, orig_pw = bb_mod.Browserbase, tools_mod.async_playwright
    orig_poll, orig_max = tools_mod.POLL_INTERVAL_MS, tools_mod.MAX_WAIT_MS
    tools_mod.POLL_INTERVAL_MS, tools_mod.MAX_WAIT_MS = 1, 3
    try:
        html = "<html><body>" + "navigation item " * 3000 + "Alaska Airlines $179 JetBlue $186 Delta $297" + "</body></html>"
        body = "Alaska $179 JetBlue $186 Delta $297"
        bb_mod.Browserbase = FakeBB
        tools_mod.async_playwright = make_fake_playwright(FakePage(html, body))

        closed["count"] = 0
        ok = await tools_mod.browserbase_fetch("https://example.com")
        check("normal path detects prices", "$179" in ok, ok[:200])
        check("normal path has no false warning", "[fetch warning]" not in ok)
        check("normal path closes browser", closed["count"] == 1, f"close called {closed['count']} times")

        html2 = "<html><body>" + "search form only " * 2000 + "</body></html>"
        tools_mod.async_playwright = make_fake_playwright(FakePage(html2, "no prices"))
        closed["count"] = 0
        warned = await tools_mod.browserbase_fetch("https://example.com")
        check("no-price path returns fetch warning", warned.startswith("[fetch warning]"), warned[:120])
        check("no-price path closes browser", closed["count"] == 1)

        class BoomPage(FakePage):
            async def content(self):
                raise RuntimeError("simulated page crash")

        tools_mod.async_playwright = make_fake_playwright(BoomPage(html, body))
        closed["count"] = 0
        boom = await tools_mod.browserbase_fetch("https://example.com")
        check("exception path returns readable error", boom.startswith("[browserbase_fetch error]"), boom[:120])
        check("exception path still closes browser", closed["count"] == 1, f"close called {closed['count']} times")
    finally:
        bb_mod.Browserbase, tools_mod.async_playwright = orig_bb, orig_pw
        tools_mod.POLL_INTERVAL_MS, tools_mod.MAX_WAIT_MS = orig_poll, orig_max
        os.environ.pop("BROWSERBASE_API_KEY", None)
        if saved is not None:
            os.environ["BROWSERBASE_API_KEY"] = saved


def report_guard_tests():
    """The exit guard: fields code can compute are not left to the model."""
    print("\n[Report guard] code owns the fields it can compute")
    from main_advanced import _enforce_report_facts, _prices_in

    parsed = ParsedQuery(departure_iata="SFO", destination_iata="JFK", date="2026-11-05",
                         return_date=None, budget_usd=180.0, cabin=None,
                         other_preferences=None, date_is_flexible=False)
    option = {"airline": "JetBlue", "departure_time": "2:55 PM", "arrival_time": "11:25 PM",
              "duration": "5h 30m", "price_usd": 195.0, "stops": "Nonstop",
              "source_strategy": "Strategy A: exact date", "booking_url": None}

    # What the live $180 run actually produced: blank route, within_budget judged
    # against the relaxed ceiling instead of the user's budget.
    r = FlightSearchReport(origin="", destination="", date="2026-11-05", within_budget=True,
                           options=[option], notes="The JetBlue flight is exactly at your relaxed budget.")
    r = _enforce_report_facts(r, parsed, [195.0, 200.0, 220.0])
    check("blank origin is filled from the parser", r.origin == "SFO", r.origin)
    check("blank destination is filled from the parser", r.destination == "JFK", r.destination)
    check("within_budget is recomputed against the user's budget", r.within_budget is False)
    check("exact-date guard fills option departure date", r.options[0].departure_date == "2026-11-05")

    # A report that already names the city keeps the model's wording.
    r = FlightSearchReport(origin="San Francisco (SFO)", destination="New York (JFK)", date="2026-11-05",
                           within_budget=True, options=[option], notes="")
    r = _enforce_report_facts(r, ParsedQuery(**{**parsed.model_dump(), "budget_usd": 200.0}), [195.0])
    check("a city name containing the IATA code is left alone", r.origin == "San Francisco (SFO)")
    check("within_budget stays true when the cheapest option fits", r.within_budget is True)

    # What the live $90 run produced: empty options although the page had flights.
    r = FlightSearchReport(origin="SFO", destination="JFK", date="2026-11-05", within_budget=False,
                           options=[], notes="Fetching failed or no real flight data was available.")
    r = _enforce_report_facts(r, ParsedQuery(**{**parsed.model_dump(), "budget_usd": 90.0}), [195.0, 200.0])
    check("an empty report over real flights says flights were found", "Flights were found" in r.notes, r.notes)

    # No budget stated: within_budget just means "there is something to show".
    r = FlightSearchReport(origin="SFO", destination="JFK", date="2026-11-05", within_budget=False,
                           options=[option], notes="")
    r = _enforce_report_facts(r, ParsedQuery(**{**parsed.model_dump(), "budget_usd": None}), [195.0])
    check("no budget + options -> within_budget true", r.within_budget is True)

    check("_prices_in reads dollar amounts", _prices_in("Price: $195\nPrice: $1,200") == [195.0, 1200.0])
    check("_prices_in on a fetch error is empty", _prices_in("[browserbase_fetch error] timeout") == [])


async def main():
    print("=" * 70)
    print("FlightFinder Pro Advanced - offline orchestration tests without real API keys")
    print("=" * 70)

    unit_tests()
    report_guard_tests()
    await browserbase_tests()
    await scenario_skip_critic()
    await scenario_with_critic_approved()
    await scenario_retry_once()
    await scenario_retry_capped()
    await scenario_no_data()
    await scenario_model_misbehaves()

    print("\n" + "=" * 70)
    print(f"Passed {len(PASS)} checks, failed {len(FAIL)} checks")
    if FAIL:
        for name in FAIL:
            print(f"  FAIL {name}")
        raise SystemExit(1)
    print("All checks passed")


if __name__ == "__main__":
    asyncio.run(main())
