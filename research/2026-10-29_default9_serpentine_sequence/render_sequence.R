# One-page full-sequence serpentine diagram, authored entirely with native R geoms.
args<-commandArgs(trailingOnly=TRUE);out<-args[1]
suppressPackageStartupMessages({library(ggplot2);library(data.table);library(jsonlite);library(systemfonts);library(ragg);library(svglite);library(grid)})
stopifnot(tolower(basename(systemfonts::match_fonts('Arial',weight='bold')$path))=='arialbd.ttf')
s<-read_json(file.path(out,'settings.json'),simplifyVector=TRUE)
rd<-function(n)as.data.frame(fread(file.path(out,'tables',n)))
rna<-rd('mRNA_bases.tsv');guides<-rd('guide_bases.tsv');rows<-rd('rows.tsv')
ends<-rd('guide_ends.tsv');labels<-rd('guide_labels.tsv');turns<-rd('turn_paths.tsv')
colors<-c(mRNA='#30363B','mRNA target core'='#D55E00','Guide core (19 nt)'='#0072B2',"Guide 3' duplex terminal (2 nt)"='#7B8792')
pt<-72.27/25.4
text_layer<-function(data,mapping,size=16,...){
 geom_text(data=data,mapping=mapping,inherit.aes=FALSE,family='Arial',fontface='bold',size=size/pt,...)
}
p<-ggplot()+
 geom_path(data=turns,aes(x=x,y=y,group=turn),colour='#A6B0B8',linewidth=.55,
  arrow=grid::arrow(length=unit(2.4,'mm'),type='closed',ends='last'))+
 text_layer(rna,aes(x,y,label=base,colour=kind),size=16)+
 text_layer(guides,aes(x,y,label=base,colour=kind),size=16)+
 text_layer(rows,aes(x=-5,y=y,label=sprintf('%04d',left_coordinate)),hjust=1,colour='#30363B')+
 text_layer(rows,aes(x=s$columns+5,y=y,label=sprintf('%04d',right_coordinate)),hjust=0,colour='#30363B')+
 text_layer(labels,aes(x,y,label=label),hjust=1,colour='#0072B2')+
 text_layer(ends,aes(x,y,label=label),colour='#0072B2')+
 annotate('text',x=-17,y=8,label='VEGFA full mRNA with nine aligned siRNA guides',
  family='Arial',fontface='bold',size=32/pt,hjust=0)+
 annotate('text',x=-17,y=5.5,label='NM_003376.6 | 3,609 nt | S-shaped reading order: follow the arrows',
  family='Arial',fontface='bold',size=20/pt,hjust=0)+
 annotate('text',x=-17,y=3.2,
  label="Orange: mRNA core sites | Blue: 19-nt guide cores | Gray: guide 3' duplex terminal 2 nt",
  family='Arial',fontface='bold',size=16/pt,hjust=0)+
 annotate('text',x=-1.8,y=0,label="5'",family='Arial',fontface='bold',size=16/pt,colour='#30363B')+
 annotate('text',x=s$terminal_3_x,y=s$terminal_3_y,label="3'",family='Arial',fontface='bold',size=16/pt,colour='#30363B')+
 annotate('text',x=-17,y=s$footer_y1,
  label='Guide labels: candidate ID | 19-nt core interval. Full 21-nt guides are aligned antiparallel to the reference mRNA.',
  family='Arial',fontface='bold',size=16/pt,hjust=0)+
 annotate('text',x=-17,y=s$footer_y2,
  label='Gray terminal bases are duplex overhangs relative to the original passenger strand; they still match this mRNA reference.',
  family='Arial',fontface='bold',size=16/pt,hjust=0)+
 annotate('text',x=-17,y=s$footer_y3,
  label='All 3,609 reference bases are shown (T converted to U). Coordinates are 1-based. Overlapping candidates occupy separate lines.',
  family='Arial',fontface='bold',size=16/pt,hjust=0)+
 scale_colour_manual(values=colors,guide='none')+
 coord_fixed(ratio=1,xlim=c(s$xmin,s$xmax),ylim=c(s$ymin,s$ymax),expand=FALSE,clip='off')+
 theme_void(base_family='Arial')+theme(plot.background=element_rect(fill='white',colour=NA),plot.margin=margin(0,0,0,0))
name<-file.path(out,'figures/default9_VEGFA_serpentine_full_sequence')
ggsave(paste0(name,'.pdf'),p,width=s$width_inches,height=s$height_inches,units='in',device=cairo_pdf,family='Arial',bg='white',limitsize=FALSE)
ggsave(paste0(name,'.svg'),p,width=s$width_inches,height=s$height_inches,units='in',device=svglite::svglite,bg='white',limitsize=FALSE)
ggsave(paste0(name,'.png'),p,width=s$width_inches,height=s$height_inches,units='in',device=ragg::agg_png,dpi=180,bg='white',limitsize=FALSE)
saveRDS(p,file.path(out,'sequence_plot.rds'))
capture.output(sessionInfo(),file=file.path(out,'logs/sessionInfo.txt'))
write_json(list(pages=1,reference=s$reference,RNA_bases=nrow(rna),guide_bases=nrow(guides),guides=nrow(labels),
 RNA_rows=nrow(rows),columns=s$columns,font='Arial Bold',base_font_pt=16,
 width_inches=s$width_inches,height_inches=s$height_inches,all_graphics_native_R=TRUE,
 plotting_packages=c('ggplot2','ragg','svglite'),new_scientific_prediction=FALSE),file.path(out,'logs/render_receipt.json'),pretty=TRUE,auto_unbox=TRUE)
cat('Exported one-page complete RNA serpentine diagram.\n')
