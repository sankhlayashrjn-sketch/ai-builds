import time
from pathlib import Path
import requests
import config

PAGES = Path(__file__).parent / "fixtures" / "pages"

MAX_RETRIES = 5
RETRY_DELAY_SECONDS = 2


class ScrapeError(Exception):
    """Raised when a page could not be fetched after MAX_RETRIES attempts."""


def fetch(domain, path="home"):
    """Return cleaned page text for a domain (home or about page).

    Never returns "" for a failure - raises ScrapeError instead, so a dead
    page can't silently pass downstream as "page has no content".
    """
    if config.OFFLINE:
        fixture = PAGES / f"{domain}_{path}.txt"
        if not fixture.exists():
            raise ScrapeError(f"{domain}/{path}: fixture not found")
        return fixture.read_text()

    url = f"https://{domain}/" + ("" if path == "home" else path)
    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            return clean(resp.text)
        except Exception as e:
            last_err = e
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS * attempt)
    raise ScrapeError(f"{domain}/{path}: failed after {MAX_RETRIES} attempts ({last_err!r})")


def clean(html):
    lines = [l.strip() for l in html.splitlines() if len(l.split()) >= 8]
    seen, out = set(), []
    for l in lines:
        if l not in seen:
            seen.add(l)
            out.append(l)
    return "\n".join(out)[:8000]
