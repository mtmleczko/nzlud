########################################################
## PROGRAM NAME: 003_weights.R                        ##
## AUTHOR: MATT MLECZKO                               ##
## DATE CREATED: 04/22/2021                           ##
## INPUTS:                                            ##
##    All2010places.csv                               ##
##    Cousub_comparability.csv                        ##
##    WHARTON LAND REGULATION DATA_1_24_2008.dta      ##
##    WRLURI_01_15_2020.dta                           ##
##    002_nzlu_place_2019.Rda                         ##
##    002_wrld_nllus_place_2006.Rda                   ##
##    001_cstm_2010.Rda                               ##
##    001_ptm_2010.Rda                                ##
##    cosubs_popdensity_2009.csv                      ##
##    places_popdensity_2009.csv                      ##
##                                                    ##
## OUTPUTS:                                           ##
##    003_allmunis_2009.Rda                           ##
##    003_msa_munis_2009.Rda                          ##
##    003_wrld_nllus_wts_all_2006.Rda                 ##
##    003_wrld_nllus_wts_msa_2006.Rda                 ##
##    003_allmunis_2019.Rda                           ##
##    003_msa_munis_2019.Rda                          ##
##    003_nzlu_wts_all_2019.Rda                       ##
##    003_nzlu_wts_msa_2019.Rda                       ##
##                                                    ##
## PURPOSE: Recreate IP weights                       ##
##                                                    ##
## LIST OF UPDATES:                                   ##
########################################################

#log <- file("path to programs here/003_weights.txt")
#sink(log, append=TRUE)
#sink(log, append=TRUE, type="message")

## load libraries ## 

library("haven")
library("foreign")
library("tidyverse")
library("stringr")
library("readxl")
library("writexl")
library("gdata")
library("tm")
library("gsubfn")
library("tidycensus")
library("tigris")
library("sf")
library("stargazer")
library("broom")
library(ggplot2)

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

## read in data ## 

## place FIPS ##
allpl.2010 <- read.csv("All2010places.csv",
                       header = T,
                       stringsAsFactors = F)

## cosub FIPS ## 
allcs.2010 <- read.csv("Cousub_comparability.csv",
                       header = T,
                       stringsAsFactors = F)

wrld.2006.in <- read_dta(paste(input_path,
                               "WHARTON LAND REGULATION DATA_1_24_2008.dta",
                               sep=""))

wrld.2018.in <- read_dta(paste(input_path,
                               "WRLURI_01_15_2020.dta",
                               sep=""))

load(paste(output_path,
           "002_nzlu_place_2019.Rda",
           sep = ""))

load(paste(output_path,
           "002_wrld_nllus_place_2006.Rda",
           sep= ""))

load(paste(output_path,
           "001_cstm_2010.Rda",
           sep=""))

load(paste(output_path,
           "001_ptm_2010.Rda",
           sep = ""))


## read-in 2009 pop density info ##
places_popdensity_2009.in <- read.csv("places_popdensity_2009.csv",
                                      header = T,
                                      stringsAsFactors = F)

cosubs_popdensity_2009.in <- read.csv("cosubs_popdensity_2009.csv",
                                      header = T,
                                      stringsAsFactors = F)


#####################################
## initial processing of FIPS data ##
#####################################

## fix the missing 0s in allpl.2010 ## 
allpl.2010$STATEFP00 <- str_pad(allpl.2010$STATEFP00, 2, pad = "0")
allpl.2010$STATEFP10 <- str_pad(allpl.2010$STATEFP10, 2, pad = "0")

allpl.2010$PLACEFP00 <- str_pad(allpl.2010$PLACEFP00, 5, pad = "0")
allpl.2010$PLACEFP10 <- str_pad(allpl.2010$PLACEFP10, 5, pad = "0")

## fix the missing 0s in allcs.2010 ## 
allcs.2010$GEOID00 <- str_pad(allcs.2010$GEOID00, 10, pad = "0")
allcs.2010$GEOID10 <- str_pad(allcs.2010$GEOID10, 10, pad = "0")

allcs.2010$STATEFP00 <- str_pad(allcs.2010$STATEFP00, 2, pad = "0")
allcs.2010$STATEFP10 <- str_pad(allcs.2010$STATEFP10, 2, pad = "0")

allcs.2010$COUNTYFP00 <- str_pad(allcs.2010$COUNTYFP00, 3, pad = "0")
allcs.2010$COUNTYFP10 <- str_pad(allcs.2010$COUNTYFP10, 3, pad = "0")

allcs.2010$COUSUBFP00 <- str_pad(allcs.2010$COUSUBFP00, 5, pad = "0")
allcs.2010$COUSUBFP10 <- str_pad(allcs.2010$COUSUBFP10, 5, pad = "0")

## process further ## 

## places ##
allpl.2010.pr <- allpl.2010 %>%
  filter(NAMELSAD != "") %>%
  rename(fullname = NAMELSAD) %>%
  select(fullname,
         STATEFP00,
         STATEFP10,
         PLACEFP00,
         PLACEFP10) %>%
  mutate(place00 = paste(STATEFP00,PLACEFP00, sep=""),
         place10 = paste(STATEFP10,PLACEFP10, sep=""))

## cosubs ##
allcs.2010.pr <- allcs.2010 %>%
  filter(STATEFP00 != "" & 
         COUSUBFP00 != "") %>%
  rename(fullname = NAMELSAD10) %>%
  select(fullname,
         GEOID00,
         GEOID10,
         STATEFP00,
         STATEFP10,
         COUNTYFP00,
         COUNTYFP10,
         COUSUBFP00,
         COUSUBFP10) %>%
  mutate(cosub00 = paste(STATEFP00,COUSUBFP00, sep=""),
         cosub10 = paste(STATEFP10,COUSUBFP10, sep=""),
         GEOID = paste(STATEFP10,COUSUBFP10, sep=""))


## clean the 2009 pop density info ## 

## places ##
places_popdensity_2009 <- places_popdensity_2009.in %>%
  select(Geo_FIPS,
         Geo_GEOID,
         Geo_NAME,
         Geo_STATE,
         Geo_COUNTY,
         Geo_COUSUB,
         Geo_PLACE,
         Geo_COUSUB,
         SE_A00002_001,
         SE_A00002_002,
         SE_A00002_003) %>%
  rename(total_pop = SE_A00002_001,
         area = SE_A00002_002,
         pop_density = SE_A00002_003) %>%
  filter(total_pop > 0 & Geo_STATE != "72")

places_popdensity_2009$Geo_STATE <- str_pad(places_popdensity_2009 $Geo_STATE, 2, pad = "0")
places_popdensity_2009$Geo_PLACE <- str_pad(places_popdensity_2009$Geo_PLACE, 5, pad = "0")
places_popdensity_2009$GEOID <- paste(places_popdensity_2009$Geo_STATE,
                                      places_popdensity_2009$Geo_PLACE,
                                      sep="")

## cosubs ##
cosubs_popdensity_2009 <- cosubs_popdensity_2009.in %>%
  select(Geo_FIPS,
         Geo_GEOID,
         Geo_NAME,
         Geo_COUNTY,
         Geo_STATE,
         Geo_COUSUB,
         Geo_PLACE,
         SE_A00002_001,
         SE_A00002_002,
         SE_A00002_003) %>%
  rename(total_pop = SE_A00002_001,
         area = SE_A00002_002,
         pop_density = SE_A00002_003) %>%
  mutate(GEOID_full = Geo_FIPS) %>%
  filter(total_pop > 0 & Geo_STATE != "72" & !grepl("CCD|precinct", Geo_NAME))

cosubs_popdensity_2009$Geo_STATE <- str_pad(cosubs_popdensity_2009 $Geo_STATE, 2, pad = "0")
cosubs_popdensity_2009$Geo_COUSUB <- str_pad(cosubs_popdensity_2009$Geo_COUSUB, 5, pad = "0")
cosubs_popdensity_2009$GEOID_full <- str_pad(cosubs_popdensity_2009 $GEOID_full, 10, pad = "0")
cosubs_popdensity_2009$GEOID_short <- paste(cosubs_popdensity_2009$Geo_STATE,
                                            cosubs_popdensity_2009$Geo_COUSUB,
                                            sep="")


## states to loop through ##
states <- c("AL","AK","AZ","AR","CA","CO","CT","DE",
            "DC","FL","GA","HI","ID","IL","IN","IA","KS",
            "KY","LA","ME","MD","MA","MI","MN","MS","MO",
            "MT","NE","NV","NH","NJ","NM","NY","NC","ND",
            "OH","OK","OR","PA","RI","SC","SD","TN","TX",
            "UT","VT","VA","WA","WV","WI","WY")

###############
## 2005-2009 ##
###############

## get ACS data ##

## View 2005-2009 Census variables ##
v2009 <- load_variables(2009, "acs5", cache=TRUE)

## initialize lists to store data frames ##
state.places.2009 <- list() 
state.cosubs.2009 <- list()

## initialize counter ## 
state.counter <- 1

## start the loop ##
for (st in states){
  
  ## get data for CDPs ##
  cdp2009 <- get_acs(geography = "place", 
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
                       state = st, 
                       survey = "acs5",
                       output = "wide",
                       year = 2009)
  
  ## add state identifying variable ##
  cdp2009$state <- st
  
  ## store the data frame in the list ## 
  state.places.2009[[state.counter]] <- cdp2009
  
  cosub2009 <- get_acs(geography = "county subdivision", 
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
                       state = st, 
                       survey = "acs5",
                       output = "wide",
                       year = 2009)
  
  ## add state identifying variable ##
  cosub2009$state <- st
  
  ## store the data frame in the list ## 
  state.cosubs.2009[[state.counter]] <- cosub2009
  
  ## increase interval by 1 ## 
  state.counter <- state.counter + 1
  
}

## combine all the data ## 

all.cdps.2009 <- bind_rows(state.places.2009)
all.cosubs.2009 <- bind_rows(state.cosubs.2009)

## reformat the cosub dataframe ## 

cosub.rf <- all.cosubs.2009 %>%
  filter(!grepl('CCD', NAME)) %>%
  mutate(geoid.f = paste(substr(GEOID,1,2),
                         substr(GEOID,6,12),
                         sep=""))

## create merge variable on cdps dataframe ##
all.cdps.2009$geoid.f <- all.cdps.2009$GEOID

## check for overlapping munis ## 

nrow(all.cdps.2009) == length(unique(all.cdps.2009$geoid.f))
class(all.cdps.2009$geoid.f)
range(nchar(trim(all.cdps.2009$geoid.f)))

nrow(cosub.rf) == length(unique(cosub.rf$geoid.f))
class(cosub.rf$geoid.f)
range(nchar(trim(cosub.rf$geoid.f)))


overlap.2009 <- stata.merge(all.cdps.2009,
                            cosub.rf,
                            "geoid.f")

## check overlap ## 
table(overlap.2009$merge.variable)

## create final muni dataframe ##

## for the non-matches, we can just drop the variables of the non-matching obs ##

munis.fin1.2009 <- overlap.2009 %>%
  filter(merge.variable ==1) %>%
  select(-ends_with(".y"))

names(munis.fin1.2009) <- sub(".x", "", names(munis.fin1.2009))

munis.fin2.2009 <- overlap.2009 %>%
  filter(merge.variable ==2) %>%
  select(-ends_with(".x"),
         -merge.variable)

names(munis.fin2.2009) <- sub(".y", "", names(munis.fin2.2009))

## the matches are more complicated ##
## the issue here is that place codes have no county code component ##
## so there will be duplicates when merging with reduced cosub codes ##
## the solution will be to deal with the duplicates manually ##

## collect cosubs with duplicate GEOIDs ##
munis.fin3.2009.v1 <- overlap.2009 %>%
  filter(merge.variable ==3) %>%
  select(-ends_with(".x"),
         -merge.variable)

## collect the corresponding duplicates ##
munis.fin3.2009.v2 <- overlap.2009 %>%
  filter(merge.variable ==3) %>%
  select(-ends_with(".y"),
         -merge.variable)

## make the vars conform ##
names(munis.fin3.2009.v1) <- sub(".y", "", names(munis.fin3.2009.v1))
names(munis.fin3.2009.v2) <- sub(".x", "", names(munis.fin3.2009.v2))

## stack the duplicates ##
munis.fin3.2009.stacked <- rbind(munis.fin3.2009.v1,
                                 munis.fin3.2009.v2)

## remove true duplicate munis ## 
munis.fin3.dd.2009 <- unique(munis.fin3.2009.stacked)

## now, fix the remaining duplicates ##
## case 1: same exact places/cosubs, just listed both as places and county subs ##
munis.fin3.gr1.2009 <- munis.fin3.dd.2009 %>% 
  group_by_at(vars(-c(GEOID, NAME))) %>% 
  filter(n() > 1) %>%
  summarize_all(list(first)) %>%
  select(geoid.f,
         GEOID,
         NAME,
         everything())

munis.fin3.gr1.2009 <- as.data.frame(munis.fin3.gr1.2009)

## case 2: different places/cosubs, but same reduced FIPS codes as other cosubs ##
## case 3: places/cosubs that extend into multiple counties ##

munis.fin3.gr2.2009 <- munis.fin3.dd.2009 %>%
  filter(geoid.f %notin% munis.fin3.gr1.2009$geoid.f)

fin3.2.s1a <- munis.fin3.gr2.2009 %>%
  filter(nchar(GEOID) == 10) %>%
  group_by(geoid.f) %>%
  summarize_if(is.numeric, list(sum))

fin3.2.s1b <- munis.fin3.gr2.2009 %>%
  filter(nchar(GEOID) == 10) %>%
  group_by(geoid.f) %>%
  summarize_if(is.character, list(first))

fin3.2.s1 <- inner_join(fin3.2.s1a,
                        fin3.2.s1b,
                        "geoid.f")

fin3.2.s1.rf <- fin3.2.s1 %>%
  select(geoid.f,
         GEOID,
         NAME, 
         everything())

fin3.2.s2 <- munis.fin3.gr2.2009 %>%
  filter(nchar(GEOID) < 10) 

fin3.2.s3 <- rbind(fin3.2.s1.rf,
                   fin3.2.s2)

fin3.2.s4 <- fin3.2.s3 %>%
  group_by(geoid.f, totpopE) %>%
  summarize_all(list(last))

## need to check these manually ##
fin3.mcheck <- fin3.2.s4 %>%
  group_by(geoid.f) %>%
  summarize(n = n()) %>%
  filter(n>1)


## manual fixes ##
munis.fin1.2009.final <- munis.fin1.2009 %>%
  select(-merge.variable)

munis.fin2.2009.final <- munis.fin2.2009 %>%
  filter(geoid.f %notin% c("3192103","3193203","3918100","3929176"))

munis.fin3a.2009.final <- fin3.2.s4 %>%
  filter(GEOID %notin% c("3114134230","3100348935","3606576540","3909917036",
                         "3904918000","3904122694","3917328014","3911729162",
                         "3901749840","3910367356","3906171892"))

munis.fin3a.2009.final <- as.data.frame(munis.fin3a.2009.final)

munis.fin3b.2009.final <- munis.fin3.gr1.2009


munis.fin3.2009.final <- rbind(munis.fin3a.2009.final,
                               munis.fin3b.2009.final)

class(munis.fin3.2009.final)

munis.fin3.2009.final <- as.data.frame(munis.fin3.2009.final)

## combine data for final data frame ## 
munis.fin.2009 <- rbind(munis.fin1.2009.final,
                        munis.fin2.2009.final,
                        munis.fin3.2009.final)

## clean data ## 

munis.fin.cl.2009 <- munis.fin.2009 %>%
  filter(!grepl('precinct', NAME) & totpopE >0) %>%
  mutate(#GEOID = geoid.f,
         totpop = totpopE,
         tothhs = tothhsE,
         totfams = totfamsE,
         hhs_oo = hhs_ooE/tothhs,
         age_65a = (age_male_65to66E + age_male_67to69E +
                    age_male_70to74E + age_male_75to79E +
                    age_male_80to84E + age_male_85aE + 
                    age_female_65to66E + age_female_67to69E +
                    age_female_70to74E + age_female_75to79E +
                    age_female_80to84E + age_female_85aE)/age_totalE,
         age_18b = (age_male_5uE + age_male_5to9E +
                    age_male_10to14E + age_male_15to17E +
                    age_female_5uE + age_female_5to9E +
                    age_female_10to14E + age_female_15to17E)/age_totalE,
         median_pvalue = median_pvalueE,
         median_hhld_inc = median_hhld_incE,
         median_fam_inc = median_fam_incE,
         hhld_pov_rt = hhlds_povE/tothhs,
         fam_pov_rt = fams_povE/totfams,
         log_mpv = log(median_pvalue),
         cgrad = (ed_male_baE + ed_male_maE + 
                  ed_male_pdE + ed_male_docE + 
                  ed_female_baE + ed_female_maE + 
                  ed_female_pdE + ed_female_docE)/ed_totalE,
         pop_latinx = pop_h_aianE + pop_h_asianE + pop_h_blackE + 
                      pop_h_nhpiE + pop_h_otherE + pop_h_whiteE,
         pop_latinx_multi = pop_h_multiE,
         pop_both_multi = pop_nh_multiE + pop_latinx_multi,
         per_asian = case_when(totpop != 0 ~ pop_nh_asianE/totpop,
                               totpop == 0 ~ 0),
         per_black = case_when(totpop != 0 ~ pop_nh_blackE/totpop,
                               totpop == 0 ~ 0),
         per_latinx = case_when(totpop != 0 ~ pop_latinx/totpop,
                                totpop == 0 ~ 0),
         per_white = case_when(totpop != 0 ~ pop_nh_whiteE/totpop,
                               totpop == 0 ~ 0),
         per_AIAN = case_when(totpop != 0 ~ pop_nh_aianE/totpop, 
                              totpop == 0 ~ 0),
         per_other = case_when(totpop != 0 ~ (pop_nh_otherE + pop_nh_nhpiE + pop_both_multi)/totpop, 
                               totpop == 0 ~ 0),
         log_asian = case_when(pop_nh_asianE != 0 ~ log(1/per_asian),
                               pop_nh_asianE == 0 ~ 0),
         log_black = case_when(pop_nh_blackE != 0 ~ log(1/per_black),
                               pop_nh_blackE == 0 ~ 0),
         log_latinx = case_when(pop_latinx != 0 ~ log(1/per_latinx),
                                pop_latinx == 0 ~ 0),
         log_white = case_when(pop_nh_whiteE != 0 ~ log(1/per_white),
                               pop_nh_whiteE == 0 ~ 0),
         log_AIAN = case_when(pop_nh_aianE != 0 ~ log(1/per_AIAN),
                              pop_nh_aianE == 0 ~ 0),
         log_other = case_when(pop_nh_otherE + pop_nh_nhpiE + pop_both_multi != 0 ~ log(1/per_other),
                               pop_nh_otherE + pop_nh_nhpiE + pop_both_multi == 0 ~ 0),
         entropy = per_asian*log_asian + 
                   per_black*log_black + 
                   per_latinx*log_latinx + 
                   per_white*log_white +
                   per_AIAN*log_AIAN +
                   per_other*log_other) %>%
  select(GEOID,
         geoid.f,
         NAME,
         totpop,
         tothhs,
         totfams,
         hhs_oo,
         age_65a,
         age_18b,
         per_white,
         log_mpv,
         median_pvalue,
         median_hhld_inc,
         median_fam_inc,
         hhld_pov_rt,
         fam_pov_rt,
         cgrad,
         entropy)

## now, merge on land and pop density info ##
nrow(munis.fin.cl.2009) == length(unique(munis.fin.cl.2009$GEOID))
class(munis.fin.cl.2009$GEOID)
range(nchar(trim(munis.fin.cl.2009$GEOID)))

nrow(places_popdensity_2009) == length(unique(places_popdensity_2009$GEOID))
class(places_popdensity_2009$GEOID)
range(nchar(trim(places_popdensity_2009$GEOID)))

## merge 1 ## 
munis.fin.wpd1a.2009.m <- stata.merge(munis.fin.cl.2009,
                                      places_popdensity_2009,
                                      "GEOID")

table(munis.fin.wpd1a.2009.m$merge.variable, useNA = "ifany")

munis.fin.wpd1a.2009 <- munis.fin.wpd1a.2009.m %>%
  filter(merge.variable == 3) %>%
  select(-merge.variable) %>%
  rename(GEOID_full = GEOID,
         GEOID = geoid.f)

pp.fm2 <- munis.fin.wpd1a.2009.m %>%
  filter(merge.variable ==2) %>%
  select(GEOID,
         Geo_FIPS,
         Geo_GEOID,
         Geo_NAME,
         Geo_STATE,
         Geo_COUNTY,
         Geo_PLACE,
         Geo_COUSUB,
         total_pop,
         area,
         pop_density)

## merge 2 ##
nrow(pp.fm2) == length(unique(pp.fm2$GEOID))
class(pp.fm2$GEOID)
range(nchar(trim(pp.fm2$GEOID)))

munis.fin.cl.2009.fm2 <- munis.fin.wpd1a.2009.m %>%
  filter(merge.variable==1) %>%
  rename(GEOID_full = GEOID,
         GEOID = geoid.f) %>%
  select(GEOID_full,
         GEOID,
         NAME,
         totpop,
         tothhs,
         totfams,
         hhs_oo,
         age_65a,
         age_18b,
         per_white,
         log_mpv,
         median_pvalue,
         median_hhld_inc,
         median_fam_inc,
         hhld_pov_rt,
         fam_pov_rt,
         cgrad,
         entropy)

nrow(munis.fin.cl.2009.fm2) == length(unique(munis.fin.cl.2009.fm2$GEOID))
class(munis.fin.cl.2009.fm2$GEOID)
range(nchar(trim(munis.fin.cl.2009.fm2$GEOID)))

munis.fin.wpd1b.2009.m <- stata.merge(pp.fm2,
                                      munis.fin.cl.2009.fm2,
                                      "GEOID")

## check merge ##
table(munis.fin.wpd1b.2009.m$merge.variable, useNA = "ifany")

munis.fin.wpd1b.2009 <- munis.fin.wpd1b.2009.m %>%
  filter(merge.variable == 3) %>%
  select(-merge.variable)

munis.fin.pld <- rbind(munis.fin.wpd1a.2009,
                       munis.fin.wpd1b.2009)

## obs check ##
nrow(munis.fin.pld) == nrow(places_popdensity_2009)

## now, merge on density data for county subs ##

nrow(munis.fin.cl.2009) == length(unique(munis.fin.cl.2009$GEOID))
class(munis.fin.cl.2009$GEOID)
range(nchar(trim(munis.fin.cl.2009$GEOID)))


cosubs_popdensity_2009$GEOID <- cosubs_popdensity_2009$GEOID_full
nrow(cosubs_popdensity_2009) == length(unique(cosubs_popdensity_2009$GEOID))
class(cosubs_popdensity_2009$GEOID)
range(nchar(trim(cosubs_popdensity_2009$GEOID)))

## merge 1 ## 
munis.fin.wpd2a.2009.m <- stata.merge(munis.fin.cl.2009,
                                      cosubs_popdensity_2009,
                                      "GEOID")

table(munis.fin.wpd2a.2009.m$merge.variable, useNA = "ifany")

munis.fin.wpd2a.2009 <- munis.fin.wpd2a.2009.m %>%
  filter(merge.variable == 3) %>%
  select(-merge.variable,
         -geoid.f,
         -GEOID_short)

## combine all obs with density info ##

munis.fin.wpd.2009 <- rbind(munis.fin.wpd1a.2009,
                            munis.fin.wpd1b.2009,
                            munis.fin.wpd2a.2009)

munis.fin.wpd.2009.dd <- munis.fin.wpd.2009 %>%
  select(-Geo_FIPS,
         -Geo_GEOID,
         -Geo_STATE,
         -Geo_COUNTY,
         -Geo_COUSUB,
         -Geo_PLACE) %>%
  group_by_at(vars(-c(GEOID, Geo_NAME))) %>%
  summarize_all(list(last)) %>%
  ungroup() %>%
  select(GEOID,
         GEOID_full,
         total_pop,
         area,
         pop_density)

## obs check ##
nrow(munis.fin.wpd.2009.dd) == nrow(munis.fin.cl.2009)


## merge back to working data ##

munis.fin.wpd.2009.merged <- stata.merge(munis.fin.cl.2009,
                                         munis.fin.wpd.2009.dd,
                                         "GEOID")

## check the merge ##
table(munis.fin.wpd.2009.merged$merge.variable)


## keep matches ##
munis.fin.fm.2009 <- munis.fin.wpd.2009.merged %>%
  filter(merge.variable == 3) %>%
  select(-merge.variable,
         -GEOID) %>%
  rename(GEOID = geoid.f)


## adjust FIPS  - WHARTON ##
wrld.nllus.2006 <- wrld.nllus.2006.final %>%
  select(GEOID)

## adjust FIPS  - CENSUS ##
munis.fin.fmf.2009 <- munis.fin.fm.2009 %>%
  mutate(GEOID = case_when(
    GEOID == "1517000" ~ "1571550",
    GEOID == "2527025" ~ "2527100",
    GEOID == "2552105" ~ "2552144",
    GEOID == "2563270" ~ "2563345",
    GEOID == "2577850" ~ "2577890",
    GEOID == "2578865" ~ "2578972",
    GEOID == "3983111" ~ "3983090",
    GEOID == "2500765" ~ "2500840",
    GEOID == "2519330" ~ "2519370",
    TRUE ~ as.character(GEOID))) 

## create sample indicator ## 

nrow(munis.fin.fm.2009) == length(unique(munis.fin.fm.2009$GEOID))
class(munis.fin.fm.2009$GEOID)
range(nchar(trim(munis.fin.fm.2009$GEOID)))

munis.cb.2009 <- stata.merge(munis.fin.fmf.2009,
                             wrld.nllus.2006,
                             "GEOID")

## check merge ##
table(munis.cb.2009$merge.variable)

## final munis ## 

munis.final.2009 <- munis.cb.2009 %>%
  mutate(in.sample = case_when(
    merge.variable == 3 ~ 1, 
    merge.variable %in% c(1,2) ~ 0)) %>%
  select(-merge.variable) %>%
  filter((!grepl("CDP", NAME)) |
         (grepl("CDP", NAME) & substr(GEOID,1,2) == "15") |
         (GEOID %in% c("0286490", "2365725")))
   
## check ##
table(munis.final.2009$in.sample)

## how much of the population does the final sample represent? ##

sum(munis.final.2009$totpop[munis.final.2009$in.sample==1], na.rm=T)/sum(munis.final.2009$totpop, na.rm=T)

## checks ## 

summary(munis.final.2009)

## save data for all munis ##
save(munis.final.2009,
     file = paste(output_path,
                  "003_allmunis_2009.Rda",
                  sep=""))


## create msa sample file ##

## merge checks ## 
nrow(munis.final.2009) == length(unique(munis.final.2009$GEOID))
class(munis.final.2009$GEOID)
range(nchar(trim(munis.final.2009$GEOID)))

nrow(ptm.2010.rd) == length(unique(ptm.2010.rd$GEOID))
class(ptm.2010.rd$GEOID)
range(nchar(trim(ptm.2010.rd$GEOID)))


## merge data frames ## 
muni.msa.2009.m1 <- stata.merge(munis.final.2009,
                                ptm.2010.rd,
                                "GEOID")

## check merge ## 
table(muni.msa.2009.m1$merge.variable)

## output non-matches eligible for match with county subs ##
no.msa.2009.m1 <- muni.msa.2009.m1 %>%
  filter(merge.variable ==1) %>%
  select(-placefp,
         -stab,
         -placenm,
         -cbsa10,
         -cbsaname10,
         -pop10,
         -afact,
         -state,
         -merge.variable)

## keep matches ## 
muni.msa.2009.keep1 <- muni.msa.2009.m1 %>%
  mutate(afact_num = as.numeric(afact)) %>%
  filter(merge.variable ==3) %>%
  group_by(GEOID) %>%
  slice(which.max(afact_num)) %>%
  select(-placefp,
         -stab,
         -placenm,
         -pop10,
         -afact,
         -merge.variable)

## check for dups ## 
## these are places that span multiple MSAs ##
muni.msa.2009.dupcheck1 <- muni.msa.2009.keep1 %>%
  group_by(GEOID) %>%
  summarize(n=n()) %>%
  filter(n>1)

## get rid of duplicates ## 

#muni.msa.2009.keep1.rd <- muni.msa.2009.keep1 %>%
  #filter(!(GEOID == "2910828" & cbsa10 == "41140"))

## check ##
nrow(muni.msa.2009.keep1) == length(unique(muni.msa.2009.keep1$GEOID))

## now, county subs ## 

## merge checks ##
nrow(cstm.2010.rd) == length(unique(cstm.2010.rd$GEOID))
class(cstm.2010.rd$GEOID)
range(nchar(trim(cstm.2010.rd$GEOID)))

nrow(no.msa.2009.m1) == length(unique(no.msa.2009.m1$GEOID))
class(no.msa.2009.m1$GEOID)
range(nchar(trim(no.msa.2009.m1$GEOID)))

## merge data frames ## 
muni.msa.2009.m2 <- stata.merge(no.msa.2009.m1,
                                cstm.2010.rd,
                                "GEOID")

## check merge ##
table(muni.msa.2009.m2$merge.variable)

## keep matches ## 
muni.msa.2009.keep2 <- muni.msa.2009.m2 %>%
  mutate(afact_num = as.numeric(afact)) %>%
  filter(merge.variable ==3) %>%
  group_by(GEOID) %>%
  slice(which.max(afact_num)) %>%
  select(-county,
         -cousubfp,
         -cntyname,
         -cousubnm,
         -pop10,
         -afact,
         -merge.variable)

## check for dups ## 
## these are places that span multiple MSAs ##
muni.msa.2009.dupcheck2 <- muni.msa.2009.keep2 %>%
  group_by(GEOID) %>%
  summarize(n=n()) %>%
  filter(n>1)

## append the two matched dataframes ##

muni.msa.2009 <- rbind(muni.msa.2009.keep1,
                       muni.msa.2009.keep2)

## output this file for later use ##
save(muni.msa.2009,
     file = paste(output_path,
                  "003_msa_munis_2009.Rda",
                  sep=""))


## checks ##

nrow(muni.msa.2009) == length(unique(muni.msa.2009$GEOID))

## create weights ## 

munis.glm.2009 <- munis.final.2009 %>%
  select(GEOID,
         in.sample,
         totpop,
         hhs_oo,
         age_65a,
         age_18b,
         per_white,
         log_mpv,
         cgrad) %>%
  mutate(pop_p100t = totpop/100000) %>%
  drop_na()

wts.2009 <- glm(in.sample ~ pop_p100t + 
                            hhs_oo + 
                            age_65a +
                            age_18b + 
                            per_white + 
                            log_mpv + 
                            cgrad,
                            data = munis.glm.2009,
                            family = binomial(link = "logit"))

## check results ## 
summary(wts.2009)

## attach weights ##
munis.glm.2009$pA_all <- predict(wts.2009, type = "response")
munis.glm.2009$pA_actual_all <- (munis.glm.2009$in.sample * munis.glm.2009$pA_all) + 
  ((1 - munis.glm.2009$in.sample) * (1 - munis.glm.2009$pA_all))
munis.glm.2009$wt_all <- 1/munis.glm.2009$pA_all
munis.glm.2009$st_wt_all <- (sum(munis.glm.2009$in.sample)/nrow(munis.glm.2009))/munis.glm.2009$pA_all

munis.glm.final.2009 <- munis.glm.2009 %>%
  select(GEOID,
         wt_all,
         st_wt_all)

munis.final.wts.2009 <- stata.merge(munis.final.2009,
                                    munis.glm.final.2009,
                                    "GEOID")

## check merge ##
table(munis.final.wts.2009$merge.variable, useNA = "ifany")

## now, do the same for the metro sample ## 

munis.msa.glm.2009 <- muni.msa.2009 %>%
  select(cbsa10,
         GEOID,
         in.sample,
         totpop,
         hhs_oo,
         age_65a,
         age_18b,
         per_white,
         log_mpv,
         cgrad) %>%
  mutate(pop_p100t = totpop/100000) %>%
  drop_na()

wts.msa.2009 <- glm(in.sample ~ pop_p100t + 
                                hhs_oo + 
                                age_65a +
                                age_18b + 
                                per_white + 
                                log_mpv + 
                                cgrad,
                                data = munis.msa.glm.2009,
                                family = binomial(link = "logit"))

## check results ## 
summary(wts.msa.2009)

## attach weights ##
munis.msa.glm.2009$pA_msa <- predict(wts.msa.2009, type = "response")
munis.msa.glm.2009$pA_actual_msa <- (munis.msa.glm.2009$in.sample * munis.msa.glm.2009$pA_msa) + 
                                    ((1 - munis.msa.glm.2009$in.sample) * (1 - munis.msa.glm.2009$pA_msa))
munis.msa.glm.2009$wt_msa <- 1/munis.msa.glm.2009$pA_msa
munis.msa.glm.2009$st_wt_msa <- (sum(munis.msa.glm.2009$in.sample)/nrow(munis.msa.glm.2009))/munis.msa.glm.2009$pA_msa

munis.msa.glm.final.2009 <- munis.msa.glm.2009 %>%
  select(GEOID,
         wt_msa,
         st_wt_msa)

munis.msa.final.wts.2009 <- stata.merge(muni.msa.2009,
                                        munis.msa.glm.final.2009,
                                        "GEOID")

## check merge ##
table(munis.msa.final.wts.2009$merge.variable, useNA = "ifany")

munis.msa.final.wts1.2009 <- select(munis.msa.final.wts.2009, -merge.variable)

## now, do the same for individual metros with 10 or more responses ##

lmsas <- muni.msa.2009 %>%
  filter(in.sample == 1) %>%
  group_by(cbsa10) %>%
  summarize(n=n()) %>%
  filter(n >= 10)

## merge checks ## 
class(muni.msa.2009$cbsa10)
range(nchar(trim(muni.msa.2009$cbsa10)))

class(lmsas$cbsa10)
range(nchar(trim(lmsas$cbsa10)))

muni.lmsa.2009.m <- stata.merge(muni.msa.2009,
                                lmsas,
                                "cbsa10")

## check merge ##
table(muni.lmsa.2009.m$merge.variable, useNA = "ifany")

## keep matches (munis in large (n>=10) MSAs) ##
muni.lmsa.2009 <- muni.lmsa.2009.m %>%
  filter(merge.variable == 3) %>%
  select(-merge.variable)

lmsas <- unique(muni.lmsa.2009$cbsa10)

## now, create a function to loop through muni GLMs ##
pred.ind.msa.2009 <- function(geoid){
  
  ## subset to relevant MSA ##
  indata <- muni.lmsa.2009 %>%
    filter(cbsa10 == geoid) %>%
    select(cbsa10,
           GEOID,
           in.sample,
           totpop,
           hhs_oo,
           age_65a,
           age_18b,
           per_white,
           log_mpv,
           cgrad) %>%
    mutate(pop_p100t = totpop/100000) %>%
    drop_na()
  
  ## run the GLM ##
  wts.lmsa.2009 <- glm(in.sample ~ pop_p100t + 
                                   hhs_oo + 
                                   age_65a +
                                   age_18b + 
                                   per_white + 
                                   log_mpv + 
                                   cgrad,
                                   data = indata,
                                   family = binomial(link = "logit"))
  
  ## check results ## 
  summary(wts.lmsa.2009)
  
  eps <- 10 * .Machine$double.eps
  
  glm0.resids <- augment(wts.lmsa.2009) %>%
    mutate(p = 1 / (1 + exp(-.fitted)),
           warning = p > 1-eps)
  
  look <- arrange(glm0.resids, desc(.fitted)) %>%  
    select(2:5, p, warning) 
  
  look <- as.data.frame(look)
  
  print(head(look,5))
  
  ## attach weights ##
  indata$pA_lmsa <- predict(wts.lmsa.2009, type = "response")
  indata$pA_actual_lmsa <- (indata$in.sample * indata$pA_lmsa) + 
                           ((1 - indata$in.sample) * (1 - indata$pA_lmsa))
  indata$wt_lmsa <- 1/indata$pA_lmsa
  indata$st_wt_lmsa <- (sum(indata$in.sample)/nrow(indata))/indata$pA_lmsa
  
  findata <- indata %>%
    select(GEOID,
           cbsa10,
           wt_lmsa,
           st_wt_lmsa)
  
  return(findata)
  
}

## run the GLMs ##
ind.msa.weights <- lapply(lmsas, pred.ind.msa.2009)

## attach the weights ##
ind.msa.weights.data <- bind_rows(ind.msa.weights)

muni.msa.keep.2009 <- stata.merge(munis.msa.final.wts1.2009,
                                  ind.msa.weights.data,
                                  c("GEOID","cbsa10"))

## check merge ##
table(muni.msa.keep.2009$merge.variable, useNA = "ifany")


## restrict to sample ##
munis.keep.2009 <- munis.final.wts.2009 %>%
  filter(in.sample == 1) %>%
  select(-merge.variable) 

muni.msa.keep.final.2009 <- muni.msa.keep.2009 %>%
  filter(in.sample == 1) %>%
  select(-merge.variable)

## check against original weights ##

summary(munis.keep.2009$wt_all)
sd(munis.keep.2009$wt_all)
summary(munis.keep.2009$st_wt_all)
sd(munis.keep.2009$st_wt_all)
summary(wrld.2006.in$weight)

summary(muni.msa.keep.final.2009$wt_msa)
sd(muni.msa.keep.final.2009$wt_msa)
summary(muni.msa.keep.final.2009$st_wt_msa)
sd(muni.msa.keep.final.2009$st_wt_msa)
summary(wrld.2006.in$weight_metro)

summary(muni.msa.keep.final.2009$wt_lmsa)
sd(muni.msa.keep.final.2009$wt_lmsa, na.rm=T)
summary(muni.msa.keep.final.2009$st_wt_lmsa)
sd(muni.msa.keep.final.2009$st_wt_lmsa, na.rm=T)

plot(density(munis.keep.2009$wt_all, na.rm=T), 
     col = "blue",
     main = "Density of weights (all)",
     xlab = "Index value")
lines(density(wrld.2006.in$weight, na.rm=T), col = "red")
legend("topright",
       legend = c("Source data",
                  "WRLURI"),
       lty = c(1,1),
       col = c("blue","red"))

plot(density(muni.msa.keep.final.2009$wt_msa, na.rm=T), 
     col = "blue",
     main = "Density of weights (MSA)",
     xlab = "Index value")
lines(density(wrld.2006.in$weight_metro, na.rm=T), col = "red")
legend("topright",
       legend = c("Source data",
                  "WRLURI"),
       lty = c(1,1),
       col = c("blue","red"))

plot(density(munis.keep.2009$st_wt_all, na.rm=T), 
     col = "blue",
     main = "Density of standardized weights (all)",
     xlab = "Index value")

plot(density(muni.msa.keep.final.2009$st_wt_msa, na.rm=T), 
     col = "blue",
     main = "Density of standardized weights (MSA)",
     xlab = "Index value")

plot(density(muni.msa.keep.final.2009$wt_lmsa, na.rm=T), 
     col = "blue",
     main = "Density of standardized weights (all)",
     xlab = "Index value",
     xlim = c(0,80),
     ylim = c(0,0.4))

plot(density(muni.msa.keep.final.2009$st_wt_lmsa, na.rm=T), 
     col = "blue",
     main = "Density of standardized weights (MSA)",
     xlab = "Index value")


## all munis in MSAs density plot (fancier) ##
all.wts06a <- density(munis.keep.2009$wt_all, na.rm=T)
all.wts06b <- density(wrld.2006.in$weight, na.rm=T)

plot(all.wts06a, 
     col = "blue",
     main = "",
     xlab = "Inverse of predicted probability of selection",
     ylim = c(0, max(c(all.wts06a$y, all.wts06b$y))),
     xlim = c(min(c(all.wts06a$x, all.wts06b$x)),
              max(c(all.wts06a$x, all.wts06b$x))))
lines(all.wts06b, col = "red")
polygon(all.wts06a, col = rgb(0,0,1, alpha = 0.5))
polygon(all.wts06b, col = rgb(1,0,0,, alpha = 0.5))
legend("topright",
       legend = c("Updated",
                  "WRLURI"),
       lty = c(1,1),
       col = c("blue","red"))

## all munis in MSAs density plot (fancier) ##
all.wts06c <- density(muni.msa.keep.final.2009$wt_msa, na.rm=T)
all.wts06d <- density(wrld.2006.in$weight_metro, na.rm=T)

plot(all.wts06c, 
     col = "blue",
     main = "",
     xlab = "Inverse of predicted probability of selection",
     ylim = c(0, max(c(all.wts06c$y, all.wts06d$y))),
     xlim = c(min(c(all.wts06c$x, all.wts06d$x)),
              max(c(all.wts06c$x, all.wts06d$x))))
lines(all.wts06d, col = "red")
polygon(all.wts06c, col = rgb(0,0,1, alpha = 0.5))
polygon(all.wts06d, col = rgb(1,0,0,, alpha = 0.5))
legend("topright",
       legend = c("Updated",
                  "WRLURI"),
       lty = c(1,1),
       col = c("blue","red"))

## export weights ## 

wrld.nllus.wts.all.2006 <- munis.keep.2009 %>%
  select(GEOID, 
         wt_all,
         st_wt_all) %>%
  rename(wt_all_2006 = wt_all,
         st_wt_all_2006 = st_wt_all)

save(wrld.nllus.wts.all.2006,
     file = paste(output_path,
                  "003_wrld_nllus_wts_all_2006.Rda",
                  sep=""))

wrld.nllus.wts.msa.2006 <- muni.msa.keep.final.2009 %>%
  select(GEOID, 
         wt_msa,
         st_wt_msa,
         wt_lmsa,
         st_wt_lmsa) %>%
  rename(wt_msa_2006 = wt_msa,
         st_wt_msa_2006 = st_wt_msa,
         wt_lmsa_2006 = wt_lmsa,
         st_wt_lmsa_2006 = st_wt_lmsa)

save(wrld.nllus.wts.msa.2006,
     file = paste(output_path,
                  "003_wrld_nllus_wts_msa_2006.Rda",
                  sep=""))

###############
## 2015-2019 ##
###############

## get ACS data ##

## View 2015-2019 Census variables ##
v2019 <- load_variables(2019, "acs5", cache=TRUE)

## initialize lists to store data frames ##
state.places.2019 <- list() 
state.cosubs.2019 <- list()
state.places.2019.area <- list()
state.cosubs.2019.area <- list()

## initialize counter ## 
state.counter <- 1

## start the loop ##
for (st in states){
  
  ## get data for CDPs ##
  cdp2019 <- get_acs(geography = "place", 
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
                                   race_tot = "B03002_001",
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
                     state = st, 
                     survey = "acs5",
                     output = "wide",
                     year = 2019)
  
  ## get land area info ##
  cdp2019.area <- places(state=st,
                         year = 2019,
                         cb=TRUE)
  
  
  ## add state identifying variable ##
  cdp2019$state <- st
  cdp2019.area$state <- st
  
  ## store the data frame in the list ## 
  state.places.2019[[state.counter]] <- cdp2019
  state.places.2019.area[[state.counter]] <- cdp2019.area
  
  cosub2019 <- get_acs(geography = "county subdivision", 
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
                                     race_tot = "B03002_001",
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
                       state = st, 
                       survey = "acs5",
                       output = "wide",
                       year = 2019)
  
  ## get land area info ##
  cosub2019.area <- county_subdivisions(state=st,
                                     year = 2019,
                                     cb=TRUE)
  
  ## add state identifying variable ##
  cosub2019$state <- st
  cosub2019.area$state <- st
  
  ## store the data frame in the list ## 
  state.cosubs.2019[[state.counter]] <- cosub2019
  state.cosubs.2019.area[[state.counter]] <- cosub2019.area
  
  ## increase interval by 1 ## 
  state.counter <- state.counter + 1
  
}

## combine all the data ## 

all.cdps.2019 <- bind_rows(state.places.2019)
all.cosubs.2019 <- bind_rows(state.cosubs.2019)
all.cdps.2019.area <- bind_rows(state.places.2019.area)
all.cosubs.2019.area <- bind_rows(state.cosubs.2019.area)


## attach land area values - places ##

all.cdps.2019.area.f <- all.cdps.2019.area %>%
  select(GEOID, 
         ALAND,
         AWATER) %>%
  mutate(total_area = ALAND + AWATER)

st_geometry(all.cdps.2019.area.f) <- NULL
class(all.cdps.2019.area.f)

## fix Louisville GEOID ##
all.cdps.2019.final.m <- stata.merge(all.cdps.2019,
                                     all.cdps.2019.area.f,
                                     "GEOID")

## check merge ##
table(all.cdps.2019.final.m$merge.variable, useNA = "ifany")

## keep matches ##
## the one non-matching obs is for Louisville, which is duplicated in the area data ##
all.cdps.2019.final <- all.cdps.2019.final.m %>%
  filter(merge.variable == 3) %>%
  select(-merge.variable)


## attach land area values - cosubs ##
all.cosubs.2019.area.f <- all.cosubs.2019.area %>%
  select(GEOID, 
         ALAND,
         AWATER) %>%
  mutate(total_area = ALAND + AWATER)

st_geometry(all.cosubs.2019.area.f) <- NULL
class(all.cosubs.2019.area.f)

all.cosubs.2019.final.m <- stata.merge(all.cosubs.2019,
                                       all.cosubs.2019.area.f,
                                       "GEOID")

## check merge ##
table(all.cosubs.2019.final.m$merge.variable, useNA = "ifany")

## keep merge.variable values 1,3 ##
all.cosubs.2019.final <- all.cosubs.2019.final.m %>%
  filter(merge.variable %in% c(1,3)) %>%
  select(-merge.variable)


## reformat the cosub dataframe ## 

cosub.rf.2019 <- all.cosubs.2019.final %>%
  filter(!grepl('CCD', NAME)) %>%
  mutate(geoid.f = paste(substr(GEOID,1,2),
                         substr(GEOID,6,12),
                         sep=""))

## create merge variable on cdps dataframe ##
all.cdps.2019.final$geoid.f <- all.cdps.2019.final$GEOID

## check for overlapping munis ## 

nrow(all.cdps.2019.final) == length(unique(all.cdps.2019.final$geoid.f))
class(all.cdps.2019.final$geoid.f)
range(nchar(trim(all.cdps.2019.final$geoid.f)))

nrow(cosub.rf.2019) == length(unique(cosub.rf.2019$geoid.f))
class(cosub.rf.2019$geoid.f)
range(nchar(trim(cosub.rf.2019$geoid.f)))


overlap.2019 <- stata.merge(all.cdps.2019.final,
                            cosub.rf.2019,
                            "geoid.f")

## check overlap ## 
table(overlap.2019$merge.variable)

## create final muni dataframe ##

## for the non-matches, we can just drop the variables of the non-matching obs ##

munis.fin1.2019 <- overlap.2019 %>%
  filter(merge.variable ==1) %>%
  select(-ends_with(".y"),
         -merge.variable)

names(munis.fin1.2019) <- sub(".x", "", names(munis.fin1.2019))

munis.fin2.2019 <- overlap.2019 %>%
  filter(merge.variable ==2) %>%
  select(-ends_with(".x"),
         -merge.variable)

names(munis.fin2.2019) <- sub(".y", "", names(munis.fin2.2019))

## the matches are more complicated ##
## the issue here is that place codes have no county code component ##
## so there will be duplicates when merging with reduced cosub codes ##
## the solution will be to deal with the duplicates manually ##

## collect cosubs with duplicate GEOIDs ##
munis.fin3.2019.v1 <- overlap.2019 %>%
  filter(merge.variable ==3) %>%
  select(-ends_with(".x"),
         -merge.variable)

## collect the corresponding duplicates ##
munis.fin3.2019.v2 <- overlap.2019 %>%
  filter(merge.variable ==3) %>%
  select(-ends_with(".y"),
         -merge.variable)

## make the vars conform ##
names(munis.fin3.2019.v1) <- sub(".y", "", names(munis.fin3.2019.v1))
names(munis.fin3.2019.v2) <- sub(".x", "", names(munis.fin3.2019.v2))

## stack the duplicates ##
munis.fin3.2019.stacked <- rbind(munis.fin3.2019.v1,
                                 munis.fin3.2019.v2)

## remove true duplicate munis ## 
munis.fin3.dd.2019 <- unique(munis.fin3.2019.stacked)

## now, fix the remaining duplicates ##
## case 1: same exact places/cosubs, just listed both as places and county subs ##
munis.fin3.gr1.2019 <- munis.fin3.dd.2019 %>% 
  group_by_at(vars(-c(GEOID, NAME))) %>% 
  filter(n() > 1) %>%
  summarize_all(list(first)) %>%
  select(geoid.f,
         GEOID,
         NAME,
         everything())

munis.fin3.gr1.2019 <- as.data.frame(munis.fin3.gr1.2019)

## case 2: different places/cosubs, but same reduced FIPS codes as other cosubs ##
## case 3: places/cosubs that extend into multiple counties ##

munis.fin3.gr2.2019 <- munis.fin3.dd.2019 %>%
  filter(geoid.f %notin% munis.fin3.gr1.2019$geoid.f)

fin3.2.s1a.2019 <- munis.fin3.gr2.2019 %>%
  filter(nchar(GEOID) == 10) %>%
  group_by(geoid.f) %>%
  summarize_if(is.numeric, list(sum))

fin3.2.s1b.2019 <- munis.fin3.gr2.2019 %>%
  filter(nchar(GEOID) == 10) %>%
  group_by(geoid.f) %>%
  summarize_if(is.character, list(first))

fin3.2.s1.2019 <- inner_join(fin3.2.s1a.2019,
                             fin3.2.s1b.2019,
                             "geoid.f")

fin3.2.s1.rf.2019 <- fin3.2.s1.2019 %>%
  select(geoid.f,
         GEOID,
         NAME, 
         everything())

fin3.2.s2.2019 <- munis.fin3.gr2.2019 %>%
  filter(nchar(GEOID) < 10) 

fin3.2.s3.2019 <- rbind(fin3.2.s1.rf.2019,
                        fin3.2.s2.2019)

fin3.2.s4.2019 <- fin3.2.s3.2019 %>%
  group_by(geoid.f, totpopE) %>%
  summarize_all(list(last))

## need to check these manually ##
fin3.mcheck.2019 <- fin3.2.s4.2019 %>%
  group_by(geoid.f) %>%
  summarize(n = n()) %>%
  filter(n>1)


## manual fixes ##
munis.fin1.2019.final <- munis.fin1.2019

munis.fin2.2019.final <- munis.fin2.2019 %>%
  filter(geoid.f %notin% c("3192103","3193203","3918010",
                           "3929176","3979730","3983349"))

munis.fin3a.2019.final <- fin3.2.s4.2019 %>%
  filter(GEOID %notin% c("1803551876","1801184014","3114134230",
                         "3100348935","3915101420","3904518000",
                         "3914728014","3911729162","3901749840",
                         "3906171892","3910978470","3904379716",
                         "3904983342"))


munis.fin3a.2019.final <- as.data.frame(munis.fin3a.2019.final)

munis.fin3b.2019.final <- munis.fin3.gr1.2019


munis.fin3.2019.final <- rbind(munis.fin3a.2019.final,
                               munis.fin3b.2019.final)

class(munis.fin3.2019.final)

munis.fin3.2019.final <- as.data.frame(munis.fin3.2019.final)

## combine data for final data frame ## 
munis.fin.2019 <- rbind(munis.fin1.2019.final,
                        munis.fin2.2019.final,
                        munis.fin3.2019.final)

## clean data ## 

munis.fin.cl.2019 <- munis.fin.2019 %>%
  filter(!grepl('precinct', NAME) & totpopE >0) %>%
  mutate(#GEOID = geoid.f,
    totpop = totpopE,
    tothhs = tothhsE,
    totfams = totfamsE,
    hhs_oo = hhs_ooE/tothhs,
    age_65a = (age_male_65to66E + age_male_67to69E +
               age_male_70to74E + age_male_75to79E +
               age_male_80to84E + age_male_85aE + 
               age_female_65to66E + age_female_67to69E +
               age_female_70to74E + age_female_75to79E +
               age_female_80to84E + age_female_85aE)/age_totalE,
    age_18b = (age_male_5uE + age_male_5to9E +
               age_male_10to14E + age_male_15to17E +
               age_female_5uE + age_female_5to9E +
               age_female_10to14E + age_female_15to17E)/age_totalE,
    median_pvalue = median_pvalueE,
    median_hhld_inc = median_hhld_incE,
    median_fam_inc = median_fam_incE,
    hhld_pov_rt = hhlds_povE/tothhs,
    fam_pov_rt = fams_povE/totfams,
    log_mpv = log(median_pvalue),
    cgrad = (ed_male_baE + ed_male_maE + 
             ed_male_pdE + ed_male_docE + 
             ed_female_baE + ed_female_maE + 
             ed_female_pdE + ed_female_docE)/ed_totalE,
    pop_latinx = pop_h_aianE + pop_h_asianE + pop_h_blackE + 
                 pop_h_nhpiE + pop_h_otherE + pop_h_whiteE,
    pop_latinx_multi = pop_h_multiE,
    pop_both_multi = pop_nh_multiE + pop_latinx_multi,
    per_asian = case_when(totpop != 0 ~ pop_nh_asianE/totpop,
                          totpop == 0 ~ 0),
    per_black = case_when(totpop != 0 ~ pop_nh_blackE/totpop,
                          totpop == 0 ~ 0),
    per_latinx = case_when(totpop != 0 ~ pop_latinx/totpop,
                           totpop == 0 ~ 0),
    per_white = case_when(totpop != 0 ~ pop_nh_whiteE/totpop,
                          totpop == 0 ~ 0),
    per_AIAN = case_when(totpop != 0 ~ pop_nh_aianE/totpop, 
                         totpop == 0 ~ 0),
    per_other = case_when(totpop != 0 ~ (pop_nh_otherE + pop_nh_nhpiE + pop_both_multi)/totpop, 
                          totpop == 0 ~ 0),
    log_asian = case_when(pop_nh_asianE != 0 ~ log(1/per_asian),
                          pop_nh_asianE == 0 ~ 0),
    log_black = case_when(pop_nh_blackE != 0 ~ log(1/per_black),
                          pop_nh_blackE == 0 ~ 0),
    log_latinx = case_when(pop_latinx != 0 ~ log(1/per_latinx),
                           pop_latinx == 0 ~ 0),
    log_white = case_when(pop_nh_whiteE != 0 ~ log(1/per_white),
                          pop_nh_whiteE == 0 ~ 0),
    log_AIAN = case_when(pop_nh_aianE != 0 ~ log(1/per_AIAN),
                         pop_nh_aianE == 0 ~ 0),
    log_other = case_when(pop_nh_otherE + pop_nh_nhpiE + pop_both_multi != 0 ~ log(1/per_other),
                          pop_nh_otherE + pop_nh_nhpiE + pop_both_multi == 0 ~ 0),
    entropy = per_asian*log_asian + 
              per_black*log_black + 
              per_latinx*log_latinx + 
              per_white*log_white +
              per_AIAN*log_AIAN +
              per_other*log_other,
    land_area_sqmeters = ALAND,
    land_area_sqmiles = ALAND/2589988,
    pop_density = totpop/land_area_sqmiles) %>%
  select(GEOID,
         geoid.f,
         NAME,
         totpop,
         tothhs,
         totfams,
         hhs_oo,
         age_65a,
         age_18b,
         per_white,
         log_mpv,
         median_pvalue,
         median_hhld_inc,
         median_fam_inc,
         hhld_pov_rt,
         fam_pov_rt,
         cgrad,
         entropy,
         land_area_sqmiles,
         pop_density) %>%
  rename(GEOID_full = GEOID,
         GEOID = geoid.f)

## prep for merge ##
nzlu.2019.final.fm <- nzlu.2019.final %>%
  ungroup() %>%
  select(GEOID)

## create sample indicator ## 

nrow(munis.fin.cl.2019) == length(unique(munis.fin.cl.2019$GEOID))
class(munis.fin.cl.2019$GEOID)
range(nchar(trim(munis.fin.cl.2019$GEOID)))

munis.cb.2019 <- stata.merge(munis.fin.cl.2019,
                             nzlu.2019.final.fm,
                             "GEOID")

## check merge ##
table(munis.cb.2019$merge.variable)

## final munis ## 

munis.final.2019 <- munis.cb.2019 %>%
  mutate(in.sample = case_when(
    merge.variable == 3 ~ 1, 
    merge.variable %in% c(1,2) ~ 0),
    region = case_when(substr(GEOID,1,2) %in% c("09","23","25","44","50","34","36","42") ~ "NE",
                       substr(GEOID,1,2) %in% c("17","18","26","39","55","19","20","27","29","31","38","46") ~ "MW",
                       substr(GEOID,1,2) %in% c("10","12","13","24","37","45","51","54","01","21","28","47","05","22","40","48") ~ "SO",
                       TRUE ~ "WE")) %>%
  select(-merge.variable) %>%
  filter((!grepl("CDP", NAME)) |
           (grepl("CDP", NAME) & substr(GEOID,1,2) == "15") |
           (GEOID %in% c("0286490", "0260310")))

## check ##
table(munis.final.2019$in.sample)

## how much of the population does the final sample represent? ##

sum(munis.final.2019$totpop[munis.final.2019$in.sample==1], na.rm=T)/sum(munis.final.2019$totpop, na.rm=T)

## check region var ##

table(munis.final.2019$region, useNA = "ifany")
class(munis.final.2019$region)

## rework as factor ## 
munis.final.2019$region <- factor(munis.final.2019$region,
                                  levels = c("NE","MW","SO","WE"))

table(munis.final.2019$region, useNA = "ifany")
class(munis.final.2019$region)
levels(munis.final.2019$region)


## checks ## 

summary(munis.final.2019)


## save data for all munis ##
save(munis.final.2019,
     file = paste(output_path,
                  "003_allmunis_2019.Rda",
                  sep=""))


## create msa sample file ##

## merge checks ## 
nrow(munis.final.2019) == length(unique(munis.final.2019$GEOID))
class(munis.final.2019$GEOID)
range(nchar(trim(munis.final.2009$GEOID)))

nrow(ptm.2010.rd) == length(unique(ptm.2010.rd$GEOID))
class(ptm.2010.rd$GEOID)
range(nchar(trim(ptm.2010.rd$GEOID)))


## merge data frames ## 
muni.msa.2019.m1 <- stata.merge(munis.final.2019,
                                ptm.2010.rd,
                                "GEOID")

## check merge ## 
table(muni.msa.2019.m1$merge.variable)

## output non-matches eligible for match with county subs ##
no.msa.2019.m1 <- muni.msa.2019.m1 %>%
  filter(merge.variable ==1) %>%
  select(-placefp,
         -stab,
         -placenm,
         -cbsa10,
         -cbsaname10,
         -pop10,
         -afact,
         -state,
         -merge.variable)

## keep matches ## 
muni.msa.2019.keep1 <- muni.msa.2019.m1 %>%
  mutate(afact_num = as.numeric(afact)) %>%
  filter(merge.variable ==3) %>%
  group_by(GEOID) %>%
  slice(which.max(afact_num)) %>%
  select(-placefp,
         -stab,
         -placenm,
         -pop10,
         -afact,
         -merge.variable)

## check for dups ## 
## these are places that span multiple MSAs ##
muni.msa.2019.dupcheck1 <- muni.msa.2019.keep1 %>%
  group_by(GEOID) %>%
  summarize(n=n()) %>%
  filter(n>1)

## get rid of duplicates ## 

#muni.msa.2019.keep1.rd <- muni.msa.2019.keep1 %>%
  #filter(!(GEOID == "2910828" & cbsa10 == "41140"))

## check ##
nrow(muni.msa.2019.keep1) == length(unique(muni.msa.2019.keep1$GEOID))

## now, county subs ## 

## merge checks ##
nrow(cstm.2010.rd) == length(unique(cstm.2010.rd$GEOID))
class(cstm.2010.rd$GEOID)
range(nchar(trim(cstm.2010.rd$GEOID)))

nrow(no.msa.2019.m1) == length(unique(no.msa.2019.m1$GEOID))
class(no.msa.2019.m1$GEOID)
range(nchar(trim(no.msa.2019.m1$GEOID)))

## merge data frames ## 
muni.msa.2019.m2 <- stata.merge(no.msa.2019.m1,
                                cstm.2010.rd,
                                "GEOID")

## check merge ##
table(muni.msa.2019.m2$merge.variable)

## keep matches ## 
muni.msa.2019.keep2 <- muni.msa.2019.m2 %>%
  mutate(afact_num = as.numeric(afact)) %>%
  filter(merge.variable ==3) %>%
  group_by(GEOID) %>%
  slice(which.max(afact_num)) %>%
  select(-county,
         -cousubfp,
         -cntyname,
         -cousubnm,
         -pop10,
         -afact,
         -merge.variable)

## check for dups ## 
## these are places that span multiple MSAs ##
muni.msa.2019.dupcheck2 <- muni.msa.2019.keep2 %>%
  group_by(GEOID) %>%
  summarize(n=n()) %>%
  filter(n>1)

## append the two matched dataframes ##

muni.msa.2019 <- rbind(muni.msa.2019.keep1,
                       muni.msa.2019.keep2)

## checks ##

nrow(muni.msa.2019) == length(unique(muni.msa.2019$GEOID))

## output this file for later use ##
save(muni.msa.2019,
     file = paste(output_path,
                  "003_msa_munis_2019.Rda",
                  sep=""))


## create weights ## 

munis.glm.2019 <- munis.final.2019 %>%
  select(GEOID,
         in.sample,
         totpop,
         hhs_oo,
         age_65a,
         age_18b,
         per_white,
         log_mpv,
         cgrad,
         region) %>%
  mutate(pop_p100t = totpop/100000) %>%
  drop_na()

wts.2019 <- glm(in.sample ~ pop_p100t + 
                            hhs_oo + 
                            age_65a +
                            age_18b + 
                            per_white + 
                            log_mpv + 
                            cgrad + 
                            region,
                            data = munis.glm.2019,
                            family = binomial(link = "logit"))

## check results ## 
summary(wts.2019)

## attach weights ##
munis.glm.2019$pA_all <- predict(wts.2019, type = "response")
munis.glm.2019$pA_actual_all <- (munis.glm.2019$in.sample * munis.glm.2019$pA_all) + 
  ((1 - munis.glm.2019$in.sample) * (1 - munis.glm.2019$pA_all))
munis.glm.2019$wt_all <- 1/munis.glm.2019$pA_all
munis.glm.2019$st_wt_all <- (sum(munis.glm.2019$in.sample)/nrow(munis.glm.2019))/munis.glm.2019$pA_all

munis.glm.final.2019 <- munis.glm.2019 %>%
  select(GEOID,
         wt_all,
         st_wt_all)

munis.final.wts.2019 <- stata.merge(munis.final.2019,
                                    munis.glm.final.2019,
                                    "GEOID")

## check merge ##
table(munis.final.wts.2019$merge.variable, useNA = "ifany")

## now, do the same for the metro sample ## 

munis.msa.glm.2019 <- muni.msa.2019 %>%
  select(cbsa10,
         GEOID,
         in.sample,
         totpop,
         hhs_oo,
         age_65a,
         age_18b,
         per_white,
         log_mpv,
         cgrad,
         region) %>%
  mutate(pop_p100t = totpop/100000) %>%
  drop_na()

wts.msa.2019 <- glm(in.sample ~ pop_p100t + 
                                hhs_oo + 
                                age_65a +
                                age_18b + 
                                per_white + 
                                log_mpv + 
                                cgrad + 
                                region,
                    data = munis.msa.glm.2019,
                    family = binomial(link = "logit"))

## check results ## 
summary(wts.msa.2019)

## attach weights ##
munis.msa.glm.2019$pA_msa <- predict(wts.msa.2019, type = "response")
munis.msa.glm.2019$pA_actual_msa <- (munis.msa.glm.2019$in.sample * munis.msa.glm.2019$pA_msa) + 
  ((1 - munis.msa.glm.2019$in.sample) * (1 - munis.msa.glm.2019$pA_msa))
munis.msa.glm.2019$wt_msa <- 1/munis.msa.glm.2019$pA_msa
munis.msa.glm.2019$st_wt_msa <- (sum(munis.msa.glm.2019$in.sample)/nrow(munis.msa.glm.2019))/munis.msa.glm.2019$pA_msa

munis.msa.glm.final.2019 <- munis.msa.glm.2019 %>%
  select(GEOID,
         wt_msa,
         st_wt_msa)

munis.msa.final.wts.2019 <- stata.merge(muni.msa.2019,
                                        munis.msa.glm.final.2019,
                                        "GEOID")

## check merge ##
table(munis.msa.final.wts.2019$merge.variable, useNA = "ifany")

munis.msa.final.wts1.2019 <- select(munis.msa.final.wts.2019, -merge.variable)

## now, do the same for individual metros with 10 or more responses ##

lmsas.2019 <- muni.msa.2019 %>%
  filter(in.sample == 1) %>%
  group_by(cbsa10) %>%
  summarize(n=n()) %>%
  filter(n >= 10)

## merge checks ## 
class(muni.msa.2019$cbsa10)
range(nchar(trim(muni.msa.2019$cbsa10)))

class(lmsas.2019$cbsa10)
range(nchar(trim(lmsas.2019$cbsa10)))

muni.lmsa.2019.m <- stata.merge(muni.msa.2019,
                                lmsas.2019,
                                "cbsa10")

## check merge ##
table(muni.lmsa.2019.m$merge.variable, useNA = "ifany")

## keep matches (munis in large (n>=10) MSAs) ##
muni.lmsa.2019 <- muni.lmsa.2019.m %>%
  filter(merge.variable == 3) %>%
  select(-merge.variable)

lmsas.2019 <- unique(muni.lmsa.2019$cbsa10)

## now, create a function to loop through muni GLMs ##
pred.ind.msa.2019 <- function(geoid){
  
  print(geoid)
  
  ## subset to relevant MSA ##
  indata <- muni.lmsa.2019 %>%
    filter(cbsa10 == geoid) %>%
    select(cbsa10,
           GEOID,
           in.sample,
           totpop,
           hhs_oo,
           age_65a,
           age_18b,
           per_white,
           log_mpv,
           cgrad) %>%
    mutate(pop_p100t = totpop/100000) %>%
    drop_na()
  
  ## run the GLM ##
  wts.lmsa.2019 <- glm(in.sample ~ pop_p100t + 
                                   hhs_oo + 
                                   age_65a +
                                   age_18b + 
                                   per_white + 
                                   log_mpv + 
                                   cgrad,
                                   data = indata,
                                   family = binomial(link = "logit"))
  
  ## check results ## 
  summary(wts.lmsa.2019)
  
  eps <- 10 * .Machine$double.eps
  
  glm0.resids <- augment(wts.lmsa.2019) %>%
    mutate(p = 1 / (1 + exp(-.fitted)),
           warning = p > 1-eps)
  
  look <- arrange(glm0.resids, desc(.fitted)) %>%  
    select(2:5, p, warning) 
  
  look <- as.data.frame(look)
  
  print(head(look,5))
  
  ## attach weights ##
  indata$pA_lmsa <- predict(wts.lmsa.2019, type = "response")
  indata$pA_actual_lmsa <- (indata$in.sample * indata$pA_lmsa) + 
    ((1 - indata$in.sample) * (1 - indata$pA_lmsa))
  indata$wt_lmsa <- 1/indata$pA_lmsa
  indata$st_wt_lmsa <- (sum(indata$in.sample)/nrow(indata))/indata$pA_lmsa
  
  findata <- indata %>%
    select(GEOID,
           cbsa10,
           wt_lmsa,
           st_wt_lmsa)
  
  return(findata)
  
}

## run the GLMs ##
ind.msa.weights.2019 <- lapply(lmsas.2019, pred.ind.msa.2019)

## attach the weights ##
ind.msa.weights.data.2019 <- bind_rows(ind.msa.weights.2019)

muni.msa.keep.2019 <- stata.merge(munis.msa.final.wts1.2019,
                                  ind.msa.weights.data.2019,
                                  c("GEOID","cbsa10"))

## check merge ##
table(muni.msa.keep.2019$merge.variable, useNA = "ifany")


## restrict to sample ##
munis.keep.2019 <- munis.final.wts.2019 %>%
  filter(in.sample == 1) %>%
  select(-merge.variable) 

muni.msa.keep.final.2019 <- muni.msa.keep.2019 %>%
  filter(in.sample == 1) %>%
  select(-merge.variable)

## check against original weights ##

summary(munis.keep.2019$wt_all)
sd(munis.keep.2019$wt_all)
summary(munis.keep.2019$st_wt_all)
sd(munis.keep.2019$st_wt_all)

summary(muni.msa.keep.final.2019$wt_msa)
sd(muni.msa.keep.final.2019$wt_msa)
summary(muni.msa.keep.final.2019$st_wt_msa)
sd(muni.msa.keep.final.2019$st_wt_msa)

summary(muni.msa.keep.final.2019$wt_lmsa)
sd(muni.msa.keep.final.2019$wt_lmsa, na.rm=T)
summary(muni.msa.keep.final.2019$st_wt_lmsa)
sd(muni.msa.keep.final.2019$st_wt_lmsa, na.rm=T)



plot(density(munis.keep.2019$wt_all, na.rm=T), 
     col = "blue",
     main = "Density of weights (all)",
     xlab = "Index value")
lines(density(wrld.2018.in$weight_full, na.rm=T), col = "red")
legend("topright",
       legend = c("Source data",
                  "WRLURI"),
       lty = c(1,1),
       col = c("blue","red"))

## all munis density plot (fancier) ##
nzlu.d1 <- density(munis.keep.2019$wt_all, na.rm=T)
wrld.d1 <- density(wrld.2018.in$weight_full, na.rm=T)

plot(nzlu.d1, 
     col = "blue",
     main = "",
     xlab = "Inverse of predicted probability of selection",
     ylim = c(0, max(c(nzlu.d1$y, wrld.d1$y))),
     xlim = c(min(c(nzlu.d1$x, wrld.d1$x)),
              max(c(nzlu.d1$x, wrld.d1$x))))
lines(wrld.d1, col = "red")
polygon(nzlu.d1, col = rgb(0,0,1, alpha = 0.5))
polygon(wrld.d1, col = rgb(1,0,0,, alpha = 0.5))
legend("topright",
       legend = c("NZLU",
                  "WRLURI"),
       lty = c(1,1),
       col = c("blue","red"))

plot(density(muni.msa.keep.final.2019$wt_msa, na.rm=T), 
     col = "blue",
     main = "Density of weights (MSA)",
     xlab = "Index value")
lines(density(wrld.2018.in$weight_metro, na.rm=T), col = "red")
legend("topright",
       legend = c("Source data",
                  "WRLURI"),
       lty = c(1,1),
       col = c("blue","red"))

## all munis in MSAs density plot (fancier) ##
nzlu.d2 <- density(muni.msa.keep.final.2019$wt_msa, na.rm=T)
wrld.d2 <- density(wrld.2018.in$weight_metro, na.rm=T)

plot(nzlu.d2, 
     col = "blue",
     main = "",
     xlab = "Inverse of predicted probability of selection",
     ylim = c(0, max(c(nzlu.d2$y, wrld.d2$y))),
     xlim = c(min(c(nzlu.d2$x, wrld.d2$x)),
              max(c(nzlu.d2$x, wrld.d2$x))))
lines(wrld.d2, col = "red")
polygon(nzlu.d2, col = rgb(0,0,1, alpha = 0.5))
polygon(wrld.d2, col = rgb(1,0,0,, alpha = 0.5))
legend("topright",
       legend = c("NZLU",
                  "WRLURI"),
       lty = c(1,1),
       col = c("blue","red"))

plot(density(munis.keep.2019$st_wt_all, na.rm=T), 
     col = "blue",
     main = "Density of standardized weights (all)",
     xlab = "Index value")

plot(density(muni.msa.keep.final.2019$st_wt_msa, na.rm=T), 
     col = "blue",
     main = "Density of standardized weights (MSA)",
     xlab = "Index value")

plot(density(muni.msa.keep.final.2019$wt_lmsa, na.rm=T), 
     col = "blue",
     main = "Density of standardized weights (MSA)",
     xlab = "Index value")

plot(density(muni.msa.keep.final.2019$st_wt_lmsa, na.rm=T), 
     col = "blue",
     main = "Density of standardized weights (MSA)",
     xlab = "Index value")

## stargazer ##

stargazer(wts.2009,
          wts.msa.2009,
          wts.2019,
          wts.msa.2019,
          type="html",
          dep.var.labels=c("In Sample"),
          out= paste(output_path,
                     "003_glm.html",
                     sep=""))

## export weights ## 

nzlu.wts.all.2019 <- munis.keep.2019 %>%
  select(GEOID, 
         wt_all,
         st_wt_all) %>%
  rename(wt_all_2019 = wt_all,
         st_wt_all_2019 = st_wt_all)

save(nzlu.wts.all.2019,
     file = paste(output_path,
                  "003_nzlu_wts_all_2019.Rda",
                  sep=""))

nzlu.wts.msa.2019 <- muni.msa.keep.final.2019 %>%
  select(GEOID, 
         wt_msa,
         st_wt_msa,
         wt_lmsa,
         st_wt_lmsa) %>%
  rename(wt_msa_2019 = wt_msa,
         st_wt_msa_2019 = st_wt_msa,
         wt_lmsa_2019 = wt_lmsa,
         st_wt_lmsa_2019 = st_wt_lmsa)

save(nzlu.wts.msa.2019,
     file = paste(output_path,
                  "003_nzlu_wts_msa_2019.Rda",
                  sep=""))


## END OF PROGRAM ##

#sink()



