'''
########################################################
## PROGRAM NAME: parse_zoning_txt.py                  ##
## PROJECT: NATIONAL ZONING AND LAND USE DATABASE     ##
## AUTHORS: MATT MLECZKO, SCOTT OVERBEY               ##
## DATE CREATED:                                      ##
## INPUTS:  User input .txt files                     ##
##          ZoningWeightedKeywords.csv                ##
##                                                    ##
## OUTPUTS:  .xls file with user-defined name         ##
##                                                    ##
## PURPOSE: Parse input zoning and land use text      ##
##          data and output database                  ##
########################################################

'''

'''
OVERALL PROCESS 

This program is a collection of functions. It is executed by running the finfun function, which triggers 
the rest of the nested functions. The one input argument for finfun is "filenames", which stores all the .txt files 
that are located in the input filepath that the user supplies. The finfun function then loops through these .txt 
files one at a time through "file", which is often the input into the nested functions of this program. The chronological 
sequence of functions once finfun is called is as follows

(1) finfun(file)
(2) getmatches
(3) getkeywords
(4) string_standardize
(5) fnote_fix
(6) threshold_mark
(7) matchvalue (nested in threshold_mark)
(8) densityinfo (also triggers fractonum and text2int)
(9) heightinfo (also triggers fractonum and text2int)
(10) parkinginfo (also triggers fractonum and text2int)
(11) resdis
(12) buildtablel1
(13) buildtablel2
(14) get_ts

TIPS FOR DEBUGGING 

This program and its constituent functions are written as a series of many loops. Oftentimes, the most straightforward
way of resolving an error in the code or determining how certain values are output is to print values along the sequence
of loops to determine how the code is handling a particular input text data. Some examples of this can be seen throughout 
the source code. Similarly, the code currently displays the filepath of each input file as it loops through all input files. 
The user is recommended to leave this as is since it helps determine which file is encountering an issue or error. The
same logic applies to printing particular values or signposts for particular functions or portions of functions. 

'''

###########################
## IMPORTANT USER INPUTS ##
###########################

# OUTPUT FILE NAME #
## NOTE: this file will save to same directory as this program ##
outputfilename = "INPUT HERE.xls"

# INPUT FOLDER FILE PATH TO INPUT .TXT FILES #
filedirect = "INPUT HERE"

# INPUT FOLDER FILE PATH TO KEYWORDS FILE #
kwpath = "INPUT HERE"

# KEYWORD CSV FILE NAME (include extension) #
kwfile = "INPUT HERE"

###########################
###########################


## import necessary modules ##

import os
import csv
import pandas as pd
import regex as re
import xlwt
import glob
import statistics
from datetime import datetime
from statistics import mode
import collections
import itertools
from iteration_utilities import deepflatten


'''
The get_ts() function retrieves the timestamp associated with each input file from the input folder.
'''

def get_ts(file):

    st_path = os.path.normpath(str(file))
    print(st_path)

    x = os.path.getmtime(st_path)
    ts = datetime.fromtimestamp(x).strftime('%Y-%m-%d %H:%M:%S')
    #print(ts)
    return(ts)

'''
The get_keywords function retrieves keywords and their respective weights from a the input .csv file. This csv file 
contains a row for each question, and keywords are listed as keyword*weight. From these, it creates a dictionary with 
the words as keys and the weights as values. It requires no arguments, so to retrieve keywords and create a dictionary 
object, the user simply write dicts = get_keywords().
'''

def get_keywords():
    keyword_dict = {}
    with open(os.path.join(kwpath, kwfile), "rt") as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        qnum = 1
        for row in list(reader):
            keywords = {}
            for kw_pair_s in row[1:]:
                if (kw_pair_s != ""):
                    kw_pair = kw_pair_s.split("*")
                    if len(kw_pair) > 1:
                        k = kw_pair[0]
                        weight = kw_pair[1]
                        keywords[k] = weight
            keyword_dict[qnum] = keywords
            qnum += 1
    if len(keyword_dict) == 0:
        print("WARNING: No keywords found.")
    values = []
    keywords = keyword_dict
    values += keyword_dict.values()
    return values


'''
The string_standardize function is used to standardized words in the input text. For example,
'singlefamily', 'single family', 'single-family', etc. wil all be standardized to 'single family'. This makes 
the task of converting keywords to weights easier and faster.
'''

def string_standardize(strng):
    replacement_dict = {
        'amendment': ['amendments'],
        'acre': ['acres','ac\.'],
        ' percent': ['%'],
        'single family': ['single-family', 'singlefamily', 'single-family'],
        'multi family': ['multi-family', 'multifamily', 'multiple-family', 'multiple family'],
        'building permit': ['building permits'],
        'use permit': ['use permits'],
        'zoning permit': ['zoning permits'],
        'special permit': ['special permits'],
        'improvement location permit': ['improvement location permits'],
        'variation': ['variations'],
        'limit': ['limits', 'limited'],
        'application': ['applications'],
        'annual': ['annually'],
        'and': ['&'],
        'front': ['frt.'],
        'year': ['yearly'],
        'allocate': ['allocation'],
        'cap': ['capped', 'caps'],
        #'construction': ['construct', 'constructed','construction'],
        'pay': ['payment'],
        'fee': ['fees'],
        'provide': ['provided', 'provision'],
        'authorize': ['authorized', 'authorizing'],
        'grant': ['granted', 'granting'],
        'approve': ['approved', 'approving', 'approval'],
        'require': ['required', 'requires', 'requirement', 'requirements', 'requiring'],
        'issue': ['issued', 'issuance'],
        'reserve': ['reserved', 'reservation'],
        'dedicate': ['dedicated'],
        'building height': ['bldg. hgt.'],
        'designate': ['designated'],
        'incorporate': ['incorporated'],
        'moratorium': ['moratoria'],
        'minimum': ['min\.'],
        'maximum': ['max\.'],
        'permit': ['permits'],
        'plan': ['plans'],
        'variance': ['variances'],
        'lot': ['lots'],
        'dwelling unit': ['d\.u\.'],
        'dwelling unit per acre': ['du\/acre', 'dus/acre'],
        'unit': ['units'],
        'square feet': ['s\.f\.', 's\.\sf\.', 'sq\sft',
                        's\.feet', 's\.\sfeet', 's\.\sfeet', 'sq\.feet',
                        'sq\.\sfeet', 'sq\sfeet'],
        'mobile home park': ['m.h. - park'],
        'mobile home subdivision': ['m.h. - subdivision'],
        'acreage': ['acreage', 'Acreage'],
        'in lieu': ['in-lieu'],
        'set aside': ['set-aside']
    }  # update as needed
    for item in replacement_dict:
        for value in sorted(replacement_dict[item]):
            re_string = r'%s' % value
            strng = re.sub(re_string, r'%s' % item, strng)
    return strng

'''
The fnote_fix function removes any footnote indicators from numbers in the thousands. This is necessary since many 
input dimensional tables will list numbers in the thousands and these numbers often have footnote indicators attached
to them. For instance, say the number 1,000 with a footnote indicator is listed in a dimensional table. Without this
function, the number will be processed as 10005 instead of 1000. This function removes the 5 (and any other footnote
indicators in the case of multiple indicators) by catching instances of more than 3 numbers after a comma. 
'''

def fnote_fix(string):
    nums = re.findall(numbers, string, flags=re.IGNORECASE)

    nums_pr = [n for n in nums if "," in n]

    for n, num in enumerate(nums_pr):
        newnum = num.split(",")
        for i, j in enumerate(newnum):
            if len(j) > 3:
                newnum[i] = j[:3]
                finnum = "".join(newnum)
                string = re.sub(str(num), str(finnum), string)

    return string


## set of stopwords to prevent false positive matches ##

stopwords = r"""(?x)          # Turn on free spacing mode
                    (?:
                      \b
                      ((?<!multi\sfamily\sresidential\sdevelopments\sin\sthe\sdistrict\sshall\shave\sa\sminimum\sarea\sof\s\d+\ssquare\-feet\sof\s|prohibiting\sall\s|residential\s)commercial\s(?!condominiums)|
                      (?<!residential\scommercial\sor\s)industrial|industry|(?<!parking\sand\soff\-street\s)loading\sspaces|
                      vehicle|bicycle|bike|trucks|cattery\spermit|fattening\smarketing|outdoor\sathletic|security\sfences|
                      rv\spark|shopping|budget|(?<!\d+\-)year|id\s*\-\s*rc\sdistrict\szone\scontrols|c\-ol\sdistrict\slot\sstandards|
                      grocery|special\sdistrict|(?<!multi\sfamily\sresidential\sdevelopment\sin\sthe\s)cc|historic\spreserve\scluster|
                      gc|animal|animals|adult\sentertainment|manufactured\shome\sparks\smust\smeet\sthe\sfollowing\srequire|
                      educational|colleges|college|cultural|subarea|trucking|truck|operating\sthe\sfacility|
                      highways|(?<!abutting\sland\sreserve\sfor\s)highway|recycling|storage|(?<!non\-)farm|bus|camp|camps|pod|pd|day\scare|hotel|motel|hotels|
                      consolidated\sparcel|non\-conforming|signage|motels|fields\sand\scourses\sshall\sbe\sa\sminimum\sof|
                      barn|barns|greenhouses|greenhouse|vehicle|vehicles|beverages|railroad|energy|
                      personal\scare\sboarding\shome|portion\sof\sa\sconvenience\sstore|other\sretail\ssales|
                      equipment|patients|private\sstreet|(?<!central\s)business\s(?!district)|restaurant|
                      motel|day\-care|shop|unincorporate|lot\son\swhich\sthe\sfacility\sis\slocated|
                      for\spark\sand\sopen\sspace\susage|cumulative\searth\sdisturbance|public\shearing\sapprove|
                      acre\stotal\sexceed|farmland|bp\-or|cs|i\-r|repairs|wetlands|tree|o\/id|fast\-food|
                      lot\sreserve\sflag\slot\sa\sbuildable\slot\swhere|multiplying\sthe\snet\sdevelopable\sacreage|
                      cbc\sdevelopment|public\sassembly|mall|pharmacies|canopy|\w{1}\slandscaped\sroundabouts|
                      service\sstation|service\sstations|worship|pcd|private\sstreets|adult\-oriented|sanitarium|tavern|
                      contiguous\sacre|cemeteries|hospital|hospitals|used\sby\ssuch\sinstitution|
                      county\shealth\sdepartment|garage\ssize\sit\sis\sintended|sleeping\sroom\sshall\sbe|
                      net\sland\sarea\sshall\sbe\srequire\sto\saccommodate\sthe\sundefined\suse|permanent\sscreen\sbuffer|
                      except\swhere\sa\sspecific\szoning\sdistrict\srequire\smore\sthan\s\d+\sacre|
                      board\sof\shealth|place\sof\sassembly|notes|(?<!recorder\'s\s)office|research|nursing\shomes|foster\scare|
                      uranium|plutonium|stable|stables|dealerships|library|libraries|automobile|automobiles|
                      wind\sturbine|mausoleum|police|assembly|livestock|freight|boat|deteriorating\sarea|
                      mp\sdistrict|hi\sdistrict|(?<!except\scommercial\sdairies\scommercial\s)kennels|
                      (?<!except\scommercial\sdairies\scommercial\s)kennel|radio|television|broadcasting|crops|assisted\sliving|
                      campus|comprehensive\sguide\splan|foster\scare|(?<!housing\sfor\sthe\s)elderly\s(?!housing)|burlapped|plant\stype|
                      group\sof\sadjacent\sparcels|products|derrick|rig|wcsquare\sfeets|cemetery|petting\sfarms|
                      residential\szoning\sboundary|i\-\d+(?!\:\sno\sspecified\sminimum)|market|community\sfacilities|
                      c\-\d+(?!\:\sno\sspecified\sminimum)|station|motor\sfuel|solid\swaste|motocross|parking\sstructure|
                      applicant\sshall\ssubmit\sa\ssite\splan|structured\sparking\son\-site\seither\swithin\sthe\sbuilding|
                      fumes|billboard|wtf|flagpole|gdp|use\sshall\soccupy\san\saccessory\sstructure|wall\smounted\ssign|
                      vending|open\sspace\squotient|sign|signs|children|nursing|tower|towers|br\-cd|turbine|
                      sign\sarea|ball|field|court|outdoor\sactivity|abutting\sresidential\sdistrict|institutional|
                      telecommunications|constricted\sturning\smovements|parking\sareas|acre\plsnet\sbuildable|
                      where\sabutting\sa\sresidential\sdistrict|districts\sin\swhich\suse\smay\sbe\spermitted|parking\sstalls|
                      recreational\soperation|recreational\sbuildings|adult|personal\scare\sbuilding|church|
                      authorize\sbuildings|common\sparking|combination\sof\suses|point\sbetween\sany\s\d+\sbuildings|
                      vibration|smoke|rodents|insects|for\sexample|example|examples|mining|adult|apiary|reational\spurpose|
                      recreation|borough\ssolicitor|impoundment|helipad|operation|parking\sbays|auction|recreational|
                      treatment\scenters|centers|town\scenter|rao\sdistrict|\d+\sacre\/\d+\ssquare\sfeet|condemned|
                      mortuary|religious|nearest\sdimensional\sdistrict\scriteria|marijuana\sgrower|
                      squares|landscaped\sarea|m\-\d+|hive|dog|dogs|horse|horses|pony|village\shousing|o\-p|
                      maximum\ssize\sof\sthe\saccessory\sbuilding|pigeons|lot\sarea\smaximum\ssize|decorative\sfence|
                      more\sthan\sthe\sminimum\s\d+\sacre\smay\sbe\sallowed|rectory|permitted\sreductions|wholesale|
                      itc|lighting|solar|crops|pastures|ranch|step\s\d+|illudus|gross\sarea\sof\sthe\sdevelopment|
                      shooting\srange|placement\spermit|adjacent\sto\sa\sone\-family\sor\stwo\-family\sresidential\szoning\sdistrict|
                      opaque\sscreen|chicken|coop|community\splan|pic\-ol|long\-term\sand\sextended\scare|wharf|
                      individual\slot\ssizes\sguided\sby\sstandards\scontained\sin|plazas|access\sto\sthe\ssite|private\sclubs|
                      minimum\sdepth\sof\ssetback|utd\sprojects|national\sregister|variable\slot\ssize\sdevelopment|
                      marijuana\sdispensaries|gallons\sper\ssquare|phased\soverall\sdevelopment|cmu|pergolas|landscaping|
                      manufacturing|using\sa\sminimum\slot\ssize\sof|mf\szone|rezone|non\-residential(?!\suses\spermitted)|
                      landscape|center\sin\sthe\scity|no\sminimum\slot\ssize\sestablished\sfor\ssubdivided\sproperties|
                      b\-\d+\sdistrict(?!\s1\smulti\sfamily\sunit)|rectories|adjacent\sto\sa\sresidential\sdistrict|sleeping\srooms|junk\syards|
                      senior\sresidential\sdwelling\sdevelopment|in\sthe\si\sdistrict|planned\smultiple\sproject|
                      attached\ssingle\sfamily\sdevelopments|faa|special\sexceptions|senior\scitizen|natural\shazard|
                      funeral|extraction\soperations|higher\seducation|i\-g\sdistrict|salvage|
                      breakfast|high\-rise\sapartments|total\sarea\sof\sthe\slot\scovered\sby\sbuildings\sparking\slot|
                      mid\-rise\sapartments|subdivision\splan|lodging\srentals|lot\ssize\sfee|(?<!high\sdensity\s)puds|watchman|
                      mini\-warehousing|game\smanagement|bp\sdistrict|pmxd\-\d+|lot\ssize\sannual\sfee|canal\scompany|
                      water\sper\sacre\sof\sland|pc-\d+|for\suses\sother\sthan\sdwellings|dollars|roadside\sstands|
                      programs\sevents|merchandise\ssales|public\sparks|port|home\soccupation\sshall\smeet|operations|
                      loading\sberth|professional\ss ervices|dancing|seminaries|special\sexception\swhere\slocated|
                      secondary\srural\sroads|proprietary|convalescent\scenter|clubs|curriculum|open\sair\sbusiness|
                      number\sof\sbedrooms\sminimum\sfloor\sarea|honey\sbees|honey\sbee|submit\sa\splan|swale|
                      public\sswimming\spools|multiplefamily\sdevelopment|dividing\sthe\snet\slot\sarea\sby|
                      standards\sfor\sminimum\sfloor\sarea\sare\sas\sfollows|ccr\szone\sdevelopment\sstandards|
                      life\scare|supervision\sof\sresidents|land\sdonation|assistance\shousing|internal\sstreet\ssystem|
                      \d+\sdependent\selderly\shousing\sunit\sper\sdwelling\sunit\spermitted\sin\sthe\szoning\sdistrict|
                      specific\sregulations\sfor\sa\ssewage\/liquid\streatment\sfacility|liquid\spipeline\sfacility|
                      specific\sregulations\sfor\san\soutdoor\sutility\ssubstation\/distribution\sfacility|
                      floor\sarea\sof\sdwellings\sshall\sbe\sas\sfollows\sfor\seach\sdistrict|
                      restaurants\sshall\sbe\spermitted\sin\sup\sto\s25\spercent\sof\sthe\shid\sdistrict|
                      table\sof\spublic\sfacilities\sdistrict|industrial\shazardous\swaste\smanagement\sfacility|
                      standards\sfor\sthe\sschool\ss*\sdistrict\sare\sas\sfollows|time\sof\sdisplay\sbe\sless\sthan\s\d+\sseconds|
                      exception\smay\sbe\sgrant\sunder\sthe\sfollowing\sconditions|seating\scapacity\srange|
                      gross\sfloor\sarea\sof\sthe\saccessory\sapartment\shoused\swithin\san\sexisting\ssingle\sfamily\sdwelling|
                      group\scare\sfacilities\saccommodating\sfrom|use\sas\san\segg\sproduction\shouse\sstockyard\sor\sfeedlot|
                      table\s\w+\s\-*\sminimum\slot\ssize\sby\sliving\sarea\sor\sfloorspace|
                      division\sof\sa\stract\sof\sland\sof\slegal\srecord\sinto\slot|average\ssize\sof\sall\slot\sof\sthe\shillside\sarea|
                      permit\swith\san\sexception\sto\sthe\smaximum\sunit\ssize|average\sfloor\sarea\spermitted\sfor\seach\stype\sof\sunit|
                      no\spart\sof\ssuch\suse\sshall\sbe\slocated\swithin\s\d+\sfeet\sof\sany\sresidence|industrial\spark\ssubdivision\sip\sintensity\sbonus|
                      minimum\sstructural\sdesign\sstandards\:\srear\sor\sside\syard\sor\sattached\sgarage|
                      no\spermit\sshall\sbe\sissue\sfor\sany\sprivate\swastewater\sdisposal\ssystem|amusement\sdevices\sshall\sbe\spermitted|
                      private\syard\shaving\san\saggregate\snet\sarea\sper\sdwelling\sunit\sof\snot\sless\sthan\s\d+\s*\d*\ssquare\sfeet|
                      exempt\sfrom\sthe\srequire\sfor\sfire\shydrants\sif\sall\sof\sthe\sfollowing\sconditions\sare\smet|
                      minimum\sproperty\ssize\.*\sthe\sland\son\swhich\sthe\sproposed\sdevelopment\swill\sbe\ssited\sis\sa\sminimum\sof\s\d+\sacre|
                      navigability\sof\sa\sstream\sor\sthe\slocation\sof\sthe\sordinary\shighwater\smark\sarise|in\sthe\scase\sof\snonresidential\sdistricts|
                      the\smaximum\sfloor\sarea\sof\san\saccessory\sbuilding\slocated\sin\sa\sresidential\szone\sshall\snot\sexceed|
                      existing\sstructures\swhich\sare\sconverted\sto\stwo\-family\sdwellings\sshall\scontain\sa\sminimum\sfloor\sarea\sof|
                      gross\sfloor\sarea\sof\sless\sthan\sthe\sfollowing|at\sleast\s300\sfeet\sfrom\sany\sproperty\szoned\sfor\sresidential\spurposesquare\sfeet|
                      accessory\sdwelling\sshall\sbe\soccupied\sby\sa\sperson\s\d+\s\d*\s*years\sor\solder|calculations\sresulting\sin\smajor\sfractions|
                      used\scar\slot\sshall\shave\sa\stotal\slot\sarea\sof|length\sin\smiles\sof\ssewer\smain\sextension\sfrom\sexisting\smanhole\sto\ssite\sboundary|
                      for\szoning\smap\samendment\sif\sthe\sarea\sis\snot\scontiguous|written\sstatement\sdetailing\show\sthe\sproposed\schange\sis\sallowable|
                      minimum\sof\s\d+\sacre\sof\shigh\sground\sfor\sparks\saround\sponds|replacement\sof\simpacted\swetland\sarea|
                      require\sin\swatershed\sdistricts\sand\sin\sother\swater|table\sof\sdimensional\sstandards\sconditional\-only\szoning\sdistricts|
                      easement\slot\smeans\sa\slot\shaving\san\sarea\sof\sa\sminimum\sof\s\d+\sacre|minimum\slot\sarea\sof\s\d+\sacre\sis\srequire\sunless\sthe\sparkland\sis\sa\slong\slinear\strail|
                      the\suseable\slot\sarea\sshall\sbe\sdetermined\sby\sdeducting\sfrom\sthe\stotal\slot\sarea|bonus\sdensity\sdesign|residential\scare\sfacilities\sshall\scomply\swith|
                      manufactured\sdwelling\spark\sgeneral\sdevelopment\sstandards|a\scredit\sof\s\d+\.*\d*\sdwelling\sunit\sper\sacre\smay\sbe\spermitted\sabove\sthe\sbase\sdensity|
                      net\sdensity\sper\sdwelling\sunit\spercentage\sof\sgross\sacre\srequire\sfor\sdedicationretail\sbody\sart|minimum\slot\ssize\sfor\sany\sstructure\sgreater\sthan\s\d+\sfeet\sin\sheight\sis\s\d+\ssquare\sfeet|
                      zoning\sdistrict\swhichever\sis\sthe\slesser\son\szoning\slot\shaving\sa\slot\sarea\s\d+\sacre\sor\smore|the\sfacility\sshall\sbe\slocated\son\sa\szoning\slot\sthat\sis\sa\sminimum|
                      ps\sadditional\srequire\snonresidential\sdevelopment|structures\sin\sthe\so\sdistrict|city\scouncil\smay\srequire\sthat\smobile\shomes|shall\sapply\sto\sall\smulti\sfamily\sland\suses\swithin\sthe|
                      be\soperated\sby\sthe\sfamily\sresiding\son\sthe\spremises|minimum\slot\sarea\sfor\spublic\/non\-public\sschools|where\sit\sabuts\sa\sresidential\szone|wireless\scommunication\sfacilities)\b|
                      secondary\sschools\sin\saccordance\swith\sthe\sfollowing\srequire\:|subdivision\shaving\sno\smore\sthan\s\d+\s*\d*\slot|maximum\snumber\sof\smobile\shomes|the\sdistrict\sshall\sencompass\sa\sminimum\sarea\sof\s\d+\sgross\sacre|
                      contents\:|schools\sand\stheir\scustomary\srelated\suses\sprovide\:|lot\sarea\ssquare\sfeet\smaximum\spermitted\sdevelopment\scoverage\sless\sthan\s\d+\s\d+\%|the\sminimum\sfloor\sspace\sper\sfamily\sshall\sbe\sas\sfollows\:|
                      maximum\spermitted\sbuilding\scoverage\sfor\sany\slot\scontaining\sa\sone\-family\sdetached\sdwelling\sin\san\sr\-2a\sr\-1a\sr\-1\/2a\sor\sr\-1\/4a\sdistrict\sshall\sbe\sas\sset\sforth\sbelow\:|
                      determined\sby\smultiplying\sthe\spba\sby\sthe\smodified\sdensity|parcels\sbetween\s\d+\sand\s\d+\sacre\:|does\snot\sapply\sif\:|\w{1}\.\sthe\sfacility\sshall|the\slot\sfor\sthe\so\-1\sdistrict|
                      the\shospice\smust\sbe\slocated\son\sa\slot\sof\srecord\swhich\smeets\sall\sof\sthe\sfollowing\scriteria\:|manufactured\shome\spark\sdevelopments\-general\srequire\.|treatment\sprogram|divide\sacreages|
                      large\-scale\sretail\sestablishments\-\smay\sbe\spermitted|community\sfacility\ssite\sdevelopment\sstandards\.|corrections\sfacilities\.|shall\snot\sbe\slocated\swithin\s\d+\sfeet\sof\sany\sresidentially\szoned\sproperty|
                      overlay\szoning\ssl\sshall\sbe\ssubject\sto\sthe\sfollowing\scriteria\:|if\slot\sare\slocated\sat\sthe\send\sof\sa\scul\-de\-sac|part\sof\san\sexisting\sfacility|advertising\sstructures|landowner\sshall\sbe\sdefined\sas|
                      other\scivic\samenities\.|farmers\'\smarket\ssubject\sto)"""

header_stopwords = r"""(?x)          # Turn on free spacing mode
                    (
                      \b
                      (industry|facility|loading\sspaces|ordinance|horse|horses|commercial\sdevelopment\sstandards|
                      vehicle|bicycle|bike|ord.|rv\spark|shopping|budget|year|
                      grocery|animal|animals|educational|colleges|college|cultural|block|trucking|truck|
                      recycling|farm|bus|camp|camps|signage|farm|swimming\spools|vegetation|
                      (?<!residential\sdistricts\s)non\-residential|
                      swimming\spool|barn|barns|greenhouses|greenhouse|nonresidential|vehicle|vehicles|beverages|
                      equipment|sewage|patients|private\sstreet|restaurant|motel|farmland|repairs|wetlands|
                      shall|pdr|pdc|pdo|where\sthe\sminimum\slot\ssize\sis|~|(?<!garage\s)entrance|suchty\sabuts|
                      commercial\sand\sindustrial\szones\sdevelopment\sstandards|is\srequire\sfor|
                      is\sintended\sto\spreserve|c\s+gross\sdensity\:\sin\sthe|none|day\scare\shome|
                      bulk\sregulations\sfor\sindustrial\sdistricts|industrial\sdistricts\sbulk\sregulations|article|
                      pursuant|lake\sshores|storm\sdrainage\sbasins|\s\w{1}\.\s|studio|efficiency\s\d+|
                      the\sminimum\slot\sarea\sfor\slot\sin\sthe|see\sdivision|
                      minimum\sarea\sownership\sand\scontrol\sthe\ssite\sof\sthe\splanned\sunit\sdevelopment|
                      within\sthe\ssubdivision\sarea\sas\sshown\son\sthe\scomprehensive\splan)
                      \b|\(\)\.\s\(\)|density\sstandards\.\sthe\snet\sdensity\sin\sthe
                      )"""

## numbers is a regex meant to capture any instance of digit information ##
## code adapted from Wiktor Stribiżew from StackOverflow: https://stackoverflow.com/questions/39594066/using-regex-extract-all-digit-and-word-numbers ##

numbers = r"""(?x)          # Turn on free spacing mode
            (
              #^a(?=\s)|     # Here we match a at the start of string before  whitespace
              #[-]?[0-9]+[,.]?[0-9]*[\/][0-9]+[,.]?[0-9]*|  # new numbers
              (?<!-\d*\.*|\.|table\s\d*\.*\d*\.*\d*\.*)\b[0-9]+[,.]?[0-9]*|  # new numbers
              (?<!-\d*\.*|\.|table\s\d*\.*\d*\.*\d*\.*)\b\d*\.?\,?\\?\d+ # HERE we match one or more digits
              #\b            # Initial word boundary 
              #(?:
              #    one|two|three|four|five|six|seven|eight|nine|ten| 
              #    eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen| 
              #    eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty| 
              #    ninety|hundred|thousand|half
              #)             # A list of alternatives
              #\b            # Trailing word boundary
              )"""

## the following set of regex entries are meant to capture acre, square feet, dwelling unit, height, and parking info ##

acreinfo_s = r"(?:)\b((?<!unit\s)acre|ac\.|ac)\b"
sqftinfo_s = r"\b(square\sfeet|sf|s\.f\.|sq\.\sfeet|sq\sft|square|for\seach\sdwelling\sunit|sq\.\sfeet|per\sdwelling\sunit)\b"
unitinfo_s = r"""(?x)(?:\b(dwelling\sunit\sper\snet\sacre|unit\sper\snet\sacre|dwelling\sunit\sper\sacre|dwelling\sunit\sper\seach\s1\snet\sacre|
                    dwelling\sunit\sper\sacre|unit\sper\sacre|unit\/net\sacre|unit\sper\sgross\sacre|unit\sper\snet\splatted\sacre|
                    du\/gross\sacre|maximum\sdwelling\sunit\sper\sstructure|maximum\sdwelling\sunit\sper\sgross\sacre|
                    density\sper\sacre|
                    maximum\sdwelling\sunit\sper\sbuildable\sacre|up\sto\s\d+\s\d*\s*unit|up\sto\s\d+\sdwelling\sunit|square\sfeet\/du|
                    \d+\-\d+\sdwelling\sunit|dwelling\sper\sgross\sacre|minimum\snumber\sof\sunit|dwelling\sunit|dua)\b)"""
height_ft = r"""(?x)(?:\b((?<!square\s)feet|(?<!sq\s)ft)\b)"""
height_st = r"""(?x)\b(story|stories)\b"""
parkinfo = r"""(?x)\b(parking\sspace|parking\sspaces|parking\sspot|parking\sspots|parking|
                guest\sspace|per\sdu|per\sdwelling\sunit|per\sunit|minimum\sparking\srequire|
                for\seach\sdwelling\sunit|for\severy\sdwelling\sunit|for\seach\sapartment|
                minimum\sspaces\srequire|for\seach\sfamily|spaces)\b"""


'''
The get_matches function is the first step of the matching process. For each input file, it first completes a set of  
of text pre-processing tasks. It then finds any general keywords in biglist, which has keywords separated by 
question (measure), and then retrieves the keyword and the surrounding x characters, depending on the measure. This 
process is meant to narrow searches to codes related to zoning and land use. The output from this step is a list of lists. 

Next, the get_matches function looks for more specific keywords, each of which has an associated weight that 
will be used to determine the value of a particular measure indicator. Consequently, this step produces a list of 
lists of lists. The largest list is every match (represented by 'matches') which is the final return of get_matches. 
Within matches, there are 27 elements, all of which are lists, each one corresponding to a question (measure). Each of these 
question lists is then a list of the actual matches. This method was used to organize our matches by question (measure).

For example:
matches[0] would return a list of matches for question (measure) 1.
matches[0][0] would return the first matches for question (measure) 1, which would look something like 
['building permit','single family]

Hence, matches has three layers: 
Layer 1 = a list of 27 lists representing the 27 question/measures
Layer 2 = a list of matching strings for a particular question/measure
Layer 3 = a list of matching keywords for a particular question/measure 
'''

def getmatches(file1,sn):
    dicts = get_keywords()
    matches = list(range(27))  # placeholders to prevent an Index Error later on
    gen_matches = []
    matches_shell = []
    test = []
    ## list of lists of keywords for each measure ##
    biglist = [[r'residential subdivision building permits', r'unit ceiling',
                r'growth management', r'growth control', r'growth rate', r'development approvals'],
               [r'residential subdivision building permits', r'unit ceiling',
                r'growth management', r'growth control', r'growth rate', r'development approvals'],
               [r'unit ceiling',
                r'growth management', r'growth control', r'growth rate', r'development approvals'],
               [r'unit ceiling',
                r'growth management', r'growth control', r'growth rate', r'development approvals'],
               [r'unit ceiling',
                r'growth management', r'growth control', r'growth rate', r'development approvals'],
               [r'unit ceiling', r'dwelling units per building',
                r'growth management', r'growth control', r'growth rate', r'development approvals',
                r'minimum additional lot area'],
               [r'lot area', r'lot size', r'lot', r'area of parcel', r'zoning district', r'residential zones',
                r'residential district', r'residential district r-1', 'residential district r-a', r'schedule of',
                r'residential r-2 district', r'residential r-3 district', r'residential r-4 district',
                r'dimension regulations', r'lot require', r'lot yard and density regulations',
                r'dimensional regulations', r'dimensional require', r'dimensional and density regulations',
                r'development standards', r'intensity of use', r'dimensional controls', r'zone dwelling family size',
                r'intensity regulations', r'dimensional standards', r'dimension restrictions', r'parcel size',
                r'maximum density', r'density', r'minimum building site area', r'bulk and replacement',
                r'maximum unit allowed', r'height and area regulations', r'area and bulk schedule', r'area and bulk standards',
                r'district design require', r'height and area require', r'lot and bulk standards',
                r'height and lot require', r'area setback and height require', r'height area and yard require',
                r'bulk and area regulations', r'density schedule', r'dimensional table', r'height and yard require',
                r'bulk and yard regulations', r'spatial require', r'zoning district schedules',
                r'lot standards by zone', r'development regulations', r'lot dimension and intensity standards',
                r'density and bulk require', r'bulk regulations', r'bulk and placement regulations',
                r'minimum lot size per dwelling unit', r'bulk and coverage controls', r'bulk require',
                r'land space require', r'lot area frontage and yard require', r'yard and height require',
                r'lot standards matrix', r'area yard and height standards', r'area yard and height regulations',
                r'other dimensions and space require', r'area, yard and height regulations', r'bulk and area standards',
                r'development criteria district', r'zone standards', r'height limit lot sizes and coverage',
                r'land use district and allowable uses', r'summary of zoning district require', r'site dimensions',
                r'bulk and setback regulations', r'residential bulk chart', r'bulk matrix',r'bulk yard and space require',
                r'residential uses and require', r'zoning district regulation chart', r'density regulations',
                r'standards for principal buildings on individual lots', r'lot and yard require',
                r'lot yard area and height require', r'area yard and height require',
                r'density dimensions and other standards', r'districts:', r'density and intensity limit',
                r'bulk schedules'],
               [r'lot area', r'lot size', r'lot', r'multiple dwelling', r'zoning district', r'residential district',
                r'residential district r-1', r'height and lot require', r'zoning district schedules',
                r'residential district r-a', r'residential r-2 district', r'residential r-3 district',
                r'residential r-4 district', r'land area provide for each dwelling unit', r'dimensional table',
                r'dimension regulations', r'dimensional regulations', r'dimensional require', r'zone dwelling family size',
                r'lot yard and density regulations', r'area setback and height require', r'spatial require',
                r'dimensional and density regulations', r'intensity of use', r'dimensional controls', r'area and bulk standards',
                r'development standards', r'intensity regulations', r'dimensional standards', r'dimension restrictions',
                r'schedule of', r'maximum permitted residential density', r'maximum allowable residential density',
                r'maximum permitted density', r'maximum allowable density', r'maximum density', r'density',
                r'residential acreage dwelling unit', r'lot require', r'height and area regulations',
                r'height and yard require', r'height area and yard require', r'bulk yard and space require',
                r'multi family', r'density schedule', r'maximum unit allowed', r'residential uses and require',
                r'acre\/dwelling unit', r'per dwelling unit', r'for each dwelling unit', r'bulk and replacement',
                r'dwelling unit per acre', r'square feet\/dwelling unit', r'unit\/net acre',
                r'district design require', r'height and area require', r'lot and bulk standards', r'bulk require',
                r'bulk and yard regulations',r'density regulations', r'site dimensions',
                r'bulk and area regulations', r'lot standards by zone', r'summary of zoning district require',
                r'development regulations', r'lot dimension and intensity standards', r'density and bulk require',
                r'bulk regulations', r'bulk and placement regulations', r'minimum lot size per dwelling unit',
                r'land space require', r'lot area frontage and yard require', r'yard and height require',
                r'lot standards matrix', r'area yard and height standards', r'area yard and height regulations',
                r'bulk and coverage controls', r'density dimensions and other standards',
                r'other dimensions and space require', r'area, yard and height regulations', r'bulk and area standards',
                r'development criteria district', r'zone standards', r'height limit lot sizes and coverage',
                r'land use district and allowable uses', r'zoning district regulation chart',
                r'bulk and setback regulations', r'residential bulk chart', r'bulk matrix',
                r'standards for principal buildings on individual lots', r'area and bulk schedule', r'density and intensity limit'
                r'lot and yard require', r'lot yard area and height require', r'area yard and height require',r'districts:',
                r'bulk schedules'],
               [r'open space'],
               [r'inclusionary', r'affordable', r'mixed income housing', r'low cost housing'],
               [r'city council', r'town council', r'village council', r'village board', r'township council',
                r'the council', r'board of aldermen', r'city commission', r'borough council', r'board of selectmen',
                r'board of supervisors', r'governing body', r'board of commissioners', r'board of mayor and aldermen',
                r'mayor and council', r'board of trustees'],
               [r'planning board', r'planning commission', r'planning and zoning commission', r'planning and zoning board',
                r'planning and appeals commission', r'plan commission', r'planning and sustainability commission',
                r'redevelopment board', r'zoning commission', r'land use board', r'the commission',
                r'metropolitan development commission', r'development commission'],
               [r'county board of commissioners', r'county board', r'county commissioners',
                r'county board of supervisors', r'county commission', r'county council',
                r'parish board of commissioners', r'parish board', r'parish commissioners',
                r'parish board of supervisors', r'parish commission', r'parish council',
                r'board of freeholders', r'board of chosen freeholders'],
               [r'health department', r'department of health', r'public health board', r'public health commission'],
               [r'site plan and architectural review board', r'site plan and architectural review commission',
                r'site plan and architectural review committee',
                r'architectural review board', r'architectural review commission', r'architectural review committee',
                r'site plan review board', r'site plan review commission', r'site plan review committee',
                r'design review board', r'design review commission', r'design review committee',
                r'design board', r'design commission', r'design committee',
                r'development review board', r'development review commission', r'development review committee',
                r'visual resources review board'],
               [r'environmental review board', r'environmental review committee', r'environmental commission',
                r'environmental impact review board', r'environmental impact review committee',
                r'environmental review advisory board', r'environmental review advisory committee',
                r'environmental assessment board', r'environmental assessment committee'],
               [r'city council', r'town council', r'village council', r'village board',r'township council',
                r'the council', r'board of aldermen', r'city commission', r'borough council', r'board of selectmen',
                r'board of supervisors', r'governing body', r'board of commissioners', r'board of mayor and aldermen',
                r'mayor and council', r'board of trustees'],
               [r'planning board', r'planning commission', r'planning and zoning commission', r'planning and zoning board',
                r'planning and appeals commission', r'plan commission', r'planning and sustainability commission',
                r'redevelopment board', r'zoning commission', r'land use board', r'the commission',
                r'metropolitan development commission', r'development commission'],
               [r'zoning board', r'board of zoning appeals', r'board of appeals', r'board of appeal',
                r'board of adjustment and appeals', r'board of adjustment', r'zoning hearing board',
                r'adjustment board', r'adjustment commission', r'adjustment committee'],
               [r'county board of commissioners', r'county board', r'county commissioners',
                r'county board of supervisors', r'county commission', r'county council',
                r'parish board of commissioners', r'parish board', r'parish commissioners',
                r'parish board of supervisors', r'parish commission', r'parish council',
                r'board of freeholders', r'board of chosen freeholders'],
               [r'county zoning board', r'county zoning commission', r'county planning board',
                r'parish zoning board', r'parish zoning commission', r'parish planning board'],
               [r'town meeting'],
               [r'environmental review board', r'environmental review committee', r'environmental commission',
                r'environmental impact review board', r'environmental impact review committee',
                r'environmental review advisory board', r'environmental review advisory committee',
                r'environmental assessment board', r'environmental assessment committee'],
               [r'accessory dwelling unit', r'accessory dwelling units', r'accessory apartment', r'accessory apartments',
                r'accessory dwelling', r'accessory dwellings', r'accessory suite', r'accessory suites',
                r'ancillary unit', r'ancillary units', r'basement apartment', r'basement apartments',
                r'carriage house', r'carriage homes', r'carriage houses', r'carriage homes',
                r'garden cottage', r'garden cottages', r'granny cottage', r'granny cottages', r'granny unit', r'granny units',
                r'secondary suite', r'secondary suites', r'granny flat', r'granny flats', r'guest house', r'guest houses',
                r'backyard cottage', r'backyard cottages', r'in-law unit', r'in-law units', r'in-law suite', r'in-law suites',
                r'in-law flat', r'in-law flats', r'secondary unit', r'secondary units', r'secondary dwelling unit', r'secondary dwelling units',
                r'laneway house' r'laneway houses', r'secondary dwelling unit', r'secondary dwelling units'],
               [r'maximum height', r'building height', r'height'],
               [r'parking spots', r'parking spaces', r'parking', r'off-street spaces require',
                r'minimum parking require', r'minimum spaces require', r'vehicle', r'one space for'],
               [r'residential districts', r'residential district', r'residential single-family district',
                r'residential multi family district', r'residential single family district',
                r'single residential', r'multiple residential', r'density residential',
                r'zoning district schedules', r'three-family district', r'residential detached zones',
                r'residential multi family district' r'residential multiple-family district', r'residential zone',
                r'residential multi family district', r'zoning districts', r'zoning district', r'zone district',
                r'multi family residential', r'single family residential', r'land use districts',
                r'residential high density', r'residential medium density', r'rural residential',
                r'residential one acre', r'residential two acre',
                r'housing district', r'residence zone', r'residential zone', r'dwelling zone', r'multiuse zone',
                r'mid-rise district', r'high-rise district', r'mixed use zone', r'overlay district', r'use regulation schedule',
                r'housing (four stories or less) district',  r'residential overlay', r'one-family zone', r'multi family zone',
                r'classes of districts', r'district', r'district that is designed to', r'residence districts',
                r'residential classifications', r'district regulations', r'creation of districts', r'dwelling district:',
                r'r1 district', r'r2 district', r'r3 district', r'r4 district', r'r5 district', r'r6 district', r'r7 district',
                r'r-1 district', r'r-2 district', r'r-3 district', r'r-4 district', r'residential-general district',
                r'low density district', r'medium density district', r'high density district', r'rural density district',
                r'general residence district', r'residential use district', r'residence district',
                r'residential urban district', r'residential suburban district', r'residential limited business district',
                r're residential-existing district', r'conservation district', 'r-16 district',
                r'low density residential', r'medium density residential', r'rm district',
                r'low density-residential', r'medium-density residential', r'medium-high-density residential',
                r'r-1 residential.', r'r-2 residential.', r'r-3 residential.',
                r'residence a district', r'residence aa district', r'residence b district', r'residence bb district',
                r'residence c-1 district', r'residence c-2 district', r'residence cc district',
                r'residence d district', r'residence dd district', r'residence e district', r'residence ee district',
                r'residence f district', r'residence ff district', r'residence k district',
                r'residence a-1', r'residence a-2', r'low-rise', r'medium-rise', r'high-rise',r'district',
                r'residential urban zone', r'residential flexible zone', r'urban residence', r'suburban residence']]

    with open(file1, 'r', errors='replace') as file:
        lines = file.read()
        ## the following lines consists of a series of text pre-processing steps ##
        lines1 = re.sub(r'"\d+', '', lines)
        lines2 = re.sub(r'[^\x00-\x7f]', r'-', lines1)
        lines3 = ' '.join(lines2.split())
        lines4 = re.sub(r'\n', ' ', lines3)  # takes away all new line indicators and replaces with a space, fixed a problem where regex wasn't catching some words when ran in the loop
        lines5 = re.sub(r'\t', ' ', lines4)  # removes \t characters
        lines6 = re.sub(r'\\', '', lines5)
        lines7 = re.sub(r'http\S+', '', lines6)
        lines8 = re.sub(r'\d+\.\d{3,}\.*\d*\.*\d*|\d+\.\d+\.\d+|\+\-+|\-{3,}', '', lines7)
        lines9 = re.sub(r'\[\d+\]', '', lines8)
        lines10 = re.sub(r'=', ' ', lines9)
        lines11 = re.sub(r'\bsf\b', "square feet", lines10)
        lines12 = re.sub(
            r'\b(Sterling\sCodifiers\,\sInc\.|Article|Chapter|Section|SECTION|Sections|Subsection|Sec|Prior\scode|Code|Ordinance|Ord|Lots|through|pg|pgs|Part)\b\.*\s*(No\.)*\s*\d*\w*\:*\.*\-*\d*\-*\d*\,*\.*\s*(and)*\s*\d*\-*\d*\-*\d*\,*\s*(and)*\s*\d*\-*\d*\-*\d*',
            '', lines11)
        lines13 = re.sub(r'\bAmended\sby\sOrd\.\sNo\.\s\d+\,\s\d+\/d+\/\d+|Amended\s\d{4}\b|amended\s\d{1,2}\/\d{1,2}\/\d{1,4}|\d+\/\d+\/\d+', '', lines12)
        lines14 = re.sub(r'\d+\:\d+', '', lines13)
        lines15 = lines14.lower()
        lines16 = re.sub(r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\b\s\d+\,*\s\d{4}', '', lines15)
        lines17 = re.sub(r'pg\.|pgs\.\s\d+\-\d+|page\s\d+', '', lines16)
        lines18 = re.sub(r'\bft\.|\bft\b', "feet ", lines17)
        lines19 = string_standardize(str(lines18))
        lines20 = fnote_fix(str(lines19))
        lines21 = re.sub(r'[",!?*\[\]]', '', lines20)
        lines22 = re.sub(r';', ' ', lines21)
        lines23 = re.sub(r'\/acre|unit\/acre|unit\/net\sacre|unit\/gross\sacre|du\/ac\b', "unit per acre", lines22)
        lines24 = re.sub(r'\d+\/\d+\/\d+\ssterling\scodifiers\sinc\.', '', lines23)

        test_str = []

        biglist1 = biglist  # copied for use in subsetting match data in list by question (e.g., element one in big list 1 will be question 1 here, but later question 1 will be replaced by all matches for question 1)
        for question in biglist:
            for keyword in question:
                #print("KEYWORD")
                #print(keyword)
                kws = re.findall(str(keyword), lines24, flags=re.IGNORECASE)
                if not kws:
                    continue
                #print("MATCHING KEYWORD")
                #print(kws)
                kwpos = [m.start(0) for m in re.finditer(keyword, lines24, flags=re.IGNORECASE)]
                #print("MATCHING KEYWORD POSITIONS")
                #print(kwpos)
                if keyword in ['zoning district', 'zoning districts', 'residence zone', 'residence zones',
                               'zone district', 'zone districts', 'residential zones', 'residential zone',
                               'residential district', 'residential districts', 'dwelling zone', 'multiuse zone',
                               'classes of districts', 'district that is designed to', 'dwelling district:',
                               'residence districts', 'residence district', 'multi family residential',
                               'single family residential', 'single residential', 'multiple residential',
                               'zone dwelling family size', 'housing (four stories or less) district',
                               'residential single family district', 'residential multi family district',
                                'mid-rise district', 'high-rise district', 'mixed use zone', 'overlay district',
                               'three-family district', 'three family district', 'residential detached zones',
                               'housing district', 'housing districts', 'residential overlay',
                               'use regulation schedule', 'one-family zone', 'multi family zone',
                               'residential classifications', 'district regulations', 'creation of districts',
                               'r1 district', 'r2 district', 'r3 district', 'r4 district', 'r5 district',
                               'r6 district', 'r7 district', 'land use districts', 'rm district',
                               'r-1 district', 'r-2 district', 'r-3 district', 'r-4 district',
                               're residential-existing district', 'conservation district', 'r-16 district',
                               'low density residential', 'medium density residential', 'density residential',
                               'residence a-1', 'residence a-2', 'low-rise', 'medium-rise', 'high-rise'
                               'residence a district', 'residence aa district', 'residence b district',
                               'residence bb district',
                               'residence c-1 district', 'residence c-2 district', 'residence cc district',
                               'residence d district', 'residence dd district', 'residence e district',
                               'residence ee district',
                               'residence f district', 'residence ff district', 'residence k district'
                               'residential high density', 'residential medium density', 'rural residential',
                               'residential one acre', 'residential two acre',
                               'residential r-2 district', 'intensity regulations', 'residential-general district',
                               'general residence district', 'residential use district',
                               'residential r-3 district', 'residential r-4 district', 'dimension regulations',
                               'low density-residential', 'medium-density residential',
                               'medium-high-density residential',
                               'residential urban zone', 'residential flexible zone',
                               'urban residence', 'suburban residence',
                               'residential urban district', 'residential suburban district',
                               'residential limited business district',
                               'dimensional require', 'dimensional and density regulations', 'dimension restrictions',
                               'development standards', 'residential zones', 'schedule of', 'dimensional regulations',
                               'dimensional standards', 'bulk and replacement', 'district design require',
                               'height and area require', 'height and area regulations', 'height and lot require',
                               'lot and bulk standards', 'lot standards by zone', 'development regulations',
                               'lot dimension and intensity standards', 'density and bulk require', 'area and bulk standards',
                               'bulk and placement regulations', 'district regulations', 'bulk require',
                               'minimum lot size per dwelling unit', 'lot require', 'area and bulk schedule',
                               'land space require', 'bulk regulations', 'lot area frontage and yard require',
                               'yard and height require', 'lot standards matrix', 'other dimensions and space require',
                               'area, yard and height regulations', 'bulk and area standards', 'density schedule',
                               'development criteria district', 'zone standards', 'height limit lot sizes and coverage',
                               'low density district', 'medium density district', 'high density district',
                               'rural density district', r'site dimensions',
                               'r-1 residential.', 'r-2 residential.', 'r-3 residential.',
                               'bulk and area regulations', 'land use district and allowable uses',
                               'bulk and setback regulations', 'intensity of use', 'dimensional controls',
                               'residential bulk chart', 'bulk matrix', 'residential uses and require',
                               'standards for principal buildings on individual lots', 'lot and yard require'
                               'lot yard and density regulations', 'area setback and height require',
                               'zoning district regulation chart', 'height area and yard require',
                               'area yard and height standards', 'bulk and coverage controls', r'spatial require',
                               'lot yard area and height require', 'area yard and height require',
                               'height and yard require', 'bulk yard and space require','bulk and yard regulations',
                               'table of allowed uses', 'table of permitted uses','use table',
                               'density dimensions and other standards', 'area yard and height regulations',
                               'districts:', 'density and intensity limit','bulk schedules']:
                    new_kwpos = [[p - 300, p + 2000] for p in kwpos]
                    for n, t in enumerate(new_kwpos):
                        t = [0 if x < 0 else x for x in t]
                        t = [len(lines24) if x > len(lines24) else x for x in t]
                        new_kwpos[n] = t

                    test_str = []

                    for r in new_kwpos:
                        test_str.append(lines24[r[0]:r[1]])

                elif keyword in ['parking spots', 'parking spaces', 'parking', 'off-street spaces require',
                                 'minimum parking require', 'minimum spaces require', 'vehicle', 'one space for']:
                    new_kwpos = [[p - 750, p + 750] for p in kwpos]
                    for n, t in enumerate(new_kwpos):
                        t = [0 if x < 0 else x for x in t]
                        t = [len(lines24) if x > len(lines24) else x for x in t]
                        new_kwpos[n] = t

                    test_str = []

                    for r in new_kwpos:
                        test_str.append(lines24[r[0]:r[1]])

                elif keyword in ['district']:
                    if any(el in lines24 for el in ['zoning district', 'zoning districts', 'residence zone', 'residence zones',
                               'zone district', 'zone districts', 'residential zones', 'residential zone',
                               'residential district', 'residential districts', 'dwelling zone', 'multiuse zone',
                               'classes of districts', 'district that is designed to',
                               'residence districts', 'residence district', 'multi family residential',
                               'single family residential', 'single residential', 'multiple residential',
                               'zone dwelling family size', 'housing (four stories or less) district',
                               'residential single family district', 'residential multi family district',
                                'mid-rise district', 'high-rise district', 'mixed use zone', 'overlay district',
                               'three-family district', 'three family district', 'residential detached zones',
                               'housing district', 'housing districts', 'residential overlay',
                               'use regulation schedule', 'one-family zone', 'multi family zone',
                               'residential classifications', 'district regulations', 'creation of districts',
                               'r1 district', 'r2 district', 'r3 district', 'r4 district', 'r5 district',
                               'r6 district', 'r7 district', 'land use districts', 'rm district',
                               'r-1 district', 'r-2 district', 'r-3 district', 'r-4 district',
                               're residential-existing district', 'conservation district', 'r-16 district',
                               'low density residential', 'medium density residential',
                               r'residence a-1', r'residence a-2', r'low-rise', r'medium-rise', r'high-rise'
                               'residence a district', 'residence aa district', 'residence b district',
                               'residence bb district',
                               'residence c-1 district', 'residence c-2 district', 'residence cc district',
                               'residence d district', 'residence dd district', 'residence e district',
                               'residence ee district',
                               'residence f district', 'residence ff district', 'residence k district'
                               "residential r-2 district", "intensity regulations", "residential-general district",
                               "general residence district",
                               "residential r-3 district", "residential r-4 district"]):
                        continue
                    else:
                        new_kwpos = [[p - 250, p + 250] for p in kwpos]
                        for n, t in enumerate(new_kwpos):
                            t = [0 if x < 0 else x for x in t]
                            t = [len(lines24) if x > len(lines24) else x for x in t]
                            new_kwpos[n] = t

                    test_str = []

                    for r in new_kwpos:
                        test_str.append(lines24[r[0]:r[1]])

                else:
                    new_kwpos = [[p - 250, p + 250] for p in kwpos]
                    for n, t in enumerate(new_kwpos):
                        t = [0 if x < 0 else x for x in t]
                        t = [len(lines24) if x > len(lines24) else x for x in t]
                        new_kwpos[n] = t

                    test_str = []

                    for r in new_kwpos:
                        test_str.append(lines24[r[0]:r[1]])

                gen_matches.append(test_str)

            biglist1[biglist.index(
                question)] = gen_matches  # puts matches for question in that questions element number in biglist1
            gen_matches = []
            # matches = []
        for i in range(len(biglist1)):  # each element is matches for a specific question
            dict = dicts[i]
            wordslist = list(dict.keys())
            regex2 = re.compile("(?=(\\b" + "\\b|\\b".join(map(re.escape, wordslist)) + "\\b))", flags=re.IGNORECASE)
            out_matches = []
            for words in biglist1[i]:
                in_matches = []
                if len(words) > 0:
                    for strings in words:
                        matches_shell.append(re.findall(regex2, strings))
                    in_matches = matches_shell
                else:
                    in_matches = []
                matches_shell = []
                out_matches.append(in_matches)
            matches[i] = out_matches

        numdouble = 0
        matches_shell = []
        for questions in matches:  # 27 elements representing each question in matches list
            new_shell = []
            for new in questions:  # number of keywords within each question
                response_shell = []
                for response in new:  # response represents a list within each keyword subset, each response is matches in one string retrieved from general keyword search
                    response_shell.append(list(set(response)))
                new_shell.append(response_shell)
            matches_shell.append(new_shell)
    matches = matches_shell

    return [matches, biglist1[6], biglist1[7], biglist1[24], biglist1[25], biglist1[26]]

'''
fractonum is a function to convert any numeric information stored as fractions into digits. The input is a 
captured string from get_matches. The output is the equivalent string if no fraction is found and the equivalent
string with the converted fraction if one is found. The code accounts for a number of different fraction formats, 
including mixed fractions and fractions expressed in words.
'''

def fractonum(string):
    frac1 = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
             "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
             "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
             "fourteen": 14, "fifteen": 15, "sixteen": 16,
             "seveneteen": 17, "eighteen": 18, "nineteen": 19,
             "half": 2, "third": 3, "thirds": 3, "fourth": 4, "fourths": 4,
             "fifth": 5, "fifths": 5, "sixth": 6, "sixths": 6, "seventh": 7, "sevenths": 7,
             "eighth": 8, "eighths": 8, "ninth": 9, "ninths": 9, "tenth": 10, "tenths": 10}

    frac2 = {"half": 0.5, "third": 0.67, "quarter": 0.25, "fourth": 0.25, "fifth": 0.2,
             "sixth": 0.16667}

    newstring = string.split()

    skf = 0

    for i, ele in enumerate(newstring):
        if ele.count("/") == 1:
            cv = ele.find('/', 0, len(ele))
            if re.findall(r'du|\/unit', ele, flags=re.IGNORECASE):
                newstring[i] = " ".join(ele.split("/"))

    for i, word in enumerate(newstring):
        idx = i

        spword = word.split("/")

        if word in ["feet/stories", "stories/feet"]:
            skf = 1
        if skf == 1:

            if spword[0].isdigit() == False and word not in ["feet/stories", "stories/feet"]:
                skf = 0

        if word == "one-and-a-half":
            newstring[i] = "1.5"
        elif i != len(newstring) - 1 and newstring[i-2] == "one" and newstring[i-1] == "and" and newstring[i] == "one" and newstring[i + 1] == "half":
            newstring[i-2] = ""
            newstring[i-1] = ""
            newstring[i + 1] = ""
            newstring[i] = "1.5"
        elif i != len(newstring) - 1 and newstring[i] == "one" and newstring[i + 1] == "half":
            newstring[i] = "0.5"
            newstring[i + 1] = ""
        elif i != len(newstring) - 1 and newstring[i] == "a" and newstring[i + 1] == "half":
            newstring[i] = "0.5"
            newstring[i + 1] = ""
        elif i != len(newstring) - 1 and newstring[i] == "one" and newstring[i + 1] == "third":
            newstring[i] = "0.33"
            newstring[i + 1] = ""
        elif i != len(newstring) - 1 and newstring[i] == "one" and newstring[i + 1] == "quarter":
            newstring[i] = "0.25"
            newstring[i + 1] = ""
        if word.count("/") == 1:
            new_word_in = word.split('/')
            new_word = [elem.replace(')', '') for elem in new_word_in]
            if sum(c.isdigit() for c in new_word[0]) > 1 and new_word[0].find(".", 0, len(new_word[0])) == -1:
                if "-" in new_word[0]:
                    new_new_word = new_word[0].split("-")
                else:
                    new_new_word = new_word[0].split()
                if len(new_new_word) > 2:
                    continue
                if len(new_new_word) > 1 and new_new_word[1].isdigit() and new_word[1].isdigit() and float(
                        new_word[1]) != 0:
                    if float(new_word[1]) != 0:
                        num = float(new_new_word[1])
                        den = float(new_word[1])
                        rep = round(num / den, 2)
                        newstring[i] = ''
                        in_rep = re.sub("[^0-9]", "", new_new_word[0])
                        if in_rep:
                            newstring[idx] = str(float(in_rep.replace('(', '')) + rep)
                elif "-" in new_word[1]:
                    rep_new_word = new_word[1].split("-")
                    if rep_new_word[0].isdigit() and rep_new_word[1] == "acre" and float(rep_new_word[0]) != 0:
                        if len(new_new_word) == 1:
                            num = float(new_new_word[0].replace('(',''))
                        elif len(new_new_word) > 1:
                            num = float(new_new_word[1].replace('(',''))
                        den = float(rep_new_word[0])
                        rep = round(num / den, 2)
                        in_rep = re.sub("[^0-9]", "", new_new_word[0])
                        newstring[idx] = str(float(in_rep) + rep) + " " + rep_new_word[1]
                elif len(new_new_word) == 1 and new_new_word[0].isdigit() and new_word[1].isdigit() and float(
                        new_word[1]) != 0 and skf == 0:
                    num = float(new_word[0])
                    den = float(new_word[1])
                    rep = round(num / den, 2)
                    newstring[idx] = str(float(rep))
                elif skf == 1:
                    num1 = float(new_word[0])
                    num2 = float(new_word[1])
                    rep = max(num1,num2)
                    newstring[idx] = str(float(rep))
            elif newstring[idx - 1].isdigit():
                if new_word[0].isdigit() and new_word[1].isdigit() and float(new_word[1]) != 0:
                    num = float(new_word[0])
                    den = float(new_word[1])
                    rep = round(num / den, 2)
                    newstring[i] = ''
                    newstring[idx - 1] = str(float(newstring[idx - 1]) + rep)
                elif "-" in new_word[1] and new_word[0].isdigit():
                    rep_new_word = new_word[1].split("-")
                    if rep_new_word[0].isdigit() and rep_new_word[1] == "acre" and float(rep_new_word[0]) != 0:
                        num = float(new_word[0])
                        den = float(rep_new_word[0])
                        rep = round(num / den, 2)
                        newstring[i] = ''
                        newstring[idx - 1] = str(float(newstring[idx - 1]) + rep) + " " + rep_new_word[1]
            else:
                new_word = word.split('/')
                if new_word[0].isdigit() and new_word[1].isdigit() and float(new_word[1]) != 0:
                    newstring[idx] = str(float(new_word[0]) / float(new_word[1]))
                elif new_word[0].isdigit() and "-" in new_word[1]:
                    rep_new_word = new_word[1].split("-")
                    if rep_new_word[0].isdigit() and rep_new_word[1] == "acre" and float(rep_new_word[0]) != 0:
                        newstring[idx] = str(float(new_word[0]) / float(rep_new_word[0])) + " " + rep_new_word[1]
        if '-' in word:
            new_word = word.split('-')
            if newstring[idx - 1] == "and" and newstring[idx - 2] in frac1:
                if set([new_word[0], new_word[1]]).issubset(set(frac1)) and float(frac1[new_word[1]]) != 0:
                    num = frac1[new_word[0]]
                    den = frac1[new_word[1]]
                    rep = round(num / den, 2)
                    newstring[i] = ''
                    newstring[idx - 1] = ''
                    newstring[idx - 2] = str(frac1[newstring[idx - 2]] + rep)
                elif new_word[0] in frac1 and new_word[1] in frac2 and float(frac2[new_word[1]]) != 0:
                    num = frac1[new_word[0]]
                    den = frac2[new_word[1]]
                    rep = round(num * den, 2)
                    newstring[i] = ''
                    newstring[idx - 1] = ''
                    newstring[idx - 2] = str(frac1[newstring[idx - 2]] + rep)
                else:
                    continue
            elif set([new_word[0], new_word[1]]).issubset(set(frac1)) and float(frac1[new_word[1]]) != 0:
                num = frac1[new_word[0]]
                den = frac1[new_word[1]]
                rep = str(round(num / den, 2))
                newstring[i] = rep
            else:
                continue
        elif word in frac2:
            st = ["story","stories"]
            if idx + 3 <= len(newstring)-1:
                if newstring[idx + 1] in st or newstring[idx+3] in st:
                    rep = 1/frac2[newstring[idx]]
                    newstring[i] = str(round(rep))
            elif idx + 1 <= len(newstring)-1:
                if newstring[idx + 1] in st:
                    rep = 1/frac2[newstring[idx]]
                    newstring[i] = str(round(rep))
            elif newstring[idx - 1] == "a" and newstring[idx - 2] == "and" and newstring[idx - 3] in frac1:
                rep = frac2[newstring[idx]]
                newstring[idx], newstring[idx - 1], newstring[idx - 2] = '', '', ''
                newstring[idx - 3] = str(frac1[newstring[idx - 3]] + rep)
            elif newstring[idx - 2] == "and" and newstring[idx - 3] in frac1 and newstring[idx - 1] in frac1:
                rep = frac1[newstring[idx - 1]] * frac2[newstring[idx]]
                newstring[idx], newstring[idx - 2], newstring[idx - 1] = '', '', ''
                newstring[idx - 3] = str(frac1[newstring[idx - 3]] + rep)
            else:
                newstring[i] = str(frac2[word])

    finstring = ' '.join(newstring)

    return finstring

'''
the text2int function is adapted from code written by someone with the username "recursive" from the StackOverflow
post here: https://stackoverflow.com/questions/493174/is-there-a-way-to-convert-number-words-to-integers

It essentially converts numeric info expressed words into digits. The input is a string and the output is the same string
with converted numeric information, if any. 

'''

def text2int(textnum, numwords={}):
    if not numwords:
        units = [
            "zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
            "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
            "sixteen", "seventeen", "eighteen", "nineteen",
        ]

        tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]

        scales = ["hundred", "thousand", "million", "billion", "trillion"]

        for idx, word in enumerate(units):    numwords[word] = (1, idx)
        for idx, word in enumerate(tens):     numwords[word] = (1, idx * 10)
        for idx, word in enumerate(scales):   numwords[word] = (10 ** (idx * 3 or 2), 0)

    decs = {"tenths": 0.1, "hundredths":0.01, "thousandths":0.001}
    ordinal_words = {'first': 1, 'second': 2, 'third': 3, 'fifth': 5, 'eighth': 8, 'ninth': 9, 'twelfth': 12}
    ordinal_endings = [('ieth', 'y'), ('th', '')]

    thwords = ['fourth', 'fifth', 'sixth', 'seventh', 'eigth', 'ninth', 'tenth', 'eleventh',
               'twelvth', 'thirteenth', 'fourteenth', 'fifteenth', 'sixteenth', 'seventeenth',
               'eighteenth', 'nineteenth']


    current = result = 0
    curstring = ""
    onnumber = False
    wstring = textnum.split()
    for w, word in enumerate(wstring):
        ## added ##
        if word.count('-') == 1:
            x = word.split("-")
            newnum1 = x[0]
            newnum2 = x[1]
            if newnum1 != "" and newnum1 in numwords and newnum2 != "" and newnum2 in numwords:
                scale1, increment1 = numwords[newnum1]
                scale2, increment2 = numwords[newnum2]
                current = current * scale1 * scale2 + increment1 + increment2
                onnumber = True
            elif current != 0:
                result += current
                curstring += repr(result) + " " + word + " "
                current = result = 0
                onnumber = False
            else:
                curstring += word + " "
        elif word in decs:
            scale, increment = (decs[word], 0)
            current = round(current * scale + increment,2)
        elif word in ordinal_words:
            scale, increment = (1, ordinal_words[word])
            current = current * scale + increment
            if scale > 100:
                result += current
                current = 0
            onnumber = True
        else:
            for ending, replacement in ordinal_endings:
                if word.endswith(ending) and word in thwords:
                    word = "%s%s" % (word[:-len(ending)], replacement)

            if word not in numwords:
                if onnumber:
                    curstring += repr(result + current) + " "
                if word.isnumeric() and w!=len(wstring)-1 and wstring[w+1] == "hundredths":
                    curstring += str(round(float(word) * 0.01, 2)) + " "
                    result = current = 0
                    onnumber = False
                else:
                    curstring += word + " "
                    result = current = 0
                    onnumber = False
            else:
                scale, increment = numwords[word]

                current = current * scale + increment
                if scale > 100:
                    result += current
                    current = 0
                onnumber = True

    if onnumber:
        curstring += repr(result + current)

    return curstring

'''
the chunks() function is used to iterate through a list of rows in the buildtable functions
'''

def chunks(s, n):
    for start in range(0, len(s), n):
        yield s[start:start + n]

'''
the resdis function determines what fraction of residential districts allow multifamily housing by-right. It does
so by searching the input string for a series of regex expressions contained in trigger_words_s. For each regex match, 
the function searches the surrounding text for indications of single family, two-family, multifamily, or mixed use
designations. The process necessarily entails checks for false-positive matches through stopwords and similar checks.
The output is a fraction, which indicates the number of matched residential districts determined as allowing multifamily
uses by right over all matched residential districts.
'''

def resdis(input):

    ## regex to capture universe of residential or residential mixed-use districts ##

    trigger_words_s = r"""(?x)          # Turn on free spacing mode
                      (?<!^)
                      \b(
                      (?<!r\-\d+\s|any\s|each\s|all\s|r\-\d+[a-z]\s|classification\sof\s|said\s|r\-[a-z]\s|r\-\d+\s)single\sfamily\sresidence\sdistrict(?!\.\samended|\sregulations|\.\sart)|
                      duplex\sresidence\sdistrict|sfrt|
                      multiple\sresidence\sdistrict|res\-\d+|
                      r\-\d+\-\d+(?!\s\d+\-\d+\-\d+)|r\-\d+\-[a-z]{1}|(?<!\d+\s\d+|or\s)r\-\d+\.\d+|
                      ^(?!(?:zoning)$)[a-z]+\-r\-\d+[a-z]*|(?<!pvc\s|day\scare\s|village\s|drawings\s\(|along\s|or\s)[a-z]+r\-\d+(?!\-[a-z]\s\(light\sindustrial|\sfeet|\sor|\s[a-z]+\shydrology|\spvc|\s\(general\soffice)|(?<!res\/)ag|ae|rhd|re\-\d+[a-z]*|
                      r\d\-\d+|gr\-\d+[a-z]*|(?<!along\s|or\s)sr\-\d+(?!\sor)|ra\s\d+\-\[a-z]+|ra\s\d+|rb\s\d+|(?<!ac\/)ah\-*\d*|ga\-\d+|
                      (?<!two\-family\sdwelling\s|\d+\s|of\s)th(?!\s+townhome|\sdetermination|\sstreet)|rco|(?<!drawings\s\()r[a-z]{1}\-\d+(?!\splanned\sbusiness)|orc(?!\s\d+\.\d+)|rcd(?!\snct)|rcm|
                      ra|re\d+|rt\d+|rp\-\d+|r\-\d+mh|m\-u\-\d+|r\-m\-\d+|r\-md\-sz|md\-\d+|r\-hd\-sz|rd\-\d+\.*\d*|rp|(?<!\-)gr|su|1f\-\d+|
                      (?<!structu\s)re(?!\-|\sdetermined|\sprocessing|\sthe\sadoption|~|\sar\s|downtown\s)|rd(?!\s\.so\.|\sseries|\.|\stable)|rg\d|rl|rms(?!\s\/\sacre)|rmm|(?<!pipe\s\()rcp|rc(?!\-\d+|\-)|ro(?!\-\d+|\-)|
                      rnc|tld|tmd|thd|(?<!overriding\s|machines\s|p\-)cd(?!\splayer)|rmf\-\d+\.*\d*|rmf\-\.\d+|rmf|rmh|
                      r\-\d+\-e|rm\-*\d+\.*\d*|rm\-*[a-z]+(?!\s\/\sacre)|rm\-\d+|(?<!document\s|revision\sof\s|\sdistricts|under\s|to\s|with\s|per\s|subdivision\sdeterminations\s\(|see\snh\s|defined\sin\s|require\sof\s)rs\-*\w+(?!\srst)|
                      ^(?!r)(?<!\()r(?!\.|\)|$)|srr|rr(?!\.\-|\)\sresidential\sunit)|rh(?!\sand\sand\srm\sdistricts)|ru\-\d+|rsh\-*\w*|src|srl|srh|rl\d+|rh\d+|r\:\d+|
                      (?<!previously\s|side\sof\s|east\s|north\s|south\s|west\s|at\s\d+\s|\-)sr(?!\.|\s\d+\.|\s\d+\sstate|\-|\s\d+\s\([a-z]\)|\s\(special|\sresidential\suses|\d+\))|
                      (?<!attached\s|safety\s\()fr(?!\s\d+\s\d+\sat)|rx\-|sfr\-w+|sfr(?!\s\|\sduplex|\sconstruction)|mhr|vldr|tn\-ldr|tn\-mdr|mcn\-ldr|mcn\-mdr|mon\-ldr|mon\-mdr|(?<!\-)ldr(?!\sand|\)\sdistricts)|sfa|url|
                      (?<!c\:|freon\:\s|r\d+\-|mn\s|boundary\sof\s|parcel\s)r\d+\-*[a-z]{1}(?!\d|\.|\sbhm)|
                      ar\-\d+|sf\-\d+|sf\-[a-z]|2f\-[a-z]|mf\-[a-z]|r\/c|ot\-mf|ot\-sf|nr\d+|lr\d+|smu\-slu|sm\-[a-z]{1,2}|nc\d+|
                      mf\-\d+|rm|(?<!tax\smap\s|freon\:\s|r\d+\-|mn\s|group\s|boundary\sof\s|parcel\s)r\d+(?!\/c|\.\d)|
                      (?<!r\-\d+\sand\s|group\s|and\stownhouse\sdistrict\s|and\stownhouse\sresidential\s\(|non\-|\-)r\-\d+[a-z]*(?!\-|\.|\soccupancy|\soccupancies|\svalue|\s\d+\-\d+\-\d+|of\sthe\s[a-z]+\sadministrative|\sand\/or)|(?<!\-|or\s)r\-\d(?!\-|\.|\soccupancy|\soccupancies|\sand\/or|\sor\sr\-\d\soccupancy|\sand\sr\-\d\soccupancies|\sprior\sto)|
                      (?<!r\-\d+\sand\s|group\s|and\stownhouse\sdistrict\s|and\stownhouse\sresidential\s\()r\-[a-z]{1,5}(?!\-|\d|\svalue)|
                      os\-[a-z]+|otr|smf|emf|mmf|hr|mf\d+|(?<!\-)mf|tf|mp|sn|rcr|ora|ira|slo|llrd|ldd|\-r\-\d\-|ld\-r|md\-r|mhd\-r|hd\-r|
                      (?<!document\s|revision\sof\s)rs|lrr|lr\-\d+[a-z]{1}|lr(?!\s\(local\sretail|\sc|\slocal\sretail)|ur\-ld|ur\-md|ur\-hd|ur|ovr|vr\-mf|vr|hrc|hr|mmh|scmxd|mxd|ru|rf|mxr|
                      s\-\.\d{1}|r\-\.\d{1}|h\-\d\-\d+|nc(?!\sor\smixed\suse\sdistrict)|tn\d+|t\-\d+[a-z]{1,2}|t\d+(?!\sn\s|\)\soccupancy\spermit)|
                      mhp|rmo|rso|rsf|rlm\-\d+|rlm|r\-ld|r\-mf|(?<!v)r\-mf|sf\d+|rm[a-z]{1}(?!\s\/\sacre)|murzd|mu\-r\-\d\-[a-z]|
                      mh\-\d+|mh|(?<!\-)mdr(?!\sand)|(?<!designation\sof\shigh\sdensity\sresidential\s\()hdr|dmu|(?<!pd\-|c\-|mixed\suse\s|mixed\-use\s|\-)mu(?!\-li|\-ar)|(?<!construction\spermit\s)mn(?!\/dot|\.)|tcmu|pdm|
                      tr(?!\-)|lhc|lha|rb(?!\sbusiness)|oh|rth|arzd|rzd|vzd|dm\-\d+|ul\-\d+|um\-\d+|uh\-\d+|
                      (?<!commercial\s\()mc(?!\-\d+|\soffice|\ssingle\-use|\smulti\-use|\s\)\smajor\scollector)|
                      mr|ns(?!\save|\.)|nu|(?<!ed\(|red\-|\-)mx\-*\d*|(?<!downtown\sdistrict\s\()dd\-\d+(?!\s\-\sdowntown)|dd(?!\.\-|\-\d+)|
                      (?<![a-z]{1}\.\s|\-|as\s|or\s|grades\s|application\sfrom\s|containing\san\s|editor\'s\snote\-\s|from\s|inst\s|districts\s|lbd\s|m\-\d+\sand\s|combined\swith\s|setbacks\sin\s|within\sthe\s|watershed\s|table\s|\(\w+\)\s|requested\s|non\-|located\sin\sthe\s|by\s|appendix\s|district\s\(|commercial\s\(|to\s|located\sin\sany\s|industrial\sdistrict\s|utah\s|road\sand\s|either\sclass\s|illustration\s|zoned\s|institutional\suse\s|see\s|et\sal\s|variance\s|\-\d+\s|[a-z]\-\d+\-\d+\sand\s|[a-z]+\-|exhibit\s|astm\s|appendix\sd\s|\.[a-z]\.\s|county\s|\([a-z]\.\s|appendix\sa\s\-\szoning\s|\slive|\sdistrict\:\slight|\'\d+\s|\([a-z].\s)[a-z]{1}\-\d+(?!\.\d|\:\sordinance|\sand\s[a-z]{1}\-\d+|\s[a-z]+\scommercial|of\sthe\s[a-z]\sadministrative|\sindustrial|\s[a-z]+\smanufacturing|\swholesale|\s[a-z]\-\d+|\smanufacturing|\soccupancies|\sprior|\soffice|\sfloodplain|\slight\sindustrial|\sneighborhood\sbusiness|\sbulk|\shighway|\svillage\scommercial|\set\sseq\.|\scoordinator|\spvc|\.[a-z]+|\sor|\soccupancy|\s[a-z]+\sbusiness|\sgeneral\sretail|\s\d\s\d\-\d+\-\d+|\-|\s\-\s[a-z]+\scommercial|\s\-\s[a-z]+\sbusiness|\sshopping\scenter|\s[a-z]+\smanufacturing|\sapp|\sand\scomplies|\sdoes\snot\sobstruct|\sheavy|\-|\d\s\d+\-\d+\-\d+|\s\-\s\d+\-\d+\-\d+|\s\d+\-\d+\-\d+|\s\-\s\d+\.\d+|\s\-\s\d\s\d+\-\d+\-\d+|\s\-\s+\d+\-\d+\-\d+|\sand\/or|\ssiding|\s[a-z]+\sflood|\soccupancy|\soccupancies|\spavement|\scommercial|\s[a-z]+\sshopping|\s\d+\.|\sbusiness|\s\([a-z]+\sbusiness|\sindustry|\.|\sand|\sthrough|\sor\s[a-z]{1}\-\d+|\s\(\w+\)\sretail|\sconditionally|\soccupancies|\soccupany|\spassed|\sreviews|\sthe\s[a-z]{1}\-\d+|\s[a-z]+\sretail|\s[a-z]+]scommercial|\-*\sgeneral\sbusiness|\s\d+\scbdd|\s[a-z]+\scbdd|\s[a-z]*\sindustrial|\s\-\s[a-z]+\smanufacturing|\ssubdivision|\sfence|\srental\shousing\slicense)|
                      (?<!\-|adjacent\sto\s)[a-z]{1}\ssingle\sfamily\sdwelling\sdistrict|(?<!\-)[a-z]{1}\stwo\-family\sdwelling\sdistrict|
                      (?<!\-)[a-z]\smulti\sfamily\sdwelling\sdistrict|a\sapartment|os\d+|a\-a|e\d+[a-z]{1}|(?<!feet\s+)e[a-c]{1}(?!\.)|
                      (?<=garden\sapartment|garden\sapartment\sresidential\s|garden\sapartments|garden\sapartment\s\(|garden\sapartments\s\()ga|
                      office\/residential|crd|crd\-[a-z]{1}|residence\sa\-\d|residence\sc\-\d+|residence\se|residence\sf|
                      (?<!as\sa\s|family\s|\d+\s\d+\s|space\s|density\s)residential\s\d+(?!\s\([a-z]\d+\)|\s\d+|\-|\sper|\spercent|\sspace|\sacre|\sfeet|\sunit\sper|\.\d+|\scentral|\senvironmental)|
                      (?<!as\sa\s)residence\saaa|(?<!as\sa\s)residence\saa|(?<!as\sa\s|family\s)residence\sa|o\sresidential\suse\sdistrict|
                      (?<!as\sa\s)residence\sbb|(?<!as\sa\s)residence\sb|(?<!as\sa\s|gc\s|other\s|equestrian\soverlay\s|residential\s|rc\s|any\s)zone\s[a-z](?!\shauling|\sstructure)|
                      (?<!as\sa\s)residence\scc|(?<!as\sa\s)residence\sc|
                      (?<!as\sa\s)residence\sdd|(?<!as\sa\s)residence\sd|
                      (?<!as\sa\s)residence\see|(?<!as\sa\s)residence\sff|residence\sr(?!\-|\smulti\sfamily)|class\su\d+|
                      (?<!family\s)residential\sa|(?<!family\s)residential\sb|(?<!family\s)residential\sc(?!\.\snos)|residential\sd|(?<!family\s)residential\se|
                      ceod|un\-[a-z]{1}|ddh|mdrd|(?<!abutting\s)a+\ssingle\sfamily\sdistrict(?!\sor)|
                      (?<!or\s)duplex\sresidential\sdistrict|(?<![a-z]\-\d+\s)townhouse\sdistrict|low\-rise\sapartment\sdistrict|high\-rise\sapartment\sdistrict|
                      (?<!net\sresidential\sdensity\s\()nrd|rdd|ub|aho\-*\d*|rt(?!\.)|tr\s*\-\s*\d+|cr\s*\-\s*\d+|ce\s*\-\s*\d+|
                      (?<!director\s\()cdd|(?<!development\s\(|no\s)mfrd(?!\sproject)|mfr\-[a-z]|(?<!parking\sof\sautomobiles\s\(|golf\scourse\s|inn\s|commercial\s|commercial\srestricted\sdistrict\s)cr(?!\-\d+|\shealth\sclub|\sinstitutional|\scommercial|\srecreation)|
                      neighborhood\s\(n\)\s|urban\s\(u\)\s|outlying\svillage\sresidential|(?<!r\-\d+\-\w\s|r\-\d+\s|\-vr\/dc\-\s|\-vr\-mf\/dc\-\s|\-vr\-\d+\/dl\-\s)village\sresidential|
                      outlying\sresidential\-commercial(?!\s\d+\-\d+|\spermitted\sground)|(?<!r\-\w+\s|commercial\s|rc\s\(|mixed\-use\s\(|all\s|neighborhood\scommercial\sand\s|mixed\s)residential\-commercial(?!\szones|\s\(rc|\src)|(?<!r\-\d+\s|a\s|r\d+\s\-\s|r\-\w+\.\s|limit\s)general\sresidence\sdistrict|
                      (?<!as\sa\s|r\-\d+\s)residence\s\d\-[a-z]{1}\d*|(?<!as\sa\s|sale\sof\s)residence\s\d+(?!\-|\sspaces|\s\d+|\sfeet|\sper)|
                      (?<!r\-\d+\s|a\s)two\-acre\ssingle\sfamily\sdistrict|(?<!r\-\d+\s|a\s)one\-acre\ssingle\sfamily\sdistrict|(?<!r\-\d+\s|a\s)\d+\ssquare\sfoot\ssingle\sfamily|
                      (?<!r\-\d+\s|a\s)low\-rise\smulti\sfamily|(?<!r\-\d+\s|a\s)medium\-rise\smulti\sfamily|(?<!r\-\d+\s|a\s|single\s|one\s|two\s|multi\s|two\-|one\-)family\sdistrict(?!\s\d+\sper\sstreet)|
                      (?<!or\s)a\sresidence\sdistricts|(?<!or\s)b\sresidence\sdistricts|(?<!or\s)c\sresidence\sdistricts|
                      (?<!or\s)r\sresidential\sdistrict|(?<!residential\s|rural\s|business\s|community\s|family\s|historic\s|conservation\s|transportation\s|overlay\s|habitat\s|zoning\s|park\s|use\s|center\s|industrial\s|public\s|this\s|sub\-|signs\spermitted\sand\sprohibited\sby\s|lighting\s|university\s)district\s\d+(?!\.\d+|\sadded|\-\d+|\ssquare)|
                      (?<!or\s)a\sresidential\sdistricts|(?<!or\s)b\sresidential\sdistricts|apartment\sdwelling\sdistrict|
                      (?<!or\s)b\sresidential\sdistrict|(?<!or\s)c\sresidential\sdistrict|
                      (?<!r\-\d+\s|a\s)harbor\svillage\sdistrict|(?<!r\-\d+\s|a\s|r\-[a-z]+\s)traditional\svillage\sdistrict|(?<!r\-\d+\s|a\s|r\-[a-z]+\s|density\s)multiple\-dwelling\sdistrict|
                      (?<!r\-\d+\s|village\s|a\sr|\-[a-z]+\s)village\sdistrict|(?<![a-z]*\-\d+\s|r\-r\s|r\-[a-z]+\s|[a-z]+\-[a-z]{1}\s|r\d+\s|the\s|r\d+\s\-\s|r\-\d+\)\s|r[a-z]{1,3}\s|of\s|rr\-)rural\sresidential\sdistrict(?!\s\(r\-|\sr\-)|(?<!r\-\d+\s|a\s|r\-[a-z]+\s|r\-\d+\)\s|a\s|r[a-z]{1}\-*\d+\-+)general\sresidential\sdistrict|
                      (?<!r\-\d+\s|a\s|r\-[a-z]+\s|from\s|r[a-z]{1,3}\s\-\s|r[a-z]{1,3}\)\s|r[a-z]{1}\-\d+\)\s)rural\sdistrict(?!\sru\-\d+)|
                      (?<!r\-\d+\s|a\s|r\-[a-z]+\s|mdr\s|mdr\s\-\s|low\-|rmd\s\-\s|existing\s|district\s)medium\sdensity\sresidential\sdistrict(?!\smedium)|(?<!r\-\d+\s|a\sr\-[a-z]+\s)affordable\shousing\soverlay\szone|affordable\shousing\soverlay\sdistrict|
                      [a-z]{1}\smultiple\sdwelling\sdistrict|^(?!(?:a)$)[a-z]{1}\sdwelling\sdistrict|
                      (?<!r\-\d+\s|a\s)garden\sapartment\sdistrict|(?<!r\-\d+\s|a\s)residential\-general|
                      (?<!\-rr\-\s)rural\sresidential(?!\sdistrict|\districts|\suses)|t\sdistrict|r\sdistrict|mg\sdistrict|m\sdistrict|
                      (?<!ldr\s\-\s|neighborhood\-|neighborhood\s\-\s|of\s|into\s|each\s|ldr\s|to\s)low\-density\sresidential(?!\sdistrict|\districts|\suses|of\s|into\s|each\s|\suses|\sdesign|\sdevelopment|\sconstruction)|
                      (?<!neighborhood\-|neighborhood\s\-\s|of\s|into\s|each\s|to\s|for\s)medium\-density\sresidential(?!\sdistrict|\districts|\suses|\suses|\sdesign|\sdevelopment|\sconstruction)|
                      (?<!to\s|of\s|into\s|each\s)high\-density\sresidential(?!\sdistrict|\districts|\suses|\sdesign|\sdevelopment|\sconstruction)|
                      (?<!r\-\d+\s|r\.\s|\.|parkmerced\s|mixed\s|term\s|within\s|see\s|condominium\s|mur\s\-\s|predominantly\s|use\-|downtown\s|multi\-|interchange\s|such\s|specific\s|open\s|home\s|elderly\s|office\/|agricultural\-|agricultural\/|agricultural\s|of\s|compact\s|household\s|nearest\s|duplex\s|multiple\s|housing\s|weight\srestrictions\s+|district\:\s|entitled\s|to\s|park\s|not\s|from\s|protection\s|use\s|and\s|conservation\s\-\s|or\s|r\s|medium\s|apartment\s|qualified\s|intensity\s|restricted\s|special\s|limit\s|this\s|[a-z]\-[a-z]\s|building\s|restrictive\s|general\s|each\s|every\s|any\s\-r\-\s|any\s|family\s|any\s|all\s|a\s|village\s|citizen\s|r\d+\s|zoned\s|density\s|urban\s|one\s|the\s|adjoining\s|planned\s|non\-|said\s|new\s|rural\s|agricultural\s|adjacent\s|r\-\w+\s|r\-\s\d+|existing\s|residence\s|suburban\s)residential\sdistrict\sone(?!\sprovide|\sr\-|\sare|\sidentification|\smeans|\sdensity|\sor\suse|\sr\-\d+|\.|\sdevelopment|\srequire\s\.+|\srequire\s+agricultural\sresidential)|
                      (?<!r\-\d+\s|r\.\s|\.|parkmerced\s|mixed\s|term\s|within\s|see\s|condominium\s|mur\s\-\s|predominantly\s|use\-|downtown\s|multi\-|interchange\s|such\s|specific\s|open\s|home\s|elderly\s|office\/|agricultural\-|agricultural\/|agricultural\s|of\s|compact\s|household\s|nearest\s|duplex\s|multiple\s|housing\s|weight\srestrictions\s+|district\:\s|entitled\s|to\s|park\s|not\s|from\s|protection\s|use\s|and\s|conservation\s\-\s|or\s|r\s|medium\s|apartment\s|qualified\s|intensity\s|restricted\s|special\s|limit\s|this\s|[a-z]\-[a-z]\s|building\s|restrictive\s|general\s|each\s|every\s|any\s\-r\-\s|any\s|family\s|any\s|all\s|a\s|village\s|citizen\s|r\d+\s|zoned\s|density\s|urban\s|one\s|the\s|adjoining\s|planned\s|non\-|said\s|new\s|rural\s|agricultural\s|adjacent\s|r\-\w+\s|r\-\s\d+|existing\s|residence\s|suburban\s)residential\sdistrict\stwo(?!\sprovide|\sr\-|\sare|\sidentification|\smeans|\sdensity|\sor\suse|\sr\-\d+|\.|\sdevelopment|\srequire\s\.+|\srequire\s+agricultural\sresidential)|
                      (?<!r\-\d+\s|r\.\s|\.|parkmerced\s|mixed\s|term\s|within\s|see\s|condominium\s|mur\s\-\s|predominantly\s|use\-|downtown\s|multi\-|interchange\s|such\s|specific\s|open\s|home\s|elderly\s|office\/|agricultural\-|agricultural\/|agricultural\s|of\s|compact\s|household\s|nearest\s|duplex\s|multiple\s|housing\s|weight\srestrictions\s+|district\:\s|entitled\s|to\s|park\s|not\s|from\s|protection\s|use\s|and\s|conservation\s\-\s|or\s|r\s|medium\s|apartment\s|qualified\s|intensity\s|restricted\s|special\s|limit\s|this\s|[a-z]\-[a-z]\s|building\s|restrictive\s|general\s|each\s|every\s|any\s\-r\-\s|any\s|family\s|any\s|all\s|a\s|village\s|citizen\s|r\d+\s|zoned\s|density\s|urban\s|one\s|the\s|adjoining\s|planned\s|non\-|said\s|new\s|rural\s|agricultural\s|adjacent\s|r\-\w+\s|r\-\s\d+|existing\s|residence\s|suburban\s)residential\sdistrict(?!\sprovide|\sr\-|\sidentification|\sare|\smeans|\sdensity|\sor\suse|\sr\-\d+|\.|\sdevelopment|\srequire\s\.+|\srequire\s+agricultural\sresidential)|
                      (?<!r\-\d+\s|r\.\s|\.|parkmerced\s|mixed\s|term\s|within\s|see\s|condominium\s|mur\s\-\s|predominantly\s|use\-|downtown\s|multi\-|interchange\s|such\s|specific\s|open\s|home\s|elderly\s|office\/|agricultural\-|agricultural\/|agricultural\s|of\s|compact\s|household\s|nearest\s|duplex\s|multiple\s|housing\s|weight\srestrictions\s+|district\:\s|entitled\s|to\s|park\s|not\s|from\s|protection\s|use\s|and\s|conservation\s\-\s|or\s|r\s|medium\s|apartment\s|qualified\s|intensity\s|restricted\s|special\s|limit\s|this\s|[a-z]\-[a-z]\s|building\s|restrictive\s|general\s|each\s|every\s|any\s\-r\-\s|any\s|family\s|any\s|all\s|a\s|village\s|citizen\s|r\d+\s|zoned\s|density\s|urban\s|one\s|the\s|adjoining\s|planned\s|non\-|said\s|new\s|rural\s|agricultural\s|adjacent\s|r\-\w+\s|r\-\s\d+|existing\s|residence\s|suburban\s)residence\sdistrict(?!\sprovide|\sr\-|\sare|\smeans|\sdensity|\sor\suse|\sr\-\d+|\.|\sdevelopment|\srequire\s\.+|\srequire\s+agricultural\sresidential)|
                      (?<!\-|order\:\s|single\sand\s)two\-family\sresidence\sdistrict|[a-z]\sdwelling\sdistrict|e\sdwelling\sdistricts|
                      (?<!\-)multi\sfamily\sresidence\sdistrict(?!\sbusiness|\.\samended)                      
                      )\b(?!$)"""

    bad_words = r"""(?x)implemented\sadjacent\sto|this\ssection\sshall\snot\sapply|vacation\sof\sroads|
                    ornamental\sgrasses|laundry\sfacility|archaeological|residential\sdriveway\sapproach"""

    text_extracts = []

    inlist = stlist = list(deepflatten(input, 1))

    all_matches = []
    all_mappings = []

    for string in inlist:
        if re.findall(bad_words, string, flags=re.IGNORECASE):
            continue
        match = re.findall(trigger_words_s, string, flags=re.IGNORECASE)
        match_pos = [m.start(0) for m in re.finditer(trigger_words_s, string, flags=re.IGNORECASE)]
        all_matches.extend(re.findall(trigger_words_s, string, flags=re.IGNORECASE))

        #print("ALL MATCHES")
        #print(all_matches)

        smfmap = {}
        keys = 0

        sf_cut = r"""rs\-|s\-\.\d{1}\ssingle\sfamily|r\-\.|re\-|r\-1\-\d+|r1\-*\d*|estate|r\-1|sf\-\d+|one\-family|mf\-\d+|may\sserve\sas\sa\stransition"""
        mf_cut = r"""(?x)rm\-|r\-\.|mx|r\-m|\bh\-\d\b|\bh\-\d\-\d+|residence\-multi\sfamily|multiple\sdwelling|multiple\sresidence|
                         multi\sfamily|mf\-\d+|may\sserve\sas\sa\stransition|r\-3|r\-4|r\-5|r\-6|r\-7"""

        if match:
            keys = match
            for n, x in enumerate(keys):
                if re.findall(r"^(c\-|i)",x,flags=re.IGNORECASE):
                    continue
                mapping = ""

                if match_pos[n] < 1500:
                    clip_start = 0
                else:
                    clip_start = match_pos[n] - 1500
                if len(string[match_pos[n]:]) < 1500:
                    clip_end = len(string)
                else:
                    clip_end = match_pos[n] + 1500
                clip = string[clip_start:clip_end]
                if match_pos[n] -125 < 0:
                    clip_s_start = 0
                else:
                    clip_s_start = match_pos[n] - 125
                if match_pos[n] + 125 > len(string):
                    clip_s_stop = len(string)
                else:
                    clip_s_stop = match_pos[n] + 125
                clip_s = string[clip_s_start:clip_s_stop]
                bhits = 0
                fhits = 0
                clip_b = string[clip_start:match_pos[n]]
                clip_f = string[match_pos[n]:clip_end]

                if re.findall(trigger_words_s, clip_b, flags=re.IGNORECASE):
                    hits = re.findall(trigger_words_s, clip_b, flags=re.IGNORECASE)
                    if x in hits:
                        hits_fin = list(filter(lambda val: val != x, hits))
                    else:
                        hits_fin = hits
                    if len(hits_fin) > 0:
                        bhits = 1
                        if not re.findall(r'permitted\suses|uses\spermitted|is\sintended\sto\sprovide|following\sare\spermissive\suses|use\:|used\sfor\:|land\smay\sbe\sused|type\sof\sresidential\sunit\sminimum\slot\sarea|district\sis\sintended\sto|purpose\sof\sthis\sdistrict', clip_s, flags=re.IGNORECASE):
                            clip_start = match_pos[n] - 30
                        else:
                            clip_start = 0
                elif re.findall(r"zone\sdistricts\.", clip_b, flags=re.IGNORECASE):
                    clip_start = [m.start() for m in re.finditer(r"zone\sdistricts\.", clip_b, flags=re.IGNORECASE)][-1]
                else:
                    clip_start = 0
                if re.findall(trigger_words_s, clip_f, flags=re.IGNORECASE):
                   hits = re.findall(trigger_words_s, clip_f, flags=re.IGNORECASE)
                   if x in hits:
                       hits_fin = list(filter(lambda val: val != x, hits))
                   else:
                       hits_fin = hits
                   if len(hits_fin) > 0:
                       fhits = 1
                       if not re.findall(r'permitted\suses|uses\spermitted|is\sintended\sto\sprovide|are\sestablished\sresidential\sareas|following\sare\spermissive\suses|use\:(?!\slot\sarea)|used\sfor\:|land\smay\sbe\sused|permitted\snumber\sof\sdwelling\sunit|district\:|following\suses\sare\spermitted|district\sis\sintended\sto|purpose\sof\sthis\sdistrict', clip_s, flags=re.IGNORECASE):
                           clip_stop = [clip_f.find(m) for m in hits_fin][0]
                       else:
                           clip_stop = 2000
                   else:
                       clip_stop = 2000
                else:
                    clip_stop = 2000
                if (match_pos[n] + clip_stop > len(string)):
                    clip_fin = string[clip_start:len(string)]
                else:
                    clip_fin = string[clip_start:match_pos[n]+clip_stop]
                if bhits == 1:
                    clip_b_in = string[clip_start:match_pos[n]]
                    clip_b_rf = re.sub(r'\([^)]*\)','',clip_b_in)
                    if (match_pos[n] + clip_stop > len(string)):
                        clip_f_rf = string[match_pos[n]:len(string)]
                    else:
                        clip_f_rf = string[match_pos[n]:match_pos[n]+clip_stop]
                    clip_fin = clip_b_rf + clip_f_rf

                eflag = re.findall(r'((\D\d\s){2,})', clip_s, flags=re.IGNORECASE)
                flag_words2 = r"""(?x)r\d\s\-\sr\d|rr\s\-\sr\d|asphalt|annexation|annexations|
                                  boarding\shouses|planned\sdevelopment\sdistrict|pud|(?<!r)p\-\d+|
                                  uses\sin\sbusiness\spark\sdistrict|electronic|no\swireless\ssupport|
                                  \d+\.\d+\sparking\sof\sautomobiles|uses\sin\sthe\sbusiness\spark\sdistrict|
                                  \:\s\(\d\)\sall\suses\spermitted\sin\sthe\sresidential\sdistricts|institutional|
                                  area\sper\sdwelling\sunit|compost|escape\sroom|signplate|bar\sand\scafe|
                                  in\sthe\sbr\-1\sbusiness\sretail\szone|motor\svehicles\sfor\sa\sone\-family|
                                  shall\sbe\scity\scode|places\sof\sworship\:|electronic\smagnetic\sforce|antennas|
                                  number\sof\saccessory\sstructures\stotal\smaximum\saccessory\sstructure|manufacturing|
                                  access\spoints|r\-\d+\sr\-\d+\sand\sr\-\d+\sresidential\szoning\sdistricts|
                                  sexually\soriented\sbusinesses|height\slimitations\.|airport\ssafety|
                                  maximum\sbuilding\sheight\.|adjustment\sto\syard\sregulations|earthen\sberms|
                                  subject\sto\sissue\sof\sa\sconditional\suse\spermit|public\sand\squasi\-public|
                                  service\scommercial|zone\sdistrict\supon\swhich|production\sand\sextraction|
                                  flood\splain\sdistrict\ssee\sfor\sdelineation|commercial\sdevelopment\srequire|
                                  general\scommercial\sdistrict\sis\sabbreviated|office\sfacilities|teardrop\sbanners|
                                  zero\slot\sline\sdwelling\sdescribed\sin\ssubsection\s\(\d\)\sshall\sbe\spermitted\suses|
                                  intended\sto\sallow\sfor\soffice\sentertainment|special\spermit\suses|signage|
                                  cemetery\szone|parking\sspace\sper\sunit\.|golf\scourse|supermarkets|light\sindustry|
                                  distilled\sspirits|principal\suse\sadvertising|reduced\sstorage\sand\sparking\sof\svehicles|
                                  no\sequipment\sshall\sbe\sparked\sor\sstored\sin\san\sopen\sparking\sspace|amends\sby|
                                  airport\soverlay\sdistrict|highway\scommercial\sdistrict|following\sare\sconditional\suses|
                                  areas\snot\spreviously\szoned\sshall\sbe\sclassified|special\sflood\shazard\sareas|
                                  if\san\sappropriate\spermanent\sscreening\sdevice|public\ssafety\sservices|
                                  cluster\sdevelopment\sby\sright|other\sdimensional\scriteria\sof\sa\ssimilar\spermitted\suse|
                                  utility\srequire|cluster\sdevelopments|noise\slevels|domestic\semployees|from\scom|
                                  maintenance\sor\sstorage\sbuilding|string\slights|boardinghouse|pollution\ssource|
                                  any\sland\suse\swith\san\sactivity|insulating\sfinish|antique\sshop|office\sretail|
                                  commercial\/service\sbuilding|large\sscale\sretail\sestablishments|stormwater\srunoff|
                                  require\sissue\sof\sa\sconditional\suse\spermit|small\-scale\ssatellite|tanks|
                                  r\-\d+\ssingle\sfamily\sand\sr\-\d+\sgeneral\sresidence|billboard|funeral\shomes|
                                  in\sa\splanned\sresidential\sdevelopment\:|religious|special\sexception\suses\.|
                                  all\sother\suses\sand\szoning\sdistricts\sshall\scomply|such\sbusiness|parking\slot|
                                  minimum\sfloor\sarea|following\ssigns\sare\spermitted|authorize\sas\sa\sspecial\sexception|
                                  subtracting\sall\sor\sportions\sof\sthe\sland\sin\sthe\sfollowing\scategories\:|
                                  shall\sbe\sno\smore\sthan\s\d+\sattached\sdwelling\sunit\son\sa\stownhouse\sdevelopment|
                                  developers\sshall\shave\sno\smore\sthan\s\d+\spercent\sof\sthe\sr\-2|nonconforming\ssigns|
                                  district\sshould\sgenerally\shave\sdirect\saccess\sfrom\sa\smajor\shighway|nonconformities\:|
                                  permitted\sby\sspecial\sexception|basic\sutility|accessory\suses\sand\sstructures\:|
                                  food\svendor|regional\scommercial|unloading\sof\svehicles|deleted\sdefinitions|
                                  (?<!permitted\suses\s+)conditional\suses(?!\s\d+\-\d+\-\d+|\.\s\-+\s\-+development\sstandards\.)|
                                  require\sfront\sand\sside\syards\sshall\sbe\slandscaped|landscaping\s\:|on\sany\sfee\-simple\slot|
                                  as\sregulated\sby\saccessory\sprivate\sswimming\spools|permitted\ssigns\stotaling|
                                  telephone\sexchanges|continue\sto\sbe\spermitted\sin\sthose\srespective\sdistricts|
                                  major\sshopping|automobile\sservice|containing\sless\sthan\s\d+\ssquare\sfeet\sof\sgross\sfloor\sarea|
                                  private\shydrants\s\(addition\)\:|accessory\suses\:|sign\srequire|special\sexceptions(?!\srequire)|
                                  conditional\suse\spermit\sfor\sthe\sfollowing\suses|pay\sin\slieu|day\-care|research|
                                  (?<!should\snot\sbe\sspotted\swith\scommercial\sand\s)industrial\suse|feet\sto\sgarages|
                                  time\ssound\slevel|landscaping\srequire|medical\sdental|light\sintensity\soffice|special\suses\.|
                                  professional\soffices|brewery|educational\sbuildings|industrial\sdistrict\:|police\sand\sfire|
                                  bed\sand\sbreakfast\sestablishment\sshall|hospitals|manufacturing|vehicles\sper\sdwelling\sunit|
                                  unless\sthe\schange\sis\sin\sconformance|auto\sparking.|annexed\sto\sthe\stown\sshall|
                                  other\suses\snot\slisted|uses\srequire\sa\sspecial\spermit|not\sprovide\sstorage\sfor\smore\sthan\sone\svehicle|
                                  retail\spersonal\sor\srepair\sservice\sestablishments\sthat|industrial\snoise"""
                alldis = re.findall(trigger_words_s, clip_s, flags=re.IGNORECASE)
                othdis = list(filter(lambda val: val != x, alldis))
                othdis_un = list(dict.fromkeys(othdis))

                if eflag:
                    continue
                if (len(othdis_un) >= 3 and bhits == 0 and fhits == 0) or (re.findall(flag_words2, clip_s, flags=re.IGNORECASE) and len(othdis_un) < 3):
                    flags = re.findall(flag_words2, clip_s, flags=re.IGNORECASE)
                    continue
                if re.findall(r"\$", clip_s, flags=re.IGNORECASE) and not re.findall(r"fine\snot\sexceeding", clip_s, flags=re.IGNORECASE):
                    continue
                if re.findall(r"""(?x)((p\s){4,})|((x\s){4,})|((n\/a\s){4,})|lot\smust\sbe\sin\sseparate\sownership\sincluded\sin\sa\ssubdivision\sof\srecord|any\ssingle\slegal\slot\sof\srecord|
                                  dwellings\sin\sthe\srelevant\szoning\sdistrict|junk\svehicles\sparked|supermarkets|amusement\sgame|window\ssignage|prior\sto\sre\-development|
                                 minimum\sdistance\sfrom\sany\sresidential\sdistrict\sor\suse|included\sin\sa\splanned\sresidential\sdevelopment\:|
                                 multi\sfamily\sdwelling\sunit\sare\sproposed|by\s+signs\sin\sthe|
                                 (?<!subject\sto\sthe\sprovides\sof\s[a-z]+\s)public\slibrary|townhouses\-+general\srequire|
                                 brick\sveneer|zoned\sfor\sbusiness\sor\sindustrial\spurposes|fee\-simple\slot\sin\sthe|
                                 current\sassessed\svalue\sas\sdetermined\sby\sthe\svillage\sassessor|massage\stherapists|
                                 used\sfor\sthe\scalculation|ambient\snoise\slevel|christmas\stree\shill|
                                 space\scontrolled\sby\sa\smedical\sservice|acupuncture|odor\sfumes|warehouse\sadded|
                                 service\-oriented\suses\.|industrial\sdistrict\sheight|\d+\.jpg|lighting\szone\sdescriptions|
                                 sign\sidentifying\seach\spublic\sentrance\sto\sa\ssubdivision\sor\smulti\sfamily\sdevelopment|
                                 billboards\sor\sposter\spanels\sshall\sbe\sso\sdesigned""", clip_fin, flags=re.IGNORECASE):
                    continue
                if re.findall(r'tables\sbelow\sexplain|lot\syard\sand\sheight\srequire\sfor\ssingle|for\spurposes\sof\sthis\stable|blank\s\-\suse\sprohibited|table\sof\suse\sregulations\soverlay\sdistricts|special\spermit\snp\s+not\spermitted|multi\sfamily\:\sna\s', clip_fin, flags=re.IGNORECASE):
                    continue
                if len(re.findall(r"road|avenue|street(\snumbers)|drive|route|north|east|west|south|collector|arterial", clip_fin, flags=re.IGNORECASE)) > 6:
                    continue
                if re.findall(r"""(?x)same\sas\s|any\suse\spermitted\sin\sthe\s|than\sis\sthe\s|all\suses\spermitted\sin\s|one\sof\swhich\smust\sbe\sthe\s|
                              shall\snot\sbe\sapplied\sto\sany\ssite\swith\sa\s|prior\selimination\sfrom\szoning\sordinance\sof\sthe\s|
                              when\sadjacent\sto\s|where\ssuch\splot\sadjoins\sa\splot\sin\sthe\s|here\ssuch\splot\sadjoins\sa\splot\sin\sa\s|
                              any\suse\sother\sthan\sthose\suses\spermitted\sin\s|any\suse\spermitted\sin\s|
                              on\sthe\ssame\sside\sof\sthe\sstreet\sto\san|adjacent\sto\san\s|abutting\san\s""", clip_fin, flags=re.IGNORECASE):
                    if re.findall(r"(?:same\sas\s|prior\selimination\sfrom\szoning\sordinance\sof\sthe\s|fee\-simple\slot\sin\sthe\s|same\sas\sspecified\sin\sthe\s)" + re.escape(x), clip_fin, flags=re.IGNORECASE):
                        continue
                    elif re.findall(r"(?:any\suse\spermitted\sin\sthe\s|one\sof\swhich\smust\sbe\sthe\s|shall\snot\sbe\sapplied\sto\sany\ssite\swith\sa\s)" + re.escape(x), clip_fin, flags=re.IGNORECASE):
                        continue
                    elif re.findall(r"(?:than\sis\sthe\s|when\sadjacent\sto\s|where\ssuch\splot\sadjoins\sa\splot\sin\sthe\s|here\ssuch\splot\sadjoins\sa\splot\sin\sa\s|on\sthe\ssame\sside\sof\sthe\sstreet\sto\san\s|adjacent\sto\san\s|abutting\san\s)" + re.escape(x), clip_fin, flags=re.IGNORECASE):
                        continue
                    elif re.findall(r"(?:all\suses\spermitted\sin\s|except\s|any\suse\sother\sthan\sthose\suses\spermitted\sin\sa\s|any\suse\spermitted\sin\s)" + re.escape(x), clip_fin, flags=re.IGNORECASE):
                        continue
                if re.findall(r"(?:uses\spermitted\sin\sthe\s|all\spermitted\suses\sin\sthe\s|uses\spermitted\sin\s|same\sas\sthose\sin\sthe\s|uses\spermitted\soutright\sin\sthe\s)" + re.escape(x) + r"(?=\s\sdistricts(?!\sshall\sbe\sas\sfollows)|\sdistrict(?!\sshall\sbe\sas\sfollows)|\sresidence\sdistrict(?!\sshall\sbe\sas\sfollows)|\szone(?!\sshall\sbe\sas\sfollows))", clip_s, flags=re.IGNORECASE) or re.findall(re.escape(x) + r"\slisted\sin", clip_s, flags=re.IGNORECASE):
                    continue
                if len(list(dict.fromkeys(re.findall(trigger_words_s, clip_s, flags=re.IGNORECASE)))) > 1 and re.findall(r"frontage\:\s\d+\sfeet\s\d+\sfeet", clip_s, flags=re.IGNORECASE):
                    continue
                if match_pos[n] >= len(string) -35 or match_pos[n] <= 35:
                    continue
                if len(re.findall(r"district\sis\sabbreviated", clip_fin, flags=re.IGNORECASE)) > 3:
                    continue
                sf_hits = r"""(?x)(?<!require\slot\sarea\sand\swidth\sfor\sa\sdetached\s|compatible\swith\s|accessory\sto\s|detached\s|abuts\sa\slot\sin\sa\s|across\san\salley\sfrom\sa\slot\sin\sa\s|both\scommercial\sand\s)single\sfamily(?!\sand\smultiple\sdwelling)|
                              1\sfamily\sdetached|single\shousehold|(?<!at\sleast\s)one\sdwelling\sunit|one\sfamily|
                              (?<!\d+\.\s|rr\s|rr\-\w{1}\s)rural(?!\skings|\scharacter)|one\-family|single\sresidence|estates|(?<!real\s|r\-\d+\sresidential\s)estate|
                              single\-unit|single\-dwelling|(?<!require\slot\sarea\sand\swidth\sfor\sa\s|garages\s|restrictions\sagainst\sconstruction\sof\s)detached(?!\sgarages|\saccessory)"""
                mf_hits = r"""(?x)(?<!except\s)multiple\sfamily(?!\sresidence\snot\spermitted|\sdwellings\sconditional\suse)|
                              (?<!instances\sof\s|instances\sof\stwo\-family\sand\s|except\s|conditional\suse\sreview\sexempt\suses\s\(see\s\)\s|conditional\suse\sreview\sexempt\suses\s\(see\s\)\sdwelling\s|other\sthan\s|\d+\.\-+)multi\sfamily(?!\sresidence\snot\spermitted|\sdwellings\sconditional\suse|\sdwellings\swith\ssite\splan\sapprove|\sdwellings\sare\snot\sa\spermitted\suse|\s*residential\suses\sshall\sbe\sallowed\sas\sspecial\sexception|\sunit\ssize\sin\scommercial\szones)|
                              (?<!in\sthe\scase\sof\sa\s)multiple\sdwelling(?!\sdwellings\sconditional\suse)|multi\-tenant|
                              senior\scomplex|(?<!bike\s|open\sspace\strail\s)senior\shousing|four\-plex|fourplex|
                              multiple\sresidence|(?<!accessory\s|incompatible\sdevelopment\ssuch\sas\s)apartments|multiple\-dwelling|
                              (?<!accessory\s|incompatible\sdevelopment\ssuch\sas\s|first\sfloor\s+of\san\s)apartment(?!\scan\sbe\sintegrated\sback\sinto\sthe|\shotel)|
                              multiple\-residential|multiple\sresidential|multi\-unit|multi\sunit|high\-rise|high\srise|four\sfamily|
                              (?<!part\sof\sa\s)multi\-household|garden\sapt\.|rental\saccommodations|
                              multi\-dwelling|rental\shousing"""
                mx_hits = r'(?<!hereby\sestablished\sin\s|institutional\)\s|\d+\s|new\s)mixed(?!\suse\-i|\suse\sany|\s\(vm|\suse\sb\-1|\suse\ssigns)|(?<!hereby\sestablished\sin\s|new\s)mixed\-use(?!\so\-i|\sinstitutional\sany)'
                tf_hits = r"""(?x)(?<!instances\sof\s)two\sfamily(?!\sand\smulti\sfamily)|(?<!instances\sof\s)2\-family(?!\sand\smulti\sfamily)|
                              (?<!instances\sof\s)2\sfamily(?!\sand\smulti\sfamily)|two\s\(2\)\sfamily|twofamily|
                              (?<!instances\sof\s)two\-family(?!\sand\smulti\sfamily)|duplex(?!\sand\sapartment)|1\sand\s2family|
                              rowhouse|rowhouses|rowhome|rowhomes|townshouses(?!\sare\sconditional)|townshouse(?!s)|townhome|townhomes"""

                mfex = r"""(?x)multi\sfamily\sdwellings\sare\screated\sonly\swithin\sexisting\sresidential\sstructure|
                       apartment\shouses\sboardinghouses\sand\sother\smultiple\sdwellings\sas\swell\sas\scommercial\sand\sindustrial\suses\sare\snot\spermitted|
                       the\svarious\szones\sare\sdesigned\sto\saccommodate\sspecific\stypes\sof\sliving\ssituations\ssuch\sas\ssingle\sfamily\sand\smulti\sfamily\shousing|
                       multi\sfamily\sdwellings\s\(with\sthe\sexception\sof\sapprove\sbasement\sapartments\sas\sdefined\swithin\sof\sthis\s\)\scommercial\sand\sindustrial\suse\sareas\sare\sstrictly\sprohibited"""

                if re.findall(sf_hits, clip_fin, flags=re.IGNORECASE):
                    tword1 = re.findall(sf_hits, clip_fin, flags=re.IGNORECASE)
                    tword2 = re.findall(sf_hits, string, flags=re.IGNORECASE)
                    tpositions = [m.start(0) for m in re.finditer(sf_hits, string, flags=re.IGNORECASE)]
                    tword1.reverse()
                    tword2.reverse()
                    tpositions.reverse()
                    if len(tword2) != len(set(tword2)):
                        dup = [item for item, count in collections.Counter(tword2).items() if count > 1]
                        for d in dup:
                            dupspots = []
                            dupspots.extend([idx for idx, item in enumerate(tword2) if item == d and item in tword2[:idx]])
                            dupspots.append(tword2.index(d))
                            pdists = []
                            for dd in dupspots:
                                pdists.append(abs(tpositions[dd] - match_pos[n]))
                            pkeep = pdists.index(min(pdists))
                            dupspots.pop(pkeep)
                            for idx in sorted(dupspots, reverse=True):
                                del tpositions[idx]
                                del tword2[idx]
                    twdict = {tword2[i]: tpositions[i] for i in range(len(tword2))}
                    tword = [i for i in tword2 if i in tword1]
                    tpositions_f = []
                    for t in tword:
                        tinput = twdict[t]
                        tpositions_f.append(tinput)
                    res_sf = []
                    if tword:
                        for t, tnum in enumerate(tword):
                            tpos = tpositions_f[t]
                            if tpos < match_pos[n]:
                                dist_sf = abs(tpos - match_pos[n] + len(tnum))
                            else:
                                dist_sf = abs(tpos - match_pos[n] - len(x))
                            res_sf.append(dist_sf)
                        dist_sf = min(res_sf)
                else:
                    dist_sf = 9999
                if re.findall(mf_hits, clip_fin, flags=re.IGNORECASE):
                    tword1 = re.findall(mf_hits, clip_fin, flags=re.IGNORECASE)
                    tword2 = re.findall(mf_hits, string, flags=re.IGNORECASE)
                    tpositions = [m.start(0) for m in re.finditer(mf_hits, string, flags=re.IGNORECASE)]
                    tword1.reverse()
                    tword2.reverse()
                    tpositions.reverse()
                    if len(tword2) != len(set(tword2)):
                        dup = [item for item, count in collections.Counter(tword2).items() if count > 1]
                        for d in dup:
                            dupspots = []
                            dupspots.extend([idx for idx, item in enumerate(tword2) if item == d and item in tword2[:idx]])
                            dupspots.append(tword2.index(d))
                            pdists = []
                            for dd in dupspots:
                                pdists.append(abs(tpositions[dd] - match_pos[n]))
                            pkeep = pdists.index(min(pdists))
                            dupspots.pop(pkeep)
                            for idx in sorted(dupspots, reverse=True):
                                del tpositions[idx]
                                del tword2[idx]
                    twdict = {tword2[i]: tpositions[i] for i in range(len(tword2))}
                    tword = [i for i in tword2 if i in tword1]
                    tpositions_f = []
                    for t in tword:
                        tinput = twdict[t]
                        tpositions_f.append(tinput)
                    res_mf = []
                    if tword:
                        for t, tnum in enumerate(tword):
                            tpos = tpositions_f[t]
                            if tpos < match_pos[n]:
                                dist_mf = abs(tpos - match_pos[n] + len(tnum))
                            else:
                                dist_mf = abs(tpos - match_pos[n] - len(x))
                            res_mf.append(dist_mf)
                        dist_mf = min(res_mf)
                else:
                    dist_mf = 9999
                if re.findall(mx_hits, clip_fin, flags=re.IGNORECASE):
                    tword1 = re.findall(mx_hits, clip_fin, flags=re.IGNORECASE)
                    tword2 = re.findall(mx_hits, string, flags=re.IGNORECASE)
                    tpositions = [m.start(0) for m in re.finditer(mx_hits, string, flags=re.IGNORECASE)]
                    tword1.reverse()
                    tword2.reverse()
                    tpositions.reverse()
                    if len(tword2) != len(set(tword2)):
                        dup = [item for item, count in collections.Counter(tword2).items() if count > 1]
                        for d in dup:
                            dupspots = []
                            dupspots.extend([idx for idx, item in enumerate(tword2) if item == d and item in tword2[:idx]])
                            dupspots.append(tword2.index(d))
                            pdists = []
                            for dd in dupspots:
                                pdists.append(abs(tpositions[dd] - match_pos[n]))
                            pkeep = pdists.index(min(pdists))
                            dupspots.pop(pkeep)
                            for idx in sorted(dupspots, reverse=True):
                                del tpositions[idx]
                                del tword2[idx]
                    twdict = {tword2[i]: tpositions[i] for i in range(len(tword2))}
                    tword = [i for i in tword2 if i in tword1]
                    tpositions_f = []
                    for t in tword:
                        tinput = twdict[t]
                        tpositions_f.append(tinput)
                    res_mx = []
                    if tword:
                        for t, tnum in enumerate(tword):
                            tpos = tpositions_f[t]
                            if tpos < match_pos[n]:
                                dist_mx = abs(tpos - match_pos[n] + len(tnum))
                            else:
                                dist_mx = abs(tpos - match_pos[n] - len(x))
                            res_mx.append(dist_mx)
                        dist_mx = min(res_mx)
                else:
                    dist_mx = 9999
                if re.findall(tf_hits, clip_fin, flags=re.IGNORECASE):
                    tword1 = re.findall(tf_hits, clip_fin, flags=re.IGNORECASE)
                    tword2 = re.findall(tf_hits, string, flags=re.IGNORECASE)
                    tpositions = [m.start(0) for m in re.finditer(tf_hits, string, flags=re.IGNORECASE)]
                    tword1.reverse()
                    tword2.reverse()
                    tpositions.reverse()
                    if len(tword2) != len(set(tword2)):
                        dup = [item for item, count in collections.Counter(tword2).items() if count > 1]
                        for d in dup:
                            dupspots = []
                            dupspots.extend([idx for idx, item in enumerate(tword2) if item == d and item in tword2[:idx]])
                            dupspots.append(tword2.index(d))
                            pdists = []
                            for dd in dupspots:
                                pdists.append(abs(tpositions[dd] - match_pos[n]))
                            pkeep = pdists.index(min(pdists))
                            dupspots.pop(pkeep)
                            for idx in sorted(dupspots, reverse=True):
                                del tpositions[idx]
                                del tword2[idx]
                    twdict = {tword2[i]: tpositions[i] for i in range(len(tword2))}
                    tword = [i for i in tword2 if i in tword1]
                    tpositions_f = []
                    for t in tword:
                        tinput = twdict[t]
                        tpositions_f.append(tinput)
                    res_tf = []
                    if tword:
                        for t, tnum in enumerate(tword):
                            tpos = tpositions_f[t]
                            if tpos < match_pos[n]:
                                dist_tf = abs(tpos - match_pos[n] + len(tnum))
                            else:
                                dist_tf = abs(tpos - match_pos[n] - len(x))
                            res_tf.append(dist_tf)
                        dist_tf = min(res_tf)
                else:
                    dist_tf = 9999
                dists = [dist_sf,dist_mf,dist_mx,dist_tf]
                dist_dict = {0: 'sf',
                             1: 'mf',
                             2: 'mx',
                             3: 'tf'}
                trigwords = re.findall(trigger_words_s, clip_fin, flags=re.IGNORECASE)
                trigpos = [m.start(0) for m in re.finditer(trigger_words_s, clip_fin, flags=re.IGNORECASE)]
                allreldis = []
                for q, r in enumerate(trigpos):
                    if q != len(trigpos) - 1:
                        reldis = trigpos[q + 1] - trigpos[q]
                        allreldis.append(reldis)
                if min(dists) == 9999 and re.findall(r'minimum\slot\sarea', clip_fin, flags=re.IGNORECASE) and not re.findall(r"recreational\sfacilities|boardinghouses|divide\sthe\snet\sbuildable\sarea|recreation\sareas", clip_fin, flags=re.IGNORECASE):
                    xnew = r"minimum\slot\sarea"
                    kclip = r'.{0,50}' + str(xnew) + r'.{0,50}'
                    kclipmatches = re.findall(kclip, clip_fin, flags=re.IGNORECASE)
                    nums_fin = []
                    for m in kclipmatches:
                        nums = re.findall(numbers, m, flags=re.IGNORECASE)
                        for y in nums:
                            nums_fin.append(float(y.replace(",","")))
                        if nums_fin:
                            maxnum = max(nums_fin)
                            if re.findall(r"square|sq\.\sfeet", m, flags=re.IGNORECASE) and maxnum >= 40000:
                                mapping = "sf"
                            elif re.findall(r"acre|acres", m, flags=re.IGNORECASE) and maxnum >= 1:
                                mapping = "sf"
                            else:
                                mapping = ""
                        else:
                            mapping = ""
                elif min(dists) == 9999:
                    mapping = ''
                elif sum(map(lambda x : x<25, dists)) > 1:
                    if match_pos[n] < len(string)-4 and re.findall(r"\-", string[match_pos[n]+len(x):match_pos[n]+len(x)+2]):
                        clip_fin = string[match_pos[n]:match_pos[n]+50]
                        if re.findall(sf_hits, clip_fin, flags=re.IGNORECASE):
                            mapping = "sf"
                        elif re.findall(mf_hits, clip_fin, flags=re.IGNORECASE):
                            mapping = "mf"
                        elif re.findall(mx_hits, clip_fin, flags=re.IGNORECASE):
                            mapping = "mx"
                        elif re.findall(tf_hits, clip_fin, flags=re.IGNORECASE):
                            mapping = "tf"
                    else:
                        final_dist = dists.index(min(dists))
                        mapping = dist_dict[final_dist]
                elif all(i < 50 for i in allreldis):
                    final_dist = dists.index(min(dists))
                    mapping = dist_dict[final_dist]
                elif (re.findall(r"""(?x)principal\suses\sin|(?<!other\s)permitted\suses|uses\spermitted|is\sintended\sto\sprovide|
                                apartment\sbuildings|the\spurpose\sof\sthis\sresidential\sdistrict|
                                primarily\ssuited\sfor|district\sis\sintended\sfor|district\sis\sintended\sto|
                                uses\sby\sright|shall\sbe\sas\sfollows\:|district\sis\sdesigned\sto|use\:|
                                as\spermitted\sby|
                                districts\sare\sintended\sto\sbe|following\suses\sare\spermitted|consist\smainly\sof|
                                permitted\snumber\sof\sdwelling\sunit|residential\suses\sin|principal\suses\sof\sland|
                                specific\sintent\.|(?<!\d+\-\d+\s)general\sprovides(?!\sart)|permitted\sdwellings|all\suses\sshall\sbe\ssubject\sto|
                                district\sdesignation\sand\sintent\:|\w\.\spurpose|district\sis\sto\sprovide\sfor|
                                allow\sthe\sestablishment\sof|land\sto\sbe\sused\sshall\sbe\sfor|permitted\suses\.|
                                uses\sshall\sbe\spermitted|minimum\sstandards\sshall\sapply\:|district\sis\sestablished\sfor|
                                statement\sof\sintent|lot\syard\sand\sheight\srequire|following\sare\spermissive\suses|
                                (?<!the\scity\sinto\s[a-z]+\s)districts\:|principal\suse\sof\sland""", clip_fin, flags=re.IGNORECASE) or len(re.findall(r"per\sunit|per\sdwelling\sunit",clip_fin,flags=re.IGNORECASE)) > 2 or len(re.findall(r"district\:",clip_fin,flags=re.IGNORECASE)) < 3) and not re.findall(r"the\sfollowing\sregulations\sshall\sapply\sin\sresidential\sdistricts", clip_fin, flags=re.IGNORECASE):
                    if re.findall(sf_hits,clip_fin,flags=re.IGNORECASE) and re.findall(r"all\sother\sunit",clip_fin,flags=re.IGNORECASE):
                        continue
                    if re.findall(r"\s[a-z]\.\s" + x, string[:match_pos[n]], flags=re.IGNORECASE):
                        clip_start = [m.start(0) for m in re.finditer(r"\s[a-z]\.\s" + x, string[:match_pos[n]], flags=re.IGNORECASE)][-1]
                        clip_fin = string[clip_start:clip_stop]
                    elif (bhits== 1 and re.findall(r"(?<!zoning\sagent\:)\s\d+\.\s|(?<!as\sregulated\sin)\s\(\w{1}\)\s|\s\(\)\s|permitted\suses\.|\-\([a-z]\)\-|\d+\-\d+\:|\-\s\d+\-\d+\.|\-\s\d+\-\d+\.|regulation\s\:", string[match_pos[n]-100:match_pos[n]], flags = re.IGNORECASE)) or (re.findall(r"conditional\suses\spermitted\.|intent\.", string[match_pos[n]-100:match_pos[n]], flags = re.IGNORECASE)):
                        clip_start = [m.start(0) for m in re.finditer(r"(?<!zoning\sagent\:)\s\d+\.\s|(?<!as\sregulated\sin)\s\(\w{1}\)\s|\s\(\)\s|permitted\suses\.|\-\([a-z]\)\-|\d+\-\d+\:|regulation\s\:|conditional\suses\spermitted\.|\-\s\d+\-\d+\.|\-\s\d+\-\d+\.|intent\.", string[:match_pos[n]], flags = re.IGNORECASE)][-1]
                        clip_fin = string[clip_start:clip_stop]
                    dblocks_f = re.findall(r"\s[a-z]\.\s|\.\s" + trigger_words_s, string[match_pos[n]:], flags=re.IGNORECASE)
                    if x in dblocks_f:
                        dblocks_f.remove(x)
                    if dblocks_f and re.findall(r"\s[a-z]\.\s|\.\s" + dblocks_f[0], string[match_pos[n]:], flags=re.IGNORECASE):
                        clip_stop = [m.start(0) for m in re.finditer(r"\s[a-z]\.\s|\.\s" + dblocks_f[0], string[match_pos[n]:], flags=re.IGNORECASE)][0]
                        clip_fin = string[clip_start:clip_stop]
                    elif (fhits == 1 and re.findall(r"(?<!zoning\sagent\:)\s\d+\.\s(?!lot\syard\sand\sheight\srequire)|(?<!\s\(\w{1}\)|thereto\:|permitted\.)\s\(\w{1}\)\s(?!uses\spermitted|\(\w{1}\)\s)|special\spermitted\suses\.|\-\(\w\)\-|\d+.\d+\-+|\d+\-\d+\:|\-\s\d+\-\d+\.(?!\spermitted\suses|\sintended\spurpose)|\d+\-\d+\sspecial\sexception\suses\.", string[match_pos[n]+100:], flags=re.IGNORECASE)) or (re.findall(r"conditional\suses\spermitted\.|uses\sby\sspecial\sexception\:|\(\w\)\snonconformities\:|\d+.\d+\-+|\-\s\d+\-\d+\.(?!\spermitted\suses|\sintended\spurpose)|\d+\-\d+\sspecial\sexception\suses\.|conditional\suses\.|prohibited\suses\.|site\splan\sreview\.", string[match_pos[n]+100:], flags = re.IGNORECASE)):
                        clip_stop = match_pos[n]+100 + [m.start(0) for m in re.finditer(r"(?<!zoning\sagent\:)\s\d+\.\s(?!lot\syard\sand\sheight\srequire)|(?<!\s\(\w{1}\)|permitted\.)\s\(\w{1}\)\s(?!uses\spermitted|\(\w{1}\)\s)|special\spermitted\suses\.|\-\(\w\)\-|\d+.\d+\-+|\d+\-\d+\:|\-\s\d+\-\d+\.(?!\spermitted\suses|\sintended\spurpose)|conditional\suses\spermitted\.|uses\sby\sspecial\sexception\:|\(\w\)\snonconformities\:|\d+\-\d+\sspecial\sexception\suses\.|conditional\suses\.|prohibited\suses\.|site\splan\sreview\.", string[match_pos[n]+100:], flags=re.IGNORECASE)][0]
                        clip_fin = string[clip_start:clip_stop]
                    if re.findall(r"\d+\-\d+\sconditional\suses\.|\d+\-\d+\sspecial\sexception\suses\.", clip_fin, flags=re.IGNORECASE):
                        continue
                    if not re.findall(mfex, clip_fin, flags=re.IGNORECASE) and re.findall(mf_hits, clip_fin, flags=re.IGNORECASE):
                        mapping = "mf"
                    elif re.findall(mx_hits, clip_fin, flags=re.IGNORECASE):
                        mapping = "mx"
                    elif re.findall(tf_hits, clip_fin, flags=re.IGNORECASE):
                        mapping = "tf"
                    elif re.findall(sf_hits, clip_fin, flags=re.IGNORECASE):
                        mapping = "sf"
                elif re.findall(r'multi\sfamily\sdwellings\sare\spermitted', clip_fin, flags=re.IGNORECASE):
                    mapping = "mf"
                elif re.findall(r"district\sdevelopment\sstandards", clip_s, flags=re.IGNORECASE):
                    if x not in dist_dict.keys():
                        final_dist = dists.index(min(dists))
                        mapping = dist_dict[final_dist]
                    else:
                        continue
                else:
                    final_dist = dists.index(min(dists))
                    mapping = dist_dict[final_dist]
                #print("DIST")
                #print(dists)
                #print("MAPPING")
                #print(mapping)
                if mapping == '' and x in smfmap:
                    continue
                else:
                    smfmap[x] = mapping

                all_mappings.append(smfmap)

                #print("ALL MAPPINGS")
                #print(all_mappings)


    all_matches_un = list(dict.fromkeys(all_matches))
    #print("ALL UNIQUE MATCHES")
    #print(all_matches_un)

    #print("ALL MAPPINGS")
    #print(all_mappings)

    result_dict = {}

    for d in all_mappings:
        for k, v in d.items():
            if v == '':
                continue
            result_dict.setdefault(k, []).append(v)

    #print("FULL DICT")
    #print(result_dict)

    final_dict = {}
    for n in result_dict:
        final_dict[n] = mode(result_dict[n])

    #print("FINAL DICT")
    #print(final_dict)

    ## calculate percentages ##

    sf = 0
    for key in final_dict:
        if final_dict[key] == 'sf':
            sf = sf + 1

    mf = 0
    for key in final_dict:
        if final_dict[key] == 'mf':
            mf = mf + 1

    mx = 0
    for key in final_dict:
        if final_dict[key] == 'mx':
            mx = mx + 1

    tf = 0
    for key in final_dict:
        if final_dict[key] == 'tf':
            tf = tf + 1

    if final_dict:
        sf_per = (sf + tf)/len(final_dict)
        mf_per = (mf + mx)/len(final_dict)
    else:
        sf_per = None
        mf_per = None

    ## if all else fails, try this approach ##

    if mf_per == None:
        for string in inlist:
            if re.findall(r"use\sregulation\sschedule", string, flags=re.IGNORECASE):
                #print("USE TABLE")
                #print(string)
                alldis = re.findall(trigger_words_s, string, flags=re.IGNORECASE)
                nalldis = len(alldis)
                #print("NUMBER OF RES DIS")
                #print(nalldis)
                sf = re.findall(r'single\sfamily|1\sfamily\sdetached|rural|one\-family|single\sresidence|estate|single\-unit|single\-dwelling', string, flags=re.IGNORECASE)
                if sf:
                    sfmatch = [m.start(0) for m in re.finditer(r'single\sfamily|1\sfamily\sdetached|rural|one\-family|single\sresidence|estate|single\-unit|single\-dwelling', string, flags=re.IGNORECASE)][0]
                    sf_clip = string[sfmatch - 100:sfmatch + 100]
                    sfdis = re.findall(r"\byes\b", sf_clip, flags=re.IGNORECASE)
                    nsfdis = len(sfdis)
                else:
                    nsfdis = 0
                sf = re.findall(r'multiple\sfamily|multi\sfamily|apartment|multiple\sdwelling|multiple\sresidence|apartments|multi\-dwelling', string, flags=re.IGNORECASE)
                if mf:
                    mfmatch = [m.start(0) for m in re.finditer(r'multiple\sfamily|multi\sfamily|apartment|multiple\sdwelling|multiple\sresidence|apartments|multi\-dwelling', string, flags=re.IGNORECASE)][0]
                    mf_clip = string[mfmatch - 100:mfmatch + 100]
                    mfdis = re.findall(r"\byes\b", mf_clip, flags=re.IGNORECASE)
                    nmfdis = len(mfdis)
                else:
                    nmfdis = 0

                if nalldis > 0 and (nsfdis > 0 or nmfdis > 0):
                    sf_per = nsfdis/nalldis
                    mf_per = nmfdis/nalldis
                    break

            elif re.findall("residence\sdistricts\.|permitted\suses", string, flags=re.IGNORECASE):
                fmpos = [m.start(0) for m in re.finditer("residence\sdistricts\.|permitted\suses", string, flags=re.IGNORECASE)][0]
                if fmpos-300 < 0:
                    fsta = 0
                else:
                    fsta = fmpos - 300
                if fmpos + 300 > len(string):
                    fsto = len(string)
                else:
                    fsto = fmpos + 300
                fclip = string[fsta:fsto]
                if re.findall(r'multiple\sfamily|multi\sfamily|apartment|multiple\sdwelling|multiple\sresidence|apartments|multi\-dwelling|three\-family',fclip,flags=re.IGNORECASE):
                    mf_per = 1
                elif re.findall(r'single\sfamily|1\sfamily\sdetached|rural|one\-family|single\sresidence|estate|single\-unit|single\-dwelling', fclip, flags=re.IGNORECASE):
                    mf_per = 0


    return(mf_per)

'''
buildtable1 is the first function meant to parse information stored in dimensional tables. It takes an input string
with flags indicating the presence of a dimensional table. This function, as opposed to buildtablel2, parses 
dimensional tables in which rows generally indicate different zoning districts (e.g., R-1) and columns contain dimensional 
criteria (e.g., minimum lot size). 

This function proceeds through a series of steps to eventually extract the necessary dimensional information:

1. First, complete regex searches for a word or phrase indicating dimensional tables
2. Determine how many columns of a potential table exist and proceed if this number exceeds some threshold 
3. Determine where the rows begin and work backwards from this point to construct the table header 
4. Next, reformat the rows 
5. Now, with the dimensional table information parsed, determine if the header contains any keywords pertaining
   to minimum lot size, maximum density, or building height maximums. 
6. Extract the correct information from step 5

'''

def buildtablel1(input1, input2):
    newlist1 = []
    inewlist1 = []
    fnewlist1 = []
    newlist2 = []
    inewlist2 = []
    fnewlist2 = []
    inlist = [input1, input2]
    test1 = inlist[0]
    test2 = inlist[1]
    mls_ind = r"""(?x)(?:(minimum\slot\sarea\sper\sdwelling\sunit|(?<!floor\s|site\s)area\sper\sdwelling\sunit|
                      minimum\slot\sarea\sper\sfamily|minimum\slot\sarea\sper\sdwelling|
                      minimum\slot\sarea\sper\sdu|area\sof\slot|area\/du|
                      minimum\slot\sarea\sper\sunit|lot\sarea\sper\sunit|
                      minimum\slot\ssize|min\.\slot\sarea|minimum\slot\sarea|min\slot\ssize|
                      minimum\slot\s(?!width|frontage)|lot\sminimums|(?<!maximum\s)lot\sarea|
                      minimum\ssize\slot\sper\sunit|lot\sarea\sminimum|
                      minimum\ssize\slot|minimum\ssize\sper\szoning\slot|
                      (?<!maximum\s)lot\ssize|area\sin\ssquare\sfeet\sper\sadditional\sfamily|
                      square\sfeet|square\sfeet\sper\sdwelling\sunit|square\sfeet\/dwelling\sunit|
                      square\sfeet\sper\sadditional\sfamily|area\sin\ssquare\sfeet|
                      (?<!maximum\spercent\sof\slot\s|maximum\s\%\sof\slot\s|maximum\slot\s)area|
                      per\sfamily|per\sunit))"""

    height_ind = r"""(?x)(?:\b(maximum\sheight\sfeet|max\sbuilding\sheight|maximum\sheight|building\sheight|
                              maximum\sbldg\.\sheight|height|max\sht|principal|
                              (?<=stories\s)feet|feet(?=\sstories)|stories)\b)"""

    acre_res = []
    unit_res = []
    sqft_res = []
    height_ft_res = []
    height_st_res = []
    height_res_final =[]
    acre_res_final1 = []
    acre_res_final2 = []
    acre_res_final = [acre_res_final1, acre_res_final2]
    unit_res_final1 = []
    unit_res_final2 = []
    unit_res_final = [unit_res_final1, unit_res_final2]
    sqft_res_final1 = []
    sqft_res_final2 = []
    sqft_res_final = [sqft_res_final1, sqft_res_final2]

    table_words = ["schedule", "dimensional stardards", "lot dimensions",
                   "zoning district", "residential district", "residential district r-1",
                   "residential district r-a", "residential r-2 district",
                   "residential r-3 district", "residential r-4 district", "dimension restrictions",
                   "dimensional require", "dimensional and density regulations",
                   "development standards", "residential zones", "minimum lot size"]

    table_words_s = r"""(?x)          # Turn on free spacing mode
                    (
                      \b
                      (schedule\sof|dimensional\srequire|dimension\sregulations|zoning\sdistrict\srules\sand\sregulations|
                       dimensional\sand\sdensity\sregulations|lot\sdimensions|dimensional\sregulations|
                       development\sstandards|dimensional\sstandards|dimension\srestrictions|lot\sand\sbulk\sstandards|
                       residential\/agricultural\sdistricts|intensity\sregulations|height\sand\sarea\srequire|
                       \w{1}\.\s+minimum\slot\ssize|bulk\sand\sreplacement|district\sdesign\srequire|lot\sstandards\sby\szone|
                       development\sregulations|lot\sdimension\sand\sintensity\sstandards|density\sand\sbulk\srequire|
                       bulk\sand\splacement\sregulations|minimum\slot\ssize\sper\sdwelling\sunit|land\sspace\srequire|
                       bulk\sregulations|lot\sarea\sfrontage\sand\syard\srequire|yard\sand\sheight\srequire|
                       zoning\sdistricts|minimum\slot\srequire|area\sand\sbulk\sstandards|
                       accessory\sstructure\smaximum\slot\sarea|minimum\szone\ssize|site\sdimensions|
                       other\sdimensions\sand\sspace\srequire|area\syard\sand\sheight\sregulations|height\sand\slot\srequire|
                       bulk\sand\sarea\sstandards|density\sschedule|development\scriteria\sdistrict|zone\sstandards|
                       height\slimit\slot\ssizes\sand\scoverage|bulk\sand\sarea\sregulations|lot\ssize|max\sht|
                       land\suse\sdistrict\sand\sallowable\suses|bulk\sand\ssetback\sregulations|residential\sbulk\schart\s(?!at\sthe\send)|
                       bulk\smatrix|residential\suses\sand\srequire|standards\sfor\sprincipal\sbuildings\son\sindividual\slots|
                       lot\sand\syard\srequire|intensity\sof\suse|dimensional\scontrols|lot\srequire|lot\sstandards\smatrix|
                       lot\syard\sand\sdensity\sregulations|height\sand\sarea\sregulations|zoning\sdistrict\sregulation\schart|
                       area\syard\sand\sheight\sstandards|bulk\sand\scoverage\scontrols|(?<!maximum\s)bulk\srequire|density\sregulations|
                       summary\sof\szoning\sdistrict\srequire|dimensional\stable|area\sand\sbulk\sschedule|
                       lot\syard\sarea\sand\sheight\srequire|area\syard\sand\sheight\srequire|height\sand\syard\srequire|
                       area\ssetback\sand\sheight\srequire|height\sarea\sand\syard\srequire|bulk\syard\sand\sspace\srequire|
                       bulk\sand\syard\sregulations|density\sdimensions\sand\sother\sstandards|zone\sdwelling\sfamily\ssize|
                       district|minimum\slot\size|minimum\slot\sarea|density\sand\sintensity\slimit|bulk\sschedules)
                      \b  
                      )"""

    trigger_words = ["zone", "district", "maximum height", "stories", "feet", "minimum lot size", "area", "frontage",
                     "standards",
                     "minimum lot width", "lot width", "minimum lot coverage", "lot coverage", "maximum lot coverage",
                     "lot coverage",
                     "lot shape", "floor area ratio", "far", "f.a.r.", "minimum percent green area requirements",
                     "lot area",
                     "minimum front yard", "minimum side yard", "minimum rear yard", "street side year", "side yard",
                     "rear yard",
                     "minimum side yard", "minimum rear yard", "accessory structures", "height", "frontage",
                     "front yard",
                     "lot coverage", "maximum size without pzba special exception",
                     "minimum lot area per dwelling unit"]

    trigger_words_l2 = ["standards", "r-1a", "r-1", "r-2", "r-3", "r-4", "r-5"]

    trigger_words_s = r"""(?x)          # Turn on free spacing mode
                    (?:
                      \b
                      (zoning\sdistrict(?!\sregulations)|(?<!dwelling\s|for\s)zoning\sdistricts(?!\:\s\-*)|zone\sdistricts|
                      zone\sdistrict|zone(?!\sstandards)|
                      minimum\sdistrict\ssize\sin\sacre|district\sarea\sin\ssquare\sfeet|
                      (?<!mixed\s)use\sdistrict|(?<!mixed\s)use\sdistricts|minimum\sarea\/du\stotal\sdensity|
                      minimum\sarea\sdu\stotal\sdensity|minimum\slot\srequire|minimum\syards\srequire|minimum\syard\srequire|
                      (?<!all\szoning\s|zoning\s|park\s)districts(?!\sregulations|\sapplicable)|use\sclassification|
                      (?<!by\s|lmdr\s|mdr\s|in\sthis\s)district(?!\sin\swhich|\sspecific|\sregulations|\.\s+secs\.|\.\scity|\sarea\sin\ssquare\sfeet|\sclassifications|\sstandards|\.\s\w+\.|\.\s\()
                      accessory\sstructure\smaximum\slot\sarea|max\slot\sarea|
                       use\sstandards|(?<!and\/or\s)uses|maximum\spercent\sof\slot\sarea\scovered|
                       zoning\sclassification|zoning\ssymbol|maximum\sheight\sfeet|(?<!minimum\s)maximum\sheight|
                       maximum\susable\sfloor\sarea\sand\saccessory\sbuilding\sfloor\sarea|unit\stype|
                       maximum\snumber\sof\sdwelling\sunits|area\sand\swidth\sreq\.\sin\sfeet|
                       setback\srequire\sin\sfeet|minimum\slivable\sfloor\sarea\sper\sunit|
                       maximum\sdwelling\sunits|maximum\simpervious\ssurface|(?<!regulations\s)minimum\syard\ssetbacks(?!\szoning\sdistrict)|
                       (?<!providing\s)minimum\syard\ssetback(?!s)|minimum\sfloor\sarea\sper\sdwelling\sunit|
                       minimum\slot\srear\sarea\sdwelling\sunit|(?<!floor\s)area\sper\sdwelling\sunit|
                       open\sspace\sper\sdwelling\sunit|total\sarea|
                       minimum\slot\sarea\sper\sdu|minimum\slot\sarea\sper\sunit|lot\sarea\sper\sunit|
                       per\sdwelling\sunit|minimum\syard\sregulations|
                       maximum\sdwelling\sunit\sdensity|(?<!height\s)lot\sdimensions|area\sof\slot|lot\sdepth|
                       maximum\susable\sfloor\sarea|dwelling\sunit\sper\snet\sacre|
                       minimum\slot\sarea\sper\sdwelling\sunit|minimum\slot\sarea\sper\sfamily|lot\sarea\sper\sfamily|
                       minimum\slot\sarea\sper\sdwelling|lot\sarea\sper\sdwelling\sunit|
                       minimum\slot\sarea\/du|maximum\s\%\sof\slot\sarea\scovered\sby\sbuildings|
                       maximum\spercent\sof\slot\sarea\scovered\sby\sbuildings|minimum\sbuilding\swidth|
                       maximum\snumber\sof\sdwelling\sunit\sper\sgross\sacre|
                       maximum\sdwelling\sunit\sper\sbuildable\sacre|unit\sper\slot|
                       minimum\ssite\sarea\sper\sdwelling\sunit|maximum\sbldg\.\sheight|
                       maximum\sdwelling\sunit\sper\sstructure|maximum\sdwelling\sunit\sper\sgross\sacre|
                       minimum\stract\sarea|minimum\slot\sarea|minimum\slot\sfrontage|
                       minimum\slot\sdimensions|minimum\slot\ssize|min\slot\ssize|max\sdua|min\slot\swidth|
                       min\stract\ssize|max\sbldg\sheight|min\sfloor\sarea|max\sbldg\scover|
                       max\simpervious\ssurface|building\sheight|minimum\ssize\slot|
                       minimum\syard\sdepth|maximum\scoverage|accessory\sbuilding|yard\ssettbacks|
                       minimum\ssize\slot\sper\sunit|minimum\ssize\sper\szoning\slot|
                       lot\sshape|floor\sarea\sratio|far|maximum\sbuilding\scoverage|area\sper\sdwelling\sunit|
                       maximum\simpervious\scoverage|minimum\sopen\sspace\sarea|minimum\sopen\sspace|
                       maximum\sbuilding\sfootprint|maximum\sbuilding\sarea|density\sper\sacre|dwelling\stype|
                       maximum\simpervious\sarea|side\slot\sline\ssetback|maximum\snumber\sof\sunit|
                       area\sin\ssquare\sfeet\sper\sadditional\sfamily|square\sfeet\sper\sadditional\sfamily|
                       minimum\spercent\sgreen\sarea\srequire|width\sin\sfeet|area\sin\ssquare\sfeet|width\sin\sfeet|
                       minimum\sgreen\sspace\scoverage|maximum\sprincipal\sbuilding\scoverage|
                       street\sside\s\(corner\slot\)\sfeet|minimum\syard\sdimensions|
                       maximum\sbuilding\slot\scoverage\sin\spercent\sof\slot\sarea|lot\sarea\ssquare\sfeet|
                       minimum\slot\swidth|minimum\slot\scoverage|maximum\slot\scoverage|
                       maximum\slot\scov|minimum\sfloor\sarea|lot\scoverage|minimum\szone\ssize|
                       (?<!maximum\s|the\sdensity\sand\s)lot\ssize(?!\srequire\swithin\sa)|max\sht|
                       minimum\sfront\syard|minimum\srear\syard|street\sside\syear|lot\scoverage|
                       minimum\sside\syard|accessory\sstructures|(?<!maximum\s)lot\sarea(?!\s\d+)|minimum\shouse\ssize|
                       maximum\ssize\swithout\spzba\sspecial\sexception|minimum\sproperty|maximum\snet\sdensity|
                       lot\scoverage|maximum\sdensity|max\sdensity|minimum\sheated\sarea|area\sin\square\sfeet|
                       minimum\sside\syard|parking|minimum\shouse\ssize|minimum\sparking\ssetback|minimum\sparking|
                       off\-street\sparking\sspaces\sper\sdwelling\sunit|square\sfeet\sper\sdwelling\sunit|
                       off\sstreet\sparking|off\sstreet\sloading|minimum\sarea\srequire|
                       minimum\sproject\ssize|housing\stypes\sallowed|utility\srequire|(?<!floor\s)area\/du|
                       front\syard\ssetback\sin\sft|side\syard\ssetback\sin\sft|rear\syard\setback\sin\sft|
                       front\syard\sin\sft|side\syard\sin\sft|rear\syard\sin\sft|maximum\sdwelling\swidth|
                       front\syard\ssetback|side\syard\ssetback|rear\syard\setback|minimum\srequire|
                       side\syard\swidth|rear\syard\sdepth|minimum\syard(?!\ssetbacks)|principal\sheight|accessory\sheight|
                       min\sfor\seach\sadd\'l\sdwelling\sunit|street\sside\s+feet|width\sand\sfrontage|minimum\swidth|
                       in\sfeet|side\syard\s+at\sleast\sone|side\syard\s+total|front\syard(?!\sarea)|side\syard|rear\syard|
                       front\ssetback|rear\ssetback|side\ssetback|front\sand\srear|per\sfamily|per\sunit|total|aggregate|
                       area\ssquare\sfeet|width\ssquare\sfeet(?!\sper\sdwelling\sunit)|depth\sfeet|front\sfeet|side\s+feet|rear\sfeet(?!\sstories)|
                       depth|each\scorner|yards\sprincipal\sbuilding|yards\saccessory\sbuilding|(?<!minimum\s)yard\ssetbacks|
                       principal\spercent\sof\slot|accessory\spercent\sof\srear\syard|principal\spercent|accessory\spercent|
                       (?<!for\s)principal|accessory|front\sand\sside\sfront|each\sside|depth\sof\sfront\syard|depth\sof\sside\syard|
                       lot\swidth\sin\sfeet\sat\sbldg\.\sline|lot\swidth\sin\sfeet|lot\swidth(?!\s\d+)|
                       (?<!lot\syard\sand\s|low\s|bulk\s)density(?!\sand\sarea\srequire)|(?<!min\s)front|one\sside|1\sside|(?<!min\s)side|(?<!min\s)rear|
                       square\sfeet\/dwelling\sunit|(?<!\d+\s)square\sfeet|(?<!square\s)feet|width\sin\sfeet|(?<!lot\s)width(?!\s\d+)|(?<!yard\s)setback|
                       (?<!yard\sand\s|the\s|maximum\s)height(?!\sbulk|\sand\sarea)|frontage|area\sin\ssquare\sfeet|
                       interior|exterior|corner|street\syard|buffer\strip|
                       percent\sof\slot|(?<!floor\s|of\s|lot\s)area(?!\srequire|\s\d+|\sby\szoning\sdistrict)|stories|code\stext)\d*
                      \b
                      )"""

    trigger_words_l2_s = r"\bstandards\b|r\-"

    endlist1 = []
    endlist2 = []
    endlist = [endlist1, endlist2]

    rowhcm = []

    for i in range(2):
        stlist = list(deepflatten(inlist[i], 1))
        rflist = []
        for string in stlist:
            rf_string = re.sub(r'\s\/', '-', string, flags=re.IGNORECASE)
            rflist.append(fractonum(rf_string))

        for string in rflist:
            try:
                endlist[i].append(text2int(string))
            except ValueError:
                endlist[i].append('')
            except IndexError:
                endlist[i].append('')

    for i in range(2):
        for string in endlist[i]:

            ## simply determine if this part of the text is actually a table ##
            text_extract = []
            if re.findall(table_words_s, string, flags=re.IGNORECASE):
                extract = re.findall(table_words_s, string, flags=re.IGNORECASE)
                mpos_og = [m.start(0) for m in re.finditer(table_words_s, string, flags=re.IGNORECASE)]
                mpos1 = [[p - 30, p + 2000] for p in mpos_og]
                for n, t in enumerate(mpos1):
                    t = [0 if x < 0 else x for x in t]
                    t = [len(string) if x > len(string) else x for x in t]
                    mpos1[n] = t
                clips1 = []
                for r, run in enumerate(mpos1):
                    clip = string[run[0]:run[1]]
                    clips1.append(clip)
                text_extract = list(dict.fromkeys(clips1))

            for t in text_extract:
                text_extract_sf = re.sub(r'1\sfamily', "one family", t)
                text_extract_tf = re.sub(r'2\sfamily', "two family", text_extract_sf)
                text_extract_thf = re.sub(r'3\sfamily', "three family", text_extract_tf)
                text_extract_thff = re.sub(r'3\sand\s4\sfamily', "three and four family", text_extract_thf)
                text_extract_ff = re.sub(r'4\sfamily', "four family", text_extract_thff)
                text_extract_fs = re.sub(r'unless\sotherwise\sspecified\)\sper\sdwelling\sunit',
                                         'unless otherwise specificed) area per dwelling unt', text_extract_ff)


                text_extract_s = re.sub(r'\bsee\b\sr\-\d+', "", text_extract_fs)

                #print("TEXT EXTRACT")
                #print(text_extract_s)

                if text_extract_s.count('~') > 3:
                    continue

                sflags = re.findall(r'\s\w{1}\.\s|\d{1}\.\s', text_extract_s, flags=re.IGNORECASE)
                if len(sflags) > 25:
                    continue

                if re.findall(r"""(?x)\b(example|dimensional\srequire\sfor\sassisted\sliving\sresidences|industrial\sdistricts\sdimensional\srequire|
                                         gas\sstation|signalized\sintersection\son\sa\sstate\sor\scounty\sroad|
                                         minimum\sgross\sarea\sfor\sformation\sof\sresidential\splanned\sunit\sdevelopment|
                                         the\sb\-2\sdistrict\sis\sgenerally\scharacterized\sby\san\sintegrated\sor\splanned\scluster\sof\sestablishments|
                                         the\sintent\sof\sthis\sto\spermit\slot\ssizes\sand\slot\swidths\sto\sbe\sadjusted)\b|
                                         minimum\sproject\sarea\spermitted\sfor\san\sopen\sspace\ssubdivision\sshall\sbe\sas\sfollows:|
                                         require\sopen\sspace\sof\slot\sin\sbusiness\sdistricts\sare\sspecified\sin\sschedule|
                                         \.{10,}""",
                              text_extract_s,
                              flags=re.IGNORECASE):
                    #print("FLAG: NOT A TABLE")
                    continue

                ## get the column names ##

                cols = []
                total_cols = []

                if re.findall(trigger_words_s, text_extract_s, flags=re.IGNORECASE):
                    cols = re.findall(trigger_words_s, text_extract_s, flags=re.IGNORECASE)
                    total_cols = list(dict.fromkeys(cols))
                else:
                    continue

                #print("TOTAL COLUMNS")
                #print(len(total_cols))

                #print("COLUMN NAMES")
                #print(total_cols)

                ## now organize the rows ##

                if len(total_cols) <= 2:
                    continue

                ## this indicates when the rows begin ##
                ## the first row marks the end of the header row ##
                row_trig = r"""(?x)(?:(?<!as\s)\b(sr\-\d+\ssingle\sfamily|
                                         r\-\d+\s\(*single\sfamily\sresidential\)*|r\-\d+\ssingle\sfamily\sdetached|
                                         r\d+\ssingle\sfamily\sdwelling|gr\-\d+|r\/a|a\-r|sfr|mfr|
                                         r\-\d+\stownhouses|r\-\w*|rs\-|sr\-\d+\ssingle\sfamily|r\-\d\-\d\-*\d*|r\-\w\-\d|r\-d\-\w+|rhr|
                                         sr\-\d+|sr\-\w{1}|ra\d|ra\-\d+|ra\-|r\d+s|r\-\d+|r\-|r1\-\d+|r1\-|r\d+\w{1}(?!\sbhm)|r\d|r\-\d+|r\-\d+\w*|rs\-\d+|s\-\d+|
                                         rr|r\w{1}(?!\d+)|dr\-\d+|gc|nc|li|hi|osi|os|lug\-|b\-\d+|ar|r\/b|
                                         r2f|rmf\-\d+\.*\d*|rmf\-\.\d+|rmf|a\-o\sagricultural|a\-o|sr|mr|mf|gr|ah|lb|
                                         rb\-\d+|rb|mu\-\d+|ba\-\d+|dd\-\d+|bb\-\d+|a\-\d+|a(?=\s\d+\sacre)|
                                         s\-\d+|r\-\d\w{1}|r\d+\-\d+\w{1}|rm\-\d+\w{1}|e\-\d+|e\d+|
                                         ba|bb|bn|dt|sl|cr\-\d+|l\d+|mx|ag|aa|bhn|ld\-r|md\-r|mhd\-r|hd\-r|ro|rc|
                                         co|mh|c\-s|f\-p|sc|sfr\-\d+|mfr\-\d+|multi\-fm|all\sother\sallowed\suses|
                                         mhp|noc\smulti\sfamily|noc\ssingle\sfamily|noc|pud|suburban|open\sspace|o\-s|a\d+|b\d+|li|lr|vr|vg|vc|ca|
                                         r\-ag|res\.\sdistrict\s\w{1}|a\-\d+\sagriculture|a\-\d+|ag\-res\sdist\.\s\w+|res\.\s\w{1}|rfwp|
                                         r\-village|r\-cultural|r\-\d+\ssingle\sfamily|r\-\d+\sduplex|r\-\d+\striplex|r\-\d+\squadplex|
                                         r\-\d+\sapartments|r\-\d+\w*\stownhouses|ccm|er|ldr|sfr}md|cbd|qg|qii|(?<!drawings\s\()rc\-\d+|vb|vr\-\d+|vr|rl\d+|
                                         non\-residential|fr|mfr|ncor|cor|hcor|co|ind|mc|pr\-\d{1,3}|conservation|special\sdistricts|
                                         \D\-\D\-\D\-|\D\-\D\-|ar\sagricultural|single\sresidence|single\sres\.\sdistrict\s\w{1}|
                                         r\-t\stwo\sfamily\sresidential|general\sdistrict|commercial\suse\sabutting\sa\sresidential\suse|
                                         sf\-\d+\ssingle\sfamily|df\-\d+\sduplex\-family|ph\-\d+\spatio\shome|cf\-\d+\scombined\sfamily|
                                         th\-\d+\stownhouse|cm\-\d+\scondominium|mf\-\d+\smulti\sfamily|sf\-\d+|tn\d+|
                                         single\sfamily\sdetached\sdwelling|single\sfamily\sdwelling|single\sfamily\sdetached|
                                         residence\sdistrict\s\w{1}|duplex|multifam|planned\sresidential|
                                         residence\s\w{1,2}|livestock\sfarm|private\scollege|senior\scitizen|cluster\sresidential|
                                         (?<!and\s|multi\sfamily\s)residential|rural|recreational|garden\sapartment|(?<!general\s)commercial|single\sfamily\s\w{1}|
                                         other\sallowed\suse|residential\sdwelling\sunit|other\spermitted\suses|i\sindustrial|cem|l\-i|w\-r|msr|
                                         two\-family\sdwelling|multi\sfamily\sdwelling|apartments|townhouses|single\sfamily|two\-family|two\sfamily|
                                         multi\sfamily|office|townhouse|mountain|rural|garden\sapartment|affordable\shousing|aho\-\d+|senior\scitizen|
                                         (?<!maximum\s|per\s|for\sthe\s\d\s*\d*\s|add\'l\s)dwelling|schools|standard\sneighborhood|planned\sresidential\sneighborhood|patio\shome|
                                         cemeteries|funeral|detached\ssingle\-|detached\ssingle|residences|cr\scountry|tr\stown|notes|(?<!for\s)dwellings|non\-dwellings|
                                         (?<!n\/|\d{4,}\s|plus\s|and\s)a(?!\sb|\snone|\)|\s\d+\s[a-z]+\d+)|(?<!\d{4,}\s|plus\s|and\s|a\s)b(?!\sc|\snone|\)|\s\d+\s[a-z]+\d+)|(?<!\d{4,}\s|plus\s|and\s|b\s)c(?!\snone|\sd|\)|\s\d+\s[a-z]+\d+)|(?<!\d{4,}\s|plus\s|and\s|c\s)d(?!\snone|\)|\s\d+\s[a-z]+\d+))\b|
                                         (\-\s\d\sfamily|single(?!\swith|\s\+)|family\shome|agriculture|other\suses|group\shomes|place\sof\sreligious\sexercise\sor\sassembly\sschool))"""
                text_extract_pre1 = re.sub(r'\-{2,}', '', text_extract_s)
                text_extract_r = re.sub(r'[+|]', '', text_extract_pre1)
                if re.findall(row_trig, text_extract_r, flags=re.IGNORECASE):
                    #print("CHECKPOINT 1")
                    row_start = [m.start(0) for m in re.finditer(row_trig, text_extract_r, flags=re.IGNORECASE)]
                    #print("ROW START")
                    #print(row_start)
                    row_start_names = [item for t in re.findall(row_trig, text_extract_r, flags=re.IGNORECASE) for item in t if item != '']
                    #print("ROW START NAMES")
                    #print(row_start_names)
                    row_start_names_un = list(dict.fromkeys(row_start_names))
                    # print("ROW START NAMES - UNIQUE")
                    # print(row_start_names_un)
                    if len(row_start_names_un) < 2:
                        continue
                    prflag1 = re.findall(r'r\-\d*\w*', ",".join(row_start_names_un), flags=re.IGNORECASE)
                    prflag2 = re.findall(r'residential', ",".join(row_start_names_un), flags=re.IGNORECASE)
                    if len(prflag1) == 1 and len(prflag2) == 1 and re.findall(r'r\-\d*\w*', row_start_names_un[0],
                                                                              flags=re.IGNORECASE) and row_start_names_un[
                        1] == "residential":
                        for n, num in enumerate(row_start):
                            if n > 1 and n < len(row_start) - 2:
                                rl1 = row_start[n + 1] - row_start[n]
                                rl2 = row_start[n + 2] - row_start[n + 1]
                                if abs(rl1) < 200 and abs(rl2) < 200:
                                    hmnum = n
                                    break
                                else:
                                    hmnum = n
                            elif n > 1 and n != len(row_start) - 1:
                                if abs(row_start[n + 1] - row_start[
                                    n]) < 250:
                                    hmnum = n
                                    break
                                else:
                                    hmnum = n
                            elif n > 1:
                                hmnum = n
                            else:
                                hmnum = 0
                    elif len(row_start) > 1:
                        for n, num in enumerate(row_start):
                            if n != 0 and n < len(row_start) - 2:
                                rl1 = row_start[n + 1] - row_start[n]
                                rl2 = row_start[n + 2] - row_start[n + 1]
                                if abs(rl1) < 200 and abs(rl2) < 200:
                                    testfrow = text_extract_r[row_start[n]:row_start[n + 1]]
                                    testfrownumsa = re.findall(numbers, testfrow, flags=re.IGNORECASE)
                                    testfrownumsb = re.findall(r'\-', testfrow, flags=re.IGNORECASE)
                                    testfrownums = len(testfrownumsa) + len(testfrownumsb)
                                    if testfrownums >= 2:
                                        hmnum = n
                                        break
                                    else:
                                        continue
                                else:
                                    hmnum = n
                            elif n != 0 and n != len(row_start) - 1:
                                if (abs(row_start[n + 1] - row_start[n]) < 250 and abs(
                                        row_start[n] - row_start[n - 1]) < 250):
                                    testfrow = text_extract_r[row_start[n]:row_start[n + 1]]
                                    testfrownumsa = re.findall(numbers, testfrow, flags=re.IGNORECASE)
                                    testfrownumsb = re.findall(r'\-', testfrow, flags=re.IGNORECASE)
                                    testfrownums = len(testfrownumsa) + len(testfrownumsb)
                                    if testfrownums >= 2:
                                        hmnum = n
                                        break
                                    else:
                                        continue
                                else:
                                    hmnum = n
                            elif n == 0:
                                if len(row_start) > 2:
                                    rl1 = row_start[n + 1] - row_start[n]
                                    rl2 = row_start[n + 2] - row_start[n + 1]
                                    if abs(rl1) < 200 and abs(rl2) < 200:
                                        testfrow = text_extract_r[row_start[n]:row_start[n + 1]]
                                        testfrownumsa = re.findall(numbers, testfrow, flags=re.IGNORECASE)
                                        testfrownumsb = re.findall(r'\-', testfrow, flags=re.IGNORECASE)
                                        testfrownums = len(testfrownumsa) + len(testfrownumsb)
                                        if testfrownums >= 2:
                                            hmnum = n
                                            break
                                    else:
                                        continue
                                else:
                                    if abs(row_start[len(row_start) - 1] - row_start[n]) < 250:
                                        hmnum = n
                                        break
                            else:
                                hmnum = n
                    else:
                        hmnum = 0
                else:
                    continue

                ## end of header ##
                h_stop = int(row_start[hmnum])

                ## this is the start of the header row ##
                tab_start_list = [m.start(0) for m in re.finditer(table_words_s, text_extract_s, flags=re.IGNORECASE)]

                if tab_start_list:
                    for st in tab_start_list:
                        tab_start = int(st)
                        hr_test = text_extract_r[tab_start:h_stop]
                        hr_sent_flag = re.findall(r'\b(is|was|are|the|as|an|has|for|as|except|out|figure|table)\b',
                                                  hr_test, flags=re.IGNORECASE)
                        if len(hr_sent_flag) > 3:
                            continue
                        else:
                            break
                else:
                    tab_start = 0

                ## start of header ##
                all_table_new = text_extract_r[tab_start:h_stop]

                #print("TABLE")
                #print(all_table_new)

                ## get rid of text in parentheses ##
                all_table_fin = re.sub(r'\([^)]*\)|and\sstructures', '', all_table_new)

                if re.findall(r'ecode360', all_table_new, flags=re.IGNORECASE):
                    continue

                #############################
                ## create header: method 1 ##
                #############################

                if re.findall(r'\|\s+\w+\s+\|', text_extract_s, flags=re.IGNORECASE):
                    #print("YES - METHOD 1")
                    rtab_start = [m.start(0) for m in re.finditer(r'\|\s+\w+\s+\|', text_extract_s, flags=re.IGNORECASE)]
                    clip = text_extract_s[rtab_start[0]:]

                    if re.findall(r'[-+\n]', clip, flags=re.IGNORECASE):
                        #print("CHECKPOINT A")
                        hrtrig1 = re.sub(r'[-+\n]', '', clip)
                        hrtrig2 = hrtrig1.split("|")

                        hr_result = [m for m in hrtrig2 if re.search(r'r\d', m)]

                        hr_results = []
                        for r in hr_result:
                            hr_results.append(hrtrig2.index(r))

                        if not hr_results:
                            continue

                        #print("HR RESULTS")
                        #print(hr_results)

                        header_sk = hrtrig2[:hr_results[0] - 1]

                        hr_rows = []
                        for r, n in enumerate(hr_results):
                            if r != len(hr_results) - 1:
                                hr_row = hrtrig2[hr_results[r]:hr_results[r + 1]]
                            else:
                                hr_row = hrtrig2[hr_results[r]:]
                            hr_rows.append(hr_row)

                        #print("HEADER")
                        #print(header_sk)

                        len_hr_rows = []
                        for r in hr_rows:
                            len_hr_rows.append(len(r))

                        new_hr = ",".join(header_sk)
                        htemps = [new_hr[x:x + 90] for x in range(0, len(new_hr), 90)]

                        hnews = []
                        for h in htemps:
                            hnew = h.split(",")
                            if hnew[0].isspace():
                                hnew.pop(0)
                            elif hnew[0] == "" or hnew[0] == " ":
                                hnew.pop(0)
                            hnews.append(hnew)
                        if not hnews:
                            continue

                        mid_hr_rows = []
                        int_hr_rows = []

                        for a in range(len(hnews[0]) - 1):
                            for b in hnews:
                                if len(b) < len(hnews[0]) - 1:
                                    ex = int(len(hnews[0]) - len(b))
                                    b.extend([""] * ex)
                                mid_hr_rows.append(b[a])
                            int_hr_rows.append(mid_hr_rows)
                            mid_hr_rows = []

                        al_rows = ["".join(ele) for ele in int_hr_rows]

                        fin_rows = [None] * len(al_rows)
                        for e, ele in enumerate(al_rows):
                            ne = str(ele)
                            ne_s = ne.strip()
                            fe = re.sub(' +', ' ', ne_s)
                            fin_rows[e] = fe

                        mls_dup = 0
                        sb_dup = 0

                        if re.findall(r'\b(area|width)\b', str(hnews[len(hnews) - 1]), flags=re.IGNORECASE):
                            mls_dup = len(re.findall(r'\b(area|width)\b', str(hnews[len(hnews) - 1]), flags=re.IGNORECASE))

                        if re.findall(r'\b(front|side|rear)\b', str(hnews[len(hnews) - 1]), flags=re.IGNORECASE):
                            sb_dup = len(
                                re.findall(r'\b(front|side|rear)\b', str(hnews[len(hnews) - 1]), flags=re.IGNORECASE))

                        dups = [0] * len(fin_rows)

                        for w, word in enumerate(fin_rows):
                            if re.findall(r'\b(minimum\slot\ssize|minimum\slot\sarea)\b', str(word), flags=re.IGNORECASE):
                                dups[w] = 1 * mls_dup
                            elif re.findall(r'\b(minimum\ssetbacks|setbacks)\b', str(word), flags=re.IGNORECASE):
                                dups[w] = 1 * sb_dup
                            else:
                                dups[w] = 1

                        if dups:
                            hr_lst = [] * sum(dups)
                        else:
                            continue
                        if sum(dups) > 1:
                            for f, frow in enumerate(fin_rows):
                                if dups[f] > 1:
                                    for r in range(dups[f]):
                                        hr_lst.append(fin_rows[f])
                                else:
                                    hr_lst.append(fin_rows[f])

                        hr_int = " ".join(hr_lst)

                    else:
                        continue

                #############################
                ## create header: method 2 ##
                #############################

                elif re.findall(trigger_words_s, all_table_fin, flags=re.IGNORECASE):
                    #print("YES - METHOD 2")
                    h_words_in = re.findall(trigger_words_s, all_table_fin, flags=re.IGNORECASE)
                    h_start_list = [m.start(0) for m in re.finditer(trigger_words_s, all_table_fin, flags=re.IGNORECASE)]
                    h_start_list.reverse()
                    zd_flag = 0
                    mnumflag = 1
                    mnum_candidates = []
                    mnum_lengths = []
                    if re.findall(r"""(?x)(?:\b(zoning\sdistrict(?!\sregulations)|residential\sdistrict(?!\sregulations)|use\sdistrict|
                                   zoning\sdistricts|residential\sdistricts|use\sdistricts|zone\sdistrict|
                                   district(?!\sregulations)|districts|use\sclassification|use\s(?!setback)|uses\s)\b)""",
                                  all_table_fin, flags=re.IGNORECASE):
                        zd_start_list = [m.start(0) for m in re.finditer(
                            r"""(?x)(?:\b(zoning\sdistrict(?!\sregulations)|residential\sdistrict(?!\sregulations)|use\sdistrict|
                                   zoning\sdistricts|residential\sdistricts|use\sdistricts|zone\sdistrict|
                                   district(?!\sregulations)|districts|use\sclassification|use\s(?!setback)|uses\s)\b)""",
                            all_table_fin, flags=re.IGNORECASE)]
                        zd_start_list.reverse()
                        zd_start = max(zd_start_list)
                        if any(ele in h_start_list for ele in zd_start_list):
                            for ele in zd_start_list:
                                if ele in h_start_list:
                                    if abs(h_start_list[h_start_list.index(ele)] - h_start_list[
                                        h_start_list.index(ele) - 1]) < 50:
                                        mnum_candidates.append(h_start_list.index(ele))
                                        mnum_lengths.append(abs(h_start_list[h_start_list.index(ele)] - h_start_list[
                                            h_start_list.index(ele) - 1]))
                                        break
                                    else:
                                        continue
                                else:
                                    continue
                    if mnum_candidates:
                        mnumflag = 0
                        x = min(mnum_lengths)
                        xpos = mnum_lengths.index(x)
                        mnum = mnum_candidates[xpos]
                    elif 1 < len(h_start_list) < 10:
                        for n, num in enumerate(h_start_list):
                            if n < len(h_start_list) - 1:
                                if abs(h_start_list[n + 1] - h_start_list[n]) > 55:
                                    mnum = n
                                    break
                            else:
                                mnum = n
                    elif mnumflag == 1 and len(h_start_list) >= 20:
                        h_start_list.reverse()
                        for n, num in enumerate(h_start_list):
                            if n < len(h_start_list) - 1:
                                if abs(h_start_list[n + 1] - h_start_list[n]) < 55:
                                    mnum = n
                                    break
                                else:
                                    mnum = n
                    else:
                        mnum = len(h_start_list) - 1

                    newlist = []
                    h_start = int(h_start_list[mnum])
                    h_start_final = h_start

                    header_temp_temp = all_table_fin[h_start_final:h_stop]

                    if re.findall(r"""(?x)shall\smeet\sthe\sfollowing|may\sbe\sallowed\sby\sspecial\spermit|
                                         uses\scustomarily\sincident|sedimentation|adjacent\sto\sroadways|
                                         none\snone|outdoor\sarea\sthe\srequire|tower\stype|in\sno\scase\sshall|
                                         minimum\slot\ssize\sand\swidth\sin\sa\scluster\sdevelopment\szone| 
                                         \d+\ssquare\sfeet\sfor\seach|there\sshall\snot\sbe\sless\sthan|
                                         church|synagogue|landscaped\sarea|height\s\d+\sfeet|shall\sbe\sincluded|
                                         where\ssuch\suse\sis\spermitted|\d+\ssquare\sfeet|maximum\s+from\s+r\d\-|
                                         standards\.\sthe\snet|are\spermitted\soutright\:|set\sforth\sin|saturation|
                                         low\sdensity\s+single\sfamily\sresidential\sdetached|including\sexisting\sstreets|
                                         none\srequire\snone\srequire|mobile\shomes|district\sshall\shave\sa|
                                         (?<!sf\-d)\d\.\ssingle\sfamily|other\sthan\ssingle\sand\stwo|\d+\.*\d*\sacre|
                                         restrictions\sr\-1\sresidential|property\slocated|as\sdefined\sby|proposed\sin|
                                         all\sdwellings\serected|permitted\suses\sdescription|total\ssign\sarea|
                                         at\sseq\.\s\d\.|\d+\s+acre\sminimum|except\sthat|mobile\sfood|\_+\s\d+\'|
                                         parking\sarea|traffic|except\sas\sprovide|\d\slot\sfor\severy\s\d\sacre|
                                         structure\smay\sbe\serected|aviation|shall\sbe|additionally|as\sneed\sto|dollars|
                                         designed\sto|parking\sand\sloading\srequire|except\sfor\sthe|in\sthis|from\sany\sexisting|
                                         now\sor|all\scontiguous\slike|any\sother\sstructure\.|number\sof\strees|provide\showever|
                                         see\sresidential|for\snew\ssubdivisions|lot\sarea\snone\sresidential|floorplate|
                                         must\smeet\sthe|stables|\d+\sfeet\sfor|in\sresponse|this\schapter|abutting\sa|
                                         facades\sof\saccessory\sstructures|amended|directly\sabuts|charitable|are\sas|
                                         shall\sbe|proposed|mixture|supportive|maximum\s\d+\sheight|there\sis\sno|formula|
                                         will\sbe|which\sproduce|centuries""", header_temp_temp, flags=re.IGNORECASE):
                        continue

                    if len(re.findall(r'\w{1}\.\w+|\:', header_temp_temp, flags=re.IGNORECASE)) > 2:
                        continue
                    if len(re.findall(numbers, header_temp_temp, flags=re.IGNORECASE)) > 4:
                        continue

                    if len(header_temp_temp) < 45:
                        continue

                    ## re-reverse the h start list ##
                    h_start_list.reverse()

                    ## re-insert legitimate words that were skipped ##
                    newlista = h_start_list.index(h_start_final)
                    newlistb = [i for i, v in enumerate(h_start_list) if v < h_start_final]
                    newlistc = [i for i, v in enumerate(h_start_list) if v > h_start_final]

                    newlist = [newlista]
                    newlist.extend(newlistb)
                    newlist.extend(newlistc)

                    neworder = [h_words_in[i] for i in newlist]

                    hr_int = neworder

                    ## header row ##
                    if len(hr_int) <= 2:
                        continue

                    #print("HR INT")
                    #print(hr_int)

                    rd = {'minimum size per zoning lot': ['area in square feet', 'width in feet', 'area', 'width'],
                          'area and width req. in feet': ['lot area square feet', 'lot area per family', 'lot width'],
                          'minimum lot size':['square feet per dwelling unit', 'lot width in feet at bldg. line',
                                              'district area in square feet', 'square feet per additional family',
                                              'minimum district size in acre', 'depth',
                                              'lot width in feet', 'area in square feet', 'width in feet',
                                              'area per dwelling unit', 'area', 'width'],
                          'minimum lot area': ['lot width in feet at bldg. line',
                                               'area per dwelling unit', 'area', 'width', 'square feet'],
                          'minimum lot area per dwelling unit': ['square feet per dwelling unit',
                                                                 'square feet/dwelling unit'],
                          'minimum lot dimensions':['area square feet', 'width square feet', 'depth feet'],
                          'minimum lot require': ['lot area', 'frontage', 'total', 'per family', 'width', 'depth'],
                          'minimum area require': ['area','width','depth'],
                          'minimum require': ['lot area', 'lot width', 'lot depth'],
                          'lot dimensions': ['area square feet', 'width square feet', 'depth feet', 'area','frontage'],
                          'lot size minimum':['area','width'],
                          'lot size': ['square feet per dwelling unit', 'lot width in feet at bldg. line',
                                       'district area in square feet', 'square feet per additional family',
                                        'minimum district size in acre',
                                        'lot width in feet', 'area in square feet', 'width in feet',
                                        'area per dwelling unit', 'area', 'width'],
                          'minimum lot frontage':['feet'],
                          'minimum yards require': ['front yard setback in ft', 'side yard in feet',
                                                    'rear yard in feet', 'front yard setback', 'front yard', 'rear yard', 'side yard'
                                                    'front', 'side', 'each corner', 'rear'],
                          'minimum yard require': ['front yard setback in ft', 'side yard in feet', 'rear yard in feet',
                                                   'front yard setback', 'front yard', 'rear yard', 'side yard',
                                                   'front', 'side', 'each corner', 'rear','street yard'],
                          'minimum yard regulations': ['front yard setback in ft', 'side yard in ft', 'rear yard in ft',
                                                       'front yard setback', 'side yard width', 'rear yard depth',
                                                       'front', 'side', 'each corner', 'rear'],
                          'minimum yard setback': ['front', 'one side', 'each side', 'total', 'rear', 'side'],
                          'minimum yard dimensions': ['front feet', 'rear feet', 'side feet', 'side  feet',
                                                      'depth of front yard', 'depth of side yard',],
                          'minimum yard': ['front','side','aggregate','rear'],
                          'minimum yards': ['front','side','aggregate','rear'],
                          'setback require in feet': ['front','side','rear'],
                          'yard setbacks minimum': ['front', 'one side', 'each side', 'total', 'rear', 'side'],
                          'yard setbacks': ['front', 'one side', '1 side', 'each side', 'total', 'rear', 'side'],
                          'yards principal building': ['front and side front', 'each side', 'rear'],
                          'yards accessory building': ['side', 'rear'],
                          'minimum parking setback': ['front','each side', 'rear'],
                          'maximum bulk require': ['bldg. coverage', 'height', 'buffer strip'],
                          'maximum height in feet': [],
                          'maximum building height': ['stories', 'feet', 'principal','accessory'],
                          'building height maximum': ['stories', 'feet','principal','accessory'],
                          'maximum height': ['feet', 'stories','principal','accessory'],
                          'building height': ['feet', 'stories','principal','accessory'],
                          'side': ['interior','exterior','corner'],
                          'height': ['feet', 'stories'],
                          'maximum building coverage':['principal percent','accessory percent'],
                          'maximum lot coverage': ['percent of lot'],
                          'minimum open space': ['percent of lot']}

                    flist = ['maximum height in feet', 'maximum building height', 'building height maximum']
                    lwrep = 0
                    for word, initial in rd.items():
                        if word == "height" and "height" in hr_int:
                            if any(ele in hr_int for ele in flist):
                                continue
                            elif (hr_int.index("height") != len(hr_int)-1 and hr_int[hr_int.index("height")+1] == "stories") or (hr_int[hr_int.index("height")-1] == "stories" and hr_int.index("height") != 0):
                                continue
                        repset = []
                        finspots = []
                        spotstr = []
                        repwords = []
                        for n, k in enumerate(initial):
                            if word in hr_int and k in hr_int:
                                spots = [i for i, j in enumerate(hr_int) if j == k]
                                spots_rd = [i for i in spots if i >= lwrep]
                                if spots_rd:
                                    spot = spots_rd[0]
                                    finspots.append(spot)
                        if finspots:
                            finspots.sort()
                            for s in finspots:
                                spotstr.append(hr_int[s])
                                repwords.append(hr_int[s])
                            newinit = [y for x, y in zip(spotstr, repwords)]
                            repwds = 0
                            for j, k in enumerate(newinit):
                                if word in hr_int and k in hr_int:
                                    wpos = hr_int.index(word)
                                    repset.append(k)
                                    if hr_int.index(k) > lwrep:
                                        hr_int.remove(k)
                                    repwds = repwds + 1
                                    if j == len(newinit)-1:
                                        lwrep = hr_int.index(word) + repwds
                            if repset:
                                hr_int[wpos:wpos + 1] = repset

                    ## join everything together ##
                    hr_int = " ".join(hr_int)
                    #print("HEADER PRE")
                    #print(hr_int)

                    prehrwords = re.findall(trigger_words_s, hr_int, flags=re.IGNORECASE)
                    prehrwords_un = list(dict.fromkeys(prehrwords))

                    if len(prehrwords_un) < 2:
                        #print("PROBABLY NOT A REAL TABLE")
                        continue

                    if len(hr_int) >= 4000:
                        #print("WAY TOO LONG")
                        continue

                    hprenums = re.findall(numbers, hr_int, flags=re.IGNORECASE)
                    if len(hprenums) > 5:
                        #print("THIS IS NOT A TABLE")
                        continue

                    ntable_flag = re.findall(r"""(?x)(?:)\b(\d+\ssquare\sfeet|\d+\sacre|\d+\sacre|\d+\sfeet|pud|pdd|
                                             \d+\ssq\sft|\d+\ssq\.\sfeet|\d+\sft|\d+\sfeet)\b""", hr_int,
                                             flags=re.IGNORECASE)
                    if ntable_flag:
                        #print("CAPTURING ROWS NOT JUST HEADER")
                        continue

                    if 250 < len(hr_int) < 4000:
                        #print("LENGTH > 250")

                        if re.findall(mls_ind, hr_int, flags=re.IGNORECASE):
                            mls_pre = [m.start(0) for m in re.finditer(mls_ind, hr_int, flags=re.IGNORECASE)]
                        else:
                            continue

                        mls_trig_res = re.findall(mls_ind, hr_int, flags=re.IGNORECASE)
                        h_trig_flag_pre = 0
                        if len(mls_pre) > 1 and mls_pre[0] == 0:
                            h_trig_flag_pre = 1
                            mls_start_pre = mls_pre[1]
                        else:
                            mls_start_pre = mls_pre[0]

                        h_trig_words_pre = re.findall(trigger_words_s, hr_int, flags=re.IGNORECASE)

                        h_trig_words_pre_un = list(dict.fromkeys(h_trig_words_pre))

                        h_trig_list_pre = [h.start(0) for h in re.finditer(trigger_words_s, hr_int, flags=re.IGNORECASE)]
                        if h_trig_flag_pre == 1:
                            h_trig_words_pre.remove(h_trig_words_pre[h_trig_list_pre.index(0)])
                            h_trig_list_pre.remove(0)

                        dups_pre = [0] * len(h_trig_words_pre_un)

                        mhdflag = 0
                        mlsdflag = 0

                        for w, word in enumerate(h_trig_words_pre_un):
                            if w != len(h_trig_words_pre_un) - 1:
                                if h_trig_words_pre_un[w] == "stories" and h_trig_words_pre_un[w + 1] == "feet":
                                    mhdflag = 1
                                    break
                                if h_trig_words_pre_un[w] == "area" and h_trig_words_pre_un[w + 1] == "frontage":
                                    mlsdflag = 1
                                    break

                        for w, word in enumerate(h_trig_words_pre_un):
                            if word == 'maximum height' and mhdflag == 1:
                                dups_pre[w] = 1 * 2
                            elif re.findall(mls_ind, str(word), flags=re.IGNORECASE) and mlsdflag == 1:
                                dups_pre[w] = 1 * 2
                            else:
                                dups_pre[w] = 1

                        hr_lst_pre = [] * sum(dups_pre)
                        if sum(dups_pre) > 1:
                            for f, frow in enumerate(h_trig_words_pre_un):
                                if dups_pre[f] > 1:
                                    for r in range(dups_pre[f]):
                                        hr_lst_pre.append(h_trig_words_pre_un[f])
                                else:
                                    hr_lst_pre.append(h_trig_words_pre_un[f])

                        if (len(hr_lst_pre) >= 2 and
                                re.findall(r'\b(zoning\sdistrict|zone|district|districts)\b', str(hr_lst_pre[0]),
                                           flags=re.IGNORECASE) and
                                re.findall(r'\b(zoning\sdistrict|zone|district|districts)\b', str(hr_lst_pre[1]),
                                           flags=re.IGNORECASE)):
                            hr_lst_pre.remove(hr_lst_pre[0])

                        hr_int = " ".join(hr_lst_pre)

                else:
                    continue

                sent_flag = re.findall(r'\b(is|was|are|the|or|as|an|has|of)\b', hr_int, flags=re.IGNORECASE)
                if len(sent_flag) > 10:
                    #print("TOO MUCH TEXT")
                    continue

                if len(hr_int) > 500:
                    #print("HEADER IS STILL TOO LONG")
                    continue

                if re.findall(header_stopwords, hr_int, flags=re.IGNORECASE):
                    #print("HEADER HAS STOPWORDS")
                    continue

                if re.findall(r"""(?x)\b(maximum\sheight|building\sheight|maximum\sbldg\.\sheight|height)\b""", hr_int, flags=re.IGNORECASE) and re.findall(r"(?<=stories\s)feet|feet(?=stories)|stories", hr_int, flags=re.IGNORECASE):
                    h1st = [m.start(0) for m in re.finditer(r"\b(maximum\sheight|building\sheight|maximum\sbldg\.\sheight|height)\b", hr_int, flags=re.IGNORECASE)][0]
                    h2st = [m.start(0) for m in re.finditer(r"(?<=stories\s)feet|feet(?=stories)|stories", hr_int, flags=re.IGNORECASE)][0]
                    if h1st < h2st:
                        hr_int = re.sub(r"\b(maximum\sheight|building\sheight|maximum\sbldg\.\sheight|height)\b", "", hr_int)

                if not re.findall(r'district(?!\sarea\sin\ssquare\sfeet)|(?<!minimum\s)zone|zoning\sdistrict|residential\sdistrict|uses|use\sclassification|zoning\sclassification',
                        str(hr_int[0:50]),
                        flags=re.IGNORECASE):
                    hr1 = "zoning district " + hr_int
                else:
                    hr1 = hr_int

                hrstart_list = [m.start(0) for m in re.finditer(
                    r"""\b(zoning\sclassification|district|(?<!minimum\s)zone|zoning\sdistrict|residential\sdistrict|use\s|uses\s)\b""",
                    hr1)]
                for cl in hrstart_list:
                    hrstart_check = hr1[int(cl):]
                    if len(hrstart_check) > 25:
                        hrstart = cl
                        break
                    else:
                        hrstart = hrstart_list[len(hrstart_list) - 1]

                ## create final header
                if hrstart_list:
                    hr = hr1[int(hrstart):]
                else:
                    hr = hr1

                h_nums = re.findall(numbers, hr, flags=re.IGNORECASE)

                if len(h_nums) > 3:
                    continue

                #print("FINAL HEADER")
                #print(hr)

                ## rest of the rows ##
                body_rows = []
                row_lens = []
                rflag = 0

                #print("ROWS")
                #print(row_start)
                for j, n in enumerate(row_start):
                    if n < h_stop:
                        continue
                    if len(row_start) == 1:
                        row_in = text_extract_r[row_start[j]:len(text_extract_r)]
                        row = re.sub(r'\||\+|\-{2,}', '', row_in)
                        if len(row) > 250:
                            row = ""
                        if "ecode360" in row:
                            break
                        body_rows.append(row)
                    elif j != len(row_start) - 1:
                        row_in = text_extract_r[row_start[j]:row_start[j + 1]]
                        row = re.sub(r'\||\+|\-{2,}', '', row_in)
                        row_len = len(row)
                        row_lens.append(row_len)
                        if j > 1:
                            if abs(row_len - max(row_lens[0:j - 1])) < 100:
                                if len(row) > 250:
                                    row = ""
                                if "ecode360" in row:
                                    break
                                body_rows.append(row)
                            else:
                                row_lens.sort()
                                row_fin = row_lens[-2]
                                init_row = text_extract_r[row_start[j]:row_start[j + 1]]
                                for chunk in chunks(init_row, row_fin):
                                    if len(chunk) > 250:
                                        chunk = ""
                                    if "ecode360" in row:
                                        break
                                    body_rows.append(chunk)
                        else:
                            if len(row) > 250:
                                row = ""
                            if "ecode360" in row:
                                break
                            body_rows.append(row)
                    else:
                        row_in = text_extract_r[row_start[j]:row_start[j] + 100]
                        row = re.sub(r'\||\+|\-{2,}', '', row_in)
                        if re.findall(r'\d+\s*$', text_extract_s, flags=re.IGNORECASE) and len(row) < len(hr) + 5:
                            row = ""
                        if re.findall(stopwords, str(row), flags=re.IGNORECASE):
                            row = ""
                        if "ecode360" in row:
                            break
                        body_rows.append(row)

                ## keep only unique rows ##
                body_rows_un = list(dict.fromkeys(body_rows))

                #print("COLLECTION OF ROWS")
                #print(body_rows_un)

                #print("NUMBER OF ROWS")
                #print(len(body_rows_un))

                if len(body_rows_un) > 50:
                    continue

                body_rows_un_nm = list(filter(None, body_rows_un))

                if len(body_rows_un_nm) < 3 and not any(ele in ['district','area'] for ele in re.findall(trigger_words_s, hr, flags=re.IGNORECASE)):
                    continue

                ## look for minimum lot size trigger words ##

                mls_cand = re.findall(mls_ind, hr, flags=re.IGNORECASE)

                #print("MLS CANDIDATE NAMES")
                #print(mls_cand)

                if mls_cand:
                    mls = [m.start(0) for m in re.finditer(mls_ind, hr, flags=re.IGNORECASE)]
                else:
                    continue

                #print("MLS CANDIDATES STARTING POSITIONS")
                #print(mls)

                h_trig_flag = 0
                if len(mls) > 1 and mls[0] == 0:
                    h_trig_flag = 1
                    mls_start = mls[1]
                elif re.findall(r'\b(minimum\slot\ssize|minimum\slot\sarea|area\sin\ssquare\sfeet|square\sfeet)\b', str(mls_cand),
                                flags=re.IGNORECASE) and re.findall(
                        r"""(?x)\b(minimum\slot\sarea\sper\sdwelling\sunit|(?<!site\s)area\sper\sdwelling\sunit|square\sfeet\sper\sdwelling\sunit|
                        square\sfeet\/dwelling\sunit|square\sfeet\sper\sadditional\sfamily|area\/du)\b""",
                        str(mls_cand), flags=re.IGNORECASE):
                    mls_start = [m.start(0) for m in re.finditer(
                        r"""(?x)\b(minimum\slot\sarea\sper\sdwelling\sunit|(?<!floor\s)area\sper\sdwelling\sunit|square\sfeet\sper\sdwelling\sunit|
                        square\sfeet\/dwelling\sunit|square\sfeet\sper\sadditional\sfamily|area\/du)\b""",
                        hr,
                        flags=re.IGNORECASE)][0]
                else:
                    mls_start = mls[0]

                #print("MLS STARTING POSITION")
                #print(mls_start)

                h_trig_words = re.findall(trigger_words_s, hr, flags=re.IGNORECASE)

                h_trig_list = [h.start(0) for h in re.finditer(trigger_words_s, hr, flags=re.IGNORECASE)]
                if h_trig_flag == 1:
                    h_trig_words.remove(h_trig_words[h_trig_list.index(0)])
                    h_trig_list.remove(0)

                #print("KEY VARS")
                #print(h_trig_words)

                #print("KEY VAR POSITIONS")
                #print(h_trig_list)

                mls_match = None

                for a in mls:
                    if len(mls) > 1 and a in h_trig_list:
                        hfind1 = re.compile(r"""(?x)(?:minimum\slot\sarea\sper\sdwelling|minimum\slot\sarea\sper\sdwelling\sunit|minimum\slot\sarea\sper\sdu|
                                           minimum\slot\sarea\sper\sunit|lot\sarea\sper\sunit|(?<!floor\s)area\sper\sdwelling\sunit|minimum\slot\sarea\sper\sfamily|
                                           area\sin\ssquare\sfeet\sper\sadditional\sfamily|square\sfeet\sper\sadditional\sfamily|area\/du|
                                           square\sfeet\sper\sdwelling\sunit|square\sfeet\/dwelling\sunit)""", flags=re.IGNORECASE)
                        hfind2 = re.compile(r"""(?x)(?:minimum\slot\ssize|minimum\slot\sarea|area\sin\ssquare\sfeet|mininimum\slot\sarea|minimum\snet\slot\sarea|square\sfeet)""", flags=re.IGNORECASE)
                        if hfind1.findall(hr) and hfind2.findall(hr):
                            try:
                                if re.findall(r'\b(minimum\slot\sarea\sper\sdwelling)\b', str(hr), flags=re.IGNORECASE):
                                    r = re.compile(r"\b(minimum\slot\sarea\sper\sdwelling)\b")
                                    mls_match_pre = h_trig_words.index(list(filter(r.match, h_trig_words))[0])
                                    mls_match = h_trig_list[mls_match_pre]
                                    break
                                elif re.findall(r'\b(minimum\slot\sarea\sper\sdwelling\sunit|minimum\slot\sarea\sper\sdu)\b', str(hr), flags=re.IGNORECASE):
                                    r = re.compile(r"\b(minimum\slot\sarea\sper\sdwelling\sunit|minimum\slot\sarea\sper\sdu)\b")
                                    mls_match_pre = h_trig_words.index(list(filter(r.match, h_trig_words))[0])
                                    mls_match = h_trig_list[mls_match_pre]
                                    break
                                elif re.findall(r'\b(lot\sarea\sper\sdwelling\sunit|(?<!site\s|floor\s)area\sper\sdwelling\sunit|minimum\slot\sarea\sper\sunit|lot\sarea\sper\sunit)\b', str(hr), flags=re.IGNORECASE):
                                    r = re.compile(r"\b(lot\sarea\sper\sdwelling\sunit|(?<!site\s|floor\s)area\sper\sdwelling\sunit|minimum\slot\sarea\sper\sunit|lot\sarea\sper\sunit)\b")
                                    mls_match_pre = h_trig_words.index(list(filter(r.match, h_trig_words))[0])
                                    mls_match = h_trig_list[mls_match_pre]
                                    break
                                elif re.findall(r'\b(minimum\slot\sarea\sper\sfamily)', str(hr), flags=re.IGNORECASE):
                                    r = re.compile(r"\b(minimum\slot\sarea\sper\sfamily)\b")
                                    mls_match_pre = h_trig_words.index(list(filter(r.match, h_trig_words))[0])
                                    mls_match = h_trig_list[mls_match_pre]
                                    break
                                elif re.findall(r'\b(area\sin\ssquare\sfeet\sper\sadditional\sfamily|square\sfeet\sper\sadditional\sfamily)\b', str(hr), flags=re.IGNORECASE):
                                    r = re.compile(r"\b(area\sin\ssquare\sfeet\sper\sadditional\sfamily|square\sfeet\sper\sadditional\sfamily)\b")
                                    mls_match_pre = h_trig_words.index(list(filter(r.match, h_trig_words))[0])
                                    mls_match = h_trig_list[mls_match_pre]
                                    break
                                elif re.findall(r"\b((?<!floor\s)area\/du|minimum\slot\sarea\/du|minimum\sarea/du\stotal\sdensity)\b", str(hr),
                                            flags=re.IGNORECASE):
                                    r = re.compile(r"\b((?<!floor\s)area\/du|minimum\slot\sarea\/du|minimum\sarea/du\stotal\sdensity)\b")
                                    mls_match_pre = h_trig_words.index(list(filter(r.match, h_trig_words))[0])
                                    mls_match = h_trig_list[mls_match_pre]
                                    break
                                elif re.findall(r"\b((?<!area\s)square\sfeet\/dwelling\sunit|(?<!area\s|area\sin\s)square\sfeet\sper\sdwelling\sunit)\b", str(hr), flags=re.IGNORECASE):
                                    r = re.compile(r"\b((?<!area\s)square\sfeet\/dwelling\sunit|(?<!area\s|area\sin\s)square\sfeet\sper\sdwelling\sunit)\b")
                                    mls_match_pre = h_trig_words.index(list(filter(r.match, h_trig_words))[0])
                                    mls_match = h_trig_list[mls_match_pre]
                                    break
                            except ValueError:
                                continue
                        else:
                            mls_match = a
                            break
                    else:
                        mls_match = mls_start

                rstartflag = 0
                mfflag = 0

                for row in body_rows_un:
                    if re.findall(r"""(?x)(?:notes\:|footnotes\:|shall\smeet\sall\sregulations\sof|following\:|
                                     miscellaneous\sprovides\:|parking\sregulations\:|additional\sregulations\:|
                                     notes\:|[a-z]\.\smaximum\snumber\sof|special\sdistrict\szoning\sis\srequested|
                                     according\sto\sthe|\(\w+\)\sthe\sbuilding\srequire|mhp\sillustration|
                                     editor\'s\snote\:|footnotes\sto\stable|passed\s\d+\-\d+\-\d+|amended\s\d+\-\d+|
                                     the\soriginal\ssite\splan\swas|table\s\d+\-\d+|conditional\suses\:|see\smotor|
                                     the\szoning\sordinance|click\shere|curving\sstreet)""", row, flags=re.IGNORECASE):
                        break
                    if re.findall(
                            r"""(?x)(?:\b(mh|outdoor\sactivity|pool|field|court|schools|school|page|commercial|rounded\sdown\sto|
                            round\sdown\sto|prud|rooms|livestock|mobile\shome|shall|all\sother\suses|b\-\d+|footnote|footnotes|
                            senior\scitizen|cluster|pdr\stract|yard\sabutting|adjacent\sto\sstate\swater\sbody|livestock|animal\shusbandry|
                            cemeteries|funeral|educational\sinstitutions|places\sof\sworship|li|multiply|balance\ssheet|conditional)\b|non\-res|
                            other\spermitted\suses|daycare\scenter|playground|leisure\sclub|sterling\scodifiers|service|extraction\sof\searth\sproducts|
                            emergency\sservices\scenter|park\sand\sride|utility\sfacilities|utility\sservice|wireless\scommunication|archery|
                            concerts|fairground|non\-dwellings|table\s\d+\sschedule|open\sspace\sper\sdwelling\sunit|other\suses|
                            other\sallowed\sprincipal\suse|park|residential\>\d+\-\s*\d+|community|low\srise\smultiple|high\srise\smultiple|mid\srise\smultiple|
                            any\sany\sany\szone\slot|conditional\suses|shopping\scenters|shopping\scenter|more\sthan\s\d+\sbut\sless\sthan\s\d+|
                            added\s\d{2}\-\d{1}\-\d{4}|however|phar\.d\.|industrial)""",
                            row, flags=re.IGNORECASE):
                        row = ""
                    if re.findall(trigger_words_s, row, flags=re.IGNORECASE) and not re.findall(
                            r'\b(front|side|rear|square\sfeet|feet|district|density|stories|uses|principal|accessory|total|per\sunit)\b', row,
                            flags=re.IGNORECASE):
                        if rstartflag == 0:
                            continue
                        elif rstartflag == 1:
                            break
                    if not re.findall(row_trig, row, flags=re.IGNORECASE):
                        continue
                    rstartflag = 1
                    nrow_in = re.sub(r"each\s\d+\sboth\d|any\spermitted\suse", "", row)
                    nrow_in2 = re.sub(r"\([^()]*\)|ref\:\s\-\s\d+\-\d+", '', nrow_in)
                    nrow = re.sub(r"2f","two-family",nrow_in2)
                    nrow2 = nrow

                    if re.findall(r"\d+\sper\s\d+\ssquare\sfeet\sof\slot\sarea", nrow, flags=re.IGNORECASE):
                        news = re.findall(numbers, nrow, flags=re.IGNORECASE)
                        newsn = [float(i) for i in news]
                        newf = max(newsn) / min(newsn)
                        newport = newf
                        nrow2 = re.sub(r"\d+\sper\s\d+\ssquare\sfeet\sof\slot\sarea", str(newport), nrow)

                    newrow = nrow2.split(' ')
                    newrowf = list(filter(None, newrow))
                    newrowf_og = newrowf
                    if len(newrowf) == 1:
                        continue

                    ## fix all problems with rows ##

                    for w, word in enumerate(newrowf):
                        newword = re.sub('\d+\'', 'na', word)
                        if w != len(newrowf) - 1 and re.findall(r'du\/\d+|ac\/\d+', word, flags=re.IGNORECASE):
                            nwm = re.findall(r'du\/\d+|ac\/\d+', word, flags=re.IGNORECASE)
                            nwm_text = " ".join(nwm)
                            numstorep = re.findall(numbers, nwm_text, flags=re.IGNORECASE)
                            numstorep.append('acre (du/ac)')
                            if (newrowf[w - 1] == "1" and newrowf[w + 1] == "acre") or (
                                    newrowf[w - 1] == "1" and newrowf[w + 1] == "dwellings"):
                                newrowf[w - 1] = " ".join(numstorep)
                                newrowf[w] = ""
                                newrowf[w + 1] = ""
                                break
                        elif w != 0 and "-" in word:
                            nwordsp = word.split("-")
                            if nwordsp[1] == "family" or nwordsp[1] == "fm":
                                newword = ''
                            elif len(word) == 1:
                                newword = word
                            elif nwordsp[0].isdigit():
                                newword = nwordsp[0]
                            else:
                                newword = nwordsp[1]
                        elif w != 0 and not re.findall(
                                r"""(?x)\d{1}\.\d+|acre|ac\.|\bna\b|stories|maximum\sdwelling\sunit\sper\sstructure|
                                n\/a|\%|unit|per|\bi\b""",
                                newword,
                                flags=re.IGNORECASE) and re.findall(r'[^0-9]', newword,
                                                                    flags=re.IGNORECASE):
                            newword = re.sub(r'[^0-9]', '', newword)
                        newrowf[w] = newword

                    rowv2 = list(filter(None, newrowf))

                    #print("ROW V2")
                    #print(rowv2)

                    rowv2_set = set(rowv2)
                    acreinfo_set = set(acreinfo_s)

                    for w, word in enumerate(rowv2):
                        if w != 0 and word in acreinfo_s and not re.findall(r'r\-m|multiple\sresidence', str(row), flags=re.IGNORECASE):
                            rowv2[w - 1] = rowv2[w - 1] + " " + word
                            rowv2[w] = ""
                        elif w!= 0 and word == "unit":
                            rowv2[w-1] = rowv2[w-1] + " " + word
                            rowv2[w] = ""
                        elif w != 0 and word == "stories":
                            rowv2[w - 1] = rowv2[w - 1] + " " + word
                            rowv2[w] = ""

                    rowv3 = list(filter(None, rowv2))

                    #print("ROW V3")
                    #print(rowv3)

                    for w, word in enumerate(rowv3):
                        if len(word) == 1 and word.isdigit():
                            if w <= len(h_trig_words) - 1:
                                if re.findall(mls_ind, str(h_trig_words[w]), flags=re.IGNORECASE) and not re.findall(
                                        r'r\-m|multiple\sresidence', str(row), flags=re.IGNORECASE):
                                    continue
                                elif re.findall(
                                        r"""(?x)\b(density|maximum\sdwelling\sunit\sper\sstructure|accessory\sstructures|
                                        maximum\sdwelling\sunit\sper\sgross\sacre|maximum\sdwelling\sunit\sper\sbuildable\sacre|
                                        stories|unit\sper\slot|side)\b""",
                                        str(h_trig_words[w]), flags=re.IGNORECASE):
                                    continue
                                else:
                                    rowv3[w] = ""

                        if re.findall(r'percent\d*', word, flags=re.IGNORECASE):
                            rowv3[w] = ""

                    rowv4 = list(filter(None, rowv3))

                    #print("ROW V4")
                    #print(rowv4)

                    ncheck = ['district', 'zone', 'zoning district', 'residential district',
                              'districts', 'zones', 'zoning districts', 'residential districts',
                              'use classification', 'zoning classification', 'uses']

                    if any(ex in hr for ex in ncheck):
                        numvars = len(h_trig_list)
                    else:
                        numvars = len(h_trig_list) + 1

                    rowv4_text = " ".join(rowv4)

                    if len(rowv4) > 2 * numvars and not re.findall(acreinfo_s, rowv4_text, flags=re.IGNORECASE) and not re.findall(sqftinfo_s, rowv4_text, flags=re.IGNORECASE) and not re.findall(r"bdr\.", row, flags=re.IGNORECASE):
                        x = re.findall(r'\b(acre|ac\.)\b', rowv4_text, flags=re.IGNORECASE)
                        frow = [''] * numvars
                        frow[0] = rowv4[0]
                        for r in range(1, numvars, 1):
                            nlist = [re.sub('[^0-9]', '', s) for s in rowv4]
                            nlist = list(filter(None, nlist))
                            nnums = list(map(int, nlist[r::numvars - 1]))
                            if any(ele >= 4000 for ele in nnums):
                                continue
                            if nnums:
                                frow[r] = str(max(nnums))
                            else:
                                frow[r] = ''
                    else:
                        frow = rowv4

                    #print("FROW")
                    #print(frow)

                    frow_text = " ".join(frow)

                    ## ACRES ##

                    acre_matches = []
                    acre_trig1 = 0
                    acre_trig2 = 0
                    acre_trig1_res = re.findall(acreinfo_s, hr, flags=re.IGNORECASE)
                    if re.findall(r'\b(mhd\-r|pud|pdr\stract|office|cem|cbd|phard|mobile\shome|c\-\d+)\b', frow_text, flags=re.IGNORECASE):
                        continue
                    if len(acre_trig1_res) == 0:
                        acre_trig1 = 0
                    elif len(acre_trig1_res) == 1 and re.findall(r'per\sgross\sacre', hr, flags=re.IGNORECASE):
                        acre_trig1 = 0
                    elif len(acre_trig1_res) >= 1:
                        acre_trig1 = 1
                    if re.findall(acreinfo_s, frow_text, flags=re.IGNORECASE):
                        acre_trig1 = 1
                    if re.findall(acreinfo_s, text_extract_s, flags=re.IGNORECASE):
                        acre_trig2 = 1
                    if acre_trig1 == 1 or acre_trig2 == 1:
                        nums = []
                        if acre_trig1 == 1:
                            if re.findall(r'\d+\sacre\s\(du\/ac\)', frow_text, flags=re.IGNORECASE):
                                match = re.findall(r'\d+\sacre\s\(du\/ac\)', frow_text, flags=re.IGNORECASE)
                                match_text = " ".join(match)
                                nums = re.findall(numbers, match_text, flags=re.IGNORECASE)
                            elif mls_match in h_trig_list:
                                if any(ex in hr for ex in ncheck):
                                    match_num = h_trig_list.index(mls_match)
                                else:
                                    match_num = h_trig_list.index(mls_match) + 1
                                if len(frow) >= match_num + 1:
                                    match = frow[match_num]
                                    if match is None:
                                        match = ""
                                    if re.findall(r'stories|unit', match, flags=re.IGNORECASE):
                                        match = ""
                                    if match.count('.') > 1:
                                        match = ""
                                    nums = re.findall(numbers, match, flags=re.IGNORECASE)
                        elif acre_trig2 == 1:
                            if re.findall(r"""(?x)\b(largest|unit\sper|per\sacre|per\sgross\sacre|
                                           per\snet\sacre|unit\/acre)\b""", row, flags=re.IGNORECASE):
                                continue
                            if mls_match in h_trig_list:
                                if any(ex in hr for ex in ncheck):
                                    match_num = h_trig_list.index(mls_match)
                                else:
                                    match_num = h_trig_list.index(mls_match) + 1
                                if len(frow) >= match_num + 1:
                                    match = frow[match_num]
                                    if match is None:
                                        match = ""
                                    if match.count('.') > 1:
                                        match = ""
                                    if re.findall(r'stories|unit', match, flags=re.IGNORECASE):
                                        match = ""
                                    if re.findall(r'(\d+)\/acre\.*', match, flags=re.IGNORECASE):
                                        pre_match = re.sub(r'(\d+)\/acre\.*', r'\1', match)
                                        grp = ["1", pre_match]
                                        new_match = "/".join(grp)
                                        match = fractonum(new_match)
                                    nums = re.findall(numbers, match, flags=re.IGNORECASE)
                        for y in nums:
                            if re.findall(r'\b(multi\sfamily|multi\-\sfamily|duplex|two\-family|two\sfamily|multi\-fm)\b', row, flags=re.IGNORECASE):
                                continue
                            if i == 0 and re.findall(r'\b(r\-\d+|residential|agriculture|ag|suburban|a\-\d+|rfwp)\b', str(frow[0]),
                                          flags=re.IGNORECASE):
                                if float(y.replace(',', '')) <= 50:
                                    acre_res.append(y)
                            else:
                                if float(y.replace(',', '')) <= 5:
                                    acre_res.append(y)

                    ## SQFT ##

                    sqft_matches = []
                    sqft_trig1 = 0
                    sqft_trig2 = 0
                    sqft_trig3 = 0
                    if re.findall(sqftinfo_s, hr, flags=re.IGNORECASE):
                        sqft_trig1 = 1
                    if re.findall(sqftinfo_s, text_extract_s, flags=re.IGNORECASE):
                        sqft_trig2 = 1
                    if re.findall(numbers, text_extract_s, flags=re.IGNORECASE):
                        nums_m = re.findall(numbers, text_extract_s, flags=re.IGNORECASE)
                        if any(float(ele.replace(',', '')) >= 500 for ele in nums_m):
                            sqft_trig3 = 1
                    if sqft_trig1 == 1 or sqft_trig2 == 1 or sqft_trig3 == 1:
                        nums = []
                        if sqft_trig1 == 1:
                            if mls_match in h_trig_list:
                                if any(ex in hr for ex in ncheck):
                                    match_num = h_trig_list.index(mls_match)
                                else:
                                    match_num = h_trig_list.index(mls_match) + 1
                                if len(frow) >= match_num + 1:
                                    match = frow[match_num]
                                    nums = re.findall(numbers, match, flags=re.IGNORECASE)
                        elif sqft_trig2 == 1 or sqft_trig3 == 1:
                            if re.findall(sqftinfo_s, row, flags=re.IGNORECASE) or re.findall(r'\d{3,6}', row,
                                                                                              flags=re.IGNORECASE):
                                if mls_match in h_trig_list:
                                    if any(ex in hr for ex in ncheck):
                                        match_num = h_trig_list.index(mls_match)
                                    else:
                                        match_num = h_trig_list.index(mls_match) + 1
                                    if len(frow) >= match_num + 1:
                                        match = frow[match_num]
                                        nums = re.findall(numbers, match, flags=re.IGNORECASE)
                        for y in nums:
                            if re.findall(r"""(?x)\b(ah|multi\sfamily|multi\-\sfamily|multifamily|duplex|two\-family|
                                                two\sfamily|planned|r\-t|r\-hh|r\-ga\d+|r\-gai|r\-gaii|ah\-\d+|
                                                affordable\shousing|apartment)\b""", row, flags=re.IGNORECASE):
                                if 380 <= float(y.replace(',', '')) < 15000:
                                    sqft_res.append(y)
                            elif 380 <= float(y.replace(',', '')):
                                sqft_res.append(y)

                    ## UNITS ##
                    unit_trig1 = 0
                    unit_trig2 = 0

                    md = []

                    if re.findall(unitinfo_s, hr, flags=re.IGNORECASE) or re.findall(r'maximum\sdensity|maximum\snet\sdensity|max\sdua', hr, flags=re.IGNORECASE):
                        unit_trig1 = 1
                    if re.findall(unitinfo_s, text_extract_s, flags=re.IGNORECASE):
                        unit_trig2 = 1
                    if unit_trig1 == 1 or unit_trig2 == 1:
                        md = [m.start(0) for m in re.finditer(unitinfo_s, hr, flags=re.IGNORECASE)]
                    else:
                        md = []

                    if md:
                        md_start = md[0]
                    elif re.findall(r'maximum\sdensity|maximum\snet\sdensity', hr, flags=re.IGNORECASE):
                        md_start = [m.start(0) for m in re.finditer(r'maximum\sdensity|maximum\snet\sdensity', hr, flags=re.IGNORECASE)][0]
                    else:
                        md_start = 0

                    unit_matches = []
                    nums = []
                    if unit_trig1 == 1:
                        if md_start in h_trig_list:
                            if any(ex in hr for ex in ncheck):
                                match_num = h_trig_list.index(md_start)
                            else:
                                match_num = h_trig_list.index(md_start) + 1
                            if len(frow) >= match_num + 1:
                                match = frow[match_num]
                                nums = re.findall(numbers, match, flags=re.IGNORECASE)
                    elif unit_trig2 == 1:
                        if re.findall(unitinfo_s, row, flags=re.IGNORECASE):
                            if md_start in h_trig_list:
                                if any(ex in hr for ex in ncheck):
                                    match_num = h_trig_list.index(md_start)
                                else:
                                    match_num = h_trig_list.index(md_start) + 1
                                if len(frow) >= match_num + 1:
                                    match = frow[match_num]
                                    nums = re.findall(numbers, match, flags=re.IGNORECASE)
                    for y in nums:
                        if float(y.replace(',', '')) <= 165:
                            unit_res.append(y)

                    ## height start ##

                    if frow in rowhcm:
                        continue
                    else:
                        rowhcm.append(frow)

                    if frow and re.findall(r"\bi\b", frow[0], flags=re.IGNORECASE):
                        continue

                    if re.findall(height_ind, hr, flags=re.IGNORECASE):
                        ht_words_in = re.findall(height_ind, hr, flags=re.IGNORECASE)
                        ht_words = list(set(h_trig_words) & set(ht_words_in))
                        ht_pos_in = [h.start(0) for h in re.finditer(height_ind, hr, flags=re.IGNORECASE)]
                        ht_pos = list(set(h_trig_list) & set(ht_pos_in))
                    else:
                        continue

                    flist = ['maximum height', 'max building height', 'maximum building height', 'building height maximum','max ht','principal',
                             'building height']

                    if ht_pos:
                        if "stories" in h_trig_words:
                            height_start_st = h_trig_words.index("stories")
                        else:
                            height_start_st = 0
                        if "feet" in h_trig_words:
                            height_start_ft = h_trig_words.index("feet")
                        elif any(ele in flist for ele in h_trig_words):
                            ele = [x for x in flist if x in h_trig_words][0]
                            height_start_ft = h_trig_words.index(ele)
                        else:
                            height_start_ft = 0
                    else:
                        continue

                    ## STORIES ##

                    nums_st = []
                    if height_start_st > 0:
                        if len(frow) >= height_start_st + 1:
                            match_st = frow[height_start_st]
                            nums_st = re.findall(numbers, match_st, flags=re.IGNORECASE)
                        if nums_st:
                            for y in nums_st:
                                if float(y.replace(',', '')) <= 50:
                                    height_st_res.append(y)

                    ## FEET ##

                    nums_ft = []
                    if height_start_ft > 0:
                        if len(frow) >= height_start_ft + 1:
                            match_ft = frow[height_start_ft]
                            nums_ft = re.findall(numbers, match_ft, flags=re.IGNORECASE)
                        for y in nums_ft:
                            if float(y.replace(',', '')) <= 165:
                                height_ft_res.append(y)

        acre_res_final[i].extend(acre_res)
        acre_res = []

        unit_res_final[i].extend(unit_res)
        unit_res = []

        sqft_res_final[i].extend(sqft_res)
        sqft_res = []

    bt_minfo = acre_res_final[0] + sqft_res_final[0]
    bt_dinfo = acre_res_final[1] + unit_res_final[1] + sqft_res_final[1]
    bt_hinfo_ft = height_ft_res
    bt_hinfo_st = height_st_res
    bt_minfo_full = list(dict.fromkeys(bt_minfo))
    bt_dinfo_full = list(dict.fromkeys(bt_dinfo))
    hinfo_ft_num = [float(i) for i in bt_hinfo_ft]
    hinfo_st_num = [float(i) for i in bt_hinfo_st]

    return [bt_minfo_full, bt_dinfo_full, hinfo_ft_num, hinfo_st_num]


'''
buildtable2 is the second function meant to parse information stored in dimensional tables. It takes an input string
with flags indicating the presence of a dimensional table. This function, as opposed to buildtablel1, parses 
dimensional tables in which rows generally indicate dimensional criteria (e.g., minimum lot size) and columns indicate 
different zoning districts (e.g., R-1). 

This function proceeds through a series of steps to eventually extract the necessary dimensional information:

1. First, complete regex searches for a word or phrase indicating dimensional tables
2. Determine how many columns of a potential table exist and proceed if this number exceeds some threshold 
3. Determine where the rows begin and work backwards from this point to construct the table header 
4. Next, reformat the rows 
5. Now, with the dimensional table information parsed, determine if the header contains any keywords pertaining
   to minimum lot size, maximum density, or building height maximums. 
6. Extract the correct information from step 5

'''

def buildtablel2(input1, input2):
    inlist = [input1, input2]
    test1 = inlist[0]
    test2 = inlist[1]
    acre_res = []
    unit_res = []
    sqft_res = []
    height_res_ft = []
    height_res_st = []
    acre_res_final1 = []
    acre_res_final2 = []
    acre_res_final = [acre_res_final1, acre_res_final2]
    unit_res_final1 = []
    unit_res_final2 = []
    unit_res_final = [unit_res_final1, unit_res_final2]
    sqft_res_final1 = []
    sqft_res_final2 = []
    sqft_res_final = [sqft_res_final1, sqft_res_final2]

    table_words = ["schedule", "dimensional stardards", "dimensional table",
                   "zoning district", "residential district", "residential district r-1",
                   "residential district r-a", "residential r-2 district",
                   "residential r-3 district", "residential r-4 district",
                   "dimensional require", "dimensional and density regulations", "dimensional regulations",
                   "development standards", "residential zones", "minimum lot size"]

    table_words_s = r"""(?x)          # Turn on free spacing mode
                      \b
                      (schedule(?!\sof\sdimensional\scontrols\samended\s)|zoning\sdistrict(?!\sclassification\.|\.\s\w+\.)|
                      dimensional\srequire|zoning\sdistrict\srules\sand\sregulations|
                       dimensional\sand\sdensity\sregulations|dimensional\sregulations(?!\.\s\(\w+\)|\.\s\d+\sspecial\sexception|\stable\.\stable)|lot\sand\sbulk\sstandards|
                       development\sstandards|dimensional\sstandards|intensity\sregulations|height\sand\sarea\srequire|
                       \w{1}\.\s+minimum\slot\ssize|bulk\sand\sreplacement|district\sdesign\srequire|lot\sstandards\sby\szone|
                       development\sregulations|lot\sdimension\sand\sintensity\sstandards|density\sand\sbulk\srequire|
                       bulk\sand\splacement\sregulations|district\sregulations|land\sspace\srequire|bulk\sregulations(?!\.\s\(\w+\))|
                       lot\sarea\sfrontage\sand\syard\srequire|yard\sand\sheight\srequire|dimension\srestrictions|area\sand\sbulk\sstandards|
                       lot\sstandards\smatrix|other\sdimensions\sand\sspace\srequire|area\syard\sand\sheight\sregulations|
                       bulk\sand\sarea\sstandards|density\sschedule|development\scriteria\sdistrict|zone\sstandards|site\sdimensions|
                       height\slimit\slot\ssizes\sand\scoverage|bulk\sand\sarea\sregulations|bulk\srequire|spatial\srequire|
                       land\suse\sdistrict\sand\sallowable\suses|bulk\sand\ssetback\sregulations|residential\sbulk\schart\s(?!at\sthe\send)|
                       bulk\smatrix|residential\suses\sand\srequire|standards\sfor\sprincipal\sbuildings\son\sindividual\slots|
                       lot\sand\syard\srequire|intensity\sof\suse|dimensional\scontrols(?!\samended\s)|lot\srequire|lot\syard\sand\sdensity\sregulations|
                       height\sand\sarea\sregulations|zoning\sdistrict\sregulation\schart|area\syard\sand\sheight\sstandards|
                       bulk\sand\scoverage\scontrols|summary\sof\szoning\sdistrict\srequire|dimensional\stable|
                       area\sand\sbulk\sschedule|lot\syard\sarea\sand\sheight\srequire|area\syard\sand\sheight\srequire|
                       height\sand\syard\srequire|height\sand\slot\srequire|area\ssetback\sand\sheight\srequire|
                       height\sarea\sand\syard\srequire|bulk\sspace\sand\syard\srequire|bulk\sand\syard\sregulations|zoning\sdistricts|
                       density\sdimensions\sand\sother\sstandards|zone\sdwelling\sfamily\ssize|(?<!set\sforth\sthe\s)space\sdimensions(?!\.))
                      \b|(?<!conservation\s)districts\:|bulk\sschedules
                      """

    trigger_words = ["standards", "r-1a", "r-1b", "r-1c", "r-1", "r-2", "r-2sf", "r-22f", "r-3", "r-4", "r-5", "re-"]

    row_trig = r"""(?x)
                (
                \b
                (minimum\snet\slot\sarea|average\sminimum\slot\sarea|tnd\sminimum\slot\sarea|
                minimum\srequire\slot\sarea|minimum\slot\sarea|net\slot\sarea\sminimum|site\sarea|
                minimum\slot\ssize|maximum\sdensity|minimum\sdensity|density\sfactor\srange|density|open\sspace\sratio|
                minimum\stotal\sliving\sarea\sper\sdwelling\sunit|minimum\stotal\sliving\sarea\sper\sdwelling|
                lot\sarea\sper\sdwelling\sunit|lot\sarea|bedrooms|efficiency\sapartment|apartment|minimum\syards|
                minimum\snet\ssite\sarea|minimum\sparcel\ssize|parcel\size|maximum\sdensity|density\smaximum|
                density\sranges|parcel\sarea\smin|residential\sdensity|density|minimum\/maximum\sdistrict\ssize|
                minimum\slot\sfrontage|without\stown\swater\sor\ssewer|lot\ssize|setback|building\sheight|lot\sareas|
                maximum\sheight|accessory\sbldg\sheight|building\sheight|maximum\sbldg\.\sheight|minimum\slivable\sfloor\sarea\sper\sunit|
                building\scoverage|project\slot\sarea|dwelling\sunit\/lot|dwelling\sunit\sper\sacre|minimum\sdwelling\sunit|
                road\sfrontage|height(?!\sregulation)|lot\scoverage|floor\sarea|(?<!\d+\'\s\(|\d+\s\()1\-story|(?<!\d+\'\s\(|\d+\s\()2\-story|siting|
                front\ssetback|side\ssetback|least|total\sof\sboth|rear\ssetback|lot\sarea|principal\sresidential\sstructures|
                accessory\sstructures|setbacks|lot\ssquare\sfootage\sper\sdu|townhouse|district\sin\swhich\suse\sis\spermitted|
                minimum\sfront\ssetback|minimum\srear\ssetback|minimum\sside\ssetback|minimum\sside\sstreet\ssetback|
                minimum\slot\swidth|lot\swidth|frontage|minimum\stotal\sopen\sspace|minimum\susable\sopen\sspace|
                non\-dwellings|(?<!feet\/)stories(?!\swhichever)|maximum\sheight\d*|open\sspace|impervious\ssurface|
                minimum\syard\swidths|minimum\syard\swidth|front\syard|side\syard|rear\syard|width|depth|accessory\sstructure|
                all\sother\spermitted\sand\sspecial\suse\slots|permitted\suses|conditional\suses|maximum\ssite\sarea|
                minimum\sdistance\sfrom\sstreet|accessory\sbldg|require\sparking\sspaces|project\sarea|area(?!\sregulations))
                \b|notes\:
                )"""

    # trigger_words_s = r"""\b(residential\sestate|standards|additional\sstandards|r\-1w*|r\-2|r\-|re\-|r1\-|r|hr\-)\b"""
    trigger_words_s = r"""(?x)(?:\b(residential\sestate|standards|additional\sstandards|r\-1\w*|r\-2|r\-3|b\-\d+|m\-\d+|
                             r\-\d+|rs\-\d+|rm\-\d+|ar\-\d+|c\-\d+|u\-\d+|m\-\d+|mu\-\d+|s\-\d+|s\-conservancy|r1a|r1b|r\d{1}|c\d{1}|
                             re\d+|rs\d+|ra\d+|rm\d+|sfr\-\d+|mfr\-\d+|r\-\d+\.\d+|ru\-\d+|ru\-\w+|rml|rmh|lr\s\d+|rg\d+|
                             general\srequire|zoning\sdistrict(?!\.\s\w+\.)|r\-|re\-|rr\-|rs\-|r1\-|r\w{1}|r\d{1}|rld|rmd|rhd|a\-\d+|b\-\d+|
                             nr|sn|mp|mu|uc|td|r|hr\-|ro|nb|rto|re\-\d+|ru\-\d+|cb|gb|gr\d*|nb|hb|icd|li|hi|sr\-\d+|mr\-\d+|umu|gc|rs|rt|
                             a\-r|r\-r|s\-r|r\-\d+|r\-\d+|dp\-\d+|mf\-\d+|sf\-\w{1}|sf\-\d+|sfe\-\d+|zl\-\d+|s2f|crs|cb|clo|cro|csx|
                             mb|umc|cmu|rc|ra|bip|c\-\d+cn|cg|cm|m\-\d|n\-c|os|building(?!\sheight|\sor)|space\sdimensions|
                             single\sfamily|two\sfamily|multi\sfamily|mdr|ldr|
                             conservation|very\shigh\-*\sdensity\sresidential|high\-*\sdensity\sresidential|
                             medium\-*\sdensity\sresidential|low\-*\sdensity\sresidential|
                             neighborhood\sresidential\s\d+|corridor\sresidential|town\scenter\sresidential|
                             (?<!for\s)residential|office|industrial|umf|smf|usf|ssf|utf|rr|agriculture|guest\sranches|
                             single\sfamily\sdwellings|conditional\suses|use)\b)"""

    hr_res_info = r"""(?x)(?:\b(residential\sestate|(?<!lot\s)standards|additional\sstandards|r\d+|r\-1\w*|r\-2|r\-3|m\-\d+|
                             general\srequire|zoning\sdistrict|r\-|re\-|rr\-|rs\-|r1\-|r\w{1}|r\d{1}|rld|rmd|rhd|r\-\d{1}\-\w{1}|
                             re\d+|rs\d+|ra\d+|rm\d+|sfr\-\d+|mfr\-\d+|a\-r|r\-r|s\-r|r\-\d+|r\-\d+|dp\-\d+|mf\-\d+|
                             nr|sn|mp|mu|uc|td|r|hr\-|ro|nb|rto|re\-\d+|ru\-\d+|cb|gb|sr\-\d+|mr\-\d+|umu|a\-\d+|b\-\d+|
                             mb|umc|cmu|rc|ra|bip|cn|cg|cm|m\-\d|os|sf\-\d+|sf\-\w{1}|sfe\-\d+|zl\-\d+|s2f|rg\d+|
                             single\sfamily\sdwelling|single\sfamily\sdwellings|
                             single\sfamily|two\sfamily|multi\sfamily|guest\sranches|
                             conservation|very\shigh\-*\sdensity\sresidential|high\-*\sdensity\sresidential|
                             neighborhood\sresidential\s\d+|corridor\sresidential|town\scenter\sresidential|
                             medium\-*\sdensity\sresidential|low\-*\sdensity\sresidential|
                             residential|agriculture|single\sfamily\sdwellings)\b)"""

    trigger_h_words_s = r"""(?x)(?:\b(r\-1\w*|r\-2|r\-3|b\-\d+|m\-\d+|r\-|re\-|rr\-|rs\-|r1\-|r\w{1}|r\d{1}|rld|rmd|rhd|
                             rs\-\d+|rm\-\d+|ar\-\d+|a\-r|r\-r|s\-r|r\-\d+|r\-\d+|dp\-\d+|mf\-\d+|a\-\d+|b\-\d+|r\-\d{1}\-\w{1}|
                             r|hr\-|ro|nb|rto|re\-\d+|ru\-\d+|cb|gb|mb|umc|cmu|rc|ra|bip|cn|cg|cm|m\-\d|os|umf|smf|
                             neighborhood\sresidential\s\d+|corridor\sresidential|town\scenter\sresidential|
                             usf|ssf|utf|rr|)\b)"""

    height_ind = r"""(?x)(?:\b(maximum\sheight|building\sheight|maximum\sbldg\.\sheight|height)\b)"""

    endlist1 = []
    endlist2 = []
    endlist = [endlist1, endlist2]
    rowhcm = []

    for i in range(2):
        stlist = list(deepflatten(inlist[i], 1))
        rflist = []
        for string in stlist:
            rf_string = re.sub(r'\s\/', '-', string, flags=re.IGNORECASE)
            rflist.append(fractonum(rf_string))
        for string in rflist:
            try:
                endlist[i].append(text2int(string))
            except ValueError:
                endlist[i].append('')
            except IndexError:
                endlist[i].append('')

    for i in range(2):
        for string in endlist[i]:

            ## simply determine if this part of the text is actually a table ##
            text_extract = []
            if re.findall(table_words_s, string, flags=re.IGNORECASE):
                extract = re.findall(table_words_s, string, flags=re.IGNORECASE)
                mpos_og = [m.start(0) for m in re.finditer(table_words_s, string, flags=re.IGNORECASE)]
                mpos1 = [[p - 30, p + 2000] for p in mpos_og]
                for n, t in enumerate(mpos1):
                    t = [0 if x < 0 else x for x in t]
                    t = [len(string) if x > len(string) else x for x in t]
                    mpos1[n] = t
                clips1 = []
                for r, run in enumerate(mpos1):
                    clip = string[run[0]:run[1]]
                    clips1.append(clip)
                text_extract = list(dict.fromkeys(clips1))

            for ex in text_extract:
                text_extract_t1 = re.sub(r'2\sfamily', "two family", ex)
                text_extract_t2 = re.sub(r'amended\-\d\/\d+\s\d\-\d+', "", text_extract_t1)
                text_extract_s = text_extract_t2

                #print("TEXT EXTRACT L2")
                #print(text_extract_s)

                if re.findall(r"""(?x)(?:\b(high\sintensity\sindustrial\suses|heavy\smanufacturing|example|chicken|coop|solar|
                                wind|electricity|\~|dimensional\srequire\sfor\sassisted\sliving\sresidences|
                                br\-cd\szoning\sdistrict\sdevelopment\sstandards|by\saverage\slot\ssize\son\sblock|
                                table\sof\sdimensional\sstandards\snonresidential\straditional\szoning\sdistricts|
                                manufacturing\szones\sdevelopment\sstandard|to\sprovide\ssites\sfor|
                                ei\szoning\sdistrict\sdevelopment\sstandards)\b|\(\w\)\sgroup\shomes\s\(adult\)\.)""", text_extract_s,
                          flags=re.IGNORECASE):
                    #print("NOT RESIDENTIAL TABLE FLAG")
                    continue

                sflags = re.findall(r'\s\w{1}\.\s|\d{1}\.\s', text_extract_s, flags=re.IGNORECASE)
                if len(sflags) > 25:
                    #print("NOT A TABLE")
                    continue

                total_count = []
                for j in text_extract:
                    hits = re.findall(trigger_words_s, j, flags=re.IGNORECASE)
                    count = len(hits)
                    total_count.append(count)

                ## get the column names ##

                if re.findall(trigger_words_s, text_extract_s, flags=re.IGNORECASE):
                    cols = re.findall(trigger_words_s, text_extract_s, flags=re.IGNORECASE)
                    total_cols_un = list(dict.fromkeys(cols))
                else:
                    continue

                #print("TOTAL COLUMNS")
                #print(len(total_cols_un))

                #print("COLUMN NAMES")
                #print(total_cols_un)

                ## now organize the rows ##

                if len(total_cols_un) < 2:
                    continue

                ## this is the start of the header row ##
                tab_start_list = [m.start(0) for m in re.finditer(table_words_s, text_extract_s, flags=re.IGNORECASE)]

                if tab_start_list:
                    tab_start = int(tab_start_list[0])
                else:
                    tab_start = 0

                ## this indicates when the rows begin ##
                ## the first row marks the end of the header row ##

                if re.findall(row_trig, text_extract_s, flags=re.IGNORECASE):
                    hr_end = [m.start(0) for m in re.finditer(row_trig, text_extract_s, flags=re.IGNORECASE)]
                else:
                    continue

                ## end of header ##
                if len(hr_end) >= 1:
                    for st in hr_end:
                        test_hr = text_extract_s[tab_start:st]
                        if len(test_hr) > 0 and len(list(dict.fromkeys(re.findall(numbers, test_hr, flags=re.IGNORECASE)))) <= 3 and len(list(dict.fromkeys(re.findall(trigger_words_s, test_hr, flags=re.IGNORECASE)))) > 2:
                            h_stop = st
                            break
                        else:
                            h_stop = len(text_extract_s)
                else:
                    h_stop = len(text_extract_s)

                ## start of header ##
                all_table = text_extract_s[tab_start:h_stop]

                #print("TABLE")
                #print(all_table)

                if re.findall(trigger_words_s, all_table, flags=re.IGNORECASE):
                    h_start_list = [m.start(0) for m in re.finditer(trigger_words_s, all_table, flags=re.IGNORECASE)]
                    if len(h_start_list) > 1:
                        for n, num in enumerate(h_start_list):
                            if n < len(h_start_list) - 2:
                                rl12 = abs(h_start_list[n] - h_start_list[n + 1])
                                rl23 = abs(h_start_list[n + 1] - h_start_list[n + 2])
                                if rl12 < 30 and rl23 < 30:
                                    mnum = n
                                    break
                            else:
                                mnum = n
                    else:
                        mnum = 0
                    h_start = int(h_start_list[mnum])

                else:
                    continue

                h_start_final = h_start

                ## header row ##
                hr_int = all_table[h_start_final:h_stop]

                #print("HEADER PRE")
                #print(hr_int)

                if re.findall(trigger_h_words_s, str(hr_int[0:5]), flags=re.IGNORECASE):
                    hr = "building " + hr_int
                else:
                    hr = hr_int

                if len(hr) > 500:
                    if re.findall(r"zoning\sdistrict|zoning\sdistricts|residential\sdistrict", all_table,
                                  flags=re.IGNORECASE):
                        zdpos = [m.start(0) for m in
                                 re.finditer(r"zoning\sdistrict|zoning\sdistricts|residential\sdistrict", all_table,
                                             flags=re.IGNORECASE)]
                        zdpos.reverse()
                        newhstart = zdpos[0]
                        hr = all_table[newhstart:]
                        if len(hr) > 500:
                            #print("HEADER STILL TOO LONG")
                            continue
                    else:
                        continue

                if re.findall(header_stopwords, hr, flags=re.IGNORECASE) or len(
                        re.findall(r'\band\b', hr, flags=re.IGNORECASE)) > 2:
                    #print("HEADER HAS STOPWORDS")
                    continue

                resinfo = re.findall(hr_res_info, hr, flags=re.IGNORECASE)
                resinfo_un = list(dict.fromkeys(resinfo))
                if len(resinfo_un) < 2:
                    #print("HEADER ONLY HAS NON-RESIDENTIAL INFO")
                    continue

                if len(hr) < 20:
                    #print("NOT THE CORRECT HEADER")
                    continue

                h_trig_words = re.findall(trigger_words_s, hr, flags=re.IGNORECASE)

                nchwords = re.findall(r"\b(residential|building|dimensional|industrial)\b", str(h_trig_words),
                                      flags=re.IGNORECASE)

                if len(h_trig_words) < 2 or (len(h_trig_words) == 3 and len(nchwords) >= 2) or (
                        len(h_trig_words) == 2 and len(nchwords) >= 1):
                    #print("NOT A VALID HEADER PT.1")
                    continue

                h_nums = re.findall(numbers, hr, flags=re.IGNORECASE)
                h_nums_un = list(dict.fromkeys(h_nums))

                if len(h_nums_un) > 3:
                    #print("NOT A VALID HEADER PT.2")
                    continue

                #print("HEADER")
                #print(hr)

                ## initialize rows ##

                row_start = [m.start(0) for m in re.finditer(row_trig, text_extract_s, flags=re.IGNORECASE)]

                ## width of rows ##
                len_rows = []
                for r, row in enumerate(row_start):
                    if r != len(row_start) - 1:
                        row_extract = text_extract_s[row_start[r]:row_start[r + 1]]
                        len_rows.append(len(row_extract))
                    else:
                        row_extract = text_extract_s[row_start[r]:]
                        len_rows.append(len(row_extract))
                if len(len_rows) == 1:
                    rw = len_rows[0]
                else:
                    rw = max(len_rows)

                ## rest of the rows ##
                body_rows = []
                rowf_lens = []
                for j, n in enumerate(row_start):
                    if n < h_stop:
                        continue
                    if len(row_start) == 1:
                        row = text_extract_s[row_start[j]:len(text_extract_s)]
                        body_rows.append(row)
                    elif j != len(row_start) - 1:
                        row = text_extract_s[row_start[j]:row_start[j + 1]]
                        rowf = row[0:rw]
                        rowf_len = len(rowf)
                        rowf_lens.append(rowf_len)
                        if j > 0:
                            if abs(rowf_len - max(rowf_lens[0:j])) < 100:
                                body_rows.append(rowf)
                            else:
                                rowf_lens.sort()
                                rowf_fin = rowf_lens[-2]
                                init_row = text_extract_s[row_start[j]:row_start[j + 1]]
                                for chunk in chunks(init_row, rowf_fin):
                                    body_rows.append(chunk)
                        else:
                            body_rows.append(rowf)
                    else:
                        row = text_extract_s[row_start[j]:len(text_extract_s)]
                        rowf = rowf = row[0:rw]
                        if re.findall(r'\d+\s*$', text_extract_s, flags=re.IGNORECASE) and len(row) < len(hr) + 5:
                            row = ""
                        body_rows.append(row)

                if re.findall(r"""(?x)provide\sthe\sfollowing\scondition|churches|separation\sbetween\saccessory\sbuildings\s\d+\sfeet|
                                 classification\sby\sbuffer|spaces\sper\sdwelling|church\ssubject|purpose\sand|except|
                                 district\s\(\d+\)\ssquare\sfeet|in\sconjunction\swith|should\sbe|and\s*$""", hr, flags=re.IGNORECASE):
                    #print("HEADER FLAG")
                    continue

                body_rows_un = list(dict.fromkeys(body_rows))

                #print("COLLECTION OF ROWS")
                #print(body_rows_un)

                if len(body_rows_un) > 50:
                    # print("TOO MANY ROWS")
                    continue

                endwords = r'\b(attachment)\b|notes\:|ecode360|footnotes\:|as\sstated\sin\sthe\sfollowing\schart|\bl\-i\b'

                ## ACRES ##

                nums = []
                mhflags = re.findall(
                    r"""(?x)(?:\b(smf\-\d+|smf|mf\-\d+|mf|multi\sfamily|r\-mh|rmh\.*\d*|mh\.*\d*|rg\.*\d*|
                                mu\-\d+|i\-industrial|industrial|residential*\-*multi|commercial\.*|r\-m|
                                multi|ipud|pud|mhpd|c\-\d+|inst|m\-\d+|inst|b\-\d+|hpr\d*|p\.*r\.*\d*|crs|cs|cb|clo|
                                hi|li|icd|mhp|cro|crs|csx|prd)\b|b\-\d+|i\-\d+)""", hr, flags=re.IGNORECASE)
                if mhflags:
                    hr_split_pre = re.sub(r'[()]', '', hr)
                    hr_split = hr_split_pre.split(" ")
                    try:
                        if mhflags[0] == "multi family":
                            mhflagpos = hr_split.index("multi")
                        else:
                            mhflagpos = hr_split.index(mhflags[0])
                    except ValueError:
                        mhflagpos = len(hr_split) - 1
                for row in body_rows_un:
                    rowf = re.sub(r'\(\d+\)|\([^)]*\)', "", row)
                    if len(rowf) >= len(hr) * 9:
                        continue
                    if len(rowf) > 250:
                        continue
                    if len(re.findall(trigger_words_s, rowf, flags=re.IGNORECASE)) > 3 or re.findall(endwords, rowf, flags=re.IGNORECASE):
                        break
                    sent_flag = re.findall(r'\b(is|was|are|the|or|as|an|has|of|and|be)\b', rowf, flags=re.IGNORECASE)
                    if len(sent_flag) > 3:
                        break
                    if re.findall(r"""(?x)(?:\b(vehicle|industrial|editor\'s\snote|floor\sarea|mobile\shome|subdivision|puds|pud|average|number\sof\sstories|established\sin|passed|project\slot\sarea|
                                                commercial\scenter|grocery\sstore|tnd|maximum\ssite\sarea|planned\sdevelopment|non\-residential|
                                                non\-dwellings|(?<!minimum\s|minimum\snet\s)site\sarea|lot\ssize\smax|
                                                farm\shomestead|map\samendment|outdoor\sstorage\spiles)\b|\$for\slot\s\<|refer\sto\s\-)""", rowf, flags=re.IGNORECASE):
                        continue
                    if re.findall(r"mobile\shome", rowf, flags=re.IGNORECASE):
                        clip_rm = r'\d*\.*\d*.{0,10}' + r'mobile\shome' + r'.{0,10}\d*\.*\d*'
                        row = re.sub(clip_rm, "", rowf, flags=re.IGNORECASE)
                    if re.findall(r"maximum\sdensity\s\(du\/ac\)|maximum\sdensity\s\(dwelling\sunit\sper\sacre\)", rowf,
                                  flags=re.IGNORECASE):
                        nums = re.findall(numbers, str(rowf), flags=re.IGNORECASE)
                        for y in nums:
                            if 0 < float(y.replace(',', '')) <= 499:
                                aa = 1 / float(y)
                                acre_res.append(aa)
                    elif re.findall(r"""(?x)
                                     \b(minimum\slot\ssize|min\.\slot\sarea|minimum\slot\sarea|minimum\slot\srequire|lot\ssize|maximum\sdensity|
                                     minimum\slot\sarea\sper\sdwelling\sunit|lot\sarea\sminimum|lot\sarea|single\sfamily|minimum\sparcel\ssize|
                                     minimum\snet\ssite\sarea|lot\sareas|area)\b""", rowf, flags=re.IGNORECASE):
                        if re.findall(acreinfo_s, rowf, flags=re.IGNORECASE):
                            if re.findall(acreinfo_s, rowf[:25], flags=re.IGNORECASE):
                                rowf_s = rowf.split(" ")
                                for s, sword in enumerate(rowf_s):
                                    if s < len(rowf_s) - 1:
                                        if mhflags and not re.findall(r'per\sdwelling\sunit|\/dwelling\sunit', rowf, flags=re.IGNORECASE) and s >= mhflagpos:
                                            rowf_s[s] = ""
                                nums = re.findall(numbers, str(rowf_s), flags=re.IGNORECASE)
                            else:
                                rowf_s = rowf.split(" ")
                                for s, sword in enumerate(rowf_s):
                                    if s < len(rowf_s) - 1:
                                        if mhflags and (
                                                rowf_s[s + 1] == "acre" or rowf_s[s + 1] == "acre" or rowf_s[s + 1] == "ac") and not re.findall(r'per\sdwelling\sunit|\/dwelling\sunit', rowf, flags=re.IGNORECASE) and s >= mhflagpos:
                                            rowf_s[s] = ""
                                    if s != len(rowf_s) - 1:
                                        if re.findall(numbers, sword, flags=re.IGNORECASE) and not re.findall(
                                                r'acre|ac\.|ac',
                                                rowf_s[s + 1],
                                                flags=re.IGNORECASE):
                                            rowf_s[s] = ""
                                nums = re.findall(numbers, str(rowf_s), flags=re.IGNORECASE)
                            for y in nums:
                                if i== 0 and 10 < float(y.replace(',', '')) <= 50:
                                    if not mhflags:
                                        acre_res.append(y)
                                    else:
                                        lcap_txt = str(y+ " acre")
                                        for r in body_rows_un:
                                            try:
                                                if r.index(lcap_txt) < mhflagpos:
                                                    acre_res.append(y)
                                            except ValueError:
                                                continue
                                elif float(y.replace(',', '')) <= 10:
                                    acre_res.append(y)

                ## SQFT ##

                nums = []
                for row in body_rows_un:
                    rowf = re.sub(r'\(\d+\)|\([^)]*\)', "", row)
                    if len(rowf) >= len(hr) * 9:
                        continue
                    if mhflags and len(rowf) < len(hr)/4:
                        continue
                    if re.findall(r"""(?x)(?:\b(vehicle|industrial|open\sspace|floor\sarea|average|number\sof\sstories|established\sin|passed|
                                                commercial\scenter|grocery\sstore|maximum\ssite\sarea|planned\sdevelopment|non\-residential|
                                                site\splan\srequire\sa\ssite\splan\sin\saccordance|map\samendment|lot\ssize\smax|
                                                farm\shomestead)\b|\$|for\slot\s\<|refer\sto\s\-)""", rowf, flags=re.IGNORECASE):
                        continue
                    if len(re.findall(trigger_words_s, rowf, flags=re.IGNORECASE)) > 3 or re.findall(endwords, rowf, flags=re.IGNORECASE):
                        break
                    if re.findall(
                            r"maximum\sdensity|maximum\sdensity\s\(du\/ac\)|maximum\sdensity\s\(dwelling\sunit\sper\sacre\)",
                            rowf, flags=re.IGNORECASE):
                        nums = re.findall(numbers, str(rowf), flags=re.IGNORECASE)
                        for y in nums:
                            if float(y.replace(',', '')) > 500:
                                sqft_res.append(y)
                    if re.findall(r'\b(\d+\sacre)\b', rowf, flags=re.IGNORECASE):
                        acrenums = re.findall(r'\b(\d+\sacre)\b', rowf, flags=re.IGNORECASE)
                        nums = re.findall(numbers, str(acrenums), flags=re.IGNORECASE)
                        for y in nums:
                            if float(y.replace(',', '')) > 500:
                                continue
                    if re.findall(r"""(?x)
                                  \b(minimum\slot\ssize|min\.\slot\sarea|minimum\slot\sarea|maximum\sdensity|
                                  minimum\slot\sarea\sper\sdwelling\sunit|lot\sarea\sminimum|lot\sarea|minimum\sparcel\ssize|
                                  minimum\snet\ssite\sarea|lot\ssize|lot\sareas|(?<!living\s)area)\b""", rowf, flags=re.IGNORECASE):
                        rowf_s = rowf.split(" ")
                        for s, sword in enumerate(rowf_s):
                            if s < len(rowf_s) - 1:
                                if mhflags and not re.findall(r'per\sdwelling\sunit|\/dwelling\sunit', rowf, flags=re.IGNORECASE) and s >= mhflagpos:
                                    if sword.isdigit():
                                        if float(sword) < 15000:
                                            continue
                                        else:
                                            rowf_s[s] = ""
                                    else:
                                        rowf_s[s] = ""
                        nums = re.findall(numbers, str(rowf_s), flags=re.IGNORECASE)
                        if re.findall(sqftinfo_s, str(rowf_s), flags=re.IGNORECASE) or any(
                                float(ele) > 1000 for ele in nums):
                            nums = re.findall(numbers, str(rowf_s), flags=re.IGNORECASE)
                            for y in nums:
                                if 380 <= float(y.replace(',', '')):
                                    sqft_res.append(y)

                ## UNITS ##

                nums = []
                for row in body_rows_un:
                    rowf = re.sub(r'\(\d+\)|\d+\%', "", row)
                    if len(rowf) >= len(hr) * 9:
                        continue
                    if len(rowf) >= 250:
                        continue
                    if re.findall(r'\b(percent|map\samendment|open\sspace\sper)\b|\$|for\slot\s\<|refer\sto\s\-', rowf, flags=re.IGNORECASE):
                        continue
                    if len(re.findall(trigger_words_s, rowf, flags=re.IGNORECASE)) > 3 or re.findall(endwords, rowf, flags=re.IGNORECASE):
                        break
                    if re.findall(unitinfo_s, rowf, flags=re.IGNORECASE):
                        if re.findall(unitinfo_s, rowf, flags=re.IGNORECASE):
                            nums = re.findall(numbers, rowf, flags=re.IGNORECASE)
                            for y in nums:
                                if float(y.replace(',', '')) <= 165:
                                    unit_res.append(y)

                ## HEIGHT ##

                mhflags_ht = re.findall(
                    r"""(?x)(?:\b(mu\-\d+|i\-industrial|industrial|residential*\-*multi|commercial\.*|b\-\d+|o\-\d+|(?<!r\-)l\-\d+|h\-\d+|
                                multi|ipud|pud|mhpd|os|hi|li|icd|mhp|cro|crs|csx|prd|i\-\d+)\b)""", hr, flags=re.IGNORECASE)

                mhflagpos_ht = None

                if mhflags_ht:
                    hr_split_pre = re.sub(r'[()]', '', hr)
                    hr_split = hr_split_pre.split(" ")
                    try:
                        mhflagpos_ht = hr_split.index(mhflags_ht[0])
                    except ValueError:
                        mhflagpos_ht = len(hr_split) - 1

                nums = []
                for row in body_rows_un:
                    if len(resinfo_un) < 3:
                        continue
                    if len(re.findall(trigger_words_s, row, flags=re.IGNORECASE)) > 3 or re.findall(endwords, row, flags=re.IGNORECASE):
                        break
                    if row in rowhcm:
                        continue
                    else:
                        rowhcm.append(row)
                    rowsp = row.split(" ")
                    for s, sword in enumerate(rowsp):
                        if s < len(rowsp) - 1:
                            if mhflags_ht and not re.findall(r'per\sdwelling\sunit|\/dwelling\sunit', row,
                                    flags=re.IGNORECASE) and mhflagpos_ht != None and s >= mhflagpos_ht:
                                rowsp[s] = ""
                    rowspf = " ".join(rowsp)
                    rowf = re.sub(r'\(\d+\)|\d+\%', "", rowspf)
                    if len(rowf) >= len(hr) * 9:
                        continue
                    if len(rowf) >= 250:
                        continue
                    if re.findall(r"""(?x)\b(percent|map\samendment|outdoor\sstorage\spiles|religious|antenna|may\sbe\spermitted|
                                        property\sis\spart|or\sfraction\sthereof|building\scodes\ssubject\sto|
                                        industrial\szoning|commercial\szoning|building\sheight\swhichever\sis\sgreater|
                                        accessory\sdwelling\sunit|building\sheight\saccessory|cantilevered|
                                        maximum\sheight\sfor\saccessory\sbuildings|accessory\sbldg|                        
                                        if\sthe\sbuilding)\b|\$|for\slot\s\<""", rowf, flags=re.IGNORECASE):
                        continue
                    if re.findall(r'\battachment\b|notes\:|footnotes\:|part\s\d+\:', rowf, flags=re.IGNORECASE):
                        break
                    if re.findall(r"maximum\sbuilding\sheight|maximum\sheight|height", rowf, flags=re.IGNORECASE) and not re.findall(r'(?<!feet\/)stories|story', rowf[:10], flags=re.IGNORECASE):
                        if re.findall(r"maximum\sbuilding\sheight|maximum\sheight|height", rowf, flags=re.IGNORECASE):
                            rowf = re.sub(r"\d+\.", "", rowf)
                            nums = re.findall(numbers, rowf, flags=re.IGNORECASE)
                            for y in nums:
                                if 10 <= float(y.replace(',', '')) <= 165:
                                    height_res_ft.append(y)
                    if re.findall(r'(?<!feet\/)stories|story', rowf, flags=re.IGNORECASE):
                        if re.findall(r"pavement\sshall\snot\sbe", rowf, flags=re.IGNORECASE):
                            continue
                        if re.findall(r"maximum\sbuilding\sheight|maximum\sheight|height|stories", rowf, flags=re.IGNORECASE):
                            rowf = re.sub(r"\d+\'|\d+\.", "", rowf)
                            nums = re.findall(numbers, rowf, flags=re.IGNORECASE)
                            for y in nums:
                                if re.findall(r"feet", rowf, flags=re.IGNORECASE) and float(y.replace(',','')) < 10:
                                    height_res_st.append(y)
                                elif not re.findall(r"feet", rowf, flags=re.IGNORECASE) and float(y.replace(',', '')) < 100:
                                    height_res_st.append(y)

        acre_res_final[i].extend(acre_res)
        acre_res = []

        unit_res_final[i].extend(unit_res)
        unit_res = []

        sqft_res_final[i].extend(sqft_res)
        sqft_res = []

    bt_minfo = acre_res_final[0] + sqft_res_final[0]
    bt_dinfo = acre_res_final[1] + unit_res_final[1] + sqft_res_final[1]
    bt_hinfo_ft = height_res_ft
    bt_hinfo_st = height_res_st
    bt_minfo_full = list(dict.fromkeys(bt_minfo))
    bt_dinfo_full = list(dict.fromkeys(bt_dinfo))
    hinfo_ft_num = [float(i) for i in bt_hinfo_ft]
    hinfo_st_num = [float(i) for i in bt_hinfo_st]

    return [bt_minfo_full, bt_dinfo_full, hinfo_ft_num, hinfo_st_num]

'''
densityinfo captures all other dimensional information not stored in dimensional tables. With each input string, 
it conducts regex searches for density information (minimum lot size and/or maximum density) in terms of (1) acres, 
(2) square feet, or (3) units per acre, accounting for stopwords that prevent false-positive matches. 

'''

def densityinfo(input1, input2):

    acre_shell = []
    unit_shell = []
    sqft_shell = []
    dinfo_acre = []
    dinfo_unit = []
    dinfo_sqft = []

    badstrings = []
    mfh_badstrings =[]
    acre_badstrings = []
    sqft_badstrings = []
    unit_badstrings = []

    acre_rm = r"""(?x)(?:(\b(\snone|contiguous|subdivision|certain\sconditional\suses|minimum\sdistrict\sarea|tract|district\ssize|may\sbe\sless\sthan|largest|in\sexcess|per\sstructure|(?<!unit)\sper\sacre|golf|
                      gross\ssite\ssize|vacant|unit\/acre|shrod|\mixed\-use\sdistrict|f-prd|project\ssize|increases|minimum\ssite\ssize|planned\sresidential\sdistrict|ncmu\sdistrict|minimum\sparcel\ssize|the\slot\sfor\sthe\spark|parcels\sin\sland\suse\sdistricts\swhich\srequire\s\d+\.*\d*\sacre| 
                      cluster\sdevelopments|garage|accessory\sstructure|f\-p|(?<!building)\ssite\sarea|commissioners|except\swhere\:|special\sexception|minimum\ssite\sof\s\d+\sacre|up\sto\s\d+\sacre|nonresidential\suse|nonresidential\suses|minimum\sgross\ssite\sarea|
                      minimum\slot\ssize\sof\sless\sthan|all\sother\suses|over\s\d+\sacre|maximum\slot\sarea\sof\s\d+\sacre|average\slot\ssize\sof|minimum\sland\sarea\sof|minimum\ssize\sof\san\sr-\d+\.*\d*\sclassification\sdevelopment\sshall\sbe|district\sshall\sencompass\sa\sminimum\sarea\sof\s\d+\sgross\sacre|
                      (?<!not|no\szoning\slot|shall\snot\sbe)\sless\sthan\s\d+\.*\d*\sacre|(?<!not|no\slot\sshall\sbe\screated\swhich\scontains|total\sarea\sof\seach\slot\snot)\sless\sthan\s1\sacre|mf|maximum\sdistrict\sarea|having\sa\stotal\slot\sarea\sof\sat\sleast\s\d+|uous\sarea|acre\sor\sless|the\sstructure\sshall\sbe\splaced|minimum\sdevelopment\sarea|
                      maximum\ssize|aximum\ssize|average\sminimum\slot\ssize|average\sminimum\slot\sarea|greater\sthan\s\d+\sacre|may\sbe\sacceptable|development\sof\sa\sparcel|minimum\sof\s\d+\sunit|comprehensive\splan|multi\sfamily|private\sclubs|development\ssites\sshall\scontain\snot\sless\sthan\s\d+\sacre|
                      provide\sit\sis\son\sa\slot\sof\sa\sminimum\sof\s\d+\sacre|subject\ssite|permit\srequested|planned\sbuilding\sgroup\sprojects|open\sspace\szoning\sdistrict|proposed\samendment|subdivisions|qr\szone|multiple\sfamily|unless\sthe\slot\sis\sa\sminimum|\d+\sacre\sof\sroadside\sagricultural\sland|
                      site\scontaining\snot\sless\sthan\s\d+\sacre|water\sprotection\szone|all\sother\sprincipal\suses|overall\sdevelopment\smust\sbe|extraterritorial\sjurisdiction|district\sshall\sbe\sa\sminimum\sof|hud\-home\sminimum\ssite|residential\scare\sfacility|
                      allowed\sonly\sin\sdevelopments\shaving\sa\sminimum\slot\ssize\sof\s\d+\sacre|acre\sexcept\sthat|average\slot\ssize\sis\sreduced\sfrom|central\sservice\sbuildings|deteriorating\sarea|not\sless\sthan\s\d+\sacre\sexcept\s\d+\spercent\sof\sthe\stotal\sarea|
                      area\sof\sthe\sdistrict\smay\sbe|open\sland\sshall\sbe\sa\sminimum\sof|having\sa\slot\sarea\sof\s\d+\sacre\sor\sgreater|proposed\scontains\snot\sless\sthan\s\d+\sacre|contiguously\sowned\sproperty|an\sadditional\s\d+\.*\d*\sacre|\d+\sacre\swhere\sminimum\slot\ssize|
                      district\sshall\sinclude\snot\sless\sthan\s\d+\sacre|minimum\sland\sarea(?!\sper\sdwelling)|mh\sdistrict|sites\sshall\shave\sa\sminimum\sarea\sof|two\-family|non\-residential|subdivide|single\sownership\sor\scontrol|mu\sdistrict|manufactured\shome\sdevelopments|prd|
                      engineered\splan|building\sfootprint\sis|lot\swhich\sare\sa\sminimum\sof|minimum\sof\s\d+\sacre\sof\sopen|having\sa\sminimum\sof\s\d+\sacre|comprehensive\stransportation\splan|for\sareas\sbetween\s\d+\sand\s\d+\sacre|for\sareas\sbetween\s\d+\.*\d*\sand\s\d+\sacre|
                      not\smore\sthan\s\d+\.*\d*\sacre|minimum\stotal\slot\sarea\sshall\sbe\sapproximately|\d+\sacre\sof\swater|horticulture|projects\sshall\shave\sa\sminimum\sof\s\d+\.*\d*\s\d*\.*\d*\s*acre|cluster|subdividing|parcels\sof\snot\sless\sthan\s\d+\sacre|p\-1|mhp|lot\sarea\sexceeds|
                      attached\sdwelling\sunit|ccr\szone|for\suses\sprescribed\sas\sexceptions|calculation|group\sdevelopment|specific\splan|dormitories|usable\sopen\sspace\sfor\seach\sdwelling|basement|retail\sestablishments|minimum\sopen\sspace\sper\sdwelling\sunit|public\sutility\szones|school|health\sand\ssenior\sservices|
                      lot\sserved\sby\ssuch\seasement|adjoining\sgross\sacre|conveyance|such\sfacilities\sshall|trailer|rvp|dormitory\sbed|planned\sresidential\sdevelopment|of\saccessory\sstructures\sparcel|manufactured\shome\spark|home\spark|minimum\spark\ssize|x|(?<!except\s)commercial|retail|public\spark|
                      zoned\sas\sbusiness\sdistrict\sc|attaching\sof\ssingle\sfamily\sdwelling\sunit|common\sopen\sspace|minimum\sdwellings\sper\snet\sacre|ership|apartment|shall\snot\sbe\srequire\sto\sexceed|install\sa\sminimum|facilities|park\sproposal|independent\sliving\sfacility|schools|restaurants|
                      chickens|minimum\sarea\sof\sany\slot\sfor\stownhome\sdevelopment|fowl|minimum\ssize\sof\seach\sneighborhood\sproper|open\sspace\srequire|not\sexceed|lot\ssize\sfor\sa\sconvalescent\shome\sshall|useable\sopen\sspace\sper\sdwelling\sunit|beehive|group\shome|group\shomes|landscaped\sislands|campsite|
                      lot\sarea\smust\snot\sbe\sgreater\sthan|warehouse|warehouses|tents|vendor\sspace|nonresidential\sdistricts|shelters\sfor\sthe\shomeless|allowed\swith\sapprove\sof\sa\sconditiona|atm\sdrive\-use|project\sarea\sfor\sa\sspecific\splan|minimum\sproject\sarea|pc\-i\ssite|under\s\d+\sacre\sin\ssize|under\s\d+\sacre\sin\ssize|
                      conditional\suse\sshall\sbe|condominium\sprojects|constructioned|easement\sof\snot\sless\sthan|fraternities|sororities|\d+\sacre\sfor\stownh|\d+\sacre\sfor\stownh|by\s\d+\sunit\sper\sacre|already\sequals\sor\sexceeds\sthe\sminimum|facility\ssite\sdevelopment\sstandards|industrially\szoned\sarea|floor\sarea|
                      surveyor\sand\ssite\splan\sare\srequire|pud\smust\sbe\snot\sless\sthan\s\d+\sacre|grant\sof\svariance\sgenerally\sis\slimit|polyethylene|randd\suses|lanned\sdevelopment|withmmercial|nonresidential\sspecial\suses\sthe\slot\ssize\sshall\sbe|boardinghouses|cumulatively\stotaling\snot\sover|dispensary|
                      multiple\sresidential\shousing|junkyards|except\swhere\sthe\slot\ssize\sexceeds\s\d+\sacre|except\swhere\sthe\slot\ssize\sexceeds\s\d+\sacre|runway|wetland\smitigation|quarries|students|srn\sdesignation|average\slot\ssize\son\sblock|usable\slot\sarea\sshall\sbe\sdetermined\sby\sdeducting\sfrom|
                      technology\spark|taverns|bars|hfdd\sshared\sresidence|for\s\d+\.*\d*\sacre|fuel\sstations|public\sland\sdistrict|automotive\suses|permitted\sas\san\saccessory\suse\son\slot\swith\sa\sminimum\slot\sarea\sof\s\d+\sacre|located\son\slot\swith\sa\slot\sarea\sof\s\d+\sacre\sor\smore|
                      \d+\sacre\sis\srequire\sfor\sa\splanned\-development|proposed\spark\sshall\sbe\sa\sminimum\sof|\d+\sacre\sfor\seach\spark|home\scommunities|manufactured\shome\sshall\shave\sa\sminimum\sof|for\sthe\spurpose\sof\sselling\ssaid\slot|minimum\ssite\sshall\sbe|provide\san\seasement|
                      area\soccupied\sby\sexisting\slakes\sor\sponds\sthat\sare\sgreater\sthan\s\d+\sacre\sin\ssize|lot\sarea\sfor\smanufactured\sdwelling\sparks|towing\stongue|social\sservices|park\ssize|planter\sbays\sor\sislands|multiplefamily\sdwelling\sdevelopment|swimming\spool|ventilating\sshafts|
                      apply\sto\san\sarea\snot\sless\sthan\s\d+\sacre|manufactured\shome\sper\seach\s\d+\.*\d*\sacre|minimum\sfinished\sfloor\selevation|in\swhich\sthe\sminimum\slot\ssize\sis\s\d+\sacre\sor\smore|park\slot\sor\sparcel\sshall\sbe\snot\sless\sthan|park\sshall\scontain\snot\sless\sthan|
                      lot\shaving\sa\slot\sarea\sof\s\d+\sacre\sor\smore|average\snet\slot\sarea\sshall\sbe|acre\sshall\sbe\srequire\swhenever\sproperty|for\sup\sto\sthe\s\d+\sacre|on\ssites\scontaining\sa\sgross\sarea\sof|equal\sto\sor\sgreater\sthan\s\d+\sunit\sper\s\d+\sacre|isds\sis\sto\sbe\sconstructed|
                      property\scontaining\sa\sminimum\sof|operated\son\sa\slot\scontaining\sa\sminimum\sof|well\sis\sto\sbe\sconstructed\sis\snot\sless\sthan\s\d+\sacre\sin\ssize|strict\sshall\shave\sa\sminimum\ssize\sof|manufactured\shousing\sdevelopment|lot\sarea\sbetween\s\d+\ssquare\sfeet\sand\s\d+\sacre|
                      home\ss\spark|strict\sshall\shave\sa\sminimum\ssize\sof|manufactured\shousing\sdevelopment|lot\sarea\sbetween\s\d+\ssquare\sfeet\sand\s\d+\sacre|on\slot\shaving\sa\slot\sarea\sof\s\d+\sacre|more\sthan\s\d+\ssquare\sfeet\sbut\sless\sthan\s\d+\sacre|on\ssites\snot\sless\sthan\s\d+\sacre|
                      on\sparcels\swith\sa\sminimum\slot\sarea\sof\s\d+\sacre|professional|high\-rise\sresidential\sdevelopment|group\scare\shome|having\sa\sgross\slot\sarea\sgreater\sthan\s\d+\.*\d*\sacre|heliport|atm\sdrive|interior\saccessory|minimum\sarea\sof\sthe\szone\sdistrict\sshall\sinclude\sacreage|
                      upon\swhich\sthe\swell\sis\sto\sbe\sconstructed\sis\snot\sless\sthan\s\d+\sacre\sin\ssize|upon\swhich\sthe\sisds\sis\sto\sbe\sconstructed\sis\snot\sless\sthan\s\d+\sacre\sin\ssize|or\sof\sa\slot\ssize\slarger\sthan\s\d+\sacre|an\soverlay\sdistrict\smust\shave\san\sarea\sof\snot\sless\sthan\s\d+\sacre|
                      the\sdistrict\sshall\scontain\san\sarea\sof\s\d+\sacre\sor\smore|minimum\slot\ssize\sfor\sany\scrd\-h\sdevelopment\sshall\sbe|that\shave\san\soverall\sdensity\sless\sthan\s\d+\sdwelling\sunit\sper\sacre|senior\shousing\slot\sarea|any\slot\sfor\stownhome\sdevelopment|l\-i|mobile\-home\sparks\sshall|
                      the\sland\sis\sa\ssingle\sparcel\sof\sland\sof\snot\sless\sthan\s\d+\sacre|park\sshall\scontain\sa\sminimum\sof\s\d+\sacre|kope\sgeologic\sformations|on\-site\spark\sarea\sof\snot\sless\sthan\s\d+\.*\d*\sacre|for\stracts\shaving\sa\sminimum\sof\s\d+\sacre|ac\s*$|manufactured\shome\sparks|parcel\ssize\s\<|
                      the\sminimum\sarea\sfor\sa\scottage\shousing\sproject|home\soccupation|density\sbonus\sof\s\d+|permitted\sdensity\sbe\sless\sthan\s\d+\.*\d*\sdwelling\sunit\sper\sgross\sacre|deteriorating\sarea\sin\sthe\saggregate\sof\snot\sless\sthan\s\d+\sacre|mixed\-income\shousing|manufactured\shome\scommunities|
                      require\sfor\sa\smobilehome\spark\sshall\sbe|mobile\shome\sparks|mobile\shome\spark|division\sof\sland\sinto\sparcels\sof\smore\sthan|developments\son\sa\sminimum\sof\s\d+\sacre|new\sdevelopment\sthe\sproposed\ssite\smust\sbe\sa\sminimum\sof|residential\szoning\sdistrict\sit\smust\sbe\sa\sminimum\ssize\sof\s\d+\sacre|
                      mhe\sthe\sminimum\slot\ssize\sshall\sbe\s\d+\sacre|shall\snot\sapply\sfor\slot\s\d+\sacre\sor\sgreater|average\snet\slot\sarea\sshall\sbe\s\d+\sacre|hub\sactivity|area\scenter|hic\d\szone\szoning\sdistrict\sshall\scontain\sa\sminimum\sof|except\sfor\sa\splanned\sunit\sdevelopment|planned\sunit\sdevelopment\sthat\sshall\shave\smore\sthan|
                      right\-of\-way\swhich\sis\snot\sless\sthan\s\d+\sacre\sin\sarea|if\sthe\sproposed\ssite\sis\smore\sthan\s\d+\sacre\sin\ssize|minimum\ssize\sof\sa\schpd\sis\s\d+\sacre|if\sthe\sarea\scontains\snot\sless\sthan\s\d+\sacre|planned\sproject|embrace\san\sarea\sof\snot\sless\sthan\s\d+\sacre|large\swind|open\sspace\sper\sbed\sshall\sbe\sa\sminimum\sof|
                      planned\sunit\sdevelopment\scontains\sa\sminimum\sof|fenced\son\sa\sparcel\sof\sland\snot\sless\sthan|government\slot|on\sparcels\sof\sland\s\d+\sacre\sor\smore\sin\ssize|minimum\sdistrict\s\d+\s\d+\sarea|not\sless\sthan\s20\slot|\d+\sacre\sfor\sthe\s\d+\sanimal|lot\ssize\saveraging\sprincipal\sbuilding|photography|
                      special\suses\sthe\slot\ssize\sshall\sbe\snot\sless\sthan\s\d+\sacre)\b|private\swell:|an\sarea\sis\sdivided\sinto\sresidential\sa\slot\sarea\sof\s\d+\sacre\sor\sgreater|shall\sexceed\sby\sat\sleast\s\d+\sacre|parcels\sof\s\d+\sacre\sor\smore\sshall\sbe|\d+\sacre\sa\squarter\-quarter|or\sa\sgovernment\slot\scontaining|
                      lot\ssize\sthroughout\sthe\sdevelopment\sshall\sbe|divided\sby\sthe\sminimum\sconventional\slot\ssize||
                      \sminimum\sof\s\d+\sunit|b\-\d*|\bhdr\-|mixed\-use\sdistrict|mixed\suse\sdistrict|minimum\soverall\sarea\:|maximum\slot\ssize\:|minimum\sdevelopment\ssite\sarea\:|maximum\:|except\swhere\:|project\:|rom\sa\sminimum\slot\ssize|schools\sand\stheir\scustomary\srelated\suses\sprovide\:|redevelopment\:|net\sarea\:|landowner\sshall\sbe\sdefined\sas|
                      gement\sfacility\sshall\sapply|\$|x\s*\d+|co\/mr\szone|note\s*\d*\:|detached\sgarages\:|minimum\slot\sarea\sin\sf\-w\sfloodway\sconservation\szone\:|\.{10,}|(?<!access\sway\sat\sleast\s)\d\.*\s*$|conditional\suse\scriteria\:|townhouse\sdwelling\:|agricultural\-type\sfencing\slocated\sin|minimum\slot\sarea\sconditional\s*\:|facility\:|laughterhouse\:|
                      minimum\ssite\:\s\d+\sacre|mxd\-mixed\suse\sdevelopment\sdistrict|home\sparks|mobilehome\spark\sarea\:|ratio\s\<\s*\d+\sacre|ratio\s\>\s*\d+\sacre|land\suse\sdistricts\swhich\srequire\s\d+\.*\d*\sacre\sminimum|a\slot\sarea\srequire\sthat\sis\s\d+\sacre\sor\sgreater|be\sdeemed\sto\sdivide\sacreages|average\slot\ssi|mf\slot\srequire\:|mf\-ah\-\d\slot\srequire\:))"""
    sqft_rm = r"""(?x)(?:\b(contiguous|certain\sconditional\suses|minimum\sdistrict\sarea|minimum\slot\scoverage|vacant|district\ssize|may\sbe\sless\sthan|planned\sresidential\sdistrict|ground\sfloor\sarea\sper\sdwelling|
                      cluster\sdevelopments|gross\ssite\ssize|gfa|garage|recreational|accessory\sstructure|f\-p|ncmu\sdistrict|commissioners|except\swhere\:|special\sexception|minimum\ssite\sof\s\d+\sacre|up\sto\s\d+\sacre|average\slot\ssize|
                      minimum\slot\ssize\sof\sless\sthan|nonresidential\suses|minimum\sgross|all\sother\suses|over\s\d+\sacre|maximum\slot\sarea\sof\s\d+\sacre|average\slot\ssize\sof|minimum\sparcel\ssize|minimum\sland\sarea\sof|\d+\ssquare\sfoot\sbuilding|
                      minimum\ssize\sof\san\sr-\d+\.*\d*\sclassification\sdevelopment\sshall\sbe|having\sa\stotal\slot\sarea\sof\sat\sleast\s\d+|uous\sarea|the\sstructure\sshall\sbe\splaced|minimum\sdevelopment\sarea|square\sfeet\sof\sbldg\.\sfloor\sspace|
                      same\sas\sr\-\d+\sfeet|\d+\sfeet\s\d+\ssquare\sfeet\sminimum\.|facility\szone\sdevelopment\sstandard|total\sdevelopment\ssite\sarea|drive\-shall|average\slot\ssize\sis\sreduced\sfrom|on\slot\shaving\s\d+\ssquare\sfeet\sor\smore|
                      \d+\ssquare\sfeet\sof\shabitable\sliving\sarea|sleeping\sroom\sshall\sbe\s\d+\s*\d*\ssquare\sfeet|shall\sbe\sset\saside\sas|\d+\ssquare\sfeet\sof\slot\sarea\sabove\sthe\sminimum|minimum\ssquare\sfootage\sper\sdwelling\sunit|
                      (?<!not|shall\snot\sbe|nor\sshall\sthe\sland\sarea\sprovide\sfor\seach\sdwelling\sunit\son\sthe\slot\sbe|no\szoning\slot|no\slot\sshall\sbe\screated\swhich\scontains|total\sarea\sof\seach\slot\snot|shall\snot\sbe|shall\snot\sbe\sreduced\sto)\sless\sthan\s\d+\ssquare\sfeet|maximum\sdistrict\sarea|
                      average\sminimum\slot\ssize|average\sminimum\slot\sarea|greater\sthan\s\d+\square\sfeet|may\sbe\sacceptable|development\sof\sa\sparcel|minimum\sof\s\d+\sunit|comprehensive\splan|private\sclubsprovide\sit\sis\son\sa\slot\sof\sa\sminimum\sof\s\d+\sacre|
                      subject\ssite|permit\srequested|planned\sbuilding\sgroup\sprojects|open\sspace\szoning\sdistrict|proposed\samendment|subdivisions|qr\szone|unless\sthe\slot\sis\sa\sminimum|district\sshall\sinclude\snot\sless\sthan\s\d+\sacre|minimum\sland\sarea(?!\sper\sdwelling)|mh\sdistrict|
                      sites\sshall\shave\sa\sminimum\sarea\sof|non\-residential|subdivide|single\sownership\sor\scontrol|mu\sdistrict|manufactured\shome\sdevelopments|prd|engineered\splan|building\sfootprint\sis|lot\swhich\are\sa\sminimum\sof|minimum\sof\s\d+\ssquare\sfeet\sof\sopen|
                      having\sa\sminimum\sof\s\d+\sacre|comprehensive\stransportation\splan|for\sareas\sbetween\s\d+\sand\s\d+\ssquare\sfeet|not\smore\sthan\s\d+\.*\d*\ssquare\sfeet|minimum\stotal\slot\sarea\sshall\sbe\sapproximately|\d+\ssquare\sfeet\sof\swater|horticulture|
                      projects\sshall\shave\sa\sminimum\sof\s\d+\.*\d*\ssquare\sfeet|cluster|subdividing|parcels\sof\snot\sless\sthan\s\d+\ssquare\sfeet|p\-1|mhp|lot\sarea\sexceeds|attached\sdwelling\sunit|ccr\szone|for\suses\sprescribed\sas\sexceptions|calculation|group\sdevelopment|
                      specific\splan|dormitories|usable\sopen\sspace\sfor\seach\sdwelling|basement|retail\sestablishments|minimum\sopen\sspace\sper\sdwelling\sunit|lot\sserved\sby\ssuch\seasement|restaurants|public\sutility\szones|school|$or\sarea\sof|minimum\spatio\sarea|
                      surfaces\sare\sno\smore\sthan\s\d+\spercent\sof\slot\sarea|accessory\sstructures\sfrom\s\d+\ssquare\sfeet\sto\s\d+\ssquare\sfeet|between\s\d+\sof\sthe\s\d+\ssquare\sfoot\snumbers\sover|each\s\d+\ssquare\sfeet\sof\sincreased\slot\sarea|utility\sinstallations|
                      provide\sfor\seach\s\d+\ssquare\sfeet|unit\sshall\sbe\sa\sminimum\sof\s\d+\ssquare\sfeet|all\sother\sprincipal\suses|outdoor\sliving\sspace|living\sarea\sof\snot\sless\sthan|multiplied\sby|parkland\sdedication|g\/i\slot\ssize\srequire|\d+\ssf\sduplex|
                      conveyance|such\sfacilities\sshall|square\sfeet\sfloor\sspace|trailer|ground\sfloor|rvp|dormitory\sbed|usable\sopen\sspace|open\sair\sbusiness|manufactured\shome\spark|home\spark|minimum\sdwelling\sunit\ssizes|commercial|retail|minimum\sfloor\sspace\sof\s\d+\ssquare\sfeet|
                      finished\sliving\sarea|minimum\sliving\sarea|private\sdriveway|planned\sresidential\sdevelopment|of\saccessory\sstructures|accessory\sstructures\s\d+\ssquare\sfeet|accessory\sstructures\sgreater\sthan|facilities|park\sproposal|x|
                      minimum\sof\s\d+\ssf\sfor\sa\sfour\-family\sdwelling|minimum\sof\s\d+\ssf\sfor\sa\stwo\-family\sdwelling|minimum\sof\s\d+\ssf\sfor\sa\sthree\-family\sdwelling|for\seach\s\d+\ssquare\sfeet\sof\sarea\savailable|minimum\stract\ssize\sshall\sbe\s\d+\ssquare\sfeet|
                      zoned\sas\sbusiness\sdistrict\sc|attaching\sof\ssingle\sfamily\sdwelling\sunit|common\sopen\sspace|minimum\sdwellings\sper\snet\sacre|ership|shall\snot\sbe\srequire\sto\sexceed|install\sa\sminimum|a\sminimum\sof\s\d+\ssquare\sfeet\smust\sbe\slocated\son\sthe\s1\sfloor|
                      independent\sliving\sfacility|chickens|minimum\sarea\sof\sany\slot\sfor\stownhome\sdevelopment|enclosed\shabitable\sindoor\sheated|fowl|minimum\ssize\sof\seach\sneighborhood\sproper|of\sliving|open\sspace\srequire|minimum\sdwelling\sunit\ssize|not\sexceed|1\sbedroom\sper\s\d+\ssquare\sfeet|
                      total\sfloor\sarea\sratio|organic\smaterial\sper\s\d+\s*\d*\ssquare\sfeet|lot\ssize\sfor\sa\sconvalescent\shome\sshall|useable\sopen\sspace\sper\sdwelling\sunit|for\seach\sstudent|beehive|with\sa\sminimum\sbuilding\sfootprint\sof|building\sfootprint\sfor|parking\sspace\sfor\severy|
                      unit\ssize\sminimum|minimum\sprincipal\sliving\sspace|open\sspace\ssquare\sfeet\sper\sdwelling\sunit|bedrooms|bedroom|minimum\sfoundation\sarea\sof|oor\sarea\stotal\sper\sunit|grass\ssite\sarea|for\sbuildable\slot\sarea\sof|\d+\ssquare\sfeet\son\smain\sfloor|
                      minimum\saverage\slot\sarea\sper\sapartment|\d+\ssquare\sfeet\sof\sgross\sheated\sand\scooled\sfloor\sarea|home\scommunities|each\sspace\sshall\shave\san\sarea\sof\snot\sless\sthan|manufactured\shome\sshall\shave\sa\sminimum\sof|two\-family\ssquare\sfeet\s\d+|
                      \d+\ssquare\sfeet\son\sthe\smain\sfloor|group\shome|group\shomes|square\sfeet\sof\suseable\sopen\sspace|landscaped\sislands|bags\sper|square\sfeet\sof\sgross\sliving\sarea|civic\sspace|campsite|schools|habitable\slevel\sof\sheated\senclosed\sspace|health\sand\ssenior\sservices|
                      may\sthe\saccessory\sapartment\sbe\sgreater\sthan\s\d+|\d+\ssquare\sfeet\sof\sland\sarea\sshall\sbe\sdesigned\sas\scommon\sspace\sper\sdwelling\sunit|manufactured\shomes\sshall\shave\sa\sminimum\sof\s\d+\s*\d*\ssquare\sfeet|square\sfeet\sof\slot\sarea\sper\spatient|minimum\sunit\ssize\sof\s\d+\ssquare\sfeet|
                      floor\sarea\sper\sunit|\d+\ssquare\sfeet\sper\sdwelling\sunit\sshall\sbe\sdeveloped\sand\sprepared\sfor\sspecific\suses|improvement\sof\sa\slot\scomprised\sof\s\d+\sor\smore\ssquare\sfeet|nonresidential\suse|patio\shome\sshall|enclosed\sentirely\son\sthe\sdwelling\swall|minimum\sdwelling\ssize\s\d+\ssquare\sfeet|
                      parking\sspaces|gallons\sper\sdwelling|lot\sarea\smust\snot\sbe\sgreater\sthan|gross\sfloor\sarea\sof\s\d+\ssquare\sfeet|warehouse|warehouses|townhouses\swith\sa\sminimum\sof|square\sfeet\son\sthe\s1\sfloor|tents|minimum\sdwelling\sunit\sarea\s\d+\ssquare\sfeet|vendor\sspace|
                      square\sfeet\sof\smeeting\sspace|open\sspace\srequire\sfor|square\sfeet\sof\sopen\sspace\sper\sdwelling\sunit|nonresidential\sdistricts|maximum\sfloo|shelters\sfor\sthe\shomeless|square\sfeet\sof\sheated\sspac|square\sfeet\sof\sheated\sspace|water\sconnection\-per\sdwelling\sunit|
                      ssory\sbuilding\sor\suse\sshall\sbe\s\d+\spercent\sof\sthe\slot\ssize|ssory\sbuilding\sor\suse\sshall\sbe\s\d+\%\sof\sthe\slot\ssize|garages\sshall\scontain\sat\sleast|enclosed\sparking\sspaces|rearceed|garages\sof\sa\sreduced|constructionion|minimum\sground\sperimeter|
                      minimum\ssize\sof\smanufactured\shome\sto\sbe\s\d+\ssquare\sfeet|for\seach\spatient|dumpster|square\sfeet\sof\sgross\sfloor\sarea|within\sthe\sstructure|per\sdwelling\sunit\snonresidential\sdevelopment|swimming\spool|gross\sfloor\sarea\sof\sthe\sprincipal\sbuilding|
                      subtract\s\d+\ssquare\sfeet|\d+\ssquare\sfeet\sof\sopen\sspace\/unit|nurseries|allowed\swith\sapprove\sof\sa\sconditiona|atm\sdrive\-use|total\scovered\sfloor\sarea\sin\ssquare\sfeet|1\sfoot\sfor\severy\s\d+\ssquare\sfeet\sof\seffective\slot\sarea|swimming\spool|enclosed\sliving\sarea\sof\sat\sleast|
                      \d+\ssquare\sfeet\sof\shabitable\sarea\sshall|open\sspace\sarea\sprivate\s*\-\s*minimum\s\d+\ssquare\sfeet\/du|project\sarea\sfor\sa\sspecific\splan|minimum\sproject\sarea|pc\-i\ssite|rear\ssetbacks\sup\sto\s\d+\ssquare\sfeet|minimum\sof\s\d+\ssquare\sfeet\sof\susable\syard\sarea|
                      minimum\sunit\ssize\sfor\sall\ssros\sshall\sbe|\d+\ssquare\sfeet\sof\susable\syard\sarea|if\sthe\slot\sor\sparcel\sis\sgreater\sthan\s\d+\ssquare\sfeet|any\slot\sor\sparcel\sthat\sis\sgreater\sthan\s\d+\ssquare\sfeet|conditional\suse\sshall\sbe|square\sfeet\sover\sthe\slivable\sarea\sallowed|
                      by\sless\sthan\s\d+\s*\d*\ssquare\sfeet|condominium\sprojects|constructioned|easement\sof\snot\sless\sthan|minimum\sbuilding\ssize\s\d+\ssquare\sfeet|fraternities|sororities|maximum\slot\ssize\ssquare\sfeet|already\sequals\sor\sexceeds\sthe\sminimum|facility\ssite\sdevelopment\sstandards|
                      industrially\szoned\sarea|surveyor\sand\ssite\splan\sare\srequire|minimum\sresidential\sunit\ssize\sshall\sbe\s\d+\ssquare\sfeet|minimum\senclosed\sfloor\sspace\sof\snot\sless\sthan\s\d+\ssquare\sfeet|grant\sof\svariance\sgenerally\sis\slimit|polyethylene|randd\suses|lanned\sdevelopment|
                      withmmercial|nonresidential\sspecial\suses\sthe\slot\ssize\sshall\sbe|sleeping|minimum\sfloor\sspace\sarea\sof\s\d+\ssquare\sfeet|boardinghouses|minimum\sfloor\sspace\sarea\sof\s\d+\s*\d*\ssquare\sfeet|\d+\ssquare\sfeet\sof\spublic\sopen\sspace\sis\srequire|cumulatively\stotaling\snot\sover|
                      minimum\shabitable\sspace\sof\s\d+\ssquare\sfeet|junkyards|drive\-though\sfacility|except\swhere\sthe\slot\ssize\sexceeds\s\d+\ssquare\sfeet|runway|wetland\smitigation|quarries|\d+\ssquare\sfeet\slarger\sthan\sthe\sminimum\sallowed|square\sfeet\sopen\sspace\sper\sdwelling\sunit|students|
                      average\slot\ssize\son\sblock|usable\slot\sarea\sshall\sbe\sdetermined\sby\sdeducting\sfrom|technology\spark|taverns|bars|hfdd\sshared\sresidence|private\sfire\shydrants|fuel\sstations|public\sland\sdistrict|automotive\suses|if\sthe\sarea\sof\ssuch\sland\sexceeds\s\d+\ssquare\sfeet\sper\sdwelling\sunit|
                      building\sshall\scontain\sa\sminimum\sof\s\d+\ssquare\sfeet|area\soccupied\sby\sexisting\slakes\sor\sponds\sthat\sare\sgreater\sthan\s\d+\ssquare\sfeet\sin\ssize|\d+\ssquare\sfeet\smore\sthan\sis\srequire|towing\stongue|social\sservices|park\ssize|professional|\d+\stown\smeeting|
                      dividing\sthe\slot\sarea\sin\ssquare\sfeet\sby\s\d+\sand\smultiplying\sthat\sfigure\sby\sthe\sminimum\sor\smaximum|planter\sbays\sor\sislands|\d+\ssquare\sfeet\sof\simpervious\scover|ventilating\sshafts|open\sspace\sshall\sbe\sa\sminimum\sof\s\d+\ssquare\sfeet|hardscaped\splaza|n\sparcels\swith\sa\sminimum\slot\sarea\sof\s\d+\ssquare\sfeet|
                      \d+\ssquare\sfeet\sper\sbed|the\sminimum\ssize\sof\sthe\sadu\sshall\sbe\s\d+\ssquare\sfeet|minimum\ssize\sof\san\saccessory\sdwelling\sshall\sbe\s\d+\ssquare\sfeet|group\scare\shome|\d+\ssquare\sfeet\sof\slivable\sfloor\sspace|square\sfeet\sof\slivab|common\sopen\/recreations\sspace|
                      building\sfootprint\sthat\sexceeds\s\d+\ssquare\sfeet|general\sbusiness\sdistrict|for\seach\scow|plus\s\d+\ssquare\sfeet\sincorporate\sinto\sadditional|having\sa\sgross\slot\sarea\sgreater\sthan\s\d+\ssquare\sfeet|\d+\ssquare\sfeet\sof\slot\sarea\snet\sacreage\scould\sbe\ssubdivided\sinto|loor\sarea\sof\sa\sdwelling\sshall\sbe\s\d+\ssquare\sfeet|
                      heliport|\d+\ssquare\sfeet\sof\syard\sarea|atm\sdrive|constructed\sbefore\s\d+\ssquare\sfeet|square\sfootage\sbasis\swith\san\sacre\sequaling\s\d+\s*\d*\ssquare\sfeet|\d+\ssquare\sfeet\sof\slivable\senclosed\sfloor\sspace|accessory\sdwelling\sunit\sshall\sbe\sa\sminimum\sof\s\d+\s*\d*\ssquare\sfeet|
                      or\sof\sa\slot\ssize\slarger\sthan\s\d+\ssquare\sfeet|maximum\stotal\saccessory\sbuildings\ssf\s\d+|park\sshall\scontain\sa\sminimum\sof\s\d+\ssquare\sfeet|kope\sgeologic\sformations|minimum\sof\s\d+\ssquare\sfeet\slivable\sflo|for\stracts\shaving\sa\sminimum\sof\s\d+\ssquare\sfeet|
                      provide\sat\sleast\s\d+\ssquare\sfeet\sof\susable\sspace\sper\sdwelling\sunit|floor\sarcture|involving\sa\slot\swith\sfewer\sthan\s\d+\ssquare\sfeet\sof\slot\sarea|minimum\slot\sarea\sis\s\d+\ssquare\sfeet\sif\sthe\slot\sarea\swas\sreduced\sbelow\s\d+\ssquare\sfeet|lot\sarea\swas\sreduced\sbelow\s\d+\ssquare\sfeet|
                      located\son\sa\slot\shaving\sa\sminimum\slot\sarea\sof\s\d+\ssquare\sfeet|lot\sarea\swas\sreduced\sbelow\s\d+\ssquare\sfeet|above\s\d+\sfeet\sin\sheight\sis\s\d+\ssquare\sfeet|\d+\ssquare\sfeet\swhichever\sis\sgreater\sis\sin\sopen\sspace\suse|minimum\sarea\sof\s\d+\ssquare\sfeet\sof\sopen\sspace|
                      defined\sas\sa\ssingle\stenant\sthat\soccupies\sa\sminimum\sof\s\d+\ssquare\sfeet|developments\sexceeding\s\d+\ssquare\sfeet\sof\snonresidential\sdevelopmentif\sthe\sarea\scontains\snot\sless\sthan\s\d+\ssquare\sfeet|minimum\samount\sof\s\d+\s*\d*\ssquare\sfeet\sof\sopen\sspace|building\sor\sbuilding\saddition\swhich\scovers\smore\sthan\s\d+\s*\d*\ssquare\sfeet|
                      nonresidential\sbuilding\sshall\snot\sbe\sless\sthan\s\d+\s*\d*\ssquare\sfeet|lot\sarea\srequire\sfor\sa\sresidential\sccrc|\d+\ssquare\sfeet\sto\sless\sthan\s\d+\ssquare\sfeet|in\sexcess\sof\s\d+\ssquare\sfeet|\d+\ssquare\syards\sof\sstreet\ssurface|buir\sarea|area\scenter|
                      buildings\swith\sa\stotal\sgross\ssquare\sfootage\sof|accessory\sbuilding\slarger\sthan|plus\s\d+\s\d+\ssquare\sfeet|areag\slarger\sthan)\b|lot\sarea\sup\sto\s\d+\ssquare\sfeet\:\s\d+\ssquare\sfeet\smaximum|consist\sof\sat\sleast\s\d+\ssquare\sfeet\sof\sfloor\sspace|
                      mixed\-use\sdistrict|mixed\suse\sdistrict|minimum\ssite\ssize|minimum\soverall\sarea\:|maximum\slot\ssize\:|minimum\sdevelopment\ssite\sarea\:|rom\sa\sminimum\slot\ssize|minimum\sfloor\sarea\sper\sdwelling\sunit\:|minimum\stotal\sliving\sspace\sper\sdwelling\sunit\:\s\d+\ssquare\sfeet|
                      maximum\:|except\swhere\:|dividing\sthe\stotal\slot\sarea\:|project\:|minimum\spark\ssize|gement\sfacility\sshall\sapply|\$|living\sarea\sper\sunit\:|living\sarea\:|bedroom\:|\-bedroom|minimum\sresidential\sdwelling\sunit\ssize\:|floor\sspace\:|minimum\ssize\sof\sdeveloped\sopen\sspace\:|
                      unit\sshall\scontain\sat\sleast\s\d+\ssquare\sfeet\sper\sdwelling\sunit\.|unit\sshall\scontain\sat\sleast\s\d+\ssquare\sfeet\sper\sfamily\sunit\.|\d+\spercent\sof\sthe\slot\ssize\sup\sto|patio\sarea\ssquare\sfeet|minimum\snet\sparcel\sarea\sof|as\sbeing\srequested\sthe\sarea\smust\scontain\sat\sleast|mobile\shome\sparks|mobile\shome\spark|
                      minimum\susable\soutdoor\sopen\sspace\:|minimum\sunit\ssize\:|\bx\s*\d+|co\/mr\szone|note\s*\d*\:|detached\sgarages\:|\d+\.*\d*\sacre\.\sbuilding\sarea\:\sminimum\s\d+\ssquare\sfeet|\.{10,}|minimum\stotal\sliving\sarea\sper\sdwelling\sunit\:|conditional\suse\scriteria\:|minimum\sfloor\sarea\:|
                      \d+\ssquare\sfeet\sof\smulti\sfamily\sland\sarea|\d+\spercent\sor\smore\sof\sthe\slot\sarea\sor\son\s\d+\ssquare\sfeet\sor\smore|contained\sa\slot\sarea\sof\s\d+\ssquare\sfeet|
                      lot\ssize\srequire\sdeveloped\sopen\sspace\/lot\ssquare\sfeet|for\sa\s\d+\sacre\ssubdivision\sin\sthe\sr\d+\szone\sthe\ssame\s\d+\ssquare\sfeet\sof\slot\sarea|for\severy\s\d+\ssquare\sfeet\sof\slot\sarea\srequire|boarding\shome\sowner\'s\sliving\sarea|maximum\slot\scoverage\son\slot\s\d+\ssquare\sfeet\sin\ssize\sor\sgreater\:|
                      minimum\srequire\s*\-\s*nonresidential|open\sspace\.|minimum\slot\sarea\sconditional\s*\:|require\srear\syard\:|area\sshall\sbe\sincreased\sby|\d+\s\-\sand\sover\ssquare\sfeet|mf\slot\srequire\:|mf\-ah\-\d\slot\srequire\:|refer\sto\s\-\s\d+\-)"""
    unit_rm = r"""(?x)(?:\b(certain\sconditional\suses|vacant|garage|may\sbe\sless\sthan|well|recreational|the\sstructure\sshall\sbe\splaced|nonresidential\sdistricts|guest\sunit|beds\sper\sacre|fuel\sstations|atm\sdrive|kope\sgeologic\sformations|
                            density\sof\s\d+\sbeds\sper|reverse\sosmosis|polyethylene|randd\suses|boardinghouses|perennial\svegetative\scover|aximum\sdensity|\d+aximum\sdensity|quarries|students|towing\stongue|
                            multi\sfamily\sdwelling\swith\s\d+\sor\sfewer\sdwelling\sunit|per\sdwelling\sunit\s\d+\s\d+\s\d+|\d+\sdwelling\sdetached|\d+\sdwelling\ssingle\sfamily|\d+\sdwelling\stwo\-family|\d+\sdwelling\sunit\.|
                            allowed\swith\sapprove\sof\sa\sconditiona|conditional\sdensities|conditional\sdensity|atm\sdrive\-use|fraternities|sororities|withmmercial|wetland\smitigation|planter\sbays\sor\sislands
                            cumulatively\stotaling\snot\sover|junkyards|technology\spark|taverns|bars|hfdd\sshared\sresidence|heliport|lodging)\b|mixed\-use\sdistrict|mixed\suse\sdistrict|for\spurposes\sof\scalculating|\d+\stownhouse\sdwelling\sunit\.|
                            types\sof\sdevelopment\sthat\scontains\smore\sthan\s\d+\sdwelling\sunit\:|projects\shaving\smore\sthan\s\d+\s\d+\sdwelling\sunit|\$\d+\sper\sdwelling|minimum\slot\swidth\sfeet\s\d+\s*\d*\s*\d*|\d+\spatio\shouse\sdwelling\sunit\.|
                            \sx\s*\d+|\d+\%\sof\sthe\stotal\sunit|\d+\spercent\sof\sthe\stotal\sunit|\.{10,}|maximum\sdensity\:\s\d+\s*\d*\sacre|conditional\suse\scriteria\:|or\sthere\sare\s\d+\sor\smore\sdwelling\sunit|block\s\d+)"""

    inlist = [input1, input2]
    inlist1 = []
    inlist2 = []
    inlist3 = []

    test1 = inlist[0]
    test2 = inlist[1]

    res = sum(x == y for x, y in zip(test1, test2))

    for i in range(2):
        instrings = list(deepflatten(inlist[i], 1))
        for string in instrings:
            newword1 = re.sub('\d*\.*\d*\(\d\)', '', string)
            newword2 = re.sub('[()]', ' ', newword1)
            newword3 = re.sub(r'\b\d{1}\.\s|\b\d{4}\.\d{2}\s|\d+\.\d+\.\d+', '', newword2)
            if re.findall(r'\s\d{1,2}\.\D', newword3, flags=re.IGNORECASE):
                csflags = re.findall(r'\s\d{1,2}\.\D', newword3, flags=re.IGNORECASE)
                for cmatch in csflags:
                    crep = newword3.index(cmatch)
                    newword4 = newword3[:crep] + "" + newword3[crep + 2:]
            else:
                newword4 = newword3
            newword5 = re.sub(r'\d+\-\d+(?!\sdwelling\sunit)', '', newword4)

            check_extract = newword5.split(" ")
            if (len(check_extract[0]) == 1 and check_extract[0] != "a" and not check_extract[0].isdigit()) or check_extract[0].isdigit():
                check_extract[0] = ''
            elif len(check_extract) > 2 and check_extract[len(check_extract)-1].isdigit():
                check_extract[len(check_extract)-1] = ''
            inlist1.append(newword5)

        ## convert fractions ##
        for j in inlist1:
            inlist2.append(fractonum(j))

        ## convert numeric text information ##
        for j in inlist2:
            try:
                inlist3.append(text2int(j))
            except ValueError:
                inlist3.append(j)
            except IndexError:
                inlist3.append(j)

        inlist_fin = list(dict.fromkeys(inlist3))

        acre_matches_in = []
        acre_matches_all = []
        acre_clips_cm = []

        sqft_matches_in = []
        sqft_matches_all = []
        sqft_clips_cm = []

        unit_matches_in = []
        unit_matches_all = []
        unit_clips_cm = []

        for string in inlist_fin:
            acre_allclips = []
            sqft_allclips = []
            unit_allclips = []
            if string == '':
                continue
            string_rf = re.sub('[()]', '', string)
            check_string = string_rf.split(" ")
            if (len(check_string[0]) == 1 and check_string[0] != "a" and check_string[0] != "." and not check_string[0].isdigit()) or check_string[0].isdigit():
                continue
            ## OVERALL FLAG ##
            if re.findall(stopwords, string_rf, flags=re.IGNORECASE) and not re.findall("residential\sdistricts\sresidential\suses\.|rural\stransitional\sdistrict\sis\screated|single\s|permitted\sin\sthe\sr\-r\sdistrict|without\spublic\swater\sor\ssewer", string_rf, flags=re.IGNORECASE):
                if len(string_rf) < 300:
                    badstrings.append(string_rf)
                continue
            if any(string_rf in ab1 for ab1 in badstrings):
                continue

            ## ACRE INFO ##

            if re.findall(acreinfo_s, string_rf, flags=re.IGNORECASE):
                acre_matches_in = re.findall(acreinfo_s, string_rf, flags=re.IGNORECASE)
                acre_mpos_og = [m.start(0) for m in re.finditer(acreinfo_s, string_rf, flags=re.IGNORECASE)]
                acre_mpos1 = [[p - 250, p + 250] for p in acre_mpos_og]
                dsflag = 0
                perskip = 0
                for n, t in enumerate(acre_mpos1):
                    t = [0 if x < 0 else x for x in t]
                    t = [len(string_rf) if x > len(string_rf) else x for x in t]
                    acre_mpos1[n] = t
                acre_clips1 = []
                acre_ir = []
                for r, run in enumerate(acre_mpos1):
                    aclip1 = string_rf[run[0]:run[1]]

                    if re.findall(stopwords, aclip1, flags=re.IGNORECASE) and not re.findall("""(?x)residential\sdistricts\sresidential\suses\.|rural\stransitional\sdistrict\sis\screated|
                                                                                                (?<!with\s\d+\s|multiple\s)single\s|permitted\sin\sthe\sr\-r\sdistrict""", aclip1, flags=re.IGNORECASE):
                        continue

                    ## PUD FLAG ##
                    if re.findall(r"""(?x)(?:\b(multi\sfamily|two\sfamily|two\-family|townhouses|townhouse|
                            townhome|townhomes|apartments|apartment|mixed\-useplanned\sunit\sdevelopment|group\shomes|
                            planned\sunit\sdevelopments|planned\sdevelopment|pud|prd|planned\sproject)\b)""", aclip1, flags=re.IGNORECASE):
                        pudmatches = re.findall(r"""(?x)(?:\b(multi\sfamily|two\sfamily|two\-family|townhouses|townhouse|
                            townhome|townhomes|apartments|apartment|mixed\-useplanned\sunit\sdevelopment|group\shomes|
                            planned\sunit\sdevelopments|planned\sdevelopment|pud|prd|planned\sproject)\b)""", aclip1, flags=re.IGNORECASE)
                        pudl = list(dict.fromkeys(pudmatches))
                        pudm = pudl[0]
                        pudclipcon = r'\d*\.*\d*.{0,250}' + str(pudm) + r'.{0,250}\d*\.*\d*'
                        pudclip = re.findall(pudclipcon, aclip1, flags=re.IGNORECASE)
                        m = re.findall(r'\bunit\sper\sacre\b', str(pudclip), flags=re.IGNORECASE)
                        if re.findall(acreinfo_s, str(pudclip), flags=re.IGNORECASE):
                            if not re.findall(r'\bunit\sper\sacre\b|\bunit\sper\snet\sacre\b', str(pudclip), flags=re.IGNORECASE):
                                continue
                    # MF FLAGS ##
                    if re.findall(r"""(?x)efficiency|mixed\-use|\bapartment\b|apartments|lot\ssize\s\d+\sor\smore\sacre\.|senior|
                                  over\s\d+\sacre\sbut\sless\sthan\s\d+\sacre\.|acre\/\d+\ssquare\sfeet|for\sa\sdensity\smore\sintense\sthan|
                                  permitted\sdensity\sbe\sless\sthan\s\d+\.*\d*\sdwelling\sunit\sper\sgross\sacre|senior\sliving""", aclip1, flags=re.IGNORECASE) or any(aclip1 in ac1 for ac1 in mfh_badstrings):
                        mfh_badstrings.append(aclip1)
                        continue
                    if re.findall(r"maximum\snumber\sof\sunit\:\s\d+", aclip1, flags=re.IGNORECASE):
                        uclipget = re.findall(r"maximum\snumber\sof\sunit\:\s\d+", aclip1, flags=re.IGNORECASE)
                        for u in uclipget:
                            unums = re.findall(numbers, u, flags=re.IGNORECASE)
                            if any(float(ele) > 1 for ele in unums):
                                continue
                    ## PER ACRE FIX ##
                    if re.findall(r"""(?x)(?:(?<!by\s|greater\sthan\s)\d+\sdwelling\sunit\sper\sacre|(?<!by\s)\d+\sdwelling\sunit\sper\sgross\sacre|(?<!by\s)\sunit\sper\sacre\s\d+|
                                   per\s1\sacre|\d+\sto\s\d+\sunit\sper\snet\sacre|(?<!by\s)\d+\sunit\/acre|(?<!by\s)\d+\sunit\/acre|(?<!by\s)\d+\sunit\s\/\sacre|(?<!by\s)\d+\sunit\s\/\sacre|
                                   (?<!by\s)\d+\sunit\sper\sacre|(?<!by\s)\d+\sor\smore\sunit\sper\sstructure|(?<!by\s)\d+\sper\slot\sacre\.*|\d+\/gross\sacre|
                                   unit\sper\sgross\sacre\:\s\d+)""", aclip1, flags=re.IGNORECASE):
                        rep_match_list = re.findall(
                            r"""(?x)(?:(?<!by\s|greater\sthan\s)\d+\.*\d*\sdwelling\sunit\sper\sacre|(?<!by\s)\d+\.*\d*\sdwelling\sunit\sper\sgross\sacre|(?<!by\s)\sunit\sper\sacre\s\d+\.*\d*|
                                   per\s1\sacre|\d+\sto\s\d+\sunit\sper\snet\sacre|(?<!by\s)\d+\.*\d*\sunit\/acre|(?<!by\s)\d+\.*\d*\sunit\/acre|(?<!by\s)\d+\.*\d*\sunit\s\/\sacre|(?<!by\s)\d+\.*\d*\sunit\s\/\sacre|
                                   (?<!by\s)\d+\.*\d*\sunit\sper\sacre|(?<!by\s)\d+\.*\d*\sor\smore\sunit\sper\sstructure|(?<!by\s)\d+\.*\d*\sper\slot\sacre\.*|\d+\/gross\sacre|
                                   unit\sper\sgross\sacre\:\s\d+)""", aclip1, flags=re.IGNORECASE)
                        if re.findall(r"\.\s*$", "".join(rep_match_list), flags=re.IGNORECASE):
                            continue
                        if re.findall(r'zoned\sfor\sdensities\sgreater\sthan|that\shave\san\soverall\sdensity\sless\sthan\s\d+\sdwelling\sunit\sper\sacre|for\sa\sdensity\smore\sintense\sthan|permitted\sdensity\sbe\sless\sthan\s\d+\.*\d*\sdwelling\sunit\sper\sgross\sacre',
                                aclip1, flags=re.IGNORECASE):
                            continue
                        rep_match = max(rep_match_list)
                        num = re.findall(numbers, str(rep_match), flags=re.IGNORECASE)
                        for n in num:
                            if num and float(n) > 2:
                                perskip = 1
                                continue
                            elif num and 0 < float(n) < 2:
                                acre_matches_all.append(1 / float(n))
                                perskip = 1
                        if perskip == 1:
                            perskip = 0
                            continue
                    ## SQFT FLAG ##
                    if re.findall(r'square\sfeet\sof\sliving\sarea\s\d+', aclip1, flags=re.IGNORECASE):
                        rep_match = re.findall(r'square\sfeet\sof\sliving\sarea\s\d+', aclip1, flags=re.IGNORECASE)
                        num = re.findall(numbers, str(rep_match), flags=re.IGNORECASE)
                        finnum = "".join(num)
                        if finnum and float(finnum) <= 21780:
                            continue
                    ## MAXIMUM DENSITY FLAG ##
                    if re.findall(r'maximum\sdensity\:|gross\sdensity\:\s\d+|maximum\sdensity\sof\s\d+\.*\d*\sunit\sper\sacre|\d+\.*\d*\sto\s\d+\.*\d*\sdu\/gross\sacre',
                            aclip1, flags=re.IGNORECASE):
                        gdflag = re.findall(r'maximum\sdensity\:|gross\sdensity\:\s\d+\.*\d*|maximum\sdensity\sof\s\d+\.*\d*\sunit\sper\sacre|\d+\.*\d*\sto\s\d+\.*\d*\sdu\/gross\sacre',
                            aclip1, flags=re.IGNORECASE)
                        if re.findall(r"\.\s*$", "".join(gdflag), flags=re.IGNORECASE):
                            continue
                        if re.findall(r'zoned\sfor\sdensities\sgreater\sthan|for\sa\sdensity\smore\sintense\sthan',
                                      aclip1, flags=re.IGNORECASE):
                            continue
                        num = re.findall(numbers, str(gdflag), flags=re.IGNORECASE)
                        for n in num:
                            if num and float(n) > 2:
                                continue
                            elif num and 0 < float(n) < 2:
                                acre_matches_all.append(1 / float(n))
                                continue
                    if re.findall(r"""(?x)(?:(minimum\slot\ssize\sper\sdwelling\sunit|minimum\slot\sarea\sper\sdwelling\sunit|minimum\slot\sarea\sfor\sindividual\sunit|
                                      minimum\slot\sarea\sper\sdwelling|maximum\sdensity|
                                      allowed\sdwelling\sunit\sshall\sinclude\sa\sminimum\sof|per\sdwelling\sunit|per\sunit|minimum\scompact\slot\ssize))""",
                                  aclip1, flags=re.IGNORECASE):
                        newstart = [m.start(0) for m in re.finditer(r"""(?x)(?:(minimum\slot\ssize\sper\sdwelling\sunit|minimum\slot\sarea\sper\sdwelling\sunit|minimum\slot\sarea\sfor\sindividual\sunit|
                                      minimum\slot\sarea\sper\sdwelling|maximum\sdensity|
                                      allowed\sdwelling\sunit\sshall\sinclude\sa\sminimum\sof|per\sdwelling\sunit|per\sunit|minimum\scompact\slot\ssize))""",
                                     string_rf,flags=re.IGNORECASE)][0]
                        string_rf = string_rf[newstart:]
                    if re.findall(r"\b(minimum\sdwelling\ssite\sarea)\b", aclip1, flags=re.IGNORECASE):
                        dsflag = 1

                    if aclip1 in acre_clips_cm:
                        acre_ir.append(r)
                        continue
                    else:
                        acre_clips_cm.append(aclip1)
                        acre_clips1.append(aclip1)

                if acre_ir:
                    acre_ir = sorted(acre_ir, reverse=True)
                    for idx in acre_ir:
                        if idx < len(acre_mpos_og):
                            acre_mpos_og.pop(idx)
                            acre_mpos1.pop(idx)

                acre_allclips.extend(acre_clips1)

                for z, zz in enumerate(acre_allclips):
                    if acre_mpos_og[z] - 60 < 0:
                        ast2 = 0
                    else:
                        ast2 = acre_mpos_og[z] - 60
                    if acre_mpos_og[z] + 60 > len(string_rf):
                        aend2 = len(string_rf)
                    else:
                        aend2 = acre_mpos_og[z] + 60
                    acre_mpos2 = [ast2, aend2]
                    aclip2 = string_rf[acre_mpos2[0]:acre_mpos2[1]]
                    if re.findall(acre_rm, aclip2, flags=re.IGNORECASE):
                        acre_badstrings.append(aclip2)
                        continue
                    if any(aclip2 in ab2 for ab2 in acre_badstrings) or any(aclip2 in ab2 for ab2 in badstrings):
                        continue
                    if len(re.findall(numbers, aclip2, flags=re.IGNORECASE)) > 10:
                        continue
                    if re.findall(r'parcel\ssize\sminimum', aclip2, flags=re.IGNORECASE) and re.findall(r'individual\slot\sstandards\sminimum', string_rf, flags=re.IGNORECASE):
                        continue
                    if re.findall(r'minimum\slot\sarea\sfor\sdevelopment\:\s\d+\.*\d*\sacre', aclip2, flags=re.IGNORECASE) and re.findall(r'minimum\slot\ssize\:', aclip2, flags=re.IGNORECASE):
                        string_rf = re.sub(r'minimum\slot\sarea\sfor\sdevelopment\:\s\d+\.*\d*\sacre','', string_rf)
                    if re.findall(r'maximum\slot\ssize\sof\s\d+\s(acre|square\sfeet)*\s*\d*', aclip2, flags=re.IGNORECASE):
                        string_rf = re.sub(r'maximum\slot\ssize\sof\s\d+\s(acre|square\sfeet)*\s*\d*', "", string_rf)
                    if re.findall(r'minimum\slot\ssize\smaximum\slot\ssize|minimum\slot\sarea\smaximum\slot\sarea', aclip1, flags=re.IGNORECASE):
                        if re.findall(r'no\sminimum\s\d+\sacre|\d+\sacre\s\d+\sacre', aclip2, flags=re.IGNORECASE):
                            newzzend = [m.start(0) for m in re.finditer(r'no\sminimum\s\d+\sacre|\d+\sacre\s\d+\sacre', string_rf, flags=re.IGNORECASE)][0]
                            string_rf = aclip2[:newzzend + 5]
                    elif re.findall(r'maximum\slot\ssize|maximum\slot\sarea', aclip1, flags=re.IGNORECASE):
                        continue
                    if dsflag == 1:
                        dsmatches = re.findall(r"\b(minimum\sdwelling\ssite\sarea)\b", aclip2, flags=re.IGNORECASE)
                        for m in dsmatches:
                            if acre_mpos_og[z] - 10 < 0:
                                ast3 = 0
                            else:
                                ast3 = acre_mpos_og[z] - 10
                            if acre_mpos_og[z] + 10 > len(string_rf):
                                aend3 = len(string_rf)
                            else:
                                aend3 = acre_mpos_og[z] + 10
                            acre_mpos3 = [ast3, aend3]
                            aclip3 = string_rf[acre_mpos3[0]:acre_mpos3[1]]
                            acre_matches_all.append(aclip3)
                    elif re.findall(r"""(?x)\b(1\sdu\/|1\sdwelling\sunit\sper|1\sdwelling\sper|1\sunit\sper\s\d+\sacre|
                                     minimum|not\sless|no\sless|lot\ssize|lot\sarea|lot\ssurface\sarea|
                                     lot\swith\sseptic|r\-\D*\d*\sresidential)\b|area\:|1\sunit\/\s\d+\sacre|1\sunit\sto\s\d+\sacre|single\sfamily\sdwelling|
                                     lot\sshall\shave\san\sarea\sof\snot\sless\sthan|an\sarea\sof\snot\sless\sthan|zoning\slots\snot\sless\sthan|
                                     no\szoning\slot\sless\sthan|1\sdwelling\sunit\sper\sexisting\slot|total\sarea\sof\seach\slot\snot\sless\sthan|
                                     no\slot\sshall\sbe\screated\swhich\scontains|in\sno\scase\swill\sa\slot\sbe\splatted\swith\sless\sthan|
                                     residential\sdwelling\sunit\son\s\d+\.*\d*\sacre|residential\sdwelling\son\s\d+\.*\d*\sacre|
                                     land\sarea\sper\sdwelling|shall\scontain\sat\sleast|
                                     residential\sdwelling\sunit\son\s\d+\.*\d*\sacre|residential\sdwelling\son\s\d+\.*\d*\sacre""",
                                     aclip2, flags=re.IGNORECASE):
                        if acre_mpos_og[z] - 10 < 0:
                            ast3 = 0
                        else:
                            ast3 = acre_mpos_og[z] - 10
                        if acre_mpos_og[z] + 10 > len(string_rf):
                            aend3 = len(string_rf)
                        else:
                            aend3 = acre_mpos_og[z] + 10
                        acre_mpos3 = [ast3, aend3]
                        aclip3 = string_rf[acre_mpos3[0]:acre_mpos3[1]]
                        acre_matches_all.append(aclip3)
                        if re.findall(r'\b(per\sacre|du\'s|parcel|below)\b|\d+\}\d+', aclip3, flags=re.IGNORECASE):
                            continue
                        if 'maximum' in aclip2 and re.findall(r"\b(1\sdu\/|1\sdwelling\sunit\sper|1\sdwelling\sper)\b", aclip2, flags=re.IGNORECASE):
                            mxdstps = [m.start() for m in re.finditer(r"\b(1\sunit\sper\s\d+\sacre|1\sdu\/\d{1,2}\sacre|1\sdwelling\sunit\sper\s\d{1,2}\sacre|1\sdwelling\sper\s\d{1,2}\sacre)\b", aclip2, flags=re.IGNORECASE)]
                            mxd_index = aclip2.index('maximum')
                            if 'minimum' in aclip2:
                                continue
                            elif mxdstps and abs(mxd_index - mxdstps[0]) > 16:
                                continue
                            if 'maximum' in aclip3:
                                continue
                            elif 'minimum' in aclip2 and re.findall(r"\b(1\sdu\/|1\sdwelling\sunit\sper|1\sdwelling\sper)\b", aclip2, flags=re.IGNORECASE):
                                continue
                            elif 'maximum' not in aclip2 and 'density bonus' not in aclip2 and re.findall(r"\b(1\sdu\/|1\sdwelling\sunit\sper|1\sdwelling\sper)\b", aclip2, flags=re.IGNORECASE):
                                continue
                            elif re.findall(r'\b(maximum(?!\slot\scoverage))\b', aclip1, flags=re.IGNORECASE):
                                max_clip = r'\d*\.*\d*.{0,10}' + 'maximum' + r'.{0,10}\d*\.*\d*'
                                max_clip_text = re.findall(max_clip, aclip1, flags=re.IGNORECASE)
                                max_nums = re.findall(numbers, str(max_clip_text), flags=re.IGNORECASE)
                                if max_nums:
                                    max_num = max(max_nums)
                                    if str(max_num) in aclip3:
                                        continue
                            acre_matches_all.append(aclip3)
                for x, comp in enumerate(acre_matches_all):
                    if isinstance(comp, float):
                        comp2 = comp
                    else:
                        comp2 = re.sub(r"^\d+|r\-\s*\d*|\d+\s*$|\d+\.$|\d+\s*\d*\sfeet|\d+\s*feet|\d+\s*feet|\d+\'|\d+\sfee$|\<\s\d+\sacre|l\/2|\d+\sfe\s*$|\d+\sf\s*$|acre\.\s\d+\.\w+", "", str(comp))
                    nums = re.findall(numbers, str(comp2), flags=re.IGNORECASE)
                    for y in nums:
                        if re.findall(r"""(?x)\b(1\sdu\/|1\sdwelling\sunit\sper|1\sdwelling\sper|minimum\ssingle\sfamily\slot\ssize|
                                      single\sfamily\sdwellings\sshall\sprovide\sa\slot\sarea\sof\sat\sleast|a\-\d+\szone|
                                      r\-a\srural|a\-1\-a|a\-agriculture|agricultural\sdistrict|r\-1|suburban|
                                      rural\sagricultural|single\sfamily\suse|sr\szoning\sdistrict|single\sfamily\sdwellings)\b""", aclip1, flags=re.IGNORECASE):
                            if float(y.replace(',', '')) <= 50:
                                acre_shell.append(y)
                        else:
                            if float(y.replace(',', '')) <= 5:
                                acre_shell.append(y)

            ## UNIT INFO ##

            if re.findall(unitinfo_s, string_rf, flags=re.IGNORECASE):
                unit_matches_in = re.findall(unitinfo_s, string_rf, flags=re.IGNORECASE)
                unit_mpos_og = [m.start(0) for m in re.finditer(unitinfo_s, string_rf, flags=re.IGNORECASE)]
                unit_mpos1 = [[p - 150, p + 150] for p in unit_mpos_og]
                for n, t in enumerate(unit_mpos1):
                    t = [0 if x < 0 else x for x in t]
                    t = [len(string_rf) if x > len(string_rf) else x for x in t]
                    unit_mpos1[n] = t
                unit_clips1 = []
                unit_ir = []
                for r, run in enumerate(unit_mpos1):
                    uclip1 = string_rf[run[0]:run[1]]
                    if re.findall(stopwords, uclip1, flags=re.IGNORECASE) and not re.findall("residential\sdistricts\sresidential\suses\.|rural\stransitional\sdistrict\sis\screated|single\s|permitted\sin\sthe\sr\-r\sdistrict", uclip1, flags=re.IGNORECASE):
                        continue

                    if uclip1 in unit_clips_cm:
                        unit_ir.append(r)
                        continue
                    else:
                        unit_clips_cm.append(uclip1)
                        unit_clips1.append(uclip1)

                if unit_ir:
                    unit_ir = sorted(unit_ir, reverse=True)
                    for idx in unit_ir:
                        if idx < len(unit_mpos_og):
                            unit_mpos_og.pop(idx)
                            unit_mpos1.pop(idx)

                unit_allclips.extend(unit_clips1)

                for z, zz in enumerate(unit_allclips):
                    if unit_matches_in[z] == "minimum number of unit":
                        if unit_mpos_og[z] - 50 < 0:
                            ust2 = 0
                        else:
                            ust2 = unit_mpos_og[z] - 50
                        if unit_mpos_og[z] + 65 > len(string_rf):
                            und2 = len(string_rf)
                        else:
                            und2 = unit_mpos_og[z] + 65
                        unit_mpos2 = [ust2, und2]
                    else:
                        if unit_mpos_og[z] - 50 < 0:
                            ust2 = 0
                        else:
                            ust2 = unit_mpos_og[z] - 50
                        if unit_mpos_og[z] + 50 > len(string_rf):
                            und2 = len(string_rf)
                        else:
                            und2 = unit_mpos_og[z] + 50
                        unit_mpos2 = [ust2, und2]
                    uclip2 = string_rf[unit_mpos2[0]:unit_mpos2[1]]
                    if re.findall(unit_rm, uclip2, flags=re.IGNORECASE):
                        unit_badstrings.append(uclip2)
                        continue
                    if any(uclip2 in ab2 for ab2 in unit_badstrings) or any(uclip2 in ab2 for ab2 in badstrings):
                        continue
                    if len(re.findall(numbers, uclip2, flags=re.IGNORECASE)) > 10:
                        continue
                    if unit_matches_in[z] == "minimum number of unit":
                        if unit_mpos_og[z] - 25 < 0:
                            ust3 = 0
                        else:
                            ust3 = unit_mpos_og[z] - 25
                        if unit_mpos_og[z] + 65 > len(string_rf):
                            und3 = len(string_rf)
                        else:
                            und3 = unit_mpos_og[z] + 65
                        unit_mpos3 = [ust3, und3]
                    else:
                        if unit_mpos_og[z] - 25 < 0:
                            ust3 = 0
                        else:
                            ust3 = unit_mpos_og[z] - 25
                        if unit_mpos_og[z] + 25 > len(string_rf):
                            und3 = len(string_rf)
                        else:
                            und3 = unit_mpos_og[z] + 25
                        unit_mpos3 = [ust3, und3]
                    uclip3 = string_rf[unit_mpos3[0]:unit_mpos3[1]]
                    unit_matches_all.append(uclip3)
                for x, comp in enumerate(unit_matches_all):
                    if re.findall(r'\b(minimum\sdensity|percent|per$|\d+\s*\d*\spe$|bedroom\sper\sdwelling\sunit\s\d+\ssquare|per\sdwelling\sunit|unit\sper\smile|single\sfamily\sdwelling\sunit\sfootprint)\b|\%', "".join(comp), flags=re.IGNORECASE):
                        continue
                    if re.findall(r"\d+\sdwelling\sunit(?!\sper\sacre)|\d+\sunit(?!\sper\sacre)|\d+\sor\smore\slot\sand\/or\sdwelling\sunit", "".join(comp), flags=re.IGNORECASE):
                        continue
                    comp2 = re.sub(r"ordinance\s\d+|record\.\s*\d+\.|\d+\s*\d*\sfeet|\d+\sfeet\s\d+\s*$|\d+\sfeet|\d+\s\d+\.*\d*\ssquare\sfeet|^\d+|\$\d+\.*\d*|\d+\s*feet|\d+\s*feet|\d+\s*fee|\d+\'|\d+\sacre|\d+\sft\s*\d*|far\s\d+\.*\d*|\d+\sf|\d+\s*$|\d+\-{2,}\d+|\d+\spoints|or\s\d+\s[a-z]+$", "", str(comp))
                    nums = re.findall(numbers, str(comp2), flags=re.IGNORECASE)
                    for y in nums:
                        if 0 < float(y.replace(',', '')) <= 165:
                            unit_shell.append(y)

            ## SQFT INFO ##

            if re.findall(sqftinfo_s, string_rf, flags=re.IGNORECASE):
                sqft_matches_in = re.findall(sqftinfo_s, string_rf, flags=re.IGNORECASE)
                sqft_mpos_og = [m.start(0) for m in re.finditer(sqftinfo_s, string_rf, flags=re.IGNORECASE)]
                sqft_mpos1 = [[p - 200, p + 200] for p in sqft_mpos_og]
                dsflag = 0
                perskip = 0
                mfflag = 0
                for n, t in enumerate(sqft_mpos1):
                    t = [0 if x < 0 else x for x in t]
                    t = [len(string_rf) if x > len(string_rf) else x for x in t]
                    sqft_mpos1[n] = t
                sqft_clips1 = []
                sqft_ir = []
                for r, run in enumerate(sqft_mpos1):
                    sclip1 = string_rf[run[0]:run[1]]

                    if re.findall(stopwords, sclip1, flags=re.IGNORECASE) and not re.findall("residential\sdistricts\sresidential\suses\.|rural\stransitional\sdistrict\sis\screated|single\s|permitted\sin\sthe\sr\-r\sdistrict", sclip1, flags=re.IGNORECASE):
                        continue

                    if re.findall(r'planned\sunit\sdevelopment|planned\sunit\sdevelopments|planned\sdevelopment|pud', sclip1, flags=re.IGNORECASE):
                        pudmatches = re.findall(r'planned\sunit\sdevelopment|planned\sunit\sdevelopments|planned\sdevelopment|pud', sclip1, flags=re.IGNORECASE)
                        pudl = list(dict.fromkeys(pudmatches))
                        pudm = pudl[0]
                        pudclipcon = str(pudm) + r'\d*\.*\d*.{0,250}'
                        pudclip = re.findall(pudclipcon, sclip1, flags=re.IGNORECASE)
                        m = re.findall(r'\bper\sdwelling\sunit\b', str(pudclip), flags=re.IGNORECASE)
                        if re.findall(sqftinfo_s, str(pudclip), flags=re.IGNORECASE):
                            if re.findall(r'\bper\sdwelling\sunit\b', str(pudclip), flags=re.IGNORECASE):
                                pudstart = [m.start(0) for m in re.finditer(r"""(?x)(?:(\bper\sdwelling\sunit\b))""", string_rf, flags=re.IGNORECASE)][0]
                                string_rf = string_rf[pudstart:]
                            else:
                                continue
                    if re.findall(r"""(?x)(?:(minimum\slot\ssize\sper\sdwelling\sunit|minimum\slot\sarea\sper\sdwelling\sunit|minimum\slot\sarea\sfor\sindividual\sunit|
                                   allowed\sdwelling\sunit\sshall\sinclude\sa\sminimum\sof|maximum\sdensity\:|minimum\scompact\slot\ssize|
                                   residential\sdwellings\sper\sunit))""", string_rf, flags=re.IGNORECASE):
                        newstart = [m.start(0) for m in re.finditer(r"""(?x)(?:(minimum\slot\ssize\sper\sdwelling\sunit|minimum\slot\sarea\sper\sdwelling\sunit|minimum\slot\sarea\sfor\sindividual\sunit|
                                                                    allowed\sdwelling\sunit\sshall\sinclude\sa\sminimum\sof|maximum\sdensity\:|minimum\scompact\slot\ssize|
                                                                    residential\sdwellings\sper\sunit))""", string_rf, flags=re.IGNORECASE)][0]
                        string_rf = string_rf[newstart:]
                    if re.findall(r"""(?x)(?:\b(minimum\sdwelling\ssite\sarea|square\sfeet\sper\sdwelling\sunit|1\sunit\sfor\severy\s\d+|
                                   1\sdu\sper\sfull\s\d+|square\sfeet\sfor\seach\sfo\sthe\sfirst\s\d+\sdwelling\sunit|
                                   each\sdwelling\sshall\shave\sa\stotal\sarea\sof\snot\sless\sthan\s\d+\ssquare\sfeet|
                                   per\sfamily\sunit|minimum\slot\sarea\sper\sunit|land\sarea\sper\sdwelling|
                                   square\sfeet\sper\sunit|minimum\sland\sarea\sper\sdwelling\sunit|
                                   square\sfeet\sfor\seach\sunit|square\sfeet\sper\sunit|
                                   square\sfeet\sfor\sall\sdwelling\sunit)\b)""", sclip1, flags=re.IGNORECASE):
                        dsflag = 1
                    if re.findall(r"""(?x)(?:\b(multi\sfamily|two\sfamily|two\-family|townhouses|townhouse|townhome|
                                      townhomes|apartments|apartment|mixed\-use)\b)""", sclip1, flags=re.IGNORECASE):
                        mfflag = 1

                    if sclip1 in sqft_clips_cm:
                        sqft_ir.append(r)
                        continue
                    else:
                        sqft_clips_cm.append(sclip1)
                        sqft_clips1.append(sclip1)

                if sqft_ir:
                    sqft_ir = sorted(sqft_ir, reverse=True)
                    for idx in sqft_ir:
                        if idx < len(sqft_mpos_og):
                            sqft_mpos_og.pop(idx)
                            sqft_mpos1.pop(idx)

                sqft_allclips.extend(sqft_clips1)

                for z, zz in enumerate(sqft_allclips):
                    if sqft_mpos_og[z] - 65 < 0:
                        sst2 = 0
                    else:
                        sst2 = sqft_mpos_og[z] - 65
                    if sqft_mpos_og[z] + 65 > len(string_rf):
                        snd2 = len(string_rf)
                    else:
                        snd2 = sqft_mpos_og[z] + 65
                    sqft_mpos2 = [sst2, snd2]
                    sclip2 = string_rf[sqft_mpos2[0]:sqft_mpos2[1]]

                    if re.findall(sqft_rm, sclip2, flags=re.IGNORECASE):
                        sqft_badstrings.append(sclip2)
                        continue
                    if any(sclip2 in ab2 for ab2 in sqft_badstrings) or any(sclip2 in ab2 for ab2 in badstrings):
                        continue
                    if len(re.findall(numbers, sclip2, flags=re.IGNORECASE)) > 10:
                        continue
                    if re.findall(r'minimum\sfloor\sarea|floor\sarea(?!\sratio)|minimum\sliving\sfloor\sarea|minimum\sdwelling\ssize', string_rf, flags=re.IGNORECASE):
                        if re.findall(r'lot\sarea|lot\ssize', sclip2, flags=re.IGNORECASE) and re.findall(r'minimum\sfloor\sarea|floor\sarea|minimum\sliving\sfloor\sarea|minimum\sdwelling\ssize', sclip2, flags=re.IGNORECASE):
                            ls = [m.start(0) for m in re.finditer(r'lot\sarea|lot\ssize', string_rf, flags=re.IGNORECASE)][0]
                            fa = [m.start(0) for m in re.finditer(r'minimum\sfloor\sarea|floor\sarea|minimum\sdwelling\ssize', string_rf, flags=re.IGNORECASE)][0]
                            if fa > ls:
                                string_rf = string_rf[:fa]
                            else:
                                string_rf = string_rf[fa + 10:]
                        else:
                            continue
                    if re.findall(r'minimum\slot\ssize\smaximum\slot\ssize|minimum\slot\sarea\smaximum\slot\sarea', sclip1, flags=re.IGNORECASE):
                        if re.findall(r'no\sminimum\s\d+\ssquare\sfeet|\d+\ssquare\sfeet\s\d+\ssquare\sfeet', sclip2, flags=re.IGNORECASE):
                            newzzend = [m.start(0) for m in re.finditer(r'no\sminimum\s\d+\ssquare\sfeet|\d+\ssquare\sfeet\s\d+\ssquare\sfeet', string_rf, flags=re.IGNORECASE)][0]
                            string_rf = string_rf[:newzzend]
                    elif re.findall(r'maximum\slot\ssize|maximum\slot\sarea', sclip1, flags=re.IGNORECASE):
                        continue
                    if re.findall(r'\b(having\san\sarea\sof\sless\sthan\s\d+\ssquare\sfeet)\b', sclip2, flags=re.IGNORECASE) and re.findall(r'\b(no\sprincipal\sbuilding\sor\suse)\b', sclip1, flags=re.IGNORECASE):
                        wmatches = re.findall(r'\b(having\san\sarea\sof\sless\sthan\s\d+\ssquare\sfeet)\b', sclip2, flags=re.IGNORECASE)
                        for w in wmatches:
                            sqft_mpos3 = [sqft_mpos_og[z] - 10, sqft_mpos_og[z] + 10]
                            sclip3 = string_rf[sqft_mpos3[0]:sqft_mpos3[1]]
                            sqft_matches_all.append(sclip3)
                    if re.findall(r'\d+\ssquare\sfeet\splus\s\d+\ssquare\sfeet\sfor\seach\sunit|\d+\ssquare\sfeet\splus\s\d+\ssquare\sfeet\sfor\sea', sclip2, flags=re.IGNORECASE):
                        fcstart = [m.start(0) for m in re.finditer(r'plus\s\d+\ssquare\sfeet\sfor\seach\sunit|plus\s\d+\ssquare\sfeet\sfor\sea', string_rf, flags=re.IGNORECASE)][0]
                        fclip = string_rf[fcstart:fcstart+25]
                        sqft_matches_all.append(fclip)
                        continue
                    if re.findall('maximum\slot\ssize\sof\s\d+\s(acre|square\sfeet)*\s*\d*', sclip2, flags=re.IGNORECASE):
                        string_rf = re.sub(r'maximum\slot\ssize\sof\s\d+\s(acre|square\sfeet)*\s*\d*',"", string_rf)
                    if dsflag == 1:
                        dsmatches = re.findall(r"""(?x)(?:\b(minimum\sdwelling\ssite\sarea|square\sfeet\sper\sdwelling\sunit|1\sunit\sfor\severy\s\d+|
                                                minimum\slot\sarea\sper\sfamily\sin\ssquare\sfeet|minimum\slot\sarea\sper\sunit|
                                                1\sdu\sper\sfull\s\d+|square\sfeet\sfor\seach\sfo\sthe\sfirst\s\d+\sdwelling\sunit|
                                                nor\sshall\sthe\sland\sarea\sprovide\sfor\seach\sdwelling\sunit\son\sthe\slot\sbe\sless\sthan|
                                                each\sdwelling\sshall\shave\sa\stotal\sarea\sof\snot\sless\sthan\s\d+\ssquare\sfeet|
                                                land\sarea\sper\sdwelling|square\sfeet\sper\sfamily\sunit|square\sfeet\sper\sunit|
                                                square\sfeet\sfor\seach\sunit|square\sfeet\sper\sunit|
                                                square\sfeet\sfor\sall\sdwelling\sunit|unit)\b)""", sclip2, flags=re.IGNORECASE)
                        for m in dsmatches:
                            if sqft_mpos_og[z] - 35 < 0:
                                sst3 = 0
                            else:
                                sst3 = sqft_mpos_og[z] - 35
                            if sqft_mpos_og[z] + 35 > len(string_rf):
                                snd3 = len(string_rf)
                            else:
                                snd3 = sqft_mpos_og[z] + 35
                            sqft_mpos3 = [sst3, snd3]
                            sclip3 = string_rf[sqft_mpos3[0]:sqft_mpos3[1]]
                            sqft_matches_all.append(sclip3)
                            continue
                    elif re.findall(r"""(?x)(?:\b(minimum|no\sless|lot\ssize|lot\sarea|lot\ssurface\sarea|lot\shaving\sa\stotal\sarea|
                                     maximum\spermitted\sresidential\sdensity|per\sdwelling\sunit|parcel\sarea\smin|
                                     maximum\sallowable\sresidential\sdensity|maximum\spermitted\sdensity|minimum\ssite\sarea|
                                     maximum\sallowable\sdensity|for\seach\sdwelling\sunit|single\sfamily\sdwelling|
                                     lot\sshall\shave\san\sarea\sof\snot\sless\sthan|zoning\slot\snot\sless\sthan|
                                     no\szoning\slot\sless\sthan|no\slot\sshall\sbe\screated\swhich\scontains\sless\sthan|
                                     dwelling\sis\serected\sshall\shave\san\sarea\sof\snot\sless\sthan|each\sadditional\sdwelling\sunit|
                                     an\sarea\sof\snot\sless\sthan\s\d+\ssquare\sfeet|shall\snot\sbe\sreduced\sto\sless\sthan|
                                     in\sno\scase\swill\sa\slot\sbe\splatted\swith\sless\sthan|total\sarea\sof\seach\slot\snot\sless\sthan|
                                     an\sarea\sof\snot\sless\sthan|contains\sat\sleast\s\d+\ssquare\sfeet)\b|lot\sarea\.|area\.\sminimum)""", sclip2, flags=re.IGNORECASE):
                        if re.findall(r'(?<!coverage\:\s|height\s)maximum(?!\sbuilding\sheight|\sheight\:|\slot\scoverage|\scoverage\:|\sbuilding)', sclip1, flags=re.IGNORECASE):
                            max_clip = r'\d*\.*\d*.{0,20}' + 'maximum' + r'.{0,20}\d*\.*\d*'
                            max_clip_text = re.findall(max_clip, sclip1, flags=re.IGNORECASE)
                            max_nums = re.findall(numbers, str(max_clip_text), flags=re.IGNORECASE)
                            if max_nums:
                                max_num = max(max_nums)
                                if re.findall(r'\b' + str(max_num) + r'\b', sclip2, flags=re.IGNORECASE):
                                    continue
                        if re.findall(r"riparian\sno\ssewer\:", sclip2, flags=re.IGNORECASE):
                            string_rf = re.sub(r"riparian\sno\ssewer\:","",string_rf)
                        if sqft_mpos_og[z] - 45 < 0:
                            sst3 = 0
                        else:
                            sst3 = sqft_mpos_og[z] - 45
                        if sqft_mpos_og[z] + 45 > len(string_rf):
                            snd3 = len(string_rf)
                        else:
                            snd3 = sqft_mpos_og[z] + 45
                        sqft_mpos3 = [sst3, snd3]
                        sclip3 = string_rf[sqft_mpos3[0]:sqft_mpos3[1]]
                        nums_init = re.findall(numbers, str(sclip3), flags=re.IGNORECASE)
                        if nums_init:
                            nums_init_num = [float(i) for i in nums_init]
                            minnum = min(nums_init_num)
                            if float(minnum) < 2000 and not re.findall(r"area|lot\ssize|each\sadditional\sdwelling\sunit", sclip2, flags=re.IGNORECASE):
                                continue
                        sqft_matches_all.append(sclip3)
                for x, comp in enumerate(sqft_matches_all):
                    comp = re.sub(r"""(?x)\d+\s*$|^\w\:\d+|^\d+|january\s\d+|february\s\d+|march\s\d+|april\s\d+|
                                  may\s\d+|june\s\d+|july\s\d+|august\s\d+|september\s\d+|october\s\d+|\d+\.*\s*$|
                                  november\s\d+|december\s\d+|in\sexcess\sof\s\d+\s*\d*\ssquare\sfeet|part\s\d+|no\.\s\d+|
                                  \d+\ssquare\sfeet\smax""", "", comp)
                    if re.findall(r'over\:|outdoor\sliving\sspace', str(comp), flags=re.IGNORECASE):
                        continue
                    nums = re.findall(numbers, str(comp), flags=re.IGNORECASE)
                    for y in nums:
                        if (380 <= float(y.replace(',', '')) and mfflag == 0) or (
                                380 <= float(y.replace(',', '')) < 15000 and mfflag == 1):
                            sqft_shell.append(y)
            else:
                continue
        dinfo_acre.append(acre_shell)
        dinfo_unit.append(unit_shell)
        dinfo_sqft.append(sqft_shell)
        acre_shell = []
        unit_shell = []
        sqft_shell = []

    minfo = dinfo_acre[0] + dinfo_acre[1] + dinfo_sqft[0]
    dinfo = dinfo_unit[0] + dinfo_unit[1] + dinfo_sqft[1]
    minfo_full = list(dict.fromkeys(minfo))
    dinfo_full = list(dict.fromkeys(dinfo))

    return [minfo_full, dinfo_full]


'''
the function heightinfo extracts building height maximum regulations not in dimensional tables and instead stated
directly in the text. It takes input strings and extracts this information in terms of feet and stories (if relevant). 
'''

def heightinfo(input1):

    ## deduplicate input lists ##
    inlist1_rd = []
    inlist1 = []
    inlist2 = []
    inlist3 = []
    inlist_fin = []

    for l in input1:
        inlist1_rd = list(dict.fromkeys(l))
        inlist1.extend(inlist1_rd)
        inlist1_rd = []

    for i in inlist1:
        inlist2.append(fractonum(i))

    for i in inlist2:
        try:
            inlist3.append(text2int(i))
        except ValueError:
            inlist3.append(i)
        except IndexError:
            inlist3.append(i)


    inlist_fin = list(dict.fromkeys(inlist3))

    matches_height_ft_pt1 = []
    all_matches_height_ft = []
    height_ft_matches = []

    matches_height_st_pt1 = []
    all_matches_height_st = []
    height_st_matches = []

    clips1_ft_cm = []
    clips1_st_cm = []

    bad_words = r"""(?x)(?:(\b(atennas|tower|towers|truck|motorized|snow\sstorage|commercial|display|mounted|attendants|
                               for\severy\sdwelling\sunit|office|hives|landscaping|airport|telecommunication|vehicle|pole|cemeteries|
                               truck|equipment|restaurant|closet|bunk\sbed|tree|trees|fence|fences|nonabsorbent|surcharge|retaining\swalls|
                               slope|storage|mezzanine|mezzanines|monument|stump|stumps|noxious|plants|evergreen|telephone|leachate|
                               growing|limousine|horse|horses|secure\senclosure|dog|botanical|erosion|balustrade|obstacle\sfree\spath|wireless|
                               headlight|installation|screening|leaf|from\sany\spublic\ssidewalk|canopy|pavement\swidth|damage|pool|freeboard|
                               drawn\sat\sa\sscale|feet\sfrom\sthe\sfront\sor\sstreet\sline|shrubs|incinerator|barbecue|professional\sengineer|
                               jail|planting\sstrip|purchaser|runway|feet\sin\sbuilding\sheight\smay\sbe\sadded|multi\-ten|stallions|flagpoles|
                               tennis\scourts|service\sstation|facility|useable\sopen\sspace|driveways|animal|utility\sowner|trunk\sdiameter|
                               nonfixed\sand\smovable\sfixtures|conical\szone|runways|antenna|abutting\san\sra|emergency\sresponder|vegetation\swildlife|
                               industrial|maximum\slength|turbine|airspace|federal|turnaround|headlamps|nonresidential)\b|\$|bulk\srequire\:|
                               cornice\streatments|roof\spitch|garage\sand\ssite\srestrictions|campers|eleemosynary\snature|
                               shall\sbe\smoved\sinto\san\senclosed\sbuilding|no\slighting\sshall\sbe\sof\ssuch\sa\snature|porte\-cochere|
                               height\sof\s\d+\sfeet\swithin\sa\srequire\sside\sor\srear\syard|a\smain\sbuilding\slimit\sto|gazebos\sshall|
                               parking\sspace\ssize|light\sstandard\sheight|temples\smay|flame\scooking\sdevices|agricultural\sstructures\.|
                               formulas\sdetermining\sminimum\sopen\sspace\srequire|street\slighting\spost\slamps|pf\-\d+\sdistrict\:|
                               no\sgarage\sserving\sa\ssingle\sfamily\sresidential\sunit\sshall\sbe\sgreater\sthan|of\-\d+\sdistrict\:|
                               emergency\sexit|subject\sto\sa\ssite\splan\sapprove\sby\sthe\scommission|minimum\ssetback\sfor\saccessory\sbuilding|
                               no\ssubstance\sother\sthan\soil|tennis\scourt|cr\sdesignation|operator\'s\sfarm|silos\smay\sexceed|
                               cc\sdistrict\ssubject\sto\sadditional\srequire|highway\s\d+\scorridor\sdistrict|
                               table\sof\sdimensional\sstandards\:|m\.p\.h\.|drive\-up|whip\santenna|watchman\semployed))"""
    for string in inlist_fin:
        allclips_ft = []
        allclips_st = []

        if string == '':
            continue
        if re.findall(r"no\.\s\d+\-\d+\s*\d*\s*\d*\-*\d*\-*\d*|\.\d\.\d+", string,flags=re.IGNORECASE):
            string = re.sub(r"no\.\s\d+\-\d+\s*\d*\s*\d*\-*\d*\-*\d*|\.\d\.\d+","",string)
        if re.findall(r"\d+\ssquare\sfeet|\d+\ssq\.\sfeet|\d+\ssq\\sft", string, flags=re.IGNORECASE):
            string = re.sub(r"\d+\ssquare\sfeet|\d+\ssq\.\sfeet|\d+\ssq\\sft","",string)
        if re.findall(r"any\s\d+\-foot\slength|any\s\d+\sfoot\slenght", string, flags=re.IGNORECASE):
            string = re.sub(r"any\s\d+\-foot\slength|any\s\d+\sfoot\slenght","",string)
        if re.findall(r"feet\.\d+\.", string, flags=re.IGNORECASE):
            string = re.sub(r"\.\d+\.","",string)
        if re.findall(r"\d{4}\s*\.\d+|\d{2}\-\d{2}\-\d{4}", string, flags=re.IGNORECASE):
            string = re.sub(r"\d{4}\s*\.\d+|\d{2}\-\d{2}\-\d{4}","",string)
        string_rf = re.sub('[()]', '', string)

        if re.findall(bad_words, string_rf, flags=re.IGNORECASE):
            continue

        ## HEIGHT (FEET) INFO ##
        if re.findall(height_ft, string_rf, flags=re.IGNORECASE):
            if re.findall(r"\d+\.*\d*\sstory|\d+\.*\d*\s\d*\.*\d*\s*stories", string_rf, flags=re.IGNORECASE):
                string_ft = re.sub(r"\d+\.*\d*\sstory|\d+\.*\d*\s\d*\.*\d*\s*stories", "", string_rf)
            else:
                string_ft = string_rf

            matches_height_ft_pt1 = re.findall(height_ft, string_ft, flags=re.IGNORECASE)
            mpos_og_ft = [m.start(0) for m in re.finditer(height_ft, string_ft, flags=re.IGNORECASE)]
            mpos1_ft = [[p - 70, p + 10] for p in mpos_og_ft]
            for n, t in enumerate(mpos1_ft):
                t = [0 if x < 0 else x for x in t]
                t = [len(string_ft) if x > len(string_ft) else x for x in t]
                mpos1_ft[n] = t

            clips1_ft = []
            ir = []
            for r, run in enumerate(mpos1_ft):
                clip = string_ft[run[0]:run[1]]
                if clip in clips1_ft_cm:
                    ir.append(r)
                    continue
                else:
                    clips1_ft_cm.append(clip)
                    clips1_ft.append(clip)

            if ir:
                ir = sorted(ir, reverse=True)
                for idx in ir:
                    if idx < len(mpos_og_ft):
                        mpos_og_ft.pop(idx)
                        mpos1_ft.pop(idx)
            allclips_ft.extend(clips1_ft)

            for z, zz in enumerate(allclips_ft):
                hmatches = [m.start(0) for m in re.finditer(r"""(?x)height""", string_ft, flags=re.IGNORECASE)]
                if re.findall(r"""(?x)ceiling|wall\sheight|nonabsorbent|increase|decrease|height\sof\sthe\swall|
                              all\splaces\swhere\smore\sthan\s\d+\sfamilies\sreside|
                              sidewalk|relation\sof\sground|flush|higher|yard|parking|taller|above|
                              line\s\d+\sfeet\sfrom|feet\sin\swidth|driveway|lineal\sfeet\sof\swall|cubic|
                              sill\sheight|lot\sline|mezzanine|mezzanines|minimum\slot\swidth|width\:|
                              whenever\sany\sbuilding\sexceeds|exceptions\:|building\swhich\sdoes\snot\sexceed|
                              within\s\d+\sfeet|west|east|north|south|from\sthe\sintersection|setback|set\sback|
                              depth\sof\s\d+\sfeet|public\ssidewalk|buffer\sarea|ffer\sarea|\d+\sfeet\sbetween|
                              wider\sthan\s\d+\sfeet|by\smore\sthan|nearer\sthan\s\d+\sfeet|feet\swide|feet\sfrom|
                              accessory|within\s\d+\sfeet|sea\slevel|front\sbuilding\sline\:|line\:|wall\splane|
                              lot\sfrontage\sof\s\d+\s*\d*\sfeet|pitch\sof\smore\sthan|by\san\sadditional\s\d+\sfeet|
                              freestanding\sbuildings\sshall\sbe\slimit\sto\s\d+\ssqaure\sfeet|frontage|
                              minimum\sclear\sheight\sof\s\d{1}\sfeet|lighting|landscape\sberm|garage|
                              garden\sstructures|screen|driveways|stairwells|satellite\sdish|campers|maximum\ssystem\sheight|
                              \d+\sfeet\sof\sroad|height\svariance|exterior\slight\ssources|\d+\sfloor\selevation\sexceeds|
                              no\sexisting\sframe\sbuilding\sshall\sbe\sraised\sto\sa\sheight\sexceeding|
                              setback\sfrom\sexternal\slot\sline\:|setback\sfrom\sexternal\srow\:|mausoleums\:|
                              mounting\sheight|illumination|residential\sproperty\sline|length\sof\swalls|
                              exit\saccess\stravel\sdistance|length\sof\sthe\sfacade|adu|floor\stop\splate|
                              supporting\sstructure|temples|schools|diamet|river|campus|ampus|lot\soccupation|
                              shed\sroof\sstyle|piled\sat\sa\sheight|which\sdo\snot\sexceed|trailer\swith\s\a\smaximum\sbody\slength|
                              conditional\suse\spermit|block\sfaces|freestanding\ssystems|farm\sstructures\:|
                              horizontal\slength|wca|wcsf|tennis\scourt|quasipublic\sbuildings|each\sstory\sshall\snot\sexceed|
                              so\slong\sas\sthe\smain\sbuilding\sis\slimit\sto|auditoriums|building\sdisposition|
                              long\sas\sall\smain\sbuildings\sare\slimit\sto|properties\sbeyond\s\d+\sfeet|c
                              length\sor\sa\swidth\sgreater\sthan|communications\satennas|maximum\spermitted\spost\sheight\sof|
                              nor\sshall\sit\sbe\sless\sthan\s\d+\sfeet|billboard\'s|shelter\sare\slimit|
                              stacked\sto\sa\sheight\sgreater\sthan|demolition\sof\sany\sbuilding\sexceeding|
                              for\seach\sfoot\sin\sheight\sthat\sa\sstructure\sshall\sexceed|slopes\sgreater\sthan|
                              for\sany\sstructure\sexceeding|light\sfixtures\sexceeding|arena|
                              buildings\sthat\sexceed\s\d+\sfeet|hc\/g\sdistricts|building\sheights\sin\sthe\sc\/r|
                              height\sof\sthe\sprincipal\sstructure\sor\s\d+\sfeet|light\sfixture\sshall\snot\sexceed|
                              for\seach\sfoot\sthat\sthe\sstructure\sexceeds|gross\ssurface\sarea|
                              total\sof\ssaid\sfeatures|percent\sof\sthe\swidth\sof\sthe\slot|permitted\sheight\sof\sa\smarquee\ssign|
                              lot\swidth\sof\s\d+\sfeet|parking\sstructure|mechanical\ssystems|
                              the\sheight\sof\sthe\sbuilding\sexceeds|all\sstructures\:|notes\:|
                              for\seach\s\d+\sfeet|greater\sof\s\d+\sfeet\sor""", str(zz), flags=re.IGNORECASE):
                    continue
                elif any(abs(mpos_og_ft[z] - float(e)) <= 50 for e in hmatches) and re.findall(r"""(?x)maximum|max|exceed|greater\sthan|single\sfamily\sdetached\sdwelling|
                                duplex\sdwelling|principal\sbuilding\sor\sstructure|height\sfeet|
                                building\sheight\sof|building\sheight\sexceeding|principal\sbuildings|
                                three\-family\sdwelling|townhouse|apartment|shall\sbe\slimit""", str(zz), flags=re.IGNORECASE):
                    mpos2_ft = [mpos_og_ft[z] -10, mpos_og_ft[z] + 10]
                    clip2_ft = string_ft[mpos2_ft[0]:mpos2_ft[1]]
                    all_matches_height_ft.append(clip2_ft)
                elif re.findall(r"maximum\sheight\sfeet", string_ft, flags=re.IGNORECASE):
                    match_pos_ft = [m.start(0) for m in re.finditer(r"maximum\sheight\sfeet", string_ft, flags=re.IGNORECASE)][0]
                    new_extract_ft = string_ft[match_pos_ft:]
                    all_matches_height_ft.append(new_extract_ft)

        ## HEIGHT (STORIES) INFO ##
        if re.findall(height_st, string_rf, flags=re.IGNORECASE):
            matches_height_st_pt1 = re.findall(height_st, string_rf, flags=re.IGNORECASE)
            mpos_og_st = [m.start(0) for m in re.finditer(height_st, string_rf, flags=re.IGNORECASE)]
            mpos1_st = [[p - 70, p + 10] for p in mpos_og_st]
            for n, t in enumerate(mpos1_st):
                t = [0 if x < 0 else x for x in t]
                t = [len(string_rf) if x > len(string_rf) else x for x in t]
                mpos1_st[n] = t

            clips1_st = []
            ir = []
            for r, run in enumerate(mpos1_st):
                clip = string_rf[run[0]:run[1]]
                if clip in clips1_st_cm:
                    ir.append(r)
                    continue
                else:
                    clips1_st_cm.append(clip)
                    clips1_st.append(clip)

            if ir:
                ir = sorted(ir, reverse=True)
                for idx in ir:
                    if idx < len(mpos_og_st):
                        mpos_og_st.pop(idx)
                        mpos1_st.pop(idx)

            allclips_st.extend(clips1_st)

            for z, zz in enumerate(allclips_st):
                if re.findall(r"""(?x)floor\sarea\scalculation|structure\smore\sthan\sone\-story|
                              all\splaces\swhere\smore\sthan\s\d+\sfamilies\sreside|open\sair\sassembly|
                              permitted\sonly\sin\sbuildings\s\d+\sstories\sor|downtown\sbusiness\sdistrict|
                              dwellings\s\d+\sstories\sor|dwellings\smore\sthan\s\d+\sstories|
                              beginning\sat\sthe\s\d\sstory\slevel|which\sdo\snot\sexceed\s\d+\sstories|
                              if\sthe\sbuilding\sto\sbe\serected\sis\smore\sthan\s\d+\sstories|
                              whenever\sany\sbuilding\sexceeds|exceptions\:|building\swhich\sdoes\snot\sexceed|
                              if\ssuch\sbuilding\sis\snot\smore\sthan|dual\sexits|the\s\d+\sstory\sfor|
                              reaches\sthe\slevel\sof\sthe\s\d+\sstory|all\sstructures\snot\sexceeding\s\d+\stories|
                              except\sthat\sin\sattics|construction\sdocuments|accessory|adu|
                              more\sthan\s\d+\sstories\sin\sheight\san\sadditional|hospital\sproperty|
                              for\sbuildings\smore\sthan\s\d+\sstories|top\sstory\sattic|higher\seducational\sproperty|
                              rooming\shouse\sor\sboarding\shouse|\d+\sfeet\sof\sadditional\sheight|
                              for\sall\sbuildings\smore\sthan\s\d+\sstories|\d\s1st\sstory|for\slot\s\<|
                              require\son\sstructures\swith\smore\sthan\s\d+\sstories|demolition\sof\sany\sbuilding\sexceeding|
                              which\sdo\snot\sexceed|any\skind\swhich\sis\sin\sexcess|mechanical\ssystems|
                              may\sbe\sincreased\sby\sone\sstory|to\s\d+\sor\smore|unenclosed\sporches|
                              may\sbe\sincreased\sby\s1|p\-1\sdistrict|stories\.\s\d+|contain\smore\sthan\s\d+\sstory|♦
                              substance\sother\sthan\soil|for\s\d+\sstory|notes\:|parking\sstructure|
                              interior\sheight\sof\ssuch\sstory|noncombustible\scovering\:|for\sstructures\s\d+\sstories\sor|
                              so\slong\sas\sthe\smain\sbuilding\sis\slimit\sto|equivalent\sof\sthe\s\d+\sstory|
                              long\sas\sall\smain\sbuildings\sare\slimit\sto|at\sthe\s\d+\sstory|bale\swalls\sshall\snot\sexceed|
                              hc\/g\sdistricts|building\sheights\sin\sthe\sc\/r|consisting\sof\smasonry\sor\sframe\swalls|
                              neighboring\smain\sbuildings\sdoes\snot\sexceed\s\d+\sstory|ceiling\sjoists\sof\sa\s\d+\sstory|
                              attic\sabove\sa\s\d+\sstory|in\scases\swhere\sthe\sbuilding\sor\sstructure\sis\smore\sthan|
                              each\sadditional\sstory\sabove\sthe\s\d+\sstory|encroachment\sshall\sbe\slimit\sto\sthe\s\d+\sstory|
                              width\sof\sthe\s\d+\sstory|e\.g\.\s\d+\sstory|finished\sfloor\sof\sthe\s\d+\sstory|
                              where\sconstruction\sinvolves\smore\sthan\s\d+\sstory|
                              total\sof\ssaid\sfeatures|may\sbe\seither\s\d+\sor\s\d+\sstories|setback\sat\sthe\s\d+\sstory|
                              implemented\sat\sthe\s\d+\sstory|above\sthe\s\d+\sstory|percent\sof\sthe\s\d+\sstory|
                              where\sthe\smaximum\sbuilding\sheight\sexceeds\s\d+\sstories""", str(zz), flags=re.IGNORECASE):
                    continue
                mpos2_st = [mpos_og_st[z] - 10, mpos_og_st[z] + 10]
                clip2_st = string_rf[mpos2_st[0]:mpos2_st[1]]
                all_matches_height_st.append(clip2_st)

    for x, comp in enumerate(all_matches_height_ft):
        if re.findall(r"lot\swidth", str(comp), flags=re.IGNORECASE):
            continue
        if re.findall(r"h\sfeet\s\d+\sfeet\s\d+\sfe|\d+\sfeet\s\d+\sfeet\s\d+\sfe|\d+\sfeet\s\d+\sfeet\sb\sexc", str(comp), flags=re.IGNORECASE) and len(comp) <= 20:
            continue
        if re.findall(r"""(?x)\d+\smm|stories\sfeet\s\d{1}\w|stories\sfeet\s\d{1}\sor\s\d{1}|stories\sfeet\s\d{1}|mfr\s\d{1}\s\d{1}|\d{1}f\-\d+|part\s\d+|
                      \d\.*\d*\s\d+\sfeet\s\d\.*\d*\s\d+|\+\s\d+|\.\s\d\.\d+|\d+\sfeet\sin\slength|\d+\sfeet\sor\swider|square\sfeet\s\d+|^\d\s|\d+\.\d+\s*$|\d+\s*$|
                      \<\s\d+|^\d+""", str(comp), flags=re.IGNORECASE):
            comp = re.sub(r"""(?x)stories\sfeet\s\d{1}\w|stories\sfeet\s\d{1}\sor\s\d{1}|stories\sfeet\s\d{1}|mfr\s\d{1}\s\d{1}|\d{1}f\-\d+|part\s\d+|
                          \d\.*\d*\s\d+\sfeet\s\d\.*\d*\s\d+|\+\s\d+|\.\s\d\.\d+|\d+\sfeet\sin\slength|\d+\sfeet\sor\swider|square\sfeet\s\d+|^\d\s|\d+\.\d+\s*$|\d+\s*$|
                          \<\s\d+|^\d+""", "", str(comp))
        nums = re.findall(numbers, str(comp), flags=re.IGNORECASE)
        nums_un = list(dict.fromkeys(nums))
        height_ft_matches.extend(nums_un)

    for x, comp in enumerate(all_matches_height_st):
        if re.findall(r"""(?x)\d+\smm|stories\sfeet\s\d{1}\w|stories\sfeet\s\d{1}\sor\s\d{1}|stories\sfeet\s\d{1}|mfr\s\d{1}\s\d{1}|\d{1}f\-\d+|part\s\d+|\d+\sfeet\/|\d+\sf$|\d+\'|\d+\:|
                      \d\.*\d*\s\d+\sfeet\s\d\.*\d*\s\d+|\+\s\d+|\.\s\d\.\d+|\d+\sfeet\sin\slength|\d+\sfeet\sor\swider|square\sfeet\s\d+|\d+\.\sstory|story\.\s\d+\.|^\d\s|\d+\.\d+\s*$|
                      over\s\d+\sstory\shigh|^\dfeet|\d+\s*$|\d+\sstory\sfaca|\d+\-\s\/|\d+\-\s(?!stories)|\d+\sstory\sor\sm|\d+\sstories\sor\sm|\d+\sfeet|\d+\s*$""", str(comp), flags=re.IGNORECASE):
            comp = re.sub(r"""(?x)\d+\smm|stories\sfeet\s\d{1}\w|stories\sfeet\s\d{1}\sor\s\d{1}|stories\sfeet\s\d{1}|mfr\s\d{1}\s\d{1}|\d{1}f\-\d+|part\s\d+|\d+\sfeet\/|\d+\sf$|\d+\'|\d+\:|
                          \d\.*\d*\s\d+\sfeet\s\d\.*\d*\s\d+|\+\s\d+|\.\s\d\.\d+|\d+\sfeet\sin\slength|\d+\sfeet\sor\swider|square\sfeet\s\d+|\d+\.\sstory|story\.\s\d+\.|^\d\s|\d+\.\d+\s*$|
                          over\s\d+\sstory\shigh|^\dfeet|\d+\s*$|\d+\sstory\sfaca|\d+\-\s\/|\d+\-\s(?!stories)|\d+\sstory\sor\sm|\d+\sstories\sor\sm|\d+\sfeet|\d+\s*$""","", str(comp))
        nums = re.findall(numbers, str(comp), flags=re.IGNORECASE)
        nums_un = list(dict.fromkeys(nums))
        height_st_matches.extend(nums_un)

    hinfo_ft_num_in = [float(i) for i in height_ft_matches]
    hinfo_ft_num = [x for x in hinfo_ft_num_in if x >= 10]
    hinfo_st_num = [float(i) for i in height_st_matches]

    #print("HEIGHT FEET")
    #print(hinfo_ft_num)

    #print("HEIGHT STORIES")
    #print(hinfo_st_num)

    return [hinfo_ft_num,hinfo_st_num]

'''
the function parkinginfo extracts minimum parking regulations stated directly in the text. It takes input strings and 
extracts this information for any districts with allowed residential uses.
'''

def parkinginfo(input1):
    ## deduplicate input lists ##
    inlist1_rd = []
    inlist1 = []
    inlist2 = []
    inlist3 = []
    inlist_fin = []

    for l in input1:
        inlist1_rd = list(dict.fromkeys(l))
        inlist1.extend(inlist1_rd)
        inlist1_rd = []

    for i in inlist1:
        inlist2.append(fractonum(i))

    for i in inlist2:
        ifm = re.sub(r"dwellings\-", "dwellings ", i)
        try:
            inlist3.append(text2int(ifm))
        except ValueError:
            inlist3.append(ifm)
        except IndexError:
            inlist3.append(ifm)

    inlist_fin = list(dict.fromkeys(inlist3))

    matches_pk_pt1 = []
    all_matches_pk = []
    pk_matches = []

    clips1_cm = []

    bad_words = r"""(?x)(?:(\b(atennas|tower|towers|artificial|arena|glare|
                     parking\sstructures|data\ssystems|trespass|aircraft|engineers|cleanup|
                     parking\sgarages|snow\sstorage|amending|intersection|bus\sparking|refuse\scontainers|
                     loading\szones|security\sfence|repeals\sand\sreplaces|city\sclerk\sduties|
                     landscaped\sislands|trunk\sheight|
                     cleaned|reflectors)\b|\$|a\.d\.t\.))"""

    for string in inlist_fin:
        allclips = []

        if re.findall('\d*\.*\d*\(\d\)', string, flags=re.IGNORECASE):
            string = re.sub('\d*\.*\d*\(\d\)', '', string)
        if re.findall('[()]', string, flags=re.IGNORECASE):
            string = re.sub('[()]', ' ', string)
        if re.findall(r'\b\d{1}\.\s|\b\d{4}\.\d{2}\s|\d+\.\d+\.\d+', string, flags=re.IGNORECASE):
            string = re.sub(r'\b\d{1}\.\s|\b\d{4}\.\d{2}\s|\d+\.\d+\.\d+', '', string)
        if re.findall(r'\s\d{1,2}\.\D', string, flags=re.IGNORECASE):
            csflags = re.findall(r'\s\d{1,2}\.\D', string, flags=re.IGNORECASE)
            for cmatch in csflags:
                crep = string.index(cmatch)
                string_rf = string[:crep] + "" + string[crep + 2:]
        else:
            string_rf = string

        if re.findall(bad_words, string_rf, flags=re.IGNORECASE):
            continue

        ## PARKING INFO ##
        if re.findall(parkinfo, string_rf, flags=re.IGNORECASE):

            matches_pk_pt1 = re.findall(parkinfo, string_rf, flags=re.IGNORECASE)
            mpos_og = [m.start(0) for m in re.finditer(parkinfo, string_rf, flags=re.IGNORECASE)]
            mpos1 = [[p - 70, p + 70] for p in mpos_og]
            for n, t in enumerate(mpos1):
                t = [0 if x < 0 else x for x in t]
                t = [len(string_rf) if x > len(string_rf) else x for x in t]
                mpos1[n] = t

            clips1 = []
            ir = []
            for r, run in enumerate(mpos1):
                clip = string_rf[run[0]:run[1]]
                if clip in clips1_cm:
                    ir.append(r)
                    continue
                else:
                    clips1_cm.append(clip)
                    clips1.append(clip)

            if ir:
                ir = sorted(ir, reverse=True)
                for idx in ir:
                    if idx < len(mpos_og):
                        mpos_og.pop(idx)
                        mpos1.pop(idx)

            allclips.extend(clips1)

            for z, zz in enumerate(allclips):
                if re.findall(r"""(?x)ceiling|\d+\sfeet\sof\stotal\sdistance|bike|circuit|ch\.\s\d+|amends|
                                   subsection|wider\sthan|\d+\sfeet\slong|improper|island|compact\scar|
                                   \d+\sor\smore\ssurface\sparking\sspaces\smust\sbe\sscreened|bowling|dental|
                                   visitor\sparking\sspaces\smay\sbe\slocated|retail|trees|shrubs|parallel\sparking|
                                   loading\sarea|with\smore\sthan\s\d+\sparking|corresponding\sto|\d\-\d\sstandards|
                                   off\-site\sfacilities|all\szones\swhere|car\swash|minimum\s\d\-|
                                   where\sa\sany\soff\-street\sparking\sarea\scontains\smore\sthan\s\d+parking|
                                   parking\sarea\sof\smore\sthan\s\d\s\d\sparking\sspaces|bed\sand\sbreakfast|
                                   each\sparking\sspace\sshall\snot\sbe\sless\sthan\s\d+|shall\smeasure|market\spud|
                                   minimum\ssize\sof\seach\scommercial\sparking\sspace|area\srequire\sfor\sparking\s\d+|
                                   percent\sof\sthe\slot\sarea|private\sclubs\sand\slodges|no\.\s\d\-\d+|
                                   that\sgenerate\s\d+\sor\smore\sparking\sspaces|parking\slot\sfor\s\d+\sor\smore\scars|
                                   parking\sareas\sfor\s\d+\s+or\smore\scars|area\srequire\sfor\s\d+\sautomobile|
                                   parking\sstalls|computing\sthe\snumber\sof\sparking\sspaces|caliper|
                                   which\srequire\sno\smore\sthan\s\d+\s+additional\sparking\sspaces|sterling\scodifiers|
                                   site\sshall\scontain\sa\sminimum\sof\s\d+\sparking\sspaces\.|front\:|side\:|rear\:|
                                   in\saddition\sto\sthe\sparking\srequire|self\-serve|automatic\swash|
                                   maximum\sof\s\d+\sspaces|the\suse\sof\soutdoor\syard\sareas|storage\sbuildings|
                                   shall\sbe\sprovide\sas\srequire\sby\sparking\sand\sloading|
                                   amended\s\/\d+\/\d+|where\s\d+\sor\smore\suses\sexist|shall\be\scounted\sas|
                                   for\sall\ssuch\splan\srequire|vertical\sclearance|attachment""", str(zz),
                                  flags=re.IGNORECASE):
                    continue
                elif re.findall(r"""(?x)\b(require|not\sto\sexceed|minimum|for\seach\sunit|for\seach\sdwelling|per\sdwelling|for\seach\sapartment|
                                           single\sfamily\sdwellings|for\seach\sfamily|apartments|dwelling)\b""", str(zz), flags=re.IGNORECASE):
                    mpos2 = [mpos_og[z] - 45, mpos_og[z] + 45]
                    clip2 = string_rf[mpos2[0]:mpos2[1]]
                    all_matches_pk.append(clip2)

    for x, comp in enumerate(all_matches_pk):
        if re.findall(r"""(?x)recreation|entertainment|golf|industrial|loading\/unloading|video\srental|
                           restaurant|parking\sspace\sreduction|candles|name\splate\ssign|
                           self\-storage\swarehouse|barber|bar\s+lounge|semiautomatic|retirement\svillage""", str(comp), flags=re.IGNORECASE):
            continue
        pprob = r"""(?x)\b\w{1}\s\d+\.\d+|\d+\.*\d*\spercent|per\severy\s\d+|for\severy\s\d+\s*\d*|per\s\d+|
                         located\s\d+|\d+\.\s|\d+\s\d*\s*feet|\d+\s\d*\s*percent|\d\struck|article\s\d+|
                         for\seach\s\d+\sparking\sspaces\sover\s\d+|\d+\sor\smore\ssq|\d{4}\s\d+|\d+\s\d*\s*perc|
                          x\s\d+\sminimum\ssquare|\d+\'\sx\s\d+\'|\d+\sor\sfewer\sparking|\d+\'|\d+\smonths|title\s\d+|
                          not\sto\sexceed\s\d+\sper\sunit|reduced\sby\smore\sthan\s\d+|\d+\shour|\d\.\sparking\sspace\:|
                          without\s\d+\shaving|\d+\syear|\d+\sby\s\d+|\d+\sseat|\d+\sdegrees|chapter\s\d+|\d+\sfeet|
                          table\.\w\.\d|exhibit\s\d+\s*\-\s*\d+|\d\sof\severy\s\d|unit\s\d\sand\s\d|^\d+|\d+\s*$|
                          with\s\d+\sor\smore|\d+\-\d\.\d+\.*|\d+\-\d\.|\d+\.\d+\s\d+|\d+\-\d+\-\d+|\d+\-\d+\.*\d*|
                          \d+\sfee$|\d{4}\s\d\-\d\-\d\-\:|\d+\sfeet\sby\s\d+\sfeet|x\s\d+\'|\d\-\d\w\-\d+\:|
                          \d+\sbedroom|\d+\sor\smore\sbedrooms|\d+\s+driveway|\d+\s\+\s\d+|\d+\s+\d+\s+percent|
                          \d+\s+percent|\d+\s+\d+\s+spaces\sor\smore|\d*\s*\d+\s*$|^\s*\d*\s*\d*|^\-\d+\s*\d*|
                          \d+\sspace\sper\semployee|article\sd+|index\s\-\s\d+|refer\sto\s\d+\.*\d*|\d+\s+inches|
                          \d\w\-\d\:|passed\s\d+\-\d+|\d+\spercent|c\-\s*\d+|\d+\-\d+\sarticle|\d+\sinch|\d+\sper$|
                          or\s\d+\sspaces\swhichever|\d+\sfloor\sunit|
                          art\.\s\d+\s\-\s\d+|medical\soffices\s\d+|\d+\sspaces\sper\sdoctor|\d+\-foot"""
        if re.findall(pprob, str(comp), flags=re.IGNORECASE):
            comp = re.sub(pprob, "", comp)
        nums = re.findall(numbers, str(comp), flags=re.IGNORECASE)
        nums_un = list(dict.fromkeys(nums))
        pk_matches.extend(nums_un)

    parking_fin_un = list(dict.fromkeys(pk_matches))

    if pk_matches:
        parking_num_in = [float(i) for i in pk_matches]
        parking_num = [x for x in parking_num_in if x <= 10]
    else:
        parking_num = []

    if parking_num:
        parking_median = statistics.median(parking_num)
        parking_mode = statistics.mode(parking_num)
    else:
        parking_median = None
        parking_mode = None

    if parking_median == None or parking_mode == None:
        for string_rf in inlist_fin:
            if re.findall(r"space\sper\sdwelling\sunit|residential\s\d\/dwelling", string_rf, flags=re.IGNORECASE):
                ppos = [m.start(0) for m in
                        re.finditer(r"space\sper\sdwelling\sunit|residential\s\d\/dwelling", string_rf,
                                    flags=re.IGNORECASE)][0]
                pclip = string_rf[ppos - 10:ppos + 20]
                pclip_fin = re.sub(r"\/", " ", pclip)
                pres = re.findall(numbers, pclip_fin, flags=re.IGNORECASE)
                if pres:
                    parking_num_in = [float(i) for i in pres]
                    parking_num = [x for x in parking_num_in if x <= 10]
                if parking_num:
                    parking_median = statistics.median(parking_num)
                    parking_mode = statistics.mode(parking_num)
                    break

    return [parking_num]


'''
The matchvalue function is used to convert matches from the get_matches function into their respective weights. 
This is done using the dictionaries pulled in with the get_keywords function above. The output is the same 
layered list organization as the matches function (see explanation above) except each keyword has now been replaced by 
its respective weight (as an integer).
'''


def matchvalue(inputs):
    matches_shell1 = []
    matches_shell2 = []
    matches_shell3 = []
    matches_shell_final = []
    matches = inputs
    dicts = get_keywords()
    for q, question in enumerate(matches):
        dict = dicts[matches.index(question)]
        qweights = []
        weights = list(dict.values())
        for num in weights:
            qweights.append(float(num))
        for new in question:
            for response in new:
                for word in response:
                    for key in dict.keys():
                        if word == key:
                            matches_shell1.append(float(dict[key]))
                matches_shell2.append(matches_shell1)
                matches_shell1 = []
            matches_shell3.append(matches_shell2)
            matches_shell2 = []
        matches_shell_final.append(matches_shell3)
        matches_shell3 = []
    return matches_shell_final


'''
The thresholdmark function is used to indicate which measures are present for each input file. It does this by summing 
the weights of all matching keywords for each question/measure (lists within each question/measure list). If the sum of 
the keyword weights crosses our threshold (currently 5), it is represented as a 1 and a 0 if it does not. The output of 
this function now just has two layers: the outer layer is a list of 27 elements representing the 27 questions/measures
and the inner layer is a list of 1s and 0s representing whether each original set of keyword matches crossed the 
threshold or not. 
'''

def thresholdmark(inputs):
    thresholds_res = []
    thresholds_new = []
    thresholds_final = []
    match_values = matchvalue(inputs)
    for question in match_values:
        for new in question:
            for response in new:
                score = sum(response)
                if score > 5:
                    thresholds_res.append(1)
                else:
                    thresholds_res.append(0)
            test = sum(thresholds_res)
            thresholds_res = []
            thresholds_new.append(test)
        thresholds_final.append(thresholds_new)
        thresholds_new = []
    return thresholds_final


'''
The finfun function runs the entire program and produces the output data. First, it writes the column names of the 
output spreadsheet manually. Next, it iterates through each file by calling all of the functions above. Each input file
takes on a new row of the output data and each column takes on a value according to the output of a particular nested
function above.

Some files may give a UnicodeDecodeError, meaning that they are encoded in something other than the standard format. These
files will be stored as blank rows in the main 'Municipalities' sheet and they are also added to a second sheet labeled
'Error Cities'.

Since the other functions described above are nested within the finfun function, the only function needed to call
is finfun(list of files).

'''

def finfun(filenames):
    # print(biglist1)
    outxl = xlwt.Workbook()
    outsheet = outxl.add_sheet('Municipalities', cell_overwrite_ok=True)
    errorsheet = outxl.add_sheet('Error Cities')
    outsheet.write(0, 0, "muni")
    outsheet.write(0, 1, "restrict_sf_permit")
    outsheet.write(0, 2, "restrict_mf_permit")
    outsheet.write(0, 3, "limit_sf_units")
    outsheet.write(0, 4, "limit_mf_units")
    outsheet.write(0, 5, "limit_mf_dwellings")
    outsheet.write(0, 6, "limit_mf_dwelling_units")
    outsheet.write(0, 7, "min_lot_size")
    outsheet.write(0, 8, "max_density")
    outsheet.write(0, 9, "open_space")
    outsheet.write(0, 10, "inclusionary")
    outsheet.write(0, 11, "council_nz")
    outsheet.write(0, 12, "planning_nz")
    outsheet.write(0, 13, "countybrd_nz")
    outsheet.write(0, 14, "pubhlth_nz")
    outsheet.write(0, 15, "site_plan_nz")
    outsheet.write(0, 16, "env_rev_nz")
    outsheet.write(0, 17, "council_rz")
    outsheet.write(0, 18, "planning_rz")
    outsheet.write(0, 19, "zoning_rz")
    outsheet.write(0, 20, "countybrd_rz")
    outsheet.write(0, 21, "countyzone_rz")
    outsheet.write(0, 22, "townmeet_rz")
    outsheet.write(0, 23, "env_rev_rz")
    outsheet.write(0, 24, "adu")
    outsheet.write(0, 25, "half_acre_less")
    outsheet.write(0, 26, "half_acre_more")
    outsheet.write(0, 27, "one_acre_more")
    outsheet.write(0, 28, "two_acre_more")
    outsheet.write(0, 29, "max_den_cat1")
    outsheet.write(0, 30, "max_den_cat2")
    outsheet.write(0, 31, "max_den_cat3")
    outsheet.write(0, 32, "max_den_cat4")
    outsheet.write(0, 33, "max_den_cat5")
    outsheet.write(0, 34, "height_ft_median")
    outsheet.write(0, 35, "height_ft_mode")
    outsheet.write(0, 36, "height_st_median")
    outsheet.write(0, 37, "height_st_mode")
    outsheet.write(0, 38, "parking_median")
    outsheet.write(0, 39, "parking_mode")
    outsheet.write(0, 40, "mf per")
    outsheet.write(0, 41, "timestamp")
    errorsheet.write(0, 0, 'muni')
    startrow = 1
    errorrow = 1
    for file in filenames:
        try:
            print(file)
            startcol = 1
            outsheet.write(startrow, 0, file)
            getmatches_res = getmatches(file,startrow)
            getmatches_othvars = getmatches_res[0]
            getmatches_mls = getmatches_res[1]
            getmatches_md = getmatches_res[2]
            getmatches_h = getmatches_res[3]
            getmatches_p = getmatches_res[4]
            getmatches_rd = getmatches_res[5]
            thresholds_final = thresholdmark(getmatches_othvars)
            dinfo1 = densityinfo(getmatches_mls, getmatches_md)
            hinfo = heightinfo(getmatches_h)
            pinfo = parkinginfo(getmatches_p)
            mls1 = dinfo1[0]
            md1 = dinfo1[1]
            mf_dis_per = resdis(getmatches_rd)
            dinfo3 = buildtablel1(getmatches_mls, getmatches_md)
            mls3 = dinfo3[0]
            md3 = dinfo3[1]
            dinfo4 = buildtablel2(getmatches_mls, getmatches_md)
            mls4 = dinfo4[0]
            md4 = dinfo4[1]
            mls = mls1 + mls3 + mls4
            md = md1 + md3 + md4
            mls_full = list(dict.fromkeys(mls))
            md_full = list(dict.fromkeys(md))
            park = pinfo[0]
            hft1 = hinfo[0]
            hst1 = hinfo[1]
            ht2_ft = dinfo3[2]
            ht2_st = dinfo3[3]
            ht3_ft = dinfo4[2]
            ht3_st = dinfo4[3]
            hft2 = []
            hst2 = []
            hft3 = []
            hst3 = []
            for h in ht2_ft:
                if float(h) > 10:
                    hft2.append(h)
            for h in ht2_st:
                hst2.append(h)
            for h in ht3_ft:
                if float(h) > 10:
                    hft3.append(h)
            for h in ht3_st:
                hst3.append(h)
            ht_ft_all = hft1 + hft2 + hft3
            ht_st_all = hst1 + hst2 + hst3
            ht_ft_uni = list(dict.fromkeys(ht_ft_all))
            ht_st_uni = list(dict.fromkeys(ht_st_all))
            if ht_ft_all:
                hinfo_ft_median = statistics.median(ht_ft_all)
            else:
                hinfo_ft_median = None
            if ht_ft_all:
                hinfo_ft_mode = statistics.mode(ht_ft_all)
            else:
                hinfo_ft_mode = None
            if ht_st_all:
                hinfo_st_median = statistics.median(ht_st_all)
            else:
                hinfo_st_median = None
            if ht_st_all:
                hinfo_st_mode = statistics.mode(ht_st_all)
            else:
                hinfo_st_mode = None

            if park:
                pinfo_median = statistics.median(park)
            else:
                pinfo_median = None
            if park:
                pinfo_mode = statistics.mode(park)
            else:
                pinfo_mode = None
            mls_int = []
            md_int = []
            for i in mls_full:
                mls_int.append(str(i).replace(',', ''))
            for i in md_full:
                md_int.append(str(i).replace(',', ''))
            mls_final = []
            md_final = []
            for x in mls_int:
                try:
                    x = re.sub(r'(\d+)/(\d+)', lambda m: str(float(m.group(1)) / float(m.group(2))), x)
                    mls_final.append(float(x))
                except ZeroDivisionError as error:
                    continue
                except ValueError:
                    continue
            for x in md_int:
                try:
                    x = re.sub(r'(\d+)/(\d+)', lambda m: str(float(m.group(1)) / float(m.group(2))), x)
                    md_final.append(float(x))
                except ZeroDivisionError as error:
                    continue
                except ValueError:
                    continue
            #print(mls_final)
            #print(md_final)

            ## final calculations ##
            for question in thresholds_final:
                if sum(question) > 0:
                    outsheet.write(startrow, startcol, 1)
                else:
                    outsheet.write(startrow, startcol, 0)
                startcol += 1
            for x in mls_final:
                if 1000 < float(x) < 21780 or 0 < float(x) < 0.5:
                    outsheet.write(startrow, 25, 1)
                    break
                else:
                    outsheet.write(startrow, 25, 0)
            for x in mls_final:
                if 21780 <= float(x) < 43560 or 0.5 <= float(x) < 1:
                    outsheet.write(startrow, 26, 1)
                    break
                else:
                    outsheet.write(startrow, 26, 0)
            for x in mls_final:
                if 43560 <= float(x) < 87120 or 1 <= float(x) < 2:
                    outsheet.write(startrow, 27, 1)
                    break
                else:
                    outsheet.write(startrow, 27, 0)
            for x in mls_final:
                if 87120 <= float(x) <= 217800 or 2 <= float(x) <= 50:
                    outsheet.write(startrow, 28, 1)
                    break
                else:
                    outsheet.write(startrow, 28, 0)
            if not md_final:
                if not mls_final:
                    outsheet.write(startrow, 29, 1)
                    outsheet.write(startrow, 30, 0)
                    outsheet.write(startrow, 31, 0)
                    outsheet.write(startrow, 32, 0)
                    outsheet.write(startrow, 33, 0)
                else:
                    for x in mls_final:
                        if float(x) > 10890:
                            outsheet.write(startrow, 29, 1)
                            outsheet.write(startrow, 30, 0)
                            outsheet.write(startrow, 31, 0)
                            outsheet.write(startrow, 32, 0)
                            outsheet.write(startrow, 33, 0)
                    for x in mls_final:
                        if 6223 < float(x) <= 10890:
                            outsheet.write(startrow, 29, 1)
                            outsheet.write(startrow, 30, 1)
                            outsheet.write(startrow, 31, 0)
                            outsheet.write(startrow, 32, 0)
                            outsheet.write(startrow, 33, 0)
                    for x in mls_final:
                        if 3111 < float(x) <= 6223:
                            outsheet.write(startrow, 29, 1)
                            outsheet.write(startrow, 30, 1)
                            outsheet.write(startrow, 31, 1)
                            outsheet.write(startrow, 32, 0)
                            outsheet.write(startrow, 33, 0)
                    for x in mls_final:
                        if 1452 < float(x) <= 3111:
                            outsheet.write(startrow, 29, 1)
                            outsheet.write(startrow, 30, 1)
                            outsheet.write(startrow, 31, 1)
                            outsheet.write(startrow, 32, 1)
                            outsheet.write(startrow, 33, 0)
                    for x in mls_final:
                        if 500 < float(x) <= 1452:
                            outsheet.write(startrow, 29, 1)
                            outsheet.write(startrow, 30, 1)
                            outsheet.write(startrow, 31, 1)
                            outsheet.write(startrow, 32, 1)
                            outsheet.write(startrow, 33, 1)
            else:
                for x in md_final:
                    if 0 < float(x) <= 4 or float(x) > 10890:
                        outsheet.write(startrow, 29, 1)
                        break
                    else:
                        outsheet.write(startrow, 29, 0)
                for x in md_final:
                    if 4 < float(x) <= 7 or 6223 < float(x) <= 10890:
                        outsheet.write(startrow, 30, 1)
                        break
                    else:
                        outsheet.write(startrow, 30, 0)
                for x in md_final:
                    if 7 < float(x) <= 14 or 3111 < float(x) <= 6223:
                        outsheet.write(startrow, 31, 1)
                        break
                    else:
                        outsheet.write(startrow, 31, 0)
                for x in md_final:
                    if 14 < float(x) <= 30 or 1452 < float(x) <= 3111:
                        outsheet.write(startrow, 32, 1)
                        break
                    else:
                        outsheet.write(startrow, 32, 0)
                for x in md_final:
                    if 30 < float(x) <= 165 or 380 < float(x) <= 1452:
                        outsheet.write(startrow, 33, 1)
                        break
                    else:
                        outsheet.write(startrow, 33, 0)
            outsheet.write(startrow, 34, hinfo_ft_median)
            outsheet.write(startrow, 35, hinfo_ft_mode)
            outsheet.write(startrow, 36, hinfo_st_median)
            outsheet.write(startrow, 37, hinfo_st_mode)
            outsheet.write(startrow, 38, pinfo_median)
            outsheet.write(startrow, 39, pinfo_mode)
            outsheet.write(startrow, 40, mf_dis_per)
            ts = get_ts(file)
            outsheet.write(startrow, 41, ts)
            print(file, "post sheet")
            startrow += 1
        except UnicodeDecodeError:
            errorsheet.write(errorrow, 0, file)
            errorrow += 1
            startrow += 1
            print(file, "hit decode error")
    outxl.save(outputfilename)



filenames = sorted(glob.glob(filedirect + "*.txt")) # finds all .txt files in the folder your code is saved in
finfun(filenames)  # the final function


