#!/usr/bin/env python3
"""Build a seven-page PDF from the seven generated PNG figures."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.backends.backend_pdf import PdfPages

HERE = Path(__file__).resolve().parent
OUT = HERE / "dist"
OUT.mkdir(exist_ok=True)
FIGURES = [
    "Figure3_score_sheet_A_dimension_means.png",
    "Figure3_score_sheet_C_dimension_means.png",
    "Figure4_task_dimension_heatmap_score_sheet_A.png",
    "FigureS1_task_dimension_heatmap_score_sheet_C.png",
    "FigureS2_changed_case_verdicts.png",
    "FigureM1_accuracy.png",
    "FigureM2_precision_recall_f1.png",
]
missing = [name for name in FIGURES if not (HERE / name).is_file()]
if missing:
    raise FileNotFoundError(f"Missing expected PNGs: {missing}")
with PdfPages(OUT / "siRNA-GPT_final_adjudication_figures.pdf") as pdf:
    for name in FIGURES:
        image = mpimg.imread(HERE / name)
        h, w = image.shape[:2]
        max_w, max_h = 10.5, 10.5
        scale = min(max_w / (w / 300), max_h / (h / 300))
        fig = plt.figure(figsize=(w / 300 * scale, h / 300 * scale), dpi=300)
        ax = fig.add_axes([0, 0, 1, 1])
        ax.imshow(image)
        ax.axis("off")
        pdf.savefig(fig, bbox_inches="tight", pad_inches=0.05)
        plt.close(fig)
print(f"Created {OUT / 'siRNA-GPT_final_adjudication_figures.pdf'} with {len(FIGURES)} pages.")
