from pathlib import Path

ROOT = Path('upper-macleay-council-intelligence')
RAW = ROOT / 'fetched' / 'raw'
TEXT = ROOT / 'fetched' / 'text'
LOG = ROOT / 'automation' / 'pdf-extraction-log.md'


def append(path, lines):
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding='utf-8') if path.exists() else ''
    path.write_text(existing.rstrip() + '\n' + '\n'.join(lines) + '\n', encoding='utf-8')


def extract_with_pypdf(path):
    try:
        from pypdf import PdfReader
    except Exception:
        return None, 'pypdf unavailable'
    try:
        reader = PdfReader(str(path))
        pages = []
        for index, page in enumerate(reader.pages, start=1):
            try:
                pages.append(f'\n\n--- Page {index} ---\n' + (page.extract_text() or ''))
            except Exception as error:
                pages.append(f'\n\n--- Page {index} extraction failed: {error} ---\n')
        return ''.join(pages), None
    except Exception as error:
        return None, str(error)


def main():
    TEXT.mkdir(parents=True, exist_ok=True)
    pdfs = sorted(RAW.glob('*.pdf')) if RAW.exists() else []
    converted = 0
    failed = 0
    lines = ['\n## PDF Extraction Run', '']
    for pdf in pdfs:
        out = TEXT / (pdf.stem + '.txt')
        text, error = extract_with_pypdf(pdf)
        if text is None:
            failed += 1
            lines.append(f'- FAILED: {pdf} | {error}')
            continue
        out.write_text(text, encoding='utf-8')
        converted += 1
        lines.append(f'- EXTRACTED: {pdf} -> {out}')
    lines.extend(['', f'Converted: {converted}', f'Failed: {failed}'])
    append(LOG, lines)
    print(f'PDF extraction complete: converted={converted} failed={failed}')


if __name__ == '__main__':
    main()
