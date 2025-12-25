#!/usr/bin/env python3
"""Fetch 10 random valid articles from daily_star_links and save to stories.txt.

Valid article if page contains element with classes "pb-20 clearfix".
Title extracted from element with classes "fw-700 e-mb-16 article-title".
"""
import random
import sys
from typing import List

import requests
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}


def load_links(path: str) -> List[str]:
    with open(path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]


def is_valid_article(soup: BeautifulSoup) -> bool:
    return soup.select_one('.pb-20.clearfix') is not None


def extract_title(soup: BeautifulSoup) -> str:
    t = soup.select_one('.fw-700.e-mb-16.article-title')
    return t.get_text(strip=True) if t else ''


def extract_body(soup: BeautifulSoup) -> str:
    c = soup.select_one('.pb-20.clearfix')
    if not c:
        return ''
    return c.get_text(separator='\n', strip=True)


def fetch_article(url: str) -> dict | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception:
        return None
    soup = BeautifulSoup(resp.content, 'html.parser')
    if not is_valid_article(soup):
        return None
    return {
        'url': url,
        'title': extract_title(soup),
        'body': extract_body(soup),
    }


def main() -> int:
    links_path = 'daily_star_links'
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
    print('Searching for up to 10 valid articles (random order)...', flush=True)

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

    out_file = 'stories.txt'
    try:
        with open(out_file, 'w', encoding='utf-8') as f:
            for i, a in enumerate(found, 1):
                f.write(f"--- ARTICLE {i} ---\n")
                f.write(f"URL: {a['url']}\n")
                f.write(f"TITLE: {a['title']}\n\n")
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
