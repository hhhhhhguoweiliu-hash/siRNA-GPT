"""Static scientist-facing reading pages; original Markdown/raw answers stay."""
import html
import json
import re
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'research/2026-10-27_evaluation_entry'


def main():
    folder=BASE/'expert_topic_review'
    for source in folder.rglob('*.md'):
        if 'reference_for_judgement' in source.parts:continue
        text=source.read_text(encoding='utf-8')
        def inline(line):
            result='';position=0
            for m in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)',line):
                result+=html.escape(line[position:m.start()]);target=m[2]
                if target.endswith('.md') and (source.parent/target).is_file() and 'reference_for_judgement' not in (source.parent/target).parts:
                    target=target[:-3]+'.html'
                result+='<a href="'+html.escape(target,quote=True)+'">'+html.escape(m[1])+'</a>';position=m.end()
            return result+html.escape(line[position:])
        blocks=[];code=False;table=False
        for line in text.splitlines():
            if line.startswith('```'):
                if table:blocks.append('</table>');table=False
                blocks.append('</pre>' if code else '<pre>');code=not code;continue
            if code:blocks.append(html.escape(line)+'\n');continue
            if line.startswith('|'):
                if not table:blocks.append('<table>');table=True
                cells=line.strip('|').split('|')
                if all(re.fullmatch(r'[\s:-]+',c) for c in cells):continue
                blocks.append('<tr>'+''.join('<td>'+inline(c.strip())+'</td>' for c in cells)+'</tr>');continue
            if table:blocks.append('</table>');table=False
            if line.startswith('#'):
                level=min(4,len(line)-len(line.lstrip('#')));blocks.append('<h'+str(level)+'>'+inline(line.lstrip('#').strip())+'</h'+str(level)+'>')
            elif line.strip():blocks.append('<p>'+inline(line)+'</p>')
        if table:blocks.append('</table>')
        body='<!doctype html><html lang="zh"><meta charset="utf-8"><title>siRNA-GPT审题材料</title><style>body{font:16px/1.75 Arial,"Microsoft YaHei",sans-serif;max-width:1100px;margin:28px auto;padding:0 24px;color:#203444}a{color:#075a86}td{border:1px solid #c4cfd7;padding:10px;vertical-align:top}table{border-collapse:collapse;width:100%}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f2f5f7;padding:15px}h1,h2,h3{line-height:1.35}</style>'+''.join(blocks)+'</html>'
        source.with_suffix('.html').write_text(body,encoding='utf-8')
    index=folder/'index.html';text=index.read_text(encoding='utf-8')
    text=re.sub(r'href="([^"]+)\.md"',lambda m:'href="'+m[1]+'.html"',text)
    index.write_text(text,encoding='utf-8')
    links=[]
    for file in folder.rglob('*.html'):
        if 'reference_for_judgement' in file.parts:continue
        for target in re.findall(r'href="([^"]+)"',file.read_text(encoding='utf-8')):
            if '://' in target or target.startswith('#'):continue
            decoded=html.unescape(target).split('#')[0]
            assert (file.parent/decoded).exists(),(file,target)
            links.append({'from':file.relative_to(folder).as_posix(),'target':decoded})
    (BASE/'expert_html_navigation_checks.json').write_text(json.dumps({'kind':'STATIC_LINK_CHECK_NOT_BROWSER_ACCEPTANCE',
        'checked_links':links,'native_browser_acceptance':False,'model_calls':0},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with zipfile.ZipFile(BASE/'expert_topic_review.zip','w',zipfile.ZIP_DEFLATED) as z:
        for file in sorted(folder.rglob('*')):
            if file.is_file():z.write(file,file.relative_to(folder))
    print('PASS: readable HTML project/task/practice pages and static evidence links; source answers unchanged; no browser or model acceptance claimed.')


if __name__=='__main__':main()
