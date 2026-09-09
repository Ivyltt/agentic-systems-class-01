"""Command-line entry point for the advanced FlightFinder demo.

The script connects the components in execution order: parse the request, run search fan-out, coordinate the multi-agent team, emit a structured report, and print observability information."""

import asyncio
import datetime
import json
import re
import sys
import traceback

from dotenv import load_dotenv

from agents_advanced import build_advanced_team, build_model_client, build_query_parser_agent
from fanout import MAX_SEARCH_DATES, fanout_search, plan_search_dates
from schemas import FlightSearchReport, ParsedQuery
from tools import PRICE_PATTERN

DEFAULT_QUERY = "Find flights from San Francisco (SFO) to New York (JFK) on November 5, within a $200 budget"
ISO_DATE_PATTERN = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")


def _prices_in(text: str) -> list:
    """Every dollar amount in a block of text, as floats. Ordinary code, no model."""
    out = []
    for m in PRICE_PATTERN.finditer(text):
        try:
            out.append(float(m.group(0).lstrip("$").replace(",", "").strip()))
        except ValueError:
            pass
    return out


def _enforce_report_facts(report: FlightSearchReport, parsed: ParsedQuery, source_prices: list) -> FlightSearchReport:
    """Fields the code can compute are not left to the model.

    The summarizer fills the whole report, and the schema only checks types: an
    empty origin is still a str, and within_budget is a bool whichever budget it
    was judged against. So after the team has spoken, code sets the fields it
    knows better, and prints one line per correction so the correction is visible.
    """
    fixes = []
    if parsed.departure_iata not in (report.origin or ""):
        fixes.append(f"origin: model wrote {report.origin!r}, code sets {parsed.departure_iata!r}")
        report.origin = parsed.departure_iata
    if parsed.destination_iata not in (report.destination or ""):
        fixes.append(f"destination: model wrote {report.destination!r}, code sets {parsed.destination_iata!r}")
        report.destination = parsed.destination_iata
    if report.date != parsed.date:
        fixes.append(f"date: model wrote {report.date!r}, code sets the requested date {parsed.date!r} "
                     f"(each option still names its own strategy)")
        report.date = parsed.date

    for option in report.options:
        if option.departure_date:
            continue
        strategy_date = ISO_DATE_PATTERN.search(option.source_strategy or "")
        if strategy_date:
            option.departure_date = strategy_date.group(0)
            fixes.append(
                f"option departure_date: copied {option.departure_date} from its dated search strategy"
            )
        elif not parsed.date_is_flexible:
            option.departure_date = parsed.date
            fixes.append(
                f"option departure_date: exact-date request lets code set {parsed.date}"
            )

    cheapest = min((o.price_usd for o in report.options), default=None)
    if parsed.budget_usd is None:
        within = bool(report.options)
    else:
        within = cheapest is not None and cheapest <= parsed.budget_usd
    if report.within_budget != within:
        if parsed.budget_usd is None:
            why = f"no budget stated, {len(report.options)} option(s) returned"
        elif cheapest is None:
            why = f"no options returned against budget ${parsed.budget_usd:.0f}"
        else:
            why = f"cheapest option ${cheapest:.0f} vs budget ${parsed.budget_usd:.0f}"
        fixes.append(f"within_budget: model wrote {report.within_budget}, code computes {within} ({why})")
        report.within_budget = within

    if not report.options and source_prices:
        fixes.append(f"notes: the report is empty, but the search found {len(source_prices)} priced flights "
                     f"(cheapest ${min(source_prices):.0f}) - saying so")
        report.notes = (report.notes + " Flights were found (cheapest "
                        f"${min(source_prices):.0f}) but none were returned as options.").strip()

    for f in fixes:
        print(f"[guard] {f}")
    if not fixes:
        print("[guard] every code-checkable field in the report already matched")
    return report


def _sum_usage(task_result) -> int:
    total = 0
    for msg in task_result.messages:
        usage = getattr(msg, "models_usage", None)
        if usage:
            total += usage.prompt_tokens + usage.completion_tokens
    return total


async def run(query: str) -> None:
    """Run the full pipeline with a readable top-level failure boundary."""
    try:
        await execute_search(query)
    except Exception as exc:

        print("\n" + "=" * 70)
        print(f"Run interrupted: {type(exc).__name__}: {exc}")
        response = getattr(exc, "response", None)
        headers = getattr(response, "headers", None)
        if headers:
            proxy_error = headers.get("X-Proxy-Error") or headers.get("x-proxy-error")
            if proxy_error:
                print(f"X-Proxy-Error: {proxy_error}")
        print("=" * 70)
        print("Common causes:")
        print("  - AuthenticationError / 401  -> OPENAI_API_KEY is wrong or has no quota")
        print("  - RateLimitError / 429       -> OpenAI rate limit; wait and rerun")
        print("  - ValidationError            -> structured model output failed validation; rerun usually fixes it")
        print("  - Fetch timeout/connection   -> Browserbase-side issue; rerun")
        print("\nFull traceback for debugging:")
        traceback.print_exc()


async def execute_search(query: str) -> dict:
    """Run the application and return a JSON-ready trace for CLI or web callers."""
    model_client = build_model_client()
    try:
        return await _run_pipeline(model_client, query)
    finally:
        try:
            await model_client.close()
        except Exception:
            pass


async def _run_pipeline(model_client, query: str) -> dict:
    today = datetime.date.today().isoformat()

    print("=" * 70)
    print("FlightFinder Pro (Advanced AutoGen) - dynamic orchestration + critic retry + parallel search + structured output")
    print(f"User query: {query}")
    print("=" * 70)

    # Track each stage so architecture decisions can be connected to token cost.
    stage_tokens = {}


    print("\n[Stage 1] Parsing query...")
    query_parser_agent = build_query_parser_agent(model_client)
    parse_result = await query_parser_agent.run(
        task=f"Today's date is {today}. The user's flight request is: {query}"
    )
    stage_tokens["Stage 1 parse"] = _sum_usage(parse_result)

    parsed = parse_result.messages[-1].content
    if not isinstance(parsed, ParsedQuery):
        raise TypeError(
            "Query parsing did not return a structured ParsedQuery: "
            f"{type(parsed).__name__}: {parsed}"
        )
    print(parsed.model_dump_json(indent=2, exclude_none=True))

    search_dates = plan_search_dates(
        parsed.date,
        date_window_start=parsed.date_window_start,
        date_window_end=parsed.date_window_end,
        include_flex_date=parsed.date_is_flexible,
        max_dates=MAX_SEARCH_DATES,
    )
    print(
        f"\n[Stage 2 - dynamic decision 1] Model judged date flexibility: {parsed.date_is_flexible} "
        f"-> code planned {len(search_dates)} search path(s): {', '.join(search_dates)}"
    )
    fanout_text, fanout_tokens = await fanout_search(
        model_client,
        departure=parsed.departure_iata,
        destination=parsed.destination_iata,
        date=parsed.date,
        return_date=parsed.return_date,
        include_flex_date=parsed.date_is_flexible,
        date_window_start=parsed.date_window_start,
        date_window_end=parsed.date_window_end,
        max_search_dates=MAX_SEARCH_DATES,
    )
    stage_tokens["Stage 2 parallel search + extraction"] = fanout_tokens
    print(fanout_text)


    print("\n[Stage 3 - dynamic decision 2] Merge/rank -> model decides whether critic review is needed...")
    preferences_text = (
        f"User preferences: budget {parsed.budget_usd if parsed.budget_usd is not None else 'unspecified'} USD, "
        f"cabin {parsed.cabin or 'unspecified'}, other preferences: {parsed.other_preferences or 'none'}"
    )
    # Two lines the team would otherwise have to guess at. Both are computed by code:
    # the route from the parser, and what the search actually found from the text.
    window_text = (
        f", acceptable window {parsed.date_window_start} through {parsed.date_window_end}"
        if parsed.date_window_start and parsed.date_window_end
        else ""
    )
    route_line = (
        f"Route: {parsed.departure_iata} -> {parsed.destination_iata}, preferred date {parsed.date}"
        f"{window_text}. Dates actually searched by code: {', '.join(search_dates)}."
    )
    source_prices = _prices_in(fanout_text)
    source_fact = (
        f"Source check (computed by code, not by a model): the extracted results contain "
        f"{len(source_prices)} priced flights"
        + (f", cheapest ${min(source_prices):.0f}." if source_prices else ". Treat this as no data.")
    )
    team = build_advanced_team(model_client)
    team_result = await team.run(task=f"{route_line}\n{preferences_text}\n{source_fact}\n\n{fanout_text}")
    stage_tokens["Stage 3 orchestration agent messages"] = _sum_usage(team_result)

    for msg in team_result.messages:
        content = msg.content
        content_preview = (
            content if isinstance(content, str) else content.model_dump_json(indent=2, exclude_none=True)
        )
        print(f"\n---------- {type(msg).__name__} ({msg.source}) ----------")
        print(content_preview)


    path = " -> ".join(m.source for m in team_result.messages)
    critic_spoke = any(m.source == "budget_critic_agent" for m in team_result.messages)
    print("\n" + "-" * 70)
    print(f"Actual SelectorGroupChat path: {path}")
    print(f"Dynamic decision 2 result: model {'chose critic review' if critic_spoke else 'skipped critic review and finalized directly'}")


    final_message = team_result.messages[-1]
    final_report = final_message.content
    print("\n" + "=" * 70)
    structured_report = None
    if isinstance(final_report, FlightSearchReport):
        final_report = _enforce_report_facts(final_report, parsed, source_prices)
        structured_report = final_report.model_dump()
        print("Final structured report (FlightSearchReport):")
        print(json.dumps(structured_report, ensure_ascii=False, indent=2))
    else:
        print("Could not obtain a structured report; the workflow may have hit MaxMessageTermination early.")
        print(f"Stop reason: {team_result.stop_reason}")
        print(f"Last message came from {final_message.source}: {final_report}")




    agent_total = sum(stage_tokens.values())
    usage = model_client.total_usage()
    real_total = usage.prompt_tokens + usage.completion_tokens

    print("=" * 70)
    print("Token usage (advanced point 4: observability)")
    for stage, tokens in stage_tokens.items():
        print(f"  {stage}: about {tokens} tokens")
    print(f"  -- Sum of agent-message usage: about {agent_total} tokens")
    print(f"  -- Actual model-client total: about {real_total} tokens")
    print(
        f"  -- Difference {max(0, real_total - agent_total)} tokens = extra SelectorGroupChat "
        "model calls used to choose the next speaker (dynamic orchestration cost)"
    )

    messages = []
    for msg in team_result.messages:
        content = msg.content
        if hasattr(content, "model_dump"):
            content = content.model_dump()
        messages.append({
            "source": msg.source,
            "message_type": type(msg).__name__,
            "content": content,
        })

    return {
        "query": query,
        "parsed_query": parsed.model_dump(exclude_none=True),
        "search_dates": search_dates,
        "fanout_results": fanout_text,
        "agent_path": [msg.source for msg in team_result.messages],
        "agent_messages": messages,
        "critic_used": critic_spoke,
        "report": structured_report,
        "stop_reason": team_result.stop_reason,
        "token_usage": {
            **stage_tokens,
            "Agent-message total": agent_total,
            "Model-client total": real_total,
            "Dynamic routing overhead": max(0, real_total - agent_total),
        },
    }


def main() -> None:
    # Prefer this project's .env over placeholder values inherited from an IDE.
    load_dotenv(override=True)
    query = " ".join(sys.argv[1:]).strip() or DEFAULT_QUERY
    asyncio.run(run(query))


if __name__ == "__main__":
    main()
