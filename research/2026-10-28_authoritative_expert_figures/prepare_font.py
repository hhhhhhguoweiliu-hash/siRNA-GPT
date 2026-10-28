"""Reuse actual embedded Arial Bold glyphs from an existing project PDF."""
import argparse
import hashlib
import io
import json
import re
from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._c_m_a_p import CmapSubtable
from pypdf import PdfReader


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--source-pdf',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    for page in PdfReader(args.source_pdf).pages:
        for ref in page['/Resources']['/Font'].values():
            obj=ref.get_object()
            if 'Arial-BoldMT' not in str(obj.get('/BaseFont')):
                continue
            actual=obj['/DescendantFonts'][0].get_object() if '/DescendantFonts' in obj else obj
            desc=actual['/FontDescriptor'].get_object()
            if '/FontFile2' not in desc:continue
            font=TTFont(io.BytesIO(desc['/FontFile2'].get_object().get_data()))
            cmap=font.getBestCmap()
            if not cmap:
                encoded=next(t.cmap for t in font['cmap'].tables if t.cmap)
                text=obj['/ToUnicode'].get_object().get_data().decode('ascii')
                pairs=re.findall(r'<([0-9A-Fa-f]{2})>\s*<([0-9A-Fa-f]{4})>',text)
                cmap={int(u,16):encoded[int(code,16)] for code,u in pairs if int(u,16) and int(code,16) in encoded}
                for platform,encoding in [(0,3),(3,1)]:
                    table=CmapSubtable.newSubtable(4)
                    table.platformID=platform;table.platEncID=encoding;table.language=0;table.cmap=cmap
                    font['cmap'].tables.append(table)
            assert all(c in cmap for c in range(32,127)), 'ASCII glyph coverage is incomplete'
            names={i:next((n.toUnicode() for n in font['name'].names if n.nameID==i and n.platformID==3 and n.langID==0x409),
                          next(n.toUnicode() for n in font['name'].names if n.nameID==i)) for i in (1,2,6)}
            assert names[1]=='Arial' and names[2]=='Bold' and names[6]=='Arial-BoldMT',names
            args.output.parent.mkdir(parents=True,exist_ok=True)
            font.save(args.output)
            print(json.dumps({'font':names,'source_pdf_sha256':hashlib.sha256(args.source_pdf.read_bytes()).hexdigest(),
                              'ascii_coverage':'32-126 complete','outline_changes':False,
                              'note':'Only Unicode character mappings restored where absent. Actual Arial Bold outlines retained.'}))
            return
    raise RuntimeError('No usable Arial Bold font in source PDF')


if __name__=='__main__':main()
