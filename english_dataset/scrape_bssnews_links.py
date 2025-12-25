#!/usr/bin/env python3
"""Extract article links from a messy BSS sitemap.

Usage:
  - default: edit SITEMAP_URL in the file and run
  - or pass a local sitemap file path or URL as first arg

Heuristics used to identify article links:
  - URL contains a date-like segment (YYYY/MM/DD or YYYY-MM-DD)
  - URL path contains a numeric id (6+ digits) or '/news/' '/story/' '/article/'
  - URL path depth >= 3 and last path segment contains hyphens (slug)
  - exclude common non-article paths (category, tag, author, page, feed, amp, search)
"""
from typing import List, Set
import sys
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# default sitemap (edit if you have exact URL)
SITEMAP_URL = 'https://www.bssnews.net/sitemap.xml'
OUT_FILE = 'bss_article_links'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

EXCLUDE_KEYWORDS = (
    'category', 'tag', 'author', 'page', '/page/', '/feed', '/tag/', '/category/', 'amp', 'search', 'wp-json', 'xml', 'rss'
)

INCLUDE_PATTERNS = (
    re.compile(r'/\d{4}/\d{2}/\d{2}/'),           # /YYYY/MM/DD/
    re.compile(r'/\d{4}-\d{2}-\d{2}/'),           # /YYYY-MM-DD/
    re.compile(r'/news/\d+'),                      # /news/1234
    re.compile(r'/story/\d+'),                     # /story/1234
    re.compile(r'/article/\d+'),                   # /article/1234
    re.compile(r'/\d{6,}'),                        # numeric id in path
)


def fetch_content(src: str) -> bytes:
    if src.startswith('http://') or src.startswith('https://'):
        r = requests.get(src, headers=HEADERS, timeout=20)
        r.raise_for_status()
        return r.content
    # local file
    with open(src, 'rb') as f:
        return f.read()


def extract_all_urls_from_xml(raw: bytes) -> List[str]:
    links: List[str] = []
    try:
        soup = BeautifulSoup(raw, 'xml')
        for loc in soup.find_all('loc'):
            text = (loc.string or '').strip()
            if text:
                links.append(text)
    except Exception:
        pass

    # fallback: regex for http(s) URLs
    if not links:
        txt = raw.decode('utf-8', errors='replace')
        links = re.findall(r"https?://[^\s<>\"']+", txt)
    return links


def is_article_url(u: str) -> bool:
    low = u.lower()
    # exclude obvious non-article links
    for k in EXCLUDE_KEYWORDS:
        if k in low:
            return False

    # include by strong patterns
    for p in INCLUDE_PATTERNS:
        if p.search(u):
            return True

    # else use heuristics: path depth and slug-like last segment
    try:
        p = urlparse(u)
        path = p.path or ''
        parts = [seg for seg in path.split('/') if seg]
        if len(parts) >= 3:
            last = parts[-1]
            # slug with hyphens (and letters)
            if '-' in last and re.search(r'[a-zA-Z]', last):
                # avoid pure numeric slugs
                if not re.fullmatch(r'\d+', last):
                    return True
            # last segment long enough to be article
            if len(last) > 40 or (len(last.split('-')) >= 2 and len(last) >= 10):
                return True
    except Exception:
        pass

    return False


def filter_article_links(links: List[str]) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for u in links:
        u = u.strip()
        if not u or u in seen:
            continue
        seen.add(u)
        if is_article_url(u):
            out.append(u)
    return out


def main(argv: List[str]) -> int:
    src = argv[1] if len(argv) > 1 else SITEMAP_URL
    try:
        raw = fetch_content(src)
    except Exception as e:
        print('Error fetching sitemap:', e, file=sys.stderr)
        return 1

    all_links = extract_all_urls_from_xml(raw)
    print(f'Found {len(all_links)} total URLs in sitemap/content')

    article_links = filter_article_links(all_links)
    print(f'Filtered {len(article_links)} probable article links')

    try:
        with open(OUT_FILE, 'w', encoding='utf-8') as f:
            for u in article_links:
                f.write(u + '\n')
    except Exception as e:
        print('Error writing output file:', e, file=sys.stderr)
        return 1

    # print a small sample
    for u in article_links[:10]:
        print(' -', u)

    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
