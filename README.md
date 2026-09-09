# Agentic Systems Studio — class 01

A one-hour class on multi-agent agentic AI, built around one real application.

    agentic-systems-studio.html   the course page — three interactive pages in one self-contained file; open it in a browser
    flightfinder/                 FlightFinder Pro, the AutoGen application the case page is about

The course page's third page reads FlightFinder Pro in the order it was built — five
decisions, each opening the real lines from `flightfinder/` — then shows the evidence:
four controlled comparisons, five real runs against Kayak, eight tests, and a copy of the
program that runs in the page.

## How the page and the code correspond

Every number on the case page comes from a file in `flightfinder/`:

| on the page                        | produced by                                             | data file                          |
|------------------------------------|---------------------------------------------------------|------------------------------------|
| the five build steps               | verbatim excerpts of the source files, with line numbers | — |
| the four comparisons (E, B, C, D)  | `examples/run_comparisons.py` — real AutoGen, scripted model, no key | `examples/comparisons.json` |
| the real-runs panel                | `examples/capture_live_runs.py` — real Kayak pages, real model | `examples/live_runs.json` (keys scrubbed) |
| the eight tests                    | verbatim excerpts of `test_offline.py` and `test_integration.py` | — |
| the runnable copy                  | a JavaScript port of `fanout.py` / `agents_advanced.py` / `main_advanced.py`, diffed against the Python on 20,193 inputs by `examples/verify_port_*.py` | — |

Pages 00 and 01 replay captured runs of small standalone Python programs whose model is
a scripted function; the page says so where the numbers appear.

## Run it without any keys

Nothing here needs an API key except the live search itself. Start with these:

    git clone https://github.com/Ivyltt/agentic-systems-class-01.git
    cd agentic-systems-class-01
    python3 -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
    pip install -r flightfinder/requirements.txt
    cd flightfinder
    python3 examples/run_comparisons.py      # the four comparisons on the page, recomputed
    python3 test_offline.py                  # 72 checks
    python3 test_integration.py              # 35 checks

The model in all three is `ReplayChatCompletionClient` answering from a script and the
fetch is a function returning prepared page text; everything in between — AutoGen's
`SelectorGroupChat`, the routing rules, the retry cap, the terminations, the schema and
the exit guard — runs for real. The numbers are the same on every machine.

## Run it for real: getting the two keys

A real run needs two services. Both have free tiers, both need an account.

**OpenAI** — the model behind every agent (`gpt-4o-mini` by default).

1. Sign in at https://platform.openai.com and create a key at
   https://platform.openai.com/api-keys. Copy it once; it is shown only at creation.
2. Add credit at https://platform.openai.com/account/billing/overview — the API is
   pay-as-you-go. One FlightFinder run on `gpt-4o-mini` uses roughly 7,000–16,000
   tokens, which is a fraction of a cent.

**Browserbase** — the hosted browser that renders the Kayak page.

1. Sign up at https://www.browserbase.com. The overview page
   (https://www.browserbase.com/overview) shows your **API key** and **Project ID** on
   the right-hand side. You need both.
2. The free plan allows **one browser session at a time**. FlightFinder fans out to up
   to three concurrent sessions when the user's date is flexible, so on the free plan
   the extra sessions are refused: those dates come back as `[browserbase_fetch error]`
   and the run continues with whatever did render. To stay within the free plan, set
   `MAX_SEARCH_DATES = 1` in `flightfinder/fanout.py`; a paid plan with three
   concurrent sessions runs the fan-out as designed.

Then put the keys in a `.env` file **next to `main_advanced.py`**:

    cd flightfinder
    cp .env.example .env
    # open .env and fill in:
    #   OPENAI_API_KEY=...
    #   OPENAI_MODEL=gpt-4o-mini        # optional
    #   BROWSERBASE_API_KEY=...
    #   BROWSERBASE_PROJECT_ID=...
    python -m playwright install chromium   # only needed by examples/verify_port_diff.py; the live
                                            # fetch connects to Browserbase's browser, not a local one

`.env` is listed in `.gitignore`. Never commit it, and never paste a key into a chat or
an issue — rotate it if you did.

## Run the FlightFinder Pro page

    cd flightfinder
    source ../.venv/bin/activate
    python3 web_app.py                 # then open http://127.0.0.1:8000

The page has a text box and three example requests (exact date / around a date / a
date range). Press **Run complete workflow**; a live run takes about a minute because
it waits for Kayak to render. What comes back is the execution trace, top to bottom:

1. **Parsed contract** — the `ParsedQuery` the model produced from your sentence.
2. **Date-range decision** — the window the model judged, and the one-to-three dates code
   decided to search.
3. **Actual agent path** — who spoke, in order, in the `SelectorGroupChat`.
4. **Validated result** — the `FlightSearchReport` after the exit guard, with each
   option's date and price.
5. **Observability** — tokens per stage, the routing overhead, the raw extraction text
   and every agent message.

The same run from the command line prints the same trace as text:

    python3 main_advanced.py "Find flights from SFO to JFK on November 5 under $200"

To reproduce the real-runs panel on the course page (five queries, stdout kept verbatim,
keys scrubbed before anything is written):

    python3 examples/capture_live_runs.py
    python3 examples/capture_live_runs.py --add "label" "one more query"

If a run stops with `Run interrupted`, the message names the cause: a 401 is a wrong or
unfunded OpenAI key; a Browserbase error on the second date is usually the concurrency
limit above; a `[fetch warning]` after 60 seconds means Kayak did not render prices for
that route and date.

## Layout of `flightfinder/`

    schemas.py            the typed boundary: ParsedQuery, FlightSearchReport
    tools.py              URL building, Browserbase fetch, page condensing/slicing
    fanout.py             date-range planning (plan_search_dates) + concurrent search/extract fan-out
    agents_advanced.py    the four agents, selector_func, candidate_func, termination
    main_advanced.py      the entry point; prints every stage, the exit guard and the token table
    web_app.py            the local page above; calls the same pipeline
    test_offline.py       72 checks, real AutoGen, scripted model, no key
    test_integration.py   seven end-to-end paths, 35 checks, no key
    examples/             comparisons, live captures, and the JS-port verification scripts

`flightfinder/README.md` goes into the design: why comparisons rather than a demo run,
the date-range budget guard, the exit guard, and how the page's JavaScript port is
checked against the Python.
