import os
import random
import time
import json
import html
import re
from typing import List, Optional

import requests
from bs4 import BeautifulSoup


BASE_DIR = os.path.dirname(__file__)
OUT_FILE = os.path.join(BASE_DIR, "banglanews24_stories.txt")
LINKS_FILE = os.path.join(BASE_DIR, "banglanews24_links")


def _looks_like_js_rendered_shell(soup: BeautifulSoup) -> bool:
    """Return True when the response is a Next.js/React shell with the body loaded client-side."""
    try:
        # Common signals in the saved debug HTML: loader + "Loading..." placeholders,
        # and no <p> tags at all.
        has_loader = bool(soup.select_one(".loader"))
        has_loading_text = "Loading..." in soup.get_text(" ", strip=True)
        has_any_p = bool(soup.find("p"))
        return (has_loader or has_loading_text) and not has_any_p
    except Exception:
        return False


def _extract_with_playwright(url: str, timeout_ms: int = 45000) -> Optional[dict]:
    """Best-effort JS-rendered extraction using Playwright (if installed).

    This is needed for pages where Banglanews24 serves a client-rendered shell (no <p> in HTML).
    """
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return None

    ua = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=ua,
            locale="bn-BD",
            extra_http_headers={"Accept-Language": "bn-BD,bn;q=0.9,en-US;q=0.8,en;q=0.7"},
        )
        page = context.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            # Give the SPA a moment to fetch and render.
            try:
                page.wait_for_selector("div[class*='articleArea']", timeout=15000)
            except Exception:
                # Sometimes the container exists but is delayed; still try extraction.
                page.wait_for_timeout(1000)

            title = (page.locator("h1").first.inner_text(timeout=3000) or "").strip()

            # Prefer the exact container pattern you provided.
            loc = page.locator("div[class*='articleArea'] article p")
            paras = [t.strip() for t in loc.all_inner_texts() if t and t.strip()]
            if not paras:
                loc = page.locator("div[class*='articleArea'] p")
                paras = [t.strip() for t in loc.all_inner_texts() if t and t.strip()]

            body = "\n\n".join(paras)
            html_text = page.content()
        finally:
            context.close()
            browser.close()

    if not body or len(body) < 100:
        return None

    # Reuse the same metadata extractors on the rendered HTML
    soup = BeautifulSoup(html_text, "html.parser")
    jsonld = extract_from_jsonld(soup)
    date = extract_date_from_soup(soup, jsonld)
    if not title:
        title = extract_title_from_soup(soup) or ""

    return {"url": url, "title": title, "body": body, "date": date or ""}


def get_response(url: str, timeout: int = 15):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
    }

    session = requests.Session()
    retries = requests.adapters.Retry(total=3, backoff_factor=1, status_forcelist=(429, 502, 503, 504))
    session.mount("https://", requests.adapters.HTTPAdapter(max_retries=retries))
    session.mount("http://", requests.adapters.HTTPAdapter(max_retries=retries))

    try:
        resp = session.get(url, headers=headers, timeout=timeout, allow_redirects=True)
    except requests.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return None

    if resp.status_code == 403:
        try:
            import cloudscraper
            scraper = cloudscraper.create_scraper()
            resp = scraper.get(url, headers=headers, timeout=timeout)
        except Exception:
            print(f"Received 403 for {url}")

    try:
        resp.raise_for_status()
    except requests.HTTPError as e:
        print(f"Error fetching the URL: {e}")
        return None

    return resp


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}


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

    meta = soup.find("meta", attrs={"property": "article:published_time"}) or soup.find("meta", attrs={"name": "article:published_time"})
    if meta and meta.get("content"):
        return meta.get("content").strip()

    t = soup.find("time")
    if t:
        dt = t.get("datetime")
        if dt and dt.strip():
            return dt.strip()
        txt = t.get_text(strip=True)
        if txt:
            return txt

    s = soup.find(attrs={"class": re.compile(r"date|time|published", re.I)})
    if s and s.get_text(strip=True):
        return s.get_text(strip=True)

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
    # First try site-specific container pattern used by Banglanews24
    try:
        special_containers = soup.find_all("div", class_=re.compile(r"details-module.*articleArea|articleArea", re.I))
    except Exception:
        special_containers = []

    if special_containers:
        paras: List[str] = []
        for container in special_containers:
            # collect from all <article> children inside the container
            articles = container.find_all("article")
            for art in articles:
                for p in art.find_all("p"):
                    txt = p.get_text(" ", strip=True)
                    if txt:
                        paras.append(txt)
        if paras:
            return "\n\n".join(paras)

    selectors = [
        "div.mainDiv",
        "article",
        "div#content",
        "div.content",
        "div[class*='article']",
        "div[class*='details']",
        "div[class*='detail']",
        "div[itemprop='articleBody']",
        "div.story",
        "main",
    ]

    paras: List[str] = []
    for sel in selectors:
        containers = soup.select(sel)
        if not containers:
            continue
        for container in containers:
            # prefer <article> child if present
            article_child = container.find("article")
            search_root = article_child if article_child is not None else container
            for p in search_root.find_all("p"):
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
    if not resp:
        return None
    if resp.status_code != 200:
        # give diagnostic for non-200
        print(f"Fetch status {resp.status_code} for {url}")
        return None
    resp.encoding = resp.encoding or "utf-8"
    text = resp.text
    soup = BeautifulSoup(text, "html.parser")

    # If the server sent only the shell (client-side rendered body), BeautifulSoup can't see the body.
    # We'll still try JSON-LD + DOM fallbacks, but later we can optionally use Playwright.

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

    if not body or len(body) < 200:
        # try more aggressive fallbacks before giving up
        # 1) longest_p_block already applied inside extract_body_from_dom
        # 2) regex-based extraction of any <p> tags in raw HTML
        p_matches = re.findall(r"<p[^>]*>(.*?)</p>", text, flags=re.DOTALL | re.IGNORECASE)
        cleaned_paras = []
        for pm in p_matches:
            # strip HTML tags from each match
            frag = BeautifulSoup(pm, "html.parser").get_text(" ", strip=True)
            if frag:
                cleaned_paras.append(frag)
        if cleaned_paras:
            body = "\n\n".join(cleaned_paras)

    if not body or len(body) < 100:
        if _looks_like_js_rendered_shell(soup):
            pw = _extract_with_playwright(url)
            if pw:
                return pw
            print(
                "Skipped (no body): server returned a JS-rendered shell (no <p> in HTML). "
                "Install Playwright to scrape these pages: pip install playwright ; python -m playwright install chromium"
            )
        # save raw HTML for debugging so you can inspect structure
        dbg_dir = os.path.join(BASE_DIR, "debug_html")
        os.makedirs(dbg_dir, exist_ok=True)
        safe_name = re.sub(r"[^0-9a-zA-Z_-]", "_", url)
        dbg_path = os.path.join(dbg_dir, safe_name[:200] + ".html")
        try:
            with open(dbg_path, "w", encoding="utf-8") as fw:
                fw.write(text)
        except Exception:
            pass
        print(f"Skipped (no body) and saved debug HTML to {dbg_path}: {url}")
        return None

    date = extract_date_from_soup(soup, jsonld)

    return {"url": url, "title": title or "", "body": body, "date": date or ""}


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
        time.sleep(0.6)

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
    main(10)
