from pathlib import Path
import re

ROOT = Path('upper-macleay-council-intelligence')
RAW = ROOT / 'fetched' / 'raw'
TEXT = ROOT / 'fetched' / 'text'
REGISTERS = ROOT / 'registers'
REPORTS = ROOT / 'reports'
AUDIT = REPORTS / 'evidence-chain-audit.md'

REGISTER_FILES = [
    REGISTERS / 'master-source-register.md',
    REGISTERS / 'historic-backfill-source-register.md',
    REGISTERS / 'fetched-source-index.md',
    REGISTERS / 'master-meeting-register.md',
    REGISTERS / 'master-issue-register.md',
    REGISTERS / 'master-action-register.md',
    REGISTERS / 'master-decision-register.md',
    REGISTERS / 'master-actor-register.md',
    REGISTERS / 'master-mechanism-register.md',
]


def read(path):
    return path.read_text(encoding='utf-8', errors='ignore') if path.exists() else ''


def referenced_paths():
    refs = set()
    for register in REGISTER_FILES:
        text = read(register)
        for match in re.findall(r'upper-macleay-council-intelligence/[^\s)]+', text):
            refs.add(match.strip())
    return sorted(refs)


def main():
    REPORTS.mkdir(parents=True, exist_ok=True)
    raw_files = sorted(RAW.glob('*')) if RAW.exists() else []
    text_files = sorted(TEXT.glob('*')) if TEXT.exists() else []
    refs = referenced_paths()
    missing = []
    present = []
    for ref in refs:
        path = Path(ref)
        if path.exists():
            present.append(ref)
        else:
            missing.append(ref)
    lines = [
        '# Evidence Chain Audit',
        '',
        'Purpose: check whether register references point back to preserved local source files.',
        '',
        'PF(H,E): 0 — automated audit, requires review before evidentiary use.',
        '',
        '## Counts',
        '',
        f'- Raw preserved files: {len(raw_files)}',
        f'- Extracted text files: {len(text_files)}',
        f'- Referenced local paths: {len(refs)}',
        f'- Referenced paths present: {len(present)}',
        f'- Referenced paths missing: {len(missing)}',
        '',
        '## Missing References',
        ''
    ]
    if missing:
        for item in missing:
            lines.append(f'- {item}')
    else:
        lines.append('- None detected')
    lines.extend(['', '## Present References', ''])
    for item in present[:500]:
        lines.append(f'- {item}')
    AUDIT.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'Evidence chain audit complete: raw={len(raw_files)} text={len(text_files)} refs={len(refs)} missing={len(missing)}')


if __name__ == '__main__':
    main()
