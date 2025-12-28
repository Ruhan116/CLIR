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
OUT_FILE = os.path.join(BASE_DIR, "jugantor_stories.txt")
LINKS_FILE = os.path.join(BASE_DIR, "jugantor_links")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}


def fetch(url: str, timeout: int = 12) -> Optional[requests.Response]:
    try:
        return requests.get(url, headers=HEADERS, timeout=timeout)
    except Exception:
        return None


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

    # some sites put date in a span with class containing 'date' or 'time'
    s = soup.find(attrs={"class": re.compile(r"date|time", re.I)})
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
    resp = fetch(url)
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

    if not body or len(body) < 200:
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
