from datetime import datetime, timezone
from pathlib import Path
import urllib.request

ROOT = Path('upper-macleay-council-intelligence')
LOG = ROOT / 'automation' / 'fetch-log.md'
RAW = ROOT / 'fetched' / 'raw'
INDEX = ROOT / 'registers' / 'fetched-source-index.md'
TARGETS = [
    'https://www.kempsey.nsw.gov.au/',
    'https://www.kempsey.nsw.gov.au/sitemap.xml'
]


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def fetch(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'MAYHEM-Council-Records-Fetcher/1.0'})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.geturl(), response.headers.get('Content-Type', 'unknown'), response.read()


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    INDEX.parent.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    log_lines = [f'\n## Fetch Run {run_id}', '', f'Run time UTC: {utc_now()}', '']
    index_lines = ['# Fetched Source Index', '', f'Updated UTC: {utc_now()}', '']
    for number, url in enumerate(TARGETS, start=1):
        try:
            final_url, content_type, body = fetch(url)
            filename = f'source-{number}-{run_id}.txt'
            path = RAW / filename
            path.write_bytes(body)
            log_lines.append(f'- FETCHED: {url}')
            log_lines.append(f'  Final URL: {final_url}')
            log_lines.append(f'  Content type: {content_type}')
            log_lines.append(f'  Saved: {path}')
            index_lines.append(f'- Source: {url}')
            index_lines.append(f'  Final URL: {final_url}')
            index_lines.append(f'  Content type: {content_type}')
            index_lines.append(f'  Saved: {path}')
            index_lines.append('')
        except Exception as error:
            log_lines.append(f'- FAILED: {url}')
            log_lines.append(f'  Error: {error}')
    LOG.write_text('\n'.join(log_lines) + '\n', encoding='utf-8')
    INDEX.write_text('\n'.join(index_lines) + '\n', encoding='utf-8')
    print(f'MAYHEM council fetch run complete: {run_id}')


if __name__ == '__main__':
    main()
