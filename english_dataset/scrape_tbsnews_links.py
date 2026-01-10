import sys
from typing import List

import requests
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}


def fetch_sitemap_links(url: str) -> List[str]:
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, "xml")

    links: List[str] = []
    # Prefer <loc> tags used in sitemaps
    for loc in soup.find_all('loc'):
        if loc.string:
            links.append(loc.string.strip())

    # Fallback: find <a href=> links if no <loc> found
    if not links:
        for a in soup.find_all('a', href=True):
            links.append(a['href'])

    return links


def main() -> int:
    url = "https://www.tbsnews.net/sitemap.xml?page=1"
    try:
        links = fetch_sitemap_links(url)
    except Exception as e:
        print("Error fetching sitemap:", e, file=sys.stderr)
        return 1

    # Print the first 5 links
    for item in links[:5]:
        print(item)

    # Save all links to a file
    links_file = 'tbsnews_links'
    try:
        with open(links_file, 'w', encoding='utf-8') as f:
            for l in links:
                f.write(l + '\n')
        print(f"Saved {len(links)} links to {links_file}")
    except Exception as e:
        print("Error writing links file:", e, file=sys.stderr)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
