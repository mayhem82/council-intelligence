from datetime import datetime, timezone
from pathlib import Path
import re
import urllib.parse
import urllib.request

ROOT = Path('upper-macleay-council-intelligence')
SOURCE_MAP = ROOT / 'config' / 'source-map.txt'
SOURCE_PRIORITY = ROOT / 'manual-seed' / 'source-priority-register.md'
MANUAL_ISSUE_REGISTER = ROOT / 'registers' / 'manual-seed-issue-register.md'
LOG = ROOT / 'automation' / 'fetch-log.md'
RAW = ROOT / 'fetched' / 'raw'
INDEX = ROOT / 'registers' / 'fetched-source-index.md'
MEETING_REGISTER = ROOT / 'registers' / 'master-meeting-register.md'
SOURCE_REGISTER = ROOT / 'registers' / 'master-source-register.md'
ISSUE_REGISTER = ROOT / 'registers' / 'master-issue-register.md'
ACTION_REGISTER = ROOT / 'registers' / 'master-action-register.md'
ISSUES_DIR = ROOT / 'issues'
ACTIONS_DIR = ROOT / 'actions'

DEFAULT_TARGETS = [
    'https://www.kempsey.nsw.gov.au/',
    'https://www.kempsey.nsw.gov.au/sitemap.xml'
]

MEETING_WORDS = [
    'council-meeting', 'council meeting', 'ordinary-council',
    'ordinary council', 'extraordinary-council', 'extraordinary council',
    'minutes', 'minute', 'agenda', 'business-paper', 'business paper',
    'business-papers', 'notice-of-motion', 'notice of motion',
    'annual-report', 'annual report', 'budget', 'public-exhibition',
    'public exhibition', 'operational plan', 'delivery program',
    'confirmed-minutes', 'confirmed minutes'
]

YEARS = ['2022', '2023', '2024', '2025', '2026']

ISSUE_KEYWORDS = {
    'flying-fox-camp': ['flying fox', 'flying-fox', 'bat camp', 'bats', 'grey-headed flying-fox', 'bellbrook park', 'central bellbrook park'],
    'roads': ['road maintenance', 'pothole', 'sealed road', 'unsealed road', 'armidale road', 'main street'],
    'bridges': ['bridge', 'causeway', 'flood crossing'],
    'water-security': ['water supply', 'water security', 'water carting', 'potable water'],
    'grants-funding': ['grant', 'funding', 'budget allocation', 'funded'],
    'planning-development': ['development application', 'planning proposal', 'rezoning'],
    'public-health-safety': ['public health', 'safety risk', 'work health safety', 'hazard', 'playground safety'],
    'community-facilities': ['hall', 'playground', 'park', 'public toilet', 'community facility'],
    'governance': ['notice of motion', 'councillor', 'resolution', 'ordinary meeting', 'report requested', 'deferred report']
}

ACTION_WORDS = ['resolved', 'recommended', 'request', 'report', 'review', 'consultation', 'investigate', 'prepare', 'endorse', 'approve', 'defer']


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read(path):
    return path.read_text(encoding='utf-8', errors='ignore') if path.exists() else ''


def load_targets():
    targets = list(DEFAULT_TARGETS)
    if SOURCE_MAP.exists():
        for line in SOURCE_MAP.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if line and not line.startswith('#'):
                targets.append(line)
    return sorted(set(targets))


def load_priority_terms():
    text = read(SOURCE_PRIORITY) + '\n' + read(MANUAL_ISSUE_REGISTER)
    terms = set()
    for line in text.splitlines():
        cleaned = line.strip().strip('-').strip()
        if not cleaned or cleaned.startswith('#'):
            continue
        if len(cleaned) > 80:
            continue
        lower = cleaned.lower()
        if any(marker in lower for marker in ['proof of fact', 'factual strength', 'plain-language', 'status:', 'rationale:']):
            continue
        if any(char.isalpha() for char in lower):
            terms.add(lower)
    for required in ['bellbrook', 'flying fox', 'flying-fox', 'ordinary council meeting 20 may 2025', '20 may 2025', '18 march 2026', 'camp management', 'public health', 'playground', 'central bellbrook park']:
        terms.add(required)
    return sorted(terms)


def fetch(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'MAYHEM-Council-Records-Fetcher/1.5'})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.geturl(), response.headers.get('Content-Type', 'unknown'), response.read()


def safe_name(text):
    text = urllib.parse.unquote(text)
    text = re.sub(r'https?://', '', text)
    text = re.sub(r'[^A-Za-z0-9._-]+', '-', text).strip('-')
    return text[:150] or 'source'


def relevant_text(url, label=''):
    return (urllib.parse.unquote(url) + ' ' + urllib.parse.unquote(label)).lower()


def looks_like_record(url, priority_terms, label=''):
    lower = relevant_text(url, label)
    has_record_word = any(word in lower for word in MEETING_WORDS)
    has_year = any(year in lower for year in YEARS)
    has_priority_term = any(term in lower for term in priority_terms if len(term) >= 4)
    is_pdf_or_doc = lower.endswith('.pdf') or '.pdf' in lower or lower.endswith('.docx') or lower.endswith('.doc')
    return has_record_word or (has_year and is_pdf_or_doc) or (has_priority_term and (has_year or is_pdf_or_doc or has_record_word))


def extract_urls(base_url, text, priority_terms):
    urls = set()
    for loc in re.findall(r'<loc>\s*([^<]+)\s*</loc>', text, flags=re.I):
        url = urllib.parse.urljoin(base_url, loc.strip())
        if url.startswith('https://www.kempsey.nsw.gov.au') and looks_like_record(url, priority_terms):
            urls.add(url)
    for href, label in re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', text, flags=re.I | re.S):
        label = re.sub(r'<[^>]+>', ' ', label)
        label = re.sub(r'\s+', ' ', label).strip()
        url = urllib.parse.urljoin(base_url, href.strip())
        if url.startswith('https://www.kempsey.nsw.gov.au') and looks_like_record(url, priority_terms, label):
            urls.add(url)
    for href in re.findall(r'href=["\']([^"\']+)["\']', text, flags=re.I):
        url = urllib.parse.urljoin(base_url, href.strip())
        if url.startswith('https://www.kempsey.nsw.gov.au') and looks_like_record(url, priority_terms):
            urls.add(url)
    return sorted(urls)


def classify_record(url, content_type):
    lower = (urllib.parse.unquote(url) + ' ' + content_type).lower()
    if 'agenda' in lower:
        return 'agenda'
    if 'minute' in lower:
        return 'minutes'
    if 'business' in lower:
        return 'business-paper'
    if 'motion' in lower:
        return 'notice-of-motion'
    if 'annual' in lower:
        return 'annual-report'
    if 'budget' in lower:
        return 'budget-record'
    if 'pdf' in lower:
        return 'pdf-record'
    return 'possible-council-record'


def infer_meeting_date(text):
    patterns = [
        r'(20\d{2})[-_/ ](0?[1-9]|1[0-2])[-_/ ](0?[1-9]|[12]\d|3[01])',
        r'(0?[1-9]|[12]\d|3[01])[-_/ ](0?[1-9]|1[0-2])[-_/ ](20\d{2})',
        r'(20\d{2})[-_/ ]?(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[-_/ ]?(0?[1-9]|[12]\d|3[01])',
        r'(0?[1-9]|[12]\d|3[01])[-_/ ]?(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[-_/ ]?(20\d{2})'
    ]
    months = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6, 'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12}
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.I)
        if match:
            parts = match.groups()
            if len(parts[0]) == 4 and parts[1].isdigit():
                return f'{int(parts[0]):04d}-{int(parts[1]):02d}-{int(parts[2]):02d}'
            if parts[0].isdigit() and parts[1].isdigit():
                return f'{int(parts[2]):04d}-{int(parts[1]):02d}-{int(parts[0]):02d}'
            if len(parts[0]) == 4:
                return f'{int(parts[0]):04d}-{months[parts[1][:3].lower()]:02d}-{int(parts[2]):02d}'
            return f'{int(parts[2]):04d}-{months[parts[1][:3].lower()]:02d}-{int(parts[0]):02d}'
    year = next((year for year in YEARS if year in text), None)
    return f'{year}-00-00' if year else 'unknown-date'


def extract_issue_hits(text):
    lower = text.lower()
    hits = []
    for issue, terms in ISSUE_KEYWORDS.items():
        for term in terms:
            if term in lower:
                hits.append((issue, term))
                break
    return hits


def extract_action_hits(text):
    lower = text.lower()
    return [word for word in ACTION_WORDS if word in lower]


def append(path, lines):
    existing = path.read_text(encoding='utf-8') if path.exists() else ''
    path.write_text(existing.rstrip() + '\n' + '\n'.join(lines) + '\n', encoding='utf-8')


def write_issue_path(issue, source_id, final_url, meeting_date, trigger):
    issue_dir = ISSUES_DIR / issue
    issue_dir.mkdir(parents=True, exist_ok=True)
    append(issue_dir / 'meeting-references.md', [
        f'\n## Reference {source_id}',
        f'Meeting date: {meeting_date}',
        f'Source: {final_url}',
        f'Trigger term: {trigger}',
        'Status: auto-detected, requires source review',
        'Proof of Fact (Human plus Evidence): 0 — Unverified, requires independent audit.'
    ])


def write_action_path(action_id, source_id, final_url, meeting_date, trigger):
    ACTIONS_DIR.mkdir(parents=True, exist_ok=True)
    append(ACTIONS_DIR / 'open.md', [
        f'\n## {action_id}',
        f'Meeting date: {meeting_date}',
        f'Source ID: {source_id}',
        f'Source: {final_url}',
        f'Action trigger term: {trigger}',
        'Status: Open',
        'Proof of Fact (Human plus Evidence): 0 — Unverified, requires independent audit.'
    ])


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    INDEX.parent.mkdir(parents=True, exist_ok=True)
    ISSUES_DIR.mkdir(parents=True, exist_ok=True)
    ACTIONS_DIR.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    checked = []
    candidates = []
    failures = []
    targets = load_targets()
    priority_terms = load_priority_terms()

    for number, url in enumerate(targets, start=1):
        try:
            final_url, content_type, body = fetch(url)
            checked.append((url, final_url, content_type))
            path = RAW / f'seed-{number}-{run_id}.txt'
            path.write_bytes(body)
            text = body.decode('utf-8', errors='ignore')
            candidates.extend(extract_urls(final_url, text, priority_terms))
        except Exception as error:
            failures.append((url, str(error)))

    candidates = sorted(set(candidates))[:500]
    fetched_records = []
    extracted_issues = []
    extracted_actions = []
    for number, url in enumerate(candidates, start=1):
        try:
            final_url, content_type, body = fetch(url)
            record_type = classify_record(final_url, content_type)
            meeting_date = infer_meeting_date(final_url)
            suffix = '.pdf' if 'pdf' in content_type.lower() or final_url.lower().endswith('.pdf') else '.txt'
            path = RAW / f'meeting-record-{number}-{run_id}-{safe_name(final_url)}{suffix}'
            path.write_bytes(body)
            source_id = f'SRC-{run_id}-{number:03d}'
            text_probe = (final_url + '\n' + body[:50000].decode('utf-8', errors='ignore'))
            issue_hits = extract_issue_hits(text_probe)
            action_hits = extract_action_hits(text_probe)
            for issue, trigger in issue_hits:
                write_issue_path(issue, source_id, final_url, meeting_date, trigger)
                extracted_issues.append((issue, trigger, source_id, meeting_date, final_url))
            for action_number, trigger in enumerate(action_hits, start=1):
                action_id = f'ACT-{run_id}-{number:03d}-{action_number:02d}'
                write_action_path(action_id, source_id, final_url, meeting_date, trigger)
                extracted_actions.append((action_id, trigger, source_id, meeting_date, final_url))
            fetched_records.append((source_id, url, final_url, content_type, record_type, meeting_date, path))
        except Exception as error:
            failures.append((url, str(error)))

    log_lines = [
        f'\n## Fetch Run {run_id}', '', f'Run time UTC: {utc_now()}',
        f'Source-map targets checked: {len(checked)}',
        f'Priority terms loaded: {len(priority_terms)}',
        f'Meeting/source candidates discovered: {len(candidates)}',
        f'Meeting/source records fetched: {len(fetched_records)}',
        f'Issue hits: {len(extracted_issues)}', f'Action hits: {len(extracted_actions)}',
        f'Failures: {len(failures)}', '', '### Checked Targets'
    ]
    for original, final_url, content_type in checked:
        log_lines.append(f'- {original} -> {final_url} ({content_type})')
    log_lines.append('')
    log_lines.append('### Priority Terms Sample')
    for term in priority_terms[:80]:
        log_lines.append(f'- {term}')
    log_lines.append('')
    log_lines.append('### Fetched Records')
    for source_id, url, final_url, content_type, record_type, meeting_date, path in fetched_records:
        log_lines.append(f'- {source_id} {record_type}: {final_url}')
        log_lines.append(f'  Meeting date: {meeting_date}')
        log_lines.append(f'  Saved: {path}')
    log_lines.append('')
    log_lines.append('### Failures')
    for url, error in failures:
        log_lines.append(f'- {url}: {error}')
    append(LOG, log_lines)

    index_lines = [f'\n## Source Index Update {run_id}', '']
    source_lines = [f'\n## Source Register Update {run_id}', '']
    meeting_lines = [f'\n## Meeting Register Update {run_id}', '']
    issue_lines = [f'\n## Issue Register Update {run_id}', '']
    action_lines = [f'\n## Action Register Update {run_id}', '']
    for source_id, url, final_url, content_type, record_type, meeting_date, path in fetched_records:
        index_lines.append(f'- {source_id}: {final_url} -> {path}')
        source_lines.extend([f'- Source ID: {source_id}', f'  Record type: {record_type}', f'  Meeting date inferred: {meeting_date}', f'  URL: {final_url}', f'  Local path: {path}', f'  Content type: {content_type}', f'  Fetched UTC: {utc_now()}', '  Proof of Fact (Human plus Evidence): 0 — Unverified, requires independent audit.', ''])
        meeting_lines.extend([f'- Candidate Meeting Record: {source_id}', f'  Meeting date inferred: {meeting_date}', f'  Record type: {record_type}', f'  URL: {final_url}', '  Status: source preserved, extraction preliminary', '  Proof of Fact (Human plus Evidence): 0 — Unverified, requires independent audit.', ''])
    for issue, trigger, source_id, meeting_date, final_url in extracted_issues:
        issue_lines.extend([f'- Issue: {issue}', f'  Source ID: {source_id}', f'  Meeting date: {meeting_date}', f'  Trigger: {trigger}', f'  Source: {final_url}', '  Status: auto-detected, requires source review', '  Proof of Fact (Human plus Evidence): 0 — Unverified, requires independent audit.', ''])
    for action_id, trigger, source_id, meeting_date, final_url in extracted_actions:
        action_lines.extend([f'- Action ID: {action_id}', f'  Source ID: {source_id}', f'  Meeting date: {meeting_date}', f'  Trigger: {trigger}', f'  Source: {final_url}', '  Status: Open', '  Proof of Fact (Human plus Evidence): 0 — Unverified, requires independent audit.', ''])
    append(INDEX, index_lines)
    append(SOURCE_REGISTER, source_lines)
    append(MEETING_REGISTER, meeting_lines)
    append(ISSUE_REGISTER, issue_lines)
    append(ACTION_REGISTER, action_lines)
    print(f'MAYHEM council fetch run complete: {run_id}; targets={len(targets)} priority_terms={len(priority_terms)} records={len(fetched_records)} issues={len(extracted_issues)} actions={len(extracted_actions)}')


if __name__ == '__main__':
    main()
