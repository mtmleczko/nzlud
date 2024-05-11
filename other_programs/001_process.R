########################################################
## PROGRAM NAME: 001_process.R                        ##
## AUTHOR: MATT MLECZKO                               ##
## DATE CREATED: 10/08/2020                           ##
## INPUTS:                                            ##
##    ufips_recode.csv                                ##
##    All2010places.csv                               ##
##    Cousub_comparability.csv                        ##
##    placetocbsa_2010.csv                            ##
##    countysubtocbsa_2010.csv                        ##
##    all-geocodes-v2019.csv                          ##               
##    msa_delineation_2020.xls                        ##
##    WHARTON LAND REGULATION DATA_1_24_2008.dta      ##
##    WRLURI_01_15_2020.dta                           ##
##    2003_NLLUS_Data.csv                             ##
##    2019_NLLUS_Data.csv                             ##
##    *_fin.xls                                       ##
##    manual_codes.xls                                ##
##    zoning.codes.xlsx                               ##
##    zc_adds.csv                                     ##
##    sf_msa_adds.xls                                 ##
##    houston_msa_adds.xls                            ##
##    tsout.csv                                       ##
##                                                    ##
## OUTPUTS:                                           ##
##    001_wrld_2006.Rda                               ##
##    001_wrld_2018.Rda                               ##
##    001_wrld_panel_2018.Rda                         ##
##    001_wrld_panel.csv                              ##
##    001_nllus_2003.Rda                              ##
##    001_nllus_2019.Rda                              ##
##    001_zd_nonmatches.Rda                           ##
##    001_nzlu_2019.Rda                               ##
##    001_ptm_2010.Rda                                ##
##    001_cstm_2010.Rda                               ##
##                                                    ##
## PURPOSE: Process input data                        ##
##                                                    ##
## LIST OF UPDATES:                                   ##
## 05/04/2021: Added NLLUS data                       ##
## 12/28/2021: Updated code for new input data        ##
########################################################

#log <- file("path to programs here/001_process.txt")
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

## FIPS codes ##
ufips.recode <- read.csv("ufips_recode.csv")

## place FIPS ##
allpl.2010 <- read.csv("All2010places.csv",
                       header = T,
                       stringsAsFactors = F)

## cosub FIPS ## 
allcs.2010 <- read.csv("Cousub_comparability.csv",
                       header = T,
                       stringsAsFactors = F)

## 2019 GEOCODES ## 
p2019.input <- read.csv("all-geocodes-v2019.csv",
                        header = T,
                        stringsAsFactors = F)

## input file with timestamps (user may choose to skip this) ##

timestamps <- read.csv("tsout.csv",
                       header=F)


## MSA files ##

## 2000 to 2010 MSA - Place ##
place.to.msa.2010 <- read.csv("placetocbsa_2010.csv",
                              header = T,
                              stringsAsFactors = F)

## 2000 to 2010 MSA - county sub ##
countysub.to.msa.2010 <- read.csv("countysubtocbsa_2010.csv",
                                  header = T,
                                  stringsAsFactors = F)

## 2020 MSA delineation file ## 
## need this because the place.to.msa file is missing some metro areas ##
msa.del.2020 <- read_excel("msa_delineation_2020.xls")

## Wharton Residential Land Use Regulation Data ##
wrld.2006.in <- read_dta("WHARTON LAND REGULATION DATA_1_24_2008.dta")
wrld.2018.in <- read_dta("WRLURI_01_15_2020.dta")

## NLLUS ## 
nllus.2003.in <- read.csv("2003_NLLUS_Data.csv")
nllus.2019.in <- read.csv("2019_NLLUS_Data.csv")

## source data ##
## this code reflects input data as a series of .xls files ##
## user may change this to one file ## 

zfile.list <- list.files(pattern='*_fin.xls')
zlist <- lapply(zfile.list, read_excel)
zd.2019 <- bind_rows(zlist)

manual.codes <- read_excel("manual_codes.xls")
manual.codes$muni <- "PA_Midland.txt"
zoning.codes <- read_excel("zoning.codes.xlsx") 
zc.adds <- read.csv("zc_adds.csv")
sf <- read_excel("sf_msa_adds.xls")
houston <- read_excel("houston_msa_adds.xls")

#####################################
## initial processing of FIPS data ##
#####################################

## fix the missing 0s in allpl.2010 ## 
allpl.2010$STATEFP00 <- str_pad(allpl.2010$STATEFP00, 2, pad = "0")
allpl.2010$STATEFP10 <- str_pad(allpl.2010$STATEFP10, 2, pad = "0")

allpl.2010$PLACEFP00 <- str_pad(allpl.2010$PLACEFP00, 5, pad = "0")
allpl.2010$PLACEFP10 <- str_pad(allpl.2010$PLACEFP10, 5, pad = "0")

## fix the missing 0s in allcs.2010 ## 
allcs.2010$STATEFP00 <- str_pad(allcs.2010$STATEFP00, 2, pad = "0")
allcs.2010$STATEFP10 <- str_pad(allcs.2010$STATEFP10, 2, pad = "0")

allcs.2010$COUNTYFP00 <- str_pad(allcs.2010$COUNTYFP00, 3, pad = "0")
allcs.2010$COUNTYFP10 <- str_pad(allcs.2010$COUNTYFP10, 3, pad = "0")

allcs.2010$COUSUBFP00 <- str_pad(allcs.2010$COUSUBFP00, 5, pad = "0")
allcs.2010$COUSUBFP10 <- str_pad(allcs.2010$COUSUBFP10, 5, pad = "0")

## process further ## 

## places ##
allpl.2010.pr <- allpl.2010 %>%
  filter((STATEFP00 != "" & 
          PLACEFP00 != "") | NAMELSAD == "Elko New Market city") %>%
  rename(fullname = NAMELSAD) %>%
  select(fullname,
         STATEFP00,
         STATEFP10,
         PLACEFP00,
         PLACEFP10) %>%
  mutate(place00 = paste(STATEFP00,PLACEFP00, sep=""),
         place10 = paste(STATEFP10,PLACEFP10, sep=""),
         GEOID = paste(STATEFP10,PLACEFP10, sep=""))

## cosubs ##
allcs.2010.pr <- allcs.2010 %>%
  filter(STATEFP00 != "" & 
         COUSUBFP00 != "") %>%
  rename(fullname = NAMELSAD10) %>%
  select(fullname,
         STATEFP00,
         STATEFP10,
         COUSUBFP00,
         COUSUBFP10) %>%
  mutate(cosub00 = paste(STATEFP00,COUSUBFP00, sep=""),
         cosub10 = paste(STATEFP10,COUSUBFP10, sep=""),
         GEOID = paste(STATEFP10,COUSUBFP10, sep=""))

## load data with correct FIPS prefix, change to character
ufips.recode$sfp <- str_pad(ufips.recode$sfp, 2, pad = "0")
ufips.recode$state <- as.character(ufips.recode$state)
ufips.recode$statename <- as.character(ufips.recode$statename)

#######################
## process WRLD 2006 ##
#######################

## drop problem munis ## 

# 218238 (Elkhorn, EN) was annexed by Omaha in 2007 ##
## 2703761492 (South St. Paul, MN) is duplicated and this entry is missing info ##
## 2705310918 (Chanhassen, MN) is duplicated and this entry is missing info ##
## 2716369970 (White Bear Lake City, MN) is duplicated and this entry is missing info ##

wrld.2006.keep <- wrld.2006.in %>%
  filter(id %notin% c("218238",
                      "2703761492",
                      "2705310918",
                      "2716369970"))

## keep non-duplicated munis ##

wrld.2006.st <- wrld.2006.keep %>%
  filter(id %notin% c("124256",
                      "182452",
                      "191844",
                      "176375",
                      "176372",
                      "173108",
                      "173109")) 

## clean duplicated munis ##

wrld.2006.tc <- wrld.2006.keep %>%
  filter(id %in% c("124256",
                   "182452",
                   "191844",
                   "176375",
                   "176372",
                   "173108",
                   "173109"))

## fix North Versailles, PA FIPS code ##
wrld.2006.tc$ufips[wrld.2006.tc$id == "176375"] <- "55488"
wrld.2006.tc$ufips[wrld.2006.tc$id == "176372"] <- "55488"

## numeric info ##

wrld.2006.tc.grouped1 <- wrld.2006.tc %>%
  group_by(state, statename, ufips) %>%
  summarize_if(is.character, first)

## non-numeric info ##

wrld.2006.tc.grouped2 <- wrld.2006.tc %>%
  group_by(state, statename, ufips) %>%
  summarize_if(is.numeric, mean, na.rm = TRUE)

## combine the info ##
wrld.2006.dd <- stata.merge(wrld.2006.tc.grouped1,
                            wrld.2006.tc.grouped2,
                            c("state","statename","ufips"))

## fix Putnam, CT info ##
wrld.2006.dd$name[wrld.2006.dd$ufips == "62710"] <- "Putnam Town, CT"
wrld.2006.dd$namene[wrld.2006.dd$ufips == "62710"] <- "Putnam Town, CT"

## check the merge ##
table(wrld.2006.dd$merge.variable, useNA = "ifany")

wrld.2006.dd <- select(wrld.2006.dd, -merge.variable)

## add de-duplicated munis back to data ##

wrld.2006.cb <- rbind(wrld.2006.st,
                      wrld.2006.dd)

## now, fix the mistakes in the WRLD ##

wrld.2006.cb$name[wrld.2006.cb$id == "195802"] <- "Town and Country"
wrld.2006.cb$name[wrld.2006.cb$id == "182914"] <- "Hialeah Gardens"
wrld.2006.cb$name[wrld.2006.cb$id == "31752"] <- "Green Township, OH"
wrld.2006.cb$type[wrld.2006.cb$id == "5509323525"] <- "Village"
wrld.2006.cb$name[wrld.2006.cb$id == "191312"] <- "Waunakee Village, WI"
wrld.2006.cb$type[wrld.2006.cb$id == "191312"] <- "Village"
wrld.2006.cb$type[wrld.2006.cb$id == "196754"] <- "City"
wrld.2006.cb$type[wrld.2006.cb$id == "2702572040"] <- "City"
wrld.2006.cb$name[wrld.2006.cb$id == "2702572040"] <- "Wyoming City"
wrld.2006.cb$type[wrld.2006.cb$id == "180865"] <- "Town"
wrld.2006.cb$type[wrld.2006.cb$id == "327050"] <- "Town"

## pad the four-character ufips values with a 0 to be 5 characters
wrld.2006.cb$ufips <- str_pad(wrld.2006.cb$ufips, 5, pad = "0")

## create summary zoning process vars ## 

wrld.2006.cb$total_nz <- rowSums(wrld.2006.cb[,c("council_norez", 
                                                 "commission_norez",
                                                 "cntyboard_norez",
                                                 "envboard_norez",
                                                 "publhlth_norez",
                                                 "dsgnrev_norez")])

wrld.2006.cb$total_rz <- rowSums(wrld.2006.cb[,c("council", 
                                                 "commission",
                                                 "loczoning",
                                                 "cntyboard",
                                                 "cntyzoning",
                                                 "envboard",
                                                 "town_meet")])



## convert 2000 place code into 2010 place code ## 

## pre-merge checks ##
wrld.2006.cb$state <- trim(wrld.2006.cb$state)
class(wrld.2006.cb$state)
class(wrld.2006.cb$statename)
range(nchar(trim(wrld.2006.cb$state)))
range(nchar(trim(wrld.2006.cb$statename)))

ufips.recode$state <- trim(ufips.recode$state)
class(ufips.recode$state)
class(ufips.recode$statename)
range(nchar(trim(ufips.recode$state)))
range(nchar(trim(ufips.recode$statename)))

## merge the FIPS prefix onto the lrd data
wrld.2006.ufips.merge <- stata.merge(wrld.2006.cb,
                                     ufips.recode,
                                     c("state","statename"))

## diagnose merge ##
table(wrld.2006.ufips.merge$merge.variable, useNA = "ifany")

## keep matches ##
wrld.2006.pr <- wrld.2006.ufips.merge %>%
  filter(merge.variable == 3) %>%
  select(-merge.variable)

## manually fix incorrect FIPS codes ## 
wrld.2006.pr$ufips[wrld.2006.pr$name == "National City City, CA"] <- "50398"
wrld.2006.pr$ufips[wrld.2006.pr$name == "Wyoming City"] <- "72022"
wrld.2006.pr$ufips[wrld.2006.pr$name == "Edison, NJ"] <- "20230"
wrld.2006.pr$ufips[wrld.2006.pr$name == "Irvington Township, NJ"] <- "34450"
wrld.2006.pr$ufips[wrld.2006.pr$name == "Lyndhurst Township, NY"] <- "42090"
wrld.2006.pr$ufips[wrld.2006.pr$name == "Millburn Township, NJ"] <- "46380"
wrld.2006.pr$ufips[wrld.2006.pr$name == "Orange Township City, NJ"] <- "13045"
wrld.2006.pr$ufips[wrld.2006.pr$name == "Rochelle Park Township, NJ"] <- "63990"
wrld.2006.pr$ufips[wrld.2006.pr$name == "Springfield Township, NJ"] <- "70020"
wrld.2006.pr$ufips[wrld.2006.pr$name == "Union Township, NJ"] <- "74480"
wrld.2006.pr$ufips[wrld.2006.pr$name == "West Milford Township, NJ"] <- "79460"
wrld.2006.pr$ufips[wrld.2006.pr$name == "Hampton Township, PA"] <- "32328"
wrld.2006.pr$ufips[wrld.2006.pr$name == "Harrison Township, PA"] <- "32832"
wrld.2006.pr$ufips[wrld.2006.pr$name == "Town of McCandless, PA"] <- "45900"
wrld.2006.pr$ufips[wrld.2006.pr$name == "North Versailles Township, PA"] <- "55488"
wrld.2006.pr$ufips[wrld.2006.pr$name == "Bristol Town, RI"] <- "09280"
wrld.2006.pr$ufips[wrld.2006.pr$name == "Chester Town, CT"] <- "14300"
wrld.2006.pr$ufips[wrld.2006.pr$name == "Stratford Town, CT"] <- "74190"
wrld.2006.pr$ufips[wrld.2006.pr$name == "Port Saint Lucie, FL"] <- "58715"
wrld.2006.pr$ufips[wrld.2006.pr$name == "Colona City, IL"] <- "15664"
wrld.2006.pr$ufips[wrld.2006.pr$name == "Dedham, Ma"] <- "16495"
wrld.2006.pr$ufips[wrld.2006.pr$name == "Reading Town, MA"] <- "56130"
wrld.2006.pr$ufips[wrld.2006.pr$name == "Marquette Township, MI"] <- "51920"
wrld.2006.pr$ufips[wrld.2006.pr$name == "Union Township, MI"] <- "81340"
wrld.2006.pr$ufips[wrld.2006.pr$name == "South St. Paul City, MN"] <- "61492"
wrld.2006.pr$ufips[wrld.2006.pr$name == "Milton Town, NH"] <- "48660"
wrld.2006.pr$ufips[wrld.2006.pr$name == "Mamaroneck, NY"] <- "44842"
wrld.2006.pr$ufips[wrld.2006.pr$name == "West Seneca Town, NY"] <- "80918"
wrld.2006.pr$ufips[wrld.2006.pr$name == "Washington City, OH"] <- "81214"
wrld.2006.pr$ufips[wrld.2006.pr$name == "Chadds Ford Township, PA"] <- "12442"
wrld.2006.pr$ufips[wrld.2006.pr$name == "Monroeville Municipality, PA"] <- "52330"
wrld.2006.pr$ufips[wrld.2006.pr$name == "Batesburg-Leesville Town, SC"] <- "04300"
wrld.2006.pr$ufips[wrld.2006.pr$name == "Abingdon Town, VA"] <- "00148"
wrld.2006.pr$ufips[wrld.2006.pr$name == "Rib Mountain Town, WI"] <- "67325"
wrld.2006.pr$ufips[wrld.2006.pr$name == "Honolulu City, HI"] <- "71550"

## pad the FIPS variable with the state-specific prefix
wrld.2006.pr$place00 <- as.character(paste(wrld.2006.pr$sfp,
                                           wrld.2006.pr$ufips,
                                           sep = ""))

## check the first few observations
wrld.2006.pr[1:10, c("ufips", "sfp", "place00")] 

## process further ## 

wrld.2006.rd <- wrld.2006.pr %>%
  select(statename,
         ufips,
         name,
         sfp,
         place00)

## merge checks ## 

nrow(allpl.2010.pr) == length(unique(allpl.2010.pr$place00))
nrow(allpl.2010.pr) == length(unique(allpl.2010.pr$place10))
class(allpl.2010.pr$place00)
range(nchar(trim(allpl.2010.pr$place00)))

nrow(wrld.2006.rd) == length(unique(trim(wrld.2006.rd$place00)))
class(wrld.2006.rd$place00)
range(nchar(trim(wrld.2006.rd$place00)))

## merge place10 codes ## 

wrld.2006.up <- stata.merge(wrld.2006.rd,
                            allpl.2010.pr,
                            "place00")

## merge diagnosis ##
table(wrld.2006.up$merge.variable, useNA = "ifany")

## non-matches need different data ##

no.place.wrld.2006 <- wrld.2006.up %>%
  filter(merge.variable == 1) %>%
  select(place00,
         statename,
         ufips,
         name,
         sfp) %>%
  rename(cosub00 = place00)

## merge checks ## 

nrow(allcs.2010.pr) == length(unique(allcs.2010.pr$cosub00))
nrow(allcs.2010.pr) == length(unique(allcs.2010.pr$cosub10))
class(allcs.2010.pr$cosub00)
range(nchar(trim(allcs.2010.pr$cosub00)))

nrow(no.place.wrld.2006) == length(unique(trim(no.place.wrld.2006$cosub00)))
class(no.place.wrld.2006$cosub00)
range(nchar(trim(no.place.wrld.2006$cosub00)))

## merge cosubs ## 

wrld.2006.cosubs <- stata.merge(no.place.wrld.2006,
                                allcs.2010.pr,
                                "cosub00")

## check merge ## 
table(wrld.2006.cosubs$merge.variable)

## what's going on with these nonmatches? ##
no.cs.wrld.2006 <- wrld.2006.cosubs %>%
  filter(merge.variable ==1)

## manual fixes ## 
wrld.2006.cosubs$STATEFP10[wrld.2006.cosubs$name == "New Market City"] <- "27"
wrld.2006.cosubs$COUSUBFP10[wrld.2006.cosubs$name == "New Market City"] <- "18662"
wrld.2006.cosubs$cosub10[wrld.2006.cosubs$name == "New Market City"] <- "2718662"

wrld.2006.cosubs$STATEFP10[wrld.2006.cosubs$name == "Honolulu City, HI"] <- "15"
wrld.2006.cosubs$COUSUBFP10[wrld.2006.cosubs$name == "Honolulu City, HI"] <- "90810"
wrld.2006.cosubs$cosub10[wrld.2006.cosubs$name == "Honolulu City, HI"] <- "1590810"

## finalize 2006 WRLD ## 

## initial matches on place FIPS ##

wrld.2006.keep1 <- wrld.2006.up %>%
  filter(merge.variable == 3) %>%
  select(place00, 
         place10) %>%
  rename(geoid00 = place00,
         geoid10 = place10)

## additional matches on cosub FIPS ## 

wrld.2006.keep2 <- wrld.2006.cosubs %>%
  filter(merge.variable == 3 | cosub00 == "2745736") %>%
  select(cosub00,
         cosub10) %>%
  rename(geoid00 = cosub00,
         geoid10 = cosub10)

## append the data frames ## 

wrld.2006.final.ids <- rbind(wrld.2006.keep1,
                             wrld.2006.keep2)

## create the final WRLD 06 data frame ## 

## merge checks ## 

nrow(wrld.2006.final.ids) == length(unique(wrld.2006.final.ids$geoid00))
class(wrld.2006.final.ids$geoid00)
range(nchar(trim(wrld.2006.final.ids$geoid00)))

## create duplicate var for merge ## 
wrld.2006.pr$geoid00 <- wrld.2006.pr$place00

nrow(wrld.2006.pr) == length(unique(wrld.2006.pr$geoid00))
class(wrld.2006.pr$geoid00)
range(nchar(trim(wrld.2006.pr$geoid00)))

wrld.2006.temp <- stata.merge(wrld.2006.final.ids,
                              wrld.2006.pr,
                              "geoid00")

## merge check ## 
table(wrld.2006.temp$merge.variable)

## non-matching observation is Honolulu, HI ##
## Honolulu CDP was split, which is causing the issue ##
wrld.2006.nm <- wrld.2006.temp %>%
  filter(merge.variable == 2) %>%
  select(statename, name, type) 

print(wrld.2006.nm)

## final GEOID corrections ##

## Honolulu, HI split into different Census designations ## 

wrld.2006.temp$geoid10[wrld.2006.temp$name == "Honolulu City, HI"]<- "1571550"

## Seneca Falls Village, NY absorbed by Seneca Falls Town, NY in 2010 ##

wrld.2006.temp$geoid10[wrld.2006.temp$name == "Seneca Falls Village, NY"]<- "3666333"

## Princeton NJ township and borough consolidated in 2013 ##

wrld.2006.temp$geoid10[wrld.2006.temp$name == "Princeton Township, NJ"]<- "3460900"

## Sanford Town, ME becomes Sanford City, ME in ##

wrld.2006.temp$geoid10[wrld.2006.temp$name == "Sanford Town, ME"]<- "2365725"


## create final data ## 

wrld.2006.final <- wrld.2006.temp %>%
  select(geoid10,
         statename,
         name,
         type,
         sfupermitlimit,
         mfupermitlimit,
         sfuconstrlimit,
         mfuconstrlimit,
         mfudwelllimit,
         mfudwellunitlimit,
         minlotsize,
         minlotsize_lhalfacre,
         minlotsize_mhalfacre,
         minlotsize_oneacre,
         minlotsize_twoacres,
         affordable,
         OSI,
         total_nz,
         total_rz) %>%
  rename(GEOID = geoid10,
         restrict_sf_permit = sfupermitlimit,
         restrict_mf_permit = mfupermitlimit,
         limit_sf_units = sfuconstrlimit,
         limit_mf_units = mfuconstrlimit,
         limit_mf_dwellings = mfudwelllimit,
         limit_mf_dwelling_units = mfudwellunitlimit,
         min_lot_size = minlotsize,
         half_acre_less = minlotsize_lhalfacre,
         half_acre_more = minlotsize_mhalfacre,
         one_acre_more = minlotsize_oneacre,
         two_acre_more = minlotsize_twoacres,
         inclusionary_wrld = affordable,
         open_space = OSI)

## reformat min lot size variables ## 

wrld.2006.final$one_acre_more <- ifelse(wrld.2006.final$two_acre_more==1,
                                        0,
                                        wrld.2006.final$one_acre_more)

wrld.2006.final$half_acre_more <- ifelse(wrld.2006.final$two_acre_more ==1 | wrld.2006.final$one_acre_more ==1,
                                         0,
                                         wrld.2006.final$half_acre_more)

wrld.2006.final$half_acre_less <- ifelse(wrld.2006.final$two_acre_more ==1 | wrld.2006.final$one_acre_more ==1 | wrld.2006.final$half_acre_more ==1,
                                         0,
                                         wrld.2006.final$half_acre_less)

## tabs ## 

prop.table(table(wrld.2006.final$half_acre_less, useNA = "ifany"))
prop.table(table(wrld.2006.final$half_acre_more, useNA = "ifany"))
prop.table(table(wrld.2006.final$one_acre_more, useNA = "ifany"))
prop.table(table(wrld.2006.final$two_acre_more, useNA = "ifany"))

## save final data ##

save(wrld.2006.final,
     file = paste(output_path,
                  "001_wrld_2006.Rda",
                  sep=""))

#######################
## process WRLD 2018 ##
#######################

## first, wrld18 ##

wrld.2018.final <- wrld.2018.in %>%
  select(GEOID,
         statecode_str,
         communityname18,
         state,
         q8a18,
         q8b18,
         q8c18,
         q8d18,
         q8e18,
         q8f18,
         q718,
         q7b18,
         q9b18,
         q4_1a18,
         q4_1b18,
         q4_1c18,
         q4_1d18,
         q4_1e18,
         q4_1f18,
         q4_1g18,
         q4_1h18,
         q4_1i18,
         q4_1j18,
         q4_2k18,
         q4_2l18,
         q4_2m18,
         q4_2n18,
         q4_2o18,
         q4_2p18,
         q4_2q18,
         q4_2r18,
         q4_2s18,
         q4_2t18,
         WRLURI18) %>%
  rename(GEOID_old = GEOID) %>%
  mutate(geo10 = substr(GEOID_old, 
                        nchar(GEOID_old)-4,
                        nchar(GEOID_old)),
         GEOID = paste(statecode_str,
                       geo10,
                       sep=""),
         restrict_sf_permit =  case_when(q8a18 == 2 ~ 0, 
                                         q8a18 == 1 ~ 1),
         restrict_mf_permit = case_when(q8b18 == 2 ~ 0, 
                                        q8b18 == 1 ~ 1), 
         limit_sf_units = case_when(q8c18 == 2 ~ 0, 
                                    q8c18 == 1 ~ 1), 
         limit_mf_units = case_when(q8d18 == 2 ~ 0, 
                                    q8d18 == 1 ~ 1), 
         limit_mf_dwellings = case_when(q8e18 == 2 ~ 0, 
                                        q8e18 == 1 ~ 1), 
         limit_mf_dwelling_units = case_when(q8f18 == 2 ~ 0, 
                                             q8f18 == 1 ~ 1), 
         min_lot_size = case_when(q718 == 2 ~ 0,
                                  q718 == 1 ~ 1),
         open_space = case_when(q9b18 == 2 ~ 0,
                                q9b18 == 1 ~ 1),
         council_nz = case_when(q4_1c18 %in% c(1,2) ~ 1,
                                q4_1c18 == 3 ~ 0),
         planning_nz = case_when(q4_1a18 %in% c(1,2) ~ 1,
                                 q4_1a18 == 3 ~ 0), 
         countybrd_nz = case_when(q4_1d18 %in% c(1,2) ~ 1,
                                  q4_1d18 == 3 ~ 0),
         pubhlth_nz = case_when(q4_1h18 %in% c(1,2) ~ 1,
                                q4_1h18 == 3 ~ 0),
         site_plan_nz = case_when(q4_1i18 %in% c(1,2) ~ 1,
                                  q4_1i18 == 3 ~ 0),
         env_rev_nz = case_when(q4_1f18 %in% c(1,2) ~ 1,
                                q4_1f18 == 3 ~ 0),
         council_rz = case_when(q4_2m18 %in% c(1,2) ~ 1,
                                q4_2m18 == 3 ~ 0),
         planning_rz = case_when(q4_2k18 %in% c(1,2) ~ 1,
                                 q4_2k18 == 3 ~ 0),
         zoning_rz = case_when(q4_2l18 %in% c(1,2) ~ 1,
                               q4_2l18 == 3 ~ 0),
         countybrd_rz = case_when(q4_2n18 %in% c(1,2) ~ 1,
                                  q4_2n18 == 3 ~ 0),
         countyzone_rz = case_when(q4_2o18 %in% c(1,2) ~ 1,
                                   q4_2o18 == 3 ~ 0),
         townmeet_rz = case_when(q4_2q18 %in% c(1,2) ~ 1,
                                 q4_2q18 == 3 ~ 0),
         env_rev_rz = case_when(q4_2p18 %in% c(1,2) ~ 1,
                                q4_2p18 == 3 ~ 0),
         half_acre_less = case_when(q7b18 == 1 ~ 1,
                                    q7b18 %in% c(2,3,4) ~ 0),
         half_acre_more = case_when(q7b18 == 2 ~ 1,
                                    q7b18 %in% c(1,3,4) ~ 0),
         one_acre_more = case_when(q7b18 == 3 ~ 1,
                                   q7b18 %in% c(1,2,4) ~ 0),
         two_acre_more = case_when(q7b18 == 4 ~ 1,
                                   q7b18 %in% c(1,2,3) ~ 0)) %>%
  select(GEOID,
         communityname18,
         state,
         restrict_sf_permit,
         restrict_mf_permit,
         limit_sf_units,
         limit_mf_units,
         limit_mf_dwellings,
         limit_mf_dwelling_units,
         min_lot_size,
         open_space,
         council_nz,
         planning_nz,
         countybrd_nz,
         pubhlth_nz,
         site_plan_nz,
         env_rev_nz,
         council_rz,
         planning_rz,
         zoning_rz,
         countybrd_rz,
         countyzone_rz,
         townmeet_rz,
         env_rev_rz,
         half_acre_less,
         half_acre_more,
         one_acre_more,
         two_acre_more,
         WRLURI18)

wrld.2018.final$total_nz <- rowSums(wrld.2018.final[,c("council_nz",
                                                       "planning_nz", 
                                                       "countybrd_nz",
                                                       "pubhlth_nz",
                                                       "site_plan_nz",
                                                       "env_rev_nz")])

wrld.2018.final$total_rz <- rowSums(wrld.2018.final[,c("council_rz",
                                                       "planning_rz", 
                                                       "zoning_rz",
                                                       "countybrd_rz",
                                                       "countyzone_rz",
                                                       "townmeet_rz",
                                                       "env_rev_rz")])

## export file ## 
save(wrld.2018.final,
     file = paste(output_path,
                  "001_wrld_2018.Rda",
                  sep=""))

## now, the panel data set of munis in both the 2006 and 2018 samples ##

## merge checks ## 

nrow(wrld.2018.final) == length(unique(wrld.2018.final$GEOID))
range(nchar(trim(wrld.2018.final$GEOID)))
class(wrld.2018.final$GEOID)

nrow(wrld.2006.final) == length(unique(wrld.2006.final$GEOID))
range(nchar(trim(wrld.2006.final$GEOID)))
class(wrld.2006.final$GEOID)

## merge and see how many places with n = 2 ##

panel <- stata.merge(wrld.2006.final,
                     wrld.2018.final,
                     "GEOID")

## merge diagnosis ## 
table(panel$merge.variable, useNA = "ifany")

## panel places ##
wrld.panel.places <- panel %>%
  filter(merge.variable == 3) %>%
  select(-merge.variable)

## export file ## 
write.csv(wrld.panel.places,
          file = paste(output_path,
                       "001_wrld_panel.csv",
                       sep=""))

## collect 2018 data for munis from WRLD 06 ## 
wrld.panel.2018 <- wrld.2018.final %>%
  filter(GEOID %in% wrld.panel.places$GEOID)


## ensure correct FIPS codes ##

## merge checks ## 

nrow(allpl.2010.pr) == length(unique(allpl.2010.pr$GEOID))
class(allpl.2010.pr$GEOID)
range(nchar(trim(allpl.2010.pr$GEOID)))

nrow(wrld.2018.final) == length(unique(trim(wrld.2018.final$GEOID)))
class(wrld.2018.final$GEOID)
range(nchar(trim(wrld.2018.final$GEOID)))

## merge check 1 ## 

wrld.2018.fips.c1 <- stata.merge(wrld.panel.2018,
                                 allpl.2010.pr,
                                 "GEOID")

## merge diagnosis ##
table(wrld.2018.fips.c1$merge.variable, useNA = "ifany")

## non-matches need different data ##

no.place.wrld.2018.c1 <- wrld.2018.fips.c1 %>%
  filter(merge.variable == 1) %>%
  select(GEOID)

## merge checks ## 

nrow(allcs.2010.pr) == length(unique(allcs.2010.pr$GEOID))
class(allcs.2010.pr$GEOID)
range(nchar(trim(allcs.2010.pr$GEOID)))

nrow(no.place.wrld.2018.c1) == length(unique(trim(no.place.wrld.2018.c1$GEOID)))
class(no.place.wrld.2018.c1$GEOID)
range(nchar(trim(no.place.wrld.2018.c1$GEOID)))

## merge check 2 ## 

wrld.2018.fips.c2 <- stata.merge(no.place.wrld.2018.c1,
                                 allcs.2010.pr,
                                 "GEOID")

## check merge ## 
table(wrld.2018.fips.c2$merge.variable)

## what's going on with these nonmatches? ##
no.match.wrld.2018.fips <- wrld.2018.fips.c2 %>%
  filter(merge.variable ==1)

## count matches ## 

wrld.2018.fips.c1f <- wrld.2018.fips.c1 %>%
  filter(merge.variable == 3) %>%
  select(GEOID)

wrld.2018.fips.c2f <- wrld.2018.fips.c2 %>%
  filter(merge.variable == 3) %>%
  select(GEOID)

## append the data frames ## 

wrld.2018.fips.fc <- rbind(wrld.2018.fips.c1f,
                           wrld.2018.fips.c2f)

## are all FIPS codes correct? ##
nrow(wrld.2018.fips.fc) == nrow(wrld.panel.2018)

## export file ## 
save(wrld.panel.2018,
     file = paste(output_path,
                  "001_wrld_panel_2018.Rda",
                  sep=""))

########################
## process NLLUS 2003 ##
########################

nllus.2003 <- nllus.2003.in %>%
  filter(placefp != "99999")

nllus.2003$fullname <- as.character(paste(nllus.2003$basename, nllus.2003$juristype))
nllus.2003$stfips_2003 <- str_pad(nllus.2003$stfips_2003, 2, pad = "0")
nllus.2003$stcofips <- str_pad(nllus.2003$stcofips, 5, pad = "0")
nllus.2003$countyfp <- str_pad(nllus.2003$countyfp, 3, pad = "0")
nllus.2003$statefp <- str_pad(nllus.2003$statefp, 2, pad = "0")
nllus.2003$placefp <- str_pad(nllus.2003$placefp, 5, pad = "0")
nllus.2003$full_fip <- str_pad(nllus.2003$full_fip, 10, pad = "0")
nllus.2003$geoid00 <- paste(nllus.2003$statefp,
                            nllus.2003$placefp,
                            sep="")
nllus.2003$place00 <- nllus.2003$geoid00

## is data unique by place code? ##

nrow(nllus.2003) == length(unique(nllus.2003$geoid00))

nllus.2003.dups <- nllus.2003 %>%
  group_by(geoid00) %>%
  summarize(n = n()) %>%
  filter(n > 1)

## fix dups ## 
nllus.2003$geoid00[nllus.2003$geoid00 == "2563305" & nllus.2003$basename == "Seekonk"] <- "2560645"
nllus.2003$place00[nllus.2003$geoid00 == "2560645" & nllus.2003$basename == "Seekonk"] <- "2560645"

nllus.2003$geoid00[nllus.2003$geoid00 == "2563305" & nllus.2003$basename == "the Town of Southbridge"] <- "2563270"
nllus.2003$place00[nllus.2003$geoid00 == "2563270" & nllus.2003$basename == "the Town of Southbridge"] <- "2563270"

nllus.2003$geoid00[nllus.2003$geoid00 == "3651000" & nllus.2003$basename == "Geneseo"] <- "3628629"
nllus.2003$place00[nllus.2003$geoid00 == "3628629" & nllus.2003$basename == "Geneseo"] <- "3628629"

## fix incorrect place/county sub codes ##
## NOTE: New Rome was dissolved in 2004, leave ##

nllus.2003$geoid00[nllus.2003$geoid00 == "1269555" & nllus.2003$basename == "Sunny Isles Beach"] <- "1269550"
nllus.2003$place00[nllus.2003$geoid00 == "1269550" & nllus.2003$basename == "Sunny Isles Beach"] <- "1269550"

nllus.2003$geoid00[nllus.2003$geoid00 == "2501260" & nllus.2003$basename == "Amesbury Town"] <- "2501185"
nllus.2003$place00[nllus.2003$geoid00 == "2501185" & nllus.2003$basename == "Amesbury Town"] <- "2501185"

nllus.2003$geoid00[nllus.2003$geoid00 == "2525172" & nllus.2003$basename == "Franklin Town"] <- "2525100"
nllus.2003$place00[nllus.2003$geoid00 == "2525100" & nllus.2003$basename == "Franklin Town"] <- "2525100"

nllus.2003$geoid00[nllus.2003$geoid00 == "3482423" & nllus.2003$basename == "Woodland Park"] <- "3479820"
nllus.2003$place00[nllus.2003$geoid00 == "3479820" & nllus.2003$basename == "Woodland Park"] <- "3479820"

nllus.2003$geoid00[nllus.2003$geoid00 == "0915420" & nllus.2003$basename == "Clinton"] <- "0915350"
nllus.2003$place00[nllus.2003$geoid00 == "0915350" & nllus.2003$basename == "Clinton"] <- "0915350"

nllus.2003$juristype[nllus.2003$geoid00 == "1743952" & nllus.2003$basename == "Lisle"] <- "township"
nllus.2003$juristype[nllus.2003$geoid00 == "1753676" & nllus.2003$basename == "Northfield"] <- "township"
nllus.2003$juristype[nllus.2003$geoid00 == "1766872" & nllus.2003$basename == "St. Jacob"] <- "township"

nllus.2003$fullname[nllus.2003$geoid00 == "1743952" & nllus.2003$basename == "Lisle"] <- "Lisle township"
nllus.2003$fullname[nllus.2003$geoid00 == "1753676" & nllus.2003$basename == "Northfield"] <- "Northfield township"
nllus.2003$fullname[nllus.2003$geoid00 == "1766872" & nllus.2003$basename == "St. Jacob"] <- "St. Jacob township"

nllus.2003$geoid00[nllus.2003$geoid00 == "3325300" & nllus.2003$basename == "Exeter"] <- "3325380"
nllus.2003$place00[nllus.2003$geoid00 == "3325380" & nllus.2003$basename == "Exeter"] <- "3325380"

nllus.2003$geoid00[nllus.2003$geoid00 == "3603188" & nllus.2003$basename == "Aurora"] <- "3603199"
nllus.2003$place00[nllus.2003$geoid00 == "3603199" & nllus.2003$basename == "Aurora"] <- "3603199"

nllus.2003$juristype[nllus.2003$geoid00 == "5527575" & nllus.2003$basename == "Fredonia"] <- "town"
nllus.2003$fullname[nllus.2003$geoid00 == "5527575" & nllus.2003$basename == "Fredonia"] <- "Fredonia town"

## changed to Robbinsville in 2007 ##
nllus.2003$fullname[nllus.2003$geoid00 == "3477210" & nllus.2003$basename == "Washington"] <- "Robbinsville township"


## take 2: is data unique by place code? ##

nrow(nllus.2003) == length(unique(nllus.2003$geoid00))
nrow(nllus.2003) == length(unique(nllus.2003$place00))

## convert 2000 place code into 2010 place code ## 

## merge checks ## 

nrow(allpl.2010.pr) == length(unique(allpl.2010.pr$place00))
nrow(allpl.2010.pr) == length(unique(allpl.2010.pr$place00))
class(allpl.2010.pr$place00)
range(nchar(trim(allpl.2010.pr$place00)))

nrow(nllus.2003) == length(unique(trim(nllus.2003$place00)))
class(nllus.2003$place00)
range(nchar(trim(nllus.2003$place00)))

## merge place10 codes ## 

nllus.2003.up <- stata.merge(nllus.2003,
                             allpl.2010.pr,
                             "place00")

## merge diagnosis ##
table(nllus.2003.up$merge.variable, useNA = "ifany")

## non-matches need different data ##

nllus.2003.cosubs <- nllus.2003.up %>%
  filter(merge.variable == 1) %>%
  select(place00,
         state_name,
         juris_2003) %>%
  rename(statename = state_name,
         cosub00 = place00) %>%
  mutate(name = as.character(juris_2003)) %>%
  select(-juris_2003)

## merge checks ## 

nrow(allcs.2010.pr) == length(unique(allcs.2010.pr$cosub00))
nrow(allcs.2010.pr) == length(unique(allcs.2010.pr$cosub10))
class(allcs.2010.pr$cosub00)
range(nchar(trim(allcs.2010.pr$cosub00)))

nrow(nllus.2003.cosubs) == length(unique(trim(nllus.2003.cosubs$cosub00)))
class(nllus.2003.cosubs$cosub00)
range(nchar(trim(nllus.2003.cosubs$cosub00)))

## merge cosubs ## 

nllus.2003.cosubs.final <- stata.merge(nllus.2003.cosubs,
                                       allcs.2010.pr,
                                       "cosub00")

## check merge ## 
table(nllus.2003.cosubs.final$merge.variable)

## what's going on with these nonmatches? ##
no.cs.nllus.2003 <- nllus.2003.cosubs.final %>%
  filter(merge.variable ==1)

## finalize NLLUS 2003 ## 

## initial matches on place FIPS ##

nllus.2003.keep1 <- nllus.2003.up %>%
  filter(merge.variable == 3) %>%
  select(place00, 
         state_name,
         juris_2003,
         place10) %>%
  rename(statename = state_name,
         name = juris_2003,
         geoid00 = place00,
         geoid10 = place10)

## additional matches on cosub FIPS ## 

nllus.2003.keep2 <- nllus.2003.cosubs.final %>%
  filter(merge.variable == 3 | cosub00 %in% c("2718662","3964570")) %>%
  select(cosub00,
         statename,
         name,
         cosub10) %>%
  rename(geoid00 = cosub00,
         geoid10 = cosub10)

## append the data frames ## 

nllus.2003.final.ids <- rbind(nllus.2003.keep1,
                              nllus.2003.keep2)


## create the final NLLUS 2003 data frame ## 

## merge checks ## 

nrow(nllus.2003.final.ids) == length(unique(nllus.2003.final.ids$geoid00))
class(nllus.2003.final.ids$geoid00)
range(nchar(trim(nllus.2003.final.ids$geoid00)))

nrow(nllus.2003) == length(unique(nllus.2003$geoid00))
class(nllus.2003$geoid00)
range(nchar(trim(nllus.2003$geoid00)))

nllus.2003.temp <- stata.merge(nllus.2003.final.ids,
                               nllus.2003,
                               "geoid00")

## merge check ## 
table(nllus.2003.temp$merge.variable)

## create file, keeping matches ##
nllus.2003.final <- nllus.2003.temp %>%
  filter(merge.variable == 3) %>%
  select(geoid10,
         statename,
         fullname,
         name,
         maxdens_2003,
         afinclzn_2003,
         afhsgfee_2003,
         afbonus_2003,
         affastrk_2003,
         afother_2003) %>%
  rename(GEOID = geoid10,
         name_old = name) %>%
  mutate(name = as.character(name_old),
         max_den_cat5 = case_when(maxdens_2003 == 5 ~ 1,
                                  maxdens_2003 %in% c(1,2,3,4) ~ 0),
         max_den_cat4 = case_when(maxdens_2003 == 4 ~ 1,
                                  maxdens_2003 %in% c(1,2,3,5) ~ 0),
         max_den_cat3 = case_when(maxdens_2003 == 3 ~ 1,
                                  maxdens_2003 %in% c(1,2,4,5) ~ 0),
         max_den_cat2 = case_when(maxdens_2003 == 2 ~ 1,
                                  maxdens_2003 %in% c(1,3,4,5) ~ 0),
         max_den_cat1 = case_when(maxdens_2003 == 1 ~ 1,
                                  maxdens_2003 %in% c(2,3,4,5) ~ 0),
         inclusionary = case_when(afinclzn_2003 == 1 |
                                  afhsgfee_2003 == 1 |
                                  afbonus_2003 == 1 |
                                  affastrk_2003 == 1 |
                                  afother_2003 == 1 ~ 1,
                                  TRUE ~ 0)) %>%
  select(GEOID,
         statename,
         fullname,
         name,
         max_den_cat1,
         max_den_cat2,
         max_den_cat3,
         max_den_cat4,
         max_den_cat5,
         inclusionary)

nllus.2003.final <- nllus.2003.final %>%
  mutate(maxden5 = max_den_cat5,
         maxden4 = ifelse(max_den_cat5 == 1, 0, max_den_cat4),
         maxden3 = ifelse(max_den_cat5 == 1 | max_den_cat4 == 1, 0, max_den_cat3),
         maxden2 = ifelse(max_den_cat5 == 1 | max_den_cat4 == 1 | max_den_cat3 == 1, 0, max_den_cat2),
         maxden1 = ifelse(max_den_cat5 == 1 | max_den_cat4 == 1 | max_den_cat3 == 1 | max_den_cat2 == 1, 0, max_den_cat1))

## final fixes ##
nllus.2003.final$GEOID[nllus.2003.final$fullname == "Elko New Market city"] <- "2718662"
nllus.2003.final$name[nllus.2003.final$fullname == "Elko New Market city"] <- "Elko New Market" 
nllus.2003.final$fullname[nllus.2003.final$GEOID == "0639003"] <- "La Ca?ada Flintridge city"
nllus.2003.final$fullname[nllus.2003.final$GEOID == "1836003"] <- "Indianapolis city (balance)"
nllus.2003.final$fullname[nllus.2003.final$GEOID == "2148006"] <- "Louisville/Jefferson County metro government (balance)"
nllus.2003.final$fullname[nllus.2003.final$GEOID == "2563345"] <- "Southbridge Town city"
nllus.2003.final$fullname[nllus.2003.final$GEOID == "2601360"] <- "Allendale charter township"
nllus.2003.final$fullname[nllus.2003.final$GEOID == "2604180"] <- "Augusta charter township"
nllus.2003.final$fullname[nllus.2003.final$GEOID == "2613660"] <- "Cascade charter township"
nllus.2003.final$fullname[nllus.2003.final$GEOID == "2629020"] <- "Flint charter township"
nllus.2003.final$fullname[nllus.2003.final$GEOID == "2631240"] <- "Gaines charter township"
nllus.2003.final$fullname[nllus.2003.final$GEOID == "2631800"] <- "Genesee charter township"
nllus.2003.final$fullname[nllus.2003.final$GEOID == "2631880"] <- "Georgetown charter township"
nllus.2003.final$fullname[nllus.2003.final$GEOID == "2633300"] <- "Grand Blanc charter township"
nllus.2003.final$fullname[nllus.2003.final$GEOID == "2633360"] <- "Grand Haven charter township"
nllus.2003.final$fullname[nllus.2003.final$GEOID == "2634020"] <- "Grand Rapids charter township"
nllus.2003.final$fullname[nllus.2003.final$GEOID == "2638660"] <- "Holland charter township"
nllus.2003.final$fullname[nllus.2003.final$GEOID == "2655040"] <- "Monroe charter township"
nllus.2003.final$fullname[nllus.2003.final$GEOID == "2656340"] <- "Muskegon charter township"
nllus.2003.final$fullname[nllus.2003.final$GEOID == "2664560"] <- "Pittsfield charter township"
nllus.2003.final$fullname[nllus.2003.final$GEOID == "2664660"] <- "Plainfield charter township"
nllus.2003.final$fullname[nllus.2003.final$GEOID == "2665320"] <- "Polkton charter township"
nllus.2003.final$fullname[nllus.2003.final$GEOID == "2677560"] <- "Superior charter township"
nllus.2003.final$fullname[nllus.2003.final$GEOID == "2689160"] <- "Ypsilanti charter township"
nllus.2003.final$fullname[nllus.2003.final$GEOID == "2941348"] <- "Lee's Summit city"
nllus.2003.final$fullname[nllus.2003.final$GEOID == "2954074"] <- "O'Fallon city"
nllus.2003.final$fullname[nllus.2003.final$GEOID == "3972522"] <- "Silverton city"
nllus.2003.final$fullname[nllus.2003.final$GEOID == "3941244"] <- "LaGrange township"
nllus.2003.final$fullname[nllus.2003.final$GEOID == "4206064"] <- "Bethel Park municipality"
nllus.2003.final$fullname[nllus.2003.final$GEOID == "4206544"] <- "Birmingham township"
nllus.2003.final$fullname[nllus.2003.final$GEOID == "4219536"] <- "Donora borough"
nllus.2003.final$fullname[nllus.2003.final$GEOID == "4250528"] <- "Monroeville municipality"
nllus.2003.final$fullname[nllus.2003.final$GEOID == "4252432"] <- "Murrysville municipality"
nllus.2003.final$fullname[nllus.2003.final$GEOID == "4752006"] <- "Nashville-Davidson metropolitan government (balance)"

## ensure correct FIPS codes ##

## merge checks ## 

nrow(allpl.2010.pr) == length(unique(allpl.2010.pr$GEOID))
class(allpl.2010.pr$GEOID)
class(allpl.2010.pr$fullname)
range(nchar(trim(allpl.2010.pr$GEOID)))

nrow(nllus.2003.final) == length(unique(trim(nllus.2003.final$GEOID)))
class(nllus.2003.final$GEOID)
class(nllus.2003.final$fullname)
range(nchar(trim(nllus.2003.final$GEOID)))

## merge check 1 ## 

nllus.2003.fips.c1 <- stata.merge(nllus.2003.final,
                                  allpl.2010.pr,
                                  c("GEOID","fullname"))

## merge diagnosis ##
table(nllus.2003.fips.c1$merge.variable, useNA = "ifany")


## non-matches need different data ##

no.place.nllus.2003.c1 <- nllus.2003.fips.c1 %>%
  filter(merge.variable == 1) %>%
  select(GEOID,
         fullname)

## merge checks ## 

nrow(allcs.2010.pr) == length(unique(allcs.2010.pr$GEOID))
class(allcs.2010.pr$GEOID)
class(allcs.2010.pr$fullname)
range(nchar(trim(allcs.2010.pr$GEOID)))

nrow(no.place.nllus.2003.c1) == length(unique(trim(no.place.nllus.2003.c1$GEOID)))
class(no.place.nllus.2003.c1$GEOID)
class(no.place.nllus.2003.c1$fullname)
range(nchar(trim(no.place.nllus.2003.c1$GEOID)))

## merge check 2 ## 

nllus.2003.fips.c2 <- stata.merge(no.place.nllus.2003.c1,
                                  allcs.2010.pr,
                                  c("GEOID","fullname"))

## check merge ## 
table(nllus.2003.fips.c2$merge.variable)

## what's going on with these nonmatches? ##
no.match.nllus.2003.fips <- nllus.2003.fips.c2 %>%
  filter(merge.variable ==1)

## count matches ## 

nllus.2003.fips.c1f <- nllus.2003.fips.c1 %>%
  filter(merge.variable == 3) %>%
  select(GEOID)

nllus.2003.fips.c2f <- nllus.2003.fips.c2 %>%
  filter(merge.variable == 3) %>%
  select(GEOID)

## append the data frames ## 

nllus.2003.fips.fc <- rbind(nllus.2003.fips.c1f,
                            nllus.2003.fips.c2f)

## are all FIPS codes correct? ##
nrow(nllus.2003.fips.fc) == nrow(nllus.2003.final)


## save data ##

save(nllus.2003.final,
     file = paste(output_path,
                  "001_nllus_2003.Rda",
                  sep=""))


########################
## process NLLUS 2019 ##
########################

nllus.2019 <- nllus.2019.in %>%
  filter(placefp_2019 != "99999" & resp_nonresp_2019 !=0)

nllus.2019$fullname <- as.character(paste(nllus.2019$basename_2019, nllus.2019$juristype_2019))
nllus.2019$stcofip_2019 <- str_pad(nllus.2019$stcofip_2019, 5, pad = "0")
nllus.2019$countyfp_2019 <- str_pad(nllus.2019$countyfp_2019, 3, pad = "0")
nllus.2019$statefp_2019 <- str_pad(nllus.2019$statefp_2019, 2, pad = "0")
nllus.2019$placefp_2019 <- str_pad(nllus.2019$placefp_2019, 5, pad = "0")
nllus.2019$full_fip_2019 <- str_pad(nllus.2019$full_fip_2019, 10, pad = "0")
nllus.2019$GEOID <- paste(nllus.2019$statefp_2019,
                                nllus.2019$placefp_2019,
                                sep="")

## is data unique by place code? ##

nrow(nllus.2019) == length(unique(nllus.2019$GEOID))

nllus.2019.dups <- nllus.2019 %>%
  group_by(GEOID) %>%
  summarize(n = n()) %>%
  filter(n > 1)

## fix dups ## 
nllus.2019$GEOID <- ifelse(nllus.2019$GEOID == "2563305" & nllus.2019$basename_2019 == "Seekonk",
                           "2560645",
                           nllus.2019$GEOID)

nllus.2019$GEOID <- ifelse(nllus.2019$GEOID == "2563305" & nllus.2019$basename_2019 == "the Town of Southbridge",
                           "2563345",
                           nllus.2019$GEOID)

## take 2: is data unique by place code? ##

nrow(nllus.2019) == length(unique(nllus.2019$GEOID))

## final file ## 

nllus.2019.final <- nllus.2019 %>%
  select(GEOID,
         fullname,
         state_name_2019,
         basename_2019,
         dupernacre_max_2019,
         ah_req_dummy_2019,
         ah_fee_2019,
         ah_bonusdens_2019,
         ah_buildenv_2019,
         ah_mindusize_2019,
         ah_adu_2019,
         ah_parking_2019,
         ah_ifwaiver_2019,
         ah_fasttrack_2019,
         ah_other_2019) %>%
  rename(statename = state_name_2019,
         name = basename_2019) %>%
  mutate(max_den_cat5 = case_when(dupernacre_max_2019 == 5 ~ 1,
                                  dupernacre_max_2019  %in% c(1,2,3,4) ~ 0),
         max_den_cat4 = case_when(dupernacre_max_2019 == 4 ~ 1,
                                  dupernacre_max_2019  %in% c(1,2,3,5) ~ 0),
         max_den_cat3 = case_when(dupernacre_max_2019 == 3 ~ 1,
                                  dupernacre_max_2019  %in% c(1,2,4,5) ~ 0),
         max_den_cat2 = case_when(dupernacre_max_2019 == 2 ~ 1,
                                  dupernacre_max_2019  %in% c(1,3,4,5) ~ 0),
         max_den_cat1 = case_when(dupernacre_max_2019 == 1 ~ 1,
                                  dupernacre_max_2019  %in% c(2,3,4,5) ~ 0),
         inclusionary = case_when(ah_req_dummy_2019 == 1 |
                                  ah_fee_2019 == 1 |
                                  ah_bonusdens_2019 == 1 |
                                  ah_buildenv_2019 == 1 |
                                  ah_mindusize_2019 == 1 |
                                  ah_adu_2019 == 1 | 
                                  ah_parking_2019 == 1 |
                                  ah_ifwaiver_2019 == 1 | 
                                  ah_fasttrack_2019 == 1 |
                                  ah_other_2019 == 1 ~ 1,
                                  TRUE ~ 0)) %>%
  select(GEOID,
         statename,
         fullname,
         name,
         max_den_cat1,
         max_den_cat2,
         max_den_cat3,
         max_den_cat4,
         max_den_cat5,
         inclusionary)

nllus.2019.final <- nllus.2019.final %>%
  mutate(maxden5 = max_den_cat5,
         maxden4 = ifelse(max_den_cat5 == 1, 0, max_den_cat4),
         maxden3 = ifelse(max_den_cat5 == 1 | max_den_cat4 == 1, 0, max_den_cat3),
         maxden2 = ifelse(max_den_cat5 == 1 | max_den_cat4 == 1 | max_den_cat3 == 1, 0, max_den_cat2),
         maxden1 = ifelse(max_den_cat5 == 1 | max_den_cat4 == 1 | max_den_cat3 == 1 | max_den_cat2 == 1, 0, max_den_cat1))

## final fixes ##
nllus.2019.final$GEOID[nllus.2019.final$GEOID == "3940767"] <- "3941230"
nllus.2019.final$GEOID[nllus.2019.final$GEOID == "4208760"] <- "4208768"
nllus.2019.final$GEOID[nllus.2019.final$GEOID == "4252332"] <- "4252432"
nllus.2019.final$GEOID[nllus.2019.final$GEOID == "5527575"] <- "5527550"

nllus.2019.final$fullname[nllus.2019.final$GEOID == "0407940"] <- "Buckeye town"
nllus.2019.final$fullname[nllus.2019.final$GEOID == "1755249"] <- "O'Fallon city"
nllus.2019.final$fullname[nllus.2019.final$GEOID == "2508085"] <- "Bridgewater town"
nllus.2019.final$fullname[nllus.2019.final$GEOID == "2563345"] <- "Southbridge Town city"
nllus.2019.final$fullname[nllus.2019.final$GEOID == "2604180"] <- "Augusta charter township"
nllus.2019.final$fullname[nllus.2019.final$GEOID == "2631240"] <- "Gaines charter township"
nllus.2019.final$fullname[nllus.2019.final$GEOID == "2633300"] <- "Grand Blanc charter township"
nllus.2019.final$fullname[nllus.2019.final$GEOID == "2633360"] <- "Grand Haven charter township"
nllus.2019.final$fullname[nllus.2019.final$GEOID == "2634020"] <- "Grand Rapids charter township"
nllus.2019.final$fullname[nllus.2019.final$GEOID == "2638660"] <- "Holland charter township"
nllus.2019.final$fullname[nllus.2019.final$GEOID == "2655040"] <- "Monroe charter township"
nllus.2019.final$fullname[nllus.2019.final$GEOID == "2664660"] <- "Plainfield charter township"
nllus.2019.final$fullname[nllus.2019.final$GEOID == "2665320"] <- "Polkton charter township"
nllus.2019.final$fullname[nllus.2019.final$GEOID == "2689160"] <- "Ypsilanti charter township"
nllus.2019.final$fullname[nllus.2019.final$GEOID == "2941348"] <- "Lee's Summit city"
nllus.2019.final$fullname[nllus.2019.final$GEOID == "2954074"] <- "O'Fallon city"
nllus.2019.final$fullname[nllus.2019.final$GEOID == "3972522"] <- "Silverton city"
nllus.2019.final$fullname[nllus.2019.final$GEOID == "3941230"] <- "LaGrange village"
nllus.2019.final$fullname[nllus.2019.final$GEOID == "4219536"] <- "Donora borough"
nllus.2019.final$fullname[nllus.2019.final$GEOID == "4250528"] <- "Monroeville municipality"
nllus.2019.final$fullname[nllus.2019.final$GEOID == "4252432"] <- "Murrysville municipality"
nllus.2019.final$fullname[nllus.2019.final$GEOID == "4752006"] <- "Nashville-Davidson metropolitan government (balance)"

## ensure correct FIPS codes ##

## merge checks ## 

nrow(allpl.2010.pr) == length(unique(allpl.2010.pr$GEOID))
class(allpl.2010.pr$GEOID)
class(allpl.2010.pr$fullname)
range(nchar(trim(allpl.2010.pr$GEOID)))

nrow(nllus.2019.final) == length(unique(trim(nllus.2019.final$GEOID)))
class(nllus.2019.final$GEOID)
class(nllus.2019.final$fullname)
range(nchar(trim(nllus.2019.final$GEOID)))

## merge check 1 ## 

nllus.2019.fips.c1 <- stata.merge(nllus.2019.final,
                                  allpl.2010.pr,
                                  c("GEOID","fullname"))

## merge diagnosis ##
table(nllus.2019.fips.c1$merge.variable, useNA = "ifany")

## non-matches need different data ##

no.place.nllus.2019.c1 <- nllus.2019.fips.c1 %>%
  filter(merge.variable == 1) %>%
  select(GEOID,
         fullname)

## merge checks ## 

nrow(allcs.2010.pr) == length(unique(allcs.2010.pr$GEOID))
class(allcs.2010.pr$GEOID)
class(allcs.2010.pr$fullname)
range(nchar(trim(allcs.2010.pr$GEOID)))

nrow(no.place.nllus.2019.c1) == length(unique(trim(no.place.nllus.2019.c1$GEOID)))
class(no.place.nllus.2019.c1$GEOID)
class(no.place.nllus.2019.c1$fullname)
range(nchar(trim(no.place.nllus.2019.c1$GEOID)))

## merge check 2 ## 

nllus.2019.fips.c2 <- stata.merge(no.place.nllus.2019.c1,
                                  allcs.2010.pr,
                                  c("GEOID","fullname"))

## check merge ## 
table(nllus.2019.fips.c2$merge.variable)

## what's going on with these nonmatches? ##
no.match.nllus.2019.fips <- nllus.2019.fips.c2 %>%
  filter(merge.variable ==1)

## count matches ## 

nllus.2019.fips.c1f <- nllus.2019.fips.c1 %>%
  filter(merge.variable == 3) %>%
  select(GEOID)

nllus.2019.fips.c2f <- nllus.2019.fips.c2 %>%
  filter(merge.variable == 3) %>%
  select(GEOID)

## append the data frames ## 

nllus.2019.fips.fc <- rbind(nllus.2019.fips.c1f,
                            nllus.2019.fips.c2f)

## are all FIPS codes correct? (ommitting the 7 munis recently created) ##
nrow(nllus.2019.fips.fc) == nrow(nllus.2019.final) - 7


## save data ## 

save(nllus.2019.final,
     file = paste(output_path,
                  "001_nllus_2019.Rda",
                  sep=""))


##################################
## process original zoning data ## 
##################################

## for reformatting ##

remove.words1 <- c("City",
                  "city",
                  "Charter",
                  "Township",
                  "township",
                  "charter",
                  "CDP",
                  "municipality",
                  "Municipality",
                  "and",
                  "Of",
                  "of",
                  "Borough",
                  "borough",
                  "Ventura",
                  "Village",
                  "village",
                  "Burough")

remove.words2 <- c("Town",
                   "town")

#####################################################
## stage 1: merge on zoning collection information ##
#####################################################

## process zoning collection information ##
zc <- zoning.codes %>%
  select(statename,name,type) %>%
  mutate(name.new = gsub(",.*$", "", name),
         name.new2 = removeWords(name.new,remove.words1),
         name.new3 = removeWords(name.new2,remove.words2),
         name.new4 = gsub("-|\'", "", name.new3),
         place = str_replace_all(name.new4, fixed(" "), ""),
         type = str_replace_all(type,
                                c("3rd Class City" = "City",
                                  "Charter City" = "City",
                                  "city" = "City",
                                  "CIty" = "City",
                                  "City-Region" = "City",
                                  "City and County" = "City",
                                  "City & County" = "City",
                                  "City-County" = "City",
                                  "City and Borough" = "City",
                                  "Doral" = "City",
                                  "TX" = "City",
                                  "Home rule municipality" = "Municipality",
                                  "Incorporated Borough" = "Borough",
                                  "Municipality-Village" = "Village",
                                  "town" = "Town",
                                  "Town within a City" = "Town",
                                  "Township of the Second Class" = "Township"))) %>%
  select(statename, place, type) 

## manually fix irregularities ## 

zc$place[zc$statename == "CT" & zc$place == "Groton" & zc$type == "Borough"] <- "GrotonBorough"
zc$place[zc$statename == "CT" & zc$place == "Groton" & zc$type == "Town"] <- "GrotonTown" 

zc$place[zc$statename == "IL" & zc$place == "Thornton" & zc$type == "Village"] <- "ThorntonVillage"
zc$place[zc$statename == "IL" & zc$place == "Thornton" & zc$type == "Town"] <- "ThorntonTown"

zc$place[zc$statename == "MI" & zc$place == "GrandBlanc" & zc$type == "City"] <- "GrandBlancCity"
zc$place[zc$statename == "MI" & zc$place == "GrandBlanc" & zc$type == "Township"] <- "GrandBlancTownship" 

zc$place[zc$statename == "MI" & zc$place == "Northville" & zc$type == "City"] <- "Northville"
zc$place[zc$statename == "MI" & zc$place == "Northville" & zc$type == "Township"] <- "NorthvilleTownship"

zc$place[zc$statename == "MI" & zc$place == "Oxford" & zc$type == "Township"] <- "OxfordTownship"

zc$place[zc$statename == "MI" & zc$place == "Plymouth" & zc$type == "City"] <- "PlymouthCity"
zc$place[zc$statename == "MI" & zc$place == "Plymouth" & zc$type == "Township"] <- "PlymouthTownship"

zc$place[zc$statename == "MI" & zc$place == "Saginaw" & zc$type == "City"] <- "SaginawCity"
zc$place[zc$statename == "MI" & zc$place == "Saginaw" & zc$type == "Township"] <- "SaginawTownship"

zc$place[zc$statename == "MO" & zc$place == "Country" & zc$type == "City"] <- "TownandCountry"

zc$place[zc$statename == "NJ" & zc$place == "Franklin" & zc$type == "Borough"] <- "FranklinBorough"

zc$place[zc$statename == "NJ" & zc$place == "Union" & zc$type == "City"] <- "UnionCity"
zc$place[zc$statename == "NJ" & zc$place == "Union" & zc$type == "Township"] <- "UnionTownship"

zc$place[zc$statename == "NY" & zc$place == "Colonie" & zc$type == "Town"] <- "ColonieTown"
zc$place[zc$statename == "NY" & zc$place == "Colonie" & zc$type == "Village"] <- "ColonieVillage"

zc$place[zc$statename == "OH" & zc$place == "Green" & zc$type == "Town"] <- "GreenTown"
zc$place[zc$statename == "OH" & zc$place == "Green" & zc$type == "City"] <- "GreenCity"

zc$place[zc$statename == "PA" & zc$place == "Lancaster" & zc$type == "City"] <- "LancasterCity"
zc$place[zc$statename == "PA" & zc$place == "Lancaster" & zc$type == "Township"] <- "LancasterTownship"  

zc$place[zc$statename == "PA" & zc$place == "Manheim" & zc$type == "Borough"] <- "ManheimBorough"
zc$place[zc$statename == "PA" & zc$place == "Manheim" & zc$type == "Township"] <- "ManheimTownship"  

zc$place[zc$statename == "PA" & zc$place == "Middletown" & zc$type == "Borough"] <- "MiddletownBorough"
zc$place[zc$statename == "PA" & zc$place == "Middletown" & zc$type == "Township"] <- "MiddletownTownship"  

zc$place[zc$statename == "PA" & zc$place == "Middletown" & zc$type == "Borough"] <- "MiddletownBorough"
zc$place[zc$statename == "PA" & zc$place == "Middletown" & zc$type == "Township"] <- "MiddletownTownship" 

zc$place[zc$statename == "SC" & zc$place == "IslePalms" & zc$type == "City"] <- "IsleofPalms" 

zc$place[zc$statename == "VT" & zc$place == "Barre" & zc$type == "City"] <- "BarreCity"
zc$place[zc$statename == "VT" & zc$place == "Barre" & zc$type == "Town"] <- "BarreTown" 

zc$place[zc$statename == "WI" & zc$place == "Delavan" & zc$type == "City"] <- "DelavanCity"
zc$place[zc$statename == "WI" & zc$place == "Delavan" & zc$type == "Town"] <- "DelavanTown" 

zc$place[zc$statename == "WI" & zc$place == "Ellsworth" & zc$type == "Village"] <- "EllsworthVillage"
zc$place[zc$statename == "WI" & zc$place == "Ellsworth" & zc$type == "Town"] <- "EllsworthTown"

zc$place[zc$statename == "WI" & zc$place == "Menasha" & zc$type == "City"] <- "MenashaCity"
zc$place[zc$statename == "WI" & zc$place == "Menasha" & zc$type == "Town"] <- "MenashaTown"

zc$place[zc$statename == "WI" & zc$place == "Mukwonago" & zc$type == "Village"] <- "MukwonagoVillage"
zc$place[zc$statename == "WI" & zc$place == "Mukwonago" & zc$type == "Town"] <- "MukwonagoTown"

zc$place[zc$statename == "WI" & zc$place == "Onalaska" & zc$type == "City"] <- "OnalaskaCity"
zc$place[zc$statename == "WI" & zc$place == "Onalaska" & zc$type == "Town"] <- "OnalaskaTown"

## process the zoning data ## 

## append manual codes with source data ##
## include full SF and Houston MSAs as well ##

sf.rf <- filter(sf, timestamp != "2022-10-01 17:36:35")
houston.rf <- filter(houston, timestamp %notin% c("2022-10-03 22:12:08",
                                                  "2022-10-03 23:33:09",
                                                  "2022-10-03 14:48:26"))

zd.2019.cb <- rbind(zd.2019,
                    manual.codes,
                    houston.rf,
                    sf.rf) 

## clean the data ## 
## municipality name includes path name to input file based on the code from parse_zoning_txt.py ##
## user will need to account for that below to reformat municipality name ##

zd.2019.pr1 <- zd.2019.cb %>%
  mutate(muni_pr = case_when(substr(muni,1,44) == "depends on user input path" ~ substr(muni, 46, nchar(muni)),
                             substr(muni,1,49) == "depends on user input path" ~ substr(muni, 51,nchar(muni)),
                             substr(muni,1,2) == "/p" ~ substr(muni, 46, nchar(muni)),
                             TRUE ~ muni),
         statename = substr(muni_pr, 1, 2),
         place.int1 = substr(muni_pr,4,nchar(muni_pr)-4),
         #place.int2 = str_replace(place.int,"_",""),
         place.int2 = str_replace_all(place.int1,
                                      c("City" = "",
                                        "Township" = "",
                                        "Village" = "")),
         place = str_replace_all(place.int2,
                                 c("Town" = ""))) %>%
  select(-timestamp,
         -last_date)

names(timestamps) <- c("muni_pr",
                       "path",
                       "timestamp",
                       "ext",
                       "size")

timestamps.pr <- filter(timestamps, timestamp != "Last Modified")

zd.2019.pr <- zd.2019.pr1 %>%
  left_join(timestamps.pr, "muni_pr")

sum(is.na(zd.2019.pr$timestamp))

## fix Town and Country, MO ##
zd.2019.pr$place[zd.2019.pr$muni_pr == "MO_TownandCountry.txt"] <- "TownandCountry"

## fix Pleasanton, CA ##
zd.2019.pr$place[zd.2019.pr$muni_pr == "CA_Pleasonton.txt"] <- "Pleasanton"

## reformat min lot size variables ## 

zd.2019.pr$none_acre_more <- ifelse(zd.2019.pr$two_acre_more==1,
                                    0,
                                    zd.2019.pr$one_acre_more)

zd.2019.pr$nhalf_acre_more <- ifelse(zd.2019.pr$two_acre_more==1 | zd.2019.pr$none_acre_more==1,
                                     0,
                                     zd.2019.pr$half_acre_more)

zd.2019.pr$nhalf_acre_less <- ifelse(zd.2019.pr$two_acre_more==1 | zd.2019.pr$none_acre_more==1 | zd.2019.pr$nhalf_acre_more==1,
                                     0,
                                     zd.2019.pr$half_acre_less)

## reformat max permitted densities variables ## 

zd.2019.pr$nmax_den_cat4 <- ifelse(zd.2019.pr$max_den_cat5==1,
                                   0,
                                   zd.2019.pr$max_den_cat4)

zd.2019.pr$nmax_den_cat3 <- ifelse(zd.2019.pr$max_den_cat4==1,
                                   0,
                                   zd.2019.pr$max_den_cat3)

zd.2019.pr$nmax_den_cat2 <- ifelse(zd.2019.pr$max_den_cat3==1,
                                   0,
                                   zd.2019.pr$max_den_cat2)

zd.2019.pr$nmax_den_cat1 <- ifelse(zd.2019.pr$max_den_cat2==1,
                                   0,
                                   zd.2019.pr$max_den_cat1)

## create summary zoning process vars ## 

zd.2019.pr$total_nz <- rowSums(zd.2019.pr[,c("council_nz", 
                                             "planning_nz",
                                             "countybrd_nz",
                                             "pubhlth_nz",
                                             "site_plan_nz",
                                             "env_rev_nz")])

zd.2019.pr$total_rz <- rowSums(zd.2019.pr[,c("council_rz", 
                                             "planning_rz",
                                             "zoning_rz",
                                             "countybrd_rz",
                                             "countyzone_rz",
                                             "townmeet_rz",
                                             "env_rev_rz")])

## manually fix irregularities ## 

zd.2019.pr <- filter(zd.2019.pr, place != "Abindgdon")

zd.2019.pr$place[zd.2019.pr$statename == "CT" & zd.2019.pr$muni_pr == "CT_GrotonTown.txt"] <- "GrotonTown" 

zd.2019.pr$place[zd.2019.pr$statename == "IL" & zd.2019.pr$muni_pr == "IL_O'Fallon.txt"] <- "OFallon"

zd.2019.pr$place[zd.2019.pr$statename == "MI" & zd.2019.pr$muni_pr == "MI_GrandBlanc.txt"] <- "GrandBlancCity" 
zd.2019.pr$place[zd.2019.pr$statename == "MI" & zd.2019.pr$muni_pr == "MI_GrandBlancTownship.txt"] <- "GrandBlancTownship" 

zd.2019.pr$place[zd.2019.pr$statename == "MI" & zd.2019.pr$muni_pr == "MI_Northville.txt"] <- "Northville"
zd.2019.pr$place[zd.2019.pr$statename == "MI" & zd.2019.pr$muni_pr == "MI_NorthvilleTownship.txt"] <- "NorthvilleTownship" 

zd.2019.pr$place[zd.2019.pr$statename == "MI" & zd.2019.pr$muni_pr == "MI_OxfordTownship.txt"] <- "OxfordTownship"

zd.2019.pr$place[zd.2019.pr$statename == "MI" & zd.2019.pr$muni_pr == "MI_Plymouth.txt"] <- "PlymouthCity"
zd.2019.pr$place[zd.2019.pr$statename == "MI" & zd.2019.pr$muni_pr == "MI_PlymouthTownship.txt"] <- "PlymouthTownship"

zd.2019.pr$place[zd.2019.pr$statename == "MI" & zd.2019.pr$muni_pr == "MI_Saginaw.txt"] <- "SaginawCity"
zd.2019.pr$place[zd.2019.pr$statename == "MI" & zd.2019.pr$muni_pr == "MI_SaginawTownship.txt"] <- "SaginawTownship"

zd.2019.pr$place[zd.2019.pr$statename == "NJ" & zd.2019.pr$muni_pr == "NJ_Abescon.txt"] <- "Absecon"

zd.2019.pr$place[zd.2019.pr$statename == "NJ" & zd.2019.pr$muni_pr == "NJ_Union.txt"] <- "UnionTownship"
zd.2019.pr$place[zd.2019.pr$statename == "NJ" & zd.2019.pr$muni_pr == "NJ_UnionCity.txt"] <- "UnionCity"

zd.2019.pr$place[zd.2019.pr$statename == "NM" & zd.2019.pr$muni_pr == "NM_Tucumari.txt"] <- "Tucumcari"

zd.2019.pr$place[zd.2019.pr$statename == "NY" & zd.2019.pr$muni_pr == "NY_ColonieTown.txt"] <- "ColonieTown"
zd.2019.pr$place[zd.2019.pr$statename == "NY" & zd.2019.pr$muni_pr == "NY_ColonieVillage.txt"] <- "ColonieVillage"

zd.2019.pr$place[zd.2019.pr$statename == "OH" & zd.2019.pr$muni_pr == "OH_Green.txt"] <- "GreenCity"
zd.2019.pr$place[zd.2019.pr$statename == "OH" & zd.2019.pr$muni_pr == "OH_GreenTownship.txt"] <- "GreenTown"

zd.2019.pr$place[zd.2019.pr$statename == "PA" & zd.2019.pr$muni_pr == "PA_Cranberry.txt"] <- "CranberryButler" 

zd.2019.pr$place[zd.2019.pr$statename == "PA" & zd.2019.pr$muni_pr == "PA_Lancaster.txt"] <- "LancasterCity" 
zd.2019.pr$place[zd.2019.pr$statename == "PA" & zd.2019.pr$muni_pr == "PA_LancasterTownship.txt"] <- "LancasterTownship"

zd.2019.pr$place[zd.2019.pr$statename == "PA" & zd.2019.pr$muni_pr == "PA_ManheimTownship.txt"] <- "ManheimTownship"

zd.2019.pr$place[zd.2019.pr$statename == "PA" & zd.2019.pr$muni_pr == "PA_MiddletownTownship.txt"] <- "MiddletownTownship"

zd.2019.pr$place[zd.2019.pr$statename == "VT" & zd.2019.pr$muni_pr == "VT_Barre.txt"] <- "BarreTown"
zd.2019.pr$place[zd.2019.pr$statename == "VT" & zd.2019.pr$muni_pr == "VT_BarreCity.txt"] <- "BarreCity"

zd.2019.pr$place[zd.2019.pr$statename == "WA" & zd.2019.pr$muni_pr == "WA_PortTownsend.txt"] <- "PortTownsend" 

zd.2019.pr$place[zd.2019.pr$statename == "WI" & zd.2019.pr$muni_pr == "WI_Delavan.txt"] <- "DelavanCity"
zd.2019.pr$place[zd.2019.pr$statename == "WI" & zd.2019.pr$muni_pr == "WI_DelavanTown.txt"] <- "DelavanTown"

zd.2019.pr$place[zd.2019.pr$statename == "WI" & zd.2019.pr$muni_pr == "WI_EllsworthVillage.txt"] <- "EllsworthVillage"
zd.2019.pr$place[zd.2019.pr$statename == "WI" & zd.2019.pr$muni_pr == "WI_EllsworthTown.txt"] <- "EllsworthTown"

zd.2019.pr$place[zd.2019.pr$statename == "WI" & zd.2019.pr$muni_pr == "WI_Menasha.txt"] <- "MenashaCity"

zd.2019.pr$place[zd.2019.pr$statename == "WI" & zd.2019.pr$muni_pr == "WI_Mukwonago.txt"] <- "MukwonagoVillage"
zd.2019.pr$place[zd.2019.pr$statename == "WI" & zd.2019.pr$muni_pr == "WI_MukwonagoTown.txt"] <- "MukwonagoTown"

zd.2019.pr$place[zd.2019.pr$statename == "WI" & zd.2019.pr$muni_pr == "WI_Onalaska.txt"] <- "OnalaskaCity"
zd.2019.pr$place[zd.2019.pr$statename == "WI" & zd.2019.pr$muni_pr == "WI_OnalaskaTown.txt"] <- "OnalaskaTown"

## merge zoning data with zoning collection information ## 
## this is necessary to distinguish places with same names ##

## add on the SF and Houston additions ##

zc.all <- rbind(zc,
                zc.adds)

## merge checks ## 

nrow(zd.2019.pr) == length(unique(paste(zd.2019.pr$statename,
                                        zd.2019.pr$place)))

zd.2019.dups <- zd.2019.pr %>%
  mutate(id = paste0(statename,place)) %>%
  group_by(id) %>%
  summarize(n=n()) %>%
  filter(n>1)

nrow(zc.all) == length(unique(paste(zc.all$statename,
                                    zc.all$place)))

zc.all.dups <- zc.all %>%
  mutate(id = paste0(statename,place)) %>%
  group_by(id) %>%
  summarize(n=n()) %>%
  filter(n>1)

## merge data frames ##
zd.2019.merged <- stata.merge(zd.2019.pr,
                              zc.all,
                              c("statename",
                                "place"))

## check merge ##
table(zd.2019.merged$merge.variable)

## output the non-matches (munis that don't have any available codes) ##
nonmatches <- zd.2019.merged %>%
  filter(merge.variable == 2)

save(nonmatches,
     file = paste(output_path,
                  "001_zd_nonmatches.Rda",
                  sep=""))

## finalize stage 1 zoning data frame ## 
zd.2019.final <- zd.2019.merged %>%
  filter(merge.variable == 3) %>%
  select(-merge.variable)

## manually fix irregularities ##

zd.2019.final$type[zd.2019.final$statename == "AR" & zd.2019.final$muni_pr == "AR_CherokeeVillage.txt"] <- "City" 

zd.2019.final$type[zd.2019.final$statename == "AZ" & zd.2019.final$muni_pr == "AZ_QueenCreek.txt"] <- "Town" 

zd.2019.final$type[zd.2019.final$statename == "GA" & zd.2019.final$muni_pr == "GA_Columbus.txt"] <- "City" 

zd.2019.final$type[zd.2019.final$statename == "IN" & zd.2019.final$muni_pr == "IN_Corydon.txt"] <- "Town" 

zd.2019.final$type[zd.2019.final$statename == "KS" & zd.2019.final$muni_pr == "KS_PrairieVillage.txt"] <- "City" 

zd.2019.final$place[zd.2019.final$statename == "MI" & zd.2019.final$muni_pr == "MI_PlainfieldTownship.txt"] <- "PlainfieldTownship" 

zd.2019.final$place[zd.2019.final$statename == "MI" & zd.2019.final$muni_pr == "MI_MarquetteTownship.txt"] <- "MarquetteTownship"

zd.2019.final$place[zd.2019.final$statename == "MI" & zd.2019.final$muni_pr == "MI_UnionTownship.txt"] <- "UnionTownship" 

zd.2019.final$place[zd.2019.final$statename == "MN" & zd.2019.final$muni_pr == "MN_StAnthony.txt"] <- "StAnthonyCity" 

zd.2019.final$place[zd.2019.final$statename == "NJ" & zd.2019.final$muni_pr == "NJ_Hamilton.txt"] <- "HamiltonTownship"

zd.2019.final$place[zd.2019.final$statename == "NJ" & zd.2019.final$muni_pr == "NJ_Lawrence.txt"] <- "LawrenceTownship" 

zd.2019.final$place[zd.2019.final$statename == "NJ" & zd.2019.final$muni_pr == "NJ_Hopewell.txt"] <- "HopewellTownship"

zd.2019.final$place[zd.2019.final$statename == "NJ" & zd.2019.final$muni_pr == "NJ_Springfield.txt"] <- "SpringfieldTownship"

zd.2019.final$place[zd.2019.final$statename == "NJ" & zd.2019.final$muni_pr == "NJ_Washington.txt"] <- "WashingtonTownship"

zd.2019.final$type[zd.2019.final$statename == "NJ" & zd.2019.final$muni_pr == "NJ_Orange.txt"] <- "Township" 

zd.2019.final$type[zd.2019.final$statename == "NJ" & zd.2019.final$muni_pr == "NJ_Princeton.txt"] <- "Municipality" 

zd.2019.final$type[zd.2019.final$statename == "NY" & zd.2019.final$muni_pr == "NY_SenecaFalls.txt"] <- "Town" 

zd.2019.final$place[zd.2019.final$statename == "NY" & zd.2019.final$muni_pr == "NY_WebsterVillage.txt"] <- "WebsterVillage" 

zd.2019.final$type[zd.2019.final$statename == "OH" & zd.2019.final$muni_pr == "OH_GreenTownship.txt"] <- "Township" 
zd.2019.final$place[zd.2019.final$statename == "OH" & zd.2019.final$muni_pr == "OH_GreenTownship.txt"] <- "GreenTownship" 

zd.2019.final$place[zd.2019.final$statename == "OH" & zd.2019.final$muni_pr == "OH_Washington.txt"] <- "WashingtonCity" 
zd.2019.final$type[zd.2019.final$statename == "OH" & zd.2019.final$muni_pr == "OH_Washington.txt"] <- "City" 

zd.2019.final$place[zd.2019.final$statename == "OH" & zd.2019.final$muni_pr == "OH_MiamiMontgomery.txt"] <- "MiamiMontgomery" 

zd.2019.final$place[zd.2019.final$statename == "OH" & zd.2019.final$muni_pr == "OH_Sycamore.txt"] <- "SycamoreTownship" 

zd.2019.final$place[zd.2019.final$statename == "OH" & zd.2019.final$muni_pr == "OH_BethelTownship.txt"] <- "BethelTownship" 

zd.2019.final$place[zd.2019.final$statename == "OH" & zd.2019.final$muni_pr == "OH_Plain.txt"] <- "PlainTownship" 

zd.2019.final$place[zd.2019.final$statename == "PA" & zd.2019.final$muni_pr == "PA_Concord.txt"] <- "ConcordTownship" 

zd.2019.final$place[zd.2019.final$statename == "PA" & zd.2019.final$muni_pr == "PA_Richland.txt"] <- "RichlandTownship" 

zd.2019.final$place[zd.2019.final$statename == "PA" & zd.2019.final$muni_pr == "PA_Salisbury.txt"] <- "SalisburyTownship" 

zd.2019.final$place[zd.2019.final$statename == "PA" & zd.2019.final$muni_pr == "PA_Spring.txt"] <- "SpringTownship" 

zd.2019.final$place[zd.2019.final$statename == "PA" & zd.2019.final$muni_pr == "PA_UpperProvidence.txt"] <- "UpperProvidenceTownship" 

zd.2019.final$place[zd.2019.final$statename == "PA" & zd.2019.final$muni_pr == "PA_White.txt"] <- "WhiteTownship" 

zd.2019.final$place[zd.2019.final$statename == "PA" & zd.2019.final$muni_pr == "PA_Amity.txt"] <- "AmityTownship" 

zd.2019.final$place[zd.2019.final$statename == "PA" & zd.2019.final$muni_pr == "PA_Amity.txt"] <- "AmityTownship" 

zd.2019.final$place[zd.2019.final$statename == "PA" & zd.2019.final$muni_pr == "PA_CranberryButler.txt"] <- "CranberryTownship" 

zd.2019.final$place[zd.2019.final$statename == "PA" & zd.2019.final$muni_pr == "PA_Douglass.txt"] <- "DouglassTownship" 

zd.2019.final$place[zd.2019.final$statename == "PA" & zd.2019.final$muni_pr == "PA_Ferguson.txt"] <- "FergusonTownship" 

zd.2019.final$place[zd.2019.final$statename == "PA" & zd.2019.final$muni_pr == "PA_Jackson.txt"] <- "JacksonTownship" 

zd.2019.final$place[zd.2019.final$statename == "PA" & zd.2019.final$muni_pr == "PA_Manchester.txt"] <- "ManchesterTownship" 

zd.2019.final$place[zd.2019.final$statename == "PA" & zd.2019.final$muni_pr == "PA_Montgomery.txt"] <- "MontgomeryTownship" 

zd.2019.final$place[zd.2019.final$statename == "PA" & zd.2019.final$muni_pr == "PA_Peters.txt"] <- "PetersTownship" 

zd.2019.final$place[zd.2019.final$statename == "PA" & zd.2019.final$muni_pr == "PA_Pine.txt"] <- "PineTownship"

zd.2019.final$place[zd.2019.final$statename == "PA" & zd.2019.final$muni_pr == "PA_Susquehanna.txt"] <- "SusquehannaTownship"

zd.2019.final$place[zd.2019.final$statename == "PA" & zd.2019.final$muni_pr == "PA_Warwick.txt"] <- "WarwickTownship"

zd.2019.final$place[zd.2019.final$statename == "PA" & zd.2019.final$muni_pr == "PA_Warrington.txt"] <- "WarringtonTownship"

zd.2019.final$place[zd.2019.final$statename == "PA" & zd.2019.final$muni_pr == "PA_Harrison.txt"] <- "HarrisonTownship"

zd.2019.final$place[zd.2019.final$statename == "PA" & zd.2019.final$muni_pr == "PA_Logan.txt"] <- "LoganTownship"

zd.2019.final$place[zd.2019.final$statename == "PA" & zd.2019.final$muni_pr == "PA_Middlesex.txt"] <- "MiddlesexTownship"

zd.2019.final$type[zd.2019.final$statename == "PA" & zd.2019.final$muni_pr == "PA_PennHills.txt"] <- "Township" 

zd.2019.final$type[zd.2019.final$statename == "PA" & zd.2019.final$muni_pr == "PA_McCandless.txt"] <- "Township" 

zd.2019.final$type[zd.2019.final$statename == "TN" & zd.2019.final$muni_pr == "TN_ChurchHill.txt"] <- "City" 

zd.2019.final$type[zd.2019.final$statename == "TX" & zd.2019.final$muni_pr == "TX_RoundRock.txt"] <- "City" 

zd.2019.final$type[zd.2019.final$statename == "TX" & zd.2019.final$muni_pr == "TX_Sinton.txt"] <- "City" 

zd.2019.final$type[zd.2019.final$statename == "TX" & zd.2019.final$muni_pr == "TX_SouthHouston.txt"] <- "City" 

zd.2019.final$type[zd.2019.final$statename == "TX" & zd.2019.final$muni_pr == "TX_TexasCity.txt"] <- "City" 

zd.2019.final$type[zd.2019.final$statename == "VA" & zd.2019.final$muni_pr == "VA_Bedford.txt"] <- "Town" 

zd.2019.final$type[zd.2019.final$statename == "VA" & zd.2019.final$muni_pr == "VA_Warrenton.txt"] <- "Town" 

zd.2019.final$type[zd.2019.final$statename == "VT" & zd.2019.final$muni_pr == "VT_StJohnsbury.txt"] <- "Town" 

zd.2019.final$type[zd.2019.final$statename == "WI" & zd.2019.final$muni_pr == "WI_RibMountain.txt"] <- "Town" 

zd.2019.final$place[zd.2019.final$statename == "WI" & zd.2019.final$muni_pr == "WI_Waunakee.txt"] <- "WaunakeeVillage"
zd.2019.final$type[zd.2019.final$statename == "WI" & zd.2019.final$muni_pr == "WI_Waunakee.txt"] <- "Village"

zd.2019.final$type[zd.2019.final$statename == "WV" & zd.2019.final$muni_pr == "WV_Huntington.txt"] <- "City"

zd.2019.final$type[zd.2019.final$statename == "WV" & zd.2019.final$muni_pr == "WV_Nitro.txt"] <- "City"

zd.2019.final$type[zd.2019.final$statename == "WY" & zd.2019.final$muni_pr == "WY_Buffalo.txt"] <- "City"

##################################
## stage 2: merge on FIPS codes ## 
##################################

vals <- c("_","-","()")

names(p2019.input) <- c("summary.level",
                        "state.fips",
                        "county.fips",
                        "countysub.fips",
                        "place.fips",
                        "ccity.fips",
                        "place.in")

## put back leading zeros ##

p2019 <- p2019.input %>%
  mutate(summary.level = str_pad(summary.level, 3, pad = "0"),
         state.fips = str_pad(state.fips, 2, pad = "0"),
         county.fips = str_pad(county.fips, 3, pad = "0"),
         countysub.fips = str_pad(countysub.fips, 5, pad = "0"),
         place.fips = str_pad(place.fips, 5, pad = "0"),
         ccity.fips = str_pad(ccity.fips, 5, pad = "0"),
         type = str_to_title(word(place.in, -1)),
         place.in2 = removeWords(place.in,remove.words1),
         place.in3 = removeWords(place.in2,remove.words2),
         place.in4 = str_replace(place.in3, "\\(\\)|\\-|\\'|\\_|\\.", ""),
         place = gsub(" ", "", place.in4)) %>%
  rename(sfp = state.fips)


## merge on state abbreviation ##

p2019.pr <- stata.merge(p2019,
                        ufips.recode,
                        "sfp")

## check merge ## 
table(p2019.pr$merge.variable)

## keep only matches ##
p2019.final <- p2019.pr %>%
  filter(merge.variable == 3) %>%
  select(-merge.variable)

## manually fix irregularities ##

p2019.final$type[p2019.final$statename == "AK" & p2019.final$place.fips == "03000"] <- "City"

p2019.final$type[p2019.final$statename == "AK" & p2019.final$place == "Petersburg"] <- "City"

p2019.final$type[p2019.final$statename == "AK" & p2019.final$place.fips == "70540"] <- "City"

p2019.final$place[p2019.final$statename == "CA" & p2019.final$place.fips == "11250"] <- "CarmelbytheSea"

p2019.final$place[p2019.final$statename == "CA" & p2019.final$place.fips == "39003"] <- "LaCanadaFlintridge"

p2019.final$type[p2019.final$statename == "CA" & p2019.final$place.fips == "45358"] <- "City"

p2019.final$place[p2019.final$statename == "CO" & p2019.final$place.fips == "11810"] <- "Canon"

p2019.final$type[p2019.final$statename == "CO" & p2019.final$place.fips == "50480"] <- "City"

p2019.final$place[p2019.final$statename == "CT" & p2019.final$place.fips == "34180"] <- "GrotonBorough"

p2019.final$type[p2019.final$statename == "CT" & p2019.final$place.fips == "34180"] <- "Borough"

p2019.final$place[p2019.final$statename == "CT" & p2019.final$countysub.fips == "34250"] <- "GrotonTown"

p2019.final$type[p2019.final$statename == "FL" & p2019.final$place.fips == "33600"] <- "City"

p2019.final$type[p2019.final$statename == "FL" & p2019.final$place.fips == "56625"] <- "City"

p2019.final$place[p2019.final$statename == "FL" & p2019.final$place.fips == "39475"] <- "LauderdalebytheSea"

p2019.final$type[p2019.final$statename == "HI" & p2019.final$place.fips == "71550"] <- "City"
p2019.final$place[p2019.final$statename == "HI" & p2019.final$place.fips == "71550"] <- "Honolulu"

p2019.final$type[p2019.final$statename == "IA" & p2019.final$place.fips == "10765"] <- "Town"

p2019.final$type[p2019.final$statename == "IL" & p2019.final$place.fips == "42028"] <- "City"

p2019.final$place[p2019.final$statename == "IL" & p2019.final$place.fips == "55249"] <- "OFallon"

p2019.final$type[p2019.final$statename == "IN" & p2019.final$place.fips == "15256"] <- "Town"

p2019.final$type[p2019.final$statename == "IN" & p2019.final$place.fips == "82700"] <- "Town"

p2019.final$type[p2019.final$statename == "KY" & p2019.final$place.fips == "72660"] <- "Town"

p2019.final$type[p2019.final$statename == "LA" & p2019.final$place.fips == "60880"] <- "Town"

p2019.final$type[p2019.final$statename == "MA" & p2019.final$place.fips == "00840"] <- "Town"

p2019.final$type[p2019.final$statename == "MA" & p2019.final$place.fips == "52144"] <- "Town"

p2019.final$type[p2019.final$statename == "MA" & p2019.final$countysub.fips == "60645"] <- "City"

p2019.final$place[p2019.final$statename == "MA" & p2019.final$countysub.fips == "37995"] <- "ManchesterbytheSea"

p2019.final$type[p2019.final$statename == "MA" & p2019.final$place.fips == "63345"] <- "Town"

p2019.final$type[p2019.final$statename == "MA" & p2019.final$place.fips == "73440"] <- "Town"

p2019.final$type[p2019.final$statename == "MA" & p2019.final$place.fips == "78972"] <- "Town"

p2019.final$type[p2019.final$statename == "ME" & p2019.final$place.fips == "65725"] <- "Town"

p2019.final$type[p2019.final$statename == "MI" & p2019.final$countysub.fips == "13660"] <- "Town"

p2019.final$place[p2019.final$statename == "MI" & p2019.final$place.fips == "33280"] <- "GrandBlancCity"

p2019.final$place[p2019.final$statename == "MI" & p2019.final$countysub.fips == "33300"] <- "GrandBlancTownship"

p2019.final$place[p2019.final$statename == "MI" & p2019.final$countysub.fips == "59000"] <- "NorthvilleTownship"

p2019.final$place[p2019.final$statename == "MI" & p2019.final$countysub.fips == "62040"] <- "OxfordTownship"

p2019.final$place[p2019.final$statename == "MI" & p2019.final$countysub.fips == "64660"] <- "PlainfieldTownship"

p2019.final$place[p2019.final$statename == "MI" & p2019.final$countysub.fips == "64660"] <- "PlainfieldTownship"

p2019.final$place[p2019.final$statename == "MI" & p2019.final$countysub.fips == "65060"] <- "PlymouthCity"
p2019.final$place[p2019.final$statename == "MI" & p2019.final$countysub.fips == "65080"] <- "PlymouthTownship"

p2019.final$place[p2019.final$statename == "MI" & p2019.final$countysub.fips == "70520"] <- "SaginawCity"
p2019.final$place[p2019.final$statename == "MI" & p2019.final$countysub.fips == "70540"] <- "SaginawTownship"

p2019.final$place[p2019.final$statename == "MI" & p2019.final$countysub.fips == "81340"] <- "UnionTownship"

p2019.final$place[p2019.final$statename == "MI" & p2019.final$countysub.fips == "51920"] <- "MarquetteTownship"

p2019.final$type[p2019.final$statename == "MI" & p2019.final$countysub.fips == "35060"] <- "Town"

p2019.final$place[p2019.final$statename == "MI" & p2019.final$countysub.fips == "71740"] <- "SaultSainteMarie"

p2019.final$type[p2019.final$statename == "MN" & p2019.final$countysub.fips == "72022"] <- "Township"

p2019.final$place[p2019.final$statename == "MN" & p2019.final$countysub.fips == "56680"] <- "StAnthonyCity"

p2019.final$place[p2019.final$statename == "MO" & p2019.final$place.fips == "54074"] <- "OFallon"

p2019.final$place[p2019.final$statename == "MO" & p2019.final$place.fips == "73618"] <- "TownandCountry"

p2019.final$type[p2019.final$statename == "MO" & p2019.final$place.fips == "61706"] <- "Municipality"

p2019.final$place[p2019.final$statename == "MO" & p2019.final$place.fips == "64180"] <- "SainteGenevieve"

p2019.final$type[p2019.final$statename == "NC" & p2019.final$place.fips == "42240"] <- "Town"

p2019.final$type[p2019.final$statename == "NC" & p2019.final$place.fips == "44320"] <- "City"

p2019.final$type[p2019.final$statename == "NH" & p2019.final$countysub.fips == "02820"] <- "Township"

p2019.final$type[p2019.final$statename == "NH" & p2019.final$countysub.fips == "02820"] <- "Township"

p2019.final$type[p2019.final$statename == "NH" & p2019.final$place.fips == "62900"] <- "Municipality"

p2019.final$place[p2019.final$statename == "NJ" & p2019.final$countysub.fips == "29310"] <- "HamiltonTownship"

p2019.final$place[p2019.final$statename == "NJ" & p2019.final$countysub.fips == "32310"] <- "HoHoKus"

p2019.final$place[p2019.final$statename == "NJ" & p2019.final$countysub.fips == "39510"] <- "LawrenceTownship"

p2019.final$place[p2019.final$statename == "NJ" & p2019.final$countysub.fips == "33180"] <- "HopewellTownship"

p2019.final$place[p2019.final$statename == "NJ" & p2019.final$countysub.fips == "70020"] <- "SpringfieldTownship"

p2019.final$place[p2019.final$statename == "NJ" & p2019.final$countysub.fips == "77240"] <- "WashingtonTownship"

p2019.final$type[p2019.final$statename == "NJ" & p2019.final$countysub.fips == "20230"] <- "Town"

p2019.final$type[p2019.final$statename == "NJ" & p2019.final$place.fips == "26610"] <- "City"

p2019.final$place[p2019.final$statename == "NJ" & p2019.final$place.fips == "24930"] <- "FranklinBorough"

p2019.final$type[p2019.final$statename == "NJ" & p2019.final$countysub.fips == "34450"] <- "Town"

p2019.final$type[p2019.final$statename == "NJ" & p2019.final$place.fips == "60900"] <- "Municipality"

p2019.final$place[p2019.final$statename == "NJ" & p2019.final$place.fips == "74630"] <- "UnionCity"

p2019.final$place[p2019.final$statename == "NJ" & p2019.final$countysub.fips == "74480"] <- "UnionTownship"

p2019.final$place[p2019.final$statename == "NY" & p2019.final$place.fips == "17332"] <- "ColonieVillage"
p2019.final$place[p2019.final$statename == "NY" & p2019.final$countysub.fips == "17343"] <- "ColonieTown"

p2019.final$place[p2019.final$statename == "NY" & p2019.final$place.fips == "19213"] <- "CrotononHudson"

p2019.final$place[p2019.final$statename == "NY" & p2019.final$place.fips == "32710"] <- "HastingsonHudson"

p2019.final$place[p2019.final$statename == "NY" & p2019.final$place.fips == "78960"] <- "WebsterVillage"

p2019.final$place[p2019.final$statename == "NM" & p2019.final$place.fips == "25170"] <- "Española"

p2019.final$type[p2019.final$statename == "OH" & p2019.final$place.fips == "11332"] <- "Village"

p2019.final$type[p2019.final$statename == "OH" & p2019.final$place.fips == "11332"] <- "Village"

p2019.final$type[p2019.final$statename == "OH" & p2019.final$place.fips == "29932"] <- "Village"

p2019.final$place[p2019.final$statename == "OH" & p2019.final$place.fips == "49098"] <- "MentorontheLake"

p2019.final$place[p2019.final$statename == "OH" & p2019.final$countysub.fips == "81718"] <- "WashingtonCity"

p2019.final$place[p2019.final$statename == "OH" & p2019.final$countysub.fips == "49392"] <- "MiamiMontgomery"

p2019.final$place[p2019.final$statename == "OH" & p2019.final$countysub.fips == "75973"] <- "SycamoreTownship"

p2019.final$place[p2019.final$statename == "OH" & p2019.final$countysub.fips == "06110"] <- "BethelTownship"

p2019.final$place[p2019.final$statename == "OH" & p2019.final$countysub.fips == "62988"] <- "PlainTownship"

p2019.final$place[p2019.final$statename == "OH" & p2019.final$countysub.fips == "31860"] <- "GreenCity"
p2019.final$type[p2019.final$statename == "OH" & p2019.final$countysub.fips == "31860"] <- "City"

p2019.final$place[p2019.final$statename == "OH" & p2019.final$countysub.fips == "31752"] <- "GreenTownship"

p2019.final$place[p2019.final$statename == "OH" & p2019.final$countysub.fips == "76582"] <- "IndianHill"

p2019.final$type[p2019.final$statename == "OH" & p2019.final$place.fips == "64486"] <- "Village"

p2019.final$type[p2019.final$statename == "OH" & p2019.final$countysub.fips == "81494"] <- "City"

p2019.final$place[p2019.final$statename == "OH" & p2019.final$county.fips == "025" & p2019.final$countysub.fips == "49322"] <- "MiamiClermont"
p2019.final$place[p2019.final$statename == "OH" & p2019.final$county.fips == "113" & p2019.final$countysub.fips == "49392"] <- "MiamiMontgomery"

p2019.final$type[p2019.final$statename == "OK" & p2019.final$place.fips == "67850"] <- "Town"

p2019.final$place[p2019.final$statename == "PA" & p2019.final$countysub.fips == "15488"] <- "ConcordTownship"

p2019.final$place[p2019.final$statename == "PA" & p2019.final$countysub.fips == "64544"] <- "RichlandTownship"

p2019.final$place[p2019.final$statename == "PA" & p2019.final$countysub.fips == "67576"] <- "SalisburyTownship"

p2019.final$place[p2019.final$statename == "PA" & p2019.final$countysub.fips == "72824"] <- "SpringTownship"

p2019.final$place[p2019.final$statename == "PA" & p2019.final$countysub.fips == "79256"] <- "UpperProvidenceTownship"

p2019.final$place[p2019.final$statename == "PA" & p2019.final$countysub.fips == "84472"] <- "WhiteTownship"

p2019.final$place[p2019.final$statename == "PA" & p2019.final$countysub.fips == "02328"] <- "AmityTownship"

p2019.final$place[p2019.final$statename == "PA" & p2019.final$countysub.fips == "16920"] <- "CranberryButler"

p2019.final$place[p2019.final$statename == "PA" & p2019.final$countysub.fips == "19672"] <- "DouglassTownship"

p2019.final$place[p2019.final$statename == "PA" & p2019.final$countysub.fips == "25624"] <- "FergusonTownship"

p2019.final$place[p2019.final$statename == "PA" & p2019.final$countysub.fips == "37488"] <- "JacksonTownship"

p2019.final$place[p2019.final$statename == "PA" & p2019.final$countysub.fips == "46872"] <- "ManchesterTownship"

p2019.final$place[p2019.final$statename == "PA" & p2019.final$countysub.fips == "50640"] <- "MontgomeryTownship"

p2019.final$place[p2019.final$statename == "PA" & p2019.final$countysub.fips == "44328"] <- "LoganTownship"

p2019.final$place[p2019.final$statename == "PA" & p2019.final$countysub.fips == "60272"] <- "PineTownship"

p2019.final$place[p2019.final$statename == "PA" & p2019.final$countysub.fips == "75528"] <- "SusquehannaTownship"

p2019.final$place[p2019.final$statename == "PA" & p2019.final$countysub.fips == "49056"] <- "MiddlesexTownship"

p2019.final$type[p2019.final$statename == "PA" & p2019.final$place.fips == "23584"] <- "City"

p2019.final$place[p2019.final$statename == "PA" & p2019.final$place.fips == "41216"] <- "LancasterCity"

p2019.final$place[p2019.final$statename == "PA" & p2019.final$countysub.fips == "41224"] <- "LancasterTownship"

p2019.final$place[p2019.final$statename == "PA" & p2019.final$countysub.fips == "46896"] <- "ManheimTownship"

p2019.final$place[p2019.final$statename == "PA" & p2019.final$countysub.fips == "46888"] <- "ManheimBorough"

p2019.final$place[p2019.final$statename == "PA" & p2019.final$place.fips == "49128"] <- "MiddletownBorough"

p2019.final$place[p2019.final$statename == "PA" & p2019.final$countysub.fips == "59608"] <- "PetersTownship"

p2019.final$place[p2019.final$statename == "PA" & p2019.final$countysub.fips == "81144"] <- "WarwickTownship"

p2019.final$place[p2019.final$statename == "PA" & p2019.final$countysub.fips == "81048"] <- "WarringtonTownship"

p2019.final$place[p2019.final$statename == "PA" & p2019.final$countysub.fips == "32832"] <- "HarrisonTownship"

p2019.final$place[p2019.final$statename == "PA" & p2019.final$county.fips == "017" & p2019.final$countysub.fips == "49120"] <- "MiddletownBucks"
p2019.final$place[p2019.final$statename == "PA" & p2019.final$county.fips == "045" & p2019.final$countysub.fips == "49136"] <- "MiddletownDelaware"

p2019.final$type[p2019.final$statename == "PA" & p2019.final$place.fips == "50528"] <- "Township"

p2019.final$place[p2019.final$statename == "PA" & p2019.final$countysub.fips == "54192"] <- "NewtownBucks"

p2019.final$place[p2019.final$statename == "PA" & p2019.final$countysub.fips == "54224"] <- "NewtownDelaware"

p2019.final$type[p2019.final$statename == "RI" & p2019.final$countysub.fips == "51580"] <- "Township"

p2019.final$place[p2019.final$statename == "SC" & p2019.final$place.fips == "36115"] <- "IsleofPalms"

p2019.final$place[p2019.final$statename == "VT" & p2019.final$place.fips == "03175"] <- "BarreCity"

p2019.final$place[p2019.final$statename == "VT" & p2019.final$countysub.fips == "03250"] <- "BarreTown"

p2019.final$place[p2019.final$statename == "WI" & p2019.final$place.fips == "19450"] <- "DelavanCity"
p2019.final$place[p2019.final$statename == "WI" & p2019.final$countysub.fips == "19475"] <- "DelavanTown"

p2019.final$place[p2019.final$statename == "WI" & p2019.final$place.fips == "23525"] <- "EllsworthVillage"
p2019.final$place[p2019.final$statename == "WI" & p2019.final$countysub.fips == "23550"] <- "EllsworthTown"

p2019.final$place[p2019.final$statename == "WI" & p2019.final$place.fips == "50825"] <- "MenashaCity"
p2019.final$place[p2019.final$statename == "WI" & p2019.final$county.fips == "139"] <- "MenashaTown"
p2019.final$countysub.fips[p2019.final$statename == "WI" & p2019.final$county.fips == "139"] <- "50850"

p2019.final$place[p2019.final$statename == "WI" & p2019.final$countysub.fips == "55075"] <- "MukwonagoTown"
p2019.final$place[p2019.final$statename == "WI" & p2019.final$county.fips == "133" & p2019.final$countysub.fips == "55050"] <- "MukwonagoVillage"

p2019.final$place[p2019.final$statename == "WI" & p2019.final$place.fips == "59925"] <- "OnalaskaCity"
p2019.final$place[p2019.final$statename == "WI" & p2019.final$countysub.fips == "59950"] <- "OnalaskaTown"

p2019.final$place[p2019.final$statename == "WI" & p2019.final$place.fips == "84350"] <- "WaunakeeVillage"


## merge on FIPS codes ## 

## merge checks ## 

nrow(zd.2019.final) == length(unique(paste(zd.2019.final$statename,
                                           zd.2019.final$place,
                                           zd.2019.final$type)))

check1 <- zd.2019.final %>%
  group_by(statename, place, type) %>%
  summarize(n=n()) %>%
  filter(n > 1)

check2 <- p2019.final %>%
  group_by(statename, place, type) %>%
  summarize(n=n()) %>%
  filter(n > 1)

class(zd.2019.final$place)
class(zd.2019.final$statename)
class(zd.2019.final$type)


nrow(p2019.final) == length(unique(paste(p2019.final$statename,
                                         p2019.final$place,
                                         p2019.final$type)))

class(p2019.final$place)
class(p2019.final$statename)
class(p2019.final$type)

## merge data frames ## 

zd.full.merged <- stata.merge(zd.2019.final,
                              p2019.final,
                              c("statename","place","type"))

## check merge ##
table(zd.full.merged$merge.variable)

## keep only matches ## 

zd.full.matches <- zd.full.merged %>%
  filter(merge.variable ==3) %>%
  select(-merge.variable)

## fix the duplicates ## 

zd.full.matches$countysub.fips[zd.full.matches$countysub.fips == '00000'] <- ''
zd.full.matches$ccity.fips[zd.full.matches$ccity.fips == '00000'] <- ''
zd.full.matches$place.fips[zd.full.matches$place.fips == '00000'] <- ''

zd.full.final <- zd.full.matches %>%
  group_by(statename,place,type) %>%
  summarize(restrict_sf_permit = mean(restrict_sf_permit),
            restrict_mf_permit = mean(restrict_mf_permit),
            limit_sf_units = mean(limit_sf_units),
            limit_mf_units = mean(limit_mf_units),
            limit_mf_dwellings = mean(limit_mf_dwellings),
            limit_mf_dwelling_units = mean(limit_mf_dwelling_units),
            min_lot_size = mean(min_lot_size),
            open_space = mean(open_space),
            inclusionary = mean(inclusionary),
            half_acre_less = mean(nhalf_acre_less),
            half_acre_more = mean(nhalf_acre_more),
            one_acre_more = mean(none_acre_more),
            two_acre_more = mean(two_acre_more),
            max_den_cat1 = mean(nmax_den_cat1),
            max_den_cat2 = mean(nmax_den_cat2),
            max_den_cat3 = mean(nmax_den_cat3),
            max_den_cat4 = mean(nmax_den_cat4),
            max_den_cat5 = mean(max_den_cat5),
            council_nz = mean(council_nz),
            planning_nz = mean(planning_nz),
            countybrd_nz = mean(countybrd_nz), 
            pubhlth_nz = mean(pubhlth_nz),
            site_plan_nz = mean(site_plan_nz),
            env_rev_nz = mean(env_rev_nz),
            council_rz = mean(council_rz),
            planning_rz = mean(planning_rz),
            zoning_rz = mean(zoning_rz), 
            countybrd_rz = mean(countybrd_rz),
            countyzone_rz = mean(countyzone_rz),
            townmeet_rz = mean(townmeet_rz),
            env_rev_rz = mean(env_rev_rz),
            total_nz = mean(total_nz),
            total_rz = mean(total_rz),
            adu = mean(adu),
            height_ft_median = mean(height_ft_median),
            height_ft_mode = mean(height_ft_mode),
            height_st_median = mean(height_st_median),
            height_st_mode = mean(height_st_mode),
            parking_median = mean(parking_median),
            parking_mode = mean(parking_mode),
            mf_per = mean(`mf per`),
            timestamp = timestamp[which(timestamp!="")[1]],
            state.fips = sfp[which(sfp != "")[1]],
            countysub.fips = countysub.fips[which(countysub.fips != "")[1]],
            place.fips = place.fips[which(place.fips != "")[1]],
            state = state[which(state != "")[1]])

## manually fix incorrect FIPS codes ##

zd.full.final$place.fips[zd.full.final$statename=="AK" & zd.full.final$place == "Petersburg" & zd.full.final$type == "City"] <- "60310"
zd.full.final$place.fips[zd.full.final$statename=="AK" & zd.full.final$place == "Yakutat" & zd.full.final$type == "Borough"] <- "86490"
zd.full.final$place.fips[zd.full.final$statename=="IN" & zd.full.final$place == "Indianapolis" & zd.full.final$type == "City"] <- "36003"

## diagnostics ## 

sum(is.na(zd.full.final$place.fips) & is.na(zd.full.final$countysub.fips))
sum(is.na(zd.full.final$place.fips) & !is.na(zd.full.final$countysub.fips))
sum(!is.na(zd.full.final$place.fips) & is.na(zd.full.final$countysub.fips))
sum(!is.na(zd.full.final$place.fips) & !is.na(zd.full.final$countysub.fips))

## create GEOID ##
zd.full.final$fips.cb <- ifelse(is.na(zd.full.final$countysub.fips), 
                                      zd.full.final$place.fips,
                                      zd.full.final$countysub.fips)

## diagnostics ## 
sum(is.na(zd.full.final$fips.cb))
sum(zd.full.final$fips.cb == "")

zd.full.final$GEOID <- paste(zd.full.final$state.fips,
                             zd.full.final$fips.cb,
                             sep ="")

## diagnose the GEOID var ## 
range(nchar(trim(zd.full.final$GEOID)))
nrow(zd.full.final) == length(unique(zd.full.final$GEOID))

## select final variables ## 
nzlu.2019 <- zd.full.final %>%
  select(GEOID,
         statename,
         place,
         type,
         restrict_sf_permit,
         restrict_mf_permit,
         limit_sf_units,
         limit_mf_units,
         limit_mf_dwellings,
         limit_mf_dwelling_units,
         min_lot_size,
         open_space,
         inclusionary,
         half_acre_less,
         half_acre_more,
         one_acre_more,
         two_acre_more,
         max_den_cat1,
         max_den_cat2,
         max_den_cat3,
         max_den_cat4,
         max_den_cat5,
         council_nz,
         planning_nz,
         countybrd_nz,
         pubhlth_nz,
         site_plan_nz,
         env_rev_nz,
         council_rz,
         planning_rz,
         zoning_rz,
         countybrd_rz,
         countyzone_rz,
         townmeet_rz,
         env_rev_rz,
         total_nz,
         total_rz,
         adu,
         height_ft_median,
         height_ft_mode,
         height_st_median,
         height_st_mode,
         parking_median,
         parking_mode,
         mf_per,
         timestamp)

nzlu.2019 <- nzlu.2019 %>%
  mutate(maxden5 = max_den_cat5,
         maxden4 = ifelse(max_den_cat5 == 1, 0, max_den_cat4),
         maxden3 = ifelse(max_den_cat5 == 1 | max_den_cat4 == 1, 0, max_den_cat3),
         maxden2 = ifelse(max_den_cat5 == 1 | max_den_cat4 == 1 | max_den_cat3 == 1, 0, max_den_cat2),
         maxden1 = ifelse(max_den_cat5 == 1 | max_den_cat4 == 1 | max_den_cat3 == 1 | max_den_cat2 == 1, 0, max_den_cat1))

## fix missing max density info ## 
sum(is.na(nzlu.2019$maxden5) & 
    is.na(nzlu.2019$maxden4) & 
    is.na(nzlu.2019$maxden3) & 
    is.na(nzlu.2019$maxden2) & 
    is.na(nzlu.2019$maxden1))

sum(is.na(nzlu.2019$maxden5) & 
    is.na(nzlu.2019$maxden4) & 
    is.na(nzlu.2019$maxden3) & 
    is.na(nzlu.2019$maxden2) & 
    is.na(nzlu.2019$maxden1) & 
    (!is.na(nzlu.2019$two_acre_more) | 
     !is.na(nzlu.2019$one_acre_more) | 
     !is.na(nzlu.2019$half_acre_more) | 
     !is.na(nzlu.2019$half_acre_less)))

nzlu.2019.fix.maxden <- nzlu.2019 %>%
  filter(is.na(maxden5) & 
         is.na(maxden4) & 
         is.na(maxden3) & 
         is.na(maxden2) & 
         is.na(maxden1) & 
         (!is.na(two_acre_more) | 
          !is.na(one_acre_more) | 
          !is.na(half_acre_more) | 
          !is.na(half_acre_less)))

## this affects 2 obs ##
## both have 1 acre minimums, so max den cat == 1 ##

nzlu.2019.fix.maxden <- nzlu.2019.fix.maxden %>%
  mutate(maxden1 = 1,
         maxden2 = 0,
         maxden3 = 0,
         maxden4 = 0,
         maxden5 = 0)

## fix missing min lot size info ## 
sum(is.na(nzlu.2019$two_acre_more) & 
    is.na(nzlu.2019$one_acre_more) & 
    is.na(nzlu.2019$half_acre_more) & 
    is.na(nzlu.2019$half_acre_less))

sum(nzlu.2019$two_acre_more == 0 & 
    nzlu.2019$one_acre_more == 0 & 
    nzlu.2019$half_acre_more == 0 & 
    nzlu.2019$half_acre_less == 0, na.rm=T)

nzlu.2019.fix.mls <- nzlu.2019 %>%
  filter((is.na(two_acre_more) & 
          is.na(one_acre_more) & 
          is.na(half_acre_more) & 
          is.na(half_acre_less)) | 
          (two_acre_more == 0 & 
           one_acre_more == 0 & 
           half_acre_more == 0 & 
           half_acre_less == 0))


nzlu.2019.fix.mls$mls_new <- 0
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "0128552"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "0610928"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "0614736"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "0620956"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "0625380"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "0644028"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "0658380"] <- 4
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "0810600"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "0937280"] <- 4 
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "1241250"] <- 3 
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "1254075"] <- 4
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "1268275"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "1320064"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "1321072"] <- 3
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "1601900"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "1809532"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "1880306"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "1880306"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "1978285"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "1962355"] <- 2
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "2005775"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "2130700"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "2385850"] <- 2
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "2537175"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "2542285"] <- 4
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "2562535"] <- 1 
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "2612320"] <- 1 
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "2634000"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "2640960"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "2646040"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "2665060"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "2700928"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "2723318"] <- 4
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "2751316"] <- 4
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "2751730"] <- 4
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "2759008"] <- 4
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "2761492"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "2768548"] <- 4
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "2813820"] <- 1 
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "3119595"] <- 4
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "3301300"] <- 4
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "3302820"] <- 4
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "3311380"] <- 4
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "3324340"] <- 4
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "3352340"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "3407600"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "3461530"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "3474480"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "3604000"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "3635672"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "3639232"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "3643005"] <- 4
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "3644787"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "3654837"] <- 2 
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "3666993"] <- 3
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "3684099"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "3713240"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "3901672"] <- 3
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "3904500"] <- 2
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "3943554"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "3944366"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "4206904"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "4226280"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "4229720"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "4232328"] <- 2
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "4254696"] <- 3
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "4442400"] <- 4
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "4636220"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "4715480"] <- 1 
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "4725760"] <- 4  
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "4727020"] <- 4 
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "4800160"] <- 3 
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "4803144"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "4806060"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "4809556"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "4811300"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "4820140"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "4824036"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "4826160"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "4827996"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "4833068"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "4834502"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "4836092"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "4843240"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "4843888"] <- 3
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "4849128"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "4855008"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "4860164"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "4863044"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "4864064"] <- 2
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "4865516"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "4869932"] <- 3
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "4871384"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "4871684"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "4872989"] <- 1
nzlu.2019.fix.mls$min_lot_size[nzlu.2019.fix.mls$GEOID == "4875476"] <- 0
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "4875476"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "4876228"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "4876948"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "5003550"] <- 4
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "5013300"] <- 4
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "5059275"] <- 3
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "5076975"] <- 4
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "5084925"] <- 4
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "5424580"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "5437636"] <- 1
nzlu.2019.fix.mls$mls_new[nzlu.2019.fix.mls$GEOID == "5536275"] <- 4


nzlu.2019.fix.mls <- nzlu.2019.fix.mls %>%
  mutate(two_acre_more = case_when(mls_new == 4 ~ 1,
                                   TRUE ~ 0), 
         one_acre_more = case_when(mls_new == 3 ~ 1,
                                   TRUE ~ 0),
         half_acre_more = case_when(mls_new == 2 ~ 1,
                                    TRUE ~ 0),
         half_acre_less = case_when(mls_new == 1 ~ 1,
                                    TRUE ~ 0)) %>%
  select(-mls_new)

## check ## 
nzlu.2019.fix.mls.check <- nzlu.2019.fix.mls %>%
  select(GEOID, 
         statename, 
         place, 
         half_acre_less,
         half_acre_more,
         one_acre_more,
         two_acre_more)

nzlu.2019.rd <- nzlu.2019 %>%
  filter(GEOID %notin% c(nzlu.2019.fix.maxden$GEOID,
                         nzlu.2019.fix.mls$GEOID))

nzlu.2019.final <- rbind(nzlu.2019.rd,
                         nzlu.2019.fix.maxden,
                         nzlu.2019.fix.mls)

nzlu.2019.final <- nzlu.2019.final[order(nzlu.2019.final$GEOID),]

## impute missing ADU ##
nzlu.2019.final$adu[nzlu.2019.final$GEOID == "4249184"] <- 0

## fix incorrect GEOIDs ##

nzlu.2019.final$GEOID[nzlu.2019.final$GEOID == "2365725"] <- "2365760"
nzlu.2019.final$GEOID[nzlu.2019.final$GEOID == "3460900"] <- "3460915"
nzlu.2019.final$GEOID[nzlu.2019.final$GEOID == "2054400"] <- "2054450"

## Princeton NJ township and borough combine in 2013 ##

nzlu.2019.final$GEOID[nzlu.2019.final$GEOID == "3460915"]<- "3460900"
nzlu.2019.final$type[nzlu.2019.final$GEOID == "3460900"]<- "Municipality"


## Sanford Town, ME becomes Sanford City, ME in ##

nzlu.2019.final$GEOID[nzlu.2019.final$GEOID == "2365760"]<- "2365725"
nzlu.2019.final$type[nzlu.2019.final$GEOID == "2365725"]<- "City"


## output final file ## 

save(nzlu.2019.final,
     file = paste(output_path,
                  "001_nzlu_2019.Rda",
                  sep=""))

##########
## MSAs ##
##########


## 2020 MSA delineation file ## 

names(msa.del.2020) <- as.matrix(msa.del.2020[2,])

msa.del.2020 <- msa.del.2020[-c(1,2),]

msa.del.2020.rd <- msa.del.2020 %>%
  filter(`Metropolitan/Micropolitan Statistical Area` == 'Metropolitan Statistical Area') %>%
  mutate(cbsa10 = `CBSA Code`,
         FIPS = paste(`FIPS State Code`, 
                      `FIPS County Code`,
                      sep = ""))

msa.del.2020.check <- msa.del.2020.rd %>%
  group_by(`CBSA Code`) %>%
  summarize(n = n()) %>%
  rename(cbsa10 = `CBSA Code`)

## check that this has 392 unique MSAs ##
nrow(msa.del.2020.check) == 392

## 2000 to 2010 MSA crosswalk file - place ## 

place.to.msa.2010 <- place.to.msa.2010[-1,]

range(nchar(trim(place.to.msa.2010$state)))
range(nchar(trim(place.to.msa.2010$placefp)))

## updates ## 
## these are primarily micropolitan areas that have since become metro areas ##

place.to.msa.2010$cbsa10[place.to.msa.2010$cbsa10 == "11300"] <- "26900"
place.to.msa.2010$cbsa10[place.to.msa.2010$cbsa10 == "11340"] <- "24860"
place.to.msa.2010$cbsa10[place.to.msa.2010$cbsa10 == "14060"] <- "14010"
place.to.msa.2010$cbsa10[place.to.msa.2010$cbsa10 == "19380"] <- "19430"
place.to.msa.2010$cbsa10[place.to.msa.2010$cbsa10 == "26180"] <- "46520"
place.to.msa.2010$cbsa10[place.to.msa.2010$cbsa10 == "29140"] <- "29200"
place.to.msa.2010$cbsa10[place.to.msa.2010$cbsa10 == "31100"] <- "31080"
place.to.msa.2010$cbsa10[place.to.msa.2010$cbsa10 == "37380"] <- "19660"
place.to.msa.2010$cbsa10[place.to.msa.2010$cbsa10 == "37700"] <- "25060"
place.to.msa.2010$cbsa10[place.to.msa.2010$cbsa10 == "39140"] <- "39150"
place.to.msa.2010$cbsa10[place.to.msa.2010$cbsa10 == "42060"] <- "42200"
place.to.msa.2010$cbsa10[place.to.msa.2010$cbsa10 == "44600"] <- "48260"
place.to.msa.2010$cbsa10[place.to.msa.2010$cbsa10 == "30500"] <- "15680"

## create GEOID ##

place.to.msa.2010$GEOID <- paste(place.to.msa.2010$state,
                                 place.to.msa.2010$placefp,
                                 sep = "")

ptm.2010.rd <- place.to.msa.2010 %>%
  filter(grepl("Metro",
               cbsaname10, 
               fixed = TRUE) == TRUE | 
           cbsa10 %in% c("10540",
                         "13220",
                         "14100",
                         "15680",
                         "16060",
                         "16540",
                         "19300",
                         "20700",
                         "21420",
                         "23900",
                         "24260",
                         "24420",
                         "25220",
                         "25940",
                         "26140",
                         "27980",
                         "33220",
                         "35100",
                         "42700",
                         "43420",
                         "44420",
                         "45540",
                         "46300",
                         "47460",
                         "48060"))

## drop micro areas ## 
ptm.2010.rd <- filter(ptm.2010.rd, cbsa10 %notin% c("26090",
                                                    "41780"))

## group by CBSA code ##
ptm.2010.rd.check <- ptm.2010.rd %>%
  group_by(cbsa10) %>%
  summarize(n=n())

## 2000 to 2010 MSA crosswalk file - county sub ## 

cs.to.msa.2010 <- countysub.to.msa.2010[-1,]

range(nchar(trim(cs.to.msa.2010$cousubfp)))

## drop micro areas ## 
cs.to.msa.2010 <- filter(cs.to.msa.2010, cbsa10 %notin% c("26100",
                                                          "41780"))

## updates ## 
## these are primarily micropolitan areas that have since become metro areas ##
cs.to.msa.2010$cbsa10[cs.to.msa.2010$cbsa10 == "10380"] <- "39660"
cs.to.msa.2010$cbsa10[cs.to.msa.2010$cbsa10 == "11300"] <- "26900"
cs.to.msa.2010$cbsa10[cs.to.msa.2010$cbsa10 == "11340"] <- "24860"
cs.to.msa.2010$cbsa10[cs.to.msa.2010$cbsa10 == "14060"] <- "14010"
cs.to.msa.2010$cbsa10[cs.to.msa.2010$cbsa10 == "19380"] <- "19430"
cs.to.msa.2010$cbsa10[cs.to.msa.2010$cbsa10 == "26180"] <- "46520"
cs.to.msa.2010$cbsa10[cs.to.msa.2010$cbsa10 == "29140"] <- "29200"
cs.to.msa.2010$cbsa10[cs.to.msa.2010$cbsa10 == "31100"] <- "31080"
cs.to.msa.2010$cbsa10[cs.to.msa.2010$cbsa10 == "37380"] <- "25060"
cs.to.msa.2010$cbsa10[cs.to.msa.2010$cbsa10 == "42060"] <- "42200"
cs.to.msa.2010$cbsa10[cs.to.msa.2010$cbsa10 == "44600"] <- "48260"
cs.to.msa.2010$cbsa10[cs.to.msa.2010$cbsa10 == "37700"] <- "25060"
cs.to.msa.2010$cbsa10[cs.to.msa.2010$cbsa10 == "39140"] <- "39150"
cs.to.msa.2010$cbsa10[cs.to.msa.2010$cbsa10 == "30500"] <- "15680"


cstm.2010.rd <- cs.to.msa.2010 %>%
  mutate(state = substr(county,1,2),
         GEOID = paste(state,
                       cousubfp,
                       sep="")) %>%
  filter(grepl("Metro",
               cbsaname10, 
               fixed = TRUE) == TRUE| 
           cbsa10 %in% c("39660",
                         "10540",
                         "13220",
                         "14100",
                         "15680",
                         "16060",
                         "16540",
                         "19300",
                         "20700",
                         "21420",
                         "23900",
                         "24260",
                         "24420",
                         "25220",
                         "25940",
                         "26140",
                         "27980",
                         "33220",
                         "35100",
                         "42700",
                         "43420",
                         "44420",
                         "45540",
                         "46300",
                         "47460",
                         "48060"))


cstm.2010.rd.check <- cstm.2010.rd %>%
  group_by(cbsa10) %>%
  summarize(n=n())

## merge checks ##

nrow(msa.del.2020.check) == length(unique(msa.del.2020.check$cbsa10))
class(msa.del.2020.check$cbsa10)
range(nchar(trim(msa.del.2020.check$cbsa10)))

nrow(cstm.2010.rd.check) == length(unique(cstm.2010.rd.check$cbsa10))
class(cstm.2010.rd.check$cbsa10)
range(nchar(trim(cstm.2010.rd.check$cbsa10)))

nrow(ptm.2010.rd.check) == length(unique(ptm.2010.rd.check$cbsa10))
class(ptm.2010.rd.check$cbsa10)
range(nchar(trim(ptm.2010.rd.check$cbsa10)))

## merge files to make sure there are 384 metros ##
## 392 - 8 MSAs in Puerto Rico ## 

cbsa.merge.check1 <- stata.merge(msa.del.2020.check,
                                 ptm.2010.rd.check,
                                 "cbsa10")

## check merge ## 
table(cbsa.merge.check1$merge.variable)

cbsa.merge.check2 <- stata.merge(msa.del.2020.check,
                                 cstm.2010.rd.check,
                                 "cbsa10")

## check merge ## 
table(cbsa.merge.check2$merge.variable)

## output files ##

save(ptm.2010.rd,
     file = paste(output_path,
                  "001_ptm_2010.Rda",
                  sep=""))

save(cstm.2010.rd,
     file = paste(output_path,
                  "001_cstm_2010.Rda",
                  sep=""))


### END OF PROGRAM ###

#sink()