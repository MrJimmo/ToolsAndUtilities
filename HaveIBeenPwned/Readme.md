# HaveIBeenPwned Utility

This Powershell script handles calling the [HaveIBeenPwned](https://haveibeenpwned.com/) api to check for password occurrences in security breaches.

More details:  https://haveibeenpwned.com/API/v3, specificaly the "Searching by range" section.

If you send an HTTP Request to...

`https://api.pwnedpasswords.com/range/<FIRST_5_CHARS_OF_PASSWORD_HASH>`

...where <FIRST_5_CHARS_OF_PASSWORD_HASH> is [0..4] chars of the SHA-1 hash of your password.

```
Example:
    pa$$word SHA-1 is 119E9F64E12B97293A8334CCD162C1245786336D
    and [0..4] is 119E9
```
...you will either get an HTTP response containing multiple rows with:
 [5..34] Chars of SHA-1 hash of password (and a count of occurrences)

Or....well, I don't know what a non-hit looks like, because all random values between 00000..FFFFF I tried, it always returned something.

(according to https://haveibeenpwned.com/API/v3, should never get 404, all 0x00000 - 0xFFFFF values are represented)

I believe you can download the entire list, but it's many GBs and an exercise for those who have the bandwidth :o)

Assuming results are returned, this script then looks for an occurrence of The last 35 bytes [5..34], of your passwords SHA-1 hash...

```
Same Example:
    pa$$word SHA-1 is 119E9F64E12B97293A8334CCD162C1245786336D
    and [0..4] is 119E9
    [5..34] is F64E12B97293A8334CCD162C1245786336D
```

...and if it finds it, it means it was found in some dump of passwords.

```
NOTE:
If you check for things like short, N-Digit pins, ex. 12345, there will be massive hits.  Good reminder that by themselves, PINs are weak.
```

The 3 main parameters:

**-Password:**
This is the password to check.  Use Quotes to surround any special characters.


```
NOTE:
Powershell escape char is the back tick "`". Like for passwords that contain "$", you'd need to escape them, ex.  "pa`$`$word"

Also note, the back tick "`" is used as the line continuation character and is used throughout, as an effort to stay with 80 chars per line.
```

**-SHA1**
This is the SHA-1 of the password to check for.

This is what this script does for you, when you use -Password or provide a list of passwords with -PasswordFile


**-PasswordFile**
    File containing list of passwords.

    File is assumed to be TSV and contain columnar data (with this header):
    [Group]<TAB>[Title]<TAB>[Username]<TAB>[Password]

    This is just the format I used when I created this script, as I wanted to output the Group/Title/Username for hits, so I could build a list of those that I needed to change.

Use Get-Help to see more details about other supported params and switches.

# Parameters
## -Password
Password in Quotes.  If Password contains quotes, "$", you'll need to escape that value.

```
Example:
-Password "pa$$word"
...should be...
-Password "pa`$`$word"
```

FYI: SHA-1 of pa$$word is 119E9F64E12B97293A8334CCD162C1245786336D, so
generating your own SHA for any tricky ones, is also an option if
some weird case exists.


## -SHA1
    SHA-1 of the password.

## -PasswordFile
Name of file containing list of passwords.

File is assumed to be Tab Separated Values(TSV) and contains columnar data:

`[Group]<TAB>[Title]<TAB>[Username]<TAB>[Password]`

Example file contents:
|Group|Title|Username|Password|
|-|-|-|-|
|Work|MyWork|jdoe@.....com|Pa$$word|
|Web|SomeRandomSite.com|guest@.......com|Passw0rd!|
|Bank|First Intl. Bank|jdoe@........com|P@ssword!|

## -Pretend
This switch causes the script to do everything except actually send the HTTP request to HaveIBeenPwned website.  Mainly for debugging.

## -LogLevel
Level of logging to use.

|Level|Meaning|
|-|-|
|Verbose|Everything including debugging output|
|Normal|Everything except debugging output. (DEFAULT)|
|Minimum|Just a few bits here and there including results|

## -RequestSleep
Seconds to sleep between requests to server.
Default is 5 seconds.

NOTE: Please Be kind to the site, don't clobber them with requests.

## -SaveContents
When this switch is present, the contents of the HTTP Results body is
saved to the current directory, unless -ContentRoot is specified.

## -ContentRoot
Root location used when the -SaveContents is specified.
This parameter is ignored if -SaveContents switch is absent from command line.

If script is run from "C:\foo\bar" with -ContentRoot ".\HashFiles" the contents will be saved to "C:\foo\bar\HashFiles\"

# Examples
`.\HaveIBeenPwned.ps1 -PasswordFile .\passwordlist.tsv -RequestSleep 10 -SaveContent -ContentRoot .\HashFiles`

Grab list of Password records from passwordlist.tsv 

Sleep for 10 second between requests

Results will be stored in directory specified by the **-ContentRoot** location

If script is run from `"C:\foo\bar"` with -ContentRoot `"HashFiles"` the contents will be saved to `"C:\foo\bar\HasFiles\""`


` .\HaveIBeenPwned.ps1 -Password "pa$$word" -LogLevel Verbose`

Sends a request to the website for the given password.
Hash is 119e9f64e12b97293a8334ccd162c1245786336d

And lots of output to the console.

`.\HaveIBeenPwned.ps1 -SHA1 "119e9f64e12b97293a8334ccd162c1245786336d"`

Sends a request to the website, based on that hash.


## Acknowledgement:
I created this after watching Mike Pound's Computerphile video:
https://www.youtube.com/watch?v=hhUb5iknVJs

And I think originally inspired by his script:
https://github.com/mikepound/pwned-search/blob/master/pwned.ps1
