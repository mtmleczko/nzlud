########################################################
## PROGRAM NAME: 002_create_analytic.R                ##
## AUTHOR: MATT MLECZKO                               ##
## DATE CREATED: 12/28/2021                           ##
## INPUTS:                                            ##
##    001_wrld_2006.Rda                               ##
##    001_wrld_2018.Rda                               ##
##    001_nzlu_2019.Rda                               ##
##    001_wrld_panel_2018.Rda                         ##
##    001_nllus_2003.Rda                              ##
##    001_nllus_2019.Rda                              ##
##    001_ptm_2010.Rda                                ##
##    001_cstm_2010.Rda                               ##
##                                                    ##
## OUTPUTS:                                           ##
##    002_wrld_nllus_place_2006.Rda                   ##
##    002_wrld_nllus_msasample_2006.Rda               ##
##    002_wrld_nllus_msa_2006.Rda                     ##
##    002_wrld_msa_2018.Rda                           ##
##    002_nllus_msa_2019.Rda                          ##
##    002_nzlu_place_2019.Rda                         ##
##    002_nzlu_place_up_2019.Rda                      ##
##    002_nzlu_msasample_2019.Rda                     ##
##    002_nzlu_msa_2019.Rda                           ##
##    002_all_place_2019.Rda                          ##
##    002_all_msa_2019.Rda                            ##
##                                                    ##
## PURPOSE: Create municipal and MSA level files      ##
##                                                    ##
## LIST OF UPDATES:                                   ##
## 12/28/2021: Updated code for updated data          ##
## 03/24/2023: Corrected zri_c calculation            ##
########################################################

#log <- file("path to programs here/002_create_analytic.txt")
#sink(log, append=TRUE)
#sink(log, append=TRUE, type="message")

## load libraries ## 

library("haven")
library("foreign")
library("dplyr")
library("tidyr")
library("stringr")
library("readxl")
library("writexl")
library("gdata")
library("tm")
library("tm")
library("gsubfn")
library("lavaan")

`%notin%` <- Negate(`%in%`)

## create a merge function that creates merge frequency as in Stata ##
## adapted from rwbuie at the following stackoverflow thread: https://stackoverflow.com/questions/30358401/is-there-a-way-to-create-statas-merge-indicator-variable-with-rs-merge ##

stata.merge <- function(x,y, name){
  x$df1 <- 1
  y$df2 <- 2
  df <- merge(x,y, by = name, all = TRUE)
  df$merge.variable <- rowSums(df[,c("df1", "df2")], na.rm=TRUE)
  df$df1 <- NULL
  df$df2<- NULL
  df
  #print(table(df$merge.variable))
  
  ## return the merged dataframe
  return(df)
}


## define paths
input_path <- # input data path here
output_path <- # output data path here

## set working directory
setwd(input_path)

## read-in data ## 
load("001_nzlu_2019.Rda")
load("001_wrld_2006.Rda")
load("001_wrld_2018.Rda")
load("001_wrld_panel_2018.Rda")
load("001_nllus_2003.Rda")
load("001_nllus_2019.Rda")
load("001_ptm_2010.Rda")
load("001_cstm_2010.Rda")

###############
## FUNCTIONS ##
###############


## create ZRI ##

create.zri.s <- function(in.data){

  ## PCA ## 

  pca.data <- in.data %>%
    ungroup %>%
    select(sindex1, sindex2, sindex3, sindex4, sindex5, sindex6, sindex7) %>%
    drop_na()

  pca.res <- prcomp(pca.data, center= T, scale=T)
  print("PCA Results")
  print(summary(pca.res))
  loadings <- pca.res$rotation
  print("Loadings")
  print(loadings)

  ## final index ## 

  in.data$zri <- in.data$sindex1*loadings[1,1] + 
    in.data$sindex2*loadings[2,1] + 
    in.data$sindex3*loadings[3,1] + 
    in.data$sindex4*loadings[4,1] + 
    in.data$sindex5*loadings[5,1] + 
    in.data$sindex6*loadings[6,1] + 
    in.data$sindex7*loadings[7,1]

  ## standardized final index ## 

  in.data$zri_st <- (in.data$zri - mean(in.data$zri, na.rm=T))/sd(in.data$zri,na.rm=T)


  ## correlations of final index with subindices ## 

  print("Correlation between zri_st and sindex1")
  print(cor(in.data$sindex1,
            in.data$zri_st, use="complete.obs"))

  print("Correlation between zri_st and sindex2")
  print(cor(in.data$sindex2,
            in.data$zri_st, use="complete.obs"))

  print("Correlation between zri_st and sindex3")
  print(cor(in.data$sindex3,
            in.data$zri_st, use="complete.obs"))

  print("Correlation between zri_st and sindex4")
  print(cor(in.data$sindex4,
            in.data$zri_st, use="complete.obs"))

  print("Correlation between zri_st and sindex5")
  print(cor(in.data$sindex5,
            in.data$zri_st, use="complete.obs"))

  print("Correlation between zri_st and sindex6")
  print(cor(in.data$sindex6,
            in.data$zri_st, use="complete.obs"))
  
  print("Correlation between zri_st and sindex7")
  print(cor(in.data$sindex7,
            in.data$zri_st, use="complete.obs"))

  ## simple additive index ## 

  in.data$add_index <- rowSums(in.data[,c("sindex1",
                                          "sindex2",
                                          "sindex3",
                                          "sindex4",
                                          "sindex5",
                                          "sindex6",
                                          "sindex7")], na.rm=TRUE)

  print("Correlation between zri_st and add_index")
  print(cor(in.data$zri_st, 
            in.data$add_index,
            use="complete.obs"))


  ## density plot of final index ##

  print("Density plot of zri_st")
  plot(density(in.data$zri_st, na.rm=T))
  
  return(in.data)
}


## create ZRI - two indices ##

create.zri.sc2 <- function(in.data){
  
  ## PCA (source data) ## 
  
  pca.data.s <- in.data %>%
    ungroup %>%
    select(sindex1.s, sindex2.s, sindex3.s, sindex4.s, sindex5.s, sindex6.s, sindex7.s) %>%
    drop_na()
  
  pca.res.s <- prcomp(pca.data.s, center= T, scale=T)
  print("PCA Results - source data")
  print(summary(pca.res.s))
  loadings.s <- pca.res.s$rotation
  print("Loadings - source data")
  print(loadings.s)
  
  ## final index ## 
  
  in.data$zri_s <- in.data$sindex1.s*loadings.s[1,1] + 
    in.data$sindex2.s*loadings.s[2,1] + 
    in.data$sindex3.s*loadings.s[3,1] + 
    in.data$sindex4.s*loadings.s[4,1] + 
    in.data$sindex5.s*loadings.s[5,1] + 
    in.data$sindex6.s*loadings.s[6,1] +
    in.data$sindex7.s*loadings.s[7,1]
  
  ## standardized final index ## 
  
  in.data$zri_s_st <- (in.data$zri_s - mean(in.data$zri_s, na.rm=T))/sd(in.data$zri_s,na.rm=T)
  
  
  ## correlations of final index with subindices ## 
  
  print("Correlation between zri_s_st and sindex1.s")
  print(cor(in.data$sindex1.s,
            in.data$zri_s_st, use="complete.obs"))
  
  print("Correlation between zri_s_st and sindex2.s")
  print(cor(in.data$sindex2.s,
            in.data$zri_s_st, use="complete.obs"))
  
  print("Correlation between zri_s_st and sindex3.s")
  print(cor(in.data$sindex3.s,
            in.data$zri_s_st, use="complete.obs"))
  
  print("Correlation between zri_s_st and sindex4.s")
  print(cor(in.data$sindex4.s,
            in.data$zri_s_st, use="complete.obs"))
  
  print("Correlation between zri_s_st and sindex5.s")
  print(cor(in.data$sindex5.s,
            in.data$zri_s_st, use="complete.obs"))
  
  print("Correlation between zri_s_st and sindex6.s")
  print(cor(in.data$sindex6.s,
            in.data$zri_s_st, use="complete.obs"))
  
  print("Correlation between zri_s_st and sindex7.s")
  print(cor(in.data$sindex7.s,
            in.data$zri_s_st, use="complete.obs"))
  
  ## simple additive index ## 
  
  in.data$add_index.s <- rowSums(in.data[,c("sindex1.s",
                                            "sindex2.s",
                                            "sindex3.s",
                                            "sindex4.s",
                                            "sindex5.s",
                                            "sindex6.s",
                                            "sindex7.s")], na.rm=TRUE)
  
  print("Correlation between zri_s_st and add_index.s")
  print(cor(in.data$zri_s_st, 
            in.data$add_index.s,
            use="complete.obs"))
  
  
  ## density plot of final index ##
  
  print("Density plot of zri_s_st")
  print(plot(density(in.data$zri_s_st, na.rm=T)))
  
  
  
  ## PCA (comparison data) ## 
  
  pca.data.c <- in.data %>%
    ungroup %>%
    select(sindex1.c, sindex2.c, sindex3.c, sindex4.c, sindex5.c, sindex6.c, sindex7.c) %>%
    drop_na()
  
  pca.res.c <- prcomp(pca.data.c, center= T, scale=T)
  print("PCA Results - comparison data")
  print(summary(pca.res.c))
  loadings.c <- pca.res.c$rotation
  print("Loadings - comparison data")
  print(loadings.c)
  
  ## final index ## 
  
  in.data$zri_c <- in.data$sindex1.c*loadings.c[1,1] + 
    in.data$sindex2.c*loadings.c[2,1] + 
    in.data$sindex3.c*loadings.c[3,1] + 
    in.data$sindex4.c*loadings.c[4,1] + 
    in.data$sindex5.c*loadings.c[5,1] + 
    in.data$sindex6.c*loadings.c[6,1] + 
    in.data$sindex7.c*loadings.c[7,1]   ## MTM corrected 03/24/2023
  
  ## standardized final index ## 
  
  in.data$zri_c_st <- (in.data$zri_c - mean(in.data$zri_c, na.rm=T))/sd(in.data$zri_c,na.rm=T)
  
  
  ## correlations of final index with subindices ## 
  
  print("Correlation between zri_c_st and sindex1.c")
  print(cor(in.data$sindex1.c,
            in.data$zri_c_st, use="complete.obs"))
  
  print("Correlation between zri_c_st and sindex2.c")
  print(cor(in.data$sindex2.c,
            in.data$zri_c_st, use="complete.obs"))
  
  print("Correlation between zri_c_st and sindex3.c")
  print(cor(in.data$sindex3.c,
            in.data$zri_c_st, use="complete.obs"))
  
  print("Correlation between zri_c_st and sindex4.c")
  print(cor(in.data$sindex4.c,
            in.data$zri_c_st, use="complete.obs"))
  
  print("Correlation between zri_c_st and sindex5.c")
  print(cor(in.data$sindex5.c,
            in.data$zri_c_st, use="complete.obs"))
  
  print("Correlation between zri_c_st and sindex6.c")
  print(cor(in.data$sindex6.c,
            in.data$zri_c_st, use="complete.obs"))
  
  print("Correlation between zri_c_st and sindex7.c")
  print(cor(in.data$sindex7.c,
            in.data$zri_c_st, use="complete.obs"))
  
  ## simple additive index ## 
  
  in.data$add_index.c <- rowSums(in.data[,c("sindex1.c",
                                            "sindex2.c",
                                            "sindex3.c",
                                            "sindex4.c",
                                            "sindex5.c",
                                            "sindex6.c",
                                            "sindex7.c")], na.rm=TRUE)
  
  print("Correlation between zri_c_st and add_index.c")
  print(cor(in.data$zri_c_st, 
            in.data$add_index.c,
            use="complete.obs"))
  
  
  ## density plot of final index ##
  
  print("Density plot of zri_c_st")
  print(plot(density(in.data$zri_c_st, na.rm=T)))
  
  return(in.data)
}


## create updated exclusionary zoning index ##

create.zri.up <- function(in.data){
  
  ## PCA ## 
  
  pca.data <- in.data %>%
    ungroup %>%
    select(sindex1, sindex2, sindex3, sindex4, sindex5, sindex6, sindex7,
           sindex8, sindex9, sindex10, sindex11) %>%
    drop_na()
  
  pca.res <- prcomp(pca.data, center= T, scale=T)
  print("PCA Results")
  print(summary(pca.res))
  loadings <- pca.res$rotation
  print("Loadings")
  print(loadings)
  
  ## final index ## 
  
  in.data$zri_up <- in.data$sindex1*loadings[1,1] + 
    in.data$sindex2*loadings[2,1] + 
    in.data$sindex3*loadings[3,1] + 
    in.data$sindex4*loadings[4,1] + 
    in.data$sindex5*loadings[5,1] + 
    in.data$sindex6*loadings[6,1] + 
    in.data$sindex7*loadings[7,1] + 
    in.data$sindex8*loadings[8,1] + 
    in.data$sindex9_st*loadings[9,1] + 
    in.data$sindex10_st*loadings[10,1] + 
    in.data$sindex11*loadings[11,1]
  
  ## standardized final index ## 
  
  in.data$zri_up_st <- (in.data$zri_up - mean(in.data$zri_up, na.rm=T))/sd(in.data$zri_up,na.rm=T)
  
  
  ## correlations of final index with subindices ## 
  
  print("Correlation between zri_up_st and sindex1")
  print(cor(in.data$sindex1,
            in.data$zri_up_st, use="complete.obs"))
  
  print("Correlation between zri_up_st and sindex2")
  print(cor(in.data$sindex2,
            in.data$zri_up_st, use="complete.obs"))
  
  print("Correlation between zri_up_st and sindex3")
  print(cor(in.data$sindex3,
            in.data$zri_up_st, use="complete.obs"))
  
  print("Correlation between zri_up_st and sindex4")
  print(cor(in.data$sindex4,
            in.data$zri_up_st, use="complete.obs"))
  
  print("Correlation between zri_up_st and sindex5")
  print(cor(in.data$sindex5,
            in.data$zri_up_st, use="complete.obs"))
  
  print("Correlation between zri_up_st and sindex6")
  print(cor(in.data$sindex6,
            in.data$zri_up_st, use="complete.obs"))
  
  print("Correlation between zri_up_st and sindex7")
  print(cor(in.data$sindex7,
            in.data$zri_up_st, use="complete.obs"))
  
  print("Correlation between zri_up_st and sindex8")
  print(cor(in.data$sindex8,
            in.data$zri_up_st, use="complete.obs"))
  
  print("Correlation between zri_up_st and sindex9")
  print(cor(in.data$sindex9,
            in.data$zri_up_st, use="complete.obs"))
  
  print("Correlation between zri_up_st and sindex10")
  print(cor(in.data$sindex10,
            in.data$zri_up_st, use="complete.obs"))
  
  print("Correlation between zri_up_st and sindex11")
  print(cor(in.data$sindex11,
            in.data$zri_up_st, use="complete.obs"))
  
  ## simple additive index ## 
  
  in.data$add_index <- rowSums(in.data[,c("sindex1",
                                          "sindex2",
                                          "sindex3",
                                          "sindex4",
                                          "sindex5",
                                          "sindex6",
                                          "sindex7",
                                          "sindex8")], na.rm=TRUE)
  
  print("Correlation between zri_up_st and add_index")
  print(cor(in.data$zri_up_st, 
            in.data$add_index,
            use="complete.obs"))
  
  
  ## density plot of final index ##
  
  print("Density plot of zri_up_st")
  plot(density(in.data$zri_up_st, na.rm=T))
  
  return(in.data)
}

####################################
## Merge WRLD 2006 and NLLUS 2003 ##
####################################

## merge checks ##

nrow(wrld.2006.final) == length(unique(wrld.2006.final$GEOID))
class(wrld.2006.final$GEOID)
range(nchar(trim(wrld.2006.final$GEOID)))

nllus.2003.fm <- nllus.2003.final %>%
  select(-statename,
         -name)

nrow(nllus.2003.fm) == length(unique(nllus.2003.fm$GEOID))
class(nllus.2003.fm$GEOID)
range(nchar(trim(nllus.2003.fm$GEOID)))

wrld.nllus.merged <- stata.merge(wrld.2006.final,
                                 nllus.2003.fm,
                                 "GEOID")

## diagnose merge ##
table(wrld.nllus.merged$merge.variable)


## create file, keeping matches 1 and 3 ##
wrld.nllus.cb <- wrld.nllus.merged %>%
  filter(merge.variable %in% c(1,3)) %>%
  select(-merge.variable)

wrld.nllus.cb$sindex1 <- rowSums(wrld.nllus.cb[,c("restrict_sf_permit", 
                                                  "restrict_mf_permit",
                                                  "limit_sf_units",
                                                  "limit_mf_units",
                                                  "limit_mf_dwellings",
                                                  "limit_mf_dwelling_units")], na.rm=TRUE)

wrld.nllus.cb$sindex2 <- wrld.nllus.cb$open_space

wrld.nllus.cb <- wrld.nllus.cb %>%
  mutate(sindex3 = case_when(
    two_acre_more == 1 ~ 4,
    one_acre_more == 1 & two_acre_more == 0 ~ 3,
    half_acre_more == 1 & two_acre_more == 0 & one_acre_more == 0 ~ 2, 
    half_acre_less == 1 & two_acre_more == 0 & one_acre_more == 0 & half_acre_more == 0 ~ 1)) 

wrld.nllus.cb$sindex4 <- wrld.nllus.cb$total_nz

wrld.nllus.cb$sindex5 <- wrld.nllus.cb$total_rz

wrld.nllus.cb <- wrld.nllus.cb %>%
  mutate(sindex6 = case_when(
    maxden5 == 1 ~ 1,
    maxden4 == 1 ~ 2,
    maxden3 == 1 ~ 3,
    maxden2 == 1 ~ 4,
    maxden1 == 1 ~ 5))

wrld.nllus.cb$sindex7 <- wrld.nllus.cb$inclusionary


## create zri ##
wrld.nllus.2006.final <- create.zri.s(wrld.nllus.cb)

## output file ##

save(wrld.nllus.2006.final,
     file = paste(output_path,
                  "002_wrld_nllus_place_2006.Rda",
                  sep=""))

################################
## assign 2006 places to MSAs ##
################################

## merge checks ## 
nrow(wrld.nllus.2006.final) == length(unique(wrld.nllus.2006.final$GEOID))
class(wrld.nllus.2006.final$GEOID)
range(nchar(trim(wrld.nllus.2006.final$GEOID)))

nrow(ptm.2010.rd) == length(unique(ptm.2010.rd$GEOID))
class(ptm.2010.rd$GEOID)
range(nchar(trim(ptm.2010.rd$GEOID)))

## merge data frames ## 
wrld.nllus.2006.msa.merge <- stata.merge(wrld.nllus.2006.final,
                                         ptm.2010.rd,
                                         "GEOID")

## check merge ## 
table(wrld.nllus.2006.msa.merge$merge.variable)

## output non-matches eligible for match with county subs ##
no.msa.wrld.nllus.2006 <- wrld.nllus.2006.msa.merge %>%
  filter(merge.variable ==1) %>%
  select(-state,
         -placefp,
         -stab,
         -placenm,
         -cbsa10,
         -cbsaname10,
         -pop10,
         -afact,
         -merge.variable)

## keep matches ## 
wrld.nllus.msa.2006.keep1 <- wrld.nllus.2006.msa.merge %>%
  mutate(afact_num = as.numeric(afact)) %>%
  filter(merge.variable ==3 & afact >= 0.01) %>%
  select(-state,
         -placefp,
         -stab,
         -placenm,
         -pop10,
         -afact,
         -merge.variable)

## check for dups ## 
## these are places that span multiple MSAs ##
wrld.nllus.msa.dupcheck1 <- wrld.nllus.msa.2006.keep1 %>%
  group_by(GEOID) %>%
  summarize(n=n()) %>%
  filter(n>1)

## now, county subs ## 

## merge checks ##
nrow(cstm.2010.rd) == length(unique(cstm.2010.rd$GEOID))
class(cstm.2010.rd$GEOID)
range(nchar(trim(cstm.2010.rd$GEOID)))

nrow(no.msa.wrld.nllus.2006) == length(unique(no.msa.wrld.nllus.2006$GEOID))
class(no.msa.wrld.nllus.2006$GEOID)
range(nchar(trim(no.msa.wrld.nllus.2006$GEOID)))

## merge data frames ## 
wrld.nllus.2006.cs.merge <- stata.merge(no.msa.wrld.nllus.2006,
                                        cstm.2010.rd,
                                        "GEOID")

## check merge ##
table(wrld.nllus.2006.cs.merge$merge.variable)

## keep matches ## 
wrld.nllus.msa.2006.keep2 <- wrld.nllus.2006.cs.merge %>%
  mutate(afact_num = as.numeric(afact)) %>%
  filter(merge.variable ==3 & afact >= 0.01) %>%
  select(-county,
         -cousubfp,
         -cntyname,
         -cousubnm,
         -pop10,
         -afact,
         -state,
         -merge.variable)

## check for dups ## 
## these are places that span multiple MSAs ##
wrld.nllus.msa.dupcheck2 <- wrld.nllus.msa.2006.keep2 %>%
  group_by(GEOID) %>%
  summarize(n=n()) %>%
  filter(n>1)

## append the two matched dataframes ##

wrld.nllus.2006.wmsas <- rbind(wrld.nllus.msa.2006.keep1,
                               wrld.nllus.msa.2006.keep2)


## export these munis for later ##
wrld.nllus.2006.wmsas.out <- wrld.nllus.2006.wmsas %>%
  select(GEOID)

save(wrld.nllus.2006.wmsas.out,
     file = paste(output_path,
                  "002_wrld_nllus_msasample_2006.Rda",
                  sep=""))

## create MSA level file ## 

wrld.nllus.msa.2006 <- wrld.nllus.2006.wmsas %>%
  group_by(cbsa10) %>%
  summarize(cbsaname10 = cbsaname10[which(cbsaname10 != "")[1]],
            responses = n(),
            restrict_sf_permit = mean(restrict_sf_permit, na.rm=T),
            restrict_mf_permit = mean(restrict_mf_permit, na.rm=T),
            limit_sf_units = mean(limit_sf_units, na.rm=T),
            limit_mf_units = mean(limit_mf_units, na.rm=T),
            limit_mf_dwellings = mean(limit_mf_dwellings, na.rm=T),
            limit_mf_dwelling_units = mean(limit_mf_dwelling_units, na.rm=T),
            min_lot_size = mean(min_lot_size, na.rm=T),
            open_space = mean(open_space, na.rm=T),
            inclusionary = mean(inclusionary, na.rm=T),
            half_acre_less = mean(half_acre_less, na.rm=T),
            half_acre_more = mean(half_acre_more, na.rm=T),
            one_acre_more = mean(one_acre_more, na.rm=T),
            two_acre_more = mean(two_acre_more, na.rm=T),
            total_nz = mean(total_nz, na.rm=T),
            total_rz = mean(total_rz, na.rm=T),
            maxden5 = mean(maxden5, na.rm=T),
            maxden4 = mean(maxden4, na.rm=T),
            maxden3 = mean(maxden3, na.rm=T),
            maxden2 = mean(maxden2, na.rm=T),
            maxden1 = mean(maxden1, na.rm=T),
            zri = median(zri, na.rm=T)) 


## re-standardize final index ## 

wrld.nllus.msa.2006$zri_st <- (wrld.nllus.msa.2006$zri - mean(wrld.nllus.msa.2006$zri, na.rm=T))/sd(wrld.nllus.msa.2006$zri,na.rm=T)


## output file ##

save(wrld.nllus.msa.2006,
     file = paste(output_path,
                  "002_wrld_nllus_msa_2006.Rda",
                  sep=""))


#####################################
## assign WRLD 2018 places to MSAs ##
#####################################

## merge checks ## 
nrow(wrld.2018.final) == length(unique(wrld.2018.final$GEOID))
class(wrld.2018.final$GEOID)
range(nchar(trim(wrld.2018.final$GEOID)))

nrow(ptm.2010.rd) == length(unique(ptm.2010.rd$GEOID))
class(ptm.2010.rd$GEOID)
range(nchar(trim(ptm.2010.rd$GEOID)))

## merge data frames ## 
wrld.2018.msa.merge <- stata.merge(wrld.2018.final,
                                   ptm.2010.rd,
                                   "GEOID")

## check merge ## 
table(wrld.2018.msa.merge$merge.variable)

## output non-matches eligible for match with county subs ##
no.msa.wrld.2018 <- wrld.2018.msa.merge %>%
  filter(merge.variable ==1) %>%
  select(-placefp,
         -stab,
         -placenm,
         -cbsa10,
         -cbsaname10,
         -pop10,
         -afact,
         -merge.variable)

## keep matches ## 
wrld.msa.2018.keep1 <- wrld.2018.msa.merge %>%
  mutate(afact_num = as.numeric(afact)) %>%
  filter(merge.variable ==3 & afact_num >= 0.01) %>%
  select(-placefp,
         -stab,
         -placenm,
         -pop10,
         -afact,
         -merge.variable)

## check for dups ## 
## these are places that span multiple MSAs ##
wrld.msa.2018.dupcheck1 <- wrld.msa.2018.keep1 %>%
  group_by(GEOID) %>%
  summarize(n=n()) %>%
  filter(n>1)

## now, county subs ## 

## merge checks ##
nrow(cstm.2010.rd) == length(unique(cstm.2010.rd$GEOID))
class(cstm.2010.rd$GEOID)
range(nchar(trim(cstm.2010.rd$GEOID)))

nrow(no.msa.wrld.2018) == length(unique(no.msa.wrld.2018$GEOID))
class(no.msa.wrld.2018$GEOID)
range(nchar(trim(no.msa.wrld.2018$GEOID)))

## merge data frames ## 
wrld.2018.cs.merge <- stata.merge(no.msa.wrld.2018,
                                  cstm.2010.rd,
                                  "GEOID")

## check merge ##
table(wrld.2018.cs.merge$merge.variable)

## keep matches ## 
wrld.msa.2018.keep2 <- wrld.2018.cs.merge %>%
  mutate(afact_num = as.numeric(afact)) %>%
  filter(merge.variable ==3 & afact >= 0.01) %>%
  select(-county,
         -cousubfp,
         -cntyname,
         -cousubnm,
         -pop10,
         -afact,
         -state,
         -merge.variable)

## check for dups ## 
## these are places that span multiple MSAs ##
wrld.msa.2018.dupcheck2 <- wrld.msa.2018.keep2 %>%
  group_by(GEOID) %>%
  summarize(n=n()) %>%
  filter(n>1)

## append the two matched dataframes ##

wrld.2018.wmsas <- rbind(wrld.msa.2018.keep1,
                         wrld.msa.2018.keep2)

## create MSA level file ## 

wrld.msa.2018 <- wrld.2018.wmsas %>%
  group_by(cbsa10) %>%
  summarize(cbsaname10 = cbsaname10[which(cbsaname10 != "")[1]],
            responses = n(),
            restrict_sf_permit = mean(restrict_sf_permit, na.rm=T),
            restrict_mf_permit = mean(restrict_mf_permit, na.rm=T),
            limit_sf_units = mean(limit_sf_units, na.rm=T),
            limit_mf_units = mean(limit_mf_units, na.rm=T),
            limit_mf_dwellings = mean(limit_mf_dwellings, na.rm=T),
            limit_mf_dwelling_units = mean(limit_mf_dwelling_units, na.rm=T),
            min_lot_size = mean(min_lot_size, na.rm=T),
            open_space = mean(open_space, na.rm=T),
            half_acre_less = mean(half_acre_less, na.rm=T),
            half_acre_more = mean(half_acre_more, na.rm=T),
            one_acre_more = mean(one_acre_more, na.rm=T),
            two_acre_more = mean(two_acre_more, na.rm=T),
            total_nz = mean(total_nz, na.rm=T),
            total_rz = mean(total_rz, na.rm=T),
            WRLURI18 = median(WRLURI18, na.rm=T))

## re-standardize final index ## 

wrld.msa.2018$WRLURI18_st <- (wrld.msa.2018$WRLURI18 - mean(wrld.msa.2018$WRLURI18, na.rm=T))/sd(wrld.msa.2018$WRLURI18,na.rm=T)


## output file ##

save(wrld.msa.2018,
     file = paste(output_path,
                  "002_wrld_msa_2018.Rda",
                  sep=""))

######################################
## assign NLLUS 2019 places to MSAs ##
######################################

## merge checks ## 
nrow(nllus.2019.final) == length(unique(nllus.2019.final$GEOID))
class(nllus.2019.final$GEOID)
range(nchar(trim(nllus.2019.final$GEOID)))

nrow(ptm.2010.rd) == length(unique(ptm.2010.rd$GEOID))
class(ptm.2010.rd$GEOID)
range(nchar(trim(ptm.2010.rd$GEOID)))

## merge data frames ## 
nllus.2019.msa.merge <- stata.merge(nllus.2019.final,
                                    ptm.2010.rd,
                                    "GEOID")

## check merge ## 
table(nllus.2019.msa.merge$merge.variable)

## output non-matches eligible for match with county subs ##
no.msa.nllus.2019 <- nllus.2019.msa.merge %>%
  filter(merge.variable ==1) %>%
  select(-state,
         -placefp,
         -stab,
         -placenm,
         -cbsa10,
         -cbsaname10,
         -pop10,
         -afact,
         -merge.variable)

## keep matches ## 
nllus.msa.2019.keep1 <- nllus.2019.msa.merge %>%
  mutate(afact_num = as.numeric(afact)) %>%
  filter(merge.variable ==3 & afact_num >= 0.01) %>%
  select(-state,
         -placefp,
         -stab,
         -placenm,
         -pop10,
         -afact,
         -merge.variable)

## check for dups ## 
## these are places that span multiple MSAs ##
nllus.msa.2019.dupcheck1 <- nllus.msa.2019.keep1 %>%
  group_by(GEOID) %>%
  summarize(n=n()) %>%
  filter(n>1)

## now, county subs ## 

## merge checks ##
nrow(cstm.2010.rd) == length(unique(cstm.2010.rd$GEOID))
class(cstm.2010.rd$GEOID)
range(nchar(trim(cstm.2010.rd$GEOID)))

nrow(no.msa.nllus.2019) == length(unique(no.msa.nllus.2019$GEOID))
class(no.msa.nllus.2019$GEOID)
range(nchar(trim(no.msa.nllus.2019$GEOID)))

## merge data frames ## 
nllus.2019.cs.merge <- stata.merge(no.msa.nllus.2019,
                                   cstm.2010.rd,
                                   "GEOID")

## check merge ##
table(nllus.2019.cs.merge$merge.variable)

## keep matches ## 
nllus.msa.2019.keep2 <- nllus.2019.cs.merge %>%
  mutate(afact_num = as.numeric(afact)) %>%
  filter(merge.variable ==3 & afact_num >= 0.01) %>%
  select(-county,
         -cousubfp,
         -cntyname,
         -cousubnm,
         -pop10,
         -afact,
         -state,
         -merge.variable)

## check for dups ## 
## these are places that span multiple MSAs ##
nllus.msa.2019.dupcheck2 <- nllus.msa.2019.keep2 %>%
  group_by(GEOID) %>%
  summarize(n=n()) %>%
  filter(n>1)

## append the two matched dataframes ##

nllus.2019.wmsas <- rbind(nllus.msa.2019.keep1,
                          nllus.msa.2019.keep2)

## create MSA level file ## 

nllus.msa.2019 <- nllus.2019.wmsas %>%
  group_by(cbsa10) %>%
  summarize(cbsaname10 = cbsaname10[which(cbsaname10 != "")[1]],
            responses = n(),
            inclusionary = mean(inclusionary, na.rm=T),
            maxden1 = mean(maxden1, na.rm=T),
            maxden2 = mean(maxden2, na.rm=T),
            maxden3 = mean(maxden3, na.rm=T),
            maxden4 = mean(maxden4, na.rm=T),
            maxden5 = mean(maxden5, na.rm=T))

## output file ##

save(nllus.msa.2019,
     file = paste(output_path,
                  "002_nllus_msa_2019.Rda",
                  sep=""))

#####################
## NZLU index file ##
#####################

## change values for munis that are verified as incorrect ##

## Barre, MA ## 
nzlu.2019.final$restrict_sf_permit[nzlu.2019.final$GEOID == "2503740"] <- 1
nzlu.2019.final$restrict_mf_permit[nzlu.2019.final$GEOID == "2503740"] <- 1
nzlu.2019.final$limit_sf_units[nzlu.2019.final$GEOID == "2503740"] <- 1
nzlu.2019.final$limit_mf_units[nzlu.2019.final$GEOID == "2503740"] <- 1
nzlu.2019.final$limit_mf_dwellings[nzlu.2019.final$GEOID == "2503740"] <- 1

## Orlando, FL ## 
nzlu.2019.final$restrict_sf_permit[nzlu.2019.final$GEOID == "1253000"] <- 0
nzlu.2019.final$restrict_mf_permit[nzlu.2019.final$GEOID == "1253000"] <- 0
nzlu.2019.final$limit_sf_units[nzlu.2019.final$GEOID == "1253000"] <- 0
nzlu.2019.final$limit_mf_units[nzlu.2019.final$GEOID == "1253000"] <- 0
nzlu.2019.final$limit_mf_dwellings[nzlu.2019.final$GEOID == "1253000"] <- 0
nzlu.2019.final$limit_mf_dwelling_units[nzlu.2019.final$GEOID == "1253000"] <- 0

## Winston Salem, NC ## 
nzlu.2019.final$restrict_sf_permit[nzlu.2019.final$GEOID == "3775000"] <- 0
nzlu.2019.final$restrict_mf_permit[nzlu.2019.final$GEOID == "3775000"] <- 0
nzlu.2019.final$limit_sf_units[nzlu.2019.final$GEOID == "3775000"] <- 0
nzlu.2019.final$limit_mf_units[nzlu.2019.final$GEOID == "3775000"] <- 0
nzlu.2019.final$limit_mf_dwellings[nzlu.2019.final$GEOID == "3775000"] <- 0
nzlu.2019.final$limit_mf_dwelling_units[nzlu.2019.final$GEOID == "3775000"] <- 0

## Palm Beach Gardens, FL ##
nzlu.2019.final$restrict_sf_permit[nzlu.2019.final$GEOID == "1254075"] <- 0
nzlu.2019.final$restrict_mf_permit[nzlu.2019.final$GEOID == "1254075"] <- 0
nzlu.2019.final$limit_sf_units[nzlu.2019.final$GEOID == "1254075"] <- 0
nzlu.2019.final$limit_mf_units[nzlu.2019.final$GEOID == "1254075"] <- 0

## carry on with processing ##

nzlu.2019.final$sindex1 <- rowSums(nzlu.2019.final[,c("restrict_sf_permit", 
                                                      "restrict_mf_permit",
                                                      "limit_sf_units",
                                                      "limit_mf_units",
                                                      "limit_mf_dwellings",
                                                      "limit_mf_dwelling_units")], na.rm=TRUE)

nzlu.2019.final$sindex2 <- nzlu.2019.final$open_space

nzlu.2019.final <- nzlu.2019.final %>%
  mutate(sindex3 = case_when(
    two_acre_more == 1 ~ 4,
    one_acre_more == 1 & two_acre_more == 0 ~ 3,
    half_acre_more == 1 & two_acre_more == 0 & one_acre_more == 0 ~ 2, 
    half_acre_less == 1 & two_acre_more == 0 & one_acre_more == 0 & half_acre_more == 0 ~ 1)) 

nzlu.2019.final$sindex4 <- nzlu.2019.final$total_nz

nzlu.2019.final$sindex5 <- nzlu.2019.final$total_rz

nzlu.2019.final <- nzlu.2019.final %>%
  mutate(sindex6 = case_when(
    maxden5 == 1 ~ 1,
    maxden4 == 1 ~ 2,
    maxden3 == 1 ~ 3,
    maxden2 == 1 ~ 4,
    maxden1 == 1 ~ 5))

nzlu.2019.final$sindex7 <- nzlu.2019.final$inclusionary

## new sub-indices ##

nzlu.2019.final <- nzlu.2019.final %>%
  rowwise() %>%
  mutate(sindex8 = adu,
         height_st_median_sc = height_st_median*14,
         height_st_mode_sc = height_st_mode*14,
         sindex9 = median(height_ft_median,
                           height_ft_mode,
                           height_st_median_sc,
                           height_st_mode_sc,
                           na.rm=T),
         sindex10 = median(parking_median,
                           parking_mode,
                           na.rm=T),
         sindex11 = mf_per)

## CA fixes ##
nzlu.2019.final$sindex3[nzlu.2019.final$GEOID == "0614736"] <- 2
nzlu.2019.final$sindex11[nzlu.2019.final$GEOID == "0614736"] <- 0
nzlu.2019.final$sindex3[nzlu.2019.final$GEOID == "0620956"] <- 1
nzlu.2019.final$sindex9[nzlu.2019.final$GEOID == "0647486"] <- 30

## TX fixes ##
nzlu.2019.final$sindex11[nzlu.2019.final$GEOID == "4802272"] <- 1

nzlu.2019.final$sindex3[nzlu.2019.final$GEOID == "4803144"] <- 1
nzlu.2019.final$sindex9[nzlu.2019.final$GEOID == "4803144"] <- 100
nzlu.2019.final$sindex10[nzlu.2019.final$GEOID == "4803144"] <- 0
nzlu.2019.final$sindex11[nzlu.2019.final$GEOID == "4803144"] <- 1

nzlu.2019.final$sindex3[nzlu.2019.final$GEOID == "4806060"] <- 1
nzlu.2019.final$sindex9[nzlu.2019.final$GEOID == "4806060"] <- 100
nzlu.2019.final$sindex11[nzlu.2019.final$GEOID == "4806060"] <- 1

nzlu.2019.final$sindex9[nzlu.2019.final$GEOID == "4807432"] <- 100
nzlu.2019.final$sindex11[nzlu.2019.final$GEOID == "4807432"] <- 1

nzlu.2019.final$sindex3[nzlu.2019.final$GEOID == "4811300"] <- 1

nzlu.2019.final$sindex3[nzlu.2019.final$GEOID == "4820140"] <- 1
nzlu.2019.final$sindex9[nzlu.2019.final$GEOID == "4820140"] <- 100
nzlu.2019.final$sindex10[nzlu.2019.final$GEOID == "4820140"] <- 0
nzlu.2019.final$sindex11[nzlu.2019.final$GEOID == "4820140"] <- 1

nzlu.2019.final$sindex10[nzlu.2019.final$GEOID == "4823164"] <- 2

nzlu.2019.final$sindex10[nzlu.2019.final$GEOID == "4827996"] <- 0
nzlu.2019.final$sindex11[nzlu.2019.final$GEOID == "4827996"] <- 0.25

nzlu.2019.final$sindex3[nzlu.2019.final$GEOID == "4833068"] <- 1
nzlu.2019.final$sindex9[nzlu.2019.final$GEOID == "4833068"] <- 35
nzlu.2019.final$sindex10[nzlu.2019.final$GEOID == "4833068"] <- 2
nzlu.2019.final$sindex11[nzlu.2019.final$GEOID == "4833068"] <- 0

nzlu.2019.final$sindex3[nzlu.2019.final$GEOID == "4834502"] <- 1
nzlu.2019.final$sindex9[nzlu.2019.final$GEOID == "4834502"] <- 100
nzlu.2019.final$sindex10[nzlu.2019.final$GEOID == "4834502"] <- 0

nzlu.2019.final$sindex11[nzlu.2019.final$GEOID == "4835000"] <- 1

nzlu.2019.final$sindex3[nzlu.2019.final$GEOID == "4836092"] <- 1
nzlu.2019.final$sindex11[nzlu.2019.final$GEOID == "4836092"] <- 1

nzlu.2019.final$sindex9[nzlu.2019.final$GEOID == "4837156"] <- 28

nzlu.2019.final$sindex9[nzlu.2019.final$GEOID == "4837984"] <- 100
nzlu.2019.final$sindex10[nzlu.2019.final$GEOID == "4837984"] <- 0

nzlu.2019.final$sindex11[nzlu.2019.final$GEOID == "4838776"] <- 1

nzlu.2019.final$sindex9[nzlu.2019.final$GEOID == "4846500"] <- 40

nzlu.2019.final$sindex9[nzlu.2019.final$GEOID == "4847337"] <- 38.75

nzlu.2019.final$sindex3[nzlu.2019.final$GEOID == "4849128"] <- 1

nzlu.2019.final$sindex9[nzlu.2019.final$GEOID == "4850628"] <- 100

nzlu.2019.final$sindex9[nzlu.2019.final$GEOID == "4854528"] <- 100
nzlu.2019.final$sindex10[nzlu.2019.final$GEOID == "4854528"] <- 0

nzlu.2019.final$sindex3[nzlu.2019.final$GEOID == "4855008"] <- 1
nzlu.2019.final$sindex9[nzlu.2019.final$GEOID == "4855008"] <- 100

nzlu.2019.final$sindex11[nzlu.2019.final$GEOID == "4856000"] <- 1

nzlu.2019.final$sindex9[nzlu.2019.final$GEOID == "4857800"] <- 35

nzlu.2019.final$sindex3[nzlu.2019.final$GEOID == "4860164"] <- 1
nzlu.2019.final$sindex9[nzlu.2019.final$GEOID == "4860164"] <- 100
nzlu.2019.final$sindex10[nzlu.2019.final$GEOID == "4860164"] <- 0

nzlu.2019.final$sindex3[nzlu.2019.final$GEOID == "4863044"] <- 1
nzlu.2019.final$sindex9[nzlu.2019.final$GEOID == "4863044"] <- 100
nzlu.2019.final$sindex10[nzlu.2019.final$GEOID == "4863044"] <- 0
nzlu.2019.final$sindex11[nzlu.2019.final$GEOID == "4863044"] <- 1

nzlu.2019.final$sindex11[nzlu.2019.final$GEOID == "4863284"] <- 1

nzlu.2019.final$sindex11[nzlu.2019.final$GEOID == "4866464"] <- 1

nzlu.2019.final$sindex9[nzlu.2019.final$GEOID == "4867688"] <- 40
nzlu.2019.final$sindex10[nzlu.2019.final$GEOID == "4867688"] <- 2

nzlu.2019.final$sindex9[nzlu.2019.final$GEOID == "4867964"] <- 100
nzlu.2019.final$sindex10[nzlu.2019.final$GEOID == "4867964"] <- 0
nzlu.2019.final$sindex11[nzlu.2019.final$GEOID == "4867964"] <- 1

nzlu.2019.final$sindex9[nzlu.2019.final$GEOID == "4869020"] <- 100

nzlu.2019.final$sindex9[nzlu.2019.final$GEOID == "4869548"] <- 100

nzlu.2019.final$sindex3[nzlu.2019.final$GEOID == "4867964"] <- 3
nzlu.2019.final$sindex9[nzlu.2019.final$GEOID == "4867964"] <- 100
nzlu.2019.final$sindex10[nzlu.2019.final$GEOID == "4867964"] <- 1
nzlu.2019.final$sindex11[nzlu.2019.final$GEOID == "4867964"] <- 0

nzlu.2019.final$sindex3[nzlu.2019.final$GEOID == "4871384"] <- 1
nzlu.2019.final$sindex9[nzlu.2019.final$GEOID == "4871384"] <- 100

nzlu.2019.final$sindex10[nzlu.2019.final$GEOID == "4871540"] <- 0

nzlu.2019.final$sindex3[nzlu.2019.final$GEOID == "4872989"] <- 1

nzlu.2019.final$sindex3[nzlu.2019.final$GEOID == "4876228"] <- 1
nzlu.2019.final$sindex11[nzlu.2019.final$GEOID == "4876228"] <- 1

nzlu.2019.final$sindex3[nzlu.2019.final$GEOID == "4876948"] <- 1
nzlu.2019.final$sindex9[nzlu.2019.final$GEOID == "4876948"] <- 43.75
nzlu.2019.final$sindex10[nzlu.2019.final$GEOID == "4876948"] <- 3
nzlu.2019.final$sindex11[nzlu.2019.final$GEOID == "4876948"] <- 0.5

nzlu.2019.final$sindex3[nzlu.2019.final$GEOID == "4877416"] <- 1
nzlu.2019.final$sindex9[nzlu.2019.final$GEOID == "4877416"] <- 100
nzlu.2019.final$sindex11[nzlu.2019.final$GEOID == "4877416"] <- 1



nzlu.2019.final$sindex9 <- ifelse(nzlu.2019.final$sindex9 > quantile(nzlu.2019.final$sindex9,0.99,na.rm=T),
                                  NA,
                                  nzlu.2019.final$sindex9)

nzlu.2019.final$sindex9_st <- (nzlu.2019.final$sindex9 - mean(nzlu.2019.final$sindex9, na.rm=T))/sd(nzlu.2019.final$sindex9,na.rm=T)
nzlu.2019.final$sindex10_st <- (nzlu.2019.final$sindex10 - mean(nzlu.2019.final$sindex10, na.rm=T))/sd(nzlu.2019.final$sindex10,na.rm=T)

summary(nzlu.2019.final)

## create zri ##

## subset to original sample ## 

nzlu.2019.wsamp.m <- stata.merge(wrld.nllus.2006.final,
                                 nzlu.2019.final,
                                 "GEOID")

## check merge ##
table(nzlu.2019.wsamp.m$merge.variable)

nzlu.2019.wsamp.ids <- nzlu.2019.wsamp.m %>%
  filter(merge.variable == 3) %>%
  select(GEOID)

nzlu.2019.wsamp <- nzlu.2019.final %>%
  filter(GEOID %in% nzlu.2019.wsamp.ids$GEOID)

nzlu.2019.zri1.up <- create.zri.s(nzlu.2019.final)
nzlu.2019.up <- create.zri.up(nzlu.2019.zri1.up)

nzlu.2019.zri1 <- create.zri.s(nzlu.2019.wsamp)
nzlu.2019.final <- create.zri.up(nzlu.2019.zri1)

## checks  ##

test <- nzlu.2019.up %>%
  filter(is.na(zri_up_st)) %>%
  select(GEOID,
         place,
         statename,
         starts_with("sindex"),
         zri_up,
         zri_up_st)

nzlu.2019.finlook <- nzlu.2019.final %>%
  select(GEOID,
         statename,
         place,
         zri,
         zri_st,
         zri_up,
         zri_up_st)

## output file ##

save(nzlu.2019.final,
     file = paste(output_path,
                  "002_nzlu_place_2019.Rda",
                  sep=""))

save(nzlu.2019.up,
     file = paste(output_path,
                  "002_nzlu_place_up_2019.Rda",
                  sep=""))

write.csv(nzlu.2019.up,
          "002_nzlu_2019_up.csv")


#######################################
## assign source 2019 places to MSAs ##
#######################################

## merge checks ## 
nrow(nzlu.2019.final) == length(unique(nzlu.2019.final$GEOID))
class(nzlu.2019.final$GEOID)
range(nchar(trim(nzlu.2019.final$GEOID)))

nrow(ptm.2010.rd) == length(unique(ptm.2010.rd$GEOID))
class(ptm.2010.rd$GEOID)
range(nchar(trim(ptm.2010.rd$GEOID)))

## merge data frames ## 
nzlu.2019.msa.merge <- stata.merge(nzlu.2019.final,
                                   ptm.2010.rd,
                                   "GEOID")

## check merge ## 
table(nzlu.2019.msa.merge$merge.variable)

## output non-matches eligible for match with county subs ##
no.msa.nzlu.2019 <- nzlu.2019.msa.merge %>%
  filter(merge.variable ==1) %>%
  select(-state,
         -placefp,
         -stab,
         -placenm,
         -cbsa10,
         -cbsaname10,
         -pop10,
         -afact,
         -merge.variable)

## keep matches ## 
nzlu.2019.msa.keep1 <- nzlu.2019.msa.merge %>%
  mutate(afact_num = as.numeric(afact)) %>%
  filter(merge.variable ==3 & afact_num >= 0.01) %>%
  select(-state,
         -placefp,
         -stab,
         -placenm,
         -pop10,
         -afact,
         -merge.variable)

## check for dups ## 
## these are places that span multiple MSAs ##
nzlu.2019.dupcheck1 <- nzlu.2019.msa.keep1 %>%
  group_by(GEOID) %>%
  summarize(n=n()) %>%
  filter(n>1)

## now, county subs ## 

## merge checks ##
nrow(cstm.2010.rd) == length(unique(cstm.2010.rd$GEOID))
class(cstm.2010.rd$GEOID)
range(nchar(trim(cstm.2010.rd$GEOID)))

nrow(no.msa.nzlu.2019) == length(unique(no.msa.nzlu.2019$GEOID))
class(no.msa.nzlu.2019$GEOID)
range(nchar(trim(no.msa.nzlu.2019$GEOID)))

## merge data frames ## 
nzlu.2019.cs.merge <- stata.merge(no.msa.nzlu.2019,
                                  cstm.2010.rd,
                                  "GEOID")

## check merge ##
table(nzlu.2019.cs.merge$merge.variable)

## keep matches ## 
nzlu.2019.msa.keep2 <- nzlu.2019.cs.merge %>%
  mutate(afact_num = as.numeric(afact)) %>%
  filter(merge.variable ==3 & afact_num >= 0.01) %>%
  select(-county,
         -cousubfp,
         -cntyname,
         -cousubnm,
         -pop10,
         -afact,
         -state,
         -merge.variable)

## check for dups ## 
## these are places that span multiple MSAs ##
nzlu.2019.dupcheck2 <- nzlu.2019.msa.keep2 %>%
  group_by(GEOID) %>%
  summarize(n=n()) %>%
  filter(n>1)

## append the two matched dataframes ##

nzlu.2019.wmsas <- rbind(nzlu.2019.msa.keep1,
                         nzlu.2019.msa.keep2)

## export these munis for later ##
nzlu.2019.wmsas.out <- nzlu.2019.wmsas %>%
  select(GEOID)

save(nzlu.2019.wmsas.out,
     file = paste(output_path,
                  "002_nzlu_msasample_2019.Rda",
                  sep=""))

## create MSA level file ## 

nzlu.msa.2019.pt1 <- nzlu.2019.wmsas %>%
  group_by(cbsa10) %>%
  summarize(cbsaname10 = cbsaname10[which(cbsaname10 != "")[1]],
            responses = n(),
            restrict_sf_permit = mean(restrict_sf_permit, na.rm=T),
            restrict_mf_permit = mean(restrict_mf_permit, na.rm=T),
            limit_sf_units = mean(limit_sf_units, na.rm=T),
            limit_mf_units = mean(limit_mf_units, na.rm=T),
            limit_mf_dwellings = mean(limit_mf_dwellings, na.rm=T),
            limit_mf_dwelling_units = mean(limit_mf_dwelling_units, na.rm=T),
            min_lot_size = mean(min_lot_size, na.rm=T),
            open_space = mean(open_space, na.rm=T),
            inclusionary = mean(inclusionary, na.rm=T),
            half_acre_less = mean(half_acre_less, na.rm=T),
            half_acre_more = mean(half_acre_more, na.rm=T),
            one_acre_more = mean(one_acre_more, na.rm=T),
            two_acre_more = mean(two_acre_more, na.rm=T),
            total_nz = mean(total_nz, na.rm=T),
            total_rz = mean(total_rz, na.rm=T),
            maxden5 = mean(maxden5, na.rm=T),
            maxden4 = mean(maxden4, na.rm=T),
            maxden3 = mean(maxden3, na.rm=T),
            maxden2 = mean(maxden2, na.rm=T),
            maxden1 = mean(maxden1, na.rm=T),
            adu = mean(adu, na.rm=T),
            height_ft_median = mean(height_ft_median, na.rm=T),
            height_ft_mode = mean(height_ft_mode, na.rm=T),
            height_st_median = mean(height_st_median, na.rm=T),
            height_st_mode = mean(height_st_mode,na.rm=T),
            parking_median = mean(parking_median,na.rm=T),
            parking_mode = mean(parking_mode,na.rm=T),
            zri_median = median(zri, na.rm=T),
            zri_range = abs(max(zri, na.rm=T) - min(zri,na.rm=T)),
            zri_median_up = median(zri_up, na.rm=T),
            zri_range_up = abs(max(zri_up, na.rm=T) - min(zri,na.rm=T))) %>%
  filter(!is.na(zri_median) & !is.na(zri_median_up))
            
## re-standardize final index ## 

nzlu.msa.2019.pt1$zri_median_st <- (nzlu.msa.2019.pt1$zri_median - mean(nzlu.msa.2019.pt1$zri_median, na.rm=T))/sd(nzlu.msa.2019.pt1$zri_median,na.rm=T)
nzlu.msa.2019.pt1$zri_range_st <- (nzlu.msa.2019.pt1$zri_range - mean(nzlu.msa.2019.pt1$zri_range, na.rm=T))/sd(nzlu.msa.2019.pt1$zri_range,na.rm=T)

nzlu.msa.2019.pt1$zri_median_up_st <- (nzlu.msa.2019.pt1$zri_median_up - mean(nzlu.msa.2019.pt1$zri_median_up, na.rm=T))/sd(nzlu.msa.2019.pt1$zri_median_up,na.rm=T)
nzlu.msa.2019.pt1$zri_range_up_st <- (nzlu.msa.2019.pt1$zri_range_up - mean(nzlu.msa.2019.pt1$zri_range_up, na.rm=T))/sd(nzlu.msa.2019.pt1$zri_range_up,na.rm=T)

nzlu.msa.2019.pt1look <- nzlu.msa.2019.pt1 %>%
  select(cbsa10,
         cbsaname10,
         zri_median,
         zri_median_st,
         zri_range,
         zri_range_st,
         zri_median_up,
         zri_median_up_st,
         zri_range_up,
         zri_range_up_st)

nzlu.msas.2019 <- nzlu.2019.wmsas %>%
  select(GEOID,
         statename,
         place,
         cbsa10,
         cbsaname10,
         zri,
         zri_st,
         zri_up,
         zri_up_st)

## now, let's create the second msa level ZRI dimension ##

## merge on central cities ##

load("cc_out.Rda")

nzlu.msa.2019.pt2.m <- stata.merge(nzlu.2019.wmsas,
                                   cc.out,
                                   "GEOID")

## check merge ##
table(nzlu.msa.2019.pt2.m$merge.variable, useNA = "ifany")


## keep all obs, create cc indicator ## 

nzlu.msa.2019.pt2.temp <- nzlu.msa.2019.pt2.m %>%
  filter(merge.variable %in% c(1,3)) %>%
  mutate(cc = ifelse(merge.variable == 3, 1, 0)) %>%
  select(-merge.variable)

nzlu.msa.2019.pt2a <- nzlu.msa.2019.pt2.temp %>%
  filter(cc == 1) %>%
  group_by(cbsa10) %>%
  summarize(cbsaname10 = first(cbsaname10),
            cc_zri = median(zri,na.rm=T))

nzlu.msa.2019.pt2b <- nzlu.msa.2019.pt2.temp %>%
  filter(cc == 0 & !is.na(zri)) %>%
  group_by(cbsa10) %>%
  summarize(noncc_zri_max = max(zri,na.rm=T))

nzlu.msa.2019.pt2 <- nzlu.msa.2019.pt2a %>%
  left_join(nzlu.msa.2019.pt2b, "cbsa10") %>%
  select(cbsa10,
         cc_zri,
         noncc_zri_max) %>%
  mutate(zri_diff = noncc_zri_max - cc_zri,
         zri_abs_diff = abs(noncc_zri_max-cc_zri))


nzlu.msa.2019.final <- nzlu.msa.2019.pt1 %>%
  left_join(nzlu.msa.2019.pt2, "cbsa10") %>%
  mutate(zri_full = zri_median + zri_diff)

nzlu.msa.2019.final$zri_full_st <- (nzlu.msa.2019.final$zri_full - mean(nzlu.msa.2019.final$zri_full, na.rm=T))/sd(nzlu.msa.2019.final$zri_full,na.rm=T)

## check ##

nzlu.msa.2019.finlook <- nzlu.msa.2019.final %>%
  select(cbsa10,
         cbsaname10,
         zri_median,
         zri_diff,
         zri_median_up,
         zri_full,
         zri_full_st)

## output file ##

save(nzlu.msa.2019.final,
     file = paste(output_path,
                  "002_nzlu_msa_2019.Rda",
                  sep=""))

#################################
## create 2019 comparison file ##
#################################

## step 1: merge NLLUS 2019 with NZLU ##

nzlu.2019.final.fm <- nzlu.2019.final %>%
  ungroup() %>%
  select(-max_den_cat1,
         -max_den_cat2,
         -max_den_cat3,
         -max_den_cat4,
         -max_den_cat5,
         -sindex1,
         -sindex2,
         -sindex3,
         -sindex4,
         -sindex5,
         -sindex6,
         -zri,
         -zri_st,
         -zri_up,
         -zri_up_st,
         -add_index) %>%
  rename(restrict_sf_permit_nzlu = restrict_sf_permit,
         restrict_mf_permit_nzlu = restrict_mf_permit,
         limit_sf_units_nzlu = limit_sf_units,
         limit_mf_units_nzlu = limit_mf_units,
         limit_mf_dwellings_nzlu = limit_mf_dwellings,
         limit_mf_dwelling_units_nzlu = limit_mf_dwelling_units,
         min_lot_size_nzlu = min_lot_size,
         open_space_nzlu = open_space,
         inclusionary_nzlu = inclusionary,
         half_acre_less_nzlu = half_acre_less,
         half_acre_more_nzlu = half_acre_more,
         one_acre_more_nzlu = one_acre_more,
         two_acre_more_nzlu = two_acre_more,
         council_nz_nzlu = council_nz,
         planning_nz_nzlu = planning_nz,
         countybrd_nz_nzlu = countybrd_nz,
         pubhlth_nz_nzlu = pubhlth_nz,
         site_plan_nz_nzlu = site_plan_nz,
         env_rev_nz_nzlu = env_rev_nz,
         council_rz_nzlu = council_rz,
         planning_rz_nzlu = planning_rz,
         zoning_rz_nzlu = zoning_rz,
         countybrd_rz_nzlu = countybrd_rz,
         countyzone_rz_nzlu = countyzone_rz,
         townmeet_rz_nzlu = townmeet_rz,
         env_rev_rz_nzlu = env_rev_rz,
         total_nz_nzlu = total_nz,
         total_rz_nzlu = total_rz,
         maxden5_nzlu = maxden5,
         maxden4_nzlu = maxden4,
         maxden3_nzlu = maxden3,
         maxden2_nzlu = maxden2,
         maxden1_nzlu = maxden1)

nllus.2019.final.fm <- nllus.2019.final %>%
  select(-statename,
         -max_den_cat1,
         -max_den_cat2,
         -max_den_cat3,
         -max_den_cat4,
         -max_den_cat5) %>%
  rename(inclusionary_nllus = inclusionary,
         maxden5_nllus = maxden5,
         maxden4_nllus = maxden4,
         maxden3_nllus = maxden3,
         maxden2_nllus = maxden2,
         maxden1_nllus = maxden1)

nllus.nzlu <- stata.merge(nzlu.2019.final.fm,
                          nllus.2019.final.fm,
                          "GEOID")

## diagnose merge ##
table(nllus.nzlu$merge.variable, useNA="ifany")

## step 2: merge WRLD 2018 with NZLU ##

nzlu.2019.final.ids <- nzlu.2019.final %>%
  ungroup() %>%
  select(GEOID)

wrld.panel.2018.fm <- wrld.panel.2018 %>%
  rename(restrict_sf_permit_wrld = restrict_sf_permit,
         restrict_mf_permit_wrld = restrict_mf_permit,
         limit_sf_units_wrld = limit_sf_units,
         limit_mf_units_wrld = limit_mf_units,
         limit_mf_dwellings_wrld = limit_mf_dwellings,
         limit_mf_dwelling_units_wrld = limit_mf_dwelling_units,
         min_lot_size_wrld = min_lot_size,
         open_space_wrld = open_space,
         half_acre_less_wrld = half_acre_less,
         half_acre_more_wrld = half_acre_more,
         one_acre_more_wrld = one_acre_more,
         two_acre_more_wrld = two_acre_more,
         council_nz_wrld = council_nz,
         planning_nz_wrld = planning_nz,
         countybrd_nz_wrld = countybrd_nz,
         pubhlth_nz_wrld = pubhlth_nz,
         site_plan_nz_wrld = site_plan_nz,
         env_rev_nz_wrld = env_rev_nz,
         council_rz_wrld = council_rz,
         planning_rz_wrld = planning_rz,
         zoning_rz_wrld = zoning_rz,
         countybrd_rz_wrld = countybrd_rz,
         countyzone_rz_wrld = countyzone_rz,
         townmeet_rz_wrld = townmeet_rz,
         env_rev_rz_wrld = env_rev_rz,
         total_nz_wrld = total_nz,
         total_rz_wrld = total_rz)

wrld.nzlu.2019 <- stata.merge(nzlu.2019.final.ids,
                              wrld.panel.2018.fm,
                              "GEOID")

table(wrld.nzlu.2019$merge.variable, useNA="ifany")

## review non-matches ##

wrld.nzlu.nonmatches <- wrld.nzlu.2019 %>%
  filter(merge.variable ==2)

## step 3: merge matched files from steps 1 and 2 ##

## clean files for merge ##

nllus.nzlu.fm <- nllus.nzlu %>%
  filter(merge.variable == 3) %>%
  select(-merge.variable)

wrld.nzlu.2019.fm <- wrld.nzlu.2019 %>%
  filter(merge.variable == 3) %>%
  select(-merge.variable)

## merge checks ## 
nrow(nllus.nzlu.fm) == length(unique(nllus.nzlu.fm$GEOID))
class(nllus.nzlu.fm$GEOID)
range(nchar(trim(nllus.nzlu.fm$GEOID)))

nrow(wrld.nzlu.2019.fm) == length(unique(wrld.nzlu.2019.fm$GEOID))
class(wrld.nzlu.2019.fm$GEOID)
range(nchar(trim(wrld.nzlu.2019.fm$GEOID)))

## merge ##

all.samples.in.2019 <- stata.merge(nllus.nzlu.fm,
                                   wrld.nzlu.2019.fm,
                                   "GEOID")
## diagnose merge ##
table(all.samples.in.2019 $merge.variable, useNA = "ifany")

## create all.samples file ##

all.samples.2019 <- all.samples.in.2019  %>%
  filter(merge.variable == 3) %>%
  select(-merge.variable)

## create ZRI subindices from source data ##

all.samples.2019$sindex1.s <- rowSums(all.samples.2019[,c("restrict_sf_permit_nzlu",
                                                          "restrict_mf_permit_nzlu",
                                                          "limit_sf_units_nzlu",
                                                          "limit_mf_units_nzlu",
                                                          "limit_mf_dwellings_nzlu",
                                                          "limit_mf_dwelling_units_nzlu")], na.rm=TRUE)

all.samples.2019$sindex2.s <- all.samples.2019$open_space_nzlu

all.samples.2019 <- all.samples.2019 %>%
  mutate(sindex3.s = case_when(
    two_acre_more_nzlu == 1 ~ 4,
    one_acre_more_nzlu == 1 & two_acre_more_nzlu == 0 ~ 3,
    half_acre_more_nzlu == 1 & two_acre_more_nzlu == 0 & one_acre_more_nzlu == 0 ~ 2, 
    half_acre_less_nzlu == 1 & two_acre_more_nzlu == 0 & one_acre_more_nzlu == 0 & half_acre_more_nzlu == 0 ~ 1)) 

all.samples.2019$sindex4.s <- all.samples.2019$total_nz_nzlu

all.samples.2019$sindex5.s <- all.samples.2019$total_rz_nzlu

all.samples.2019 <- all.samples.2019 %>%
  mutate(sindex6.s = case_when(
    maxden5_nzlu == 1 ~ 1,
    maxden4_nzlu == 1 ~ 2,
    maxden3_nzlu == 1 ~ 3,
    maxden2_nzlu == 1 ~ 4,
    maxden1_nzlu == 1 ~ 5))

all.samples.2019$sindex7.s <- all.samples.2019$inclusionary_nzlu


## create ZRI subindices from comparison data ##

all.samples.2019$sindex1.c <- rowSums(all.samples.2019[,c("restrict_sf_permit_wrld",
                                                          "restrict_mf_permit_wrld",
                                                          "limit_sf_units_wrld",
                                                          "limit_mf_units_wrld",
                                                          "limit_mf_dwellings_wrld",
                                                          "limit_mf_dwelling_units_wrld")], na.rm=TRUE)

all.samples.2019$sindex2.c <- all.samples.2019$open_space_wrld

all.samples.2019 <- all.samples.2019 %>%
  mutate(sindex3.c = case_when(
    two_acre_more_wrld == 1 ~ 4,
    one_acre_more_wrld == 1 & two_acre_more_wrld == 0 ~ 3,
    half_acre_more_wrld == 1 & two_acre_more_wrld == 0 & one_acre_more_wrld == 0 ~ 2, 
    half_acre_less_wrld == 1 & two_acre_more_wrld == 0 & one_acre_more_wrld == 0 & half_acre_more_wrld == 0 ~ 1)) 

all.samples.2019$sindex4.c <- all.samples.2019$total_nz_wrld

all.samples.2019$sindex5.c <- all.samples.2019$total_rz_wrld

all.samples.2019 <- all.samples.2019 %>%
  mutate(sindex6.c = case_when(
    maxden5_nllus == 1 ~ 1,
    maxden4_nllus == 1 ~ 2,
    maxden3_nllus == 1 ~ 3,
    maxden2_nllus == 1 ~ 4,
    maxden1_nllus == 1 ~ 5))

all.samples.2019$sindex7.c <- all.samples.2019$inclusionary_nllus

## create zri ##
all.samples.2019.final <- create.zri.sc2(all.samples.2019)

## output file ##

save(all.samples.2019.final,
     file = paste(output_path,
                  "002_all_place_2019.Rda",
                  sep=""))


###########################################
## assign comparison 2019 places to MSAs ##
###########################################

## merge checks ## 
nrow(all.samples.2019.final) == length(unique(all.samples.2019.final$GEOID))
class(all.samples.2019.final$GEOID)
range(nchar(trim(all.samples.2019.final$GEOID)))

nrow(ptm.2010.rd) == length(unique(ptm.2010.rd$GEOID))
class(ptm.2010.rd$GEOID)
range(nchar(trim(ptm.2010.rd$GEOID)))

## merge data frames ## 
all.samples.2019.msa.merge <- stata.merge(all.samples.2019.final,
                                          ptm.2010.rd,
                                          "GEOID")

## check merge ## 
table(all.samples.2019.msa.merge$merge.variable)

## output non-matches eligible for match with county subs ##
no.msa.all.samples.2019 <- all.samples.2019.msa.merge %>%
  filter(merge.variable ==1) %>%
  select(-placefp,
         -stab,
         -placenm,
         -cbsa10,
         -cbsaname10,
         -pop10,
         -afact,
         -merge.variable)

## keep matches ## 
all.samples.msa.2019.keep1 <- all.samples.2019.msa.merge %>%
  mutate(afact_num = as.numeric(afact)) %>%
  filter(merge.variable ==3 & afact_num >= 0.01) %>%
  select(-placefp,
         -stab,
         -placenm,
         -pop10,
         -afact,
         -merge.variable)

## check for dups ## 
## these are places that span multiple MSAs ##
all.samples.msa.2019.dupcheck1 <- all.samples.msa.2019.keep1 %>%
  group_by(GEOID) %>%
  summarize(n=n()) %>%
  filter(n>1)


## now, county subs ## 

## merge checks ##
nrow(cstm.2010.rd) == length(unique(cstm.2010.rd$GEOID))
class(cstm.2010.rd$GEOID)
range(nchar(trim(cstm.2010.rd$GEOID)))

nrow(no.msa.all.samples.2019) == length(unique(no.msa.all.samples.2019$GEOID))
class(no.msa.all.samples.2019$GEOID)
range(nchar(trim(no.msa.all.samples.2019$GEOID)))

## merge data frames ## 
all.samples.2019.cs.merge <- stata.merge(no.msa.all.samples.2019,
                                         cstm.2010.rd,
                                         "GEOID")

## check merge ##
table(all.samples.2019.cs.merge$merge.variable)

## keep matches ## 
all.samples.msa.2019.keep2 <- all.samples.2019.cs.merge %>%
  mutate(afact_num = as.numeric(afact)) %>%
  filter(merge.variable ==3 & afact_num >= 0.01) %>%
  select(-county,
         -cousubfp,
         -cntyname,
         -cousubnm,
         -pop10,
         -afact,
         -state,
         -merge.variable)

## check for dups ## 
## these are places that span multiple MSAs ##
all.samples.msa.2019.dupcheck2 <- all.samples.msa.2019.keep2 %>%
  group_by(GEOID) %>%
  summarize(n=n()) %>%
  filter(n>1)

## append the two matched dataframes ##

all.samples.2019.wmsas <- rbind(all.samples.msa.2019.keep1,
                                all.samples.msa.2019.keep2)

## create MSA level file ## 

all.samples.msa.2019.final <- all.samples.2019.wmsas %>%
  group_by(cbsa10) %>%
  summarize(cbsaname10 = cbsaname10[which(cbsaname10 != "")[1]],
            responses = n(),
            across(restrict_sf_permit_nzlu:total_rz_wrld, ~mean(.x, na.rm=T)),
            across(sindex1.s:add_index.c, ~median(.x, na.rm=T))) %>%
  select(-zri_s_st,
         -zri_c_st)

## re-standardize indices ##

all.samples.msa.2019.final$zri_s_st <- (all.samples.msa.2019.final$zri_s - mean(all.samples.msa.2019.final$zri_s, na.rm=T))/sd(all.samples.msa.2019.final$zri_s,na.rm=T)
all.samples.msa.2019.final$zri_c_st <- (all.samples.msa.2019.final$zri_c - mean(all.samples.msa.2019.final$zri_c, na.rm=T))/sd(all.samples.msa.2019.final$zri_c,na.rm=T)

            
## output file ##

save(all.samples.msa.2019.final,
     file = paste(output_path,
                  "002_all_msa_2019.Rda",
                  sep=""))



## END OF PROGRAM ##


#sink()
