"""Collect the authorized public source with a small, resumable worker pool."""
import concurrent.futures
import hashlib
import json
import re
import sys
import time
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / '.cache'
ORIGIN = 'https://cleanworks.kr'
CACHE.mkdir(exist_ok=True)


def fetch(url):
    key = hashlib.sha256(url.encode()).hexdigest()
    target = CACHE / key
    if target.exists():
        return target.read_bytes()
    for attempt in range(3):
        try:
            response = requests.get(url, timeout=45, headers={'User-Agent': 'HaneolAuthorizedMigration/1.0'})
            response.raise_for_status()
            target.write_bytes(response.content)
            return response.content
        except requests.RequestException:
            if attempt == 2:
                raise
            time.sleep(attempt + 1)


def collect():
    index = ET.fromstring(fetch(ORIGIN + '/sitemap-index.xml'))
    maps = [e.text for e in index.iter() if e.tag.endswith('loc')]
    urls = []
    for sitemap in maps:
        xml = ET.fromstring(fetch(sitemap))
        urls.extend(e.text for e in xml.iter() if e.tag.endswith('loc'))
    urls = list(dict.fromkeys(urls + [ORIGIN + '/privacy/']))
    (ROOT / 'data').mkdir(exist_ok=True)
    (ROOT / 'data' / 'source-urls.json').write_text(json.dumps(urls, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Collecting {len(urls)} pages', flush=True)
    failed = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        jobs = {pool.submit(fetch, u): u for u in urls}
        for n, task in enumerate(concurrent.futures.as_completed(jobs), 1):
            try:
                task.result()
            except Exception as error:
                failed.append({'url': jobs[task], 'error': str(error)})
            if n % 50 == 0 or n == len(urls):
                print(f'Pages {n}/{len(urls)}; failed={len(failed)}', flush=True)
    if failed:
        print(json.dumps(failed, ensure_ascii=False), flush=True)
        sys.exit(1)
    print('Page collection complete', flush=True)


if __name__ == '__main__':
    collect()
