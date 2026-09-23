"""Turn public HTML into reusable page shells and page content records."""
import concurrent.futures
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1] / 'work' / 'python-libs'))
from bs4 import BeautifulSoup
from collect import fetch, ORIGIN

ASSETS = ROOT / 'assets'
TEMPLATES = ROOT / 'templates'
TRACKERS = ('pstatic.net', 'cloudflareinsights.com', 'wcs_add', 'wcs_do', 'google-analytics', 'googletagmanager')
REPLACEMENTS = {
    '수려한 홈케어는': '__BRAND_NAME__은', '수려한홈케어는': '__BRAND_NAME__은',
    '수려한 홈케어를': '__BRAND_NAME__을', '수려한홈케어를': '__BRAND_NAME__을',
    '수려한 홈케어와': '__BRAND_NAME__과', '수려한홈케어와': '__BRAND_NAME__과',
    '수려한 홈케어': '__BRAND_NAME__', '수려한홈케어': '__BRAND_NAME__',
    '010-9257-2069': '__BRAND_PHONE__', '01092572069': '__BRAND_PHONE_DIGITS__',
    '조승우': '__BRAND_REPRESENTATIVE__', '506-25-77825': '__BRAND_BUSINESS_NUMBER__',
    '제2026-00004호 (관악구청, 2026-09-11)': '__BRAND_LICENSE__',
    '제2026-00004호 (관악구청)': '__BRAND_LICENSE__',
    '제2026-00004호': '__BRAND_LICENSE__',
    '서울특별시 관악구 성현로 80, 116동 1801호(봉천동, 관악드림타운)': '__BRAND_ADDRESS__',
    '서울특별시 관악구 성현로 80, 116동 1801호': '__BRAND_ADDRESS__',
    '성현로 80, 116동 1801호': '__BRAND_ADDRESS__',
    'https://cleanworks.kr': '__BRAND_ORIGIN__',
}


def tokenize(text):
    for old, new in REPLACEMENTS.items():
        text = text.replace(old, new)
    return text


def process(url):
    soup = BeautifulSoup(fetch(url).decode('utf-8'), 'html.parser')
    if not soup.main:
        raise ValueError('No main: ' + url)
    for node in list(soup.find_all('script')):
        if any(t in str(node) for t in TRACKERS):
            node.decompose()
    for node in soup.select('meta[name$="site-verification"], meta[name="generator"]'):
        node.decompose()
    for node in soup.select('link[rel="icon"], link[rel="apple-touch-icon"]'):
        node['href'] = '/haneol/favicon.svg'
        node['type'] = 'image/svg+xml'
    for node in soup.select('meta[property="og:image"], meta[name="twitter:image"]'):
        node['content'] = '__BRAND_ORIGIN__/images/hero-main.webp'
    for node in soup.select('meta[name="robots"]'):
        node['content'] = '__BRAND_ROBOTS__'
    for node in soup.select('script[type="application/ld+json"]'):
        data = json.loads(node.string or node.get_text())
        def clean(obj):
            if isinstance(obj, dict):
                if obj.get('@type') == 'LocalBusiness':
                    obj['address'] = {'@type': 'PostalAddress', 'streetAddress': '__BRAND_ADDRESS__', 'addressCountry': 'KR'}
                    obj.pop('logo', None)
                for key, value in list(obj.items()):
                    if key == 'image' and isinstance(value, list):
                        obj[key] = [v for v in value if 'og-brand-phone' not in str(v)]
                    elif key == 'image' and isinstance(value, str) and 'og-brand-phone' in value:
                        obj[key] = '__BRAND_ORIGIN__/images/hero-main.webp'
                    clean(obj[key])
            elif isinstance(obj, list):
                for child in obj:
                    clean(child)
        clean(data)
        node.string = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    for img in list(soup.select('img[src*="logo.png"],img[src*="logo-white.png"]')):
        logo = soup.new_tag('span')
        logo['class'] = ['haneol-logo'] + (['haneol-logo-light'] if 'white' in img['src'] else [])
        logo['role'] = 'img'
        logo['aria-label'] = '__BRAND_NAME__'
        logo.string = '__BRAND_NAME__'
        img.replace_with(logo)
    toggle = soup.select_one('#nav-toggle')
    if toggle:
        toggle.decompose()
        burger = soup.select_one('label.burger')
        burger.name = 'button'
        burger.attrs.pop('for', None)
        burger.attrs.pop('aria-hidden', None)
        burger['type'] = 'button'
        burger['aria-label'] = '메뉴 열기'
        burger['aria-expanded'] = 'false'
        burger['aria-controls'] = 'haneol-mobile-menu'
        soup.select_one('.mobile-menu')['id'] = 'haneol-mobile-menu'
    for a in soup.select('a[href^="tel:"]'):
        a['data-phone-link'] = ''
    # Keep the original source CSS and functional page modules, with local overrides.
    link = soup.new_tag('link', rel='stylesheet', href='/haneol/brand.css')
    soup.head.append(link)
    script = soup.new_tag('script', src='/haneol/site.js', defer=True)
    soup.body.append(script)
    for tag in soup.select('a[href]'):
        if tag['href'].startswith(ORIGIN):
            tag['href'] = tag['href'][len(ORIGIN):] or '/'
    # Head metadata is content data, while CSS, preload tags and body shell are shared.
    metadata = []
    for node in list(soup.head.contents):
        if getattr(node, 'name', '') in ('meta', 'title', 'script') or (getattr(node, 'name', '') == 'link' and 'canonical' in node.get('rel', [])):
            metadata.append(str(node.extract()))
    main = str(soup.main)
    soup.main.replace_with('__PAGE_MAIN__')
    soup.head.insert(0, '__PAGE_METADATA__')
    shell = tokenize(str(soup))
    shell_id = hashlib.sha256(shell.encode()).hexdigest()[:12]
    TEMPLATES.mkdir(exist_ok=True)
    (TEMPLATES / (shell_id + '.html')).write_text(shell, encoding='utf-8')
    assets = set()
    for tag in soup.select('[src],link[href]'):
        ref = tag.get('src') or tag.get('href')
        if ref.startswith('/haneol/') or ref.endswith('rss.xml') or 'canonical' in tag.get('rel', []):
            continue
        abs_url = urljoin(url, ref)
        if urlparse(abs_url).netloc == 'cleanworks.kr':
            assets.add(abs_url)
    for tag in BeautifulSoup(main, 'html.parser').select('[src]'):
        abs_url = urljoin(url, tag['src'])
        if urlparse(abs_url).netloc == 'cleanworks.kr':
            assets.add(abs_url)
    return {'path': urlparse(url).path, 'template': shell_id, 'metadata': tokenize(''.join(metadata)), 'main': tokenize(main)}, assets


def download_asset(url):
    path = unquote(urlparse(url).path).lstrip('/')
    dest = ASSETS / path
    if not dest.resolve().is_relative_to(ASSETS.resolve()):
        raise ValueError('Invalid asset path')
    data = fetch(url)
    refs = set()
    if path.endswith(('.css', '.js')):
        text = data.decode('utf-8')
        patterns = [r'url\([\s\"\']*([^\)\"\'\s]+)', r'from\s*[\"\']([^\"\']+)', r'import\s*[\"\']([^\"\']+)']
        for pattern in patterns:
            for ref in re.findall(pattern, text):
                if ref.startswith(('data:', '#')):
                    continue
                abs_url = urljoin(url, ref)
                if urlparse(abs_url).netloc == 'cleanworks.kr':
                    refs.add(abs_url)
        data = text.replace(ORIGIN, '').encode('utf-8')
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return refs


def main():
    sample = '--sample' in sys.argv
    urls = [ORIGIN + '/'] if sample else json.loads((ROOT / 'data/source-urls.json').read_text('utf-8'))
    pages, assets = [], set()
    for index, url in enumerate(urls):
        record, refs = process(url)
        pages.append(record)
        assets.update(refs)
        if (index + 1) % 100 == 0:
            print(f'Content records: {index + 1}/{len(urls)}', flush=True)
    done = set()
    while assets - done:
        batch = sorted(assets - done)
        print(f'Collecting {len(batch)} assets', flush=True)
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            jobs = {pool.submit(download_asset, u): u for u in batch}
            for n, task in enumerate(concurrent.futures.as_completed(jobs), 1):
                assets.update(task.result())
                done.add(jobs[task])
                if n % 50 == 0:
                    print(f'Assets: {len(done)}', flush=True)
    (ROOT / 'data/pages.json').write_text(json.dumps(pages, ensure_ascii=False), encoding='utf-8')
    print(f'Saved {len(pages)} content records; {len(done)} assets', flush=True)


if __name__ == '__main__':
    main()
