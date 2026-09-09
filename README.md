# Agentic Systems Studio — class 01

A one-hour class on multi-agent agentic AI, built around one real application.
Three things live in this repository, and each one is checked against the others.

    agentic-systems-studio.html   the course page — three interactive pages, self-contained, open it in a browser
    teaching-script.md            the lecture script: English to be read aloud, full Chinese translation above each paragraph, stage directions in parentheses
    flightfinder/                 FlightFinder Pro, the AutoGen application the case page is about (its own README explains how to run it)

The published copy of the course page is at
https://claude.ai/code/artifact/2eaf01dd-d795-4af0-a839-132db3131a6e — the file here is
the same page.

## How the page and the code correspond

The course page has three pages: **00 Agency** (five rungs of autonomy), **01 Routing**
(who speaks next) and **02 FlightFinder Pro** (the case). Every number on page 02 comes
from a file in `flightfinder/`:

| on the page                        | produced by                                             | data file                          |
|------------------------------------|---------------------------------------------------------|------------------------------------|
| the four comparisons (E, B, C, D)  | `flightfinder/examples/run_comparisons.py` — real AutoGen, scripted model, no key | `flightfinder/examples/comparisons.json` |
| the real-runs panel                | `flightfinder/examples/capture_live_runs.py` — real Kayak pages, real model | `flightfinder/examples/live_runs.json` (keys scrubbed) |
| the runnable copy                  | a JavaScript port of `fanout.py` / `agents_advanced.py` / `main_advanced.py`, diffed against the Python on 20,193 inputs by `flightfinder/examples/verify_port_*.py` | — |
| the concept table                  | the eight source files, named row by row                | — |

Pages 00 and 01 replay captured runs of small standalone Python programs whose model is
a scripted function; the page says so where the numbers appear.

## Run the application

    python3 -m venv .venv && source .venv/bin/activate
    pip install -r flightfinder/requirements.txt
    cd flightfinder
    python3 examples/run_comparisons.py      # no key, no network — start here
    python3 test_offline.py                  # 72 checks, no key

Real runs need your own OpenAI and Browserbase keys in `flightfinder/.env`
(copy `.env.example`). `.env` is git-ignored; never commit it.
