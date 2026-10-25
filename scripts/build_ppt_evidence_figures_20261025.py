"""Typeset two evidence figures from saved records only. No network/model/science calls."""
from pathlib import Path
import datetime as dt
import hashlib
import html
import json
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile

from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader
from pypdf.generic import ContentStream

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'research/2026-10-25_ppt_figures'
FIG = OUT / 'figures'
A = Path('research/2026-10-24_nearfull_complete/live')
B = Path('research/2026-10-23_literature/live_20261024/actual_demo')
REGULAR = Path('C:/Windows/Fonts/arial.ttf')
BOLD = Path('C:/Windows/Fonts/arialbd.ttf')
W, H = 1280, 720
INK, MUTED, TEAL, RED, GRID = '#162C34', '#465C65', '#176C72', '#A52E2E', '#B8C7CB'
manifest = {}


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load(p):
    p = Path(p)
    src = ROOT / p
    manifest[p.as_posix()] = {'sha256': digest(src), 'bytes': src.stat().st_size}
    return json.loads(src.read_text(encoding='utf-8'))


def save_json(p, obj):
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


class Figure:
    """Matching editable SVG and PDF text. No fabricated browser chrome or screenshots."""
    def __init__(self, name, title):
        self.name = name
        self.cv = canvas.Canvas(str(FIG / (name + '.pdf')), pagesize=(W, H), invariant=1)
        self.cv.setTitle(title)
        self.cv.setAuthor('siRNA-GPT evidence export')
        self.svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
                    '<rect width="1280" height="720" fill="white"/>']
        self.records = []
        self.text(48, 51, title, 32, bold=True)

    def text(self, x, y, value, size=19, bold=False, color=INK, source=None):
        assert isinstance(value, str) and '\n' not in value
        # Figure labels are English only; original Chinese is in the retained record/map.
        assert all(ord(c) < 128 for c in value), value
        font = 'Arial-Bold' if bold else 'Arial'
        width = pdfmetrics.stringWidth(value, font, size)
        assert x >= 35 and x + width < W - 25, (value, x, width)
        assert 25 <= y <= H - 22
        self.cv.setFont(font, size)
        self.cv.setFillColor(color)
        self.cv.drawString(x, H-y, value)
        self.svg.append(f'<text x="{x}" y="{y}" font-family="Arial" font-size="{size}" font-weight="{700 if bold else 400}" fill="{color}">{html.escape(value)}</text>')
        self.records.append({'text': value, 'x': x, 'baseline_y': y, 'font_size': size,
                             'font_weight': 'bold' if bold else 'normal', 'width': width,
                             'source': source})

    def lines(self, x, y, values, size=19, leading=25, **kw):
        for i, value in enumerate(values):
            self.text(x, y + leading*i, value, size, **kw)

    def line(self, x1, y1, x2, y2, color=GRID, width=.8):
        self.cv.setStrokeColor(color)
        self.cv.setLineWidth(width)
        self.cv.line(x1, H-y1, x2, H-y2)
        self.svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"/>')

    def finish(self):
        self.cv.showPage()
        self.cv.save()
        self.svg.append('</svg>')
        (FIG / (self.name + '.svg')).write_text('\n'.join(self.svg), encoding='utf-8')
        save_json(FIG / (self.name + '_elements.json'), self.records)


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    for name, path in [('Arial', REGULAR), ('Arial-Bold', BOLD)]:
        assert path.is_file(), path
        pdfmetrics.registerFont(TTFont(name, str(path)))
        # Fail rather than silently substituting another font.
        assert pdfmetrics.getFont(name).face.familyName == b'Arial'

    conv = load(A / 'conversation_export_original.json')
    calls = load(A / 'actual_model_call_summary.json')
    inspected = load(A / 'tool_export/inspect_candidates.json')
    target = load(A / 'tool_export/verify_target.json')
    score = load(A / 'tool_export/score_candidates.json')
    seed = load(A / 'tool_export/match_seed.json')
    expression = load(A / 'tool_export/query_expression.json')
    report = load(A / 'tool_export/report.json')
    plan = load(A / 'tool_export/plan.json')
    assert conv['run_id'] == '20261024_121627_1e50c9'
    assert conv['runtime']['commit'] == '03092ef5fbc2af289aaa2b7bc8d57315c050964f'
    assert len(calls['calls']) == 8 and calls['total_tokens'] == 39048
    assert [x['phase'] for x in calls['calls']] == ['planning'] + ['execution']*7
    events = conv['events']
    tool_ends = [e for e in events if e['kind'] == 'tool_finished']
    assert [e['message'] for e in tool_ends] == plan['tools'] == conv['plan']['completed']
    execution_starts = [e for e in events if e['kind'] == 'model_started']
    execution_ends = [e for e in events if e['kind'] == 'model_finished']
    assert len(execution_starts) == len(execution_ends) == 7
    planner_return = next(e['time'] for e in events if e['kind'] == 'planner_finished')
    timestamp = dt.datetime.fromisoformat
    gap = (timestamp(execution_starts[0]['time']) - timestamp(planner_return)).total_seconds()
    execution = (timestamp(execution_ends[-1]['time']) - timestamp(execution_starts[0]['time'])).total_seconds()
    intervals = [(timestamp(e['time']) - timestamp(s['time'])).total_seconds()
                 for s, e in zip(execution_starts, execution_ends)]
    original_request = next(m['text'] for m in conv['messages'] if m['role'] == 'user')
    wrong = 'GAUAGAGCAAGACAAGACAAGAAA'
    correct = plan['candidates'][0]['passenger_paired_core_19nt_5to3']
    assert len(wrong) == 24 and len(correct) == 19 and wrong in report['model_summary']
    assert inspected['rows'][0]['guide_core19_5to3'] == 'UUUCUUGUCUUGCUCUAUC'
    assert correct == 'GAUAGAGCAAGACAAGAAA'
    assert correct.translate(str.maketrans('ACGU', 'UGCA'))[::-1] == inspected['rows'][0]['guide_core19_5to3']
    assert target['rows'][0]['covered_transcripts'] == 18
    assert expression['candidate_summary'][0]['matched_genes'] == 2839
    assert expression['candidate_summary'][0]['state_detected_genes'] == 1595
    assert score['status'] == seed['status'] == 'IMPORTED_VERIFIED_LOCAL'

    af = Figure('A_purchased_Agent_case', 'One purchased si-VEGF duplex, one recorded Agent run')
    af.text(48, 81, 'Saved-record excerpts, not a web screenshot | run 20261024_121627_1e50c9 | code 03092ef', 17, color=MUTED)
    af.text(48, 116, 'a  User request and confirmed plan', 20, bold=True, color=TEAL)
    af.lines(48, 144, [
        'Review the purchased duplex, preserve TT/N3, use the bound offline results,',
        'check the reference, add expression context and produce a report. [Translated request excerpt]'],
        20, leading=26, source='conversation_export_original.json#/messages/1/text')
    af.text(48, 205, 'Confirmed plan: candidate check; reference check; score; seed; expression; report.', 20,
            source='conversation_export_original.json#/plan/tools')
    af.text(48, 233, '8 model requests = 1 planning + 7 execution requests; 6 tool calls; 39,048 tokens.', 19,
            source='actual_model_call_summary.json')
    af.line(48, 252, 1232, 252)
    af.text(48, 281, 'b  Execution log, 12:16:27-12:17:03 UTC', 20, bold=True, color=TEAL,
            source='conversation events: first model_started to final model_finished')
    af.text(760, 281, 'c  Evidence-derived candidate excerpt', 20, bold=True, color=TEAL)
    af.text(48, 310, 'Call', 17, bold=True)
    af.text(105, 310, 'Tool name (verbatim)', 17, bold=True)
    af.text(340, 310, 'Recorded operation', 17, bold=True)
    af.text(627, 310, 'Tool s', 17, bold=True)
    operations = ['Live input check', 'Live reference match', 'Verified local import',
                  'Verified local import', 'Live baseline join', 'Report saved']
    for i, (e, operation) in enumerate(zip(tool_ends, operations)):
        y = 341 + i*29
        af.text(48, y, 'M' + str(i+1), 18, source=f'events: tool_finished {i+1}')
        af.text(105, y, e['message'], 18, source=f'events: tool_finished {i+1}')
        af.text(340, y, operation, 18, source=f'events: tool_finished {i+1}/status')
        af.text(627, y, f"{e['seconds']:.3f}", 18, source=f'events: tool_finished {i+1}/seconds')
    af.text(48, 521, f'M7: final model answer, {intervals[-1]:.3f} s; no seventh tool.', 18,
            source='conversation events: model_started/finished turn 7')
    af.text(48, 550, 'OligoFormer/SeedMatchR were imported, not rerun in the cloud.', 18,
            source='score_candidates.json + match_seed.json status')
    af.text(760, 314, "Guide core, 19 nt (5'-3')", 17, bold=True)
    af.text(760, 340, inspected['rows'][0]['guide_core19_5to3'], 20,
            source='tool_export/inspect_candidates.json#/rows/0/guide_core19_5to3')
    af.text(760, 373, "Other core, 19 nt (5'-3', conditional role)", 17, bold=True)
    af.text(760, 399, correct, 20, source='tool_export/plan.json#/candidates/0/passenger_paired_core_19nt_5to3')
    af.text(760, 432, 'NM_003376.6: 1439-1457; coverage 18/20', 18, source='tool_export/verify_target.json#/rows/0')
    af.text(760, 462, f"OligoFormer score {score['rows'][0]['oligoformer_scaled_score']:.6f} (not %)", 18, source='tool_export/score_candidates.json#/rows/0')
    af.text(760, 492, 'Guide: 3,539 non-target sites / 2,839 genes', 18, source='tool_export/query_expression.json#/candidate_summary/0')
    af.text(760, 522, '1,595 detected in hypoxia; 3 unmapped', 18, source='tool_export/query_expression.json#/candidate_summary/0')
    af.text(760, 550, 'Conditional roles; TT/N3 retained, not simulated.', 17, source='tool_export/inspect_candidates.json#/rows/0/limits')
    af.line(48, 570, 1232, 570)
    af.text(48, 599, 'Original answer error retained: the passenger core was written as 24 nt, not 19 nt.', 22, bold=True, color=RED,
            source='tool_export/report.json#/model_summary + ANSWER_CORRECTION_ZH.md')
    af.text(48, 628, f'Plan-to-execution gap {gap:.3f} s (includes user wait; click time not logged); execution {execution:.3f} s.', 18,
            source='conversation events: planner_finished to first model_started; first start to final end')
    af.text(48, 655, 'Planner duration not logged. Seed matches and expression are annotations, not measured siRNA effects.', 18,
            source='conversation events + tool_export/query_expression.json#/scope')
    af.text(48, 686, 'Sources: 2026-10-24_nearfull_complete/live/; full original paths, versions and excerpts in SOURCE_MAP.md.', 16, color=MUTED)
    af.finish()

    results = load(B / 'results.json')
    qa_path = B / 'conversation/evidence/ef511585f2734fe999f4f28c.json'
    qa = load(qa_path)
    exchange = load(B / 'conversation/evidence/8adf373e980643189b6f0479.json')
    passed = json.loads(exchange['request']['input'][0]['content'][0]['text'])
    assert len(qa['retrieved_excerpts']) == len(passed['retrieved_excerpts']) == 6
    for q, r in zip(qa['retrieved_excerpts'], passed['retrieved_excerpts']):
        assert q['text'] == r['text'] and q['citation_id'] == r['citation_id']
    b02 = next(r for r in results if r['id'] == 'B02')
    assert qa['answer'] == b02['answer'] and qa['model_call_count'] == 1
    assert b02['usage'][0]['total_tokens'] == 6232
    excerpts = {e['citation_id']: e for e in qa['retrieved_excerpts']}
    paper_sentence = 'The output of the model represents a prediction score for each siRNA, reflecting its potential effectiveness in inducing gene knockdown.'
    code_line = 'Y_PRED = [i*1.341 for i in Y_PRED]'
    code_result = "RESULT['efficacy'] = Y_PRED"
    assert paper_sentence in excerpts['S3']['text']
    assert code_line in excerpts['S2']['text'] and code_result in excerpts['S2']['text']
    assert code_line in excerpts['S5']['text']
    assert '分数超过 1 不能解释为“超过100%敲低率”' in qa['answer']
    assert '不能据此反推出某一具体分数对应的实际敲低百分比' in qa['answer']
    with zipfile.ZipFile(ROOT/B/'library.zip') as archive:
        assert archive.testzip() is None
        code_bytes = archive.read('originals/ec77cffdc9e76e478068430f.txt')
        paper_bytes = archive.read('originals/e2cea21b6712b85250758e8b.txt')
        assert hashlib.sha256(code_bytes).hexdigest() == excerpts['S2']['file_sha256']
        assert hashlib.sha256(paper_bytes).hexdigest() == excerpts['S3']['file_sha256']
        code_text = code_bytes.decode('utf-8')
        paper_text = paper_bytes.decode('utf-8')
        source_lines = [i+1 for i,line in enumerate(code_text.splitlines()) if code_line in line]
        paper_quote_offset = paper_text.index(paper_sentence)
        assert source_lines and paper_quote_offset >= 0
    save_json(OUT/'B02_original_source_locators.json', {
        'official_code': {'zip': str(B/'library.zip'),
                          'entry': 'originals/ec77cffdc9e76e478068430f.txt',
                          'sha256': excerpts['S2']['file_sha256'],
                          'scaling_line_numbers_1based': source_lines,
                          'source_url': excerpts['S2']['source_url'],
                          'source_version': excerpts['S2']['source_version']},
        'article': {'entry': 'originals/e2cea21b6712b85250758e8b.txt',
                    'sha256': excerpts['S3']['file_sha256'],
                    'quote_start_character_0based': paper_quote_offset,
                    'quote_end_character_exclusive': paper_quote_offset + len(paper_sentence),
                    'retrieved_chunk': 'text-c020',
                    'chunk_start': excerpts['S3']['start'], 'chunk_end': excerpts['S3']['end'],
                    'source_url': excerpts['S3']['source_url'],
                    'pdf_page': None},
        'all_six_passed_texts_match_saved_retrieval': True,
        'note': 'Coordinates locate saved text, not a PDF page. No new retrieval or model call.'})
    bf = Figure('B_literature_answer_evidence', 'An answer linked to retrieved evidence')
    bf.text(48, 81, 'Recorded B02 query | 1 model call | 6 retrieved snippets | 6,232 tokens | code 179a7af', 18, color=MUTED)
    bf.text(48, 119, 'a  User question (translated)', 20, bold=True, color=TEAL)
    bf.text(48, 152, 'Can an OligoFormer score above 1 mean more than 100% knockdown?', 25, bold=True,
            source='results.json#/B02/question')
    bf.line(48, 179, 1232, 179)
    bf.text(48, 214, 'b  Evidence actually passed to the model', 22, bold=True, color=TEAL)
    bf.text(780, 214, 'c  Answer (translated excerpts)', 22, bold=True, color=TEAL)
    bf.text(48, 253, '[S3] Article full text, text-c020', 19, bold=True, source='qa retrieved_excerpts S3')
    bf.lines(48, 284, [
        '"The output of the model represents a prediction score',
        'for each siRNA, reflecting its potential effectiveness',
        'in inducing gene knockdown."'], 21, leading=29, source='qa retrieved_excerpts S3 text (verbatim)')
    bf.text(48, 382, 'OligoFormer, DOI: 10.1093/bioinformatics/btae577', 17, color=MUTED, source='qa retrieved_excerpts S3 metadata')
    bf.text(48, 422, '[S2] Official source code, text-c007', 19, bold=True, source='qa retrieved_excerpts S2')
    bf.text(48, 452, code_line, 21, source='qa retrieved_excerpts S2 text (verbatim)')
    bf.text(48, 483, code_result, 21, source='qa retrieved_excerpts S2 text (verbatim)')
    bf.text(48, 515, 'scripts/infer.py @ e2f53ad63387 (also retrieved in S5)', 17, color=MUTED, source='qa retrieved_excerpts S2 + S5 metadata')
    bf.text(48, 555, '[S1] Project setting (translated, not a paper result)', 19, bold=True, source='qa retrieved_excerpts S1')
    bf.text(48, 585, '"The model score is not an experimental knockdown percentage."', 20,
            source='qa retrieved_excerpts S1 text (translated excerpt)')
    bf.text(780, 261, 'No.', 32, bold=True, color=TEAL, source='qa answer verdict (translated)')
    bf.lines(780, 302, [
        'A score above 1 cannot mean',
        'more than 100% knockdown.',
        '[S1, S3]'], 22, leading=29, source='qa answer key result 1 (translated excerpt)')
    bf.lines(780, 410, [
        'The output is linearly scaled',
        'by 1.341. [S2, S5]'], 22, leading=29, source='qa answer key result 2 (translated excerpt)')
    bf.lines(780, 493, [
        'These snippets do not establish',
        'a measured knockdown percentage',
        'for a specific score.'], 21, leading=29, source='qa answer limitation (translated excerpt)')
    bf.line(48, 611, 1232, 611)
    bf.text(48, 641, 'English translations of saved Chinese records; original source quotes retained. Not a web screenshot.', 19, color=MUTED)
    bf.text(48, 669, 'Text fragments, not PDF pages. Source types remain separate. No independent quality score is claimed.', 18, color=MUTED)
    bf.text(48, 695, 'Run library_demo_20261024_032210_21c28f; library b4d516450903...; exact files and S1-S6 in SOURCE_MAP.md.', 16, color=MUTED)
    bf.finish()

    save_json(OUT/'evidence_checks.json', {
        'base_main_commit': '927910c74181417b2d3229e4e8a3ffeedec841bd',
        'source_case_run': conv['run_id'], 'source_case_code': '03092ef5fbc2af289aaa2b7bc8d57315c050964f',
        'model_requests': 8, 'planning_requests': 1, 'execution_requests': 7, 'tool_calls': len(tool_ends),
        'case_tokens': 39048, 'tool_reported_seconds': [e['seconds'] for e in tool_ends],
        'execution_model_intervals_seconds': intervals,
        'plan_return_to_execution_start_seconds': gap,
        'gap_not_pure_model_or_tool_duration': True,
        'confirmation_click_timestamp_available': False,
        'planner_model_duration_available': False,
        'execution_first_start_to_final_end_seconds': execution,
        'original_request': original_request,
        'confirmed_plan': conv['plan'],
        'model_answer_wrong_sequence': wrong, 'verified_other_core': correct,
        'original_answer_unmodified': True,
        'B02_run': 'library_demo_20261024_032210_21c28f',
        'B02_code': qa['runtime']['commit'], 'B02_library': qa['library_version'],
        'B02_model_calls': 1, 'B02_tokens': 6232,
        'B02_all_6_excerpts_match_actual_model_request': True,
        'B02_source_quote_substrings_checked': True,
        'B02_answer_matches_saved_result': True,
        'B02_original_question': qa['question'],
        'B02_displayed_paper_sentence': paper_sentence,
        'B02_retrieved_excerpts': qa['retrieved_excerpts'],
        'B02_original_answer': qa['answer'],
        'new_model_calls_this_batch': 0, 'new_scientific_runs_this_batch': 0,
        'new_browser_capture_this_batch': False, 'production_changes_this_batch': False,
        'font_files': {str(p): digest(p) for p in [REGULAR, BOLD]},
    })
    # Bind exact raw files, retaining their original bytes in the self-contained delivery.
    for path in [A/'tool_export/events.jsonl', A/'ANSWER_CORRECTION_ZH.md', A/'case_completed.png',
                 A/'tool_export/run_config.json', A/'tool_export/verified_import/purchased_sivegf_20261024_v1/manifest.json',
                 A/'tool_export/verified_import/purchased_sivegf_20261024_v1/input_assets.json',
                 A/'tool_export/verified_import/purchased_sivegf_20261024_v1/seed_pilot_02__sessionInfo.txt',
                 B/'library.zip', B.parent/'live_demo_complete.png']:
        src = ROOT/path
        manifest[path.as_posix()] = {'sha256': digest(src), 'bytes': src.stat().st_size}
    for path in (ROOT/A/'tool_export/attempts').glob('*.json'):
        rel = path.relative_to(ROOT).as_posix()
        manifest[rel] = {'sha256': digest(path), 'bytes': path.stat().st_size}
    for rel in manifest:
        dst = OUT/'raw_evidence'/rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT/rel, dst)
        assert digest(dst) == manifest[rel]['sha256']
    # Git stores these text reviews with LF; preserve exact Git bytes rather than
    # claiming that Windows checkout CRLF is the original remote byte sequence.
    for rel in ['docs/reviews/20261025_1040_ppt_figure_selection.md',
                'docs/reviews/20261025_1040_ppt_figure_audit.json']:
        raw = subprocess.run(['git', 'show', '927910c74181417b2d3229e4e8a3ffeedec841bd:'+rel],
                             cwd=ROOT, check=True, capture_output=True).stdout
        assert raw.replace(b'\r\n', b'\n') == (ROOT/rel).read_bytes().replace(b'\r\n', b'\n')
        dst = OUT/'raw_evidence'/rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(raw)
        manifest[rel] = {'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw),
                         'read_method': 'exact_git_blob_at_927910c',
                         'working_copy_newline_normalization_only': True}
    save_json(OUT/'source_manifest.json', manifest)

    font_checks = []
    for name in ['A_purchased_Agent_case', 'B_literature_answer_evidence']:
        path = FIG/(name+'.pdf')
        reader = PdfReader(path)
        assert len(reader.pages) == 1
        page = reader.pages[0]
        assert tuple(float(x) for x in page.mediabox[2:]) == (W, H)
        text = page.extract_text()
        for element in json.loads((FIG/(name+'_elements.json')).read_text(encoding='utf-8')):
            assert element['text'] in text, element['text']
        fonts = []
        for ref in page['/Resources']['/Font'].values():
            font = ref.get_object()
            # ReportLab's unused default Helvetica is not used by any text object.
            base = str(font['/BaseFont'])
            if 'Arial' not in base:
                continue
            descriptor = font['/FontDescriptor'].get_object()
            assert '/FontFile2' in descriptor
            fonts.append({'basefont': base, 'embedded_true_type': True})
        assert len(fonts) == 2, fonts
        active_font = None
        text_showing_fonts = []
        for operands, operator in ContentStream(page['/Contents'].get_object(), reader).operations:
            if operator == b'Tf':
                active_font = operands[0]
            if operator in (b'Tj', b'TJ', b"'", b'"'):
                actual_font = page['/Resources']['/Font'][active_font].get_object()
                assert 'Arial' in str(actual_font['/BaseFont']), actual_font
                text_showing_fonts.append(str(actual_font['/BaseFont']))
        root = ET.parse(FIG/(name+'.svg')).getroot()
        texts = root.findall('{http://www.w3.org/2000/svg}text')
        assert texts and all(t.get('font-family') == 'Arial' for t in texts)
        assert any(t.get('font-weight') == '700' for t in texts)
        font_checks.append({'figure': name, 'page_points': [W,H], 'pdf_fonts': fonts,
                            'editable_svg_text_elements': len(texts), 'all_text_matches_pdf': True,
                            'all_pdf_text_show_operations_use_embedded_Arial': True,
                            'pdf_text_show_operation_count': len(text_showing_fonts)})
        pdftoppm = shutil.which('pdftoppm')
        assert pdftoppm, 'Poppler pdftoppm required'
        subprocess.run([pdftoppm, '-png', '-singlefile', '-scale-to-x', '3840', '-scale-to-y', '2160',
                        str(path), str(FIG/name)], check=True, capture_output=True)
    save_json(OUT/'font_and_format_checks.json', font_checks)
    print(json.dumps({'figures': 2, 'formats': ['editable SVG', 'embedded Arial PDF', '3840x2160 PNG'],
                      'source_files': len(manifest), 'new_model_calls': 0, 'new_scientific_runs': 0,
                      'execution_seconds': execution, 'plan_execution_gap_seconds': gap}))


if __name__ == '__main__':
    main()
