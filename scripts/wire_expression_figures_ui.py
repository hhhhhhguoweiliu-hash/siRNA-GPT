"""One-time bounded source edit; retained for transparent UI wiring."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=root/'index.html';s=p.read_text(encoding='utf-8')
changes=[
 ('compile_report:\'Compile candidate report\',','compile_report:\'Compile candidate report\',render_expression_figures:\'Render expression background in R\','),
 ('<option value="seed">Check seed matches and annotate expression</option>',
  '<option value="seed">Check seed matches and annotate expression</option><option value="figures">Plot candidate expression background (R)</option><option value="full_figures">Complete review with expression figures (R)</option>'),
 ('<div class="chips"><button class="chip"',
  '<div class="chips"><button class="chip" data-prompt="Use R to plot expression background for the currently selected siRNA candidates: expressed-match counts, Venn overlap and matched-gene TPM heatmap. Export the PDF and source tables.">Plot candidate expression background</button><button class="chip"'),
 ("$('links').append(link('Download tools and execution records'",
  "if(r.expression_figures?.status==='COMPLETE')$('links').append(link('View expression figures','/runs/'+id+'/'+r.expression_figures.report),link('Download expression PDF','/runs/'+id+'/'+r.expression_figures.pdf));$('links').append(link('Download tools and execution records'")]
for before,after in changes:
    if before not in s:raise ValueError('UI anchor missing: '+before)
    s=s.replace(before,after,1)
p.write_text(s,encoding='utf-8')
