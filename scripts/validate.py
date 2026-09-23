"""Check every generated route and reference, not just a sample."""
import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1] / 'work' / 'python-libs'))
from bs4 import BeautifulSoup

dist = ROOT / 'dist'
brand = json.loads((ROOT / 'brand.json').read_text('utf-8'))
pages = json.loads((ROOT / 'data/pages.json').read_text('utf-8'))
errors = []
references = set()
for page in pages:
    path = page['path']
    file = dist / unquote(path).strip('/') / 'index.html'
    if not file.exists():
        errors.append([path, 'Missing page'])
        continue
    text = file.read_text('utf-8')
    for pattern in ('수려한', '010-9257', '0109257', '조승우', '506-25', '성현로 80', '제2026-00004', 'wcs.pstatic', 'wcs_add', 'naver-site-verification', 'cleanworks.kr', '__BRAND_', '__PAGE_'):
        if pattern in text:
            errors.append([path, 'Old or unresolved content: ' + pattern])
    soup = BeautifulSoup(text, 'html.parser')
    if len(soup.select('h1')) != 1:
        errors.append([path, 'Expected one H1'])
    canonical = soup.select_one('link[rel="canonical"]')
    if not canonical or canonical.get('href') != brand['origin'] + path:
        errors.append([path, 'Canonical mismatch'])
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            json.loads(script.string)
        except Exception:
            errors.append([path, 'Invalid JSON-LD'])
    for tag in soup.select('[src],a[href],link[href]'):
        ref = tag.get('src') or tag.get('href')
        if not ref or ref.startswith(('#', 'data:', 'tel:', 'mailto:')):
            continue
        target = urlparse(urljoin(brand['origin'] + path, ref))
        if target.netloc != urlparse(brand['origin']).netloc:
            continue
        references.add(unquote(target.path))
for ref in references:
    target = dist / ref.lstrip('/')
    if not target.is_file() and not (target / 'index.html').is_file():
        errors.append([ref, 'Missing internal destination'])
for file in (dist / '_astro').glob('*.css'):
    for ref in re.findall(r'url\([\s\"\']*([^\)\"\'\s]+)', file.read_text('utf-8')):
        if ref.startswith(('data:', 'http', '#')):
            continue
        relative = '/' + file.relative_to(dist).as_posix()
        target = dist / unquote(urlparse(urljoin(relative, ref)).path).lstrip('/')
        if not target.exists():
            errors.append([str(file.name), 'Missing CSS asset ' + ref])
report = {'pages': len(pages), 'templates': len(set(p['template'] for p in pages)), 'checked_local_destinations': len(references), 'asset_files': sum(1 for p in (ROOT / 'assets').rglob('*') if p.is_file()), 'errors': errors}
(ROOT / 'validation-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
sys.exit(1 if errors else 0)
