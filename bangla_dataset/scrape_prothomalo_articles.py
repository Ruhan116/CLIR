import os
import random
import time
import json
import html
from typing import List, Optional

import requests
from bs4 import BeautifulSoup


OUT_FILE = os.path.join(os.path.dirname(__file__), "prothomalo_stories.txt")
LINKS_FILE = os.path.join(os.path.dirname(__file__), "prothomalo_links")

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

        # JSON-LD can be a list or a dict
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
    # Try common places
    title = None
    h1 = soup.find("h1")
    if h1 and h1.get_text(strip=True):
        title = h1.get_text(strip=True)

    if not title:
        og = soup.find("meta", property="og:title") or soup.find("meta", attrs={"name": "og:title"})
        if og and og.get("content"):
            title = og.get("content").strip()

    if not title:
        t = soup.title
        if t:
            title = t.get_text(strip=True)

    return title


def extract_body_from_jsonld_field(field: str) -> str:
    # field may contain HTML-escaped paragraphs
    unescaped = html.unescape(field)
    soup = BeautifulSoup(unescaped, "html.parser")
    paras = [p.get_text(strip=True) for p in soup.find_all("p") if p.get_text(strip=True)]
    if paras:
        return "\n\n".join(paras)
    return soup.get_text(separator="\n\n", strip=True)


def extract_body_from_dom(soup: BeautifulSoup) -> str:
    selectors = [
        "div.story-content",
        "div.story-element.story-element-text",
        "article",
        "div#container",
        "div[itemprop='articleBody']",
        "div.content",
        "div.story-body",
    ]

    paras: List[str] = []
    for sel in selectors:
        containers = soup.select(sel)
        if not containers:
            continue
        for container in containers:
            for p in container.find_all("p"):
                text = p.get_text(" ", strip=True)
                if len(text) >= 30:
                    paras.append(text)
        if paras:
            break

    # Fallback to collecting all <p> tags in page
    if not paras:
        for p in soup.find_all("p"):
            text = p.get_text(" ", strip=True)
            if len(text) >= 60:
                paras.append(text)

    # Final fallback: use any text
    if not paras:
        body = soup.get_text(separator="\n\n", strip=True)
        return body

    return "\n\n".join(paras)


def extract_article(url: str) -> Optional[dict]:
    resp = fetch(url)
    if not resp or resp.status_code != 200:
        return None
    resp.encoding = resp.encoding or "utf-8"
    soup = BeautifulSoup(resp.text, "html.parser")

    # Try JSON-LD first
    jsonld = extract_from_jsonld(soup)
    title = None
    body = None
    if jsonld:
        # headline can be in 'headline' or 'name'
        title = jsonld.get("headline") or jsonld.get("name")
        article_body = jsonld.get("articleBody") or jsonld.get("articleBodyHtml")
        if article_body:
            try:
                body = extract_body_from_jsonld_field(article_body)
            except Exception:
                body = str(article_body)

    # Fallbacks
    if not title:
        title = extract_title_from_soup(soup)

    if not body:
        body = extract_body_from_dom(soup)

    if not body or len(body) < 200:
        return None

    # extract publish date
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
        time.sleep(0.5)

    if not results:
        print("No articles extracted.")
        return

    # Write output
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
