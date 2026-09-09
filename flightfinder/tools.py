"""Tool layer for the FlightFinder agentic workflow.

This file demonstrates a core agentic-AI design principle: keep deterministic operations in code and expose them as clean capabilities to the rest of the system. URL construction, browser fetching, page-text condensation, and content slicing are all handled here before any agent reasons over the result.

The public boundary is `search_flights`: one function that returns the search URL and page content for a route/date. Keeping this as one atomic capability makes the downstream agent workflow easier to reason about in class."""

import os
import re
from typing import Optional

from html2text import html2text
from playwright.async_api import async_playwright




# Shared readiness signal: prices indicate that rendered flight results are likely present.
PRICE_PATTERN = re.compile(r"\$\s?\d[\d,]*")

MAX_CONTENT_CHARS = 8000
MAX_WAIT_MS = 60_000
POLL_INTERVAL_MS = 3_000


def kayak_search_url(
    departure: str,
    destination: str,
    date: str,
    return_date: Optional[str] = None,
) -> str:
    """Generate a Kayak flight search URL from structured flight fields."""
    url = f"https://www.kayak.com/flights/{departure}-{destination}/{date}"
    if return_date:
        url += f"/{return_date}"



    url += "?currency=USD"
    return url


def _condense(text: str) -> str:
    """Reduce rendered page text to lines that are more useful for flight extraction."""

    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)

    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)

    lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if not re.search(r"[0-9A-Za-z\u4e00-\u9fff]", line):
            continue
        lines.append(line)


    deduped = []
    for line in lines:
        if deduped and deduped[-1] == line:
            continue
        deduped.append(line)

    return "\n".join(deduped)


def _slice_around_prices(text: str, limit: int = MAX_CONTENT_CHARS) -> str:
    """Keep the page segment most likely to contain flight rows by anchoring near prices."""
    total_len = len(text)
    matches = list(PRICE_PATTERN.finditer(text))
    price_count = len(matches)

    if total_len <= limit:
        header = f"[fetch diagnostic] Page text has {total_len} characters, was not truncated, and contains {price_count} price markers."
        return f"{header}\n\n{text}"

    if price_count == 0:


        header = (
            f"[fetch diagnostic] Page text has {total_len} characters, but no price marker ($) was detected. "
            f"The flight list may not have rendered successfully. Showing the first {limit} characters for diagnosis."
        )
        return f"{header}\n\n{text[:limit]}"

    first_price_at = matches[0].start()

    start = max(0, first_price_at - 500)
    end = min(total_len, start + limit)
    header = (
        f"[fetch diagnostic] Page text has {total_len} characters and {price_count} price markers; "
        f"the first price starts at character {first_price_at}. The slice below covers characters {start}-{end}, "
        f"which should be the flight-list region rather than the top navigation."
    )
    return f"{header}\n\n{text[start:end]}"


async def _wait_for_results(page) -> int:
    """Poll the browser page until flight-like prices appear or the wait limit is reached."""
    waited = 0
    while waited < MAX_WAIT_MS:
        await page.wait_for_timeout(POLL_INTERVAL_MS)
        waited += POLL_INTERVAL_MS
        try:
            body_text = await page.evaluate("() => document.body ? document.body.innerText : ''")
        except Exception:
            continue
        found = len(PRICE_PATTERN.findall(body_text or ""))

        if found >= 3:
            return found
    return 0


async def browserbase_fetch(url: str) -> str:
    """Fetch a JavaScript-rendered page through Browserbase and return condensed text."""
    api_key = os.environ.get("BROWSERBASE_API_KEY")
    if not api_key:
        return (
            "[browserbase_fetch error] BROWSERBASE_API_KEY was not found in the environment. "
            "Configure it in .env before running a live fetch."
        )

    try:
        from browserbase import Browserbase
    except ImportError:
        return "[browserbase_fetch error] browserbase is not installed. Run pip install browserbase first."

    project_id = os.environ.get("BROWSERBASE_PROJECT_ID") or None

    try:
        bb = Browserbase(api_key=api_key)
        session = bb.sessions.create(project_id=project_id) if project_id else bb.sessions.create()

        async with async_playwright() as playwright:
            browser = await playwright.chromium.connect_over_cdp(session.connect_url)



            try:
                context = browser.contexts[0]
                page = context.pages[0] if context.pages else await context.new_page()

                await page.goto(url, wait_until="domcontentloaded", timeout=60_000)


                found = await _wait_for_results(page)

                html = await page.content()
            finally:
                try:
                    await browser.close()
                except Exception:
                    pass

        text = _condense(html2text(html))
        result = _slice_around_prices(text)

        if found == 0:
            result = (
                "[fetch warning] Waited 60 seconds and still did not detect flight prices on the page. "
                "Common causes: Kayak anti-bot protection, no results for this route/date, or a changed page structure.\n\n"
                + result
            )
        return result

    except Exception as exc:
        return f"[browserbase_fetch error] Fetch failed: {exc!r}"


# Public tool boundary consumed by the rest of the agentic workflow.
async def search_flights(
    departure: str,
    destination: str,
    date: str,
    return_date: Optional[str] = None,
) -> str:
    """Atomic flight-search capability used by the workflow: build URL, fetch page, return text."""
    url = kayak_search_url(departure, destination, date, return_date)
    content = await browserbase_fetch(url)
    return f"Search URL: {url}\n\nPage content:\n{content}"
