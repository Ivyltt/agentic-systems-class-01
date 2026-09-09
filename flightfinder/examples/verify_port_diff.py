"""Run the page's JavaScript port on the reference inputs and diff against Python.
    python3 examples/verify_port_python.py   # first: writes port_reference.json
    python3 examples/verify_port_diff.py            # diffs against ../agentic-systems-studio.html
    python3 examples/verify_port_diff.py PAGE.html  # or any other copy of the page
"""
import asyncio, json, os, sys
from playwright.async_api import async_playwright
here = os.path.dirname(os.path.abspath(__file__))
PY = json.load(open(os.path.join(here, "port_reference.json")))
PAGE = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "..", "..", "agentic-systems-studio.html")   # the page at the repo root
JS = """(C)=>{
  const plans = C.plans.map(p => { const [a,s,e,flex,mx]=p.in;
    try { return FF.planSearchDates(a, s, e, flex, mx, C.today); } catch(err){ return "EXC:"+err.name; } });
  const verdict={}; C.verdicts.forEach(v=>{ verdict[v]=FF.criticVerdict(v); });
  const sel=[],cand=[];
  C.paths.forEach(p=>{ const m=p.map(x=>({source:x[0],content:x[1]})); sel.push(FF.selectorFunc(m)); cand.push(FF.candidateFunc(m)); });
  return {plans,verdict,sel,cand};
}"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page()
        await pg.goto("file://" + os.path.abspath(PAGE)); await pg.wait_for_timeout(1200)
        js = await pg.evaluate(JS, {"plans": PY["plans"], "verdicts": list(PY["verdict"].keys()),
                                    "today": PY["today"], "paths": PY["paths"]})
        await b.close()
    bad = []
    for p, jv in zip(PY["plans"], js["plans"]):
        if p["out"] != jv: bad.append(("plan_search_dates", p["in"], p["out"], jv))
    for k, v in PY["verdict"].items():
        if js["verdict"].get(k) != v: bad.append(("_critic_verdict", k, v, js["verdict"].get(k)))
    for p, a, c in zip(PY["paths"], PY["sel"], js["sel"]):
        if a != c: bad.append(("selector_func", [x[0] for x in p], a, c))
    for p, a, c in zip(PY["paths"], PY["cand"], js["cand"]):
        if a != c: bad.append(("candidate_func", [x[0] for x in p], a, c))
    total = len(PY["plans"]) + len(PY["verdict"]) + 2 * len(PY["paths"])
    print(f"compared {total} cases: {len(PY['plans'])} plan_search_dates inputs, {len(PY['verdict'])} verdicts, "
          f"{len(PY['paths'])} conversation prefixes x 2 routing functions")
    if not bad: print("ALL MATCH")
    else:
        print(f"{len(bad)} DIVERGENCES (first 20):")
        for r in bad[:20]: print("  ", r)
        sys.exit(1)
asyncio.run(main())
