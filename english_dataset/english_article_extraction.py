#!/usr/bin/env python3
"""Collect up to 2,500 English news articles (aiming for 500 per paper).

Order: BSS -> New Age -> Dhaka Tribune -> TBS -> Daily Star. If a site yields
fewer than its quota, the shortfall rolls to the next site.

Stores rows in SQLite `english_articles.db` with columns:
- source, title, body, url (unique), date, language (required)
- tokens, word_embeddings, named_entities (left empty for now)
"""
import json
import random
import re
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable, List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "close",
}

UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
]

RATE_SECONDS = (0.6, 1.4)

DB_PATH = "english_articles.db"
TARGET_PER_SITE = 500
TOTAL_TARGET = 2500

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
    val = (raw or "").strip()
    if not val:
        return ""
    try:
        dt = datetime.fromisoformat(val.replace("Z", "+00:00"))
        return dt.date().isoformat()
    except Exception:
        pass

    m = re.search(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", val)
    if m:
        y, mo, d = map(int, m.groups())
        try:
            return datetime(y, mo, d).date().isoformat()
        except Exception:
            pass

    m = re.search(r"(\d{1,2})[-/](\d{1,2})[-/](\d{4})", val)
    if m:
        d, mo, y = map(int, m.groups())
        try:
            return datetime(y, mo, d).date().isoformat()
        except Exception:
            pass

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


def extract_date_generic(soup: BeautifulSoup, url: str) -> str:
    # Try JSON-LD first (most reliable)
    for s in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(s.string or "")
        except Exception:
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if not isinstance(item, dict):
                continue
            # Check for datePublished in main object
            for key in ("datePublished", "dateCreated", "dateModified"):
                if key in item and item[key]:
                    dt = normalize_date(str(item[key]))
                    if dt:
                        return dt
            # Check @graph for nested date info
            if "@graph" in item and isinstance(item["@graph"], list):
                for g in item["@graph"]:
                    if isinstance(g, dict):
                        for key in ("datePublished", "dateCreated", "dateModified"):
                            if key in g and g[key]:
                                dt = normalize_date(str(g[key]))
                                if dt:
                                    return dt

    # Meta tags
    meta_attrs = [
        ("property", "article:published_time"),
        ("name", "pubdate"),
        ("name", "publishdate"),
        ("itemprop", "datePublished"),
        ("property", "og:pubdate"),
        ("name", "date"),
        ("name", "dc.date"),
        ("name", "dc.date.issued"),
        ("name", "originalpublicationdate"),
    ]
    for attr, val in meta_attrs:
        el = soup.find("meta", attrs={attr: val})
        if el and el.get("content"):
            dt = normalize_date(el["content"])
            if dt:
                return dt

    # Time tag
    time_el = soup.find("time")
    if time_el:
        if time_el.get("datetime"):
            dt = normalize_date(time_el["datetime"])
            if dt:
                return dt
        txt = time_el.get_text(strip=True)
        dt = normalize_date(txt)
        if dt:
            return dt

    # Common CSS selectors (including BSS-specific .entry_update)
    for sel in ('.entry_update', '.date', '.post-date', '.published', '.entry-meta time'):
        el = soup.select_one(sel)
        if el:
            txt = el.get_text(strip=True)
            if txt:
                # For entry_update (BSS), extract only the first date (before "Update")
                if 'Update' in txt or 'update' in txt:
                    txt = txt.split('Update')[0].strip()
                    txt = txt.rstrip(':').strip()
                dt = normalize_date(txt)
                if dt:
                    return dt

    # Try extracting from URL patterns
    m = re.search(r"(\d{4})/(\d{1,2})/(\d{1,2})", url)
    if m:
        y, mo, d = map(int, m.groups())
        try:
            return datetime(y, mo, d).date().isoformat()
        except Exception:
            pass

    m = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", url)
    if m:
        y, mo, d = map(int, m.groups())
        try:
            return datetime(y, mo, d).date().isoformat()
        except Exception:
            pass

    return ""


def detect_language(soup: BeautifulSoup) -> str:
    html_lang = soup.find("html")
    if html_lang and html_lang.get("lang"):
        return html_lang["lang"].split("-")[0].lower()
    meta_lang = soup.find("meta", attrs={"http-equiv": "content-language"})
    if meta_lang and meta_lang.get("content"):
        return meta_lang["content"].split(",")[0].strip().lower()
    meta_locale = soup.find("meta", attrs={"property": "og:locale"})
    if meta_locale and meta_locale.get("content"):
        loc = meta_locale["content"].lower()
        if "en" in loc:
            return "en"
    return "en"


def extract_title_with_selectors(soup: BeautifulSoup, selectors: Iterable[str]) -> str:
    for sel in selectors:
        el = soup.select_one(sel)
        if not el:
            continue
        if sel.startswith("meta") and el.get("content"):
            val = el["content"].strip()
            if val:
                return val
        text = el.get_text(separator=" ", strip=True)
        if text:
            return text
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    return ""


def extract_body_with_selectors(
    soup: BeautifulSoup, selectors: Iterable[str], unwanted: Iterable[str] = DEFAULT_UNWANTED
) -> str:
    for sel in selectors:
        el = soup.select_one(sel)
        if not el:
            continue
        ps = [p.get_text(separator=" ", strip=True) for p in el.find_all("p")]
        ps = [t for t in ps if t]

        def keep(t: str) -> bool:
            low = t.lower()
            if any(marker.lower() in low for marker in unwanted):
                return False
            if len(t) < 40 and len(t.split()) < 6:
                return False
            return True

        if ps:
            filtered = [t for t in ps if keep(t)]
            if filtered:
                return "\n\n".join(filtered)
            return "\n\n".join(ps)

        text = el.get_text(separator="\n", strip=True)
        if text and len(text) > 80:
            return text

    for s in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(s.string or "")
        except Exception:
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if isinstance(item, dict) and item.get("@type", "").lower() in ("article", "newsarticle"):
                body = item.get("articleBody") or item.get("description")
                if body:
                    return str(body).strip()

    ps = [p.get_text(separator=" ", strip=True) for p in soup.find_all("p")]
    ps = [t for t in ps if t and len(t) > 30]
    return "\n\n".join(ps)


def fetch(url: str) -> Optional[BeautifulSoup]:
    # polite delay between calls
    time.sleep(random.uniform(*RATE_SECONDS))

    parsed = urlparse(url)
    referer = f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else None
    for attempt in range(4):
        ua = random.choice(UA_POOL)
        headers = {**HEADERS, "User-Agent": ua}
        if referer:
            headers["Referer"] = referer
        try:
            resp = Session.get(url, timeout=25, headers=headers)
            if resp.status_code == 403:
                # rotate UA and retry with small backoff
                time.sleep(1.0 + attempt * 0.5)
                continue
            resp.raise_for_status()
            return BeautifulSoup(resp.content, "html.parser")
        except Exception as e:
            if attempt == 3:
                print(f"Fetch failed: {url} ({e})", file=sys.stderr)
            time.sleep(0.5 + attempt * 0.5)
            continue
    return None


# Site-specific extractors

def parse_bss(soup: BeautifulSoup, url: str) -> Optional[dict]:
    title = extract_title_with_selectors(
        soup,
        ["h1", ".article-title", 'meta[property="og:title"]', "title"],
    )
    body = extract_body_with_selectors(
        soup,
        ["div.col-sm-9", "div.panel-body", "div#content", "article", "div.container"],
    )
    if not body:
        return None
    return {"title": title, "body": body, "date": extract_date_generic(soup, url)}


def parse_newage(soup: BeautifulSoup, url: str) -> Optional[dict]:
    title = extract_title_with_selectors(
        soup,
        ["h1.entry-title", "h1.post-title", "h1", ".post-title"],
    )
    body = extract_body_with_selectors(
        soup,
        ["div.post-content", "div.post-content .post-content", ".post-content", "article.post", "article"],
    )
    if not body:
        return None
    return {"title": title, "body": body, "date": extract_date_generic(soup, url)}


def parse_dhakatribune(soup: BeautifulSoup, url: str) -> Optional[dict]:
    title = extract_title_with_selectors(
        soup,
        [
            "h1.entry-title",
            "h1.post-title",
            "h1",
            ".content_detail .title_holder h1",
            ".entry-title",
        ],
    )
    body = extract_body_with_selectors(
        soup,
        [
            "[itemprop='articleBody'].viewport.jw_article_body",
            ".jw_detail_content_holder",
            ".content_detail .content",
            ".content_detail .jw_detail_content_holder",
            "div.content_detail",
            ".content",
            "article",
        ],
    )
    if not body:
        return None
    return {"title": title, "body": body, "date": extract_date_generic(soup, url)}


def parse_tbs(soup: BeautifulSoup, url: str) -> Optional[dict]:
    title = extract_title_with_selectors(
        soup,
        ["h1.article-title", "h1.title", "h1", ".entry-title", ".post-title", ".node-title"],
    )
    body = extract_body_with_selectors(
        soup,
        [
            ".article-body",
            ".story__content",
            ".post-content",
            ".entry-content",
            ".node__content",
            ".content",
            "article",
        ],
    )
    if not body:
        return None
    return {"title": title, "body": body, "date": extract_date_generic(soup, url)}


def parse_dailystar(soup: BeautifulSoup, url: str) -> Optional[dict]:
    title = extract_title_with_selectors(
        soup,
        [".fw-700.e-mb-16.article-title", "h1", "title"],
    )
    body = extract_body_with_selectors(
        soup,
        [".pb-20.clearfix", "article", ".story", "div.article"],
    )
    if not body:
        return None
    return {"title": title, "body": body, "date": extract_date_generic(soup, url)}


# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent

SITE_CONFIGS = [
    {
        "name": "bss",
        "link_file": str(SCRIPT_DIR / "bss_article_links"),
        "parser": parse_bss,
    },
    {
        "name": "newage",
        "link_file": str(SCRIPT_DIR / "newagebd_links"),
        "parser": parse_newage,
    },
    {
        "name": "dhakatribune",
        "link_file": str(SCRIPT_DIR / "dhakatribune_links"),
        "parser": parse_dhakatribune,
    },
    {
        "name": "tbs",
        "link_file": str(SCRIPT_DIR / "tbsnews_links"),
        "parser": parse_tbs,
    },
    {
        "name": "dailystar",
        "link_file": str(SCRIPT_DIR / "daily_star_links"),
        "parser": parse_dailystar,
    },
]


def init_db(conn: sqlite3.Connection) -> None:
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


def harvest_site(conn: sqlite3.Connection, cfg: dict, target: int) -> int:
    links = load_links(cfg["link_file"])
    if not links:
        print(f"No links for {cfg['name']}")
        return 0
    print(f"Starting {cfg['name']} with {len(links)} links; need {target}")
    random.shuffle(links)
    found = 0
    attempts = 0
    for url in links:
        if found >= target:
            break
        attempts += 1
        if "subscriber" in url:
            continue
        if attempts % 10 == 0 or attempts == 1:
            print(f"{cfg['name']}: attempt {attempts}/{len(links)}; found {found}/{target}")
        soup = fetch(url)
        if not soup:
            continue
        parsed = cfg["parser"](soup, url)
        if not parsed or not parsed.get("body"):
            continue
        language = detect_language(soup) or "en"
        raw_date = parsed.get("date") or extract_date_generic(soup, url)
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
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    print(f"Goal: {TOTAL_TARGET} total (aim {TARGET_PER_SITE} per site)")

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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
