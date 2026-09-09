# FlightFinder Pro

The application behind page 02 of the course page (`../agentic-systems-studio.html`).
Everything on that page — the five build steps, the real-runs panel, the tests panel and
the runnable copy — is excerpted from, produced by, or checked against the files in this
folder.

One English sentence in, a validated `FlightSearchReport` out. A parser agent, a
bounded date-range plan, concurrent browser searches against Kayak, an extractor per
date, a three-agent team with a dispatcher, and a token report.

The whole application makes exactly **two** kinds of model judgement — what date
window the user's wording allows, and whether the ranked results need critic review.
Ordinary Python caps the range at three searches, runs them concurrently, and owns
termination and final fact checks.

## Layout

    schemas.py            the typed boundary: ParsedQuery, FlightSearchReport
    tools.py              URL building, Browserbase fetch, page condensing/slicing
    fanout.py             date-range planning (plan_search_dates) + concurrent search/extract fan-out
    agents_advanced.py    the four agents, selector_func, candidate_func, termination
    main_advanced.py      the entry point; prints every stage, the exit guard and the token table
    web_app.py            local classroom UI; calls the same pipeline and shows its trace
    test_offline.py       72 checks, real AutoGen, scripted model, no key needed
    test_integration.py   seven end-to-end paths, 35 checks, no key needed
    requirements.txt
    .env.example          copy to .env and fill in your own keys (.env is git-ignored)
    examples/
      run_comparisons.py     controlled A/B comparisons — no key, no network
      comparisons.json       its output
      capture_live_runs.py   real runs against real Kayak and a real model
      live_runs.json         their verbatim stdout (keys scrubbed); the page's real-runs panel reads it
      verify_port_python.py  runs the real Python over ~20k inputs -> port_reference.json
      verify_port_diff.py    runs the page's JavaScript port on the same inputs and diffs

## Setup

From the repository root (the top-level README has the key sign-up steps):

    python3 -m venv .venv && source .venv/bin/activate
    pip install -r flightfinder/requirements.txt
    python -m playwright install chromium     # only needed by examples/verify_port_diff.py
    cp flightfinder/.env.example flightfinder/.env   # then fill in your keys; .env is git-ignored
    cd flightfinder

## Run

    python3 examples/run_comparisons.py       # no key needed — start here
    python3 test_offline.py                   # no key needed
    python3 test_integration.py               # no key needed
    python3 main_advanced.py "Find flights from SFO to JFK on November 5 under $200"
    python3 web_app.py                        # then open http://127.0.0.1:8000
    python3 examples/capture_live_runs.py     # five real runs -> examples/live_runs.json
    python3 examples/capture_live_runs.py --add "label" "query"   # one more, appended

`run_comparisons.py`, `test_offline.py` and `test_integration.py` need no API key and
no network: they run the real AutoGen team with `ReplayChatCompletionClient` standing
in for the model. Only `main_advanced.py`, `web_app.py` and `capture_live_runs.py`
call out to OpenAI and Browserbase.

## Why comparisons rather than a demo run

A single run tells you the system works. It does not tell you what any part of it is
for. `run_comparisons.py` changes exactly one input at a time and reports what moved,
so each number is attributable:

    A  exact date vs flexible window    -> one search or a bounded fan-out (max three)
    E  same flag, different date        -> the guard withdraws the second search
    B  budget stated or not             -> the critic round appears or vanishes
    C  budget reachable or impossible   -> the retry cap fires; within_budget = false
    D  page had rows or was empty       -> same path, zero options, nothing invented
    F  count the routing calls          -> how much of the order the rules decided

## The date-range budget guard

The parser writes `date_window_start` and `date_window_end` when the user's wording
is flexible. `plan_search_dates()` then converts that interval into at most three
dates. It preserves the range boundaries and the preferred date when possible,
clips past dates, and degrades to the preferred date when the interval is malformed.
This boundary is intentional: the model interprets language, while code controls
how many expensive browser sessions may be created.

## The exit guard (main_advanced.py)

Two live runs showed the summarizer filling report fields the code knew better:
`origin`/`destination` came back as empty strings, and `within_budget` was judged
against a relaxed ceiling instead of the user's budget. The schema passed both,
because both were the right type.

So the team is now handed two lines computed by code — the route, and how many
priced flights the search found and the cheapest of them — and after the team has
spoken, `_enforce_report_facts()` overwrites any field code can compute, printing
one `[guard]` line per correction. The ranker's instructions also gained one
sentence: never drop a flight for being over budget. No agent, routing rule or
schema changed. `test_offline.py` covers the guard with nine deterministic checks.

## Checking the page's JavaScript port against this code

The course page runs a line-for-line JavaScript port of `plan_search_dates`,
`selector_func`, `candidate_func` and `_critic_verdict`. Two scripts keep it honest:

    python3 examples/verify_port_python.py     # runs the REAL Python over ~20k inputs
    python3 examples/verify_port_diff.py       # runs the page's JS on the same inputs, diffs
                                               # (defaults to ../agentic-systems-studio.html)

Last run: 20,193 comparisons, all match, with `max_dates` in 1..3.

One thing the diff found in `plan_search_dates` itself (not fixed here — it is your
call): with `max_dates >= 4` two interior sample dates can be equidistant from the
preferred date, and the tie is broken by `min()` over a `set`, i.e. by hash order
rather than by anything you chose. The app only uses `MAX_SEARCH_DATES = 3`, where
there is a single interior date and no tie is possible. If the cap ever rises,
sort the candidates before taking `min()` so the earlier date wins deterministically.
