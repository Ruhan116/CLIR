import os
import random
import time
import json
import html
import re
import argparse
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

try:
    import cloudscraper
except Exception:
    cloudscraper = None

USE_PLAYWRIGHT = False
PROXY = None
DELAY = 0.6
JITTER = 0.0


BASE_DIR = os.path.dirname(__file__)
OUT_FILE = os.path.join(BASE_DIR, "kalerkantho_stories.txt")
LINKS_FILE = os.path.join(BASE_DIR, "kalerkantho_links")
DEBUG_DIR = os.path.join(BASE_DIR, "debug_html")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

HEADERS.update({
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
})


def ensure_debug_dir():
    os.makedirs(DEBUG_DIR, exist_ok=True)


def clean_html_text(text: str) -> str:
    # Replace CRLF
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Replace common block tags with paragraph breaks
    text = re.sub(r"</?(p|div|br|li|h[1-6]|tr|td|section|article|header|footer|blockquote)[^>]*>", "\n\n", text, flags=re.IGNORECASE)

    # remove remaining tags
    text = re.sub(r"<[^>]+>", "", text)

    # unescape html entities
    text = html.unescape(text)

    # collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # strip trailing spaces on each line and trim
    lines = [ln.rstrip() for ln in text.splitlines()]
    return "\n".join(lines).strip()


def get_response(url: str, timeout: int = 12) -> Optional[requests.Response]:
    return _get_response_impl(url, timeout)


def extract_from_jsonld(soup: BeautifulSoup) -> Optional[dict]:
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            text = script.string or script.get_text()
            if not text:
                continue
            data = json.loads(text.strip())
        except Exception:
            continue

        items = data if isinstance(data, list) else [data]
        for it in items:
            if not isinstance(it, dict):
                continue
            t = it.get("@type") or it.get("type")
            if isinstance(t, list):
                t = t[0]
            if t and ("Article" in t or "NewsArticle" in t or t == "NewsArticle"):
                return it
    return None


def extract_date_from_jsonld(jsonld: dict) -> Optional[str]:
    if not isinstance(jsonld, dict):
        return None
    for key in ("datePublished", "dateCreated", "dateModified", "date"):
        v = jsonld.get(key)
        if isinstance(v, str) and v.strip():
            return v.strip()
        if isinstance(v, dict):
            for subk in ("@value", "name", "value"):
                if subk in v and isinstance(v[subk], str) and v[subk].strip():
                    return v[subk].strip()
    return None


def extract_date_from_soup(soup: BeautifulSoup, jsonld: Optional[dict] = None) -> Optional[str]:
    if jsonld:
        jd = extract_date_from_jsonld(jsonld)
        if jd:
            return jd

    meta_props = [
        ("property", "article:published_time"),
        ("property", "article:modified_time"),
        ("itemprop", "datePublished"),
        ("name", "publishdate"),
        ("name", "date"),
    ]
    for attr, val in meta_props:
        m = soup.find("meta", attrs={attr: val})
        if m and m.get("content"):
            return m.get("content").strip()

    t = soup.find("time")
    if t:
        dt = t.get("datetime")
        if dt and dt.strip():
            return dt.strip()
        txt = t.get_text(strip=True)
        if txt:
            return txt

    return None


def extract_title_from_soup(soup: BeautifulSoup) -> Optional[str]:
    h1 = soup.find("h1")
    if h1 and h1.get_text(strip=True):
        return h1.get_text(strip=True)
    og = soup.find("meta", property="og:title") or soup.find("meta", attrs={"name": "og:title"})
    if og and og.get("content"):
        return og.get("content").strip()
    if soup.title:
        return soup.title.get_text(strip=True)
    return None


def extract_body_from_jsonld_field(field: str) -> str:
    unescaped = html.unescape(field)
    soup = BeautifulSoup(unescaped, "html.parser")
    paras = [p.get_text(strip=True) for p in soup.find_all("p") if p.get_text(strip=True)]
    if paras:
        return "\n\n".join(paras)
    return soup.get_text(separator="\n\n", strip=True)


def longest_p_block(html_text: str) -> str:
    matches = list(re.finditer(r"<p[^>]*>.*?</p>", html_text, flags=re.DOTALL | re.IGNORECASE))
    if not matches:
        return ""

    groups = []
    cur_group = [matches[0]]
    for a, b in zip(matches, matches[1:]):
        gap = b.start() - a.end()
        if gap < 400:
            cur_group.append(b)
        else:
            groups.append(cur_group)
            cur_group = [b]
    groups.append(cur_group)

    best_html = ""
    best_len = 0
    for grp in groups:
        start = grp[0].start()
        end = grp[-1].end()
        fragment = html_text[start:end]
        frag_soup = BeautifulSoup(fragment, "html.parser")
        paras = [p.get_text(" ", strip=True) for p in frag_soup.find_all("p") if p.get_text(strip=True)]
        combined = "\n\n".join(paras)
        if len(combined) > best_len:
            best_len = len(combined)
            best_html = combined

    return best_html


def extract_body_from_dom(soup: BeautifulSoup, raw_html: str) -> str:
    selectors = [
        "article",
        "div[itemprop='articleBody']",
        "div[class*='article']",
        "div[class*='content']",
        "div[class*='news-details']",
        "main",
    ]

    paras: List[str] = []
    for sel in selectors:
        containers = soup.select(sel)
        if not containers:
            continue
        for container in containers:
            for p in container.find_all("p"):
                text = p.get_text(" ", strip=True)
                if text:
                    paras.append(text)
        if paras:
            return "\n\n".join(paras)

    block = longest_p_block(raw_html)
    if block and len(block) > 200:
        return block

    all_ps = [p.get_text(" ", strip=True) for p in soup.find_all("p") if p.get_text(strip=True)]
    long_ps = [p for p in all_ps if len(p) > 60]
    if long_ps:
        return "\n\n".join(long_ps)

    return "\n\n".join(all_ps)


def extract_article(url: str) -> Optional[dict]:
    resp = get_response(url)
    if not resp or resp.status_code != 200:
        return None
    resp.encoding = resp.encoding or "utf-8"
    text = resp.text
    soup = BeautifulSoup(text, "html.parser")

    jsonld = extract_from_jsonld(soup)
    title = None
    body = None
    if jsonld:
        title = jsonld.get("headline") or jsonld.get("name")
        article_body = jsonld.get("articleBody") or jsonld.get("articleBodyHtml")
        if article_body:
            try:
                body = extract_body_from_jsonld_field(article_body)
            except Exception:
                body = str(article_body)

    if not title:
        title = extract_title_from_soup(soup)

    if not body:
        body = extract_body_from_dom(soup, text)

    # clean HTML from body (handles HTML fragments and entities)
    if body:
        body = clean_html_text(body)

    if not body or len(body) < 200:
        # save debug HTML for inspection
        ensure_debug_dir()
        safe_name = re.sub(r"[^0-9a-zA-Z]+", "_", url)[:120]
        fname = os.path.join(DEBUG_DIR, f"kalerkantho_failed_{safe_name}.html")
        open(fname, "w", encoding="utf-8", errors="ignore").write(text)
        print(f"Saved debug HTML to {fname}")
        return None

    date = extract_date_from_soup(soup, jsonld)

    return {"url": url, "title": title or "", "body": body, "date": date or ""}


def get_response(url: str, timeout: int = 12) -> Optional[requests.Response]:
    return get_response.__wrapped__(url, timeout) if hasattr(get_response, "__wrapped__") else _get_response_impl(url, timeout)


def _get_response_impl(url: str, timeout: int = 12) -> Optional[requests.Response]:
    attempts = 3
    backoff = 1.0
    for attempt in range(1, attempts + 1):
        try:
            # try cloudscraper first if available
            if cloudscraper is not None:
                try:
                    scraper = cloudscraper.create_scraper()
                    r = scraper.get(url, headers=HEADERS, timeout=timeout, proxies=PROXY)
                    if r.status_code == 200:
                        return r
                    # save 403 bodies
                    if r.status_code == 403:
                        ensure_debug_dir()
                        fname = os.path.join(DEBUG_DIR, f"kalerkantho_403_{attempt}.html")
                        open(fname, "w", encoding="utf-8", errors="ignore").write(r.text)
                        print(f"Saved 403 response to {fname}")
                except Exception as e:
                    print(f"cloudscraper attempt {attempt} failed: {e}")

            # fallback to requests
            r = requests.get(url, headers=HEADERS, timeout=timeout, proxies=PROXY)
            if r.status_code == 200:
                return r
            if r.status_code == 403:
                ensure_debug_dir()
                fname = os.path.join(DEBUG_DIR, f"kalerkantho_403_{attempt}.html")
                open(fname, "w", encoding="utf-8", errors="ignore").write(r.text)
                print(f"Saved 403 response to {fname}")

            # if not successful and playwright requested, try Playwright
            if USE_PLAYWRIGHT:
                try:
                    content = fetch_with_playwright(url, timeout=timeout)
                    if content:
                        # craft a fake Response-like object with .text
                        class FakeResp:
                            def __init__(self, text):
                                self.status_code = 200
                                self.text = text
                                self.encoding = "utf-8"

                        return FakeResp(content)
                except Exception as e:
                    print(f"Playwright fetch attempt failed: {e}")

        except Exception as e:
            print(f"Attempt {attempt} error: {e}")

        time.sleep(backoff)
        backoff *= 2

    return None


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
            if PROXY:
                # Playwright proxy support would require launching browser with proxy settings; skip for now
                pass
            page.goto(url, wait_until="networkidle", timeout=timeout * 1000)
            content = page.content()
            browser.close()
            return content
    except Exception as e:
        print(f"Playwright fetch failed for {url}: {e}")
        return ""


def main(n: int = 10):
    if not os.path.exists(LINKS_FILE):
        print(f"Links file not found: {LINKS_FILE}")
        return

    with open(LINKS_FILE, "r", encoding="utf-8") as f:
        links = [line.strip() for line in f if line.strip()]

    random.shuffle(links)
    results: List[dict] = []

    for url in links:
        if len(results) >= n:
            break
        art = extract_article(url)
        if art:
            results.append(art)
            print(f"Collected ({len(results)}/{n}): {url}")
        else:
            print(f"Skipped: {url}")
        # respect configured delay and jitter
        if DELAY and DELAY > 0:
            if JITTER and JITTER > 0:
                sleep_time = max(0.1, random.uniform(DELAY - JITTER, DELAY + JITTER))
            else:
                sleep_time = DELAY
            time.sleep(sleep_time)

    if not results:
        print("No articles extracted.")
        return

    with open(OUT_FILE, "w", encoding="utf-8") as out:
        for i, art in enumerate(results, 1):
            out.write(f"=== Article {i} ===\n")
            out.write(f"URL: {art['url']}\n")
            out.write(f"Title: {art['title']}\n")
            out.write(f"Date: {art.get('date','')}\n\n")
            out.write(art["body"])
            out.write("\n\n")

    print(f"Saved {len(results)} stories to {OUT_FILE}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Fetch 10 random Kaler Kantho articles from links file")
    p.add_argument("--n", type=int, default=10, help="number of articles to fetch")
    p.add_argument("--delay", type=float, default=0.6, help="seconds to wait between article fetches")
    p.add_argument("--jitter", type=float, default=0.0, help="jitter to randomize delay")
    p.add_argument("--use-playwright", action="store_true", help="use Playwright fallback for blocked pages")
    p.add_argument("--proxy", type=str, default=None, help="proxy URL to use for requests (e.g. http://127.0.0.1:8888)")
    args = p.parse_args()
    USE_PLAYWRIGHT = args.use_playwright
    PROXY = {"http": args.proxy, "https": args.proxy} if args.proxy else None
    DELAY = args.delay
    JITTER = args.jitter
    main(args.n)
