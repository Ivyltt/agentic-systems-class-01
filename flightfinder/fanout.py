"""Fan-out / fan-in search layer.

This module shows how ordinary async Python and agents can be composed. Python decides how many independent searches to run and runs them concurrently; extractor agents then interpret each raw result; the merged text becomes context for the later multi-agent team."""

import asyncio
import datetime
from typing import List, Optional, Tuple

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

from tools import PRICE_PATTERN, search_flights

MAX_SEARCH_DATES = 3


def _debug_dump(raw: str, label: str) -> None:
    """Print compact fetch diagnostics for one search path."""
    total_len = len(raw)
    price_count = len(PRICE_PATTERN.findall(raw))
    print(f"\n[debug] {label} fetch result: {total_len} characters, {price_count} price markers detected")


    for line in raw.splitlines():
        if line.startswith(("[fetch diagnostic]", "[fetch warning]", "[browserbase_fetch error]")):
            print(f"[debug] {label} -> {line}")

    if price_count == 0:
        print(f"[debug] {label} did not contain any prices. First 800 characters:")
        print(raw[:800])


def _make_extractor(model_client: OpenAIChatCompletionClient, name: str, date_label: str) -> AssistantAgent:
    """Create an extractor agent that reads raw page text for one date and summarizes candidates."""
    return AssistantAgent(
        name=name,
        model_client=model_client,
        description=f"Extract candidate flights from Kayak raw page text for {date_label}",
        system_message=f"""You are a flight-information extraction assistant for Kayak search results on {date_label}.

The user message will contain raw fetched page text. The first line may begin with "[fetch diagnostic]",
"[fetch warning]", or "[browserbase_fetch error]". Read it first; it tells you whether this fetch succeeded.

If the fetch succeeded and flight data is present, extract up to 3 real candidate flights. For each one,
include airline, departure time, arrival time, duration, price, and whether it is nonstop or has stops.
Use a concise list format. The raw text was converted from a web page, so related fields may be spread across nearby lines; merge them using context.

If the fetch failed or no flight data is present, say clearly that the {date_label} path did not return flight data and briefly explain why.

Never invent flight data. It is better to report that the fetch returned no usable data than to fabricate a plausible-looking option.""",
    )


def _as_date(value: Optional[str]) -> Optional[datetime.date]:
    """Parse one ISO date without letting malformed model output escape the guard."""
    if not value:
        return None
    try:
        return datetime.date.fromisoformat(value.strip())
    except (ValueError, AttributeError):
        return None


def plan_search_dates(
    date: str,
    date_window_start: Optional[str] = None,
    date_window_end: Optional[str] = None,
    include_flex_date: bool = True,
    max_dates: int = MAX_SEARCH_DATES,
    today: Optional[datetime.date] = None,
) -> List[str]:
    """Turn a model-interpreted date window into a small deterministic search plan.

    A flexible window can contain many dates, but a live browser search is expensive.
    Code therefore samples at most ``max_dates`` dates while preserving the start,
    end, and preferred date when possible. This is the fan-out budget guard.
    """
    if max_dates < 1:
        return []

    anchor = _as_date(date)
    if anchor is None:
        return [date]
    if not include_flex_date:
        return [anchor.isoformat()]

    current = today or datetime.date.today()
    start = _as_date(date_window_start)
    end = _as_date(date_window_end)

    # Backward-compatible fallback when an older parser only returns flexible=true.
    if start is None or end is None:
        try:
            start = anchor - datetime.timedelta(days=1)
            end = anchor + datetime.timedelta(days=1)
        except OverflowError:
            return [anchor.isoformat()]

    if start > end:
        return [anchor.isoformat()]

    start = max(start, current)
    if end < start:
        return [anchor.isoformat()]

    day_count = (end - start).days + 1
    if day_count <= max_dates:
        return [(start + datetime.timedelta(days=i)).isoformat() for i in range(day_count)]

    if max_dates == 1:
        chosen = anchor if start <= anchor <= end else start
        return [chosen.isoformat()]

    chosen = {start, end}
    interior_slots = max_dates - 2
    for i in range(1, interior_slots + 1):
        offset = round(i * (day_count - 1) / (interior_slots + 1))
        chosen.add(start + datetime.timedelta(days=offset))

    if interior_slots and start < anchor < end and anchor not in chosen:
        interior = [d for d in chosen if d not in (start, end)]
        if interior:
            chosen.remove(min(interior, key=lambda d: abs((d - anchor).days)))
        chosen.add(anchor)

    return [d.isoformat() for d in sorted(chosen)[:max_dates]]


def compute_flex_date(date: str) -> Optional[str]:
    """Compatibility helper for the former one-day-earlier teaching example."""
    planned = plan_search_dates(date, include_flex_date=True, max_dates=2)
    earlier = [candidate for candidate in planned if candidate < date]
    return earlier[0] if earlier else None


def _sum_usage(task_result) -> int:
    total = 0
    for msg in task_result.messages:
        usage = getattr(msg, "models_usage", None)
        if usage:
            total += usage.prompt_tokens + usage.completion_tokens
    return total


# Fan-out/fan-in boundary: run independent searches first, then give agents the raw results.
async def fanout_search(
    model_client: OpenAIChatCompletionClient,
    departure: str,
    destination: str,
    date: str,
    return_date: Optional[str] = None,
    include_flex_date: bool = True,
    date_window_start: Optional[str] = None,
    date_window_end: Optional[str] = None,
    max_search_dates: int = MAX_SEARCH_DATES,
) -> Tuple[str, int]:
    """Run a bounded set of date searches, extract candidates, and fan results in."""
    search_dates = plan_search_dates(
        date,
        date_window_start=date_window_start,
        date_window_end=date_window_end,
        include_flex_date=include_flex_date,
        max_dates=max_search_dates,
    )

    if include_flex_date and len(search_dates) == 1:
        print(f"\n[note] Flexible-date planning produced one usable date: {search_dates[0]}.")

    raw_results = await asyncio.gather(
        *(search_flights(departure, destination, search_date, return_date) for search_date in search_dates)
    )

    for index, (search_date, raw) in enumerate(zip(search_dates, raw_results)):
        strategy = chr(ord("A") + index)
        _debug_dump(raw, f"Strategy {strategy} ({search_date})")

    extractors = [
        _make_extractor(model_client, f"explorer_date_{index + 1}", search_date)
        for index, search_date in enumerate(search_dates)
    ]
    extracted = await asyncio.gather(
        *(agent.run(task=f"Raw page content:\n{raw}") for agent, raw in zip(extractors, raw_results))
    )

    sections = []
    for index, (search_date, result) in enumerate(zip(search_dates, extracted)):
        strategy = chr(ord("A") + index)
        relationship = "preferred date" if search_date == date else "date-window sample"
        sections.append(f"[Strategy {strategy}: {search_date}, {relationship}]\n{result.messages[-1].content}")

    usage_tokens = sum(_sum_usage(result) for result in extracted)
    return "\n\n".join(sections), usage_tokens
