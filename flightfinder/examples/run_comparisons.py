"""
Controlled comparisons over the real FlightFinder team.

This is not a smoke test. Every case here is one half of a PAIR, and the two halves
differ in exactly one input. That is the whole point: when only one thing changes,
the difference in the output is attributable to it, and the numbers mean something.

What is real here: AutoGen's own SelectorGroupChat, this project's selector_func,
candidate_func, critic protocol, retry cap, termination condition and Pydantic
schema validation all execute for real. What is scripted: the model's replies, via
ReplayChatCompletionClient - the same substitution test_offline.py makes. No API key
and no network are needed, so the results are identical on every machine.

    python3 examples/run_comparisons.py            # readable report
    python3 examples/run_comparisons.py --json     # writes comparisons.json

The fan-out half (pair A and pair E) does not go through the team at all; it calls
plan_search_dates directly, because that is where the execution-budget decision lives.
"""
import argparse
import asyncio
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from autogen_core.models import ModelFamily, ModelInfo
from autogen_ext.models.replay import ReplayChatCompletionClient

from agents_advanced import build_advanced_team
from fanout import plan_search_dates
from schemas import FlightSearchReport

MODEL_INFO = ModelInfo(vision=False, function_calling=True, json_output=True,
                       family=ModelFamily.UNKNOWN, structured_output=True)

# A line that appears only in the dispatcher's prompt, never in an agent's.
SELECTOR_MARK = "You are the dispatcher for a multi-agent workflow"


class CountingClient(ReplayChatCompletionClient):
    """A replay client that also records which calls were speaker-selection calls.

    SelectorGroupChat asks the model who speaks next only when selector_func returns
    None. Those calls produce no message and are invisible in the transcript, so the
    only way to count them is to look at what was sent.
    """

    def __init__(self, replies, **kw):
        super().__init__(replies, **kw)
        self.routing_calls = 0
        self.agent_calls = 0

    async def create(self, messages, **kw):
        text = "".join(str(getattr(m, "content", "")) for m in messages)
        if SELECTOR_MARK in text:
            self.routing_calls += 1
        else:
            self.agent_calls += 1
        return await super().create(messages, **kw)


def report_json(**over):
    base = {"origin": "SFO", "destination": "JFK", "date": "2026-11-05",
            "within_budget": True,
            "options": [{"airline": "Alaska Airlines", "departure_time": "7:00 am",
                         "arrival_time": "3:32 pm", "duration": "5h 32m",
                         "price_usd": 179.0, "stops": "nonstop",
                         "source_strategy": "Strategy A: exact date", "booking_url": None}],
            "notes": "Found options within budget."}
    base.update(over)
    return json.dumps(base, ensure_ascii=False)


EMPTY_REPORT = report_json(within_budget=False, options=[],
                           notes="Fetch failed; no real flight data was available.")
OVER_BUDGET_REPORT = report_json(within_budget=False,
                                 notes="Nothing met the stated budget; the cheapest fare is listed.")

CANDIDATES = "Candidate flights: 1. Alaska Airlines $179 nonstop  2. JetBlue $186 nonstop"
NO_CANDIDATES = "No usable candidate flights are available; every search path returned no real flight data."


async def run_team(replies, task):
    client = CountingClient(replies, model_info=MODEL_INFO)
    team = build_advanced_team(client)
    result = await team.run(task=task)
    final = result.messages[-1].content
    usage = client.total_usage()
    return {
        "path": [m.source for m in result.messages],
        "agent_turns": len(result.messages) - 1,
        "routing_calls": client.routing_calls,
        "model_calls": client.routing_calls + client.agent_calls,
        "stop_reason": result.stop_reason,
        "structured": isinstance(final, FlightSearchReport),
        "within_budget": getattr(final, "within_budget", None),
        "n_options": len(getattr(final, "options", []) or []),
        "tokens": usage.prompt_tokens + usage.completion_tokens,
    }


def task_for(budget, candidates=CANDIDATES):
    pref = f"budget {budget} USD" if budget is not None else "budget unspecified"
    return (f"User preferences: {pref}, cabin unspecified, other preferences: none\n\n"
            f"[Strategy A: 2026-11-05 exact date]\n{candidates}")


# --------------------------------------------------------------- the pairs
async def pair_a():
    """One model bit -> how many browser sessions the system opens."""
    today = datetime.date.today()
    preferred = today + datetime.timedelta(days=60)
    future = preferred.isoformat()
    window_start = (preferred - datetime.timedelta(days=3)).isoformat()
    window_end = (preferred + datetime.timedelta(days=3)).isoformat()
    planned = plan_search_dates(future, window_start, window_end, True)
    return {
        "id": "A", "title": "Does the model call the date flexible?",
        "varies": "date_is_flexible, with the same preferred date and the same seven-day window",
        "teaches": "One bit of model judgement decides how much work the system does - one browser "
                   "session, or the capped fan-out of three. Nothing else in the input changed.",
        "sides": [
            {"label": "date_is_flexible = false", "input": {"date": future, "flexible": False},
             "result": {"search_dates": [future], "searches": 1}},
            {"label": "date_is_flexible = true", "input": {"date": future, "flexible": True},
             "result": {"search_dates": planned, "searches": len(planned)}},
        ]}


async def pair_e():
    """Same model opinion, different date: code overrules it."""
    today = datetime.date.today()
    preferred = today + datetime.timedelta(days=60)
    future = preferred.isoformat()
    todays = today.isoformat()
    a = plan_search_dates(
        future,
        (preferred - datetime.timedelta(days=3)).isoformat(),
        (preferred + datetime.timedelta(days=3)).isoformat(),
        True,
    )
    b = plan_search_dates(
        todays,
        (today - datetime.timedelta(days=2)).isoformat(),
        todays,
        True,
    )
    c = plan_search_dates("Nov 5", include_flex_date=True)
    return {
        "id": "E", "title": "The model says flexible. Is it actionable?",
        "varies": "the date and its window, with date_is_flexible pinned to true in all three",
        "teaches": "The model returned flexible = true in all three. plan_search_dates then "
                   "sampled a valid seven-day window down to three dates, clipped a window that had "
                   "already passed down to one, and searched malformed output as a single path. "
                   "The model has an opinion; the code keeps the veto.",
        "sides": [
            {"label": f"date = {future}, window {(preferred - datetime.timedelta(days=3)).isoformat()} to {(preferred + datetime.timedelta(days=3)).isoformat()} (seven days, all in the future)",
             "input": {"date": future, "flexible": True},
             "result": {"search_dates": a, "searches": len(a)}},
            {"label": f"date = {todays}, window {(today - datetime.timedelta(days=2)).isoformat()} to {todays} (two of the three days already gone)",
             "input": {"date": todays, "flexible": True},
             "result": {"search_dates": b, "searches": len(b)}},
            {"label": "date = 'Nov 5' (the parser was supposed to normalise this and did not - the raw string reached the code)",
             "input": {"date": "Nov 5", "flexible": True},
             "result": {"search_dates": c, "searches": len(c)}},
        ]}


async def pair_b():
    """Whether the user stated a budget changes the team's shape at runtime."""
    with_budget = await run_team(
        [CANDIDATES, "budget_critic_agent", "APPROVED Candidates satisfy the $200 budget.",
         report_json()], task_for(200.0))
    without = await run_team(
        [CANDIDATES, "summarizer_agent", report_json(notes="No budget stated; cheapest first.")],
        task_for(None))
    return {
        "id": "B", "title": "Did the user mention a budget?",
        "varies": "one clause in the user's sentence; the code and the team are identical",
        "teaches": "The same three agents produce a different shape of run. Nobody wrote "
                   "an if-statement for this — the dispatcher read the request and skipped "
                   "a whole review round.",
        "sides": [{"label": "budget stated ($200)", "result": with_budget},
                  {"label": "no budget stated", "result": without}]}


async def pair_c():
    """A reachable budget versus one nothing can satisfy."""
    reachable = await run_team(
        [CANDIDATES, "budget_critic_agent", "APPROVED Candidates satisfy the $200 budget.",
         report_json()], task_for(200.0))
    # Replies alternate with the dispatcher's picks. selector_func sends control back
    # to the ranker on a RETRY without asking anyone, but the transition *out* of the
    # ranker is the one question it refuses to answer, so it recurs on the second lap.
    impossible = await run_team(
        [CANDIDATES,                                    # merge_ranker
         "budget_critic_agent",                         # dispatcher picks
         "RETRY Nothing meets $90. The cheapest is $179; relax the ceiling and rerank.",
         CANDIDATES,                                    # merge_ranker again (rule sent it back)
         "budget_critic_agent",                         # dispatcher picks again
         "RETRY Still nothing at $90.",                 # second RETRY - over the cap
         OVER_BUDGET_REPORT], task_for(90.0))           # summarizer
    return {
        "id": "C", "title": "Can the budget actually be met?",
        "varies": "the budget number only: $200 against $90",
        "teaches": "The impossible budget costs five agent turns instead of three and nearly "
                   "twice the tokens, because it buys one rerank before MAX_CRITIC_RETRIES "
                   "cuts the loop off. It still returns the cheapest fare it found, with "
                   "within_budget = false attached — an honest answer rather than an empty "
                   "one, and rather than a loop.",
        "sides": [{"label": "budget $200 (reachable)", "result": reachable},
                  {"label": "budget $90 (impossible)", "result": impossible}]}


async def pair_d():
    """A successful fetch versus one that returned nothing."""
    ok = await run_team(
        [CANDIDATES, "budget_critic_agent", "APPROVED Candidates satisfy the $200 budget.",
         report_json()], task_for(200.0))
    empty = await run_team(
        [NO_CANDIDATES, "budget_critic_agent",
         "NO_DATA The candidate list is empty and the source text shows a fetch error.",
         EMPTY_REPORT], task_for(200.0, NO_CANDIDATES))
    return {
        "id": "D", "title": "What if the page came back empty?",
        "varies": "whether the search returned flight rows",
        "teaches": "Read the two paths: they are identical, and so is the number of routing "
                   "calls. Nothing about the orchestration changed. What changed is the "
                   "content — NO_DATA is not RETRY, so the critic does not ask for a rerank "
                   "that cannot help, and the report carries zero options rather than a "
                   "plausible invented flight.",
        "sides": [{"label": "the fetch returned rows", "result": ok},
                  {"label": "the fetch returned nothing", "result": empty}]}


async def pair_f():
    """What the rules are worth: how often the model is asked who speaks next."""
    run = await run_team(
        [CANDIDATES, "budget_critic_agent", "APPROVED Candidates satisfy the $200 budget.",
         report_json()], task_for(200.0))
    turns = run["agent_turns"]
    return {
        "id": "F", "title": "How often is the model asked who speaks next?",
        "varies": "nothing — this reads the run in pair B/C/D and counts",
        "teaches": "Three agents spoke, and the model was asked to choose the speaker "
                   f"{run['routing_calls']} time, not {turns}. selector_func answered every "
                   "other transition from the transcript alone. Those routing calls produce "
                   "no message, so the only way to see them is to count.",
        "sides": [{"label": "one full run with selector_func in place",
                   "result": {"agent_turns": turns,
                              "decided_by_rule": turns - run["routing_calls"],
                              "decided_by_model": run["routing_calls"],
                              "model_calls_total": run["model_calls"]}}]}


PAIRS = [pair_a, pair_e, pair_b, pair_c, pair_d, pair_f]


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true", help="write comparisons.json")
    args = ap.parse_args()

    out = {"captured": datetime.datetime.now().isoformat(timespec="seconds"),
           "python": sys.version.split()[0],
           "today": datetime.date.today().isoformat(),
           "note": "real AutoGen SelectorGroupChat, real selector_func/candidate_func/"
                   "termination/schema; model replies scripted via ReplayChatCompletionClient",
           "pairs": []}
    try:
        import importlib.metadata as md
        out["versions"] = {p: md.version(p) for p in
                           ("autogen-agentchat", "autogen-core", "autogen-ext", "pydantic")}
    except Exception:
        pass

    for fn in PAIRS:
        p = await fn()
        out["pairs"].append(p)
        print("\n" + "=" * 78)
        print(f"PAIR {p['id']}  {p['title']}")
        print(f"  varies: {p['varies']}")
        print("=" * 78)
        for s in p["sides"]:
            print(f"\n  {s['label']}")
            for k, v in s["result"].items():
                if isinstance(v, list):
                    v = " -> ".join(v)
                print(f"      {k:<18} {v}")
        print(f"\n  >> {p['teaches']}")

    if args.json:
        dest = os.path.join(os.path.dirname(os.path.abspath(__file__)), "comparisons.json")
        with open(dest, "w") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
        print(f"\nwrote {dest}")


if __name__ == "__main__":
    asyncio.run(main())
