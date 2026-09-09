"""
Capture REAL FlightFinder runs for the course page.

This does not reimplement anything. It runs `main_advanced.py` unchanged, once per
query, and keeps its stdout verbatim. That script already prints every stage, the
ParsedQuery, the fan-out text, each team message, the actual SelectorGroupChat path,
the final report, and the token table -- which is exactly what the page needs.

    cd flightfinder
    python3 examples/capture_live_runs.py                    # the five queries below
    python3 examples/capture_live_runs.py --add "label" "query"   # one more run, appended

Needs a .env beside main_advanced.py containing your own keys:

    OPENAI_API_KEY=...
    OPENAI_MODEL=gpt-4o-mini          # optional
    BROWSERBASE_API_KEY=...
    BROWSERBASE_PROJECT_ID=...

The keys are read by the application itself. This script never prints them, and
scrubs anything key-shaped out of the captured text before writing the file, in
case a traceback echoes the environment. Read live_runs.json before sending it
anywhere -- it is your run, with your data in it.

Costs real money: 5 runs x (1 parse + 1-3 extractions + 1-2 routing + 2-4 team
calls) on your OpenAI key, plus up to 10 Browserbase sessions. On gpt-4o-mini this
is cents, but check your own pricing.
"""
import datetime
import json
import os
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
APP_DIR = HERE.parent
ENTRY = APP_DIR / "main_advanced.py"

# Chosen to exercise different paths through the same code, not to look good.
QUERIES = [
    ("early November window, budget $200",
     "Find flights from San Francisco (SFO) to New York (JFK) in early November, "
     "within a $200 budget. Any day in early November works."),
    ("fixed date, no budget",
     "Find flights from SFO to JFK on November 5. The date cannot change."),
    ("budget 180, just under the cheapest fare",
     "Find a flight from SFO to JFK on November 5 under $180."),
    ("two-day window, budget $200",
     "Find flights from SFO to JFK on November 5 or 6, under $200."),
    ("window mostly behind us",
     "I need to get from SFO to JFK today or tomorrow; earlier this week would also have been fine."),
]

# Defensive scrub: never let a key reach the JSON, even via a traceback.
SECRET_RX = [
    re.compile(r"sk-[A-Za-z0-9_\-]{16,}"),
    re.compile(r"bb_[A-Za-z0-9_\-]{16,}"),
    re.compile(r"(?i)(api[_-]?key|token|secret)\s*[=:]\s*\S+"),
]


def scrub(text: str) -> str:
    for rx in SECRET_RX:
        text = rx.sub("[REDACTED]", text)
    for name in ("OPENAI_API_KEY", "BROWSERBASE_API_KEY", "BROWSERBASE_PROJECT_ID"):
        val = os.environ.get(name)
        if val and len(val) > 8:
            text = text.replace(val, "[REDACTED]")
    return text


def versions() -> dict:
    import importlib.metadata as md
    out = {}
    for pkg in ("autogen-agentchat", "autogen-core", "autogen-ext", "pydantic", "openai"):
        try:
            out[pkg] = md.version(pkg)
        except Exception:
            pass
    return out


def run_one(label: str, query: str) -> dict:
    print(f"--- {label}\n    {query}")
    t0 = datetime.datetime.now()
    r = subprocess.run([sys.executable, str(ENTRY), query],
                       capture_output=True, text=True, cwd=APP_DIR, timeout=900)
    secs = (datetime.datetime.now() - t0).total_seconds()
    stdout, stderr = scrub(r.stdout.rstrip()), scrub(r.stderr.rstrip())
    ok = r.returncode == 0 and "Run interrupted" not in stdout
    print(f"    exit={r.returncode}  {secs:.0f}s  {len(stdout.splitlines())} lines"
          f"  {'ok' if ok else 'FAILED'}")
    if not ok and stderr:
        print("    last stderr line:", stderr.splitlines()[-1][:160])
    return {"label": label, "query": query, "seconds": round(secs, 1),
            "exit": r.returncode, "ok": ok, "stdout": stdout, "stderr": stderr}


def main() -> None:
    if not ENTRY.exists():
        sys.exit(f"main_advanced.py not found in {APP_DIR}; this script lives in its examples/ folder.")
    if not (APP_DIR / ".env").exists() and not os.environ.get("OPENAI_API_KEY"):
        print("warning: no .env beside main_advanced.py and OPENAI_API_KEY is unset -- the run will fail on a missing key\n")

    out = {
        "captured": datetime.datetime.now().isoformat(timespec="seconds"),
        "python": sys.version.split()[0],
        "versions": versions(),
        "model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini (default)"),
        "note": "stdout of `python main_advanced.py <query>`, verbatim, keys scrubbed",
        "runs": [],
    }

    dest = HERE / "live_runs.json"

    # --add "label" "query": run one more query and append it to the existing file.
    if len(sys.argv) >= 2 and sys.argv[1] == "--add":
        if len(sys.argv) != 4:
            sys.exit('usage: capture_live_runs.py --add "label" "query"')
        if dest.exists():
            out = json.loads(dest.read_text())
        out["runs"].append(run_one(sys.argv[2], sys.argv[3]))
    else:
        for label, query in QUERIES:
            out["runs"].append(run_one(label, query))
            if len(out["runs"]) == 1 and "Error code: 403" in out["runs"][0]["stdout"] + out["runs"][0]["stderr"]:
                print("    first API call returned 403; stopping after first run")
                break

    dest.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    good = sum(1 for x in out["runs"] if x["ok"])
    print(f"\nwrote {dest}  ({dest.stat().st_size // 1024} KB)  --  {good}/{len(out['runs'])} runs succeeded")
    print("Open it and read it before sending it on. It contains your real search results.")


if __name__ == "__main__":
    main()
