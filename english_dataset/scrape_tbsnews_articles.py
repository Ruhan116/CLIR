#!/usr/bin/env python3
"""Fetch 10 random valid TBS articles from tbsnews_links and save to tbs_stories.txt.

This script is resilient to varying page structures by trying multiple
selectors for title and body and considers a page valid when a body
selector returns text.
"""
import random
import sys
from typing import List

import requests
from bs4 import BeautifulSoup
import json

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# Candidate selectors to locate title and body; first matching selector is used
TITLE_SELECTORS = [
    'h1.article-title',
    'h1.title',
    'h1',
    '.entry-title',
    '.post-title',
    '.node-title',
]

BODY_SELECTORS = [
    '.article-body',
    '.story__content',
    '.post-content',
    '.entry-content',
    '.node__content',
    '.content',
    'article',
]


def load_links(path: str) -> List[str]:
    with open(path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]


def find_text(soup: BeautifulSoup, selectors: List[str]) -> str:
    # Prefer structured containers and paragraph-level text to avoid nav/related noise
    unwanted_markers = ('Top Stories', 'Related News', 'Related', 'Most Viewed', 'Comments', 'Related Posts')

    for sel in selectors:
        el = soup.select_one(sel)
        if not el:
            continue

        # ignore containers that look like sidebars or related blocks by class or text
        cls = ' '.join(el.get('class') or [])
        if any(k in cls.lower() for k in ('related', 'sidebar', 'most-viewed', 'top-stories', 'panel')):
            continue

        # collect paragraph texts under the container (most reliable)
        ps = [p.get_text(strip=True) for p in el.find_all('p')]
        ps = [t for t in ps if t]
        if ps:
            # filter out blocks that are clearly navigation lists
            joined = '\n\n'.join(ps)
            if any(m in joined for m in unwanted_markers):
                # try to return only the first paragraph if the block contains markers
                return ps[0]
            return joined

        # fallback to element text but try to avoid large nav-like blocks
        text = el.get_text(separator='\n', strip=True)
        if not text:
            continue
        if any(m in text for m in unwanted_markers):
            # return first non-empty paragraph if possible
            first_p = el.find('p')
            if first_p and first_p.get_text(strip=True):
                return first_p.get_text(strip=True)
            continue
        return text

    # If no selector matched, try to parse JSON-LD for articleBody
    for s in soup.find_all('script', type='application/ld+json'):
        try:
            import json

            data = json.loads(s.string or '')
            # data may be a list or dict
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get('@type', '').lower() in ('article', 'newsarticle'):
                        body = item.get('articleBody') or item.get('description')
                        if body:
                            return body.strip()
            elif isinstance(data, dict):
                if data.get('@type', '').lower() in ('article', 'newsarticle'):
                    body = data.get('articleBody') or data.get('description')
                    if body:
                        return body.strip()
        except Exception:
            continue

    return ''


def extract_date(soup: BeautifulSoup) -> str:
    # JSON-LD
    for s in soup.find_all('script', type='application/ld+json'):
        try:
            data = json.loads(s.string or '')
            items = data if isinstance(data, list) else [data]
            for item in items:
                if not isinstance(item, dict):
                    continue
                for key in ('datePublished', 'dateCreated', 'dateModified'):
                    if key in item and item[key]:
                        return str(item[key]).strip()
                if '@graph' in item and isinstance(item['@graph'], list):
                    for g in item['@graph']:
                        for key in ('datePublished', 'dateCreated', 'dateModified'):
                            if key in g and g[key]:
                                return str(g[key]).strip()
        except Exception:
            continue

    for attr, val in (('property', 'article:published_time'), ('itemprop', 'datePublished'), ('name', 'pubdate')):
        m = soup.find('meta', attrs={attr: val})
        if m and m.get('content'):
            return m.get('content').strip()

    t = soup.find('time')
    if t:
        if t.get('datetime'):
            return t.get('datetime').strip()
        txt = t.get_text(strip=True)
        if txt:
            return txt

    for sel in ('.date', '.post-date', '.published', '.entry-meta time'):
        el = soup.select_one(sel)
        if el:
            txt = el.get_text(strip=True)
            if txt:
                return txt

    return ''


def fetch_article(url: str) -> dict | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception:
        return None
    soup = BeautifulSoup(resp.content, 'html.parser')
    body = find_text(soup, BODY_SELECTORS)
    if not body:
        return None
    title = find_text(soup, TITLE_SELECTORS)
    date = extract_date(soup)
    return {'url': url, 'title': title, 'body': body, 'date': date}


def main() -> int:
    links_path = 'tbsnews_links'
    try:
        links = load_links(links_path)
    except Exception as e:
        print('Error loading links:', e, file=sys.stderr)
        return 1

    if not links:
        print('No links found in', links_path, file=sys.stderr)
        return 1

    print(f"Loaded {len(links)} links from {links_path}", flush=True)
    indices = list(range(len(links)))
    random.shuffle(indices)
    print('Searching for up to 10 valid TBS articles (random order)...', flush=True)

    found = []
    attempts = 0
    for idx in indices:
        if len(found) >= 10:
            break
        attempts += 1
        url = links[idx]
        print(f"Attempt {attempts}: {url}", flush=True)
        art = fetch_article(url)
        if art and art.get('body'):
            found.append(art)
            print(f"  -> Found {len(found)} valid articles", flush=True)
        else:
            print("  -> Not an article or failed to fetch", flush=True)

    out_file = 'tbs_stories.txt'
    try:
        with open(out_file, 'w', encoding='utf-8') as f:
            for i, a in enumerate(found, 1):
                f.write(f"--- ARTICLE {i} ---\n")
                f.write(f"URL: {a['url']}\n")
                f.write(f"TITLE: {a['title']}\n")
                f.write(f"DATE: {a.get('date','')}\n\n")
                f.write(a['body'] + '\n\n')
        print(f"Saved {len(found)} stories to {out_file}")
    except Exception as e:
        print('Error writing stories file:', e, file=sys.stderr)
        return 1

    print(f"Completed: {len(found)} articles found from {attempts} attempts.", flush=True)

    if len(found) < 10:
        print(f'Only found {len(found)} valid articles (requested 10).')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
