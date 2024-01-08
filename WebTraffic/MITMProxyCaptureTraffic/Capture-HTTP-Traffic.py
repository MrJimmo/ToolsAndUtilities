'''
~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^
MIT License

Copyright (c) 2024 Jim Moore

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^


This is a MITMProxy addon that saves requests and responses to local storage.

MITMProxy reference:
https://docs.mitmproxy.org/stable/addons-overview/

This script defines/implements the CaptureHTTPTraffic class that saves HTTP
Requests and Responses, to local storage.

Key features:
    - Saves all content from a given browser based on the User-Agent string

    - If present, it uses a unique ID provided by the User-Agent string in the
      http request to name the directory where traffic will be stored.

      See the getGetUserAgentID() method for more info.
      This 'feature' allows capturing and grouping traffic for a given browser.

    - Headers are included in the output, one per line as a NAME:VALUE pair.

Command line options consumed by this addon:
    capture_enabled:
        - Allows specifying True == Capture, False == No capture

    capture_save_location:
        - Allows specifying a new root of save location.

    capture_logging_enabled:
        - Allows specifying True == Logging, False == No logging
        (I added a ton of logging because this is my first MITMProxy addon.)

    These options appear in the MITMProxy or MITMWeb options list.

Example:
mitmweb -s Capture-HTTP-Traffic.py
    --set capture_save_location="./NotDefaultCaptureLocation"
    --set capture_enabled=false
    --set capture_logging_enabled=true

    This will start MITMWeb with this add-on NOT initially capturing/saving
    HTTP request/responses but logging is enabled.  If user enables capturing
    in MITMWeb Options UI, it will then start saving the traffic to a directory
    named "NotDefaultCaptureLocation", relative to where the script is being
    loaded from.

NOTE:
Currently, the content is saved in very basic manner and (mostly) NOT
re-playable if copy/pasted into various HTTP traffic tools (Burp Suite, Fiddler,
etc.)  Support for that TBD.

Basic Class Structure:
    load()
    configure()
    request()/response()
        handleFlow()
            getGetUserAgentID()
                generateSHA1HashOfString()
            generateFileNameFromURL()
                generateSHA1HashOfString()
            saveFlowToFile()
                getHeadersAsString()
'''
import logging
import hashlib
import os
import datetime
import re

from mitmproxy import ctx

class CaptureHTTPTraffic:
    def __init__(self):
        '''
        capture_enabled:

        Allows toggling on/off the saving of contents.
        Default is True.
        '''
        self.capture_enabled = True

        '''
        root_save_location:

        This is relative to where the script is being loaded from.
        and will be used as part of where files are to be saved.

        Default is  "./captures" and filenames will look like
        "./captures/<[unknown_<UASTRING_HASH>|CID]/<FORMATTED_URL>_[req|res].txt
        '''
        self.root_save_location = "./captures"

        '''
        capture_logging_enabled:

        When enabled, the output of all the outputString calls will go to
        MITMProxy logging.info.
        Useful mainly when developing this Add-on, so default is False.
        '''
        self.capture_logging_enabled = False

        self.outputString("[CaptureHTTPTraffic::__init__] Initializing")

    '''
    Save the the string (strText) to the given File (strFilename).
    Default is to append to file if it exists.

    Also uses self.root_save_location as the root for the files.
    '''
    def saveToFile(self, strText, pathAndFilename, append=True):
        path     = os.path.dirname(pathAndFilename)
        filename = os.path.basename(pathAndFilename)

        # Create the path if it doesn't exist.
        if not os.path.exists(path):
            os.makedirs(path)
        outputdir_filename = "{0}/{1}".format(path, filename)
       
        if append:
            filemode = "ab"
        else:
            filemode = "wb"

        with open(outputdir_filename, filemode) as f:
            f.write(strText)

    '''
    Get the ID from the User Agent String
    If no "cid=" in the UA String, hash full value and return
    "unknown_<HASH>"

    Example:
    User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
        cid=736d6172-7479-7061-6e74-7321213a2d50
        (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36

    This will pull out the GUID: 736d6172-7479-7061-6e74-7321213a2d50
    And and return that.

    If the "cid" part was missing:
        Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
            (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36

    That value would be hashed with SHA1 and returned as:
        "unknown_1a8baea2c9405c9a25c8ef6667534ef1aec47d58"
    '''
    def getGetUserAgentID(self, uaString):
        rx_cid_pattern = 'cid=(?P<CID>.*?)\s'
        cid = re.search(rx_cid_pattern, uaString)
        id = ""
        if cid is not None:
            id = cid.group('CID')
        else:
            id = "unknown_{0}".format(self.generateSHA1HashOfString(uaString))

        self.outputString(
            "[CaptureHTTPTraffic::getUserAgentID] User Agent: {0}".format(id))

        return id

    '''
    Generate a filename based on the URL
    If URL contains "?" search/query string, that part is just hashed and
    added to the filename.

    All ":", "/", and "." parts are replaced with underscores

    Examples:
    URL     : https://example.com
    Filename: https___example_com_

    URL     :"http://www.bing.com/search?q=mitmproxy+adoon+documentation"
    Filename:
        http___www_bing_com_search_8b35844dcfa1ab0a26ec88d9b434dcc8cabb7bfc
    The "?" is replaced with "_", and "?q=mitmproxy+adoon+documentation" is what
    gets hashed.

    The caller will append the "req" or "res" depending on Request or Response.
    '''
    def generateFileNameFromURL(self, strUrl):
        generated_filename = ""
        try:
            urlParts = strUrl.split('?')
        except ValueError as ve:
            (self.outputString("[CaptureHTTPTraffic::generateFileNameFromURL] "
                "Failed to split URL.")
            )
            (self.outputString("[CaptureHTTPTraffic::generateFileNameFromURL] "
                "{0}.".format(ve))
            )
            return generated_filename

        filename = urlParts[0]
        for ch in [':','/','.']:
            filename = filename.replace(ch,'_')

        (self.outputString("[CaptureHTTPTraffic::generateFileNameFromURL] "
            "urlParts[0]: {0}".format(urlParts[0]))
        )
        hash = ""

        if (len(urlParts) > 1): 
            (self.outputString("[CaptureHTTPTraffic::generateFileNameFromURL] " 
                "urlParts[1]: {0}".format(urlParts[1]))
            )
            hash = self.generateSHA1HashOfString(urlParts[1])

        generated_filename = "{0}".format( filename + '_' + hash )

        return generated_filename

    '''
    Generate the SHA1 Hash of the given string
    '''
    def generateSHA1HashOfString(self, string):
        hlib = hashlib.sha1()
        hlib.update(string.encode(encoding = 'UTF-8'))
        return hlib.hexdigest()

    '''
    Called for both Request and Response flows, this method returns the headers
    as a string block that will be added to the output file.
    Typical <HEADER>:<SP><VALUE>, one per line formatting used.
    Caller is responsible for adding any necessary trailing spaces.
    '''
    def getHeadersAsString(self, reqres):
        output = ""
        try:
            for k,v in reqres.headers.items():
                output += "{0}: {1}\n".format(k, v)
        except Exception as ex:
            (self.outputString("[CaptureHTTPTraffic::getHeadersAsString] "
                "Exception: {0}".format(ex))
            )
        return output

    '''
    This method saves the given flow to a file.

    The isRequest param controls the saving of headers and content based on
    whether this is for a Request (isRequest == true) or Response (isRequest ==
    false)

    The first line of the file will contain one line specifying time/date saved
    and the URL visited:
    "[Saved:2024-01-03 23:49:44.221628 URL:http://google.com/]"

    This could easily be stripped if needed for replay.

    For Requests, the second line is the typical METHOD, URL, HTTP Version:
    "GET http://google.com/ HTTP/1.1"

    For Responses, the second line is the typical HTTP Version, Status code,
    and Reason.
    "HTTP/1.1 200 OK"

    The the list of Headers and their values follow, one per line
    content-length: 9940
    content-type: application/json; charset=utf-8
    ...etc

    2 blank lines, and then the body (if present) fills out the rest of the
    file.

    '''
    def saveFlowToFile(self, flow, filename, isRequest = True):
        header = "[Saved:{0} URL:{1}]\n".format(datetime.datetime.now(),
            flow.request.url)
        self.saveToFile(str.encode(header), filename, False)
        if isRequest == True:
            method_url = "{0} {1} {2}\n".format(flow.request.method,
                flow.request.url, flow.request.http_version)
            headers_as_string = self.getHeadersAsString(flow.request)
            self.saveToFile(str.encode(method_url), filename)
            self.saveToFile(str.encode(headers_as_string), filename)
            self.saveToFile(str.encode("\n\n"), filename)
            self.saveToFile(flow.request.content, filename)
        else:
            request_response = "{0} {1} {2}\n".format(
                flow.response.http_version, flow.response.status_code,
                flow.response.reason)
            headers_as_string = self.getHeadersAsString(flow.response)
            self.saveToFile(str.encode(request_response), filename)
            self.saveToFile(str.encode(headers_as_string), filename)
            self.saveToFile(str.encode("\n\n"), filename)
            self.saveToFile(flow.response.content, filename)

    '''
    This function handles both Request and Response flows.

    It creates the filename to use for saving the flow, by calling the
    generateFileNameFromURL() method.
    '''
    def handleFlow(self, flow, isRequest = True):
        if (self.capture_enabled == False):
            return
        user_agent   = flow.request.headers['User-Agent']
        useragent_id = self.getGetUserAgentID(user_agent)
        file_suffix  = "req.txt"

        if isRequest is not True:
            file_suffix = "res.txt"

        if useragent_id is not None:
            reqUrl   = "{0}".format(flow.request.url)
            save_dir = "{0}/{1}".format(self.root_save_location, useragent_id)
            filename = "{0}/{1}_{2}".format(save_dir,
                self.generateFileNameFromURL(reqUrl), file_suffix)
            (self.outputString("[CaptureHTTPTraffic] Request Filename: {0}"
                .format(filename))
            )
            self.saveFlowToFile(flow, filename, isRequest)
        else:
            (self.outputString("[CaptureHTTPTraffic::handleFlow] **** Failed "
                "to get useragent ID from: {0}".format(user_agent))
            )

    '''
    This function is called from configure(), to show key settings for this
    add-on in the MITMProxy/Web output log.
    '''
    def showSettings(self):
        self.outputString("[CaptureHTTPTraffic] Settings:\n")
        (self.outputString("    [capture_save_location]   = {0}"
            .format(ctx.options.capture_save_location))
        )
        (self.outputString("    [self.root_save_location] = {0}"
            .format(self.root_save_location))
        )
        (self.outputString("    [capture_enabled]         = {0}"
            .format(self.capture_enabled))
        )
        (self.outputString("    [capture_logging_enabled] = {0}"
            .format(self.capture_logging_enabled))
        )

    '''
    Simple function to wrap logging.info
    '''
    def outputString(self, string):
        if (self.capture_logging_enabled):
            logging.info(string)

    '''
    MITMProxy Addon HTTP Request Handler
    https://docs.mitmproxy.org/stable/api/events.html#HTTPEvents.request
    '''
    def request(self, flow):
        self.handleFlow(flow)

    '''
    MITMProxy Addon HTTP Response Handler
    https://docs.mitmproxy.org/stable/api/events.html#HTTPEvents.response
    '''
    def response(self, flow):
        self.handleFlow(flow, False)

    '''
    MITMProxy Addon configure event handler
    https://docs.mitmproxy.org/stable/api/events.html#LifecycleEvents.configure
    '''
    def configure(self, updates):
        self.outputString("[CaptureHTTPTraffic::configure]")
        if "capture_enabled" in updates:
            self.capture_enabled = ctx.options.capture_enabled

        if "capture_save_location" in updates:
            self.root_save_location = ctx.options.capture_save_location

        if "capture_logging_enabled" in updates:
            self.capture_logging_enabled = ctx.options.capture_logging_enabled
        
        self.showSettings()

    '''
    MITMProxy Addon load event handler
    https://docs.mitmproxy.org/stable/api/events.html#LifecycleEvents.load
    '''
    def load(self, loader):
        self.outputString("[CaptureHTTPTraffic] Class loaded")

        loader.add_option(
            name="capture_enabled",
            typespec=bool,
            default=True,
            help=("Flag indicating capture status. True == Capturing, "
                "False == not Capturing"),
        )

        loader.add_option(
            name="capture_save_location",
            typespec=str,
            default=self.root_save_location,
            help="Root location where HTTP Reqs/Resp will be saved",
        )

        loader.add_option(
            name="capture_logging_enabled",
            typespec=bool,
            default=False,
            help="True == logging enabled.  False == no logging.",
        )

# Get the ball rolling...
addons = [CaptureHTTPTraffic()]

