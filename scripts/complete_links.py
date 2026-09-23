import concurrent.futures
import json
from urllib.parse import quote
from migrate import ROOT, ORIGIN, process, download_asset

pages = json.loads((ROOT / 'data/pages.json').read_text('utf-8'))
errors = json.loads((ROOT / 'validation-report.json').read_text('utf-8'))['errors']
paths = [row[0] for row in errors if row[1] == 'Missing internal destination' and row[0].endswith('/')]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    for record, assets in pool.map(process, [ORIGIN + quote(p) for p in paths]):
        pages.append(record)
        for asset in assets:
            download_asset(asset)
        print('Added ' + record['path'], flush=True)
(ROOT / 'data/pages.json').write_text(json.dumps(pages, ensure_ascii=False), encoding='utf-8')
print(f'Total {len(pages)}')
