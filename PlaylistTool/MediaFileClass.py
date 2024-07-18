'''
MediaFileClass

Simple class representing an individual media file entry in the Windows Media
Playlist

Some Reference:
https://en.wikipedia.org/wiki/Windows_Media_Player_Playlist

Note about columns:
It's not always known what columns the OS supports or are available, so the
following print() statement can be used in the get_list_of_metadata_columns()
function, to print the columns:

    print("COLUMNS:\n{0}".format(MediaFileClass._columns))

Example columns from Win10 machine...

COLUMNS:
['Name', 'Size', 'Item type', 'Date modified', 'Date created', 'Date accessed',
'Attributes', 'Offline status', 'Availability', 'Perceived type', 'Owner',
'Kind', 'Date taken', 'Contributing artists', 'Album', 'Year', 'Genre',
'Conductors', 'Tags', 'Rating', 'Authors', 'Title', 'Subject', 'Categories',
'Comments', 'Copyright', '#', 'Length', 'Bit rate', 'Protected', 'Camera model',
'Dimensions', 'Camera maker', 'Company', 'File description', 'Masters keywords',
'Masters keywords']
'''

import os
import win32com.client
from bs4.formatter import HTMLFormatter
import re

'''
Simple class to retain attribute ordering

From:
https://www.crummy.com/software/BeautifulSoup/bs4/doc/#writing-your-own-formatter
'''
class UnsortedAttributes(HTMLFormatter):
    def attributes(self, tag):
        for k, v in tag.attrs.items():
            yield k, v

class MediaFileClass:

    # Static class properties
    _columns            = []   # Static param shared across instances
    _length_col_index   = -1   # Index of the "Length" column.
    _bit_rate_col_index = -1   # Index of the "Bit Rate" column.
    _sh                 = None # Shell.Application
    _index              = 0    # Each instance will get assigned _index++

    # Constructor
    def __init__(self, media_entry):
        self.file_size     = -1 # -1 == unknown size.
        self.length        = ""
        self.lengthMS      = 0
        self.bit_rate      = ""
        self.cid           = ""
        self.tid           = ""
        self.media_elem    = media_entry
        self.file_name     = self.media_elem['src']
        self.bucket_number = -1 # -1 means not part of a bucket

        if (self.media_elem.has_attr('cid')):
            self.cid  = media_entry['cid']

        if (self.media_elem.has_attr('tid')):
            self.tid = media_entry['tid']

        # Original position in the playlist.
        self.originalOrder = MediaFileClass._index
        MediaFileClass._index += 1

        MediaFileClass._sh = win32com.client.gencache.EnsureDispatch(
            'Shell.Application', 0)

        # If list of columns not yet created, do it now...
        if (len(MediaFileClass._columns)==0):
            self.get_list_of_metadata_columns()

        # verify the file exists, before trying to get any of the other details
        if (os.path.isfile(self.file_name)):
            self.get_file_size()
            self.get_media_file_extra_details()
        else:
            print("Bad file Found: {0}  Size:{1}".
                  format(self.file_name, self.file_size))

    '''
    This function generates the full list of available file attribute columns.

    Based on an answer from:
    https://stackoverflow.com/questions/12521525/reading-metadata-with-python
    '''
    def get_list_of_metadata_columns(self):

        dir_name  = os.path.dirname(os.path.abspath(__name__))

        ns = MediaFileClass._sh.NameSpace(os.path.abspath(dir_name))

        colnum = 0
        while True:
            colname = ns.GetDetailsOf(colnum, colnum)

            # Indicates end of list
            if not colname:
                break

            MediaFileClass._columns.append(colname)

            # Grab index values for from these specific columns, they will be
            # used in a later call to GetDetailsOf()
            if (colname == "Length"):
                MediaFileClass._length_col_index = colnum
            elif (colname == "Bit rate"):
                MediaFileClass._bit_rate_col_index = colnum

            colnum += 1

    '''
    This function gets details from specific columns that were found during the
    previous call to get_list_of_metadata_columns()
    '''
    def get_media_file_extra_details(self):
        dir_name  = os.path.dirname(self.file_name)
        base_name = os.path.basename(self.file_name)

        ns   = MediaFileClass._sh.NameSpace(os.path.abspath(dir_name))
        file = ns.ParseName(base_name)

        # This is a string in  "HH:MM:SS" format
        length_val  = ns.GetDetailsOf(file, MediaFileClass._length_col_index)
        self.length = length_val

        bit_rate_val = ns.GetDetailsOf(file, MediaFileClass._bit_rate_col_index)

        # For some reason, the bitrate column returns a string with the
        # left-to-right mark as the first char (ex "[U+200E]705kbps")
        # Here we just throw it away
        self.bit_rate = bit_rate_val.strip('\u200e')

        # If a length was found, convert to milliseconds.
        # If not found, it will remain as 0
        if (len(self.length) > 0):
            # SECONDS multiplier for ss, mm, hh, dd.  dd not used...yet?
            multiplier = [1, 60, 3600, 24] 

            # Length is returned as a string in "HH:MM:SS" form.
            #   ex.  "11:22:33" == 11hrs, 22mins, and 33s
            # Here it's split into each component, and then reversed so
            # the calculation below starts with seconds
            ssmmhh = self.length.split(":")  # Ex. 11:22:33
            ssmmhh.reverse()                 # Ex. 33:22:11

            mult         = 0 # index into multiplier array
            totalSeconds = 0

            # Go through each time component (seconds, mins, hrs) and
            # multiply by seconds factor, and sum up all into total Seconds,
            # and finally convert to milliseconds.
            for t in ssmmhh:
                totalSeconds += int(t) * multiplier[mult]
                mult += 1

            self.lengthMS = totalSeconds * 1000

        # HACK HACK HACK
        # Attempt to 'fix' the length, for files that have a length of 0 (or no
        # value in "Length" column)
        #
        # The factor used is just a quick check against apps that show
        # length (but Explorer shows blank for "Length" and "kbps" columns).
        #
        # Factor was calculated as:
        # (Length_Shown_In_VLC_Converted_to_Milliseconds / FileSize_Bytes)
        # (1h:58m:33s * 1000) ==> 7,113,000ms / 113,815,552 = 0.062495
        #
        # Out of all files I have, only 1 doesn't show any value in Length
        # column, so I don't really care to solve this problem yet for the
        # more general case.
        if (self.lengthMS <= 0):
            self.lengthMS = int(0.062495 * self.file_size)

        # Just an FYI.  I've only found 1 file without this value
        # This routine might be too noisy, if OS version doesn't have a bitrate
        # column.
        if (len(self.bit_rate) <= 0):
            print( "!!!!! No Bit Rate for {0}".format(self.file_name))

    def get_file_size(self):
        self.file_size = os.path.getsize(self.file_name)

    # This function returns the media tag:
    #     <media src="..." cid="..." tid="..."/> 
    # for this media file, and will be used during main routine file writing.
    # It uses the UnsortedAttributes() formatter, so that original order
    # is retained SRC/CID/TID, which makes eye-balling the results easier
    def to_media_element_string(self):
        str = (
            ( self.media_elem.encode(formatter=UnsortedAttributes()) )
                .decode('UTF-8')
        )
        # Need to replace "&"" and then apostrophe("'").
        # Do in this order, so "&apos" dosen't get nuked by the "&" replacement
        str = re.sub(r"&", "&amp;", str)
        str = re.sub(r"'", "&apos;", str)
        return str

