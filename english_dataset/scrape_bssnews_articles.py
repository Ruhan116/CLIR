#!/usr/bin/env python3
"""Fetch up to 10 random BSS articles from `bss_article_links` and save to `bss_stories.txt`.

Heuristics based on the example HTML in `all_scraped_experiment.txt`:
- Title: try `h1`, then `meta[property="og:title"]`, then `<title>` tag.
- Body: prefer main containers like `div.col-sm-9`, `div.panel-body`, then collect all <p> within and filter short/byline/ads.
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

TITLE_SELECTORS = [
    'h1',
    '.article-title',
    'meta[property="og:title"]',
    'title',
]

BODY_CONTAINERS = [
    'div.col-sm-9',
    'div.panel-body',
    'div#content',
    'article',
    'div.container',
]


def load_links(path: str) -> List[str]:
    with open(path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]


def extract_title(soup: BeautifulSoup) -> str:
    # try selectors
    for sel in TITLE_SELECTORS:
        if sel.startswith('meta'):
            m = soup.select_one(sel)
            if m and m.get('content'):
                return m.get('content').strip()
            continue
        el = soup.select_one(sel)
        if el:
            text = el.get_text(separator=' ', strip=True)
            if text:
                return text
    # fallback to head title tag
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    return ''


def extract_body(soup: BeautifulSoup) -> str:
    unwanted_markers = ('Related', 'Related News', 'Most Viewed', 'Comments', 'Related Posts', 'Advertisement')

    # prefer specific containers
    for sel in BODY_CONTAINERS:
        el = soup.select_one(sel)
        if not el:
            continue
        ps = [p.get_text(separator=' ', strip=True) for p in el.find_all('p')]
        ps = [t for t in ps if t]
        if not ps:
            # maybe paragraphs use divs — fallback to text
            txt = el.get_text(separator='\n', strip=True)
            if txt and len(txt) > 50:
                return txt
            continue

        def keep(t: str) -> bool:
            low = t.lower()
            if any(k.lower() in low for k in unwanted_markers):
                return False
            if len(t) < 40 and len(t.split()) < 6:
                return False
            return True

        filtered = [t for t in ps if keep(t)]
        if filtered:
            return '\n\n'.join(filtered)
        # if filtering removed everything, return joined paragraphs
        return '\n\n'.join(ps)

    # fallback: try JSON-LD articleBody
    for s in soup.find_all('script', type='application/ld+json'):
        try:
            import json
            data = json.loads(s.string or '')
            if isinstance(data, dict):
                for key in ('articleBody', 'description'):
                    if key in data and data[key]:
                        return data[key].strip()
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        for key in ('articleBody', 'description'):
                            if key in item and item[key]:
                                return item[key].strip()
        except Exception:
            continue

    # last resort: collect all <p> in page
    ps = [p.get_text(separator=' ', strip=True) for p in soup.find_all('p')]
    ps = [t for t in ps if t and len(t) > 30]
    return '\n\n'.join(ps)


def extract_date(soup: BeautifulSoup) -> str:
    # Try JSON-LD first
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

    # Common meta tags
    meta_attrs = [
        ('property', 'article:published_time'),
        ('name', 'pubdate'),
        ('name', 'publishdate'),
        ('itemprop', 'datePublished'),
    ]
    for attr, val in meta_attrs:
        m = soup.find('meta', attrs={attr: val})
        if m and m.get('content'):
            return m.get('content').strip()

    # time tag
    t = soup.find('time')
    if t:
        if t.get('datetime'):
            return t.get('datetime').strip()
        txt = t.get_text(strip=True)
        if txt:
            return txt

    # some common classes
    for sel in ('.entry_update', '.date', '.post-date', '.published', '.entry-meta time'):
        el = soup.select_one(sel)
        if el:
            txt = el.get_text(strip=True)
            if txt:
                # For entry_update, extract only the first date (before "Update")
                if 'Update' in txt or 'update' in txt:
                    txt = txt.split('Update')[0].strip()
                    # Remove any trailing symbols like ':' or newlines
                    txt = txt.rstrip(':').strip()
                return txt

    return ''


def fetch_article(url: str) -> dict | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception:
        return None
    soup = BeautifulSoup(resp.content, 'html.parser')
    title = extract_title(soup)
    body = extract_body(soup)
    date = extract_date(soup)
    if not body:
        return None
    return {'url': url, 'title': title, 'body': body, 'date': date}


def main() -> int:
    links_path = 'bss_article_links'
    try:
        links = load_links(links_path)
    except Exception as e:
        print('Error loading links:', e, file=sys.stderr)
        return 1

    if not links:
        print('No links found in', links_path, file=sys.stderr)
        return 1

    print(f"Loaded {len(links)} links from {links_path}")
    indices = list(range(len(links)))
    random.shuffle(indices)

    found = []
    attempts = 0
    for idx in indices:
        if len(found) >= 10:
            break
        attempts += 1
        url = links[idx]
        print(f"Attempt {attempts}: {url}")
        art = fetch_article(url)
        if art and art.get('body'):
            found.append(art)
            print(f"  -> Found {len(found)} valid articles")
        else:
            print('  -> Not an article or failed to fetch')

    out_file = 'bss_stories.txt'
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

    print(f"Completed: {len(found)} articles found from {attempts} attempts.")
    if len(found) < 10:
        print(f'Only found {len(found)} valid articles (requested 10).')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
