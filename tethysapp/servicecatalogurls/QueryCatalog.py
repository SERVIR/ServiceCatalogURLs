"""
# Initial Creation:
#   Lance Gilliland - March 1, 2019
# General Description:
#   This script uses the Service Catalog API (see "Servir - ServiceCalatogue GraphQL API.PDF") to request all services
#   objects contained within the Service Catalog.  Then, for each service, it parses through the Data, Tools, News,
#   and Training Materials category fields, extracting the URLs defined in each category field.  Note that currently,
#   these category fields are multiline text fields containing markup-style text, thus we have to parse through the
#   text and extract the URLs that nee to be verified.  The goal of the script is to generate a list of URLs (along
#   with the corresponding service and category) of URLs that return an error code.
#
# More Detail:
#   The original script was adapted to this version which can be called by a Django app.
#   QueryServiceCatalog() is the main entry point from the calling app.
#
# Last Modified By:
#   Lance Gilliland - March 19, 2019
#           Setup the default logging and a check for "DATA" URLs on whether or not they contain "gis1.servirglobal.net"
#           as part of the URL. "DATA" entries in the Service Catalog should point to the Global Data Catalog at
#           http://gis1.servirglobal.net:8080/geonetwork/...  Any "DATA" URLs found that DO NOT contain the Global
#           Data Catalog base location are captured to report.
#
"""
import linecache  # required for capture_exception()
import sys  # required for capture_exception()
import os
import re  # required for Regular Expressions - this library is installed with python!
import requests  # required for initiating the call to the API to retrieve the data
import time

# import urllib2    # Apparently urllib2 has been split into urllib.request and urllib.error for python 3.x
import urllib.request  # required for making calls to URLs
import urllib.error  # required for checking the status of the URL calls
import ssl  # required for ssl._create_unverified_context()  - this was needed for the tethys URL verifications.

import logging
# -------------------------------------------
# For debugging / running in the PyCharm IDE... all you have to do is uncomment this logging.basicConfig() call.
# This call just sets up the local logging environment instead of the Django env.
# logging.basicConfig(filename='E:\Code\ServiceCatalogURLs\DebugLog_QueryServiceCatalog.log', level=logging.DEBUG,
#                     format='%(asctime)s: %(levelname)s --- %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
# -------------------------------------------
Logfile = logging.getLogger(__name__)  # "CheckURLs.QueryCatalog"
ServiceCatalogAPI_URL = "https://www.servirglobal.net/ServiceCatalogueBackend/graphql"


class Service(object):

    def __init__(self, _id="", title="", regions=[], serviceareas=[], data=[], tools=[], news=[], trainingmaterials=[]):
        self.ID = _id
        self.Title = title
        self.Regions = regions
        self.ServiceAreas = serviceareas
        self.Data = data
        self.Tools = tools
        self.News = news
        self.TrainingMaterials = trainingmaterials

    def ID(self, _id):
        self.ID = _id

    def Title(self, title):
        self.Title = title

    def Regions(self, regions):
        self.Regions = regions

    def ServiceAreas(self, serviceareas):
        self.ServiceAreas = serviceareas

    def Data(self, data):
        self.Data = data

    def Tools(self, tools):
        self.Tools = tools

    def News(self, news):
        self.News = news

    def TrainingMaterials(self, trainingmaterials):
        self.TrainingMaterials = trainingmaterials


class InvalidEntry(object):

    def __init__(self, status="", region="", servicearea="", title="", identifier="", section="", sectionentry="", url=""):
        self.Status = status
        self.Region = region
        self.ServiceArea = servicearea
        self.Title = title
        self.ID = identifier
        self.Section = section
        self.SectionEntry = sectionentry
        self.URL = url

    def Status(self, status):
        self.Status = status

    def Region(self, region):
        self.Region = region

    def ServiceArea(self, servicearea):
        self.ServiceArea = servicearea

    def Title(self, title):
        self.Title = title

    def ID(self, identifier):
        self.ID = identifier

    def Section(self, section):
        self.Section = section

    def SectionEntry(self, sectionentry):
        self.SectionEntry = sectionentry

    def URL(self, url):
        self.URL = url


# Common function used by many!!
def capture_exception():
    # Not clear on why "exc_type" has to be in this line - but it does...
    exc_type, exc_obj, tb = sys.exc_info()
    frm = tb.tb_frame
    lineno = tb.tb_lineno
    fname = frm.f_code.co_filename
    linecache.checkcache(fname)
    line = linecache.getline(fname, lineno, frm.f_globals)
    s = '### ERROR ### [{}, LINE {} "{}"]: {}'.format(fname, lineno, line.strip(), exc_obj)
    return s


def getScriptPath():
    # Returns the path where this script is running
    return os.path.dirname(os.path.realpath(sys.argv[0]))


def getScriptName():
    # Tries to get the name of the script being executed...  returns "" if not found.
    try:
        # Get the name of this script!
        scriptFullPath = sys.argv[0]
        if len(scriptFullPath) < 1:
            return ""
        else:
            # In case it is the full pathname, split it...
            scriptPath, scriptLongName = os.path.split(scriptFullPath)
            # Split again to separate extension...
            scriptName, scriptExt = os.path.splitext(scriptLongName)
            return scriptName

    except:
        return ""


# Calculate and return time elapsed since input time
def timeElapsed(timeS):
    seconds = time.time() - timeS
    hours = seconds // 3600
    seconds -= 3600*hours
    minutes = seconds // 60
    seconds -= 60*minutes
    if hours == 0 and minutes == 0:
        return "%02d seconds" % seconds
    if hours == 0:
        return "%02d:%02d seconds" % (minutes, seconds)
    return "%02d:%02d:%02d seconds" % (hours, minutes, seconds)


# Get a new time object
def get_NewStart_Time():
    timeStart = time.time()
    return timeStart


# Get the amount of time elapsed from the input time.
def get_Elapsed_Time_As_String(timeInput):
    return timeElapsed(timeInput)


def get_site_status(url):
    """
    # Simply checks the internet to see if the URL passed in is valid and passes back a status and status code.
    #
    #  Python 3.6 version!
    #
    # Issue: Using urllib2.urlopen() with python 2.7 did not give a problem with SSL certificates.  However, with
    # python 3.x, urllib2 was divided up between urllib.request and urllib.error, and they implemented a 'fix' that
    # requires SSL certificate verification on HTTPS calls. Please see https://www.python.org/dev/peps/pep-0476/
    # for more info.  Currently, our tethys server is reporting a 'certificate verify failed' for some reason, so
    # we are implementing the unverified context work-around for "tethys" site links.
    """
    try:
        if "tethys" in url:
            #  The tethys server has a valid certificate, but for some reason is reporting certificate verify failed.
            #  Thus, need to provide an 'unverified' context to bypass certificate authorization.
            context = ssl._create_unverified_context()
            urlfile = urllib.request.urlopen(url, context=context)
        else:
            #  Do not provide context to bypass certificate authorization...
            urlfile = urllib.request.urlopen(url)
    except urllib.error.URLError as e:
        if hasattr(e, 'code'):
            # The server couldn't fulfill the request.
            # NOTE that 403 errors are captured here, but sites are usually able to be accessed anyway. Would
            #  need to put in more logic here to let those pass...  ToDo?
            return 'down', e.code
        elif hasattr(e, 'reason'):
            # We failed to reach a server.
            return 'down', e.reason
    else:
        # everything is fine
        return 'up', urlfile.code


def is_internet_reachable():
    # Checks Google then Yahoo just in case one is down
    statusGoogle, stat_code = get_site_status('http://www.google.com')
    statusYahoo, stat_code = get_site_status('http://www.yahoo.com')
    if statusGoogle == 'down' and statusYahoo == 'down':
        return False
    return True


def GetAllRegions():
    """
    #  Entry point from Django - ServiceCatalogURLs.CheckURLs.views.py
    #  Calls the Service Catalog API to retrieve all regions and passes back a sorted dictionary
    #  of the regions including the Name and the ID.
    """
    try:
        RegionDict = {}

        # Setup the query to use in the API call - All Services!
        PAYLOAD = {
            "operationName": "",
            "variables": {},
            "query": "{"
            "   allRegions(sort: \"\", limit: 10, start: 0, where: \"\") {"
            "       _id"
            "       Name"
            "   }"
            "}"
        }

        # Send the API request and get the result.
        resp = requests.post(ServiceCatalogAPI_URL, json=PAYLOAD)
        json_response = resp.json()

        # Store the regions into a dictionary... use the "Name" as the key so we can lookup later!
        Logfile.info('----- Retrieving All Regions -----')
        tmp = {}
        for region in json_response['data']['allRegions']:
            tmp[region['Name']] = region['_id']

        # Sort the dictionary...
        for key in sorted(tmp):
            Logfile.info('{0}:\t{1}'.format(tmp[key], key))
            RegionDict[key] = tmp[key]

        del tmp
        return RegionDict

    except:
        error = capture_exception()
        Logfile.error(error)


def GetURLs_FromString(theString):
    """
    # Uses a regular expression to parse all matching patterns from the string passed in.
    # Returns a list - either empty or with some items.
    """
    try:
        # Init a return list.
        retList = []

        # Ensure that the string has data...
        if theString is not None and len(theString) > 0:
            # We are dealing with a multi-line text field containing name/value markup that looks like this:
            # "[Some text here](https://www.somesite.com/news/blah/index.html)\n
            # \n
            # [More words here](https://another.net/Articles/invading-kenya-ecosystem)\n
            # \n
            # [Even additional text](https://anysite.net/Data/SomePage)"
            # etc.

            # The following pattern kinda works just scanning the entire string, but it grabs the closing ")"
            # after the URL. So if using this pattern, the last character needs to be removed from
            # any matching strings...
            # url_regex = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!#*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'

            #  New approach...
            #  Since the data in theString is in the markup format, use the name/url combination below to
            #  extract both the Name and URL tags all at once.  Found this example at:
            # https://stackoverflow.com/questions/23394608/python-regex-fails-to-identify-markdown-links
            name_regex = "[^]]+"            # This is the Name portion of the markup tag.
            url_regex = "http[s]?://[^)]+"  # This is the URL portion of the markup tag.
            #  Put together to build the full regex pattern...
            markup_regex = '\[({0})]\(\s*({1})\s*\)'.format(name_regex, url_regex)

            matches = re.findall(markup_regex, theString)
            for match in matches:
                # Create an inner list to contain the Name and URL to be added to the return list.
                # retList will be a nested list like: [[Name1, URL1], [Name2, URL2], [Name3, URL3], ...]
                innerList = [match[0], match[1]]

                # Add the inner list to the list to be returned.
                # retList.append(match[1])
                retList.append(innerList)

        return retList

    except:
        error = capture_exception()
        Logfile.error(error)
        return retList


def ProcessURLs(svc_cls, svcCategory, URLs, Dict_AlreadyChecked, List_ErrURLs, List_ErrCatalogs):
    """
    # Loops through the list of URLs passed in and calls a function to verify the site is valid.
    # It first checks to see if each URL has already been processed (via the dictionary passed in).
    # If the URL(key) already exists in the dictionary, the status(value) of either "up" or "down" is used to report.
    # If the URL is not in the dictionary, get_site_status() is called and the dictionary is updated respectively.
    #
    #  The 1 Dictionary and 2 Lists passed in are also returned back to the calling function as this function may
    #  modify the contents of those objects.
    """
    try:
        # Loop through the URLs and report on each one.
        for lnkName, lnk in URLs:

            # First, check to see if the URL has already been checked... there will be duplicates.
            if lnk in Dict_AlreadyChecked:
                # The URL has already been checked and reported.
                # If "down", go ahead and report it again...
                if Dict_AlreadyChecked[lnk] == "down":
                    # Init a new errEntry class, populate it, and add it to the List of Err URLs.
                    errEntry = InvalidEntry()

                    errEntry.Status = "DUPLICATE"
                    errEntry.Region = svc_cls.Regions[0]['Name']
                    errEntry.ServiceArea = svc_cls.ServiceAreas[0]['Name']
                    errEntry.Title = svc_cls.Title.replace(",", " ")
                    errEntry.ID = svc_cls.ID
                    errEntry.Section = svcCategory
                    errEntry.SectionEntry = lnkName.replace(",", " ")
                    errEntry.URL = lnk

                    List_ErrURLs.append(errEntry)
                    Logfile.error("### DUPLICATE! ### ===> ({0}) {1}\tpreviously verified as down!".format(errEntry.Section,
                                                                                                        errEntry.URL))
                else:
                    Logfile.debug("\t\t\t{0}\t (previously checked)".format(lnk))

            else:
                try:
                    status, stat_code = get_site_status(lnk)
                except:
                    # Log the error and keep going!
                    error = capture_exception()
                    Logfile.error(error)
                    status = "down"  # This statement required if get_site_status() errors.
                    stat_code = "Connection Error"  # This statement required if get_site_status() errors.

                # Careful - This if is not part of the except clause...
                if status != "up":
                    # Init a new errEntry class, populate it, and add it to the List of Err URLs.
                    errEntry = InvalidEntry()

                    errEntry.Status = str(stat_code).replace(",", " ")
                    errEntry.Region = svc_cls.Regions[0]['Name']
                    errEntry.ServiceArea = svc_cls.ServiceAreas[0]['Name']
                    errEntry.Title = svc_cls.Title.replace(",", " ")
                    errEntry.ID = svc_cls.ID
                    errEntry.Section = svcCategory
                    errEntry.SectionEntry = lnkName.replace(",", " ")
                    errEntry.URL = lnk

                    List_ErrURLs.append(errEntry)
                    Logfile.error("### Oops! ### Code {0} ===> ({1}) {2} is down!".format(errEntry.Status,
                                                                                          errEntry.Section,
                                                                                          errEntry.URL))
                    #  Capture the status of the URL in a dictionary
                    Dict_AlreadyChecked[lnk] = "down"
                else:
                    Logfile.debug("\t\t\t{0}".format(lnk))
                    #  Capture the status of the URL in a dictionary
                    Dict_AlreadyChecked[lnk] = "up"

            # LATE ENHANCEMENT - PER REQUEST OF THE SUPPORT TEAM
            # For URLs from the "Data" Service Category section, whether it is 'up' or 'down', check to see if the URL
            # contains the "gis1.servirglobal.net" string to ensure that the entry is pointing at the Global SERVIR
            # Data Catalog.  If not, report it to the Data_SourceReport log file.
            if "DATA" in svcCategory.upper():
                if "gis1.servirglobal.net" not in lnk.lower():
                    # Init a new errEntry class, populate it, and add it to the List of Err Catalogs.
                    errEntry = InvalidEntry()

                    errEntry.Status = "INCORRECT CATALOG"
                    errEntry.Region = svc_cls.Regions[0]['Name']
                    errEntry.ServiceArea = svc_cls.ServiceAreas[0]['Name']
                    errEntry.Title = svc_cls.Title.replace(",", " ")
                    errEntry.ID = svc_cls.ID
                    errEntry.Section = svcCategory
                    errEntry.SectionEntry = lnkName.replace(",", " ")
                    errEntry.URL = lnk

                    List_ErrCatalogs.append(errEntry)

        return Dict_AlreadyChecked, List_ErrURLs, List_ErrCatalogs

    except:
        error = capture_exception()
        Logfile.error(error)


def QueryServiceCatalog(region_id):
    """
    #  Entry point from Django - ServiceCatalogURLs.CheckURLs.views.py
    #  Calls the Service Catalog API with the Region passed in to retrieve all related Services and associated
    #  Tools, Data, News, and Training Materials links. It then checks each URL and returns a List of ErrURLs to
    #  the calling function. It also checks "Data" URLs to see if they contain "gis1.servirglobal.net". If not,
    #  those entries are added to the List of ErrCatalogs, which is also returned.
    """
    try:
        # Setup the logging.  args.logging will either be passed in as an optinal argument by the user,
        # or will assume the default as specified in setupArgs().
        Logfile.info('------------------------- Processing Starting -------------------------')

        # Get a start time for the entire script run process.
        time_TotalScriptRun = get_NewStart_Time()

        # Make sure we can see the internet!
        if not is_internet_reachable():
            Logfile.error("Internet is not accessible.")
            Logfile.info('------------------------- Processing Halted -------------------------')
            sys.exit()

        # Sample query to use in the API call for All Services!
        # PAYLOAD = {
        #     "operationName": "",
        #     "variables": {},
        #     "query": "{"
        #     "   services: searchServices(regions: [], countries: [], serviceAreas: [], status: [], dataSources: [], freeText: \"\") {"
        #     "       _id"
        #     "       Title"
        #     "       regions {"
        #     "           _id"
        #     "           Name"
        #     "       }"
        #     "       serviceareas {"
        #     "           _id"
        #     "           Name"
        #     "       }"
        #     "       Data"
        #     "       Tools"
        #     "       News"
        #     "       TrainingMaterials"
        #     "   }"
        #     "}"
        # }

        # Lets build the API query in parts so that we can insert the region passed in, if specified.
        # Build the Query portion of the API call using the Region passed in.
        firstPart = "{   services: searchServices(regions: ["
        if len(region_id) > 0:
            middlePart = "\"" + region_id + "\""
        else:
            middlePart = ""
        lastPart = "], countries: [], serviceAreas: [], status: [], dataSources: [], freeText: \"\") {" \
                   "       _id" \
                   "       Title" \
                   "       regions {" \
                   "           _id" \
                   "           Name" \
                   "       }" \
                   "       serviceareas {" \
                   "           _id" \
                   "           Name" \
                   "       }" \
                   "       Data" \
                   "       Tools" \
                   "       News" \
                   "       TrainingMaterials" \
                   "   }" \
                   "}"

        PAYLOAD = {
            "operationName": "",
            "variables": {},
            "query": firstPart + middlePart + lastPart
        }
        # Debug!!!
        # print(" --- ")
        # print(firstPart + middlePart + lastPart)
        # print(" --- ")

        # For testing purposes... Get only services from a particular Region!
        # "5bb3f96f51ebdcae796832e6" = Eastern/Southern Africa
        # "5bb3f96951ebdcae796832e5" = West Africa
        # "5bb3f97b51ebdcae796832e9" = Mekong
        # "5bb3f97451ebdcae796832e7" = Himalaya
        # PAYLOAD = {
        #     "operationName": "",
        #     "variables": {},
        #     "query": "{"
        #     "   services: searchServices(regions: [\"5bb3f97b51ebdcae796832e9\"], countries: [], serviceAreas: [], status: [], dataSources: [], freeText: \"\") {"
        #     "       _id"
        #     "       Title"
        #     "       regions {"
        #     "           _id"
        #     "           Name"
        #     "       }"
        #     "       serviceareas {"
        #     "           _id"
        #     "           Name"
        #     "       }"
        #     "       Data"
        #     "       Tools"
        #     "       News"
        #     "       TrainingMaterials"
        #     "   }"
        #     "}"
        # }

        # Send the API request and get the result.
        # args.api will either contain the URL passed in as an optional argument, or if not specified, it will contain
        # the default value as specified in setupArgs().
        r = requests.post(ServiceCatalogAPI_URL, json=PAYLOAD)
        json_data = r.json()

        Logfile.info("{0} services retrieved from Service Catalog API.".format(len(json_data['data']['services'])))

        # Not great to loop through services twice, but wanted to grab each service into a class and build
        # a list of class objects so that I know what I'm working with later...
        Services_List = []
        for service in json_data['data']['services']:
            svc = Service()
            svc.ID = service['_id']
            svc.Title = service['Title']
            svc.Regions = service['regions']
            svc.ServiceAreas = service['serviceareas']
            svc.Data = service['Data']
            svc.Tools = service['Tools']
            svc.News = service['News']
            svc.TrainingMaterials = service['TrainingMaterials']
            # Add the class to the list of services.
            Services_List.append(svc)

        # Process each Service
        # #######################
        URL_Dict = {}
        ErrURLs_List = []
        ErrCatalogs_List = []
        for svc in Services_List:
            Logfile.info("Service: {0}".format(svc.Title))

            # Process Data
            # #######################
            DataURLs = GetURLs_FromString(svc.Data)
            Logfile.debug("\t\tData:\t({0} total)".format(len(DataURLs)))
            URL_Dict, ErrURLs_List, ErrCatalogs_List = ProcessURLs(svc, "DATA", DataURLs,
                                                                   URL_Dict, ErrURLs_List, ErrCatalogs_List)

            # Process Tools
            # #######################
            ToolsURLs = GetURLs_FromString(svc.Tools)
            Logfile.debug("\t\tTools:\t({0} total)".format(len(ToolsURLs)))
            URL_Dict, ErrURLs_List, ErrCatalogs_List = ProcessURLs(svc, "TOOLS", ToolsURLs,
                                                                   URL_Dict, ErrURLs_List, ErrCatalogs_List)

            # Process News
            # #######################
            NewsURLs = GetURLs_FromString(svc.News)
            Logfile.debug("\t\tNews:\t({0} total)".format(len(NewsURLs)))
            URL_Dict, ErrURLs_List, ErrCatalogs_List = ProcessURLs(svc, "NEWS", NewsURLs,
                                                                   URL_Dict, ErrURLs_List, ErrCatalogs_List)

            # Process Training Materials
            # #######################
            TrainingMaterialsURLs = GetURLs_FromString(svc.TrainingMaterials)
            Logfile.debug("\t\tTraining Materials:\t({0} total)".format(len(TrainingMaterialsURLs)))
            URL_Dict, ErrURLs_List, ErrCatalogs_List = ProcessURLs(svc, "TRAINING MATERIALS", TrainingMaterialsURLs,
                                                                   URL_Dict, ErrURLs_List, ErrCatalogs_List)

        # In case there were no error URLs or Invalid Catalog entries found, insert a dummy placeholder entry.
        # This should be done in the calling function, but for now...
        dummyEntry = InvalidEntry()
        dummyEntry.Status = "No Data to Report"
        if len(ErrURLs_List) < 1:
            ErrURLs_List.append(dummyEntry)
        if len(ErrCatalogs_List) < 1:
            ErrCatalogs_List.append(dummyEntry)

        # Report the URL totals.
        Logfile.info("=== TOTAL URLs CHECKED ===>: {0}".format(len(URL_Dict)))
        numDown = sum(value == "down" for value in URL_Dict.values())
        Logfile.info("=== NUMBER OF THOSE URLs 'DOWN' ===>: {0}  (not including DUPLICATES)".format(numDown))

        #  Cleanup objects when done...
        del URL_Dict
        del Services_List

        return ErrURLs_List, ErrCatalogs_List

    except:
        err = capture_exception()
        Logfile.error(err)

    finally:
        Logfile.info("=== TOTAL RUN TIME ===>: " +
                         get_Elapsed_Time_As_String(time_TotalScriptRun))
        Logfile.info('------------------------- Processing Complete -------------------------')


def QueryServiceCatalog_DummyTestReturn(region_id):
    """
    #  This function is a simple test to mimic the return values from the actual QueryServiceCatalog() function.
    #  It simply populates some dummy data into the expected return objects and passes them back.
    #  Use this to test passing some dummy data back to the Django app.
    """

    Logfile.info('------------------------- Processing Starting -------------------------')
    # ##### INVALID URL ENTRIES #####
    tstURLs_List = []

    tstEntry1 = InvalidEntry()
    tstEntry1.Status = "403"
    tstEntry1.Region = "Eastern & Southern Africa"
    tstEntry1.ServiceArea = "Water and Water Related Disasters"
    tstEntry1.Title = "Climate Change Vulnerability Impacts and Assessments Service"
    tstEntry1.ID = "5bd049af51ebdcae7968336f"
    tstEntry1.Section = "TOOLS"
    tstEntry1.SectionEntry = "Tool Entry 1"
    tstEntry1.URL = "https://www.businessdailyafrica.com/news/Pastoralists-go-digital/539546-4544716-f7nany/index.html"
    Logfile.debug("Adding entry to tstURLs_List - Service: {0}".format(tstEntry1.Title))
    tstURLs_List.append(tstEntry1)

    tstEntry2 = InvalidEntry()
    statCode = "[WinError 10060] A connection attempt failed because the connected party did not properly " \
               "respond after a period of time, or established connection failed because connected host " \
               "has failed to respond"
    tstEntry2.Status = statCode.replace(",", " ")
    tstEntry2.Region = "Hindu Kush Himalaya"
    tstEntry2.ServiceArea = "Land Use Land Cover"
    tstEntry2.Title = "Regional Drought Monitoring and Early Warning System"
    tstEntry2.ID = "5bc8936451ebdcae7968335e"
    tstEntry2.Section = "TRAINING MATERIALS"
    tstEntry2.SectionEntry = "Training Materials Entry 1"
    tstEntry2.URL = "https://www.geospatialworld.net/news/kenyas-first-national-crop-monitor-set-to-strengthen-food-security/"
    Logfile.debug("Adding entry to tstURLs_List - Service: {0}".format(tstEntry2.Title))
    tstURLs_List.append(tstEntry2)

    tstEntry3 = InvalidEntry()
    tstEntry3.Status = "404"
    tstEntry3.Region = "Mekong"
    tstEntry3.ServiceArea = "Food Security and Agriculture"
    tstEntry3.Title = "Improving the Mekong River Commission's Regional Flood Forecasting"
    tstEntry3.ID = "5c3479a79ff7d708e49cc976"
    tstEntry3.Section = "NEWS"
    tstEntry3.SectionEntry = "News Entry 1"
    tstEntry3.URL = "https://www.ghanabusinessnews.com/2018/09/19/smallholder-charcoal-producers-call-for-review-of-regulations/"
    Logfile.debug("Adding entry to tstURLs_List - Service: {0}".format(tstEntry3.Title))
    tstURLs_List.append(tstEntry3)

    tstEntry4 = InvalidEntry()
    tstEntry4.Status = "DUPLICATE"
    tstEntry4.Region = "West Africa"
    tstEntry4.ServiceArea = "Weather and Climate"
    tstEntry4.Title = "Charcoal Production Site Monitoring Service for West Gonja and Sene Districts in Ghana"
    tstEntry4.ID = "5bcf240a51ebdcae79683366"
    tstEntry4.Section = "DATA"
    tstEntry4.SectionEntry = "Data Entry 1"
    tstEntry4.URL = "https://www.ghanabusinessnews.com/2018/09/19/smallholder-charcoal-producers-call-for-review-of-regulations/"
    Logfile.debug("Adding entry to tstURLs_List - Service: {0}".format(tstEntry4.Title))
    tstURLs_List.append(tstEntry4)

    # ##### ERRANT CATALOG ENTRIES #####
    tstCatalogs_List = []

    catalogEntry1 = InvalidEntry()
    catalogEntry1.Status = "INCORRECT CATALOG"
    catalogEntry1.Region = "Mekong"
    catalogEntry1.ServiceArea = "Food Security and Agriculture"
    catalogEntry1.Title = "This is a very Bad Example of a Service Title"
    catalogEntry1.ID = "5bd052d451ebdcae79683375"
    catalogEntry1.Section = "DATA"
    catalogEntry1.SectionEntry = "Data Entry 1"
    catalogEntry1.URL = "https://somesite.otherthan_gis1.servirglobal.net/..."
    Logfile.debug("Adding entry to tstURLs_List - Service: {0}".format(catalogEntry1.Title))
    tstCatalogs_List.append(catalogEntry1)

    # In case there were no error URLs or Invalid Catalog entries found, insert a dummy placeholder entry.
    dummyEntry = InvalidEntry()
    dummyEntry.Status = "No Data to Report"
    if len(tstURLs_List) < 1:
        Logfile.debug("Adding DUMMY entry to: tstURLs_List")
        tstURLs_List.append(dummyEntry)
    if len(tstCatalogs_List) < 1:
        Logfile.debug("Adding DUMMY entry to: tstCatalogs_List")
        tstCatalogs_List.append(dummyEntry)

    Logfile.info('------------------------- Processing Complete -------------------------')

    return tstURLs_List, tstCatalogs_List


# For debugging / running in the PyCharm IDE...
# Note - This is not called when running in the Django environment.
if __name__ == "__main__":
    # "5bb3f96f51ebdcae796832e6" = Eastern/Southern Africa
    # "5bb3f96951ebdcae796832e5" = West Africa
    # "5bb3f97b51ebdcae796832e9" = Mekong
    # "5bb3f97451ebdcae796832e7" = Himalaya
    InvalidURLs_List, InvalidCatalogs_List = QueryServiceCatalog_DummyTestReturn("5bb3f96951ebdcae796832e5")
    # InvalidURLs_List, InvalidCatalogs_List = QueryServiceCatalog("5bb3f96951ebdcae796832e5")

    for item in InvalidURLs_List:
        Logfile.info("------------ Invalid URL ----------------------")
        Logfile.info("{0}".format(item.Status))
        Logfile.info("{0}".format(item.Region))
        Logfile.info("{0}".format(item.ServiceArea))
        Logfile.info("{0}".format(item.Title))
        Logfile.info("{0}".format(item.ID))
        Logfile.info("{0}".format(item.Section))
        Logfile.info("{0}".format(item.SectionEntry))
        Logfile.info("{0}".format(item.URL))

    for entry in InvalidCatalogs_List:
        Logfile.info("------------ Invalid Catalog ----------------------")
        Logfile.info("{0}".format(entry.Status))
        Logfile.info("{0}".format(entry.Region))
        Logfile.info("{0}".format(entry.ServiceArea))
        Logfile.info("{0}".format(entry.Title))
        Logfile.info("{0}".format(entry.ID))
        Logfile.info("{0}".format(entry.Section))
        Logfile.info("{0}".format(entry.SectionEntry))
        Logfile.info("{0}".format(entry.URL))


# if __name__ == "__main__":
#     # Try different strings to make sure GetURLs_FromString() can handle different scenarios...
#     Tools = "[Enhancing Eastern and Southern Africa climate services by increasing access to remote sensing and model datasets](https://earlywarning.usgs.gov/fews/ewx/index.html)\n\n[ClimateSERV](https://climateserv.servirglobal.net/)\n\n[Hazard and Disaster Risk Identification and Mapping System in Malawi](http://tools.rcmrd.org/vulnerabilitytool/)\n\nWeb-based GIS Water Resource Management System - Wajir County, Kenya\n"
#     # Tools = "[Enhancing Eastern and Southern Africa climate services by increasing access to remote sensing and model datasets](https://earlywarning.usgs.gov/fews/ewx/index.html)\n\n[ClimateSERV](https://climateserv.servirglobal.net/)\n\n[Hazard and Disaster Risk Identification and Mapping System in Malawi](http://tools.rcmrd.org/vulnerabilitytool/)\n\n[Web-based GIS Water Resource Management System - Wajir County, Kenya]()\n"
#     # Tools = "[Enhancing Eastern and Southern Africa climate services by increasing access to remote sensing and model datasets](https://earlywarning.usgs.gov/fews/ewx/index.html)\n\n[ClimateSERV](https://climateserv.servirglobal.net/)\n\n[Hazard and Disaster Risk Identification and Mapping System in Malawi](http://tools.rcmrd.org/vulnerabilitytool/)\n\n[Web-based GIS Water Resource Management System - Wajir County, Kenya]\n"
#     # Tools = "[Enhancing Eastern and Southern Africa climate services by increasing access to remote sensing and model datasets](https://earlywarning.usgs.gov/fews/ewx/index.html)\n\n[ClimateSERV](https://climateserv.servirglobal.net/)\n\n[Hazard and Disaster Risk Identification and Mapping System in Malawi](http://tools.rcmrd.org/vulnerabilitytool/)\n\n[Web-based GIS Water Resource Management System - Wajir County, Kenya](https://www.someval.com/)\n"
#     URLs = GetURLs_FromString(Tools)
#     for lnkName, lnk in URLs:
#         print("Found {0}".format(lnkName))
