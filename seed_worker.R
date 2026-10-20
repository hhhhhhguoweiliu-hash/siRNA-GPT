args <- commandArgs(trailingOnly=TRUE)
root <- args[1]; input <- args[2]; output <- args[3]
.libPaths(c('C:/Users/86182/AppData/Local/R/win-library/4.3',.libPaths()))
suppressPackageStartupMessages({library(Biostrings);library(dplyr)})
source(file.path(root,'official_tools/SeedMatchR_1.1.1/R/get_seed.R'))
source(file.path(root,'official_tools/SeedMatchR_1.1.1/R/SeedMatchR.R'))
stopifnot(as.character(get_seed('UUAUAGAGCAAGAACACUGUUUU','mer7m8')$Target.Seq)=='CTCTATA')
candidates <- read.delim(input,check.names=FALSE,stringsAsFactors=FALSE,fileEncoding='UTF-8-BOM')
manifest <- read.delim(file.path(root,'prepared/utr_manifest_representative.tsv'),check.names=FALSE)
utrs <- readDNAStringSet(file.path(root,'prepared/refseq_utr3_representative.fasta'))
gtf <- manifest[,c('transcript_id','gene_id')]
res <- data.frame(gene_id=manifest$gene_id)
all <- list()
for(i in seq_len(nrow(candidates))){
 z <- SeedMatchR(res=res,gtf=gtf,seqs=utrs,sequence=candidates$guide_core19_5to3[i],seed.name='mer7m8',mismatches=0,indels=FALSE)
 names(z)[names(z)=='mer7m8'] <- 'seed_site_count'
 z <- z[z$seed_site_count>0,,drop=FALSE]
 z$candidate_id <- candidates$candidate_id[i];z$strand_role <- 'guide';z$seed_type <- 'mer7m8'
 all[[length(all)+1L]] <- z
 cat('seed matched',candidates$candidate_id[i],'\n');flush.console()
}
write.table(do.call(rbind,all),output,sep='\t',row.names=FALSE,quote=FALSE)
