# IO/timing adapter around unchanged official SeedMatchR 1.1.1 / Biostrings.
args <- commandArgs(trailingOnly=TRUE)
root <- args[1]; input <- args[2]; out <- args[3]; mode <- args[4]
stopifnot(mode %in% c('seed','nearfull'),!dir.exists(out));dir.create(out,recursive=TRUE)
elapsed <- function() unname(proc.time()[3])
start <- elapsed()
.libPaths(c('C:/Users/86182/AppData/Local/R/win-library/4.3',.libPaths()))
suppressPackageStartupMessages({library(Biostrings);library(dplyr);library(data.table)})
source(file.path(root,'official_tools/SeedMatchR_1.1.1/R/get_seed.R'))
source(file.path(root,'official_tools/SeedMatchR_1.1.1/R/SeedMatchR.R'))
example <- get_seed('UUAUAGAGCAAGAACACUGUUUU','mer7m8')
stopifnot(as.character(example$Target.Seq)=='CTCTATA')
writeLines(capture.output(example),file.path(out,'official_example.txt'))
writeLines(capture.output(sessionInfo()),file.path(out,'sessionInfo.txt'))
job <- read.delim(input,check.names=FALSE,stringsAsFactors=FALSE,fileEncoding='UTF-8-BOM')
timings <- list();summaries <- list()
if(mode=='seed'){
 t <- elapsed()
 manifest <- read.delim(file.path(root,'prepared/utr_manifest_representative.tsv'),check.names=FALSE)
 refs <- readDNAStringSet(file.path(root,'prepared/refseq_utr3_representative.fasta'))
 stopifnot(length(refs)==19415,!anyDuplicated(names(refs)),!anyDuplicated(manifest$gene_id),setequal(names(refs),as.character(manifest$transcript_id)))
 ref_gene_order<-as.character(manifest$gene_id[match(names(refs),manifest$transcript_id)])
 gtf <- manifest[,c('transcript_id','gene_id')];res <- data.frame(gene_id=manifest$gene_id)
 cat('REFERENCE_LOAD_SECONDS',elapsed()-t,'REFERENCE_GENES',length(refs),'\n');flush.console()
 for(i in seq_len(nrow(job))){
  t<-elapsed();r<-job[i,];seq<-r$sequence_core19_RNA
  z<-SeedMatchR(res=res,gtf=gtf,seqs=refs,sequence=seq,seed.name='mer7m8',mismatches=0,indels=FALSE)
  stopifnot(nrow(z)==19415,identical(as.character(z$gene_id),as.character(res$gene_id)))
  names(z)[names(z)=='mer7m8']<-'seed_site_count'
  seed<-as.character(get_seed(seq,'mer7m8')$Target.Seq)
  sites<-as.data.frame(vmatchPattern(DNAString(seed),refs,fixed=TRUE))
  recounted<-tabulate(sites$group,nbins=length(refs))
  recounted_res_order<-recounted[match(as.character(res$gene_id),ref_gene_order)]
  stopifnot(identical(as.integer(z$seed_site_count),as.integer(recounted_res_order)))
  z$candidate_id<-r$candidate_id;z$strand_role<-r$strand_role;z$target_motif_DNA<-seed
  key<-paste(r$candidate_id,r$strand_role,sep='__')
  fwrite(z,file.path(out,paste0(key,'__counts.tsv.gz')),sep='\t',compress='gzip')
  sites$transcript_id<-names(refs)[sites$group];sites$gene_id<-manifest$gene_id[match(sites$transcript_id,manifest$transcript_id)]
  sites$candidate_id<-rep(r$candidate_id,nrow(sites));sites$strand_role<-rep(r$strand_role,nrow(sites));sites$target_motif_DNA<-rep(seed,nrow(sites))
  fwrite(sites,file.path(out,paste0(key,'__sites.tsv.gz')),sep='\t',compress='gzip')
  non<-as.character(z$gene_id)!='7422';seconds<-elapsed()-t
  summaries[[i]]<-data.frame(candidate_id=r$candidate_id,strand_role=r$strand_role,reference_genes=nrow(z),seed_sites_all=sum(z$seed_site_count),matched_genes_all=sum(z$seed_site_count>0),
   seed_sites_non_target=sum(z$seed_site_count[non]),matched_genes_non_target=sum(z$seed_site_count[non]>0),target_motif_DNA=seed,seconds=seconds,status='COMPLETED')
  fwrite(do.call(rbind,summaries),file.path(out,'summary_checkpoint.tsv'),sep='\t')
  cat('SEED_COMPLETED',i,nrow(job),key,seconds,'\n');flush.console()
 }
} else {
 t<-elapsed();refs<-readDNAStringSet(file.path(root,'prepared/refseq_all_transcripts.fasta'));stopifnot(!anyDuplicated(names(refs)))
 mapping<-fread(file.path(root,'prepared/refseq_all_transcript_gene_loci.tsv'),colClasses=c(gene_id='character'))
 genemap<-split(as.character(mapping$gene_id),mapping$transcript_id)
 cat('REFERENCE_LOAD_SECONDS',elapsed()-t,'REFERENCE_TRANSCRIPTS',length(refs),'\n');flush.console()
 for(i in seq_len(nrow(job))){
  t<-elapsed();r<-job[i,];pattern<-DNAString(r$target_pattern_DNA)
  hits<-as.data.frame(vmatchPattern(pattern,refs,max.mismatch=2,with.indels=FALSE,fixed=TRUE))
  if(nrow(hits)){
   hits$transcript_id<-names(refs)[hits$group]
   hits$mismatches<-vapply(seq_len(nrow(hits)),function(k) as.integer(neditStartingAt(pattern,refs[[hits$group[k]]],hits$start[k],with.indels=FALSE,fixed=TRUE)),integer(1))
   stopifnot(all(hits$mismatches<=2))
   hits$gene_ids<-vapply(hits$transcript_id,function(id){g<-sort(unique(genemap[[id]]));if(length(g))paste(g,collapse=';') else 'UNKNOWN_MAPPING'},character(1))
  } else {hits$transcript_id<-character();hits$mismatches<-integer();hits$gene_ids<-character()}
  hits$candidate_id<-rep(r$candidate_id,nrow(hits));hits$strand_role<-rep(r$strand_role,nrow(hits));hits$query_kind<-rep(r$query_kind,nrow(hits));hits$target_pattern_DNA<-rep(r$target_pattern_DNA,nrow(hits))
  key<-paste(r$candidate_id,r$strand_role,r$query_kind,sep='__')
  fwrite(hits,file.path(out,paste0(key,'__hits.tsv.gz')),sep='\t',compress='gzip')
  ss<-list()
  for(mm in 0:2){
   h<-hits[hits$mismatches<=mm,,drop=FALSE]
   ids<-unique(unlist(strsplit(h$gene_ids[h$gene_ids!='UNKNOWN_MAPPING'],';',fixed=TRUE)))
   ss[[mm+1]]<-data.frame(candidate_id=r$candidate_id,strand_role=r$strand_role,query_kind=r$query_kind,max_mismatches=mm,site_count=nrow(h),
    non_target_gene_n=sum(ids!='7422'),unknown_mapping_transcript_n=length(unique(h$transcript_id[h$gene_ids=='UNKNOWN_MAPPING'])),
    target_gene_present='7422'%in%ids,seconds=NA_real_,status='COMPLETED')
  }
  summaries[[i]]<-do.call(rbind,ss);summaries[[i]]$seconds<-elapsed()-t
  fwrite(do.call(rbind,summaries),file.path(out,'summary_checkpoint.tsv'),sep='\t')
  cat('NEARFULL_COMPLETED',i,nrow(job),key,'hits',nrow(hits),'seconds',elapsed()-t,'\n');flush.console()
 }
}
fwrite(do.call(rbind,summaries),file.path(out,'summary.tsv'),sep='\t')
writeLines(c(paste('mode',mode),paste('planned_units',nrow(job)),paste('completed_units',length(summaries)),paste('worker_total_seconds',elapsed()-start),'status COMPLETE'),file.path(out,'status.txt'))
cat('COMPLETE',mode,nrow(job),'TOTAL_SECONDS',elapsed()-start,'\n');flush.console()
