import re
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter, Retry
from urllib.parse import urlparse

LOCAL_XML = Path("d:/Win/CLIR/CLIR/all_scraped_xml.txt")
DEFAULT_SITEMAPS = [
    str(LOCAL_XML),
    "https://www.banglanews24.com/sitemap.xml",
    "https://www.banglanews24.com/daily-sitemap/2025-09-28/sitemap.xml",
    "https://www.banglanews24.com/daily-sitemap/2025-11-06/sitemap.xml",
    "https://www.banglanews24.com/daily-sitemap/2025-12-22/sitemap.xml",
]


OUT_PATH = Path(__file__).resolve().parent / "banglanews24_links"


def get_response(source: str, timeout: int = 15):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
    }

    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=(429, 502, 503, 504))
    session.mount("https://", HTTPAdapter(max_retries=retries))
    session.mount("http://", HTTPAdapter(max_retries=retries))

    try:
        resp = session.get(source, headers=headers, timeout=timeout, allow_redirects=True)
    except requests.RequestException as e:
        print(f"Error fetching {source}: {e}")
        return None

    if resp.status_code == 403:
        try:
            import cloudscraper
            scraper = cloudscraper.create_scraper()
            resp = scraper.get(source, headers=headers, timeout=timeout)
        except Exception:
            print(f"Received 403 for {source}")

    try:
        resp.raise_for_status()
    except requests.HTTPError as e:
        print(f"Error fetching {source}: {e}")
        return None

    return resp


def fetch_sitemap(source: str) -> str:
    if source.startswith("http://") or source.startswith("https://"):
        resp = get_response(source)
        return resp.text if resp else ""
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
    if "/amp/" in url:
        return False
    try:
        h = urlparse(url).hostname or ""
    except Exception:
        return False
    # filter out sitemap pages and index pages that are not articles
    low = url.lower()
    if "daily-sitemap" in low or low.endswith("sitemap.xml") or "/sitemap" in low:
        return False
    return h.endswith("banglanews24.com")


def dedupe_preserve_order(items):
    seen = set()
    out = []
    for it in items:
        if it not in seen:
            seen.add(it)
            out.append(it)
    return out


def main(sources=None):
    sources = sources or DEFAULT_SITEMAPS
    all_locs = []
    for src in sources:
        print(f"Processing source: {src}")
        text = fetch_sitemap(src)
        if not text:
            print(f"  (no content from {src})")
            continue
        locs = extract_locs(text)
        print(f"  found {len(locs)} <loc> entries in source")
        all_locs.extend(locs)

    all_locs = [u.strip() for u in all_locs]
    filtered = [u for u in all_locs if is_article_url(u)]
    print(f"Total locs before filtering: {len(all_locs)}, after filter: {len(filtered)}")
    all_locs = dedupe_preserve_order(filtered)

    OUT_PATH.write_text("\n".join(all_locs), encoding="utf-8")
    print(f"Wrote {len(all_locs)} links to {OUT_PATH}")


if __name__ == "__main__":
    main()
