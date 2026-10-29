"""Exact illustrative metric diagram. The counts are not project results."""
from pathlib import Path
import argparse,json,hashlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,Ellipse
from matplotlib import font_manager,text as mt
from PIL import Image

HERE=Path(__file__).resolve().parent
COLORS={'TP':'#90D9CA','TN':'#99C4CE','FP':'#AB88B3','FN':'#DDCDE2'}
INK='#22262B';EDGE='#48505A'
def main(font):
    font=font.resolve();font_manager.fontManager.addfont(str(font))
    fp=font_manager.FontProperties(family='Arial',weight='bold',fname=str(font))
    assert fp.get_name()=='Arial'
    plt.rcParams.update({'svg.fonttype':'none','font.family':'Arial','font.weight':'bold'})
    fig=plt.figure(figsize=(13.2,9.5),facecolor='white')
    fig.text(.055,.963,'How accuracy, precision, recall and F1 are calculated',fontsize=23,va='top',color=INK)
    fig.text(.055,.914,'Illustrative example: TP = 8, TN = 5, FP = 2, FN = 5; N = 20; no missing answers.',fontsize=13,color=EDGE)
    panels=[
      ('a','Accuracy','Correct judgments / All judgments','(TP + TN) / (TP + TN + FP + FN)',[('TP',8),('TN',5),('FP',2),('FN',5)],13,20,'(8 + 5) / 20 = 65.0%'),
      ('b','Precision','Correct positives / Predicted positives','TP / (TP + FP)',[('TP',8),('FP',2)],8,10,'8 / (8 + 2) = 80.0%'),
      ('c','Recall','Found positives / All actual positives','TP / (TP + FN)',[('TP',8),('FN',5)],8,13,'8 / (8 + 5) = 61.5%'),
      ('d','F1 score','Harmonic mean of precision and recall','2TP / (2TP + FP + FN)',[('TP',16),('FP',2),('FN',5)],16,23,'16 / (16 + 2 + 5) = 69.6%'),
    ]
    for i,(letter,title,meaning,formula,groups,num,den,result) in enumerate(panels):
        x=.05+(i%2)*.48;y=.525-(i//2)*.365
        ax=fig.add_axes([x,y,.445,.325]);ax.set_xlim(0,10);ax.set_ylim(0,7.4);ax.axis('off')
        ax.add_patch(FancyBboxPatch((.04,.05),9.92,7.25,boxstyle='round,pad=0.02,rounding_size=.22',facecolor='#FAFBFC',edgecolor='#DDE2E7',lw=1.1))
        ax.text(.35,6.67,letter,fontsize=20,ha='left',va='center',color=INK)
        ax.text(1.05,6.67,title,fontsize=20,ha='left',va='center',color=INK)
        ax.text(.40,5.82,meaning,fontsize=12.5,color=EDGE)
        ax.text(.40,5.02,formula,fontsize=14,color=INK)
        # Each circle is one denominator unit. For F1, each TP is counted twice.
        cats=[cat for cat,n in groups for _ in range(n)]
        for j,cat in enumerate(cats):
            cx=.65+(j%10)*.90;cy=3.92-(j//10)*.68
            ax.add_patch(Ellipse((cx,cy),.46,.65,facecolor=COLORS[cat],edgecolor=EDGE,lw=.65))
        note='F1 = 2PR / (P + R); each TP is weighted twice.' if title=='F1 score' else f'Each circle = 1 of {den} denominator units.'
        ax.text(.40,1.70,note,fontsize=10.5,color=EDGE)
        ax.text(.40,.64,result,fontsize=19,color=INK,va='center')
    legend=[('TP','Actual positive, correctly identified'),('TN','Actual negative, correctly rejected'),
            ('FP','Actual negative, incorrectly called positive'),('FN','Actual positive, missed')]
    for i,(cat,desc) in enumerate(legend):
        x=.058+(i%2)*.48;y=.137-(i//2)*.039
        fig.patches.append(Ellipse((x,y+.003),.012,.012*13.2/9.5,transform=fig.transFigure,facecolor=COLORS[cat],edgecolor=EDGE,lw=.65))
        fig.text(x+.014,y,cat+'  '+desc,fontsize=11.5,va='center',color=INK)
    fig.text(.055,.045,'Project rule: missing / incomplete responses stay in N and are never TN; positive missing also enters FN.',fontsize=11,color=EDGE)
    for t in fig.findobj(match=mt.Text):
        size=t.get_fontsize();t.set_fontproperties(fp);t.set_fontsize(size)
    fig.canvas.draw();w,h=fig.canvas.get_width_height();renderer=fig.canvas.get_renderer()
    for t in fig.findobj(match=mt.Text):
        if not t.get_visible() or not t.get_text():continue
        b=t.get_window_extent(renderer);assert b.x0>=0 and b.y0>=0 and b.x1<=w and b.y1<=h,(t.get_text(),b.bounds)
        assert Path(font_manager.findfont(t.get_fontproperties(),fallback_to_default=False)).resolve()==font
    for ext in ['png','svg']:fig.savefig(HERE/f'four_metric_calculation_schematic.{ext}',dpi=600)
    with Image.open(HERE/'four_metric_calculation_schematic.png') as im:im.load()
    svg=(HERE/'four_metric_calculation_schematic.svg').read_text();assert 'DejaVu' not in svg and '<image' not in svg and '<text' in svg
    (HERE/'README.md').write_text('''# Four-metric calculation schematic

![Four-metric calculation schematic](four_metric_calculation_schematic.png)

Illustrative example only, **not project performance data**: TP=8, TN=5, FP=2,
FN=5, N=20, no abstentions. Accuracy=65.0%, precision=80.0%, recall=61.5%,
F1=69.6%. F1 circle counts use 2TP+FP+FN=23 weighted units; these are not 23 cases.

For the actual project data, missing/incomplete responses remain in the total
accuracy denominator and are never TN; positive abstentions also enter FN.
See [the full protocol](../PROTOCOL.md) for the 2x3 confusion table and formulas.

Verified Arial Bold; paper-derived colors; 600 dpi PNG and editable SVG.
Reproduce: `python draw_metric_schematic.py --font /path/to/Arial-Bold.ttf`.
''')
    print(json.dumps({'saved':str(HERE),'font':'Arial Bold','example_not_project_data':True,'checks':'passed'}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--font',type=Path,required=True);main(p.parse_args().font)
