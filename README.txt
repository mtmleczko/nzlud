#####################################
NATIONAL ZONING AND LAND USE DATABASE
#####################################

DATE THIS README WAS LAST UPDATED: 03/24/2023

PROJECT DESCRIPTION: We created the National Zoning and Land Use Database (NZLUD) to provide national zoning and land use data for the 2019-2022 time period. We supply our source code to enable timely access to publicly available zoning information. Users can rerun our code at regular intervals to create panel zoning data moving forward. Users can also expand to additional municipalities or additional zoning and land use measures not currently captured by our process. The intent is for this code to further automate the process of building national zoning and land use information in an open source way. 

The entire process is currently encoded in parse_zoning_txt.py, a Python program that creates the NZLUD via 
a series of nested functions (see the program for documentation). The process employs basic natural language 
processing (NLP) techniques, primarily through a series of regular expression searches. Users may build upon our process, for instance, by identify efficiency gains and/or employing more complex NLP techniques, both of which could potentially include more zoning and land use measures to the output. Adding geospatial information to the process could be a worthwhile next step. 

While our process provides a more efficient method of extracting selected zoning and land use information from the text of the regulations, it still requires the manual collection of the input text data, which is a time-consuming process. We downloaded the input text data from a series of municipal code vendors (see Online Only Supplement for this list) as well as directly from municipal websites. In most cases, we were unable to utilize web scraping due to the idiosyncratic ways that these regulations are stored, even within the same vendor. Moreover, we recommend checking that the downloaded codes contain the relevant information. 
			   
For instance, municipal codes will frequently contain zoning/land use/development chapters/sections/titles in their table of contents, but the chapters/sections/titles themselves may be blank or only contain references or links to the actual zoning/land use/development codes. Without this check, users may inadvertently include text data that does not contain any relevant zoning or land use information. Similarly, we recommend downloading the entire set of municipal codes when possible to ensure that all relevant information to zoning 				   and land use is captured in the input text data.  

TIPS FOR DEBUGGING:  As it stands, the parse_zoning_txt.py program and its constituent functions are written as a series of many loops. Oftentimes, the most straightforward way of resolving an error in the code or determining how certain values are output is to print values along the sequence of loops to determine how the code is processing particular input text data. Some examples of this can be seen throughout the source code. Similarly, the code currently displays the filepath of each input file as it loops through all input files. The user is recommended to leave this as is since it helps determine which file is encountering an issue or error. The same logic applies to printing particular values or signposts for particular functions or portions of functions. 

NOTE ABOUT OUTPUT:   As of right now, the code in the main program that creates the output zoning data takes all input files and creates one output .xls file. Depending on the amount of input files, the user may want to parallelize the code to speed up the process. We ultimately implemented this (which is why our zoning output is a series of .xls files), but we retained the non-parallel approach in the publicly available program for simplicity's sake. 

NOTE ABOUT MSA coverage: Because we replicate the sample from the 2006 Wharton Residential Land Use Regulatory Index database (Gyourko, Saiz, and Summers 2008), which was constructed from a survey of municipalities across 323 MSAs with oftentimes low response rates, many MSAs in our sample are missing data for a large proportion of their municipalities. Consequently, since we create the MSA-level files by aggregating the municipal-level data, users are cautioned to consider MSA-level coverage (what proportion of municipalities in a given MSA are present in the NZLUD) when interpreting and using the MSA-level data. See the msa_coverage_rates.csv file for more information.
			   
AUTHORS: Matt Mleczko, Scott Overbey, Matt Desmond

CONTACT: mmleczko@princeton.edu 

LINK TO PAPER AND ONLINE SUPPLEMENT: https://journals.sagepub.com/doi/10.1177/00420980231156352

FILES: 
- parse_zoning_txt.py: Python program that creates the NZLUD by parsing the input zoning and land use text data and outputing an Excel file
- municipal_codes: folder including .txt files containing zoning and land use information
- other_programs: folder including programs that take output from parse_zoning_txt.py along with other input data and create the final NZLUD files (001_process.R completes initial processing of input files; 002_create_analytic.R generates analytic files, including NZLUD files with the Zoning Restrictiveness Index (ZRI); 003_weights.R calculates survey weights; 004_compare.R carries out comparisons across the different datasets, analyzes sociodemographic characteristics of municipalities and MSAs by ZRI scores, and outputs final NZLUD files)
- other_data: folder including input data needed to run programs available in the other_programs folder
- ZoningWeightedKeywords.csv: .csv file containing weights for keyword matches
- nzlud_muni.csv: municipal-level National Zoning and Land Use Database in .csv version (Note: includes additional fields from the output of parse_zoning_txt.py)
- nzlud_muni.Rda: municipal-level National Zoning and Land Use Database for R (Note: includes additional fields from the output of parse_zoning_txt.py)
- nzlud_msa.csv: unweighted MSA-level National Zoning and Land Use Database in .csv version
- nzlud_msa.Rda: unweighted MSA-level National Zoning and Land Use Database for R
- ZRI_expand_muni_up.xlsx: underlying ZRI measure (includes all subindices for expanded sample) used for Figures 1 and 2 in the paper
- nzlud_dictionary: Data dictionary for nzlud_muni and nzlud_msa files
- msa_coverage_rates: file containing coverage rates for all MSAs present in NZLUD
- Online Only Supplement for Mleczko and Desmond (2023)

LICENSE: MIT license

03/24/2023: 002_create_analytic.R contained an error in calculating zri_c; this only impacts Tables S12 and S15 in the Online Only Supplement, which has been updated on GitHub.