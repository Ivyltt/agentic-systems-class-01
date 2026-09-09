"""Run the REAL fanout/agents functions over a big input grid and dump the results.
Pair with verify_port_diff.py, which runs the page's JavaScript port on the same
inputs and diffs the two. No key, no network."""
import sys, os, json, datetime, itertools
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fanout import plan_search_dates, MAX_SEARCH_DATES
from agents_advanced import _critic_verdict, make_selector_func, make_candidate_func

TODAY = datetime.date(2026, 9, 9)          # pinned so both sides agree
T = TODAY.isoformat()
class M:
    def __init__(s, source, content=""): s.source, s.content = source, content
sel = make_selector_func(); cand = make_candidate_func()

def d(k): return (TODAY + datetime.timedelta(days=k)).isoformat()

# ---- plan_search_dates: anchors, windows (as offsets from today), flags, max_dates
anchors = [d(k) for k in (-3, 0, 1, 5, 30, 60)] + ["Nov 5", "", "2026-13-40", "20261105", " 2026-11-05 "]
windows = [(None, None), (-2, 0), (-1, 1), (0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (0, 7), (0, 10),
           (2, 9), (3, 3), (5, 2), (-10, -4), (28, 34), (58, 64), (55, 70), (1, 60), (60, 60), ("bad", 5), (5, "bad")]
plans = []
for a, (ws, we), flex, mx in itertools.product(anchors, windows, (True, False), (1, 2, 3)):   # 4+: Python tie-breaks via set order (see README)
    s = None if ws is None else (ws if isinstance(ws, str) else d(ws))
    e = None if we is None else (we if isinstance(we, str) else d(we))
    try:
        out = plan_search_dates(a, s, e, flex, mx, today=TODAY)
    except Exception as ex:
        out = "EXC:" + type(ex).__name__
    plans.append({"in": [a, s, e, flex, mx], "out": out})

# ---- routing: every conversation prefix up to 5 messages
SOURCES = ["user", "merge_ranker_agent", "budget_critic_agent", "summarizer_agent"]
CRITIC = ["APPROVED - fine", "RETRY - relax to 179", "NO_DATA - empty"]
paths = []
for n in range(0, 6):
    for combo in itertools.product(SOURCES, repeat=n):
        for msgs in itertools.product(*[[(s, t) for t in CRITIC] if s == "budget_critic_agent" else [(s, "...")] for s in combo]):
            paths.append(list(msgs))
VERDICTS = ["APPROVED - looks good", "RETRY - relax", "NO_DATA - nothing", "  approved (lower)", "The list is fine, APPROVED",
            "", "RETRYING later", "no_data here", "retry", "APPROVE", "NODATA", "  RETRY  ", "xyz"]
out = {"today": T, "max_default": MAX_SEARCH_DATES, "plans": plans,
       "verdict": {v: _critic_verdict(v) for v in VERDICTS},
       "sel": [sel([M(s, c) for s, c in p]) for p in paths],
       "cand": [cand([M(s, c) for s, c in p]) for p in paths], "paths": paths}
json.dump(out, open(os.path.join(os.path.dirname(__file__), "port_reference.json"), "w"))
print(f"plan_search_dates cases: {len(plans)}  routing prefixes: {len(paths)}  verdicts: {len(VERDICTS)}")
