import html
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
brand = json.loads((ROOT / 'brand.json').read_text('utf-8'))
pages = json.loads((ROOT / 'data/pages.json').read_text('utf-8'))
dist = ROOT / 'dist'
dist.mkdir(exist_ok=True)
shutil.copytree(ROOT / 'assets', dist, dirs_exist_ok=True)
tokens = {f'__BRAND_{key.upper()}__': str(value) for key, value in brand.items()}
tokens['__BRAND_PHONE_DIGITS__'] = re.sub(r'\D', '', brand['phone'])
tokens['__BRAND_ROBOTS__'] = 'noindex, nofollow' if brand['private_preview'] else 'index, follow, max-image-preview:large'
for page in pages:
    shell = (ROOT / 'templates' / (page['template'] + '.html')).read_text('utf-8')
    output = shell.replace('__PAGE_MAIN__', page['main']).replace('__PAGE_METADATA__', page['metadata'])
    output = output.replace('__BRAND_LICENSE__ (관악구청, 2026-09-11)', '__BRAND_LICENSE__')
    for key, value in tokens.items():
        output = output.replace(key, html.escape(value, quote=True))
    if brand['phone'] == '000-0000-0000':
        output = output.replace('href="tel:00000000000"', 'href="#" data-phone-pending="true"')
    from urllib.parse import unquote
    route = unquote(page['path']).strip('/')
    folder = dist / route
    if not folder.resolve().is_relative_to(dist.resolve()):
        raise ValueError('Invalid route: ' + route)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'index.html').write_text(output, encoding='utf-8')
urls = ''.join('<url><loc>' + html.escape(brand['origin'] + p['path']) + '</loc></url>' for p in pages if p['path'] != '/privacy/')
(dist / 'sitemap-0.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + urls + '</urlset>', encoding='utf-8')
(dist / 'sitemap-index.xml').write_text('<?xml version="1.0"?><sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><sitemap><loc>' + brand['origin'] + '/sitemap-0.xml</loc></sitemap></sitemapindex>', encoding='utf-8')
(dist / 'robots.txt').write_text('User-agent: *\n' + ('Disallow: /\n' if brand['private_preview'] else 'Allow: /\nDisallow: /go/\n') + 'Sitemap: ' + brand['origin'] + '/sitemap-index.xml\n', encoding='utf-8')
(dist / 'rss.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>' + html.escape(brand['name']) + '</title><link>' + brand['origin'] + '</link><description>한얼 청소 서비스 안내</description></channel></rss>', encoding='utf-8')
print(f'Built {len(pages)} pages')
