"""Score-conserving, three-column Sankey using the user-confirmed expert sheet.

No model requests, re-scoring, source workbook edits or averaging of reviewers.
"""
import csv
import hashlib
import io
import json
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.colors import to_rgba
from matplotlib.path import Path as MPath
from matplotlib.patches import FancyBboxPatch, PathPatch
from PIL import Image
from pypdf import PdfReader

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE_COMMIT = 'c68baaf2a47b91c9713fc1c046f2bbfa45b217c8'
SOURCE_DIR = ROOT / 'research/2026-10-28_authoritative_expert_analysis'
SOURCE_CSV = SOURCE_DIR / 'scores_by_actual_group.csv'
WORKBOOK = SOURCE_DIR / 'source_workbook_user_corrected.xlsx'
GROUPS = ('agent', 'workflow', 'llm')
DIMS = ('factual_accuracy', 'evidence_support', 'requirement_completion', 'boundary_handling')
COLORS = {'agent': '#9256C5', 'workflow': '#62A76D', 'llm': '#4D80BD'}
GROUP_NAMES = {'agent': 'Agent', 'workflow': 'Fixed workflow', 'llm': 'LLM'}
DIM_NAMES = ('Factual accuracy', 'Evidence support', 'Requirement\ncompletion', 'Boundary handling')
Q_LABELS = [
    'Q1  Existing-reagent\ncalculation audit',
    'Q2  Sequence and\nreference check',
    'Q3  Existing scores\nand interpretation',
    'Q4  High scores vs.\nnear-match warnings',
    'Q5  Additional\nrequirements',
    'Q6  Unspecified\nstrand roles',
    'Q7  Modified sequence:\nreuse of prior scores',
    'Q8  Coordinate-sequence\nconsistency',
    'Q9  Missing current\nexpression table',
]
NAME = 'siRNA_GPT_expert_score_sankey_20261028'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_and_check():
    relative = SOURCE_CSV.relative_to(ROOT).as_posix()
    source_bytes = subprocess.check_output(['git', 'show', f'{SOURCE_COMMIT}:{relative}'], cwd=ROOT)
    assert source_bytes == SOURCE_CSV.read_bytes(), 'Source differs from verified remote commit'
    rows = list(csv.DictReader(io.StringIO(source_bytes.decode('utf-8-sig'))))
    assert len(rows) == 27
    keyed = {}
    ns = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    with zipfile.ZipFile(WORKBOOK) as z:
        sheet = ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
    cells = {c.attrib['r']: c for c in sheet.findall('.//m:c', ns)}
    for r in rows:
        q = int(r['question_number'])
        g = r['group']
        assert g in GROUPS and 1 <= q <= 9 and (g, q) not in keyed
        scores = [int(r[d]) for d in DIMS]
        assert all(s in (0, 1, 2) for s in scores)
        assert sum(scores) == int(r['total'])
        row_number = r['source_total_formula_cell'].split('!G')[1]
        for col, score in zip('CDEF', scores):
            assert int(cells[col + row_number].find('m:v', ns).text) == score
        total_cell = cells['G' + row_number]
        assert total_cell.find('m:f', ns) is not None
        assert int(total_cell.find('m:v', ns).text) == sum(scores)
        keyed[g, q] = dict(r, scores=scores, total=sum(scores))
    assert len(keyed) == 27
    totals = {g: sum(keyed[g, q]['total'] for q in range(1, 10)) for g in GROUPS}
    assert totals == {'agent': 70, 'workflow': 51, 'llm': 52}
    assert keyed['workflow', 9]['scores'] == keyed['agent', 9]['scores'] == [2, 2, 2, 2]
    return keyed, totals


def configure_fonts():
    result = {}
    for weight, name in [('normal', 'arial.ttf'), ('bold', 'arialbd.ttf')]:
        path = Path('C:/Windows/Fonts') / name
        assert path.is_file(), 'Actual Arial required; font substitution is prohibited'
        font_manager.fontManager.addfont(str(path))
        resolved = Path(font_manager.findfont(font_manager.FontProperties(family='Arial', weight=weight), fallback_to_default=False))
        assert resolved.resolve() == path.resolve()
        result[weight] = {'path': str(path), 'sha256': sha(path)}
    plt.rcParams.update({'font.family': 'Arial', 'font.weight': 'normal', 'font.size': 10,
                         'pdf.fonttype': 42, 'svg.fonttype': 'none', 'svg.hashsalt': NAME,
                         'figure.facecolor': 'white', 'savefig.facecolor': 'white'})
    return result


def build():
    keyed, totals = load_and_check()
    font_sources = configure_fonts()
    original_hashes = {str(p.relative_to(ROOT)): sha(p) for p in (SOURCE_CSV, WORKBOOK, SOURCE_DIR / 'source_workbook_original.xlsx')}
    out = HERE / 'figures'
    out.mkdir(parents=True, exist_ok=True)
    fig = plt.figure(figsize=(14, 9.4), dpi=120)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1400)
    ax.set_ylim(940, 0)
    ax.axis('off')
    def text(x, y, s, **kwargs):
        obj = ax.text(x, y, s, color='#17202A', va='center', ha='center', **kwargs)
        return obj

    # Main title and the template's lowercase panel label.
    ax.text(25, 28, 'a', ha='left', va='center', fontsize=17, fontweight='bold', color='#17202A')
    ax.text(60, 28, 'Expert score distribution across models, tasks and dimensions',
            ha='left', va='center', fontsize=16, fontweight='bold', color='#17202A')
    ax.text(25, 57, 'One expert | Nine seen development tasks | User-corrected scores',
            ha='left', va='center', fontsize=10, color='#5B6470')
    for x, title in [(130, 'Model configuration'), (685, 'Question'), (1240, 'Evaluation dimension')]:
        text(x, 94, title, fontsize=12, fontweight='bold')

    top, bottom = 125.0, 810.0
    total_score = sum(totals.values())
    scale = (bottom - top - 8 * 10) / total_score
    x_boxes = [(25, 235), (530, 840), (1100, 1380)]
    nodes = {}
    y = top
    for g in GROUPS:
        height = totals[g] * scale
        nodes[g] = (y, height)
        y += height + 40
    q_totals = {q: sum(keyed[g, q]['total'] for g in GROUPS) for q in range(1, 10)}
    y = top
    for q in range(1, 10):
        height = q_totals[q] * scale
        nodes['Q' + str(q)] = (y, height)
        y += height + 10
    d_totals = {d: sum(r['scores'][i] for r in keyed.values()) for i, d in enumerate(DIMS)}
    y = top
    for d in DIMS:
        height = d_totals[d] * scale
        nodes[d] = (y, height)
        y += height + 80 / 3
    assert all(top - 1e-8 <= y0 and y0 + h <= bottom + 1e-8 for y0, h in nodes.values())

    links = []
    # Separate offsets keep source identity and score mass through each task.
    left_source = {g: nodes[g][0] for g in GROUPS}
    left_task = {q: nodes['Q' + str(q)][0] for q in range(1, 10)}
    right_task = {q: nodes['Q' + str(q)][0] for q in range(1, 10)}
    right_dim = {d: nodes[d][0] for d in DIMS}

    def ribbon(x0, y0, x1, y1, value, group, source, target, answer_id, dimension=''):
        width = value * scale
        link = dict(source=source, target=target, model=group, answer_id=answer_id,
                    dimension=dimension, score=value, width_plot_units=width,
                    source_y=y0, target_y=y1, drawn=value > 0)
        links.append(link)
        if not value:
            return
        dx = (x1 - x0) * .46
        verts = [(x0, y0), (x0 + dx, y0), (x1 - dx, y1), (x1, y1),
                 (x1, y1 + width), (x1 - dx, y1 + width), (x0 + dx, y0 + width),
                 (x0, y0 + width), (x0, y0)]
        codes = [MPath.MOVETO, MPath.CURVE4, MPath.CURVE4, MPath.CURVE4,
                 MPath.LINETO, MPath.CURVE4, MPath.CURVE4, MPath.CURVE4, MPath.CLOSEPOLY]
        patch = PathPatch(MPath(verts, codes), facecolor=COLORS[group], alpha=.28,
                          edgecolor='none', linewidth=0, zorder=1)
        patch.set_gid(f'{source}-{target}-{group}-{answer_id}-{value}')
        ax.add_patch(patch)

    for g in GROUPS:
        for q in range(1, 10):
            r = keyed[g, q]
            ribbon(235, left_source[g], 530, left_task[q], r['total'], g, g, f'Q{q}', r['answer_id'])
            left_source[g] += r['total'] * scale
            left_task[q] += r['total'] * scale
    # Sort task exits by model then dimension, destination entries by model then
    # task. Models therefore retain continuous colored blocks at each endpoint.
    for g in GROUPS:
        for q in range(1, 10):
            r = keyed[g, q]
            for i, d in enumerate(DIMS):
                value = r['scores'][i]
                ribbon(840, right_task[q], 1100, right_dim[d], value, g, f'Q{q}', d, r['answer_id'], d)
                right_task[q] += value * scale
                right_dim[d] += value * scale

    node_texts = []

    def box(col, key, label, border, fontsize=11.2, emphasis=False):
        x0, x1 = x_boxes[col]
        y0, h = nodes[key]
        patch = FancyBboxPatch((x0, y0), x1 - x0, h, boxstyle='round,pad=0,rounding_size=9',
                               facecolor=to_rgba(border, .045), edgecolor=border, linewidth=1.05, zorder=3)
        # Opaque paper under the very pale node tint prevents ribbon bleed.
        underlay = FancyBboxPatch((x0, y0), x1 - x0, h, boxstyle='round,pad=0,rounding_size=9',
                                  facecolor='white', edgecolor='none', zorder=2)
        ax.add_patch(underlay)
        ax.add_patch(patch)
        label_text = text((x0 + x1) / 2, y0 + h / 2, label, fontsize=fontsize,
                          fontweight='bold' if emphasis else 'normal', linespacing=1.3, zorder=4)
        node_texts.append((key, label_text, (x0, y0, x1, y0 + h)))

    for g in GROUPS:
        box(0, g, GROUP_NAMES[g] + f'\n{totals[g]} / 72 points', COLORS[g], fontsize=12, emphasis=True)
    for q in range(1, 10):
        border = '#74A47B' if q <= 4 else '#D3A243' if q == 5 else '#8B9CAD'
        box(1, f'Q{q}', Q_LABELS[q - 1], border, fontsize=10.7)
    for d, label, border in zip(DIMS, DIM_NAMES, ['#6BA878', '#D5A147', '#CD9461', '#7898B5']):
        box(2, d, label + f'\n{d_totals[d]} / 54 points', border, fontsize=11.3, emphasis=True)

    ax.text(25, 847, 'Ribbon width = awarded score points. Model to question: four-dimension total (0-8); question to dimension: item score (0-2).',
            fontsize=9, color='#434C57', ha='left', va='center')
    ax.text(25, 870, 'Color retains model identity across all three columns. Zero-score links have zero width and are omitted; all scores remain in the data.',
            fontsize=9, color='#434C57', ha='left', va='center')
    ax.text(25, 900, 'Q1-Q4: standard tasks | Q5: requirement change | Q6-Q9: reliability | Source: user-confirmed expert sheet, GitHub c68baaf',
            fontsize=8.5, color='#66717D', ha='left', va='center')

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    for key, obj, bounds in node_texts:
        bb = obj.get_window_extent(renderer).transformed(ax.transData.inverted())
        xs, ys = sorted((bb.x0, bb.x1)), sorted((bb.y0, bb.y1))
        x0, y0, x1, y1 = bounds
        assert xs[0] > x0 + 5 and xs[1] < x1 - 5 and ys[0] > y0 + 3 and ys[1] < y1 - 3, (key, xs, ys, bounds)
    for obj in fig.findobj(matplotlib.text.Text):
        if obj.get_text():
            font = Path(font_manager.findfont(obj.get_fontproperties(), fallback_to_default=False)).name.lower()
            assert font in ('arial.ttf', 'arialbd.ttf'), font
            bb = obj.get_window_extent(renderer)
            assert bb.x0 >= 0 and bb.y0 >= 0 and bb.x1 <= fig.bbox.width and bb.y1 <= fig.bbox.height

    for ext in ('svg', 'pdf', 'png'):
        metadata = {'Creator': 'siRNA-GPT expert score Sankey'}
        if ext == 'svg':
            metadata['Date'] = None
        elif ext == 'pdf':
            metadata.update(CreationDate=None, ModDate=None)
        fig.savefig(out / f'{NAME}.{ext}', dpi=600, metadata=metadata)
    fig.savefig(HERE / 'preview.png', dpi=160)
    plt.close(fig)

    # Independently reconcile all score mass, including zero-valued links.
    incoming, outgoing = defaultdict(int), defaultdict(int)
    model_dimension = defaultdict(int)
    for link in links:
        outgoing[link['source']] += link['score']
        incoming[link['target']] += link['score']
        assert abs(link['width_plot_units'] - link['score'] * scale) < 1e-10
        if link['dimension']:
            model_dimension[link['model'], link['dimension']] += link['score']
    assert len(links) == 135 and sum(l['score'] for l in links if not l['dimension']) == total_score == 173
    assert sum(l['score'] for l in links if l['dimension']) == total_score
    assert all(incoming[f'Q{q}'] == outgoing[f'Q{q}'] == q_totals[q] for q in range(1, 10))
    assert all(outgoing[g] == totals[g] for g in GROUPS)
    assert all(incoming[d] == d_totals[d] for d in DIMS)
    for g in GROUPS:
        assert sum(model_dimension[g, d] for d in DIMS) == totals[g]
    with (HERE / 'sankey_links.csv').open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(links[0]))
        writer.writeheader()
        writer.writerows(links)

    pdf = PdfReader(out / f'{NAME}.pdf')
    assert len(pdf.pages) == 1
    embedded_fonts = []
    for value in pdf.pages[0]['/Resources']['/Font'].get_object().values():
        font = value.get_object()
        name = str(font.get('/BaseFont', ''))
        core = font['/DescendantFonts'][0].get_object() if font.get('/DescendantFonts') else font
        descriptor = core['/FontDescriptor'].get_object()
        assert 'Arial' in name and descriptor.get('/FontFile2'), name
        embedded_fonts.append(name)
    assert any('Bold' in name for name in embedded_fonts) and any('Bold' not in name for name in embedded_fonts)
    svg_text = (out / f'{NAME}.svg').read_text('utf-8')
    ET.fromstring(svg_text)
    assert '<image' not in svg_text and 'Arial' in svg_text
    assert not any(s in svg_text for s in ('DejaVu', 'Arimo', 'Liberation'))
    with Image.open(out / f'{NAME}.png') as im:
        assert all(abs(x - 600) < 1 for x in im.info['dpi'])
        png_pixels = im.size
    assert original_hashes == {str(p.relative_to(ROOT)): sha(p) for p in (SOURCE_CSV, WORKBOOK, SOURCE_DIR / 'source_workbook_original.xlsx')}
    checks = dict(status='PASS', source_commit=SOURCE_COMMIT, source_csv=str(SOURCE_CSV.relative_to(ROOT)),
                  source_sha256=original_hashes, original_sources_unchanged=True,
                  workbook_cells_checked=108, cached_totals_checked=27, n_models=3, n_questions=9, n_dimensions=4,
                  model_totals=totals, question_totals=q_totals, dimension_totals=d_totals, score_points=total_score,
                  flow_conservation_at_all_nine_questions=True, common_linear_width_scale=scale,
                  links=len(links), nonzero_links=sum(l['drawn'] for l in links),
                  zero_links_omitted=sum(not l['drawn'] for l in links), zero_scores_retained_in_data=True,
                  model_identity_preserved=True, embedded_pdf_fonts=embedded_fonts, pdf_pages=1,
                  png_dpi=600, png_pixels=png_pixels, svg_fully_vector=True, node_label_bounds='PASS',
                  new_quality_scores=0, new_model_requests=0, fonts=font_sources,
                  artifact_sha256={p.name: sha(p) for p in out.iterdir() if p.is_file()})
    (HERE / 'validation.json').write_text(json.dumps(checks, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(checks, indent=2))


if __name__ == '__main__':
    build()
