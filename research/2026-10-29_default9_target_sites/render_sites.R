# Native R target-coordinate graphics; fixed historical reference, no model fitting.
args<-commandArgs(trailingOnly=TRUE);out<-args[1]
suppressPackageStartupMessages({library(ggplot2);library(data.table);library(systemfonts);library(ragg);library(svglite);library(jsonlite)})
stopifnot(dir.exists(out),tolower(basename(systemfonts::match_fonts('Arial',weight='bold')$path))=='arialbd.ttf')
d<-as.data.frame(fread(file.path(out,'tables/default9_primary_positions.tsv'),colClasses=list(character='short_id')))
regions<-as.data.frame(fread(file.path(out,'tables/primary_reference_regions.tsv')))
regions$component<-ifelse(regions$region=='CDS','CDS','UTR')
regions$label<-c("5' UTR",'CDS',"3' UTR")
pt<-72.27/25.4;BLUE<-'#0072B2';ORANGE<-'#D55E00';GRAY<-'#D8DEE2'
theme_set(theme_bw(base_family='Arial',base_size=18)+theme(
 text=element_text(family='Arial',face='bold'),plot.title=element_text(size=24,face='bold',margin=margin(b=10)),
 plot.subtitle=element_text(size=16,face='bold',margin=margin(b=12)),
 axis.title=element_text(size=20,face='bold'),axis.text=element_text(size=18,face='bold',colour='black'),
 axis.text.y.right=element_text(size=16),axis.title.y.right=element_text(size=18),
 plot.caption=element_text(size=16,hjust=0,lineheight=1.05,margin=margin(t=12)),
 panel.grid=element_blank(),panel.border=element_rect(colour='black',fill=NA,linewidth=.6),
 panel.background=element_rect(fill='white',colour=NA),plot.background=element_rect(fill='white',colour=NA),
 legend.position='bottom',legend.text=element_text(size=16),legend.title=element_blank(),
 plot.margin=margin(14,18,12,14)))
palette<-c(UTR=GRAY,CDS=BLUE,'19-nt core'=ORANGE)
make_track<-function(z,limits,breaks,title,subtitle,architecture=FALSE){
 z$y<-rev(seq_len(nrow(z)));n<-nrow(z)
 labels<-paste0(z$core_start,'-',z$core_end)
 p<-ggplot()+geom_rect(data=z,aes(xmin=core_start-.5,xmax=core_end+.5,ymin=y-.12,ymax=y+.12,fill='19-nt core'),colour=NA)+
  scale_fill_manual(values=palette,breaks=if(architecture)c('UTR','CDS','19-nt core')else'19-nt core',drop=FALSE)+
  scale_x_continuous(limits=limits,breaks=breaks,labels=scales::label_comma(),expand=c(0,0))+
  scale_y_continuous(breaks=z$y,labels=z$short_id,limits=c(.4,n+if(architecture)2.1 else .65),expand=c(0,0),
   sec.axis=dup_axis(breaks=z$y,labels=labels,name=NULL))+
  labs(title=title,subtitle=paste(subtitle,'Left: candidate ID suffix | Right: core interval (nt)',sep='\n'),
   x='VEGFA mRNA coordinate (nt)',y=NULL)
 if(architecture){
  p<-p+geom_rect(data=regions,aes(xmin=start-.5,xmax=end+.5,ymin=n+1.05,ymax=n+1.48,fill=component),colour=NA)+
   geom_text(data=regions,aes(x=(start+end)/2,y=n+1.78,label=label),family='Arial',fontface='bold',size=16/pt)+
   annotate('text',x=c(497,1684),y=n+.70,label=c('497','1684'),family='Arial',fontface='bold',size=16/pt)+
   labs(caption=paste('NM_003376.6: 3,609 nt; annotated CDS 497-1684.',
    'Core intervals are 19 nt. Candidate suffixes name 23-nt windows.',sep='\n'))
 }else{
  p<-p+labs(caption=paste('3499, 3500 and 3502 target strongly overlapping regions.',
   'Mature mRNA coordinates: 1-based, inclusive; not genomic DNA.',sep='\n'))
 }
 p
}
overview<-make_track(d,c(.5,3609.5),c(1,1000,2000,3000,3609),
 'Nine siRNA target sites on VEGFA','NM_003376.6 | Paired 19-nt cores | 5\u2032 to 3\u2032',TRUE)
zoom<-d[d$short_id%in%c('3499','3500','3502','3535'),]
detail<-make_track(zoom,c(3484.5,3565.5),c(3485,3500,3520,3540,3565),
 "VEGFA 3' UTR: target-site detail",'NM_003376.6 | Zoom: 3485-3565 nt',FALSE)
plots<-list(default9_VEGFA_full_reference=overview,default9_VEGFA_3UTR_zoom=detail)
for(nm in names(plots)){
 ggsave(file.path(out,'figures',paste0(nm,'.png')),plots[[nm]],width=10,height=7,units='in',dpi=240,device=ragg::agg_png,bg='white')
 ggsave(file.path(out,'figures',paste0(nm,'.svg')),plots[[nm]],width=10,height=7,units='in',device=svglite::svglite,bg='white')
}
cairo_pdf(file.path(out,'figures/default9_VEGFA_target_sites.pdf'),width=10,height=7,family='Arial',onefile=TRUE,bg='white')
for(p in plots)print(p)
dev.off()
saveRDS(list(plots=plots,source=d,regions=regions),file.path(out,'target_site_plots.rds'))
capture.output(sessionInfo(),file=file.path(out,'logs/sessionInfo.txt'))
write_json(list(pages=2,width_inches=10,height_inches=7,font='Arial Bold',title_pt=24,axis_title_pt=20,
 candidate_label_pt=18,coordinate_label_pt=16,reference='NM_003376.6',coordinates='1-based inclusive mature mRNA',
 package='ggplot2',all_graphics_native_R=TRUE,model_fitting=FALSE),file.path(out,'logs/render_receipt.json'),pretty=TRUE,auto_unbox=TRUE)
cat('Exported two native-R target-position pages.\n')
