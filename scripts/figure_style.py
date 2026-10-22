"""English manuscript typography. Fail visibly rather than silently replace Arial."""
import hashlib, re
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.text import Text
from matplotlib.patches import FancyArrowPatch
from matplotlib.ft2font import FT2Font

def configure():
    for name in ('arial.ttf','arialbd.ttf','ariali.ttf','arialbi.ttf'):
        path=Path('C:/Windows/Fonts')/name
        if path.is_file():font_manager.fontManager.addfont(str(path))
    records={}
    for weight in ('normal','bold'):
        path=Path(font_manager.findfont(font_manager.FontProperties(family='Arial',weight=weight),fallback_to_default=False))
        records[weight]={'name':'Arial','path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    plt.rcParams.update({'font.family':'Arial','font.sans-serif':['Arial'],'font.size':10,
        'axes.titleweight':'bold','axes.labelweight':'normal','pdf.fonttype':42,'svg.fonttype':'none',
        'axes.spines.top':False,'axes.spines.right':False,'axes.unicode_minus':False})
    return records

def prepare(fig):
    """Scale an existing panel layout to a 183 mm canvas; retain source data unchanged."""
    factor=(183/25.4)/fig.get_figwidth()
    old_height=fig.get_figheight();fig.set_size_inches(183/25.4,old_height*factor)
    texts=[]
    text_objects=list(fig.findobj(Text))
    for ax in fig.axes:
        for table in ax.tables:
            text_objects.extend(cell.get_text() for cell in table.get_celld().values())
    for text in dict.fromkeys(text_objects):
        value=text.get_text().replace('₂','2').replace('–','-').replace('—','-').replace('‑','-')
        if not value:continue
        text.set_text(value)
        if re.search(r'[\u3400-\u9fff]',value):raise ValueError('Non-English manuscript figure text: '+value[:60])
        text.set_fontfamily('Arial')
        if text.get_gid()=='panel_label':text.set_fontsize(8);text.set_fontweight('bold')
        else:text.set_fontsize(max(5,min(7,text.get_fontsize()*factor)))
        prop=text.get_fontproperties();actual=font_manager.findfont(prop,fallback_to_default=False)
        if font_manager.FontProperties(fname=actual).get_name()!='Arial':raise ValueError('Arial was replaced')
        face=FT2Font(actual)
        missing={character for character in value if not character.isspace() and not face.get_char_index(ord(character))}
        if missing:raise ValueError('Arial glyphs unavailable: '+repr(missing)+' in '+value[:80])
        texts.append({'text':value,'size_pt':text.get_fontsize(),'weight':text.get_fontweight(),'font_file':Path(actual).name})
    for ax in fig.axes:
        # Auto locators may create ticks during savefig after canvas resizing.
        # Set the tick template as well as existing Text objects.
        ax.tick_params(axis='both',which='both',labelsize=6)
        for line in ax.lines:
            line.set_linewidth(max(.4,line.get_linewidth()*factor))
            line.set_markersize(line.get_markersize()*factor)
        for collection in ax.collections:
            if hasattr(collection,'get_sizes') and hasattr(collection,'set_sizes'):
                collection.set_sizes(collection.get_sizes()*factor**2)
        for patch in ax.patches:
            if isinstance(patch,FancyArrowPatch):patch.set_mutation_scale(patch.get_mutation_scale()*factor)
    fig.canvas.draw()
    final_texts=list(fig.findobj(Text))
    for ax in fig.axes:
        for table in ax.tables:final_texts.extend(cell.get_text() for cell in table.get_celld().values())
    texts=[]
    for text in dict.fromkeys(final_texts):
        if not text.get_text():continue
        prop=text.get_fontproperties();actual=font_manager.findfont(prop,fallback_to_default=False)
        assert font_manager.FontProperties(fname=actual).get_name()=='Arial'
        assert 5<=text.get_fontsize()<=8,(text.get_text(),text.get_fontsize())
        texts.append({'text':text.get_text(),'size_pt':text.get_fontsize(),'weight':text.get_fontweight(),'font_file':Path(actual).name})
    return {'canvas_width_mm':183,'ordinary_text_pt':'5–7','panel_label_pt':8,
        'font_family':'Arial','text_count':len(texts),'text_elements':texts}
