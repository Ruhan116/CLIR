import re
from pathlib import Path
import requests
from urllib.parse import urlparse

LOCAL_XML = Path("d:/Win/CLIR/CLIR/all_scraped_xml.txt")
DEFAULT_SITEMAPS = [
    str(LOCAL_XML),
    "https://www.dhakapost.com/law-courts/sitemaps.xml",
    "https://www.dhakapost.com/education/sitemaps.xml",
]

OUT_PATH = Path(__file__).resolve().parent / "dhakapost_links"


def fetch_sitemap(source: str) -> str:
    if source.startswith("http://") or source.startswith("https://"):
        try:
            r = requests.get(source, timeout=20)
            r.raise_for_status()
            return r.text
        except Exception as e:
            print(f"Failed to fetch {source}: {e}")
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
    # Accept dhakapost article pages; exclude AMP variants and media hosts
    if "/amp/" in url:
        return False
    h = urlparse(url).hostname or ""
    return h.endswith("dhakapost.com")


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
