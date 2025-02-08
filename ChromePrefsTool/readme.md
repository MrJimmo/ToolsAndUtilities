# Chrome Preferences Tool

Simple script to read the Preferences file for Chrome (and MS Edge) and list or export the scripts that live in the DevTools Snippets tab.

At the time this script was created, the Preferences file contains a large JSON
object.

Script snippets are found in devtools.preferences.script-snippets JSON Path.
And within a dictionary: dict['devtools']['preferences']['script-snippets']

Each Snippet has a 'name' and 'content' field.


**Possible Preference File locations:**

|Browser|Preferences file location|
|-|-|
|Chrome (Windows)|%USERPROFILE%/AppData/Local/Google/Chrome/User Data/Default/Preferences|
|Edge (Windows)|%USERPROFILE%/AppData/Local/Microsoft/Edge/User Data/Profile 1/Preferences
Chrome (Linux)|~/.config/google-chrome/Default/Preferences|


<div style="background:yellow;color:black;border:solid">
<b>NOTE:</b> Parts of the path may be slightly different, depending on which release channel you have installed or Profile you are operating under.
</div>
<p>


## Usage
```
usage: chromeprefs.py [-h] -i INPUT_FILE [-o OUTPUT_DIRECTORY] [-n SCRIPT_NAME_PATTERN] [-l] [-c] [-s]
```
|Switch|Meaning|
|-|-|
|-i INPUT_FILE, --input-file INPUT_FILE|Name of file to process|
|-o OUTPUT_DIRECTORY, --output-directory OUTPUT_DIRECTORY|Path to the directory where files are to be saved. If omitted, current dir is used|
|-n SCRIPT_NAME_PATTERN, --script-name SCRIPT_NAME_PATTERN|Name of script to find (regex patterns supported) Ex: **snippet_(1\|3)**, finds "snippet_1" and "snippet_3"|
|-l, --list|List the snippet names|
|-c, --show-contents|Show script contents in console|
|-s, --save-contents|Save contents of the snippets foundFile will be named <NAME>.js|


## Example
```
python chromeprefs.py -i "C:/Users/Foo/AppData/Local/Google/Chrome/User Data/Default/Preferences" -l -n ".*Scratch.*" -c -s -o ./Snippets

This will list all the names of the snippets that contain "Scratch" string in their name and will show the the contents as well as save them to /Snippets directory.
```

