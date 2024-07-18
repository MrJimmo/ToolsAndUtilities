'''
--------------------------------------------------------------------------------
MIT License

Copyright (c) 2024 Jim Moore

Permission is hereby granted, free of charge, to any person obtaining a copy of 
this software and associated documentation files (the "Software"), to deal in 
the Software without restriction, including without limitation the rights to 
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies 
of the Software, and to permit persons to whom the Software is furnished to do 
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all 
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE 
SOFTWARE.
--------------------------------------------------------------------------------

Playlist Tool

This tool reads a Windows Media Player Playlist XML file and distributes
the media files into 'buckets' defined by the media files that are greater
than some threshold in length, and the 'buckets' contain the shorter files.


Kind of silly, given the age of WMP and the goal, but here's the "Why?"...

I have a playlist that I created for just about all my media files (nearly
1500 files)

About 200 of the media files are 45min or longer, while most of the remaining
files are ones dumped from my library of CDs, and are much shorter.

Just randomly sorting the entire list, often places the longer files near or
next to the other long ones.

I'd rather have the longer ones spread out semi-evenly, and
then all the shorter files be sprinkled evenly throughout the entire list.

By treating these 'longer' files as bucket delimiters, all the files that are
shorter in length, are placed within these buckets, and the way the algorithm
does this, each bucket has a relatively even length of play time [Not exactly
true, see the "Interesting side-effect" comment below]

Example:
Given 3 files that are 1hr in length (LONG1, LONG2, LONG3)
And 10 files are shorter, maybe 3-5min (short1, short2, ..., short10)

After this tool processes the existing list, the resulting file should be
similar to:

LONG2
  short1
  short4
  short7
  short10
LONG1
  short2
  short5
  short8
LONG3
  short3
  short6
  short9

Some things to notice:
o The LONG files are distributed randomly, defining 3 buckets
o The short files are added one at a time, to each bucket successively

Once this distribution is made, each bucket is then randomized further, so it
might result in:
LONG2
  short7
  short1
  short10
  short4
LONG1
  short5
  short2
  short8
LONG2
  short9
  short3
  short6

  Same files within each bucket, but now sorted randomly.

  Interesting side-effect of sorting the initial full list in descending order
  of file length, is that the total play time for each bucket steadly decreases.

  This is likely due to the nature of the bucket filling routine, which adds 1
  short file per bucket, starting first bucket and when reaching the last
  bucket, starts (wraps around to) the first bucket again.
  
  This biases the longer overall bucket playtime in descending bucket order,
  because Bucket[N] is always getting File[X] which is >= the length of
  File[X+1], and Bucket[N+1] ends up with with File[X+1] which because of the
  sorting of the list by descending length time means File[X].length >= 
  File[X+1].length, and this causes the overall bucket play time to decrease
  from first bucket, to last bucket.

  If it really needs to be fixed, a couple tweaks to the bucket filling 
  algorithm could produce a better distribution:

  Algo tweak Option 1:
  Instead of 'wrapping around' to the first bucket, flip the bucket fill
  direction each time the last/first bucket is found (basically bouncing back
  and forth, until all short files are added)

  Algo tweak Option 2:
  Create an array of bucket indices, randomize, fill buckets in this random 
  order, after one iteration, radomize again, and continue until all files
  are distributed.  This might actually remove the need for the
  randomize_buckets() routine all together because the 'randomization' factor
  is part of the indeces already.

Key details of the algorithm:
- File is read and a MediaFileClass obj is created for each entry in playlist
- Size and Length are retrived by using win32com.client / Shell.Application
- This complete list is sorted by length (descending) [FIG A in Readme.md]
- A new list is created from all media files that are greater than a given
  threshold
- The rest of the big list of media files is processed, and inserted into each
  bucket one at a time successively, in a descending (length) order. [Fig B in
  Readme.md]
- Then a randomization of the files within each 'bucket' is done [Fig C in
  Readme.md]
- Finally, this new list is written out to a specified XML file.

This all might be a bit goofy, especially the algo I settled on, but this was
part coding exercise and part utilitarian, and in the end I ended up with a
playlist ordered in the way I want. It works, and after listening to the new
playlist, it accomplished what I wanted.

Execution Notes:
    May need to install lxml and beautifulsoup

        pip install beautifulsoup4 lxml

Example usage:
    python playlisttool.py -p "test.wpl" -d -c -o out.csv -v -w NewPlayList.wpl

    This will consume playlist file "test.wpl", distribute the files, and
    output the results to the given out.csv and create a new playlist file
    called "NewPlayList.wpl"

Reference:
    https://en.wikipedia.org/wiki/Windows_Media_Player_Playlist


usage: playlisttool.py [-h] [-a] [-b BUCKET_THRESHOLD] [-c] [-d]
    [-o OUTPUT_FILENAME] -p PLAYLIST_FILE [-r] [-t PLAYLIST_TITLE] [-v]
    [-w WPL_FILE]

Playlist Tool

options:
  -h, --help            show this help message and exit
  -b BUCKET_THRESHOLD, --bucket-threshold BUCKET_THRESHOLD
                        Bucket threshold (in ms). Smaller number here will
                        produce more buckets, larger value will produce fewer
                        buckets.
  -c, --csv             When this switch is present, output is csv.
  -d, --distribute-files
                        When this switch is present, a new list is created with
                        the songs distributed according to length.
  -o OUTPUT_FILENAME, --output-file OUTPUT_FILENAME
                        Name of file for output. This is execution output, not
                        the the name of the new playlist file. Use -w/--wpl-file
                        param to specify the new WPL file name.
  -p PLAYLIST_FILE, --playlist-file PLAYLIST_FILE
                        Name of playlist file to process.
  -r, --remove-bad-files
                        Remove any bad files found (really just ignores them)
                        Does not remove from storage.
  -t PLAYLIST_TITLE, --title PLAYLIST_TITLE
                        Specify the title for the new playlist (if -w is
                        specified)
  -v, --verbose         Enable for verbose output
  -w WPL_FILE, --wpl-file WPL_FILE
                        Name of new wpl file to create.
'''


from bs4 import BeautifulSoup
from bs4.formatter import HTMLFormatter
import argparse
from datetime import datetime
import os
import random
import re

# MediaFileClass.py is expected to be in the same directory
# An instance of this class represents 1 <media> entry in the playlist.
from MediaFileClass import MediaFileClass

# Global array of media file sources found within the playlist.
media_files = None

# Global options object, produced by argparse.ArgumentParser.parse_args()
options = None

# Soup object based on the playlist file (XML format)
playlist_soup = None

'''
get_playlist_soup_from_file

This function uses BeautifulSoup to read the given playlist into the 
global playlist_soup variable.
'''
def get_playlist_soup_from_file(playlist_filename):
    global playlist_soup

    if not os.path.isfile(playlist_filename):
        output_string('XML File: "{0}" not valid '.format(playlist_filename))
        return

    # Need to specify encoding as utf-8 here, because some media file names can
    # contain special chars like umlauts over "o"'s or tilde's over "n"'s
    with open(playlist_filename, "r", encoding="utf-8") as xmlFile:
        playlist_soup = BeautifulSoup(xmlFile, 'xml')

    output_playlist_details(playlist_soup)


'''
output_playlist_details

Output basic information of the playlist, based on several Meta tags.
'''
def output_playlist_details(playlist):
    all_meta = playlist.find_all('meta')

    item_count = -1
    for elem in all_meta:
        if (elem.has_attr('name') and elem.has_attr('content') and not
            elem['name'] == 'Generator'):
            item_count = int(elem['content'])

    output_string("Title     : {0}".format(playlist.title.get_text()))
    output_string("Author    : {0}".format(playlist.author.get_text()))
    output_string("Item Count: {0}".format(item_count))


'''
get_file_list_from_playlist

This function reads the specified playlist file and builds an array of soup
objects for all the <media> tags.

Each entry in the Playlist XML follows the form:
    <media src="C:\Path\To\Media\File.mp3" cid=GUID  tid=GUID/>
'''
def get_file_list_from_playlist(playlist):
    global options
    global media_files

    media_files = []

    # Iterate through the XML file and fill the list with MediaFileClass objects
    # base on all the <media> elements found
    for media in playlist.find_all('media'):
        media_files.append(MediaFileClass(media))

    # Invalid files are mostly those that have likely been moved or deleted
    # but the playlist itself was never updated.
    list_invalid_files(media_files)

    # Sort list of media_files by length in ms, ascending.
    media_files.sort(key=lambda x: x.lengthMS, reverse=True)

    output_string('Media Files Found: {0}'.format(len(media_files)))


'''
list_invalid_files

This function handles checking for Media files with a size of -1, and
output the list (or simple message if no bad ones found)

If -r/--remove-bad-files cmd line switch is specified, this routine handles
removing them from the global list of files.
'''
def list_invalid_files(files):
    global options
    if files == None:
        output_string('[list_invalid_files] No invalid files to process')
        return

    bad_file_indices = []

    # An array of bad files is created, and will be used later to delete those
    # array elements (if any were found)
    for file_index in range(0, len(files) - 1):
        if (files[file_index].file_size < 0):
            debug_print("Found bad file at index: {0}".format(file_index))
            bad_file_indices.append(file_index)

    print("[list_invalid_files] Before file_index loop. bad_file_indices: {0}"
          .format(len(bad_file_indices)))

    if (len(bad_file_indices) > 0):
        output_string('These files were not found:')
        for bad_index in bad_file_indices:
            output_string('{0}'.format(files[bad_index].file_name))

    # If -r/--remove-bad-files switch specified, remove any bad files found.
    # the bad_file_indices array is sorted in reverse order, and each element
    # is removed, last-to-first ...I actually didn't test to see if
    # removing in first-to-last order was actually a problem.  Just wrote it
    # this way initialy and it works :o)
    if options.remove_bad_files:
        bad_file_indices.sort(reverse=True)
        for bad_index in bad_file_indices:
            del files[bad_index]

'''
distribute_list

This is the main driver of the algorithm.

This function attempts to re-arrange the the list of provided song files, by
spreading out the longer songs and intersperse some number of shorter songs.

The longer songs can be thought of as bucket boundaries, where the shorter songs
are going to be placed.

Initial array is assumed to be sorted (descending by song length). This makes
the placing of the shorter songs more evenly distributed, otherwise if not
sorted, a bucket may end up being longer or shorter than average.

Basic
o Take all songs in the initial array >= length_threshold and add to new array
o Randomize this new array
o Iterate over all songs < length_threshold in initial array, inserting after
  each Boundary song (in succession), until iteration complete.
  - Keep track of the Boundary song indices so insertion is known
o Finally, randomize each 'bucket'
  - This routine will depend on the boundary song indices

length_threshold is the minimun length(ms) for a song to be considered a
'bucket'.

Readme.md explains this with some pictures and examples playlist.
'''
def distribute_list(mediaFiles, length_threshold):
    global options

    new_list = []

    bucket_number = 0

    # Fill the new_list array with the files that are longer than the threshold
    for boundary_song in mediaFiles:
        if (boundary_song.lengthMS >= length_threshold):
            # During development, I was adding "XXXXXX" to the beginning of
            # each bucket boundary file, to more easily see it in the resulting
            # file and verify the algo.  Pointless now, but may need in future
            # as tweaks to the algorithm are made.
            # boundary_song.file_name = "XXXXXXX{0}"
            #   .format(boundary_song.file_name)
            boundary_song.bucket_number = "{0}".format(bucket_number)
            new_list.append(boundary_song)
            bucket_number += 1


    # Shuffle to randomly distributes the bucket boundary entries.
    random.shuffle(new_list)
    output_string("Buckets Created: {0}".format ( len(new_list) ) )

    # Need to keep track of the bucket indexes which will be used during the
    # bucket filling/randomizing routine.
    boundary_indices = list(range(0, len(new_list)))

    debug_print("[distribute_list] boundary_indices.length: {0}"
        .format(len(boundary_indices)))
    debug_print(boundary_indices)
    output_list_of_files(new_list)

    current_boundary_index = 0

    # Optimize by skipping the first len(new_list) files,
    # TODO: change this to use range instead of just "in"
    for short_song in media_files:
        if (short_song.lengthMS < length_threshold):
            # Insert just after the current boundary
            short_song.bucket_number = new_list[
                boundary_indices[current_boundary_index]].bucket_number
            debug_print("[distribute_list] short_song.bucket_number = {0}".
                format(short_song.bucket_number))
            new_list.insert(boundary_indices[current_boundary_index]+1,
                            short_song)

            # Because we inserted a new song, bump up the remaining indices
            # This makes the indexes "move-right" so they retain accurate
            # bucket boundary positions.
            for i in range(current_boundary_index+1, len(boundary_indices)):
                boundary_indices[i] += 1

        # Advance to the next boundary index
        current_boundary_index += 1

        # wrap back to first, if we've gone past end
        # TODO: Consider just bouncing and go last to first (and then bounce
        # again when it reaches the first bucket) This would be Algo tweak
        # Option #2, mentioned in earlier comment.
        if (current_boundary_index >= len(boundary_indices)):
            current_boundary_index = 0

    debug_print(boundary_indices)

    randomize_buckets(new_list, boundary_indices)

    return new_list


'''
randomize_buckets

This function will randomize the buckets defined by the bucket_indices

Algo:
- iterate through media_files with a current_file index
- skip bucket boundaries
- choose a random value between current bucket index+1 and next bucket index-1
- swap
- repeat for next bucket.

So a walking index across all files, skipping bucket bounaries, and randomly
swapping current media file with one within the current bucket range.
'''
def randomize_buckets(mediaFiles, bucket_indices):
    # Indexes of the first and second bucket boundaries
    bucket_index_current = 0
    bucket_index_next    = 1

    # Skip the first mediaFiles entry, as it's most likely a bucket boundary
    start_iteration_index = bucket_indices[bucket_index_current] + 1

    # But, just in case the first bucket index is not the first mediaFile index,
    # set the iteration index to the start of the mediaFiles array
    if (bucket_indices[bucket_index_current] > 0):
        start_iteration_index = 0

    # May need the output from these if any future tweaks to algorithm.
    # debug_print(bucket_indices)
    # debug_print("[Before Loop] bucket_index_current:{0} next_bucket_index:{1}"
    #             .format(bucket_index_current, bucket_index_next))
    # debug_print("start_iteration_index: {0}, len(mediaFiles)-1:{1}"
    #             .format(start_iteration_index, len(mediaFiles)-1))

    # Iterate through the entire list of media files, starting at the first
    # non-boundary bucket index (usually second element in mediaFiles array)
    for current_file_index in range(start_iteration_index, len(mediaFiles)-1 ):

        # If we're on a bucket boundary, update index variables and continue
        if current_file_index == bucket_indices[bucket_index_next]:
            bucket_index_current = bucket_index_next
            bucket_index_next += 1

            # If we're at the end of the mediaFiles, break out of the routine
            if (bucket_index_next == len(bucket_indices)):
                break

            debug_print("bucket_index_current:{0} next_bucket_index:{1}"
                        .format(bucket_index_current, bucket_index_next))

            continue # We've hit the next bucket Index

        # These two variables now define the first and last items in the current
        # bucket.
        first_in_bucket_index = bucket_indices[bucket_index_current] + 1
        last_in_bucket_index  = bucket_indices[bucket_index_next]    - 1

        # Super noisy output, but crucial during development and future tweaks
        # Uncomment and specify -v/--verbose param.
        # debug_print("Current: {0}, first: {1}, Last:{2}".
        #             format(current_file_index, first_in_bucket_index,
        #                    last_in_bucket_index))

        # Choose a random index to swap the current mediaFile with.
        swap_index = random.randint(first_in_bucket_index, last_in_bucket_index)

        # Do the swapperoo (simple 'in place' swap using tuple unpacking)
        # Formatted here with spaces and line continuation char, just to
        # illustrate the technique.
        mediaFiles[swap_index],         mediaFiles[current_file_index] = \
        mediaFiles[current_file_index], mediaFiles[swap_index]


'''
output_list_of_files

This function simply dumps the list of files found in the playlist, and
depending on the options, output may go to a file or just console.
'''
def output_list_of_files(mediaFiles):
    global options

    # Writing the console is mainly for debugging, so is more verbose
    # Should really create some kind of MediaFileClass.toString() function.
    def write_to_console():
        for file in mediaFiles:
            output_string(("Media Filename: {0} [{1}] Length:{2} ({3}ms) "
                           "[{4}] cid={5}, tid={6}").
                           format(file.file_name,
                                  file.file_size,
                                  file.length,
                                  file.lengthMS,
                                  file.bit_rate,
                                  file.cid, file.tid))

    def write_to_file(file):
        with open(options.output_filename, 'w') as output_file:
            for file in mediaFiles:
                output_file.write("\"{0}\" [{1}] Length:{2} ({3}ms) [{4}]\n".
                        format(file.file_name, file.file_size, file.length,
                            file.lengthMS, file.bit_rate))

    if (len(options.output_filename) > 0):
        debug_print("[output_list_of_files] Writing to file: {0}".format(options.output_filename))
        write_to_file(options.output_filename)
    else:
        debug_print("[output_list_of_files] Writing to console")
        write_to_console()


'''
output_as_csv

This function simply iterates through the given list of Media File objects
and outputs to console as a list of comman separated values.  Useful only as
a curiosity, when I was doing some analysis and debugging.

First line is is header:  Index,Filename, Size, LengthMS

If -o / --output-file was specified, then output is written to that file, in a
form that can be opened in Excel or other spreadsheet/CSV aware app.
'''
def output_as_csv(mediaFiles):
    global options
    header ="Index,filename,size,lengthMS,BucketNumber"

    def write_to_console():
        print(header)
        for file in mediaFiles:
            line = ('"{0}",{1},{2},{3}'.
                format(file.file_name, file.file_size, file.lengthMS,
                       file.bucket_number))
            print(line)

    def write_to_file(file):
        with open(options.output_filename, 'w') as csvFile:
            csvFile.writelines(header+"\n")
            for file in mediaFiles:
                line = ('{0},"{1}",{2},{3},{4}\n'.
                    format(file.originalOrder, file.file_name, file.file_size,
                           file.lengthMS, file.bucket_number))
                csvFile.write(line)

    if (len(options.output_filename) > 0):
        write_to_file(options.output_filename)
    else:
        write_to_console()

'''
write_new_playlist

This function handles writing the list of files in mediaFiles to the wpl file
given in options.wpl_file and other params.

Params:
    mediaFiles: Array of BS4 objects for each <media> tag found in playlist
    options   : ArgumentParser options.
    playlist  : BS4 object representing the playlist.
'''
def write_new_playlist(mediaFiles, options, playlist):
    if mediaFiles == None:
        output_string('[write_new_playlist] No files to process')
        return

    # Get <SEQ> tag. If it's not present, then likely bad/unexpected WPL file
    seq_elem = playlist.find('seq')
    if seq_elem == None:
        output_string("Unable to find <SEQ> tag in playlist: {0}"
                      .format(options.playlist_file))
        return

    # Update ItemCount. Invalid files may have been pruned with
    # the -r/--remove-bad-files switches
    item_count = playlist.find('meta', { "name" : "ItemCount" })
    if item_count:
        item_count["content"] = len(mediaFiles)

    # Update Title
    # If not specified via the -t/--title param, just append a simple date time
    # string formatted as:  YYYYMMDD-HHMMSS  ex 20240703-142250.
    # This will at least make it distinct from original when viewed in WMP.
    #
    # BUG:  The <Title> element is including carriage returns, which WMP shows
    #       and looks terrible.  Figure out how to output the <TITLE> without
    #       any carriage returns, so it's one line like:
    #           <title>Distributed All</title>
    #       not like:
    #           <title>
    #               Distributed All
    #           </title>
    #       Currently, I just hand edit after generating.
    title = playlist.find('title')
    if title:
        if len(options.playlist_title) > 0:
            title.string = options.playlist_title
        else:
            now = datetime.now().strftime("%Y%m%d-%H%M%S")
            title.string = "{0} ({1})".format(title.string, now)
    else:
        # TBD: Should do something here. Maybe something clever based on
        #      filename.
        pass

    # helper function, to replace the <SEQ> element from the playList.
    replace_seq_with_mediafiles(seq_elem, mediaFiles)

    # Default indent is 1 space, this will change it to 4 spaces.
    # WMP doesn't care, but made debugging a lot easier.
    indent_formatter = HTMLFormatter(indent=4)

    # Write everything out into (or overwrite) the specified WPL file
    # This routine removes the XML Prolog string "<?xml.....?>" which does
    # not appear in 'normal' WPL files.
    with open(options.wpl_file, "w", encoding="utf-8") as xmlFile:
        xml_text = playlist.prettify(formatter=indent_formatter)
        xml_text = re.sub(r"<\?xml.*\?>\n", "", xml_text)
        xmlFile.write(xml_text)


'''
replace_seq_with_mediafiles

Clear and replace the contents of the <SEQ> element, with the new list of
media file elements.
'''
def replace_seq_with_mediafiles(seq, mediaFiles):
    seq.clear()
    for media in mediaFiles:
        seq.append(media.to_media_element_string())


'''
output_options

Output the params and their values.
'''
def output_options():
    global options
    output_string('[=========== Playlist Tool  ===========]')
    output_string('Playlist File     : {0}'.format(options.playlist_file))
    output_string('New Playlist File : {0}'.format(options.wpl_file))
    output_string('Bucket Threshold  : {0}'.format(options.bucket_threshold))
    output_string('Output File       : {0}'.format(options.output_filename))
    output_string('Output as CSV     : {0}'.format(options.output_as_csv))
    output_string('Distribute Files  : {0}'.format(options.distribute_files))
    output_string('Remove Bad Files  : {0}'.format(options.remove_bad_files))
    output_string('Verbose output    : {0}'.format(options.verbose_output))

def debug_print(str):
    global options
    if (options.verbose_output):
        print(str)

def output_string(str):
    print("{0} {1}".format("[{:%Y-%d-%m %H:%M:%S}]".format(datetime.now()),str))

def parse_args():
    parser = argparse.ArgumentParser(
        description='Playlist Tool')

    parser.add_argument('-b','--bucket-threshold',
        required = False,
        dest     = 'bucket_threshold',
        type     = int,
        default  = 1765000,
        help     = ('Bucket threshold (in ms). Smaller number here will produce'
                    ' more buckets, larger value will produce fewer buckets.')
    )

    parser.add_argument('-c','--csv',
        required = False,
        dest     = 'output_as_csv',
        action   = "store_true",
        default  = False,
        help     = ('When this switch is present, output is csv.')
    )

    parser.add_argument('-d','--distribute-files',
        required = False,
        dest     = 'distribute_files',
        action   = "store_true",
        default  = False,
        help     = ('When this switch is present, a new list is created with '
                    'the songs distributed according to length.')
    )

    parser.add_argument('-o','--output-file',
        required = False,
        dest     = 'output_filename',
        default  = '',
        help     = ('Name of file for output. This is execution output, not the'
                    ' the name of the new playlist file.  Use -w/--wpl-file'
                    ' param to specify the new WPL file name.'
                   )
    )

    parser.add_argument('-p','--playlist-file',
        required = True,
        dest     = 'playlist_file',
        default  = '',
        help     = 'Name of playlist file to process.'
    )

    parser.add_argument('-r','--remove-bad-files',
        required = False,
        dest     = 'remove_bad_files',
        action   = "store_true",
        default  = False,
        help     = ( 'Remove any bad files found (really just ignores them) '
                    'Does not remove from storage.')
    )

    parser.add_argument('-t','--title',
        required = False,
        dest     = 'playlist_title',
        default  = "",
        help     = 'Specify the title for the new playlist (if -w is specified)'
    )

    parser.add_argument('-v','--verbose',
        required = False,
        dest     = 'verbose_output',
        action   = "store_true",
        default  = False,
        help     = 'Enable for verbose output'
    )

    parser.add_argument('-w','--wpl-file',
        required = False,
        dest     = 'wpl_file',
        default  = '',
        help     = 'Name of new wpl file to create. '
    )

    options = parser.parse_args()

    return options

def main(options):
    global media_files
    global playlist_soup

    output_options()

    get_playlist_soup_from_file(options.playlist_file)

    get_file_list_from_playlist(playlist_soup)

    if (options.distribute_files):
        media_files = distribute_list(media_files, options.bucket_threshold)

    if (options.output_as_csv):
        output_as_csv(media_files)

    if (options.verbose_output):
        output_list_of_files(media_files)

    if (len(options.wpl_file) > 0):
        write_new_playlist(media_files, options, playlist_soup)

if __name__ == "__main__":
    options = parse_args()

    start_time = datetime.now()
    main(options)
    finished_time = datetime.now()

    elapsed_time = finished_time - start_time

    print("Started : {0}".format("[{:%Y-%d-%m %H:%M:%S}]".format(start_time)))
    print("Finished: {0}".format("[{:%Y-%d-%m %H:%M:%S}]".format(finished_time)))
    print("Elapsed : {0}".format(elapsed_time))
