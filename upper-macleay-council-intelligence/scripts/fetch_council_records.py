from datetime import datetime, timezone
from pathlib import Path
import re
import urllib.request

ROOT = Path('upper-macleay-council-intelligence')
LOG = ROOT / 'automation' / 'fetch-log.md'
RAW = ROOT / 'fetched' / 'raw'
INDEX = ROOT / 'registers' / 'fetched-source-index.md'
MEETING_REGISTER = ROOT / 'registers' / 'master-meeting-register.md'
SOURCE_REGISTER = ROOT / 'registers' / 'master-source-register.md'
TARGETS = [
    'https://www.kempsey.nsw.gov.au/',
    'https://www.kempsey.nsw.gov.au/sitemap.xml'
]
MEETING_WORDS = [
    'council-meeting', 'council meeting', 'ordinary-council',
    'extraordinary-council', 'minutes', 'agenda', 'business-paper',
    'business paper', 'business-papers', 'notice-of-motion'
]


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def fetch(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'MAYHEM-Council-Records-Fetcher/1.1'})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.geturl(), response.headers.get('Content-Type', 'unknown'), response.read()


def safe_name(text):
    text = re.sub(r'https?://', '', text)
    text = re.sub(r'[^A-Za-z0-9._-]+', '-', text).strip('-')
    return text[:120] or 'source'


def looks_like_meeting_record(text):
    lower = text.lower()
    return any(word in lower for word in MEETING_WORDS)


def extract_urls(text):
    urls = set()
    urls.update(re.findall(r'<loc>\s*([^<]+)\s*</loc>', text, flags=re.I))
    urls.update(re.findall(r'href=["\']([^"\']+)["\']', text, flags=re.I))
    clean = []
    for url in urls:
        if url.startswith('/'):
            url = 'https://www.kempsey.nsw.gov.au' + url
        if url.startswith('https://www.kempsey.nsw.gov.au') and looks_like_meeting_record(url):
            clean.append(url)
    return sorted(set(clean))


def classify_record(url, content_type):
    lower = (url + ' ' + content_type).lower()
    if 'agenda' in lower:
        return 'agenda'
    if 'minute' in lower:
        return 'minutes'
    if 'business' in lower:
        return 'business-paper'
    if 'motion' in lower:
        return 'notice-of-motion'
    if 'pdf' in lower:
        return 'pdf-record'
    return 'possible-meeting-record'


def append(path, lines):
    existing = path.read_text(encoding='utf-8') if path.exists() else ''
    path.write_text(existing.rstrip() + '\n' + '\n'.join(lines) + '\n', encoding='utf-8')


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    INDEX.parent.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    checked = []
    candidates = []
    failures = []

    for number, url in enumerate(TARGETS, start=1):
        try:
            final_url, content_type, body = fetch(url)
            checked.append((url, final_url, content_type))
            path = RAW / f'seed-{number}-{run_id}.txt'
            path.write_bytes(body)
            text = body.decode('utf-8', errors='ignore')
            candidates.extend(extract_urls(text))
        except Exception as error:
            failures.append((url, str(error)))

    candidates = sorted(set(candidates))[:100]
    fetched_records = []
    for number, url in enumerate(candidates, start=1):
        try:
            final_url, content_type, body = fetch(url)
            record_type = classify_record(final_url, content_type)
            suffix = '.pdf' if 'pdf' in content_type.lower() or final_url.lower().endswith('.pdf') else '.txt'
            path = RAW / f'meeting-record-{number}-{run_id}-{safe_name(final_url)}{suffix}'
            path.write_bytes(body)
            fetched_records.append((url, final_url, content_type, record_type, path))
        except Exception as error:
            failures.append((url, str(error)))

    log_lines = [
        f'\n## Fetch Run {run_id}', '',
        f'Run time UTC: {utc_now()}',
        f'Seed targets checked: {len(checked)}',
        f'Meeting candidates discovered: {len(candidates)}',
        f'Meeting records fetched: {len(fetched_records)}',
        f'Failures: {len(failures)}', '',
        '### Checked Targets'
    ]
    for original, final_url, content_type in checked:
        log_lines.append(f'- {original} -> {final_url} ({content_type})')
    log_lines.append('')
    log_lines.append('### Fetched Meeting Records')
    for url, final_url, content_type, record_type, path in fetched_records:
        log_lines.append(f'- {record_type}: {final_url}')
        log_lines.append(f'  Saved: {path}')
    log_lines.append('')
    log_lines.append('### Failures')
    for url, error in failures:
        log_lines.append(f'- {url}: {error}')
    append(LOG, log_lines)

    index_lines = [f'\n## Source Index Update {run_id}', '']
    source_lines = [f'\n## Source Register Update {run_id}', '']
    meeting_lines = [f'\n## Meeting Register Update {run_id}', '']
    for number, (url, final_url, content_type, record_type, path) in enumerate(fetched_records, start=1):
        source_id = f'SRC-{run_id}-{number:03d}'
        index_lines.append(f'- {source_id}: {final_url} -> {path}')
        source_lines.append(f'- Source ID: {source_id}')
        source_lines.append(f'  Record type: {record_type}')
        source_lines.append(f'  URL: {final_url}')
        source_lines.append(f'  Local path: {path}')
        source_lines.append(f'  Content type: {content_type}')
        source_lines.append(f'  Fetched UTC: {utc_now()}')
        source_lines.append('')
        meeting_lines.append(f'- Candidate Meeting Record: {source_id}')
        meeting_lines.append(f'  Record type: {record_type}')
        meeting_lines.append(f'  URL: {final_url}')
        meeting_lines.append(f'  Status: source preserved, extraction pending')
        meeting_lines.append('')
    append(INDEX, index_lines)
    append(SOURCE_REGISTER, source_lines)
    append(MEETING_REGISTER, meeting_lines)
    print(f'MAYHEM council fetch run complete: {run_id}; records={len(fetched_records)}')


if __name__ == '__main__':
    main()
