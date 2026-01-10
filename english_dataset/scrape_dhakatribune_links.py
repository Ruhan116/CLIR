#!/usr/bin/env python3
"""Fetch all <loc> links from a Dhaka Tribune daily sitemap and save them to `dhakatribune_links`.
Example sitemap URL: https://www.dhakatribune.com/2025-12-01.xml
"""
from typing import List, Tuple
import re
import sys
import requests
from bs4 import BeautifulSoup
from lxml import etree


SITEMAP_URL = 'https://www.dhakatribune.com/2025-12-01.xml'
OUT_FILE = 'dhakatribune_links'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/xml, text/xml, */*;q=0.1',
    'Accept-Language': 'en-US,en;q=0.9',
}


def fetch(url: str, timeout: int = 25) -> Tuple[bytes, requests.Response]:
    resp = requests.get(url, headers=HEADERS, timeout=timeout)
    resp.raise_for_status()
    return resp.content, resp


def extract_locs_from_soup(soup: BeautifulSoup) -> List[str]:
    urls: List[str] = []
    for loc in soup.find_all('loc'):
        text = loc.get_text(strip=True)
        if text:
            urls.append(text)
    # fallback to namespaced tag names
    if not urls:
        for tag in soup.find_all():
            name = getattr(tag, 'name', '')
            if name and name.lower().endswith('loc'):
                t = tag.get_text(strip=True)
                if t:
                    urls.append(t)
    return urls


def extract_locs_via_lxml(raw: bytes) -> List[str]:
    urls: List[str] = []
    try:
        root = etree.fromstring(raw)
        texts = root.xpath("//*[local-name() = 'loc']/text()")
        for t in texts:
            if t and t.strip():
                urls.append(t.strip())
    except Exception:
        pass
    return urls


def extract_via_regex(text: str) -> List[str]:
    # simple, permissive pattern to capture URLs inside <loc> tags
    pattern = r'<loc>\s*(https?://[^\s<>\"]+)\s*</loc>'
    found = re.findall(pattern, text)
    if found:
        return found
    # domain-restricted fallback
    return re.findall(r'https?://www\.dhakatribune\.com[^\s<>"\']+', text)


def main() -> int:
    try:
        raw, resp = fetch(SITEMAP_URL)
    except Exception as e:
        print('Error fetching sitemap:', e, file=sys.stderr)
        return 1

    # Try BeautifulSoup XML parse
    soup = BeautifulSoup(raw, 'xml')
    links = extract_locs_from_soup(soup)

    # lxml fallback
    if not links:
        links = extract_locs_via_lxml(raw)

    # regex fallback on text
    if not links:
        try:
            text = raw.decode(resp.encoding or 'utf-8', errors='replace')
        except Exception:
            text = raw.decode('utf-8', errors='replace')
        links = extract_via_regex(text)

    # Save raw for debugging if still empty
    if not links:
        try:
            with open('dhakatribune_raw_response.xml', 'wb') as rf:
                rf.write(raw[:1000000])
            print('No <loc> found; saved raw response to dhakatribune_raw_response.xml')
        except Exception:
            pass

    # Deduplicate and write
    unique = []
    seen = set()
    for u in links:
        if u not in seen:
            seen.add(u)
            unique.append(u)

    try:
        with open(OUT_FILE, 'w', encoding='utf-8') as f:
            for u in unique:
                f.write(u + '\n')
    except Exception as e:
        print('Error writing file:', e, file=sys.stderr)
        return 1

    print(f'Saved {len(unique)} links to {OUT_FILE}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
