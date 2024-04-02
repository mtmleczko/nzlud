########################################################
## PROGRAM NAME: 004_compare.R                        ##
## AUTHOR: MATT MLECZKO                               ##
## DATE CREATED: 12/29/2021                           ##
## INPUTS:                                            ##
##    msa_delineation_2020.xls                        ##
##    acs_rank_H_1519_out.dta                         ##
##    2019_ACS_tracts_p1.Rda                          ##
##    2019_ACS_tracts_p2.Rda                          ##
##    nzlu_ts.Rda                                     ##
##    001_zd_nonmatches.Rda                           ##
##    001_wrld_2018.Rda                               ##
##    001_wrld_panel_2018.Rda                         ## 
##    001_nllus_2019.Rda                              ## 
##    002_wrld_nllus_place_2006.Rda                   ##
##    002_wrld_nllus_msasample_2006.Rda               ##
##    002_wrld_nllus_msa_2006.Rda                     ##
##    002_wrld_msa_2018.Rda                           ##
##    002_nllus_msa_2019.Rda                          ##
##    002_nzlu_place_2019.Rda                         ##
##    002_nzlu_msa_2019.Rda                           ##
##    002_nzlu_msasample_2019.Rda                     ##
##    002_all_place_2019.Rda                          ##
##    002_all_msa_2019.Rda                            ##
##    003_wrld_nzlu_wts_all_2006.Rda                  ##
##    003_wrld_nzlu_wts_msa_2006.Rda                  ##
##    003_wrld_nzlu_wts_all_2019.Rda                  ##
##    003_wrld_nzlu_wts_msa_2019.Rda                  ##
##    003_all_munis_2019.Rda                          ##
##    003_msa_munis_2019.Rda                          ##
##                                                    ##
## OUTPUTS:                                           ##
##    nzlu_data.Rda                                   ##
##    nzlu_data.csv                                   ##
##                                                    ##
## PURPOSE: Compare original zoning data with         ##
##          WRLD 2018 and NLLUS 2019 samples;         ##
##          output NZLUD                              ##
##                                                    ##
## LIST OF UPDATES:                                   ##
## 04/02/2024 MTM: Added code to process              ##
##                 alltracts.2019.p1 and              ##
##                 alltracts.2019.p2 (original file   ##
##                 was too large for GitHub           ##
########################################################

#log <- file("path to programs here/004_compare.txt")
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
library("mice")
library("reldist")
library("ggplot2")
library("tidycensus")
library("tigris")
library("sf")
library("RColorBrewer")
library("stats")

census_api_key("CENSUS API KEY HERE")
options(tigris_use_cache = TRUE)

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
load("001_zd_nonmatches.Rda")
load("001_wrld_2018.Rda")
load("001_wrld_panel_2018.Rda")
load("001_nllus_2019.Rda")
load("002_wrld_nllus_place_2006.Rda")           
load("002_wrld_nllus_msa_2006.Rda") 
load("002_wrld_nllus_msasample_2006.Rda")  
load("002_wrld_msa_2018.Rda")
load("002_nllus_msa_2019.Rda")
load("002_nzlu_place_2019.Rda")
load("002_nzlu_msasample_2019.Rda")
load("002_nzlu_msa_2019.Rda")
load("002_all_place_2019.Rda")
load("002_all_msa_2019.Rda")
load("003_wrld_nllus_wts_all_2006.Rda")
load("003_wrld_nllus_wts_msa_2006.Rda")
load("003_nzlu_wts_all_2019.Rda")
load("003_nzlu_wts_msa_2019.Rda")
load("003_allmunis_2019.Rda")
load("003_msa_munis_2019.Rda")
load("2019_ACS_tracts_p1.Rda")
load("2019_ACS_tracts_p2.Rda")
load("nzlu_ts.rda")

## rank H input file for later ##
## this was calculated separately using all metro area 2015-2019 5-year ACS tract estimates ## 

rankH <- read_dta("acs_rank_H_1519_out.dta")

## 2020 MSA delineation file ## 

msa.del.2020 <- read_excel("path to raw data/msa_delineation_2020.xls")

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

## output nzlu (muni-level) ##

m1m <- stata.merge(nzlu.2019.final,
                   nzlu.wts.all.2019,
                   "GEOID")

table(m1m$merge.variable, useNA = "ifany")

m1 <- m1m %>%
  select(-merge.variable)

m2m <- stata.merge(m1,
                   nzlu.wts.msa.2019,
                   "GEOID")

table(m2m$merge.variable, useNA = "ifany")

m2 <- m2m %>%
  select(-merge.variable)

nzlu.2019.ts.m <- nzlu.2019.ts %>%
  ungroup() %>%
  select(GEOID,timestamp)

m3m <- stata.merge(m2,
                   nzlu.2019.ts.m,
                   "GEOID")

table(m3m$merge.variable, useNA = "ifany")

nzlu.data <- m3m %>%
  filter(merge.variable == 3) %>%
  select(-merge.variable)

## rda ##

save(nzlu.data,
     file = "Y:/Zoning/ZoningI/Data/Processed/Out/nzlud_muni.Rda")

## csv ##
write.csv(nzlu.data,
     file = "Y:/Zoning/ZoningI/Data/Processed/Out/nzlud_muni.csv")

## output nzlu (msa-level) ##

## csv (.rda already exists as 002_nzlu_msa_2019.rda) ##

write.csv(nzlu.msa.2019.final,
          file = "Y:/Zoning/ZoningI/Data/Processed/Out/nzlud_msa.csv")


#######################
## overall data sets ## 
#######################

## single family permit limits ##

prop.table(table(nzlu.2019.final$restrict_sf_permit, useNA = "ifany"))

prop.table(table(wrld.2018.final$restrict_sf_permit, useNA = "ifany"))

## multi family permit limits ##

prop.table(table(nzlu.2019.final$restrict_mf_permit, useNA = "ifany"))

prop.table(table(wrld.2018.final$restrict_mf_permit, useNA = "ifany"))

## single family unit limits ##

prop.table(table(nzlu.2019.final$limit_sf_units, useNA = "ifany"))

prop.table(table(wrld.2018.final$limit_sf_units, useNA = "ifany"))

## multi family unit limits ##

prop.table(table(nzlu.2019.final$limit_mf_units, useNA = "ifany"))

prop.table(table(wrld.2018.final$limit_mf_units, useNA = "ifany"))

## multi family dwelling limits ##

prop.table(table(nzlu.2019.final$limit_mf_dwellings, useNA = "ifany"))

prop.table(table(wrld.2018.final$limit_mf_dwellings, useNA = "ifany"))

## multi family dwelling unit limits ##

prop.table(table(nzlu.2019.final$limit_mf_dwelling_units, useNA = "ifany"))

prop.table(table(wrld.2018.final$limit_mf_dwelling_units, useNA = "ifany"))

## min lot sizes ##

prop.table(table(nzlu.2019.final$min_lot_size, useNA = "ifany"))

prop.table(table(wrld.2018.final$min_lot_size, useNA = "ifany"))

## min lot size - detail ##

prop.table(table(nzlu.2019.final$half_acre_less, useNA = "ifany"))

prop.table(table(wrld.2018.final$half_acre_less, useNA = "ifany"))


prop.table(table(nzlu.2019.final$half_acre_more, useNA = "ifany"))

prop.table(table(wrld.2018.final$half_acre_more, useNA = "ifany"))


prop.table(table(nzlu.2019.final$one_acre_more, useNA = "ifany"))

prop.table(table(wrld.2018.final$one_acre_more, useNA = "ifany"))


prop.table(table(nzlu.2019.final$two_acre_more, useNA = "ifany"))

prop.table(table(wrld.2018.final$two_acre_more, useNA = "ifany"))


## open space ## 

prop.table(table(nzlu.2019.final$open_space, useNA = "ifany"))

prop.table(table(wrld.2018.final$open_space, useNA = "ifany"))


## approvals - no rezoning - council ##

prop.table(table(nzlu.2019.final$council_nz, useNA = "ifany"))

prop.table(table(wrld.2018.final$council_nz, useNA = "ifany"))

## approvals - no rezoning - planning board ##

prop.table(table(nzlu.2019.final$planning_nz, useNA = "ifany"))

prop.table(table(wrld.2018.final$planning_nz, useNA = "ifany"))

## approvals - no rezoning - county board ##

prop.table(table(nzlu.2019.final$countybrd_nz, useNA = "ifany"))

prop.table(table(wrld.2018.final$countybrd_nz, useNA = "ifany"))

## approvals - no rezoning - public health board ##

prop.table(table(nzlu.2019.final$pubhlth_nz, useNA = "ifany"))

prop.table(table(wrld.2018.final$pubhlth_nz, useNA = "ifany"))

## approvals - no rezoning - site design review board ##

prop.table(table(nzlu.2019.final$site_plan_nz, useNA = "ifany"))

prop.table(table(wrld.2018.final$site_plan_nz, useNA = "ifany"))

## approvals - no rezoning - env rev board ##

prop.table(table(nzlu.2019.final$env_rev_nz, useNA = "ifany"))

prop.table(table(wrld.2018.final$env_rev_nz, useNA = "ifany"))

## approvals - rezoning - council ##

prop.table(table(nzlu.2019.final$council_rz, useNA = "ifany"))

prop.table(table(wrld.2018.final$council_rz, useNA = "ifany"))

## approvals - rezoning - planning board ##

prop.table(table(nzlu.2019.final$planning_rz, useNA = "ifany"))

prop.table(table(wrld.2018.final$planning_rz, useNA = "ifany"))

## approvals - rezoning - zoning board ##

prop.table(table(nzlu.2019.final$zoning_rz, useNA = "ifany"))

prop.table(table(wrld.2018.final$zoning_rz, useNA = "ifany"))

## approvals - rezoning - county board ##

prop.table(table(nzlu.2019.final$countybrd_rz, useNA = "ifany"))

prop.table(table(wrld.2018.final$countybrd_rz, useNA = "ifany"))

## approvals - rezoning - county zoning authority ##

prop.table(table(nzlu.2019.final$countyzone_rz, useNA = "ifany"))

prop.table(table(wrld.2018.final$countyzone_rz, useNA = "ifany"))

## approvals - rezoning - town meeting ##

prop.table(table(nzlu.2019.final$townmeet_rz, useNA = "ifany"))

prop.table(table(wrld.2018.final$townmeet_rz, useNA = "ifany"))

## approvals - rezoning - env rev board ##

prop.table(table(nzlu.2019.final$env_rev_rz, useNA = "ifany"))

prop.table(table(wrld.2018.final$env_rev_rz, useNA = "ifany"))


summary(nzlu.2019.final$total_nz)
summary(wrld.2018.final$total_nz)

summary(nzlu.2019.final$total_rz)
summary(wrld.2018.final$total_rz)

## now compare munis in both samples ##

## initial tabs ## 

## single family permit limits ##

prop.table(table(nzlu.2019.final$restrict_sf_permit, useNA = "ifany"))

prop.table(table(wrld.panel.2018$restrict_sf_permit, useNA = "ifany"))

## multi family permit limits ##

prop.table(table(nzlu.2019.final$restrict_mf_permit, useNA = "ifany"))

prop.table(table(wrld.panel.2018$restrict_mf_permit, useNA = "ifany"))

## single family unit limits ##

prop.table(table(nzlu.2019.final$limit_sf_units, useNA = "ifany"))

prop.table(table(wrld.panel.2018$limit_sf_units, useNA = "ifany"))

## multi family unit limits ##

prop.table(table(nzlu.2019.final$limit_mf_units, useNA = "ifany"))

prop.table(table(wrld.panel.2018$limit_mf_units, useNA = "ifany"))

## multi family dwelling limits ##

prop.table(table(nzlu.2019.final$limit_mf_dwellings, useNA = "ifany"))

prop.table(table(wrld.panel.2018$limit_mf_dwellings, useNA = "ifany"))

## multi family dwelling unit limits ##

prop.table(table(nzlu.2019.final$limit_mf_dwelling_units, useNA = "ifany"))

prop.table(table(wrld.panel.2018$limit_mf_dwelling_units, useNA = "ifany"))

## min lot sizes ##

prop.table(table(nzlu.2019.final$min_lot_size, useNA = "ifany"))

prop.table(table(wrld.panel.2018$min_lot_size, useNA = "ifany"))

## min lot size - detail ##

prop.table(table(nzlu.2019.final$half_acre_less, useNA = "ifany"))

prop.table(table(wrld.panel.2018$half_acre_less, useNA = "ifany"))


prop.table(table(nzlu.2019.final$half_acre_more, useNA = "ifany"))

prop.table(table(wrld.panel.2018$half_acre_more, useNA = "ifany"))


prop.table(table(nzlu.2019.final$one_acre_more, useNA = "ifany"))

prop.table(table(wrld.panel.2018$one_acre_more, useNA = "ifany"))


prop.table(table(nzlu.2019.final$two_acre_more, useNA = "ifany"))

prop.table(table(wrld.panel.2018$two_acre_more, useNA = "ifany"))


## open space ## 

prop.table(table(nzlu.2019.final$open_space, useNA = "ifany"))

prop.table(table(wrld.panel.2018$open_space, useNA = "ifany"))


## approvals - no rezoning - council ##

prop.table(table(nzlu.2019.final$council_nz, useNA = "ifany"))

prop.table(table(wrld.panel.2018$council_nz, useNA = "ifany"))

## approvals - no rezoning - planning board ##

prop.table(table(nzlu.2019.final$planning_nz, useNA = "ifany"))

prop.table(table(wrld.panel.2018$planning_nz, useNA = "ifany"))

## approvals - no rezoning - county board ##

prop.table(table(nzlu.2019.final$countybrd_nz, useNA = "ifany"))

prop.table(table(wrld.panel.2018$countybrd_nz, useNA = "ifany"))

## approvals - no rezoning - public health board ##

prop.table(table(nzlu.2019.final$pubhlth_nz, useNA = "ifany"))

prop.table(table(wrld.panel.2018$pubhlth_nz, useNA = "ifany"))

## approvals - no rezoning - site design review board ##

prop.table(table(nzlu.2019.final$site_plan_nz, useNA = "ifany"))

prop.table(table(wrld.panel.2018$site_plan_nz, useNA = "ifany"))

## approvals - no rezoning - env rev board ##

prop.table(table(nzlu.2019.final$env_rev_nz, useNA = "ifany"))

prop.table(table(wrld.panel.2018$env_rev_nz, useNA = "ifany"))

## approvals - rezoning - council ##

prop.table(table(nzlu.2019.final$council_rz, useNA = "ifany"))

prop.table(table(wrld.panel.2018$council_rz, useNA = "ifany"))

## approvals - rezoning - planning board ##

prop.table(table(nzlu.2019.final$planning_rz, useNA = "ifany"))

prop.table(table(wrld.panel.2018$planning_rz, useNA = "ifany"))

## approvals - rezoning - zoning board ##

prop.table(table(nzlu.2019.final$zoning_rz, useNA = "ifany"))

prop.table(table(wrld.panel.2018$zoning_rz, useNA = "ifany"))

## approvals - rezoning - county board ##

prop.table(table(nzlu.2019.final$countybrd_rz, useNA = "ifany"))

prop.table(table(wrld.panel.2018$countybrd_rz, useNA = "ifany"))

## approvals - rezoning - county zoning authority ##

prop.table(table(nzlu.2019.final$countyzone_rz, useNA = "ifany"))

prop.table(table(wrld.panel.2018$countyzone_rz, useNA = "ifany"))

## approvals - rezoning - town meeting ##

prop.table(table(nzlu.2019.final$townmeet_rz, useNA = "ifany"))

prop.table(table(wrld.panel.2018$townmeet_rz, useNA = "ifany"))

## approvals - rezoning - env rev board ##

prop.table(table(nzlu.2019.final$env_rev_rz, useNA = "ifany"))

prop.table(table(wrld.panel.2018$env_rev_rz, useNA = "ifany"))


summary(nzlu.2019.final$total_nz)
summary(wrld.panel.2018$total_nz)

summary(nzlu.2019.final$total_rz)
summary(wrld.panel.2018$total_rz)



## merge data frames ## 

## rename vars ##
nzlu.2019.final.fm <- nzlu.2019.final %>%
  rename(restrict_sf_permit_nzlu = restrict_sf_permit,
         restrict_mf_permit_nzlu = restrict_mf_permit,
         limit_sf_units_nzlu = limit_sf_units,
         limit_mf_units_nzlu = limit_mf_units,
         limit_mf_dwellings_nzlu = limit_mf_dwellings,
         limit_mf_dwelling_units_nzlu = limit_mf_dwelling_units,
         min_lot_size_nzlu = min_lot_size,
         open_space_nzlu = open_space,
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
         total_rz_nzlu = total_rz)

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

## merge checks ## 
nrow(nzlu.2019.final.fm) == length(unique(nzlu.2019.final.fm$GEOID))
class(nzlu.2019.final.fm$GEOID)
range(nchar(trim(nzlu.2019.final.fm$GEOID)))

nrow(wrld.panel.2018.fm) == length(unique(wrld.panel.2018.fm$GEOID))
class(wrld.panel.2018.fm$GEOID)
range(nchar(trim(wrld.panel.2018.fm$GEOID)))

## merge data frames ## 

nzlu.wrld.2019.merge <- stata.merge(nzlu.2019.final.fm,
                                    wrld.panel.2018.fm, 
                                    "GEOID")

## merge check ## 
table(nzlu.wrld.2019.merge$merge.variable)

## keep matches only ##

nzlu.wrld.2019 <- nzlu.wrld.2019.merge %>%
  filter(merge.variable == 3) %>%
  select(-merge.variable)

##############
## analysis ## 
##############

## restrict sf permits ##

sfpermits <- nzlu.wrld.2019 %>%
  select(GEOID,
         place,
         restrict_sf_permit_nzlu,
         restrict_sf_permit_wrld) %>%
  filter(!is.na(restrict_sf_permit_wrld))

prop.table(table(sfpermits$restrict_sf_permit_nzlu, useNA = "ifany"))
prop.table(table(sfpermits$restrict_sf_permit_wrld, useNA = "ifany"))

sum(sfpermits$restrict_sf_permit_nzlu == sfpermits$restrict_sf_permit_wrld)/nrow(sfpermits)


## restrict mf permits ##

mfpermits <- nzlu.wrld.2019 %>%
  select(GEOID,
         place,
         restrict_mf_permit_nzlu,
         restrict_mf_permit_wrld) %>%
  filter(!is.na(restrict_mf_permit_wrld))

prop.table(table(mfpermits$restrict_mf_permit_nzlu, useNA = "ifany"))
prop.table(table(mfpermits$restrict_mf_permit_wrld, useNA = "ifany"))

sum(mfpermits$restrict_mf_permit_nzlu == mfpermits$restrict_mf_permit_wrld)/nrow(mfpermits)

## restrict sf units ##

sfunits <- nzlu.wrld.2019 %>%
  select(GEOID,
         place,
         limit_sf_units_nzlu,
         limit_sf_units_wrld) %>%
  filter(!is.na(limit_sf_units_wrld)) 

prop.table(table(sfunits$limit_sf_units_nzlu, useNA = "ifany"))
prop.table(table(sfunits$limit_sf_units_wrld, useNA = "ifany"))

sum(sfunits$limit_sf_units_nzlu == sfunits$limit_sf_units_wrld)/nrow(sfunits)


## restrict mf units ##

mfunits <- nzlu.wrld.2019 %>%
  select(GEOID,
         place,
         limit_mf_units_nzlu,
         limit_mf_units_wrld) %>%
  filter(!is.na(limit_mf_units_wrld)) 

prop.table(table(mfunits$limit_mf_units_nzlu, useNA = "ifany"))
prop.table(table(mfunits$limit_mf_units_wrld, useNA = "ifany"))

sum(mfunits$limit_mf_units_nzlu == mfunits$limit_mf_units_wrld)/nrow(mfunits)


## restrict mf dwellings ##

mfdwellings <- nzlu.wrld.2019 %>%
  select(GEOID,
         place,
         limit_mf_dwellings_nzlu,
         limit_mf_dwellings_wrld) %>%
  filter(!is.na(limit_mf_dwellings_wrld)) 

prop.table(table(mfdwellings$limit_mf_dwellings_nzlu, useNA = "ifany"))
prop.table(table(mfdwellings$limit_mf_dwellings_wrld, useNA = "ifany"))

sum(mfdwellings$limit_mf_dwellings_nzlu == mfdwellings$limit_mf_dwellings_wrld)/nrow(mfdwellings)


## restrict mf dwelling units ##

mfdwellunits <- nzlu.wrld.2019 %>%
  select(GEOID,
         place,
         limit_mf_dwelling_units_nzlu,
         limit_mf_dwelling_units_wrld) %>%
  filter(!is.na(limit_mf_dwelling_units_wrld))

prop.table(table(mfdwellunits$limit_mf_dwelling_units_nzlu, useNA = "ifany"))
prop.table(table(mfdwellunits$limit_mf_dwelling_units_wrld, useNA = "ifany"))

sum(mfdwellunits$limit_mf_dwelling_units_nzlu == mfdwellunits$limit_mf_dwelling_units_wrld)/nrow(mfdwellunits)

## min lot sizes ## 

minlotsize <- nzlu.wrld.2019 %>%
  select(GEOID,
         place,
         min_lot_size_nzlu,
         min_lot_size_wrld) %>%
  filter(!is.na(min_lot_size_wrld)) 

prop.table(table(minlotsize$min_lot_size_nzlu, useNA = "ifany"))
prop.table(table(minlotsize$min_lot_size_wrld, useNA = "ifany"))

sum(minlotsize$min_lot_size_nzlu == minlotsize$min_lot_size_wrld)/nrow(minlotsize)

## min lot size - two acres or more ## 

mlotsize4 <- nzlu.wrld.2019 %>%
  select(GEOID,
         place,
         two_acre_more_nzlu,
         two_acre_more_wrld) %>%
  filter(!is.na(two_acre_more_wrld))

prop.table(table(mlotsize4$two_acre_more_nzlu, useNA = "ifany"))
prop.table(table(mlotsize4$two_acre_more_wrld, useNA = "ifany"))

sum(mlotsize4$two_acre_more_nzlu == mlotsize4$two_acre_more_wrld, na.rm=T)/nrow(mlotsize4)

mlotsize4.ds <- mlotsize4 %>%
  filter(two_acre_more_nzlu != two_acre_more_wrld)

## min lot size - one acre or more ## 

mlotsize3 <- nzlu.wrld.2019 %>%
  select(GEOID,
         place,
         one_acre_more_nzlu,
         one_acre_more_wrld) %>%
  filter(!is.na(one_acre_more_wrld)) 

prop.table(table(mlotsize3$one_acre_more_nzlu, useNA = "ifany"))
prop.table(table(mlotsize3$one_acre_more_wrld, useNA = "ifany"))

sum(mlotsize3$one_acre_more_nzlu == mlotsize3$one_acre_more_wrld, na.rm=T)/nrow(mlotsize3)

mlotsize3.ds <- mlotsize3 %>%
  filter(one_acre_more_nzlu != one_acre_more_wrld & 
         GEOID %notin% mlotsize4.ds$GEOID)

## min lot size - more than half acre ## 

mlotsize2 <- nzlu.wrld.2019 %>%
  select(GEOID,
         place,
         half_acre_more_nzlu,
         half_acre_more_wrld) %>%
  filter(!is.na(half_acre_more_wrld)) 

prop.table(table(mlotsize2$half_acre_more_nzlu, useNA = "ifany"))
prop.table(table(mlotsize2$half_acre_more_wrld, useNA = "ifany"))

sum(mlotsize2$half_acre_more_nzlu == mlotsize2$half_acre_more_wrld, na.rm=T)/nrow(mlotsize2)

mlotsize2.ds <- mlotsize2 %>%
  filter(half_acre_more_nzlu != half_acre_more_wrld & 
         GEOID %notin% mlotsize4.ds$GEOID & 
         GEOID %notin% mlotsize3.ds$GEOID)

## min lot size - less than half acre ## 

mlotsize1 <- nzlu.wrld.2019 %>%
  select(GEOID,
         place,
         half_acre_less_nzlu,
         half_acre_less_wrld) %>%
  filter(!is.na(half_acre_less_wrld))

prop.table(table(mlotsize1$half_acre_less_nzlu, useNA = "ifany"))
prop.table(table(mlotsize1$half_acre_less_wrld, useNA = "ifany"))

sum(mlotsize1$half_acre_less_nzlu == mlotsize1$half_acre_less_wrld, na.rm=T)/nrow(mlotsize1)

mlotsize1.ds <- mlotsize1 %>%
  filter(half_acre_less_nzlu != half_acre_less_wrld & 
         GEOID %notin% mlotsize4.ds$GEOID & 
         GEOID %notin% mlotsize3.ds$GEOID & 
         GEOID %notin% mlotsize2.ds$GEOID)


## open space requirements ## 

openspace <- nzlu.wrld.2019 %>%
  select(GEOID,
         place,
         open_space_nzlu,
         open_space_wrld) %>%
  filter(!is.na(open_space_wrld)) 

prop.table(table(openspace$open_space_nzlu, useNA = "ifany"))
prop.table(table(openspace$open_space_wrld, useNA = "ifany"))

sum(openspace$open_space_nzlu == openspace$open_space_wrld)/nrow(openspace)

test.os <- filter(openspace, open_space_nzlu != open_space_wrld)


## procedural vars ##

cnz <- nzlu.wrld.2019 %>%
  select(GEOID,
         place,
         council_nz_nzlu,
         council_nz_wrld) %>%
  filter(!is.na(council_nz_wrld))

prop.table(table(cnz$council_nz_nzlu, useNA = "ifany"))
prop.table(table(cnz$council_nz_wrld, useNA = "ifany"))

sum(cnz$council_nz_nzlu == cnz$council_nz_wrld)/nrow(cnz)

test.council.nz <- cnz %>%
  filter(council_nz_nzlu != council_nz_wrld)

plnz <- nzlu.wrld.2019 %>%
  select(GEOID,
         place,
         planning_nz_nzlu,
         planning_nz_wrld) %>%
  filter(!is.na(planning_nz_wrld))

prop.table(table(plnz$planning_nz_nzlu, useNA = "ifany"))
prop.table(table(plnz$planning_nz_wrld, useNA = "ifany"))

sum(plnz$planning_nz_nzlu == plnz$planning_nz_wrld)/nrow(plnz)

cntyboard <- nzlu.wrld.2019 %>%
  select(GEOID,
         place,
         countybrd_nz_nzlu,
         countybrd_nz_wrld) %>%
  filter(!is.na(countybrd_nz_wrld))

prop.table(table(cntyboard$countybrd_nz_nzlu, useNA = "ifany"))
prop.table(table(cntyboard$countybrd_nz_wrld, useNA = "ifany"))

sum(cntyboard$countybrd_nz_nzlu == cntyboard$countybrd_nz_wrld)/nrow(cntyboard)

phb <- nzlu.wrld.2019 %>%
  select(GEOID,
         place,
         pubhlth_nz_nzlu,
         pubhlth_nz_wrld) %>%
  filter(!is.na(pubhlth_nz_wrld))

prop.table(table(phb$pubhlth_nz_nzlu, useNA = "ifany"))
prop.table(table(phb$pubhlth_nz_wrld, useNA = "ifany"))

sum(phb$pubhlth_nz_nzlu == phb$pubhlth_nz_wrld)/nrow(phb)

spnz <- nzlu.wrld.2019 %>%
  select(GEOID,
         place,
         site_plan_nz_nzlu,
         site_plan_nz_wrld) %>%
  filter(!is.na(site_plan_nz_wrld))

prop.table(table(spnz$site_plan_nz_nzlu, useNA = "ifany"))
prop.table(table(spnz$site_plan_nz_wrld, useNA = "ifany"))

sum(spnz$site_plan_nz_nzlu == spnz$site_plan_nz_wrld)/nrow(spnz)

envnz <- nzlu.wrld.2019 %>%
  select(GEOID,
         place,
         env_rev_nz_nzlu,
         env_rev_nz_wrld) %>%
  filter(!is.na(env_rev_nz_wrld))

prop.table(table(envnz$env_rev_nz_nzlu, useNA = "ifany"))
prop.table(table(envnz$env_rev_nz_wrld, useNA = "ifany"))

sum(envnz$env_rev_nz_nzlu == envnz$env_rev_nz_wrld)/nrow(envnz)

crz <- nzlu.wrld.2019 %>%
  select(GEOID,
         place,
         council_rz_nzlu,
         council_rz_wrld) %>%
  filter(!is.na(council_rz_wrld))

prop.table(table(crz$council_rz_nzlu, useNA = "ifany"))
prop.table(table(crz$council_rz_wrld, useNA = "ifany"))

sum(crz$council_rz_nzlu == crz$council_rz_wrld)/nrow(crz)

plrz <- nzlu.wrld.2019 %>%
  select(GEOID,
         place,
         planning_rz_nzlu,
         planning_rz_wrld) %>%
  filter(!is.na(planning_rz_wrld))

prop.table(table(plrz$planning_rz_nzlu, useNA = "ifany"))
prop.table(table(plrz$planning_rz_wrld, useNA = "ifany"))

sum(plrz$planning_rz_nzlu == plrz$planning_rz_wrld)/nrow(plrz)

zrz <- nzlu.wrld.2019 %>%
  select(GEOID,
         place,
         zoning_rz_nzlu,
         zoning_rz_wrld) %>%
  filter(!is.na(zoning_rz_wrld))

prop.table(table(zrz$zoning_rz_nzlu, useNA = "ifany"))
prop.table(table(zrz$zoning_rz_wrld, useNA = "ifany"))

sum(zrz$zoning_rz_nzlu == zrz$zoning_rz_wrld)/nrow(zrz)

cntyboard_rz <- nzlu.wrld.2019 %>%
  select(GEOID,
         place,
         countybrd_rz_nzlu,
         countybrd_rz_wrld) %>%
  filter(!is.na(countybrd_rz_wrld))

prop.table(table(cntyboard_rz$countybrd_rz_nzlu, useNA = "ifany"))
prop.table(table(cntyboard_rz$countybrd_rz_wrld, useNA = "ifany"))

sum(cntyboard_rz$countybrd_rz_nzlu == cntyboard_rz$countybrd_rz_wrld)/nrow(cntyboard_rz)

cntyzone_rz <- nzlu.wrld.2019 %>%
  select(GEOID,
         place,
         countyzone_rz_nzlu,
         countyzone_rz_wrld) %>%
  filter(!is.na(countyzone_rz_wrld))

prop.table(table(cntyzone_rz$countyzone_rz_nzlu, useNA = "ifany"))
prop.table(table(cntyzone_rz$countyzone_rz_wrld, useNA = "ifany"))

sum(cntyzone_rz$countyzone_rz_nzlu == cntyzone_rz$countyzone_rz_wrld)/nrow(cntyzone_rz)

envrz <- nzlu.wrld.2019 %>%
  select(GEOID,
         place,
         env_rev_rz_nzlu,
         env_rev_rz_wrld) %>%
  filter(!is.na(env_rev_rz_wrld))

prop.table(table(envrz$env_rev_rz_nzlu, useNA = "ifany"))
prop.table(table(envrz$env_rev_rz_wrld, useNA = "ifany"))

sum(envrz$env_rev_rz_nzlu == envrz$env_rev_rz_wrld)/nrow(envrz)


twnmt <- nzlu.wrld.2019 %>%
  select(GEOID,
         place,
         townmeet_rz_nzlu,
         townmeet_rz_wrld) %>%
  filter(!is.na(townmeet_rz_wrld))

prop.table(table(twnmt$townmeet_rz_nzlu, useNA = "ifany"))
prop.table(table(twnmt$townmeet_rz_wrld, useNA = "ifany"))

sum(twnmt$townmeet_rz_nzlu == twnmt$townmeet_rz_wrld)/nrow(twnmt)

## procedural vars - totals ##

nz.total <- nzlu.wrld.2019 %>%
  select(GEOID,
         place,
         total_nz_nzlu,
         total_nz_wrld) %>%
  filter(!is.na(total_nz_wrld))

prop.table(table(nz.total$total_nz_nzlu, useNA = "ifany"))
prop.table(table(nz.total$total_nz_wrld, useNA = "ifany"))

sum(nz.total$total_nz_nzlu == nz.total$total_nz_wrld)/nrow(nz.total)
sum(abs(nz.total$total_nz_nzlu - nz.total$total_nz_wrld) < 2)/nrow(nz.total)

summary(nz.total$total_nz_nzlu)
summary(nz.total$total_nz_wrld)

pr1.w <- nz.total %>%
  filter(total_nz_nzlu != total_nz_wrld)

rz.total <- nzlu.wrld.2019 %>%
  select(GEOID,
         place,
         total_rz_nzlu,
         total_rz_wrld) %>%
  filter(!is.na(total_rz_wrld))

prop.table(table(rz.total$total_rz_nzlu, useNA = "ifany"))
prop.table(table(rz.total$total_rz_wrld, useNA = "ifany"))


sum(rz.total$total_rz_nzlu == rz.total$total_rz_wrld)/nrow(rz.total)
sum(abs(rz.total$total_rz_nzlu - rz.total$total_rz_wrld) < 2)/nrow(rz.total)

summary(rz.total$total_rz_nzlu)
summary(rz.total$total_rz_wrld)

pr2.w <- rz.total %>%
  filter(total_rz_nzlu != total_rz_wrld)

## check 20 random munis ## 

pr.check.munis <- sample(nzlu.2019.final$place, 20)
pr.check.munis

########################
## compare with NLLUS ## 
########################

## overall tabs - source data ##

prop.table(table(nzlu.2019.final$maxden5))
prop.table(table(nzlu.2019.final$maxden4))
prop.table(table(nzlu.2019.final$maxden3))
prop.table(table(nzlu.2019.final$maxden2))
prop.table(table(nzlu.2019.final$maxden1))

prop.table(table(nzlu.2019.final$inclusionary))

## overall tabs - NLLUS ##

prop.table(table(nllus.2019.final$maxden5))
prop.table(table(nllus.2019.final$maxden4))
prop.table(table(nllus.2019.final$maxden3))
prop.table(table(nllus.2019.final$maxden2))
prop.table(table(nllus.2019.final$maxden1))

prop.table(table(nllus.2019.final$inclusionary))


## merge checks ## 

nzlu.2019.final.fm2 <- nzlu.2019.final %>%
  rename(maxden5_nzlu = maxden5,
         maxden4_nzlu = maxden4,
         maxden3_nzlu = maxden3,
         maxden2_nzlu = maxden2,
         maxden1_nzlu = maxden1,
         inclusionary_nzlu = inclusionary)

nllus.2019.final.fm2 <- nllus.2019.final %>%
  select(-statename) %>%
  rename(maxden5_wrld = maxden5,
         maxden4_wrld = maxden4,
         maxden3_wrld = maxden3,
         maxden2_wrld = maxden2,
         maxden1_wrld = maxden1,
         inclusionary_wrld = inclusionary)

nrow(nzlu.2019.final.fm2) == length(unique(nzlu.2019.final.fm2$GEOID))
class(nzlu.2019.final.fm2$GEOID)
range(nchar(trim(nzlu.2019.final.fm2$GEOID)))

nrow(nllus.2019.final.fm2) == length(unique(nllus.2019.final.fm2$GEOID))
class(nllus.2019.final.fm2$GEOID)
range(nchar(trim(nllus.2019.final.fm2$GEOID)))

nzlu.nllus.2019 <- stata.merge(nzlu.2019.final.fm2,
                               nllus.2019.final.fm2,
                               "GEOID")

## check merge results ## 
table(nzlu.nllus.2019$merge.variable)

nzlu.nllus.2019.keep <- nzlu.nllus.2019 %>%
  filter(merge.variable == 3) %>%
  select(-merge.variable,
         -max_den_cat1.x,
         -max_den_cat1.y,
         -max_den_cat2.x,
         -max_den_cat2.y,
         -max_den_cat3.x,
         -max_den_cat3.y,
         -max_den_cat4.x,
         -max_den_cat4.y,
         -max_den_cat5.x,
         -max_den_cat5.y)

## max den ##

## NZLU ##
prop.table(table(nzlu.nllus.2019.keep$maxden5_nzlu))
prop.table(table(nzlu.nllus.2019.keep$maxden4_nzlu))
prop.table(table(nzlu.nllus.2019.keep$maxden3_nzlu))
prop.table(table(nzlu.nllus.2019.keep$maxden2_nzlu))
prop.table(table(nzlu.nllus.2019.keep$maxden1_nzlu))

prop.table(table(nzlu.nllus.2019.keep$inclusionary_nzlu))

## NLLUS ##
prop.table(table(nzlu.nllus.2019.keep$maxden5_wrld))
prop.table(table(nzlu.nllus.2019.keep$maxden4_wrld))
prop.table(table(nzlu.nllus.2019.keep$maxden3_wrld))
prop.table(table(nzlu.nllus.2019.keep$maxden2_wrld))
prop.table(table(nzlu.nllus.2019.keep$maxden1_wrld))

prop.table(table(nzlu.nllus.2019.keep$inclusionary_wrld))


sum(nzlu.nllus.2019.keep$maxden5_nzlu == nzlu.nllus.2019.keep$maxden5_wrld, na.rm=T)/nrow(nzlu.nllus.2019.keep)
sum(nzlu.nllus.2019.keep$maxden4_nzlu == nzlu.nllus.2019.keep$maxden4_wrld, na.rm=T)/nrow(nzlu.nllus.2019.keep)
sum(nzlu.nllus.2019.keep$maxden3_nzlu == nzlu.nllus.2019.keep$maxden3_wrld, na.rm=T)/nrow(nzlu.nllus.2019.keep)
sum(nzlu.nllus.2019.keep$maxden2_nzlu == nzlu.nllus.2019.keep$maxden2_wrld, na.rm=T)/nrow(nzlu.nllus.2019.keep)
sum(nzlu.nllus.2019.keep$maxden1_nzlu == nzlu.nllus.2019.keep$maxden1_wrld, na.rm=T)/nrow(nzlu.nllus.2019.keep)

sum(nzlu.nllus.2019.keep$inclusionary_nzlu == nzlu.nllus.2019.keep$inclusionary_wrld, na.rm=T)/nrow(nzlu.nllus.2019.keep)

nllus.comp.m5 <- nzlu.nllus.2019.keep %>%
  filter(maxden5_nzlu != maxden5_wrld) %>%
  select(GEOID,
         statename,
         place,
         maxden5_nzlu,
         maxden5_wrld)

nllus.comp.m4 <- nzlu.nllus.2019.keep %>%
  filter(maxden4_nzlu != maxden4_wrld & 
         GEOID %notin% nllus.comp.m5$GEOID) %>%
  select(GEOID,
         statename,
         place,
         maxden4_nzlu,
         maxden4_wrld)

nllus.comp.m3 <- nzlu.nllus.2019.keep %>%
  filter(maxden3_nzlu != maxden3_wrld & 
         GEOID %notin% nllus.comp.m5$GEOID & 
         GEOID %notin% nllus.comp.m4$GEOID) %>%
  select(GEOID,
         statename,
         place,
         maxden3_nzlu,
         maxden3_wrld)

nllus.comp.m2 <- nzlu.nllus.2019.keep %>%
  filter(maxden2_nzlu != maxden2_wrld & 
         GEOID %notin% nllus.comp.m5$GEOID & 
         GEOID %notin% nllus.comp.m4$GEOID &
         GEOID %notin% nllus.comp.m3$GEOID) %>%
  select(GEOID,
         statename,
         place,
         maxden2_nzlu,
         maxden2_wrld)

nllus.comp.m1 <- nzlu.nllus.2019.keep %>%
  filter(maxden1_nzlu != maxden2_wrld & 
         GEOID %notin% nllus.comp.m5$GEOID & 
         GEOID %notin% nllus.comp.m4$GEOID &
         GEOID %notin% nllus.comp.m3$GEOID & 
         GEOID %notin% nllus.comp.m2$GEOID) %>%
  select(GEOID,
         statename,
         place,
         maxden2_nzlu,
         maxden2_wrld)

max.den.check <- nzlu.nllus.2019.keep %>%
  select(GEOID,
         statename,
         place,
         maxden1_nzlu,
         maxden2_nzlu,
         maxden3_nzlu,
         maxden4_nzlu,
         maxden5_nzlu)


## summary of zri ## 

summary(nzlu.2019.final$zri_st)
sd(nzlu.2019.final$zri_st, na.rm=T)

summary(wrld.2018.final$WRLURI18)
sd(wrld.2018.final$WRLURI18, na.rm=T)

summary(all.samples.2019.final$zri_s_st)
sd(all.samples.2019.final$zri_s_st, na.rm=T)

summary(all.samples.2019.final$zri_c_st)
sd(all.samples.2019.final$zri_c_st, na.rm=T)

summary(nzlu.msa.2019.final$zri_full_st)
sd(nzlu.msa.2019.final$zri_full_st, na.rm=T)

summary(wrld.msa.2018$WRLURI18_st, na.rm=T)
sd(wrld.msa.2018$WRLURI18_st, na.rm=T)

summary(all.samples.msa.2019.final$zri_s_st)
sd(all.samples.msa.2019.final$zri_s_st, na.rm=T)

summary(all.samples.msa.2019.final$zri_c_st)
sd(all.samples.msa.2019.final$zri_c_st, na.rm=T)


## correlation between ez.index.st (2019) and WRLURI 2018 ##

## merge checks ## 
nrow(nzlu.2019.final) == length(unique(nzlu.2019.final$GEOID))
class(nzlu.2019.final$GEOID)
range(nchar(trim(nzlu.2019.final$GEOID)))

nrow(wrld.panel.2018) == length(unique(wrld.panel.2018$GEOID))
class(wrld.panel.2018$GEOID)
range(nchar(trim(wrld.panel.2018$GEOID)))

nzlu.wrld.2019.cor.merge <- stata.merge(nzlu.2019.final,
                                        wrld.panel.2018,
                                        "GEOID")

## diagnose merge ##
table(nzlu.wrld.2019.cor.merge$merge.variable)

nzlu.wrld.2019.cor <- nzlu.wrld.2019.cor.merge %>%
  filter(merge.variable == 3) %>%
  select(-merge.variable)

cor(nzlu.wrld.2019.cor$zri_st,
    nzlu.wrld.2019.cor$WRLURI18,
    use = "complete.obs")

## plot densities ## 

plot(density(nzlu.2019.final$zri_st, na.rm=T),
     col = "blue",
     main = "",
     xlab = "Index value")
lines(density(wrld.2018.final$WRLURI18, na.rm=T), col = "red")
legend("topright",
       legend = c("NZLU",
                  "WRLURI"),
       cex = 0.3,
       lty = c(1,1),
       col = c("blue","red"))


mdata <- data.frame(index = c(nzlu.2019.final$zri_st,
                              wrld.msa.2018$WRLURI18_st),
                    gr = c(rep("NZLU",length(nzlu.2019.final$zri_st)),
                           rep("WRLURI",length(wrld.msa.2018$WRLURI18_st))))


ggplot(data = mdata, aes(x=index, group=gr, fill = gr)) +
  geom_density(adjust=1.5,alpha=.4) + 
  ggtitle("") +
  xlab("Index Value") + 
  ylab("Density") + 
  scale_fill_manual(name= NULL,values=c("blue", "red")) +
  theme_classic()


## all munis density plot (fancier) something wrong with legend ##
nzlu.d1 <- density(nzlu.2019.final$zri_st, na.rm=T)
wrld.d1 <- density(wrld.2018.final$WRLURI18, na.rm=T)

plot(nzlu.d1, 
     col = "blue",
     main = "",
     xlab = "Index value",
     ylim = c(0, max(c(nzlu.d1$y, wrld.d1$y))),
     xlim = c(min(c(nzlu.d1$x, wrld.d1$x)),
              max(c(nzlu.d1$x, wrld.d1$x))))
lines(wrld.d1, col = "red")
polygon(nzlu.d1, col = rgb(0,0,1, alpha = 0.5))
polygon(wrld.d1, col = rgb(1,0,0,, alpha = 0.5))
legend("topright",
       legend = c("ZRI",
                  "WRLURI"),
       lty = c(1,1),
       col = c("blue","red"))

plot(density(all.samples.2019.final$zri_s_st, na.rm=T), 
     col = "blue",
     main = "Density of ez.index in full samples",
     xlab = "Index value")
lines(density(all.samples.2019.final$zri_c_st, na.rm=T), col = "red")
legend("topright",
       legend = c("Source data",
                  "Comparison data"),
       lty = c(1,1),
       col = c("blue","red"))


plot(density(nzlu.msa.2019.final$zri_st, na.rm=T), 
     col = "blue",
     main = "Density of ZRI in full samples (MSA level)",
     xlab = "Index value")
lines(density(wrld.2018.final$WRLURI18, na.rm=T), col = "red")
legend("topright",
       legend = c("ZRI",
                  "WRLURI"),
       lty = c(1,1),
       col = c("blue","red"))

## MSA density plot (fancier) ##

## use this ggplot version ##

ddata <- data.frame(index = c(nzlu.msa.2019.final$zri_full_st,
                              wrld.msa.2018$WRLURI18_st),
                    gr = c(rep("NZLU",length(nzlu.msa.2019.final$zri_full_st)),
                           rep("WRLURI",length(wrld.msa.2018$WRLURI18_st))))

ggplot(data = ddata, aes(x=index, group=gr, fill = gr)) +
  geom_density(adjust=1.5,alpha=.4) + 
  ggtitle("") +
  xlab("Index Value") + 
  ylab("Density") + 
  scale_fill_manual(name= NULL,values=c("blue", "red")) +
  theme_classic()
  

## legend is messed up with this version ##
nzlu.d2 <- density(nzlu.msa.2019.final$zri_full_st, na.rm=T)
wrld.d2 <- density(wrld.msa.2018$WRLURI18_st, na.rm=T)

plot(nzlu.d2, 
     col = "blue",
     main = "",
     xlab = "Index value",
     ylim = c(0, max(c(nzlu.d2$y, wrld.d2$y))),
     xlim = c(min(c(nzlu.d2$x, wrld.d2$x)),
              max(c(nzlu.d2$x, wrld.d2$x))))
lines(wrld.d2, col = "red")
polygon(nzlu.d2, col = rgb(0,0,1, alpha = 0.5))
polygon(wrld.d2, col = rgb(1,0,0,, alpha = 0.5))
legend("topright",
       legend = c("ZRI",
                  "WRLURI"),
       cex = 0.3,
       lty = c(1,1),
       col = c("blue","red"))


plot(density(all.samples.msa.2019.final$zri_s_st, na.rm=T), 
     col = "blue",
     main = "Density of ez.index in full samples (MSA level)",
     xlab = "Index value")
lines(density(all.samples.msa.2019.final$zri_c_st, na.rm=T), col = "red")
legend("topright",
       legend = c("Source data",
                  "Comparison data"),
       lty = c(1,1),
       col = c("blue","red"))

#################################
## top 10 most regulated munis ## 
#################################

## NZLU ##
t10.muni.nzlu <- nzlu.2019.final[order(-nzlu.2019.final$zri_st),]

head(t10.muni.nzlu[,c("place","statename", "zri_st")], 10)

## WRLD ##
t10.muni.wrld <- wrld.2018.final[order(-wrld.2018.final$WRLURI18),]

head(t10.muni.wrld[,c("communityname18","state", "WRLURI18")], 10)

## all samples - source ##
t10.muni.as.s <- all.samples.2019.final[order(-all.samples.2019.final$zri_s_st),]

head(t10.muni.as.s[,c("place","statename","zri_s_st")], 10)

## all samples - comparison ##
t10.muni.as.c <- all.samples.2019.final[order(-all.samples.2019.final$zri_c_st),]

head(t10.muni.as.c[,c("place","statename", "zri_c_st")], 10)

######################################
## bottom 5 (least) regulated munis ##
######################################

## NZLU ##
b5.muni.nzlu <- nzlu.2019.final[order(nzlu.2019.final$zri_st),]

head(b5.muni.nzlu[,c("place","statename", "zri_st")], 10)

## WRLD ## 
b5.muni.wrld <- wrld.2018.final[order(wrld.2018.final$WRLURI18),]

head(b5.muni.wrld[,c("communityname18","state", "WRLURI18")], 10)

## all samples - source ##
b5.muni.as.s <- all.samples.2019.final[order(all.samples.2019.final$zri_s_st),]

head(b5.muni.as.s[,c("place","statename", "zri_s_st")], 10)

## all samples - comparsion ##
b5.muni.as.c <- all.samples.2019.final[order(all.samples.2019.final$zri_c_st),]

head(b5.muni.as.c[,c("place","statename", "zri_c_st")], 10)

################################
## top 10 most regulated MSAs ##
################################

## NZLU ## 
t10.msa.nzlu <- nzlu.msa.2019.final[order(-nzlu.msa.2019.final$zri_full_st),]

head(t10.msa.nzlu[,c("cbsaname10", "zri_full_st")], 10)

## WRLD ## 
t10.msa.wrld <- wrld.msa.2018[order(-wrld.msa.2018$WRLURI18_st),]

head(t10.msa.wrld[,c("cbsaname10", "WRLURI18_st")], 10)


###########################################################
## top 10 most regulated MSAs with at least 10 responses ##
###########################################################

nzlu.msa.large.2019 <- nzlu.msa.2019.final %>%
  filter(responses >= 10)

wrld.msa.large.2018 <- wrld.msa.2018 %>%
  filter(responses >= 10)

## NZLU ##
t10.msa.large.nzlu <- nzlu.msa.large.2019[order(-nzlu.msa.large.2019$zri_full_st),]

head(t10.msa.large.nzlu[,c("cbsaname10", "zri_full_st")], 10)

## WRLD ##
t10.msa.large.wrld <- wrld.msa.large.2018[order(-wrld.msa.large.2018$WRLURI18_st),]

head(t10.msa.large.wrld[,c("cbsaname10", "WRLURI18_st")], 10)


######################################
## bottom 10 (least) regulated MSAs ##
######################################

## NZLU ##
b10.msa.nzlu <- nzlu.msa.2019.final[order(nzlu.msa.2019.final$zri_full_st),]

head(b10.msa.nzlu[,c("cbsaname10", "zri_full_st")], 10)

## WRLD ##
b10.msa.wrld <- wrld.msa.2018[order(wrld.msa.2018$WRLURI18),]

head(b10.msa.wrld[,c("cbsaname10", "WRLURI18")], 10)

#################################################################
## bottom 10 (least) regulated MSAs with at least 10 responses ##
#################################################################

## NZLU ##
b10.msa.large.nzlu <- nzlu.msa.large.2019[order(nzlu.msa.large.2019$zri_full_st),]

head(b10.msa.large.nzlu[,c("cbsaname10", "zri_full_st")], 10)

## WRLD ##
b10.msa.large.wrld <- wrld.msa.large.2018[order(wrld.msa.large.2018$WRLURI18),]

head(b10.msa.large.wrld[,c("cbsaname10", "WRLURI18")], 10)

##################################
## Inclusionary zoning programs ##
##################################

## states - NZLU ##

iz.states.nzlu <- nzlu.2019.final %>%
  filter(inclusionary == 1) %>%
  group_by(statename) %>%
  summarize(n=n())

iz.states.nzlu <- iz.states.nzlu[order(-iz.states.nzlu$n),]

head(iz.states.nzlu[,c("statename","n")], 5)

## states - NLLUS ##

iz.states.nllus <- nllus.2019.final %>%
  filter(inclusionary == 1) %>%
  group_by(statename) %>%
  summarize(n=n())

iz.states.nllus <- iz.states.nllus[order(-iz.states.nllus$n),]

head(iz.states.nllus[,c("statename","n")],5)

## all samples - source ##

iz.states.as.s <- all.samples.2019.final %>%
  filter(inclusionary_nzlu == 1) %>%
  group_by(statename) %>%
  summarize(n=n())

iz.states.as.s <- iz.states.as.s[order(-iz.states.as.s$n),]

head(iz.states.as.s[,c("statename","n")],5)

## all samples - comparison ##

iz.states.as.c <- all.samples.2019.final %>%
  filter(inclusionary_nllus == 1) %>%
  group_by(statename) %>%
  summarize(n=n())

iz.states.as.c <- iz.states.as.c[order(-iz.states.as.c$n),]

head(iz.states.as.c[,c("statename","n")],5)

## MSAs - NZLU ##

iz.msas.nzlu <- nzlu.msa.2019.final %>%
  group_by(cbsaname10) 

iz.msas.nzlu <- iz.msas.nzlu[order(-iz.msas.nzlu$inclusionary),]

head(iz.msas.nzlu[,c("cbsaname10","inclusionary")],5)

## MSAs - NLLUS ##

iz.msas.nllus <- nllus.msa.2019 %>%
  group_by(cbsaname10) 

iz.msas.nllus <- iz.msas.nllus[order(-iz.msas.nllus$inclusionary),]

head(iz.msas.nllus[,c("cbsaname10","inclusionary")],5)

## MSAs with at least 10 responses ##

## NZLU ##

iz.msas.large.nzlu <- nzlu.msa.large.2019 %>%
  group_by(cbsaname10) 

iz.msas.large.nzlu <- iz.msas.large.nzlu[order(-iz.msas.large.nzlu$inclusionary),]

head(iz.msas.large.nzlu[,c("cbsaname10","inclusionary")],5)

## NLLUS ##

iz.msas.large.nllus <- nllus.msa.2019 %>%
  filter(responses >= 10) %>%
  group_by(cbsaname10) 

iz.msas.large.nllus <- iz.msas.large.nllus[order(-iz.msas.large.nllus$inclusionary),]

head(iz.msas.large.nllus[,c("cbsaname10","inclusionary")],5)

## IZ graphics ##

par(mfrow=c(2,2))

col <- brewer.pal(5, "Set2")


## plot 1 ##

iz.states.nzlu.p <- iz.states.nzlu[order(-iz.states.nzlu$n),]
names(iz.states.nzlu.p)[names(iz.states.nzlu.p) == "statename"] <- "state"

iz.states.nzlu.bp <- iz.states.nzlu.p[1:5,]
iz.states.nzlu.bp$g <- "NZLU - All"

iz.bp1 <- barplot(iz.states.nzlu.bp$n,
                  names.arg = iz.states.nzlu.bp$state,
                  width = c(0.1,0.1,0.1,0.1,0.1),
                  main = "NZLU (all)",
                  ylab = "Number of munis",
                  ylim = c(0,200),
                  col=col)

text(x = iz.bp1,
     y = iz.states.nzlu.bp$n, 
     label = iz.states.nzlu.bp$n, 
     pos = 3, cex = 0.8, col = "red")

## plot 2 ##

iz.states.nllus.p <- iz.states.nllus[order(-iz.states.nllus$n),]
names(iz.states.nllus.p)[names(iz.states.nllus.p) == "statename"] <- "state"

iz.states.nllus.bp <- iz.states.nllus.p[1:5,]
iz.states.nllus.bp$g <- "NLLUS - All"

iz.bp2 <- barplot(iz.states.nllus.bp$n,
                  names.arg = iz.states.nllus.bp$state,
                  width = c(0.1,0.1,0.1,0.1,0.1),
                  main = "NLLUS (all)",
                  ylab = "Number of munis",
                  ylim = c(0,200),
                  col=col)

text(x = iz.bp2,
     y = iz.states.nllus.bp$n, 
     label = iz.states.nllus.bp$n, 
     pos = 3, cex = 0.8, col = "red")

## plot 3 ##

iz.states.as.s.p <- iz.states.as.s[order(-iz.states.as.s$n),]
names(iz.states.as.s.p)[names(iz.states.as.s.p) == "statename"] <- "state"

iz.states.as.s.bp <- iz.states.as.s.p[1:5,]
iz.states.as.s.bp $g <- "NZLU - MS"

iz.bp3 <- barplot(iz.states.as.s.bp$n,
                  names.arg = iz.states.as.s.bp$state,
                  width = c(0.1,0.1,0.1,0.1,0.1),
                  main = "NZLU (across all 3 samples)",
                  ylab = "Number of munis",
                  ylim = c(0,50),
                  col=col)

text(x = iz.bp3,
     y = iz.states.as.s.bp$n, 
     label = iz.states.as.s.bp$n, 
     pos = 3, cex = 0.8, col = "red")

## plot 4 ##

iz.states.as.c.p <- iz.states.as.c[order(-iz.states.as.c$n),]
names(iz.states.as.c.p)[names(iz.states.as.c.p) == "statename"] <- "state"

iz.states.as.c.bp <- iz.states.as.c.p[1:5,]
iz.states.as.c.bp $g <- "NLLUS - MS"

iz.bp4 <- barplot(iz.states.as.c.bp$n,
                  names.arg = iz.states.as.c.bp$state,
                  width = c(0.1,0.1,0.1,0.1,0.1),
                  main = "NLLUS (across all 3 samples)",
                  ylab = "Number of munis",
                  ylim = c(0,50),
                  col=col)

text(x = iz.bp4,
     y = iz.states.as.c.bp$n, 
     label = iz.states.as.c.bp$n, 
     pos = 3, cex = 0.8, col = "red")


iz.bp <- rbind(iz.states.nzlu.bp,
               iz.states.nllus.bp,
               iz.states.as.s.bp,
               iz.states.as.c.bp)

iz.bp$gf <- as.factor(iz.bp$g)
levels(iz.bp$gf)
iz.bp$gf <- relevel(iz.bp$gf,
                    "NZLU - All",
                    "NLLUS - All",
                    "NZLU - MS",
                    "NLLUS - MS")
levels(iz.bp$gf)

ggplot(iz.bp, aes(gf, n, fill = reorder(state, -n))) + 
  geom_bar(stat="identity", position = "dodge") + 
  geom_text(aes(label=n), position=position_dodge(width=0.9), vjust=-0.25, size=2.5, col="red") +
  scale_fill_brewer(palette = "Set2") + 
  labs(y = "Number of municipalities",
       x = "") + 
  ggtitle("") + 
  guides(fill=guide_legend(title="States"))  + 
  theme_classic()


##################################
## summary stats (with weights) ## 
##################################

## 2019 ##

## row 1 ##
summary(nzlu.panel.final$zri_st_2019)
sd(nzlu.panel.final$zri_st_2019, na.rm=T)
nrow(nzlu.panel.final)

## row 2 ##
weighted.mean(nzlu.panel.final$zri_st_2019, w = nzlu.panel.final$fwt_all,na.rm=T)
min(nzlu.panel.final$zri_st_2019*nzlu.panel.final$fwt_all,na.rm=T)
wtd.quantile(nzlu.panel.final$zri_st_2019, q=0.25, na.rm = T, weight=nzlu.panel.final$fwt_all)
wtd.quantile(nzlu.panel.final$zri_st_2019, q=0.5, na.rm = T, weight=nzlu.panel.final$fwt_all)
wtd.quantile(nzlu.panel.final$zri_st_2019, q=0.75, na.rm = T, weight=nzlu.panel.final$fwt_all)
max(nzlu.panel.final$zri_st_2019*nzlu.panel.final$fwt_all)
sqrt(wtd.var(nzlu.panel.final$zri_st_2019, nzlu.panel.final$fwt_all))


ms.2019 <- stata.merge(nzlu.panel.final,
                       nzlu.2019.wmsas.out,
                       "GEOID")

table(ms.2019$merge.variable, useNA = "ifany")

non.msa.sample <- ms.2019 %>%
  filter(merge.variable == 1) %>%
  select(-merge.variable)

ms.2019.keep <- ms.2019 %>%
  filter(merge.variable == 3) %>%
  select(-merge.variable)

ms.2019.keep.nm <- ms.2019.keep %>%
  filter(!is.na(fwt_msa))

## row 3 ##
summary(ms.2019.keep$zri_st_2019)
sd(ms.2019.keep$zri_st_2019)
nrow(ms.2019.keep)

## row 4 ##
weighted.mean(ms.2019.keep.nm$zri_st_2019, w = ms.2019.keep.nm$fwt_msa)
min(ms.2019.keep$zri_st_2019*ms.2019.keep$fwt_msa, na.rm=T)
wtd.quantile(ms.2019.keep$zri_st_2019, q=0.25, na.rm = FALSE, weight=ms.2019.keep$fwt_msa)
wtd.quantile(ms.2019.keep$zri_st_2019, q=0.5, na.rm = FALSE, weight=ms.2019.keep$fwt_msa)
wtd.quantile(ms.2019.keep$zri_st_2019, q=0.75, na.rm = FALSE, weight=ms.2019.keep$fwt_msa)
max(ms.2019.keep$zri_st_2019*ms.2019.keep$fwt_msa, na.rm=T)
sqrt(wtd.var(ms.2019.keep.nm$zri_st_2019, ms.2019.keep.nm$fwt_msa))

## row 5 ##
summary(non.msa.sample$zri_st_2019)
sd(non.msa.sample$zri_st_2019)
nrow(non.msa.sample)

## individual metros (with 10 or more municipalities) ##

nzlu.lmsa <- nzlu.panel.final %>%
  filter(!is.na(fwt_lmsa))

## merge on cbsa codes ##

muni.msa.2019.fm <- muni.msa.2019 %>%
  select(GEOID, cbsa10, cbsaname10)

nrow(muni.msa.2019.fm) == length(unique(muni.msa.2019.fm$GEOID))
class(muni.msa.2019.fm$GEOID)
range(nchar(trim(muni.msa.2019.fm$GEOID)))

nzlu.lmsa.cbsa.m <- stata.merge(nzlu.lmsa,
                                muni.msa.2019.fm,
                                "GEOID")

## check merge ## 
table(nzlu.lmsa.cbsa.m$merge.variable, useNA = "ifany")

nzlu.lmsa.cbsa <- nzlu.lmsa.cbsa.m %>%
  filter(merge.variable == 3) %>%
  select(-merge.variable)

lmsa.wt <- function(cbsa){
  
  indata <- nzlu.lmsa.cbsa %>%
    filter(cbsa10 == cbsa)
  
  r1 <- weighted.mean(indata$zri_st_2019, w = indata$fwt_lmsa)
  r2 <- min(indata$zri_st_2019*indata$fwt_lmsa, na.rm=T)
  r3 <- wtd.quantile(indata$zri_st_2019, q=0.25, na.rm = FALSE, weight=indata$fwt_lmsa)
  r4 <- wtd.quantile(indata$zri_st_2019, q=0.5, na.rm = FALSE, weight=indata$fwt_lmsa)
  r5 <- wtd.quantile(indata$zri_st_2019, q=0.75, na.rm = FALSE, weight=indata$fwt_lmsa)
  r6 <- max(indata$zri_st_2019*indata$fwt_lmsa, na.rm=T)
  r7 <- sqrt(wtd.var(indata$zri_st_2019, indata$fwt_lmsa))
  
  res.in <- data.frame(rbind(r1,r2,r3,r4,r5,r6,r7))
  res <- as.data.frame(t(res.in))
  res$cbsa10 <- cbsa
  
  return(res)
}


nzlu.lmsa.cbsas <- unique(nzlu.lmsa.cbsa$cbsa10)

lmsa.res.in <- lapply(nzlu.lmsa.cbsas, lmsa.wt)

lmsa.res <- bind_rows(lmsa.res.in)

nzlu.msa.og <- nzlu.msa.2019.final %>%
  select(cbsa10,
         zri_median_st)

nzlu.msa.comp.m <- stata.merge(lmsa.res,
                               nzlu.msa.og,
                               "cbsa10")

table(nzlu.msa.comp.m$merge.variable, useNA = "ifany")

nzlu.msa.comp <- nzlu.msa.comp.m %>%
  filter(merge.variable == 3) %>%
  select(-merge.variable) %>%
  mutate(diff.mean = abs(r1-zri_median_st),
         diff.median = abs(r4 - zri_median_st))

summary(nzlu.msa.comp$diff.median)
sd(nzlu.msa.comp$diff.median)

##########################################################################
## sociodemographic profile of municipalities along distribution of ZRI ##
##########################################################################

summary(nzlu.2019.final$zri_st)

nrow(nzlu.2019.final) == length(unique(nzlu.2019.final$GEOID))
class(nzlu.2019.final$GEOID)
range(nchar(trim(nzlu.2019.final$GEOID)))

nrow(munis.final.2019) == length(unique(munis.final.2019$GEOID))
class(munis.final.2019$GEOID)
range(nchar(trim(munis.final.2019$GEOID)))

nzlu.sda.m <- stata.merge(nzlu.2019.final,
                          munis.final.2019,
                          "GEOID")

## check merge ## 
table(nzlu.sda.m$merge.variable, useNA = "ifany")

## keep matches ##
nzlu.sda <- nzlu.sda.m %>%
  filter(merge.variable == 3) %>%
  select(-merge.variable) %>%
  mutate(rl = case_when(zri_st < -0.69924 ~ "low",
                        zri_st >= -0.69924 & zri_st <= 0.68557 ~ "medium",
                        zri_st > 0.68557 ~ "high"))

nzlu.sda.l <- nzlu.sda %>%
  filter(rl == "low")

nzlu.sda.m <- nzlu.sda %>%
  filter(rl == "medium") 

nzlu.sda.h <- nzlu.sda %>%
  filter(rl == "high") 

nrow(nzlu.sda.l) + nrow(nzlu.sda.m) + nrow(nzlu.sda.h) == 2639


nzlu.sda.ls <- nzlu.sda.l %>%
  group_by(rl) %>%
  summarize(median_hh_income = mean(median_hhld_inc, na.rm=T),
            median_prop_value = mean(median_pvalue, na.rm=T),
            pc_cg = mean(cgrad, na.rm=T),
            hhld_pov_rt = mean(hhld_pov_rt, na.rm=T),
            entropy = mean(entropy, na.rm=T),
            per_white = mean(per_white, na.rm=T),
            pop = mean(totpop, na.rm=T),
            land_area = mean(land_area_sqmiles, na.rm=T),
            pop_density = mean(pop_density, na.rm=T))

nzlu.sda.ms <- nzlu.sda.m %>%
  group_by(rl) %>%
  summarize(median_hh_income = mean(median_hhld_inc, na.rm=T),
            median_prop_value = mean(median_pvalue, na.rm=T),
            pc_cg = mean(cgrad, na.rm=T),
            hhld_pov_rt = mean(hhld_pov_rt, na.rm=T),
            entropy = mean(entropy, na.rm=T),
            per_white = mean(per_white, na.rm=T),
            pop = mean(totpop, na.rm=T),
            land_area = mean(land_area_sqmiles, na.rm=T),
            pop_density = mean(pop_density, na.rm=T))

nzlu.sda.hs <- nzlu.sda.h %>%
  group_by(rl) %>%
  summarize(median_hh_income = mean(median_hhld_inc, na.rm=T),
            median_prop_value = mean(median_pvalue, na.rm=T),
            pc_cg = mean(cgrad, na.rm=T),
            hhld_pov_rt = mean(hhld_pov_rt, na.rm=T),
            entropy = mean(entropy, na.rm=T),
            per_white = mean(per_white, na.rm=T),
            pop = mean(totpop, na.rm=T),
            land_area = mean(land_area_sqmiles, na.rm=T),
            pop_density = mean(pop_density, na.rm=T))

print(t(nzlu.sda.ls))            
print(t(nzlu.sda.ms))  
print(t(nzlu.sda.hs))


##################################################################
## sociodemographic profile of metros along distribution of ZRI ##
##################################################################

## create msa level file ##

v2019 <- load_variables(2019, "acs5", cache=T)

msas.2019 <- get_acs(geography = "metropolitan statistical area/micropolitan statistical area",
                     variables = c(totpop = "B01003_001",
                              tothhs = "B25003_001",
                              totfams = "B11003_001",
                              hhs_oo = "B25003_002",
                              hhs_ro = "B25003_003",
                              age_total = "B01001_001",
                              age_male_5u = "B01001_003",
                              age_male_5to9 = "B01001_004",
                              age_male_10to14 = "B01001_005",
                              age_male_15to17 = "B01001_006",
                              age_male_65to66 = "B01001_020",
                              age_male_67to69 = "B01001_021",
                              age_male_70to74 = "B01001_022",
                              age_male_75to79 = "B01001_023",
                              age_male_80to84 = "B01001_024",
                              age_male_85a = "B01001_025",
                              age_female_5u = "B01001_027",
                              age_female_5to9 = "B01001_028",
                              age_female_10to14 = "B01001_029",
                              age_female_15to17 = "B01001_030",
                              age_female_65to66 = "B01001_044",
                              age_female_67to69 = "B01001_045",
                              age_female_70to74 = "B01001_046",
                              age_female_75to79 = "B01001_047",
                              age_female_80to84 = "B01001_048",
                              age_female_85a = "B01001_049",
                              race_tot = "B02001_001",
                              pop_white = "B02001_002",
                              pop_black = "B02001_003",
                              pop_aian = "B02001_004",
                              pop_asian = "B02001_005",
                              pop_nhpi = "B02001_006",
                              pop_other = "B02001_007",
                              pop_multi = "B02001_008",
                              pop_nh = "B03002_002",
                              pop_nh_white = "B03002_003",
                              pop_nh_black = "B03002_004",
                              pop_nh_aian = "B03002_005",
                              pop_nh_asian = "B03002_006",
                              pop_nh_nhpi = "B03002_007",
                              pop_nh_other = "B03002_008",
                              pop_nh_multi = "B03002_009",
                              pop_hisp = "B03002_012",
                              pop_h_white = "B03002_013",
                              pop_h_black = "B03002_014",
                              pop_h_aian = "B03002_015",
                              pop_h_asian = "B03002_016",
                              pop_h_nhpi = "B03002_017",
                              pop_h_other = "B03002_018",
                              pop_h_multi = "B03002_019",
                              median_pvalue = "B25077_001",
                              median_hhld_inc = "B19013_001",
                              median_fam_inc = "B19113_001",
                              hhlds_pov = "B17017_002",
                              fams_pov = "B17010_002",
                              ed_total = "B15002_001",
                              ed_male_ba = "B15002_015",
                              ed_male_ma = "B15002_016",
                              ed_male_pd = "B15002_017",
                ed_male_doc = "B15002_018",
                ed_female_ba = "B15002_032",
                ed_female_ma = "B15002_033",
                ed_female_pd = "B15002_034",
                ed_female_doc = "B15002_035"),
                survey = "acs5",
                output = "wide",
                year = 2019)

msa.area.2019 <- core_based_statistical_areas(year = 2019,
                                              cb=TRUE)

#st_geometry(msa.area.2019) <- NULL
msa.area.2019.df <- as.data.frame(msa.area.2019)
class(msa.area.2019.df)


msas.2019.final <- msas.2019 %>%
  filter(grepl("Metro Area", NAME)) %>%
  mutate(pop_total_msa = totpopE,
         tothhs_msa = tothhsE,
         totfams_msa = totfamsE,
         pop_nh_aian_msa = pop_nh_aianE,
         pop_nh_asian_msa = pop_nh_asianE,
         pop_nh_black_msa  = pop_nh_blackE,
         pop_nh_other_msa  = pop_nh_otherE,
         pop_nh_nhpi_msa  = pop_nh_nhpiE,
         pop_nh_white_msa  = pop_nh_whiteE,
         pop_latinx_msa = pop_hispE,
         pop_both_multi_msa  = pop_nh_multiE, 
         per_asian_msa  = case_when(pop_total_msa != 0 ~ pop_nh_asian_msa/pop_total_msa,
                                    pop_total_msa == 0 ~ 0),
         per_black_msa = case_when(pop_total_msa != 0 ~ pop_nh_black_msa/pop_total_msa,
                                   pop_total_msa == 0 ~ 0),
         per_latinx_msa = case_when(pop_total_msa != 0 ~ pop_latinx_msa/pop_total_msa,
                                    pop_total_msa == 0 ~ 0),
         per_white_msa = case_when(pop_total_msa != 0 ~ pop_nh_white_msa/pop_total_msa,
                                   pop_total_msa == 0 ~ 0),
         per_aian_msa = case_when(pop_total_msa != 0 ~ pop_nh_aian_msa/pop_total_msa, 
                                  pop_total_msa == 0 ~ 0),
         per_other_msa = case_when(pop_total_msa != 0 ~ (pop_nh_other_msa + pop_nh_nhpi_msa + pop_both_multi_msa)/pop_total_msa, 
                                   pop_total_msa == 0 ~ 0),
         log_asian_msa = case_when(pop_nh_asianE != 0 ~ log(1/per_asian_msa),
                                   pop_nh_asianE == 0 ~ 0),
         log_black_msa = case_when(pop_nh_blackE != 0 ~ log(1/per_black_msa),
                                   pop_nh_blackE == 0 ~ 0),
         log_latinx_msa = case_when(pop_latinx_msa != 0 ~ log(1/per_latinx_msa),
                                    pop_latinx_msa == 0 ~ 0),
         log_white_msa = case_when(pop_nh_whiteE != 0 ~ log(1/per_white_msa),
                                   pop_nh_whiteE == 0 ~ 0),
         log_aian_msa = case_when(pop_nh_aianE != 0 ~ log(1/per_aian_msa),
                                  pop_nh_aianE == 0 ~ 0),
         log_other_msa = case_when(pop_nh_other_msa + pop_nh_nhpi_msa + pop_both_multi_msa != 0 ~ log(1/per_other_msa),
                                   pop_nh_other_msa + pop_nh_nhpi_msa + pop_both_multi_msa == 0 ~ 0),
         metro_entropy = per_asian_msa*log_asian_msa + 
                         per_black_msa*log_black_msa + 
                         per_latinx_msa*log_latinx_msa + 
                         per_white_msa*log_white_msa +
                         per_aian_msa*log_aian_msa +
                         per_other_msa*log_other_msa,
         tothhs_msa = tothhsE,
         totfams_msa = totfamsE,
         hhs_oo_msa = hhs_ooE/tothhs_msa,
         age_65a_msa = (age_male_65to66E + age_male_67to69E +
                      age_male_70to74E + age_male_75to79E +
                      age_male_80to84E + age_male_85aE + 
                      age_female_65to66E + age_female_67to69E +
                      age_female_70to74E + age_female_75to79E +
                      age_female_80to84E + age_female_85aE)/age_totalE,
         age_18b_msa = (age_male_5uE + age_male_5to9E +
                      age_male_10to14E + age_male_15to17E +
                      age_female_5uE + age_female_5to9E +
                      age_female_10to14E + age_female_15to17E)/age_totalE,
         median_pvalue_msa = median_pvalueE,
         median_hhld_inc_msa = median_hhld_incE,
         median_fam_inc_msa = median_fam_incE,
         hhld_pov_rt_msa = hhlds_povE/tothhs_msa,
         fam_pov_rt_msa = fams_povE/totfams_msa,
         log_mpv_msa = log(median_pvalue_msa),
         cgrad_msa = (ed_male_baE + ed_male_maE + 
                      ed_male_pdE + ed_male_docE + 
                      ed_female_baE + ed_female_maE + 
                      ed_female_pdE + ed_female_docE)/ed_totalE) %>%
  rename(cbsa10 = GEOID) %>%
  select(cbsa10,
         pop_total_msa,
         pop_nh_aian_msa,
         pop_nh_asian_msa,
         pop_nh_black_msa,
         pop_nh_other_msa,
         pop_nh_nhpi_msa,
         pop_nh_white_msa,
         pop_latinx_msa,
         pop_both_multi_msa,
         per_asian_msa,
         per_black_msa,
         per_latinx_msa,
         per_white_msa,
         per_aian_msa,
         per_other_msa,
         log_asian_msa,
         log_black_msa,
         log_latinx_msa,
         log_white_msa,
         log_aian_msa,
         log_other_msa,
         metro_entropy,
         tothhs_msa,
         totfams_msa,
         hhs_oo_msa,
         age_65a_msa,
         age_18b_msa,
         median_pvalue_msa,
         median_hhld_inc_msa,
         median_fam_inc_msa,
         hhld_pov_rt_msa,
         fam_pov_rt_msa,
         log_mpv_msa,
         cgrad_msa)

msa.area.2019.final <- msa.area.2019.df %>%
  select(GEOID,
         ALAND) %>%
  rename(cbsa10 = GEOID)

## merge on land area ##

msas.2019.complete.m <- stata.merge(msas.2019.final,
                                    msa.area.2019.final,
                                    "cbsa10")

## check merge ## 
table(msas.2019.complete.m$merge.variable, useNA = "ifany")

## keep matches ##
msas.2019.complete <- msas.2019.complete.m %>%
  filter(merge.variable == 3) %>%
  select(-merge.variable) %>%
  mutate(aland_num = as.numeric(ALAND),
         land_area_sqmiles = aland_num/2589988,
         pop_density_msa = pop_total_msa/land_area_sqmiles)

# combine alltracts.2019.p1 and alltracts.2019.p2

alltracts.2019 <- bind_rows(alltracts.2019.p1,
                            alltracts.2019.p2)

## now, clean input tracts file ##

alltracts.2019.final <- alltracts.2019 %>%
  select(GEOID,
         pop_totalE,
         starts_with("pop_h"),
         starts_with("pop_nh")) %>%
  mutate(FIPS = substr(GEOID,1,5),
         pop_total = pop_totalE,
         pop_nh_aian = pop_nh_aianE,
         pop_nh_asian = pop_nh_asianE,
         pop_nh_black = pop_nh_blackE,
         pop_nh_other = pop_nh_otherE,
         pop_nh_nhpi = pop_nh_nhpiE,
         pop_nh_white = pop_nh_whiteE,
         pop_latinx = pop_hE,
         pop_both_multi = pop_nh_multiE,
         per_asian = case_when(pop_total != 0 ~ pop_nh_asianE/pop_total,
                      pop_total == 0 ~ 0),
         per_black = case_when(pop_total != 0 ~ pop_nh_blackE/pop_total,
                      pop_total == 0 ~ 0),
         per_latinx = case_when(pop_total != 0 ~ pop_latinx/pop_total,
                       pop_total == 0 ~ 0),
         per_white = case_when(pop_total != 0 ~ pop_nh_whiteE/pop_total,
                      pop_total == 0 ~ 0),
         per_aian = case_when(pop_total != 0 ~ pop_nh_aianE/pop_total, 
                     pop_total == 0 ~ 0),
         per_other = case_when(pop_total != 0 ~ (pop_nh_otherE + pop_nh_nhpiE + pop_both_multi)/pop_total, 
                      pop_total == 0 ~ 0),
         log_asian = case_when(pop_nh_asianE != 0 ~ log(1/per_asian),
                      pop_nh_asianE == 0 ~ 0),
         log_black = case_when(pop_nh_blackE != 0 ~ log(1/per_black),
                      pop_nh_blackE == 0 ~ 0),
         log_latinx = case_when(pop_latinx != 0 ~ log(1/per_latinx),
                       pop_latinx == 0 ~ 0),
         log_white = case_when(pop_nh_whiteE != 0 ~ log(1/per_white),
                       pop_nh_whiteE == 0 ~ 0),
         log_aian = case_when(pop_nh_aianE != 0 ~ log(1/per_aian),
                     pop_nh_aianE == 0 ~ 0),
         log_other = case_when(pop_nh_otherE + pop_nh_nhpiE + pop_both_multi != 0 ~ log(1/per_other),
                      pop_nh_otherE + pop_nh_nhpiE + pop_both_multi == 0 ~ 0),
         tract_entropy = per_asian*log_asian + 
                         per_black*log_black + 
                         per_latinx*log_latinx + 
                         per_white*log_white +
                         per_aian*log_aian +
                         per_other*log_other)
 
summary(alltracts.2019.final$tract_entropy)

## get cbsa code for tracts ##

nrow(alltracts.2019.final) == length(unique(alltracts.2019.final$FIPS))
class(alltracts.2019.final$FIPS)
range(nchar(trim(alltracts.2019.final$FIPS)))

nrow(msa.del.2020.rd) == length(unique(msa.del.2020.rd$FIPS))
class(msa.del.2020.rd$FIPS)
range(nchar(trim(msa.del.2020.rd$FIPS)))

metro.tracts.2019.m <- stata.merge(alltracts.2019.final,
                                   msa.del.2020.rd,
                                   "FIPS")

table(metro.tracts.2019.m$merge.variable, useNA = "ifany")

## keep matches ## 
metro.tracts.2019 <- metro.tracts.2019.m %>%
  filter(merge.variable == 3) %>%
  select(-`CBSA Code`,
         -`Metropolitan Division Code`,
         -`CSA Code`,
         -`CBSA Title`,
         -`Metropolitan/Micropolitan Statistical Area`,
         -`Metropolitan Division Title`,
         -`CBSA Title`,
         -`County/County Equivalent`,
         -`State Name`,
         -`FIPS State Code`,
         -`FIPS County Code`,
         -`Central/Outlying County`)

## now merge onto tracts ##

nrow(msas.2019.complete) == length(unique(msas.2019.complete$cbsa10))
class(msas.2019.complete$cbsa10)
range(nchar(trim(msas.2019.complete$cbsa10)))

nrow(metro.tracts.2019) == length(unique(metro.tracts.2019$cbsa10))
class(metro.tracts.2019$cbsa10)
range(nchar(trim(metro.tracts.2019$cbsa10)))

msas.tracts.2019.m <- stata.merge(msas.2019.complete,
                                  metro.tracts.2019,
                                  "cbsa10")

## check merge ##
table(msas.tracts.2019.m$merge.variable, useNA = "ifany")

metro.DH <- msas.tracts.2019.m %>%
  filter(merge.variable == 3) %>%
  select(-merge.variable) %>%
  mutate(D_comp_aian = case_when(pop_nh_aian != 0 ~ per_aian * log(per_aian/per_aian_msa),
                                 pop_nh_aian == 0 ~ 0),
         D_comp_asian = case_when(pop_nh_asian != 0 ~ per_asian * log(per_asian/per_asian_msa),
                                  pop_nh_asian == 0 ~ 0),
         D_comp_black = case_when(pop_nh_black != 0 ~ per_black * log(per_black/per_black_msa),
                                  pop_nh_black == 0 ~ 0),
         D_comp_latinx = case_when(pop_latinx != 0 ~ per_latinx * log(per_latinx/per_latinx_msa),
                                  pop_latinx == 0 ~ 0),
         D_comp_other = case_when(pop_nh_other != 0 ~ per_other * log(per_other/per_other_msa),
                                  pop_nh_other == 0 ~ 0),
         D_comp_white = case_when(pop_nh_white != 0 ~ per_white * log(per_white/per_white_msa),
                                  pop_nh_white == 0 ~ 0),
         D_comp_all = D_comp_aian + D_comp_asian + D_comp_black + D_comp_latinx + D_comp_other + D_comp_white,
         D_comp_final = (pop_total/pop_total_msa) * D_comp_all,
         H_comp = (pop_total/pop_total_msa) * (metro_entropy - tract_entropy)/metro_entropy) %>%
  group_by(cbsa10) %>%
  summarize(metro_H = sum(H_comp,na.rm=T),
            metro_D = sum(D_comp_final, na.rm=T)) 

summary(metro.DH$metro_H)
summary(metro.DH$metro_D)

## merge 1 ##

msa.fm1.2019 <- stata.merge(msas.2019.complete,
                            metro.DH,
                            "cbsa10")

table(msa.fm1.2019$merge.variable, useNA = "ifany")


msa.k1.2019 <- msa.fm1.2019 %>%
  filter(merge.variable == 3) %>%
  select(-merge.variable)

## merge 2 ##

nzlu.msa.2019.fm <- nzlu.msa.2019.final %>%
  select(cbsa10,
         zri_full_st)

msa.fm2.2019 <- stata.merge(msa.k1.2019,
                            nzlu.msa.2019.fm,
                            "cbsa10")

## check merge ##
table(msa.fm2.2019$merge.variable, useNA = "ifany")


msa.k2.2019 <- msa.fm2.2019 %>%
  filter(merge.variable == 3) %>%
  select(-merge.variable)

summary(msa.k2.2019$ez.index.st)

## merge on rank H ##

rankH$cbsa10 <- as.character(rankH$metro)

nrow(rankH) == length(unique(rankH$cbsa10))
class(rankH$cbsa10)
range(nchar(trim(rankH$cbsa10)))

msa.k3.2019.m <- stata.merge(msa.k2.2019,
                             rankH,
                             "cbsa10")

table(msa.k3.2019.m$merge.variable, useNA = "ifany")

msa.k3.2019 <- msa.k3.2019.m %>%
  filter(merge.variable==3) %>%
  select(-merge.variable)

## keep matches ##
nzlu.msa.sda <- msa.k3.2019 %>%
  mutate(rl = case_when(zri_full_st < -0.56284 ~ "low",
                        zri_full_st >= -0.56284 & zri_full_st <= 0.54044   ~ "medium",
                        zri_full_st > 0.54044   ~ "high"))

nzlu.msa.sda.l <- nzlu.msa.sda %>%
  filter(rl == "low")

nzlu.msa.sda.m <- nzlu.msa.sda %>%
  filter(rl == "medium") 

nzlu.msa.sda.h <- nzlu.msa.sda %>%
  filter(rl == "high") 

nrow(nzlu.msa.sda.l) + nrow(nzlu.msa.sda.m) + nrow(nzlu.msa.sda.h) == 327


nzlu.msa.sda.ls <- nzlu.msa.sda.l %>%
  group_by(rl) %>%
  summarize(median_hh_income = mean(median_hhld_inc_msa, na.rm=T),
            median_prop_value = mean(median_pvalue_msa, na.rm=T),
            pc_cg = mean(cgrad_msa, na.rm=T),
            hhld_pov_rt = mean(hhld_pov_rt_msa, na.rm=T),
            entropy = mean(metro_entropy, na.rm=T),
            metroH = mean(h4_adj, na.rm=T),
            metroD = mean(metro_D, na.rm=T),
            per_white = mean(per_white_msa, na.rm=T),
            pop = mean(pop_total_msa, na.rm=T),
            land_area = mean(land_area_sqmiles, na.rm=T),
            pop_density = mean(pop_density_msa, na.rm=T))

nzlu.msa.sda.ms <- nzlu.msa.sda.m %>%
  group_by(rl) %>%
  summarize(median_hh_income = mean(median_hhld_inc_msa, na.rm=T),
            median_prop_value = mean(median_pvalue_msa, na.rm=T),
            pc_cg = mean(cgrad_msa, na.rm=T),
            hhld_pov_rt = mean(hhld_pov_rt_msa, na.rm=T),
            entropy = mean(metro_entropy, na.rm=T),
            metroH = mean(h4_adj, na.rm=T),
            metroD = mean(metro_D, na.rm=T),
            per_white = mean(per_white_msa, na.rm=T),
            pop = mean(pop_total_msa, na.rm=T),
            land_area = mean(land_area_sqmiles, na.rm=T),
            pop_density = mean(pop_density_msa, na.rm=T))

nzlu.msa.sda.hs <- nzlu.msa.sda.h %>%
  group_by(rl) %>%
  summarize(median_hh_income = mean(median_hhld_inc_msa, na.rm=T),
            median_prop_value = mean(median_pvalue_msa, na.rm=T),
            pc_cg = mean(cgrad_msa, na.rm=T),
            hhld_pov_rt = mean(hhld_pov_rt_msa, na.rm=T),
            entropy = mean(metro_entropy, na.rm=T),
            metroH = mean(h4_adj, na.rm=T),
            metroD = mean(metro_D, na.rm=T),
            per_white = mean(per_white_msa, na.rm=T),
            pop = mean(pop_total_msa, na.rm=T),
            land_area = mean(land_area_sqmiles, na.rm=T),
            pop_density = mean(pop_density_msa, na.rm=T))

print(t(nzlu.msa.sda.ls))            
print(t(nzlu.msa.sda.ms))  
print(t(nzlu.msa.sda.hs))

################
## last items ##
################

prop.table(table(nzlu.2019.final$adu, useNA = "ifany"))
summary(nzlu.2019.final$sindex9)
sd(nzlu.2019.final$sindex9, na.rm=T)
summary(nzlu.2019.final$sindex10)
sd(nzlu.2019.final$sindex10, na.rm=T)
summary(nzlu.2019.final$sindex11)
sd(nzlu.2019.final$sindex11,na.rm=T)

## subindex analysis ##

msa.test <- nzlu.msa.2019.final %>%
  select(cbsa10,
         cbsaname10,
         open_space,
         one_acre_more,
         two_acre_more,
         inclusionary,
         adu,
         starts_with("maxden"),
         starts_with("zri"))

msa.test10 <- msa.test %>%
  filter(cbsa10 %in% nzlu.msa.large.2019$cbsa10) %>%
  mutate(mls = one_acre_more + two_acre_more)

### END OF PROGRAM ###

#sink()
