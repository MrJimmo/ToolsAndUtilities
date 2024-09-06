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

Chrome Preferences Tool

Simple tool for processing Chrome's preference file, and in version 1 of this
script, it allows listing and/or saving all the Script Snippets from DevTools.

Possible Preference File locations:
[Windows]
Chrome:
%USERPROFILE%/AppData/Local/Google/Chrome/User Data/Default/Preferences

Edge
%USERPROFILE%/AppData/Local/Microsoft/Edge/User Data/Profile 1/Preferences

[Linux]
~/.config/google-chrome/Default/Preferences

NOTE:  Parts of path may be slightly different, depending on which release
channel you have installed or Profile you are operating under.


At the time this script was created, the Preferences file contains a large JSON
object.

Script snippets are found in devtools.preferences.script-snippets JSON Path.
And within the dictionary: dict['devtools']['preferences']['script-snippets']

And each Snippet has a 'name' and 'content' field.

usage: chromeprefs.py [-h] -i INPUT_FILE [-o OUTPUT_DIRECTORY]
                        [-n SCRIPT_NAME_PATTERN] [-l] [-c] [-s]

    -h, --help            show this help message and exit

    -i INPUT_FILE, --input-file INPUT_FILE
                        Name of file to process

    -o OUTPUT_DIRECTORY, --output-directory OUTPUT_DIRECTORY
                        Path to the directory where files are to be saved.
                        If omitted, current dir is used
    -n SCRIPT_NAME_PATTERN, --script-name SCRIPT_NAME_PATTERN
                        Name of script to find (regex patterns supported)Ex:
                        snippet_(1|3), finds "snippet_1" and "snippet_3"

    -l, --list            List the file names

    -c, --show-contents   Show script contents in console

    -s, --save-contents   Save contents of the snippets foundFile will be named
                          <NAME>.js

Example:
    chromeprefs.py
    -i "C:/Users/Foo/AppData/Local/Google/Chrome/User Data/Default/Preferences"
    -l -n ".*Scratch.* -c -s -o ./Snippets

    This will list all the names of the snippets that contain "Scratch" string
    in their name and will show the the contents as well as save to /Snippets
    directory.

TODO:
    - Support absence of -i/--input-file param, and find it for current user.
'''

import json
import argparse
import os
import re

from datetime import datetime

# Global options object, produced by argparse.ArgumentParser.parse_args()
options = None

'''
read_input_file_into_dict

Read the given file and return a dictionary
'''
def read_input_file_into_dict(file_name):
    try:
        with open(file_name) as f:
            return json.load(f)
    except Exception as err:
        output_string("{0}: {1}".format( type(err), err) )

'''
write_script_to_file

This function takes a script item and writes it to a js file.

The item is a simple object in the Preferences file that has 'name' and
'content' fields.

Resulting file will be written to:
"<options.output_directory>\<script_name>.js"

If options.output_directory was not provided by the user, the default is the
current directory.
'''
def write_script_to_file( script ):
    global options

    if (len(script['content']) == 0):
        output_string('No contents for script \"{0}\"'.format(script['name']))
        return

    # If output directory doesn't exist, create it.
    full_directory_path = os.path.abspath(options.output_directory)
    #output_string( "full_directory_path: {0}".format(full_directory_path))

    if not os.path.isdir(full_directory_path):
        output_string("Creating Path: \"{0}\"".format(full_directory_path))
        os.makedirs(full_directory_path, exist_ok=True)

    full_path_Name = "{0}{1}{2}.js".format(os.path.abspath(
        options.output_directory), os.sep, script['name'])

    try:
        with open(full_path_Name, 'w') as output_file:
            output_file.write(script['content'])
    except OSError as err:
        output_string("[OSError] {0}: {1}".format( type(err), err) )
    except Exception as err:
        output_string("[Exception] {0}: {1}".format( type(err), err) )

    output_string( "Wrote {0} bytes to {1}".format(len(script['content']),
        full_path_Name))


'''
process_file

This is the main routine that processes the given file.
'''
def process_file(file_name):
    global options

    file_contents_dict = read_input_file_into_dict(file_name)

    if (file_contents_dict == None):
        output_string("Failed to read file: \"{0}\"".format(file_name))
        output_string("**** Check path and filename are as expected")
        return

    try:
        script_snippets = json.loads(file_contents_dict['devtools']
                                     ['preferences']['script-snippets'])
    except KeyError as err:
        output_string("KeyError {0}: {1}".format( type(err), err) )
        output_string( ("**** Is the file missing devtools.preferences."
                        "script-snippets object?"))
        return
    except Exception as err:
        output_string("Failed loading file \"{0}\"".format(file_name))
        output_string("**** Is the file the right one (and in JSON format)?")
        output_string("[Exception] {0}: {1}".format( type(err), err) )
        return

    num_scripts_found = 0
    for script in script_snippets:
            select_script = True

            # if a name/pattern was provided, check for match
            if (len(options.script_name_pattern) > 0):
                try:
                    rx = re.compile('{0}'.format(options.script_name_pattern))
                except Exception as err:
                    output_string("Failed to compile regex: {0}".format(
                        options.script_name_pattern))
                    output_string("[Exception] {0}: {1}".format( type(err),
                        err))
                    output_string("**** Check regex pattern")
                    return

                if not re.match(rx, script['name']):
                    select_script = False

            if select_script:
                num_scripts_found += 1
                if (options.list_snippets):
                    output_string( 'Name: {0} ({1:,})'.format(script['name'],
                        len(script['content'])))

                if (options.show_contents):
                    output_string( '{0}\n'.format(script['content']))
                    output_string('='*80)

                if (options.save_contents):
                    write_script_to_file(script)

    output_string("Showing: {0} of {1}".format(num_scripts_found,
        len(script_snippets)))


'''
output_options

Output the params and their values.
'''
def output_options():
    global options
    output_string('[=========== Chrome Preferences Tool  ===========]')
    output_string('Preferences File     : {0}'.format(options.input_file))
    output_string('Output Directory     : {0}'.format(options.output_directory))
    output_string('Script Name Pattern  : {0}'.
        format(options.script_name_pattern))
    output_string('List Files           : {0}'.format(options.list_snippets))
    output_string('Show Script Contents : {0}'.format(options.show_contents))
    output_string('Save Script Contents : {0}'.format(options.save_contents))


'''
output_string

Simple output wrapper that prepends a time string in YYYY-MM-DD HH:MM:SS format.
Example:
    [2024-09-06 01:21:31] <string passed in>
'''
def output_string(str):
    print("{0} {1}".format("[{:%Y-%m-%d %H:%M:%S}]".format(datetime.now()),str))


def parse_args():
    parser = argparse.ArgumentParser(
        description='Chrome Preference Tool')

    parser.add_argument('-i', '--input-file',
        required = True,
        dest     = 'input_file',
        default  = '',
        help     = ('Name of file to process')
    )

    parser.add_argument('-o', '--output-directory',
        required = False,
        dest     = 'output_directory',
        default  = '.\\',
        help     = ('Path to the directory where files are to be saved.  '
                    'If omitted, current dir is used.')
    )

    parser.add_argument('-n', '--script-name',
        required = False,
        dest     = 'script_name_pattern',
        default  = '',
        help     = ('Name of script to find (regex patterns supported)'
                    'Ex: snippet_(1|3), finds \"snippet_1\" and \"snippet_3\"')
    )

    parser.add_argument('-l','--list',
        required = False,
        dest     = 'list_snippets',
        action   = "store_true",
        default  = False,
        help     = ('List the snippet names')
    )

    parser.add_argument('-c','--show-contents',
        required = False,
        dest     = 'show_contents',
        action   = "store_true",
        default  = False,
        help     = ('Show script contents in console')
    )

    parser.add_argument('-s','--save-contents',
        required = False,
        dest     = 'save_contents',
        action   = "store_true",
        default  = False,
        help     = ('Save contents of the snippets found'
                    'File will be named <NAME>.js')
    )

    options = parser.parse_args()

    if (len(options.output_directory) == 0):
        options.output_directory = os.path.dirname(os.path.abspath(__file__))

    return options


def main(options):

    output_options()

    process_file( options.input_file)


if __name__ == "__main__":
    options = parse_args()

    start_time = datetime.now()
    main(options)
    finished_time = datetime.now()

    elapsed_time = finished_time - start_time

    print("Started : {0}".format("[{:%Y-%d-%m %H:%M:%S}]".format(start_time)))
    print("Finished: {0}".format("[{:%Y-%d-%m %H:%M:%S}]".
        format(finished_time)))
    print("Elapsed : {0}".format(elapsed_time))
