from datetime import datetime, timezone
from pathlib import Path
import re
import urllib.parse
import urllib.request

ROOT = Path('upper-macleay-council-intelligence')
CONFIG = ROOT / 'config' / 'source-map.txt'
PRIORITY_REGISTER = ROOT / 'manual-seed' / 'source-priority-register.md'
MANUAL_ISSUE_REGISTER = ROOT / 'registers' / 'manual-seed-issue-register.md'
RAW = ROOT / 'fetched' / 'raw'
LOG = ROOT / 'automation' / 'backfill-log.md'
SOURCE_REGISTER = ROOT / 'registers' / 'historic-backfill-source-register.md'

YEARS = ['2022', '2023', '2024', '2025', '2026']
RECORD_TERMS = [
    'agenda', 'minutes', 'minute', 'business-paper', 'business paper',
    'ordinary-council', 'ordinary council', 'extraordinary-council',
    'extraordinary council', 'notice-of-motion', 'notice of motion',
    'council-meeting', 'council meeting', 'public forum', 'confirmed minutes'
]
DEFAULT_PRIORITY_TERMS = [
    'bellbrook', 'upper macleay', 'flying-fox', 'flying fox', 'bats',
    'camp management', 'public health', 'playground', 'central bellbrook park',
    'community meeting', 'management options', 'armidale road', 'bridge',
    'water carting', 'community facility'
]


def now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read(path):
    return path.read_text(encoding='utf-8', errors='ignore') if path.exists() else ''


def append(path, lines):
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding='utf-8') if path.exists() else ''
    path.write_text(existing.rstrip() + '\n' + '\n'.join(lines) + '\n', encoding='utf-8')


def source_urls():
    if not CONFIG.exists():
        return []
    urls = []
    for line in CONFIG.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        urls.append(line)
    return urls


def priority_terms():
    terms = set(DEFAULT_PRIORITY_TERMS)
    text = read(PRIORITY_REGISTER) + '\n' + read(MANUAL_ISSUE_REGISTER)
    for line in text.splitlines():
        cleaned = line.strip().strip('-').strip()
        if not cleaned or cleaned.startswith('#') or len(cleaned) > 90:
            continue
        lower = cleaned.lower()
        if any(skip in lower for skip in ['proof of fact', 'factual strength', 'plain-language', 'status:', 'rationale:']):
            continue
        if any(char.isalpha() for char in lower):
            terms.add(lower)
    return sorted(terms)


def fetch(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'MAYHEM-Historic-Backfill/1.1'})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.geturl(), response.headers.get('Content-Type', 'unknown'), response.read()


def relevant_text(url, label=''):
    return (urllib.parse.unquote(url) + ' ' + urllib.parse.unquote(label)).lower()


def is_candidate(url, terms, label=''):
    lower = relevant_text(url, label)
    has_year = any(year in lower for year in YEARS)
    has_record_term = any(term in lower for term in RECORD_TERMS)
    has_priority_term = any(term in lower for term in terms if len(term) >= 4)
    is_document = lower.endswith('.pdf') or '.pdf' in lower or lower.endswith('.doc') or lower.endswith('.docx')
    return (has_year and has_record_term) or (has_year and has_priority_term) or (is_document and has_priority_term)


def clean_label(html):
    label = re.sub(r'<[^>]+>', ' ', html)
    label = re.sub(r'\s+', ' ', label)
    return label.strip()


def extract_links(base_url, body, terms):
    text = body.decode('utf-8', errors='ignore')
    found = set()
    for loc in re.findall(r'<loc>\s*([^<]+)\s*</loc>', text, flags=re.I):
        found.add((loc, ''))
    for href, label in re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', text, flags=re.I | re.S):
        found.add((href, clean_label(label)))
    for href in re.findall(r'href=["\']([^"\']+)["\']', text, flags=re.I):
        found.add((href, ''))
    clean = []
    for href, label in found:
        url = urllib.parse.urljoin(base_url, href.strip())
        if url.startswith('https://www.kempsey.nsw.gov.au') and is_candidate(url, terms, label):
            clean.append(url)
    return sorted(set(clean))


def safe_name(url):
    text = urllib.parse.unquote(url)
    text = re.sub(r'https?://', '', text)
    text = re.sub(r'[^A-Za-z0-9._-]+', '-', text).strip('-')
    return text[:150] or 'record'


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    seeds = source_urls()
    terms = priority_terms()
    discovered = []
    failures = []
    checked = []

    for url in seeds:
        try:
            final_url, content_type, body = fetch(url)
            checked.append((url, final_url, content_type))
            if is_candidate(final_url, terms):
                discovered.append(final_url)
            discovered.extend(extract_links(final_url, body, terms))
        except Exception as error:
            failures.append((url, str(error)))

    discovered = sorted(set(discovered))[:350]
    fetched = []
    for index, url in enumerate(discovered, start=1):
        try:
            final_url, content_type, body = fetch(url)
            suffix = '.pdf' if 'pdf' in content_type.lower() or final_url.lower().endswith('.pdf') else '.txt'
            path = RAW / f'historic-{run_id}-{index:03d}-{safe_name(final_url)}{suffix}'
            path.write_bytes(body)
            fetched.append((url, final_url, content_type, path))
        except Exception as error:
            failures.append((url, str(error)))

    log = [f'\n## Historic Backfill Run {run_id}', f'Run UTC: {now()}', f'Seed sources checked: {len(checked)}', f'Priority terms loaded: {len(terms)}', f'Candidate records discovered: {len(discovered)}', f'Candidate records fetched: {len(fetched)}', f'Failures: {len(failures)}', '', '### Checked Sources']
    for original, final_url, content_type in checked:
        log.append(f'- {original} -> {final_url} ({content_type})')
    log.append('')
    log.append('### Fetched Historic Records')
    register = [f'\n## Historic Backfill Source Register {run_id}', '']
    for index, (original, final_url, content_type, path) in enumerate(fetched, start=1):
        source_id = f'HIST-{run_id}-{index:03d}'
        log.append(f'- {source_id}: {final_url} -> {path}')
        register.extend([f'- Source ID: {source_id}', f'  URL: {final_url}', f'  Content type: {content_type}', f'  Local path: {path}', f'  PF(H,E): 0 - fetched record, content requires review.', ''])
    log.append('')
    log.append('### Failures')
    for url, error in failures:
        log.append(f'- {url}: {error}')
    append(LOG, log)
    append(SOURCE_REGISTER, register)
    print(f'Historic backfill complete: seeds={len(seeds)} priority_terms={len(terms)} discovered={len(discovered)} fetched={len(fetched)} failures={len(failures)}')


if __name__ == '__main__':
    main()
