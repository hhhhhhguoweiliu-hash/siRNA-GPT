# Native R figures; adapted from the user's approved 2026-10-29 large-font book.
# No model inference, differential testing, risk weighting or post-render drawing.
suppressPackageStartupMessages({
 library(ggplot2);library(ggforce);library(patchwork);library(systemfonts)
 library(ragg);library(svglite);library(jsonlite)
})
out<-commandArgs(trailingOnly=TRUE)[1]
stopifnot(dir.exists(out))
fonts<-systemfonts::system_fonts()
if(!any(fonts$family=='Arial' & grepl('bold',fonts$style,ignore.case=TRUE)))
 stop('Arial Bold is unavailable; font substitution is forbidden.')
settings<-read_json(file.path(out,'settings.json'),simplifyVector=TRUE)
read_table<-function(n)read.delim(file.path(out,n),check.names=FALSE,stringsAsFactors=FALSE)
d<-read_table('candidate_summary.tsv');top<-read_table('top20_selection.tsv')
mx<-read_table('match_matrix.tsv');ex<-read_table('expression_long.tsv')
S<-settings$samples;COL<-c(Normoxia='#0072B2',Hypoxia='#D55E00');pt_per_mm<-72.27/25.4
big_theme<-theme_bw(base_size=18,base_family='Arial')+theme(
 text=element_text(family='Arial',face='bold',size=18),
 axis.title=element_text(size=20,face='bold'),axis.text=element_text(size=18,face='bold',colour='black'),
 plot.title=element_text(size=24,face='bold',margin=margin(b=12)),
 plot.subtitle=element_text(size=18,face='bold',margin=margin(b=10)),
 legend.text=element_text(size=16),legend.title=element_text(size=16),legend.position='bottom',
 panel.grid=element_blank(),panel.border=element_rect(colour='black',fill=NA,linewidth=.6),
 panel.background=element_rect(fill='white',colour=NA),plot.background=element_rect(fill='white',colour=NA),
 axis.line=element_blank(),plot.margin=margin(14,18,14,14))
theme_set(big_theme)
# Default IDs use their short suffix; arbitrary supported IDs retain complete labels.
short_id<-function(x)sub('^VEGFA_SD_','',x)
annotation_theme<-theme(plot.title=element_text(family='Arial',face='bold',size=24),plot.subtitle=element_text(family='Arial',face='bold',size=18))
plots<-list()
for(k in seq_len(ceiling(nrow(d)/3))){
 indices<-seq.int((k-1)*3+1,min(k*3,nrow(d)));a<-d[indices,,drop=FALSE]
 n<-nrow(a);a$y<-rev(seq_len(n));a$id<-short_id(a$candidate_id)
 pts<-rbind(data.frame(y=a$y,n=a$N,state='Normoxia'),data.frame(y=a$y,n=a$H,state='Hypoxia'))
 left<-ggplot(a,aes(y=y))+geom_segment(aes(x=H,xend=N,yend=y),colour='#A8B2B8',linewidth=.8)+
  geom_point(data=pts,aes(x=n,colour=state),size=4)+scale_colour_manual(values=COL,name=NULL,limits=names(COL))+
  scale_y_continuous(breaks=a$y,labels=a$id,limits=c(.3,n+.85),expand=c(0,0))+
  scale_x_continuous(limits=c(0,max(1,max(d$N,d$H))*1.08),labels=scales::label_comma(),n.breaks=3,expand=expansion(mult=c(.02,.03)))+
  labs(title='Expressed matches',x='Matched genes',y='Candidate ID')+theme(plot.title=element_text(size=20),axis.title=element_text(size=18))
 circles<-rbind(data.frame(y=a$y,x=.55,state='Normoxia'),data.frame(y=a$y,x=.90,state='Hypoxia'));circles$r<-.43
 nums<-rbind(data.frame(y=a$y,x=.28,label=scales::comma(a$N_only)),data.frame(y=a$y,x=.725,label=scales::comma(a$both)),data.frame(y=a$y,x=1.15,label=scales::comma(a$H_only)))
 right<-ggplot()+ggforce::geom_circle(data=circles,aes(x0=x,y0=y,r=r,fill=state,colour=state),alpha=.17,linewidth=.8)+
  geom_text(data=nums,aes(x,y,label=label),family='Arial',fontface='bold',size=18/pt_per_mm)+
  geom_text(data=a,aes(x=2.05,y=y+.13,label=paste0('Neither: ',scales::comma(neither))),family='Arial',fontface='bold',size=16/pt_per_mm)+
  geom_text(data=a,aes(x=2.05,y=y-.18,label=paste0('Unmapped: ',unmapped)),family='Arial',fontface='bold',size=16/pt_per_mm)+
  annotate('text',x=c(.28,.725,1.15),y=n+.65,label=c('Nor\nonly','Both','Hyp\nonly'),family='Arial',fontface='bold',size=16/pt_per_mm)+
  scale_fill_manual(values=COL,guide='none')+scale_colour_manual(values=COL,guide='none')+
  scale_y_continuous(limits=c(.3,n+.85),expand=c(0,0))+scale_x_continuous(limits=c(-.05,2.9),expand=c(0,0))+
  coord_cartesian(clip='off')+labs(title='Expression overlap',x=NULL,y=NULL)+theme(plot.title=element_text(size=20),panel.border=element_blank(),axis.text=element_blank(),axis.ticks=element_blank())
 plots[[paste0('Candidates_Venn_',k)]]<-(left|right)+plot_layout(widths=c(1,1.25))+
  plot_annotation(title='Candidate expression background',subtitle=paste0('Candidates ',min(indices),'-',max(indices),' of ',nrow(d)),theme=annotation_theme)
}
if(nrow(top)>0){
 all_limits<-range(log2(ex$TPM+1));if(diff(all_limits)==0)all_limits<-all_limits+c(0,1)
 for(k in seq_len(ceiling(nrow(top)/10))){
  indices<-seq.int((k-1)*10+1,min(k*10,nrow(top)));genes<-as.character(top$display_label[indices])
  m<-mx[mx$display_label%in%genes,,drop=FALSE];m$display_label<-factor(m$display_label,levels=rev(genes))
  m$candidate<-factor(short_id(m$candidate_id),levels=short_id(d$candidate_id))
  left<-ggplot(m,aes(candidate,display_label))+geom_point(data=m[m$matched==1,,drop=FALSE],size=3,colour='#284859')+
   scale_x_discrete(expand=expansion(add=.5),drop=FALSE)+scale_y_discrete(expand=expansion(add=.5),drop=FALSE)+
   labs(title='Seed matches',x='Candidate ID',y=NULL)+theme(plot.title=element_text(size=20),axis.title.x=element_text(size=18),axis.text.x=element_text(angle=45,hjust=1,size=16),axis.text.y=element_text(size=16),axis.ticks=element_blank())
  e<-ex[ex$display_label%in%genes,,drop=FALSE];e$display_label<-factor(e$display_label,levels=rev(genes));e$sample<-factor(e$sample,levels=S)
  right<-ggplot(e,aes(sample,display_label,fill=log2(TPM+1)))+geom_tile(colour=NA)+
   scale_x_discrete(expand=c(0,0),drop=FALSE)+scale_y_discrete(expand=c(0,0),drop=FALSE)+
   scale_fill_viridis_c(name='log2(TPM + 1)',limits=all_limits)+
   guides(fill=guide_colourbar(display='rectangles',title.position='top',barwidth=grid::unit(5,'cm'),barheight=grid::unit(.45,'cm')))+
   labs(title='Baseline expression',x=NULL,y=NULL)+theme(plot.title=element_text(size=20),axis.text.y=element_blank(),axis.text.x=element_text(angle=45,hjust=1,size=16),axis.ticks=element_blank(),legend.position='bottom')
  plots[[paste0('Candidate_genes_',k)]]<-(left|right)+plot_layout(widths=c(1,1),guides='collect')+
   plot_annotation(title='Reference matches and expression',subtitle=paste0('Top ',nrow(top),' display genes: ',min(indices),'-',max(indices)),theme=annotation_theme)
 }
}
for(nm in names(plots)){
 ggsave(file.path(out,paste0(nm,'.png')),plots[[nm]],width=10,height=7,units='in',device=ragg::agg_png,dpi=240,bg='white')
 ggsave(file.path(out,paste0(nm,'.svg')),plots[[nm]],width=10,height=7,units='in',device=svglite::svglite,bg='white')
}
cairo_pdf(file.path(out,'candidate_expression.pdf'),width=10,height=7,onefile=TRUE,family='Arial',bg='white')
for(p in plots)print(p)
notes<-c(
 'All eight untreated vessels retained: Nor1-Nor4 and Hyp1-Hyp4. One culture batch; no inferred pairing.',
 'Detected: TPM >= 1 in at least 2 of 4 vessels in each state. Target VEGFA (Entrez 7422) excluded from non-target counts.',
 'Venn counts are exact; circle areas are schematic. Neither: mapped genes below the detection rule in both states. Unmapped: expression unknown.',
 'Top 20: union of positive guide seed-matched, uniquely mapped non-target genes; ranked by mean TPM across all eight samples. No differential-expression selection.',
 'Heatmap: log2(TPM + 1); identical gene order and color limits across pages; no row standardization. Full match data are retained in source tables.',
 'Guide mer7m8 reference matches are not experimentally measured off-target effects. Expression annotations do not change candidate ranking.',
 'Current candidates and exact input versions are recorded in settings.json and manifest.json. Historical score/seed imports remain marked as imports.',
 'Native R packages: ggplot2, ggforce, patchwork; Arial Bold; 10 x 7 inches. No model inference or new differential testing in the plotting tool.')
for(k in 1:2){
 grid::grid.newpage()
 grid::grid.text(paste0('Methods and interpretation ',k,'/2'),x=.04,y=.94,just='left',gp=grid::gpar(fontfamily='Arial',fontface='bold',fontsize=24))
 lines<-unlist(lapply(notes[seq.int((k-1)*4+1,k*4)],function(x)c(strwrap(x,width=78),'')))
 if(length(lines)>20)stop('Methods page exceeds readable layout; paginate rather than shrink.')
 grid::grid.text(paste(lines,collapse='\n'),x=.04,y=.84,just=c('left','top'),gp=grid::gpar(fontfamily='Arial',fontface='bold',fontsize=16,lineheight=1.16))
}
dev.off()
capture.output(sessionInfo(),file=file.path(out,'sessionInfo.txt'))
write_json(list(pages=length(plots)+2L,figure_pages=length(plots),methods_pages=2L,png_files=paste0(names(plots),'.png'),svg_files=paste0(names(plots),'.svg'),
 r_version=R.version.string,packages=setNames(lapply(c('ggplot2','ggforce','patchwork','ragg','svglite','systemfonts','jsonlite'),function(x)as.character(packageVersion(x))),c('ggplot2','ggforce','patchwork','ragg','svglite','systemfonts','jsonlite')),
 font='Arial Bold',plotting_method='Native ggplot2 + ggforce + patchwork; cairo PDF, ragg PNG, svglite SVG'),file.path(out,'render_receipt.json'),auto_unbox=TRUE,pretty=TRUE)
