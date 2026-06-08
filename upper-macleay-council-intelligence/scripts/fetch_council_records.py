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
ISSUE_REGISTER = ROOT / 'registers' / 'master-issue-register.md'
ACTION_REGISTER = ROOT / 'registers' / 'master-action-register.md'
ISSUES_DIR = ROOT / 'issues'
ACTIONS_DIR = ROOT / 'actions'
TARGETS = [
    'https://www.kempsey.nsw.gov.au/',
    'https://www.kempsey.nsw.gov.au/sitemap.xml'
]
MEETING_WORDS = [
    'council-meeting', 'council meeting', 'ordinary-council',
    'extraordinary-council', 'minutes', 'agenda', 'business-paper',
    'business paper', 'business-papers', 'notice-of-motion'
]
ISSUE_KEYWORDS = {
    'flying-fox-camp': ['flying fox', 'flying-fox', 'bat camp', 'grey-headed flying-fox'],
    'roads': ['road maintenance', 'pothole', 'sealed road', 'unsealed road', 'armidale road', 'main street'],
    'bridges': ['bridge', 'causeway', 'flood crossing'],
    'water-security': ['water supply', 'water security', 'water carting', 'potable water'],
    'grants-funding': ['grant', 'funding', 'budget allocation', 'funded'],
    'planning-development': ['development application', 'planning proposal', 'rezoning'],
    'public-health-safety': ['public health', 'safety risk', 'work health safety', 'hazard'],
    'community-facilities': ['hall', 'playground', 'park', 'public toilet', 'community facility'],
    'governance': ['notice of motion', 'councillor', 'resolution', 'ordinary meeting']
}
ACTION_WORDS = ['resolved', 'recommended', 'request', 'report', 'review', 'consultation', 'investigate', 'prepare', 'endorse', 'approve', 'defer']


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def fetch(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'MAYHEM-Council-Records-Fetcher/1.2'})
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


def infer_meeting_date(text):
    patterns = [
        r'(20\d{2})[-_/ ](0?[1-9]|1[0-2])[-_/ ](0?[1-9]|[12]\d|3[01])',
        r'(0?[1-9]|[12]\d|3[01])[-_/ ](0?[1-9]|1[0-2])[-_/ ](20\d{2})'
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            parts = match.groups()
            if len(parts[0]) == 4:
                return f'{int(parts[0]):04d}-{int(parts[1]):02d}-{int(parts[2]):02d}'
            return f'{int(parts[2]):04d}-{int(parts[1]):02d}-{int(parts[0]):02d}'
    return 'unknown-date'


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
    path = issue_dir / 'meeting-references.md'
    lines = [
        f'\n## Reference {source_id}',
        f'Meeting date: {meeting_date}',
        f'Source: {final_url}',
        f'Trigger term: {trigger}',
        'Status: auto-detected, requires source review'
    ]
    append(path, lines)


def write_action_path(action_id, source_id, final_url, meeting_date, trigger):
    ACTIONS_DIR.mkdir(parents=True, exist_ok=True)
    path = ACTIONS_DIR / 'open.md'
    lines = [
        f'\n## {action_id}',
        f'Meeting date: {meeting_date}',
        f'Source ID: {source_id}',
        f'Source: {final_url}',
        f'Action trigger term: {trigger}',
        'Status: Open',
        'Proof of Fact (Human plus Evidence): 0 — Unverified, requires independent audit.'
    ]
    append(path, lines)


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
        f'\n## Fetch Run {run_id}', '',
        f'Run time UTC: {utc_now()}',
        f'Seed targets checked: {len(checked)}',
        f'Meeting candidates discovered: {len(candidates)}',
        f'Meeting records fetched: {len(fetched_records)}',
        f'Issue hits: {len(extracted_issues)}',
        f'Action hits: {len(extracted_actions)}',
        f'Failures: {len(failures)}', '',
        '### Checked Targets'
    ]
    for original, final_url, content_type in checked:
        log_lines.append(f'- {original} -> {final_url} ({content_type})')
    log_lines.append('')
    log_lines.append('### Fetched Meeting Records')
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
        source_lines.append(f'- Source ID: {source_id}')
        source_lines.append(f'  Record type: {record_type}')
        source_lines.append(f'  Meeting date inferred: {meeting_date}')
        source_lines.append(f'  URL: {final_url}')
        source_lines.append(f'  Local path: {path}')
        source_lines.append(f'  Content type: {content_type}')
        source_lines.append(f'  Fetched UTC: {utc_now()}')
        source_lines.append('')
        meeting_lines.append(f'- Candidate Meeting Record: {source_id}')
        meeting_lines.append(f'  Meeting date inferred: {meeting_date}')
        meeting_lines.append(f'  Record type: {record_type}')
        meeting_lines.append(f'  URL: {final_url}')
        meeting_lines.append(f'  Status: source preserved, extraction preliminary')
        meeting_lines.append('')
    for issue, trigger, source_id, meeting_date, final_url in extracted_issues:
        issue_lines.append(f'- Issue: {issue}')
        issue_lines.append(f'  Source ID: {source_id}')
        issue_lines.append(f'  Meeting date: {meeting_date}')
        issue_lines.append(f'  Trigger: {trigger}')
        issue_lines.append(f'  Source: {final_url}')
        issue_lines.append('  Status: auto-detected, requires source review')
        issue_lines.append('')
    for action_id, trigger, source_id, meeting_date, final_url in extracted_actions:
        action_lines.append(f'- Action ID: {action_id}')
        action_lines.append(f'  Source ID: {source_id}')
        action_lines.append(f'  Meeting date: {meeting_date}')
        action_lines.append(f'  Trigger: {trigger}')
        action_lines.append(f'  Source: {final_url}')
        action_lines.append('  Status: Open')
        action_lines.append('')
    append(INDEX, index_lines)
    append(SOURCE_REGISTER, source_lines)
    append(MEETING_REGISTER, meeting_lines)
    append(ISSUE_REGISTER, issue_lines)
    append(ACTION_REGISTER, action_lines)
    print(f'MAYHEM council fetch run complete: {run_id}; records={len(fetched_records)} issues={len(extracted_issues)} actions={len(extracted_actions)}')


if __name__ == '__main__':
    main()
