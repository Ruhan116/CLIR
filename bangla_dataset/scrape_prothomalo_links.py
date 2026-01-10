#!/usr/bin/env python3
"""Fetch article links from a Prothom Alo sitemap and save them to `prothomalo_links`.
Usage:
  python scrape_prothomalo_links.py [SITEMAP_URL_or_local_path]

If the argument is a path to an existing file, it will be read instead of fetched.
"""
from typing import List, Tuple
import sys
import os
import re
import requests
from bs4 import BeautifulSoup
from lxml import etree


DEFAULT_SITEMAPS = [
	'https://www.prothomalo.com/sitemap/sitemap-daily-2023-12-21.xml',
	'https://www.prothomalo.com/sitemap/sitemap-daily-2024-04-21.xml',
	'https://www.prothomalo.com/sitemap/sitemap-daily-2025-11-28.xml',
	'https://www.prothomalo.com/sitemap/sitemap-daily-2025-11-29.xml',
	'https://www.prothomalo.com/sitemap/sitemap-daily-2025-12-21.xml',
	'https://www.prothomalo.com/sitemap/sitemap-daily-2025-11-26.xml',
	'https://www.prothomalo.com/sitemap/sitemap-daily-2020-12-10.xml',
	'https://www.prothomalo.com/sitemap/sitemap-daily-2021-12-01.xml',
]

# place output inside the same directory as this script
OUT_FILE = os.path.join(os.path.dirname(__file__), 'prothomalo_links')
HEADERS = {
	'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
	'Accept': 'application/xml, text/xml, */*;q=0.1',
	'Accept-Language': 'en-US,en;q=0.9',
}


def fetch(url: str, timeout: int = 25) -> Tuple[bytes, requests.Response]:
	resp = requests.get(url, headers=HEADERS, timeout=timeout)
	resp.raise_for_status()
	return resp.content, resp


def extract_locs_via_lxml(raw: bytes) -> List[str]:
	urls: List[str] = []
	try:
		root = etree.fromstring(raw)
		# select <loc> that are children of <url> elements (avoids image:loc)
		texts = root.xpath("//*[local-name() = 'url']/*[local-name() = 'loc']/text()")
		for t in texts:
			if t and t.strip():
				urls.append(t.strip())
	except Exception:
		pass
	return urls


def extract_locs_from_soup(soup: BeautifulSoup) -> List[str]:
	urls: List[str] = []
	for url_tag in soup.find_all(lambda tag: tag.name and tag.name.lower().endswith('url')):
		loc = url_tag.find(lambda t: t.name and t.name.lower().endswith('loc'))
		if loc:
			t = loc.get_text(strip=True)
			if t:
				urls.append(t)
	# fallback: direct <loc> tags (but avoid namespaced ones like image:loc)
	if not urls:
		for loc in soup.find_all('loc'):
			text = loc.get_text(strip=True)
			if text:
				urls.append(text)
	return urls


def extract_via_regex(text: str) -> List[str]:
	# capture URLs inside plain <loc> tags (not image:loc)
	pattern = r'<loc>\s*(https?://[^\s<>"\']+)\s*</loc>'
	found = re.findall(pattern, text)
	if found:
		return found
	return []


def filter_article_urls(urls: List[str]) -> List[str]:
	filtered: List[str] = []
	seen = set()

	media_ext = re.compile(r'\.(?:jpg|jpeg|png|gif|svg|webp|mp4|mov|mp3)(?:\?|$)', re.I)
	media_paths = ('/media/', '/uploads/', '/cdn/', '/images/', '/wp-content/')

	for u in urls:
		if not u:
			continue
		if 'prothomalo.com' not in u:
			continue
		if media_ext.search(u):
			continue
		if any(p in u.lower() for p in media_paths):
			continue
		# basic heuristic: article urls usually do not end with a file extension
		if u not in seen:
			seen.add(u)
			filtered.append(u)
	return filtered


def main() -> int:
	# accept multiple sitemap arguments; if none provided use defaults
	sitemaps = sys.argv[1:] if len(sys.argv) > 1 else DEFAULT_SITEMAPS

	all_links: List[str] = []

	for sitemap in sitemaps:
		raw = None
		resp = None

		if os.path.exists(sitemap):
			try:
				with open(sitemap, 'rb') as f:
					raw = f.read()
			except Exception as e:
				print(f'Error reading local file {sitemap}:', e, file=sys.stderr)
				continue
		else:
			try:
				raw, resp = fetch(sitemap)
			except Exception as e:
				print(f'Error fetching sitemap {sitemap}:', e, file=sys.stderr)
				continue

		links: List[str] = []

		links = extract_locs_via_lxml(raw)

		if not links:
			try:
				soup = BeautifulSoup(raw, 'xml')
				links = extract_locs_from_soup(soup)
			except Exception:
				links = []

		if not links:
			try:
				text = raw.decode(getattr(resp, 'encoding', None) or 'utf-8', errors='replace') if resp else raw.decode('utf-8', errors='replace')
			except Exception:
				text = raw.decode('utf-8', errors='replace')
			links = extract_via_regex(text)

		if not links:
			print(f'No <loc> found in sitemap {sitemap}.', file=sys.stderr)

		all_links.extend(links)

	if not all_links:
		print('No links extracted from any sitemap.', file=sys.stderr)

	# dedupe and filter
	# keep original order for first occurrence
	seen = set()
	unique = []
	for u in all_links:
		if u and u not in seen:
			seen.add(u)
			unique.append(u)

	article_links = filter_article_urls(unique)

	try:
		with open(OUT_FILE, 'w', encoding='utf-8') as f:
			for u in article_links:
				f.write(u + '\n')
	except Exception as e:
		print('Error writing file:', e, file=sys.stderr)
		return 1

	print(f'Saved {len(article_links)} article links to {OUT_FILE}')
	return 0


if __name__ == '__main__':
	raise SystemExit(main())

