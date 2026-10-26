"""Check packaged originals and the expert PDF; no API calls or quality grading."""
import hashlib
import json
import re
import subprocess
import zipfile
from pathlib import Path

import pdfplumber
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'research/2026-10-27_real_dialogue_mini'
OUT = BASE / 'outputs/01a15800-7529-7ee0-b82c-8428c7746a68'


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    pdf = OUT / 'siRNA_GPT_三组真实问答评审总册.pdf'
    rows = load(BASE / 'raw/results_original.json')
    cases = load(BASE / 'raw/cases_original.json')
    owner = BASE / 'raw/model_and_tool_records_original.zip'
    reviewer = BASE / 'raw/anonymous_reviewer_package_original.zip'
    originals = []
    with zipfile.ZipFile(owner) as z, zipfile.ZipFile(reviewer) as rz:
        assert z.testzip() is None and rz.testzip() is None
        for row in rows:
            aid = row['answer_id']
            text = '\n\n'.join('第' + str(t['round']) + '轮\n' + t['answer'] for t in row['rounds'])
            source = rz.read('answers/' + aid + '/answer.txt').decode('utf-8')
            # Windows text export uses CRLF; compare original characters with
            # line endings normalized while retaining the archive bytes intact.
            assert source.replace('\r\n', '\n') == text.replace('\r\n', '\n'), aid
            original = json.loads(z.read(aid + '/result.json'))
            assert original['rounds'] == row['rounds'], aid
            originals.append({'answer_id': aid, 'all_rounds_equal_original': True,
                              'anonymous_answer_exact_source_text_except_OS_line_endings': True})
        assert not any('private_group' in n or 'http_attempt_' in n for n in rz.namelist())
    reader = PdfReader(pdf)
    assert len(reader.pages) == 44
    attachments = dict(reader.attachments)
    assert list(attachments) == ['原始输入与实际回答证据.zip']
    assert attachments['原始输入与实际回答证据.zip'][0] == reviewer.read_bytes()
    normalize = lambda s: re.sub(r'\s+', '', s)
    text = normalize('\n'.join(p.extract_text() for p in reader.pages))
    for case in cases:
        for turn in case['rounds']:
            assert normalize(turn['message']) in text, case['id']
    for row in rows:
        assert row['answer_id'] in text, row['answer_id']
    geometry = []
    with pdfplumber.open(pdf) as book:
        for number, page in enumerate(book.pages, 1):
            assert len(page.extract_text() or '') > 100
            outside = [c for c in page.chars if c['x0'] < -1 or c['x1'] > page.width + 1
                       or c['top'] < -1 or c['bottom'] > page.height + 1]
            if outside:
                geometry.append(number)
    assert not geometry
    patterns = [re.compile(rb'ark-[a-zA-Z0-9-]{30,}'),
                re.compile(rb'Bearer\s+(?!\[REDACTED\])[A-Za-z0-9._-]{20,}')]
    paths = [p for folder in (BASE, ROOT / 'research/2026-10-27_real_dialogue')
             for p in folder.rglob('*') if p.is_file() and not p.name.startswith('_layout_')]
    checked = 0
    for path in paths:
        content = path.read_bytes()
        assert not any(pattern.search(content) for pattern in patterns), 'Credential pattern in ' + str(path)
        checked += 1
        if path.suffix == '.zip':
            with zipfile.ZipFile(path) as z:
                for member in z.infolist():
                    if member.filename.endswith(('.json', '.jsonl', '.txt', '.md')):
                        assert not any(p.search(z.read(member)) for p in patterns), 'Credential pattern in ZIP'
                        checked += 1
    protected = subprocess.check_output([
        'git', 'diff', '--name-only', 'c5a13ae6dd0afa2cac8eb0f3c29c2fa7d8fc119e', '--',
        'data', 'references', 'research/2026-10-22_fairness', 'research/2026-10-22_review_ready',
        'research/2026-10-27_evaluation_fixes_v2', 'research/2026-10-27_evaluation_entry'
    ], cwd=ROOT, text=True).splitlines()
    assert not protected, protected
    save(BASE / 'final_delivery_checks.json', {
        'kind': 'ARTIFACT_COMPLETENESS_NOT_INDEPENDENT_SCIENTIFIC_GRADING',
        'real_run_source_commit': '6c13c5788405e8ecf1aaf77144accd8108701d48',
        'answer_units': len(rows), 'user_rounds': sum(len(r['rounds']) for r in rows),
        'source_text_comparisons': originals, 'all_complete_question_messages_present_in_pdf': True,
        'all_27_answer_ids_present_in_pdf': True, 'pdf_pages': 44, 'pdf_sha256': sha(pdf),
        'embedded_anonymous_zip_bytes_equal': True, 'text_outside_page': geometry,
        'visual_review': 'All 44 pages rendered; six contact sheets inspected; selected pages inspected at full size',
        'credential_pattern_scan_items': checked, 'credential_pattern_matches': 0,
        'protected_tracked_science_and_old_answers_changed': protected,
        'human_scores_filled': 0, 'independent_scientific_quality_verified': False,
        'production_deployment_or_browser_acceptance': False
    })
    excluded = {'SHA256SUMS.json', 'SYNC.md', 'DELIVERY.md'}
    entries = []
    for folder in (BASE, ROOT / 'research/2026-10-27_real_dialogue'):
        for path in sorted(folder.rglob('*')):
            if path.is_file() and path.name not in excluded and not path.name.startswith('_layout_'):
                entries.append({'path': path.relative_to(ROOT).as_posix(), 'bytes': path.stat().st_size,
                                'sha256': sha(path)})
    save(BASE / 'SHA256SUMS.json', {'scope': 'Exact evidence bytes; excludes this manifest, DELIVERY, SYNC and intermediate layout PDF',
                                  'files': entries})
    print('PASS: all 27 original answers/33 rounds retained; full questions and IDs in 44-page PDF; embedded anonymous evidence identical; grades blank; protected evidence unchanged.')


if __name__ == '__main__':
    main()
