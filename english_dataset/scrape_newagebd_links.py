#!/usr/bin/env python3
"""Fetch all <loc> links from https://www.newagebd.net/news-sitemap/1.xml
Save them to `newagebd_links` and print the total count.
"""
import re
import sys
import requests


def main() -> int:
    sitemap_url = 'https://www.newagebd.net/news-sitemap/1.xml'
    
    try:
        # Simple request - no custom headers needed
        response = requests.get(sitemap_url, timeout=30)
        response.raise_for_status()
        
        # Get the text content
        content = response.text
        
        # Extract all URLs using regex
        # Pattern matches URLs inside <loc> tags, handling whitespace
        pattern = r'<loc>\s*(https://www\.newagebd\.net/[^\s<]+)\s*</loc>'
        links = re.findall(pattern, content)
        
        # Alternative: simpler pattern if the above doesn't catch everything
        if not links:
            pattern = r'https://www\.newagebd\.net/post/[^\s<>"]+'
            links = re.findall(pattern, content)
        
        # Write to file
        out_file = 'newagebd_links'
        with open(out_file, 'w', encoding='utf-8') as f:
            for link in links:
                f.write(link + '\n')
        
        print(f'Saved {len(links)} links to {out_file}')
        print(len(links))
        return 0
        
    except requests.exceptions.RequestException as e:
        print(f'Error fetching sitemap: {e}', file=sys.stderr)
        return 1
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())