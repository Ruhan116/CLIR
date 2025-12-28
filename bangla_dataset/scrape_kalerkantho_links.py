import re
import time
import argparse
import random
from pathlib import Path
import requests
from urllib.parse import urlparse

try:
    import cloudscraper
except Exception:
    cloudscraper = None

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
    "Connection": "keep-alive",
}

DEFAULT_SITEMAPS = [
    "https://www.kalerkantho.com/daily-sitemap/2025-12-25/sitemap.xml",
    "https://www.kalerkantho.com/daily-sitemap/2025-12-24/sitemap.xml",
    "https://www.kalerkantho.com/daily-sitemap/2025-11-23/sitemap.xml",
    "https://www.kalerkantho.com/daily-sitemap/2025-10-16/sitemap.xml",
    "https://www.kalerkantho.com/daily-sitemap/2025-07-01/sitemap.xml",
]

OUT_PATH = Path(__file__).resolve().parent / "kalerkantho_links"


def fetch_sitemap(source: str, use_playwright: bool = False) -> str:
    if source.startswith("http://") or source.startswith("https://"):
        # Prefer cloudscraper to handle Cloudflare/anti-bot if available
        if cloudscraper is not None:
            try:
                scraper = cloudscraper.create_scraper()
                r = scraper.get(source, headers=HEADERS, timeout=20)
                r.raise_for_status()
                return r.text
            except Exception as e:
                print(f"cloudscraper failed for {source}: {e}")

        # fallback to requests with browser-like headers
        try:
            r = requests.get(source, headers=HEADERS, timeout=20)
            r.raise_for_status()
            return r.text
        except Exception as e:
            print(f"Failed to fetch {source} with requests: {e}")
            # final fallback: try Playwright (real browser) if requested/available
            if use_playwright:
                try:
                    return fetch_with_playwright(source, timeout=20)
                except Exception as e2:
                    print(f"Playwright fallback failed: {e2}")
            return ""
    else:
        p = Path(source)
        if p.exists():
            return p.read_text(encoding="utf-8")
        else:
            print(f"Local file not found: {source}")
            return ""


def extract_locs(text: str):
    pattern = re.compile(r"<loc>\s*(https?://[^<\s]+)\s*</loc>", re.IGNORECASE)
    return pattern.findall(text)


def is_article_url(url: str) -> bool:
    # exclude AMP/media/gallery pages
    if "/amp/" in url or "/photos/" in url or "/gallery/" in url:
        return False
    h = urlparse(url).hostname or ""
    return h.endswith("kalerkantho.com")


def dedupe_preserve_order(items):
    seen = set()
    out = []
    for it in items:
        if it not in seen:
            seen.add(it)
            out.append(it)
    return out


def main(sources=None, delay: float = 2.0, jitter: float = 0.0, use_playwright: bool = False):
    sources = sources or DEFAULT_SITEMAPS
    all_locs = []
    for i, src in enumerate(sources, start=1):
        print(f"Processing source ({i}/{len(sources)}): {src}")
        text = fetch_sitemap(src, use_playwright=use_playwright)
        if not text:
            print(f"  (no content from {src})")
        else:
            locs = extract_locs(text)
            print(f"  found {len(locs)} <loc> entries in source")
            all_locs.extend(locs)

        if delay and i < len(sources):
            if jitter and jitter > 0:
                sleep_time = max(0.1, random.uniform(delay - jitter, delay + jitter))
            else:
                sleep_time = delay
            print(f"  sleeping {sleep_time:.2f} seconds before next sitemap")
            time.sleep(sleep_time)

    all_locs = [u.strip() for u in all_locs]
    filtered = [u for u in all_locs if is_article_url(u)]
    print(f"Total locs before filtering: {len(all_locs)}, after filter: {len(filtered)}")
    all_locs = dedupe_preserve_order(filtered)

    OUT_PATH.write_text("\n".join(all_locs), encoding="utf-8")
    print(f"Wrote {len(all_locs)} links to {OUT_PATH}")
def fetch_with_playwright(url: str, timeout: int = 20) -> str:
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        print("Playwright not installed. Install with: pip install playwright && python -m playwright install chromium")
        return ""

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context(user_agent=HEADERS.get("User-Agent"), viewport={"width": 1280, "height": 800})
            page = context.new_page()
            page.set_extra_http_headers({"Accept-Language": HEADERS.get("Accept-Language"), "Referer": HEADERS.get("Referer")})
            page.goto(url, wait_until="networkidle", timeout=timeout * 1000)
            content = page.content()
            browser.close()
            return content
    except Exception as e:
        print(f"Playwright fetch failed for {url}: {e}")
        return ""


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Fetch Kaler Kantho sitemaps and extract article links")
    p.add_argument("--delay", type=float, default=2.0, help="seconds to sleep between sitemap fetches (default 2.0)")
    p.add_argument("--jitter", type=float, default=0.0, help="jitter amount in seconds to randomize sleep (e.g. 0.5)")
    p.add_argument("--use-playwright", action="store_true", help="use Playwright browser fallback for blocked sitemaps")
    args = p.parse_args()
    main(delay=args.delay, jitter=args.jitter, use_playwright=args.use_playwright)
