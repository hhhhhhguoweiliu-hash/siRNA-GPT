"""Compatibility entrypoint: use corrected exports; preserve old SVG/CSV files."""
import runpy,sys
from pathlib import Path
target=Path(__file__).resolve().parents[2]/'2026-10-28_adjudication_figures_v2'/'build_figures.py'
sys.path.insert(0,str(target.parent))
sys.argv=[str(target)]+sys.argv[1:]
if __name__=='__main__':runpy.run_path(str(target),run_name='__main__')
