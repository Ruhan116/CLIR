#!/usr/bin/env python3
"""Collect up to 2,500 Bangla news articles (aiming for 500 per paper).

Order: Kalerkantho -> Jugantor -> Banglanews24 -> Prothomalo -> DhakaPost
If a site yields fewer than its quota, the shortfall rolls to the next site.

Special handling for Kalerkantho: uses Playwright, skips after 20 consecutive failures.

Stores rows in SQLite `bangla_articles.db` with columns:
- source, title, body, url (unique), date, language (required)
- tokens, word_embeddings, named_entities (left empty for now)
"""
import html
import json
import random
import re
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable, List, Optional

import requests
from bs4 import BeautifulSoup

# Try to import optional dependencies
try:
    import cloudscraper
except ImportError:
    cloudscraper = None

try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,bn-BD,bn;q=0.8",
    "Connection": "close",
}

UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
]

RATE_SECONDS = (0.6, 1.4)

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent

DB_PATH = str(SCRIPT_DIR / "bangla_articles.db")
TARGET_PER_SITE = 500
TOTAL_TARGET = 2500
KALERKANTHO_MAX_CONSECUTIVE_FAILURES = 20

DEFAULT_UNWANTED = (
    "Related",
    "Related News",
    "Most Viewed",
    "Comments",
    "Related Posts",
    "Advertisement",
    "Sponsored",
)

Session = requests.Session()
Session.headers.update(HEADERS)


def load_links(path: str) -> List[str]:
    p = Path(path)
    if not p.exists():
        print(f"Link file missing: {path}", file=sys.stderr)
        return []
    with p.open("r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def normalize_date(raw: str) -> str:
    """Convert various date formats to ISO format (YYYY-MM-DD)."""
    val = (raw or "").strip()
    if not val:
        return ""
    try:
        dt = datetime.fromisoformat(val.replace("Z", "+00:00"))
        return dt.date().isoformat()
    except Exception:
        pass

    # Try YYYY-MM-DD or YYYY/MM/DD
    m = re.search(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", val)
    if m:
        y, mo, d = map(int, m.groups())
        try:
            return datetime(y, mo, d).date().isoformat()
        except Exception:
            pass

    # Try DD-MM-YYYY or DD/MM/YYYY
    m = re.search(r"(\d{1,2})[-/](\d{1,2})[-/](\d{4})", val)
    if m:
        d, mo, y = map(int, m.groups())
        try:
            return datetime(y, mo, d).date().isoformat()
        except Exception:
            pass

    # Try "DD MonthName YYYY"
    m = re.search(r"(\d{1,2})\s+([A-Za-z]{3,})\s+(\d{4})", val)
    if m:
        d = int(m.group(1))
        month_name = m.group(2)
        y = int(m.group(3))
        try:
            mo = datetime.strptime(month_name[:3], "%b").month
            return datetime(y, mo, d).date().isoformat()
        except Exception:
            pass

    return ""


def detect_language(soup: BeautifulSoup) -> str:
    """Detect language from HTML meta tags."""
    html_lang = soup.find("html")
    if html_lang and html_lang.get("lang"):
        lang = html_lang["lang"].split("-")[0].lower()
        if "bn" in lang or "bangla" in lang:
            return "bn"
    meta_lang = soup.find("meta", attrs={"http-equiv": "content-language"})
    if meta_lang and meta_lang.get("content"):
        lang = meta_lang["content"].split(",")[0].strip().lower()
        if "bn" in lang or "bangla" in lang:
            return "bn"
    meta_locale = soup.find("meta", attrs={"property": "og:locale"})
    if meta_locale and meta_locale.get("content"):
        loc = meta_locale["content"].lower()
        if "bn" in loc or "bangla" in loc:
            return "bn"
    return "bn"  # Default to Bangla


def fetch(url: str) -> Optional[BeautifulSoup]:
    """Fetch a URL and return BeautifulSoup object."""
    time.sleep(random.uniform(*RATE_SECONDS))

    for attempt in range(3):
        ua = random.choice(UA_POOL)
        headers = {**HEADERS, "User-Agent": ua}
        try:
            resp = Session.get(url, timeout=20, headers=headers)
            if resp.status_code == 403:
                time.sleep(1.0 + attempt * 0.5)
                continue
            resp.raise_for_status()
            resp.encoding = resp.encoding or "utf-8"
            return BeautifulSoup(resp.content, "html.parser")
        except Exception as e:
            if attempt == 2:
                print(f"Fetch failed: {url} ({e})", file=sys.stderr)
            time.sleep(0.5 + attempt * 0.5)
            continue
    return None


def fetch_with_cloudscraper(url: str) -> Optional[BeautifulSoup]:
    """Fetch using cloudscraper to bypass anti-bot measures."""
    if not cloudscraper:
        return None

    time.sleep(random.uniform(*RATE_SECONDS))

    try:
        scraper = cloudscraper.create_scraper()
        resp = scraper.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        resp.encoding = resp.encoding or "utf-8"
        return BeautifulSoup(resp.content, "html.parser")
    except Exception as e:
        print(f"Cloudscraper fetch failed: {url} ({e})", file=sys.stderr)
        return None


def fetch_with_playwright(url: str) -> Optional[str]:
    """Fetch using Playwright for JavaScript-rendered pages."""
    if not HAS_PLAYWRIGHT:
        return None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=HEADERS["User-Agent"],
                locale="bn-BD",
                extra_http_headers={"Accept-Language": "bn-BD,bn;q=0.9,en-US;q=0.8,en;q=0.7"},
            )
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=45000)

            # Wait for content to load
            try:
                page.wait_for_selector("article, div[class*='article'], div[class*='content']", timeout=10000)
            except Exception:
                page.wait_for_timeout(2000)

            html_content = page.content()
            context.close()
            browser.close()
            return html_content
    except Exception as e:
        print(f"Playwright fetch failed: {url} ({e})", file=sys.stderr)
        return None


# ============================================================================
# Common extraction helpers
# ============================================================================

def extract_from_jsonld(soup: BeautifulSoup) -> Optional[dict]:
    """Extract JSON-LD data from page."""
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
            if t and ("Article" in t or "NewsArticle" in t):
                return it
    return None


def extract_date_from_jsonld(jsonld: dict) -> Optional[str]:
    """Extract date from JSON-LD data."""
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


def extract_date_generic(soup: BeautifulSoup, jsonld: Optional[dict] = None) -> str:
    """Generic date extraction from soup."""
    # Try JSON-LD first
    if jsonld:
        jd = extract_date_from_jsonld(jsonld)
        if jd:
            dt = normalize_date(jd)
            if dt:
                return dt

    # Meta tags
    meta_attrs = [
        ("property", "article:published_time"),
        ("property", "article:modified_time"),
        ("itemprop", "datePublished"),
        ("name", "publishdate"),
        ("name", "date"),
    ]
    for attr, val in meta_attrs:
        el = soup.find("meta", attrs={attr: val})
        if el and el.get("content"):
            dt = normalize_date(el["content"])
            if dt:
                return dt

    # Time tag
    t = soup.find("time")
    if t:
        if t.get("datetime"):
            dt = normalize_date(t["datetime"])
            if dt:
                return dt
        txt = t.get_text(strip=True)
        if txt:
            dt = normalize_date(txt)
            if dt:
                return dt

    # CSS selectors with date/time in class
    el = soup.find(attrs={"class": re.compile(r"date|time|published", re.I)})
    if el:
        txt = el.get_text(strip=True)
        if txt:
            dt = normalize_date(txt)
            if dt:
                return dt

    return ""


def extract_title_generic(soup: BeautifulSoup) -> str:
    """Generic title extraction."""
    h1 = soup.find("h1")
    if h1 and h1.get_text(strip=True):
        return h1.get_text(strip=True)

    og = soup.find("meta", property="og:title") or soup.find("meta", attrs={"name": "og:title"})
    if og and og.get("content"):
        return og.get("content").strip()

    if soup.title:
        return soup.title.get_text(strip=True)

    return ""


def extract_body_from_jsonld_field(field: str) -> str:
    """Extract body text from JSON-LD articleBody field."""
    unescaped = html.unescape(field)
    soup = BeautifulSoup(unescaped, "html.parser")
    paras = [p.get_text(strip=True) for p in soup.find_all("p") if p.get_text(strip=True)]
    if paras:
        return "\n\n".join(paras)
    return soup.get_text(separator="\n\n", strip=True)


def longest_p_block(html_text: str) -> str:
    """Find the longest block of consecutive <p> tags in raw HTML."""
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


def extract_body_generic(soup: BeautifulSoup, raw_html: str, selectors: List[str]) -> str:
    """Generic body extraction using provided selectors."""
    paras: List[str] = []
    for sel in selectors:
        containers = soup.select(sel)
        if not containers:
            continue
        for container in containers:
            for p in container.find_all("p"):
                text = p.get_text(" ", strip=True)
                if text and len(text) > 30:
                    paras.append(text)
        if paras:
            return "\n\n".join(paras)

    # Fallback to longest block
    block = longest_p_block(raw_html)
    if block and len(block) > 200:
        return block

    # Final fallback: all <p> tags
    all_ps = [p.get_text(" ", strip=True) for p in soup.find_all("p") if p.get_text(strip=True)]
    long_ps = [p for p in all_ps if len(p) > 60]
    if long_ps:
        return "\n\n".join(long_ps)

    return "\n\n".join(all_ps)


# ============================================================================
# Site-specific parsers
# ============================================================================

def parse_kalerkantho(soup: BeautifulSoup, url: str, raw_html: str) -> Optional[dict]:
    """Parse Kaler Kantho articles."""
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
        title = extract_title_generic(soup)

    if not body:
        selectors = [
            "article",
            "div[itemprop='articleBody']",
            "div[class*='article']",
            "div[class*='content']",
            "div[class*='news-details']",
            "main",
        ]
        body = extract_body_generic(soup, raw_html, selectors)

        # Clean HTML artifacts
        if body:
            body = re.sub(r"</?(p|div|br|li|h[1-6])[^>]*>", "\n\n", body, flags=re.IGNORECASE)
            body = re.sub(r"<[^>]+>", "", body)
            body = html.unescape(body)
            body = re.sub(r"\n{3,}", "\n\n", body)
            body = "\n".join(line.rstrip() for line in body.splitlines()).strip()

    if not body or len(body) < 200:
        return None

    date = extract_date_generic(soup, jsonld)
    return {"title": title or "", "body": body, "date": date}


def parse_jugantor(soup: BeautifulSoup, url: str, raw_html: str) -> Optional[dict]:
    """Parse Jugantor articles."""
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
        title = extract_title_generic(soup)

    if not body:
        selectors = [
            "div.mainDiv",
            "article",
            "div#content",
            "div.content",
            "div[class*='article']",
            "div[class*='details']",
            "div[class*='detail']",
            "main",
        ]
        body = extract_body_generic(soup, raw_html, selectors)

    if not body or len(body) < 200:
        return None

    date = extract_date_generic(soup, jsonld)
    return {"title": title or "", "body": body, "date": date}


def parse_banglanews24(soup: BeautifulSoup, url: str, raw_html: str) -> Optional[dict]:
    """Parse Banglanews24 articles."""
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
        title = extract_title_generic(soup)

    if not body:
        # Banglanews24-specific selectors
        special_containers = soup.find_all("div", class_=re.compile(r"details-module.*articleArea|articleArea", re.I))
        if special_containers:
            paras: List[str] = []
            for container in special_containers:
                articles = container.find_all("article")
                for art in articles:
                    for p in art.find_all("p"):
                        txt = p.get_text(" ", strip=True)
                        if txt:
                            paras.append(txt)
            if paras:
                body = "\n\n".join(paras)

        if not body:
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
            body = extract_body_generic(soup, raw_html, selectors)

    if not body or len(body) < 200:
        return None

    date = extract_date_generic(soup, jsonld)
    return {"title": title or "", "body": body, "date": date}


def parse_prothomalo(soup: BeautifulSoup, url: str, raw_html: str) -> Optional[dict]:
    """Parse Prothom Alo articles."""
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
        title = extract_title_generic(soup)

    if not body:
        selectors = [
            "div.story-content",
            "div.story-element.story-element-text",
            "article",
            "div#container",
            "div[itemprop='articleBody']",
            "div.content",
            "div.story-body",
        ]
        body = extract_body_generic(soup, raw_html, selectors)

    if not body or len(body) < 200:
        return None

    date = extract_date_generic(soup, jsonld)
    return {"title": title or "", "body": body, "date": date}


def parse_dhakapost(soup: BeautifulSoup, url: str, raw_html: str) -> Optional[dict]:
    """Parse Dhaka Post articles."""
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
        title = extract_title_generic(soup)

    if not body:
        selectors = [
            "article",
            "div[itemprop='articleBody']",
            "div[class*='article']",
            "div[class*='content']",
            "div[class*='story']",
            "main",
        ]
        body = extract_body_generic(soup, raw_html, selectors)

    if not body or len(body) < 200:
        return None

    date = extract_date_generic(soup, jsonld)
    return {"title": title or "", "body": body, "date": date}


# ============================================================================
# Site configurations
# ============================================================================

SITE_CONFIGS = [
    {
        "name": "kalerkantho",
        "link_file": str(SCRIPT_DIR / "kalerkantho_links"),
        "parser": parse_kalerkantho,
        "use_cloudscraper": True,
        "use_playwright": True,
    },
    {
        "name": "jugantor",
        "link_file": str(SCRIPT_DIR / "jugantor_links"),
        "parser": parse_jugantor,
        "use_cloudscraper": False,
        "use_playwright": False,
    },
    {
        "name": "banglanews24",
        "link_file": str(SCRIPT_DIR / "banglanews24_links"),
        "parser": parse_banglanews24,
        "use_cloudscraper": False,
        "use_playwright": True,
    },
    {
        "name": "prothomalo",
        "link_file": str(SCRIPT_DIR / "prothomalo_links"),
        "parser": parse_prothomalo,
        "use_cloudscraper": False,
        "use_playwright": False,
    },
    {
        "name": "dhakapost",
        "link_file": str(SCRIPT_DIR / "dhakapost_links"),
        "parser": parse_dhakapost,
        "use_cloudscraper": False,
        "use_playwright": False,
    },
]


# ============================================================================
# Database operations
# ============================================================================

def init_db(conn: sqlite3.Connection) -> None:
    """Initialize the database schema."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            title TEXT,
            body TEXT,
            url TEXT UNIQUE,
            date TEXT,
            language TEXT,
            tokens INTEGER,
            word_embeddings TEXT,
            named_entities TEXT
        );
        """
    )
    conn.commit()


def insert_article(conn: sqlite3.Connection, row: dict) -> bool:
    """Insert an article into the database."""
    try:
        conn.execute(
            """
            INSERT INTO articles (source, title, body, url, date, language, tokens, word_embeddings, named_entities)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row.get("source"),
                row.get("title"),
                row.get("body"),
                row.get("url"),
                row.get("date"),
                row.get("language"),
                None,
                None,
                None,
            ),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    except Exception as e:
        print(f"DB insert failed for {row.get('url')}: {e}", file=sys.stderr)
        return False


# ============================================================================
# Harvesting logic
# ============================================================================

def harvest_site(conn: sqlite3.Connection, cfg: dict, target: int) -> int:
    """Harvest articles from a specific site."""
    links = load_links(cfg["link_file"])
    if not links:
        print(f"No links for {cfg['name']}")
        return 0

    print(f"Starting {cfg['name']} with {len(links)} links; need {target}")
    random.shuffle(links)
    found = 0
    attempts = 0
    consecutive_failures = 0

    for url in links:
        if found >= target:
            break

        # Special handling for Kalerkantho: skip after 20 consecutive failures
        if cfg["name"] == "kalerkantho" and consecutive_failures >= KALERKANTHO_MAX_CONSECUTIVE_FAILURES:
            print(f"Kalerkantho: Skipping after {consecutive_failures} consecutive failures")
            break

        attempts += 1
        if attempts % 10 == 0 or attempts == 1:
            print(f"{cfg['name']}: attempt {attempts}/{len(links)}; found {found}/{target}")

        # Try different fetch methods based on config
        soup = None
        raw_html = ""

        if cfg.get("use_cloudscraper") and cloudscraper:
            soup = fetch_with_cloudscraper(url)
            if soup:
                raw_html = str(soup)

        if not soup and cfg.get("use_playwright") and HAS_PLAYWRIGHT:
            html_content = fetch_with_playwright(url)
            if html_content:
                soup = BeautifulSoup(html_content, "html.parser")
                raw_html = html_content

        if not soup:
            soup = fetch(url)
            if soup:
                raw_html = str(soup)

        if not soup:
            consecutive_failures += 1
            continue

        # Parse the article
        parsed = cfg["parser"](soup, url, raw_html)
        if not parsed or not parsed.get("body"):
            consecutive_failures += 1
            continue

        # Reset consecutive failures on success
        consecutive_failures = 0

        language = detect_language(soup) or "bn"
        raw_date = parsed.get("date") or extract_date_generic(soup)
        norm_date = normalize_date(raw_date) if raw_date else ""

        row = {
            "source": cfg["name"],
            "title": parsed.get("title", ""),
            "body": parsed.get("body", ""),
            "url": url,
            "date": norm_date,
            "language": language,
        }

        if insert_article(conn, row):
            found += 1

        if attempts % 50 == 0:
            print(f"{cfg['name']}: {found}/{target} after {attempts} attempts")

    print(f"{cfg['name']}: collected {found} (target {target}, attempts {attempts})")
    return found


def main() -> int:
    """Main execution function."""
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    print(f"Goal: {TOTAL_TARGET} total (aim {TARGET_PER_SITE} per site)")
    print(f"Database: {DB_PATH}")

    carry = 0
    total_inserted = 0

    for cfg in SITE_CONFIGS:
        desired = TARGET_PER_SITE + carry
        collected = harvest_site(conn, cfg, desired)
        total_inserted += collected
        carry = max(0, desired - collected)
        print(f"After {cfg['name']}: total {total_inserted}, carry {carry}")

    print(f"Final total inserted: {total_inserted}")
    if total_inserted < TOTAL_TARGET:
        print(f"Short of target by {TOTAL_TARGET - total_inserted}", file=sys.stderr)

    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
