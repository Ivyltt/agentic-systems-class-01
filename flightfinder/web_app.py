"""Local classroom web entry point for FlightFinder Pro.

Run ``python web_app.py`` and open http://127.0.0.1:8000. The server uses only
Python's standard library; the existing AutoGen pipeline remains the application
backend.
"""

import argparse
import asyncio
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from dotenv import load_dotenv

from main_advanced import execute_search


PAGE = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>FlightFinder Pro</title>
  <style>
    :root {
      --ink: #172121; --muted: #62706d; --line: #d9dfdc; --paper: #f7f8f6;
      --white: #ffffff; --teal: #087e72; --teal-dark: #075f58; --amber: #c77700;
      --amber-bg: #fff5df; --red: #b34235; --green-bg: #e8f5ef; --shadow: 0 12px 28px rgba(23,33,33,.08);
    }
    * { box-sizing: border-box; }
    body { margin: 0; color: var(--ink); background: var(--paper); font: 15px/1.5 Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    button, textarea { font: inherit; }
    .shell { min-height: 100vh; display: grid; grid-template-columns: 360px minmax(0, 1fr); }
    aside { position: sticky; top: 0; height: 100vh; padding: 30px 26px; background: #102827; color: white; overflow-y: auto; }
    .eyebrow { margin: 0 0 5px; color: #87c9c1; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: .08em; }
    h1 { margin: 0; font-size: 30px; line-height: 1.12; letter-spacing: 0; }
    .intro { margin: 12px 0 24px; color: #c5d7d4; }
    label { display: block; margin-bottom: 8px; font-size: 13px; font-weight: 700; }
    textarea { width: 100%; min-height: 150px; resize: vertical; padding: 13px; color: var(--ink); background: white; border: 1px solid #7c9692; border-radius: 6px; outline: none; }
    textarea:focus { border-color: #54c4b7; box-shadow: 0 0 0 3px rgba(84,196,183,.2); }
    .examples { display: grid; gap: 7px; margin: 12px 0 18px; }
    .example { padding: 8px 10px; color: #d5e6e3; background: transparent; border: 1px solid #496864; border-radius: 5px; text-align: left; cursor: pointer; }
    .example:hover { border-color: #88c8c0; color: white; }
    .run { width: 100%; min-height: 44px; padding: 10px 14px; color: white; background: var(--teal); border: 0; border-radius: 6px; font-weight: 750; cursor: pointer; }
    .run:hover { background: #099488; }
    .run:disabled { cursor: wait; opacity: .7; }
    .side-note { margin: 18px 0 0; padding-top: 15px; color: #9fbbb7; border-top: 1px solid #34514d; font-size: 12px; }
    main { min-width: 0; padding: 30px clamp(22px, 4vw, 58px) 60px; }
    .topline { display: flex; align-items: center; justify-content: space-between; gap: 18px; margin-bottom: 22px; }
    .topline h2 { margin: 0; font-size: 20px; letter-spacing: 0; }
    .status { padding: 5px 9px; border: 1px solid var(--line); border-radius: 4px; color: var(--muted); background: white; font-size: 12px; font-weight: 700; }
    .status.running { color: var(--amber); border-color: #e5bd75; background: var(--amber-bg); }
    .status.done { color: var(--teal-dark); border-color: #8cc8bd; background: var(--green-bg); }
    .status.error { color: var(--red); border-color: #e1aaa4; background: #fff1ef; }
    .empty { padding: 52px 0; border-top: 1px solid var(--line); color: var(--muted); }
    .empty strong { display: block; margin-bottom: 8px; color: var(--ink); font-size: 18px; }
    section { padding: 24px 0; border-top: 1px solid var(--line); }
    section h3 { margin: 0 0 14px; font-size: 15px; letter-spacing: 0; }
    .flow { display: grid; grid-template-columns: repeat(4, minmax(130px, 1fr)); align-items: stretch; gap: 10px; }
    .flow-step { position: relative; min-height: 82px; padding: 12px; background: white; border: 1px solid var(--line); border-radius: 6px; }
    .flow-step b { display: block; margin-bottom: 4px; font-size: 13px; }
    .flow-step span { color: var(--muted); font-size: 12px; }
    .flow-step.active { border-color: #86bfb7; box-shadow: var(--shadow); }
    .facts { display: grid; grid-template-columns: repeat(4, minmax(120px, 1fr)); gap: 1px; overflow: hidden; border: 1px solid var(--line); border-radius: 6px; background: var(--line); }
    .fact { min-width: 0; padding: 11px 12px; background: white; }
    .fact dt { margin: 0 0 3px; color: var(--muted); font-size: 11px; text-transform: uppercase; }
    .fact dd { margin: 0; overflow-wrap: anywhere; font-weight: 700; }
    .decision { display: grid; grid-template-columns: minmax(130px, .8fr) minmax(180px, 1.2fr) minmax(220px, 2fr); gap: 10px; align-items: center; }
    .decision-box { min-height: 72px; padding: 12px; border: 1px solid var(--line); border-radius: 6px; background: white; }
    .decision-box small { display: block; color: var(--muted); }
    .dates, .path { display: flex; flex-wrap: wrap; gap: 7px; margin-top: 7px; }
    .date-chip { padding: 5px 8px; color: #754900; background: var(--amber-bg); border: 1px solid #ecc67e; border-radius: 4px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 12px; }
    .path-node { padding: 6px 9px; color: var(--teal-dark); background: var(--green-bg); border: 1px solid #a9d4cc; border-radius: 4px; font-size: 12px; font-weight: 700; }
    .arrow { align-self: center; color: #8e9a97; }
    .summary { display: flex; align-items: baseline; gap: 12px; margin-bottom: 13px; }
    .summary strong { font-size: 22px; }
    .summary span { color: var(--muted); }
    .table-wrap { overflow-x: auto; border: 1px solid var(--line); border-radius: 6px; background: white; }
    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    th, td { padding: 10px 12px; border-bottom: 1px solid #e9edeb; text-align: left; vertical-align: top; }
    th { color: var(--muted); background: #fafbf9; font-size: 11px; text-transform: uppercase; }
    tr:last-child td { border-bottom: 0; }
    .price { color: var(--teal-dark); font-weight: 800; }
    .notes { margin: 13px 0 0; color: var(--muted); }
    .tokens { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
    .token { padding: 10px 11px; border-left: 3px solid #9bb8b3; background: white; }
    .token b { display: block; font-size: 17px; }
    .token span { color: var(--muted); font-size: 11px; }
    details { margin-top: 9px; background: white; border: 1px solid var(--line); border-radius: 6px; }
    summary { padding: 11px 13px; cursor: pointer; font-weight: 700; }
    pre { margin: 0; padding: 13px; overflow: auto; border-top: 1px solid var(--line); color: #33413f; background: #fbfcfb; font: 12px/1.55 ui-monospace, SFMono-Regular, Menlo, monospace; white-space: pre-wrap; }
    .error-box { padding: 14px; color: var(--red); background: #fff1ef; border: 1px solid #e1aaa4; border-radius: 6px; }
    @media (max-width: 900px) {
      .shell { grid-template-columns: 1fr; }
      aside { position: static; height: auto; }
      .flow, .facts { grid-template-columns: repeat(2, minmax(130px, 1fr)); }
      .decision { grid-template-columns: 1fr; }
      .tokens { grid-template-columns: repeat(2, 1fr); }
    }
    @media (max-width: 560px) {
      aside, main { padding: 22px 18px; }
      .flow, .facts, .tokens { grid-template-columns: 1fr; }
      .topline { align-items: flex-start; }
    }
  </style>
</head>
<body>
<div class="shell">
  <aside>
    <p class="eyebrow">Agentic Systems Studio</p>
    <h1>FlightFinder Pro</h1>
    <p class="intro">One request becomes a bounded search plan, parallel evidence, a routed agent team, and a validated report.</p>
    <form id="search-form">
      <label for="query">Flight request</label>
      <textarea id="query" required></textarea>
      <div class="examples" aria-label="Example requests">
        <button class="example" type="button" data-kind="exact">Exact date</button>
        <button class="example" type="button" data-kind="around">Around a preferred date</button>
        <button class="example" type="button" data-kind="range">Flexible date range</button>
      </div>
      <button class="run" id="run-button" type="submit">Run complete workflow</button>
    </form>
    <p class="side-note">Search fan-out is capped at three dates. The model interprets intent; code owns the execution budget.</p>
  </aside>
  <main>
    <div class="topline">
      <h2>Execution trace</h2>
      <span class="status" id="status">Ready</span>
    </div>
    <div id="results" class="empty"><strong>No run yet</strong>Choose an example or enter a flight request to inspect every boundary in the system.</div>
  </main>
</div>
<script>
  const form = document.querySelector('#search-form');
  const query = document.querySelector('#query');
  const results = document.querySelector('#results');
  const statusEl = document.querySelector('#status');
  const runButton = document.querySelector('#run-button');
  const now = new Date();
  const targetYear = now.getMonth() >= 10 ? now.getFullYear() + 1 : now.getFullYear();
  const examples = {
    exact: `Find flights from SFO to JFK on November 5, ${targetYear}. The date cannot change. Budget is $250.`,
    around: `Find flights from SFO to JFK around November 5, ${targetYear}, preferably nonstop and under $250.`,
    range: `Find the best flight from SFO to JFK between November 3 and November 9, ${targetYear}, under $250. My dates are flexible.`
  };
  query.value = examples.range;

  document.querySelectorAll('.example').forEach(button => {
    button.addEventListener('click', () => { query.value = examples[button.dataset.kind]; query.focus(); });
  });

  const esc = value => String(value ?? '').replace(/[&<>'"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));
  const label = key => key.replaceAll('_', ' ').replace(/\b\w/g, char => char.toUpperCase());
  const contentText = value => typeof value === 'string' ? value : JSON.stringify(value, null, 2);

  function render(data) {
    const parsed = data.parsed_query || {};
    const report = data.report || { options: [], notes: 'No structured report was produced.' };
    const options = report.options || [];
    const facts = Object.entries(parsed).map(([key, value]) => `<div class="fact"><dt>${esc(label(key))}</dt><dd>${esc(value)}</dd></div>`).join('');
    const dates = (data.search_dates || []).map((date, index) => `<span class="date-chip">${String.fromCharCode(65 + index)} · ${esc(date)}</span>`).join('');
    const path = (data.agent_path || []).map((agent, index) => `${index ? '<span class="arrow">→</span>' : ''}<span class="path-node">${esc(agent)}</span>`).join('');
    const rows = options.map(item => `<tr><td><strong>${esc(item.airline)}</strong><br><small>${esc(item.source_strategy)}</small></td><td>${esc(item.departure_date || 'See strategy')}</td><td>${esc(item.departure_time)} – ${esc(item.arrival_time)}</td><td>${esc(item.duration)}</td><td>${esc(item.stops)}</td><td class="price">$${esc(Number(item.price_usd).toFixed(0))}</td></tr>`).join('');
    const tokenEntries = Object.entries(data.token_usage || {});
    const tokens = tokenEntries.map(([key, value]) => `<div class="token"><b>${esc(value)}</b><span>${esc(key)}</span></div>`).join('');
    const messages = (data.agent_messages || []).map(item => `${item.source} (${item.message_type})\n${contentText(item.content)}`).join('\n\n' + '-'.repeat(60) + '\n\n');
    results.className = '';
    results.innerHTML = `
      <section>
        <h3>System shape</h3>
        <div class="flow">
          <div class="flow-step active"><b>1. Interpret</b><span>Parser agent turns language into a typed request.</span></div>
          <div class="flow-step active"><b>2. Plan + fan-out</b><span>Code caps the date range and searches concurrently.</span></div>
          <div class="flow-step active"><b>3. Coordinate</b><span>Ranker, optional critic, and summarizer collaborate.</span></div>
          <div class="flow-step active"><b>4. Guard</b><span>Code validates facts before returning the report.</span></div>
        </div>
      </section>
      <section><h3>1 · Parsed contract</h3><dl class="facts">${facts}</dl></section>
      <section>
        <h3>2 · Date-range decision</h3>
        <div class="decision">
          <div class="decision-box"><small>Model judgment</small><strong>${parsed.date_is_flexible ? 'Flexible range' : 'Exact date'}</strong></div>
          <div class="decision-box"><small>Structured window</small><strong>${esc(parsed.date_window_start || parsed.date)} → ${esc(parsed.date_window_end || parsed.date)}</strong></div>
          <div class="decision-box"><small>Code-owned plan · max 3</small><div class="dates">${dates}</div></div>
        </div>
      </section>
      <section><h3>3 · Actual agent path</h3><div class="path">${path}</div></section>
      <section>
        <h3>4 · Validated result</h3>
        <div class="summary"><strong>${options.length} option${options.length === 1 ? '' : 's'}</strong><span>${report.within_budget ? 'At least one is within budget' : 'No returned option is within budget'}</span></div>
        ${options.length ? `<div class="table-wrap"><table><thead><tr><th>Flight</th><th>Date</th><th>Time</th><th>Duration</th><th>Stops</th><th>Price</th></tr></thead><tbody>${rows}</tbody></table></div>` : '<div class="error-box">No usable flight options were returned.</div>'}
        <p class="notes">${esc(report.notes)}</p>
      </section>
      <section><h3>Observability</h3><div class="tokens">${tokens}</div>
        <details><summary>Parallel extraction evidence</summary><pre>${esc(data.fanout_results)}</pre></details>
        <details><summary>Agent messages</summary><pre>${esc(messages)}</pre></details>
      </section>`;
  }

  form.addEventListener('submit', async event => {
    event.preventDefault();
    runButton.disabled = true;
    runButton.textContent = 'Running…';
    statusEl.className = 'status running';
    statusEl.textContent = 'Searching and coordinating';
    results.className = 'empty';
    results.innerHTML = '<strong>Workflow in progress</strong>Up to three browser searches are running concurrently. A live run can take about one minute.';
    try {
      const response = await fetch('/api/search', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({query: query.value.trim()}) });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || 'The workflow failed.');
      render(payload);
      statusEl.className = 'status done';
      statusEl.textContent = 'Complete';
    } catch (error) {
      results.className = '';
      results.innerHTML = `<div class="error-box"><strong>Run failed</strong><br>${esc(error.message)}</div>`;
      statusEl.className = 'status error';
      statusEl.textContent = 'Needs attention';
    } finally {
      runButton.disabled = false;
      runButton.textContent = 'Run complete workflow';
    }
  });
</script>
</body>
</html>"""


class FlightFinderHandler(BaseHTTPRequestHandler):
    def _send(self, status: int, content_type: str, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path not in ("/", "/index.html"):
            self._send(404, "text/plain; charset=utf-8", b"Not found")
            return
        self._send(200, "text/html; charset=utf-8", PAGE.encode("utf-8"))

    def do_POST(self) -> None:
        if self.path != "/api/search":
            self._send(404, "application/json", b'{"error":"Not found"}')
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 1 or length > 20_000:
                raise ValueError("Request body must be between 1 and 20,000 bytes.")
            payload = json.loads(self.rfile.read(length))
            query = str(payload.get("query", "")).strip()
            if not query:
                raise ValueError("Enter a flight request first.")
            result = asyncio.run(execute_search(query))
            body = json.dumps(result, ensure_ascii=False, default=str).encode("utf-8")
            self._send(200, "application/json; charset=utf-8", body)
        except ValueError as exc:
            body = json.dumps({"error": str(exc)}, ensure_ascii=False).encode("utf-8")
            self._send(400, "application/json; charset=utf-8", body)
        except Exception as exc:
            body = json.dumps({"error": f"{type(exc).__name__}: {exc}"}, ensure_ascii=False).encode("utf-8")
            self._send(500, "application/json; charset=utf-8", body)

    def log_message(self, format: str, *args) -> None:
        print(f"[web] {self.address_string()} - {format % args}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the FlightFinder Pro classroom web app.")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    # The classroom project owns its local configuration. This also prevents a
    # placeholder inherited from a shell or IDE from shadowing a valid .env key.
    load_dotenv(override=True)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), FlightFinderHandler)
    print(f"FlightFinder Pro is available at http://127.0.0.1:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
