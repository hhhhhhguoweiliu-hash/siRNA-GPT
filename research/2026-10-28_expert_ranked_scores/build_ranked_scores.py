"""Rank all nine existing question totals within each configuration; no re-scoring."""
import csv
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'research/2026-10-28_expert_score_sankey'))
from build_sankey import load_and_check, configure_fonts, SOURCE_COMMIT, SOURCE_CSV, WORKBOOK
import matplotlib.pyplot as plt
from matplotlib import colors, font_manager
from matplotlib.lines import Line2D
from PIL import Image
from pypdf import PdfReader

NAME = 'siRNA_GPT_ranked_expert_scores_20261028'
GROUPS = ('agent', 'workflow', 'llm')
LABELS = {'agent': 'Agent', 'workflow': 'Fixed workflow', 'llm': 'LLM'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    keyed, totals = load_and_check()
    fonts = configure_fonts()
    before = {str(p.relative_to(ROOT)): sha(p) for p in (SOURCE_CSV, WORKBOOK)}
    out = HERE / 'figures'
    out.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(12, 6.7))
    fig.subplots_adjust(left=.075, right=.88, bottom=.26, top=.78)
    cmap = plt.get_cmap('RdYlBu')
    norm = colors.Normalize(vmin=0, vmax=8)
    pooled_mean = sum(totals.values()) / 27
    xs, qlabels, sorted_rows, bar_checks = [], [], [], []
    for i, g in enumerate(GROUPS):
        ranked = sorted((keyed[g, q] for q in range(1, 10)), key=lambda r: (-r['total'], int(r['question_number'])))
        values = [r['total'] for r in ranked]
        assert values == sorted(values, reverse=True) and len(values) == 9
        assert sum(values) == totals[g]
        positions = [i * 11.8 + j for j in range(9)]
        bars = ax.bar(positions, values, width=.67, color=[cmap(norm(v)) for v in values], edgecolor='none', zorder=3)
        for rank, (x, r, bar) in enumerate(zip(positions, ranked, bars), start=1):
            assert bar.get_height() == r['total']
            ax.text(x, r['total'] + .13, str(r['total']), ha='center', va='bottom', fontsize=9)
            xs.append(x)
            qlabels.append('Q' + r['question_number'])
            sorted_rows.append(dict(group=g, rank_within_group=rank, question_number=r['question_number'],
                                    case_id=r['case_id'], answer_id=r['answer_id'],
                                    factual_accuracy=r['scores'][0], evidence_support=r['scores'][1],
                                    requirement_completion=r['scores'][2], boundary_handling=r['scores'][3],
                                    total=r['total'], source_cells=r['source_cells']))
            bar_checks.append(dict(group=g, question=int(r['question_number']), value=int(bar.get_height())))
        center = (positions[0] + positions[-1]) / 2
        ax.text(center, -.19, LABELS[g], transform=ax.get_xaxis_transform(), ha='center', va='center', fontsize=13, fontweight='bold')
        ax.text(center, -.29, f'n = 9; mean = {totals[g] / 9:.2f} / 8', transform=ax.get_xaxis_transform(),
                ha='center', va='center', fontsize=10, color='#59636F')
    ax.axhline(pooled_mean, color='#747C85', linewidth=1, linestyle=(0, (3, 3)), zorder=2)
    ax.set_xticks(xs)
    ax.set_xticklabels(qlabels, fontsize=8.5)
    ax.set_xlim(-.8, 32.4)
    ax.set_ylim(0, 8.9)
    ax.set_yticks([0, 2, 4, 6, 8])
    ax.set_ylabel('Expert total score (0-8)', fontsize=12, labelpad=12)
    ax.tick_params(axis='x', length=0, pad=9)
    ax.tick_params(axis='y', labelsize=10)
    ax.spines[['right', 'top']].set_visible(False)
    ax.spines[['left', 'bottom']].set_color('#626B75')
    ax.grid(axis='y', color='#E6E9ED', linewidth=.6, zorder=0)
    ax.set_axisbelow(True)
    fig.text(.026, .955, 'b', fontsize=16, fontweight='bold', va='center')
    fig.text(.075, .955, 'Expert scores ranked within each model', fontsize=17, fontweight='bold', va='center')
    fig.text(.075, .9, 'Nine seen tasks per configuration | One expert | User-corrected Q9 scores', fontsize=10, color='#59636F')
    fig.legend([Line2D([0], [0], color='#747C85', linewidth=1, linestyle=(0, (3, 3)))],
               [f'Overall mean: {pooled_mean:.2f} / 8 (descriptive reference)'],
               loc='upper left', bbox_to_anchor=(.068, .87), frameon=False, fontsize=9.5)
    cax = fig.add_axes([.915, .26, .014, .52])
    scalar = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
    colorbar = fig.colorbar(scalar, cax=cax, ticks=[0, 2, 4, 6, 8])
    colorbar.solids.set_rasterized(False)
    colorbar.solids.set_edgecolor('face')
    colorbar.outline.set_visible(False)
    colorbar.ax.tick_params(length=0, labelsize=9, pad=7)
    colorbar.ax.set_title('Score', fontsize=10, pad=12)
    fig.text(.075, .075, 'Bars show all nine original question totals per model, sorted independently; question IDs retain the pairing.',
             fontsize=8.5, color='#59636F')
    fig.text(.075, .035, 'Color continuously encodes the original score; no high/low-quality or noise thresholds are inferred. Source: GitHub c68baaf.',
             fontsize=8.5, color='#59636F')
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    for obj in fig.findobj(plt.Text):
        if obj.get_text():
            resolved = Path(font_manager.findfont(obj.get_fontproperties(), fallback_to_default=False)).name.lower()
            assert resolved in ('arial.ttf', 'arialbd.ttf')
            if obj.get_visible():
                bb = obj.get_window_extent(renderer)
                assert bb.x0 >= 0 and bb.y0 >= 0 and bb.x1 <= fig.bbox.width and bb.y1 <= fig.bbox.height, obj.get_text()
    for ext in ('png', 'svg', 'pdf'):
        metadata = {'Creator': 'siRNA-GPT ranked expert scores'}
        if ext == 'svg':
            metadata['Date'] = None
        elif ext == 'pdf':
            metadata.update(CreationDate=None, ModDate=None)
        fig.savefig(out / f'{NAME}.{ext}', dpi=600, metadata=metadata)
    fig.savefig(HERE / 'preview.png', dpi=160)
    plt.close(fig)
    with (HERE / 'ranked_plot_data.csv').open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(sorted_rows[0]))
        writer.writeheader()
        writer.writerows(sorted_rows)
    assert {(r['group'], r['question_number']) for r in sorted_rows} == {(g, str(q)) for g in GROUPS for q in range(1, 10)}
    assert before == {str(p.relative_to(ROOT)): sha(p) for p in (SOURCE_CSV, WORKBOOK)}
    reader = PdfReader(out / f'{NAME}.pdf')
    assert len(reader.pages) == 1
    embedded = []
    for ref in reader.pages[0]['/Resources']['/Font'].get_object().values():
        font = ref.get_object()
        name = str(font['/BaseFont'])
        core = font['/DescendantFonts'][0].get_object() if font.get('/DescendantFonts') else font
        assert 'Arial' in name and core['/FontDescriptor'].get_object().get('/FontFile2')
        embedded.append(name)
    svg = (out / f'{NAME}.svg').read_text('utf-8')
    ET.fromstring(svg)
    assert '<image' not in svg and 'Arial' in svg
    with Image.open(out / f'{NAME}.png') as im:
        assert all(abs(v - 600) < 1 for v in im.info['dpi'])
        pixels = im.size
    result = dict(status='PASS', source_commit=SOURCE_COMMIT, source_hashes=before, original_scores_unchanged=True,
                  groups=3, questions_per_group=9, total_bars=27, all_questions_included_once_per_group=True,
                  independent_descending_sort=True, tie_break='original question number',
                  group_totals=totals, overall_mean=pooled_mean, mean_line_is_not_a_quality_threshold=True,
                  score_range=[0, 8], continuous_color_scale=True, quality_categories_inferred=False,
                  embedded_pdf_fonts=embedded, pdf_pages=1, png_dpi=600, png_pixels=pixels,
                  svg_fully_vector=True, font_sources=fonts, new_model_calls=0, new_quality_scores=0,
                  bar_values=bar_checks, artifacts={p.name: sha(p) for p in out.iterdir() if p.is_file()})
    (HERE / 'validation.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k not in ('bar_values', 'font_sources')}, indent=2))


if __name__ == '__main__':
    main()
