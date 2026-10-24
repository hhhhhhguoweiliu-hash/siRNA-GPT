# Read-only confirmation of one actual boundary alignment; not a new pool scan.
args<-commandArgs(trailingOnly=TRUE)
.libPaths(c('C:/Users/86182/AppData/Local/R/win-library/4.3',.libPaths()))
suppressPackageStartupMessages(library(Biostrings))
stopifnot(as.character(packageVersion('Biostrings'))=='2.70.1')
x<-readDNAStringSet(args[1]);stopifnot(length(x)==1,names(x)=='XR_007059861.1',width(x)==7000)
pattern<-DNAString('AAATTCTTTAATACAAAAT')
actual<-neditStartingAt(pattern,x[[1]],6983,with.indels=FALSE,fixed=TRUE)
stopifnot(as.integer(actual)==2)
writeLines(c('Real reference transcript XR_007059861.1 length 7000; raw start 6983 end 7001',
 '18 observed bases, 1 observed mismatch, 1 pattern base beyond reference; neditStartingAt = 2',
 'No complete 19nt substring exists at that recorded interval. Raw Biostrings output retained.',capture.output(sessionInfo())),args[2])
rd<-utils:::.getHelpFile(help('lowlevel-matching',package='Biostrings'))
writeLines(capture.output(tools::Rd2txt(rd)),args[3])
