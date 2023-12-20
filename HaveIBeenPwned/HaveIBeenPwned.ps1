<#
.SYNOPSIS
    This script handles calling the HaveIBeenPwned endpoint to check for
    a given password occurrence in security breaches.

.DESCRIPTION
    This script handles calling the HaveIBeenPwned api to check for password
    occurrences in security breaches.

    More details:  https://haveibeenpwned.com/API/v3, specificaly the
    "Searching by range" section.

    If you send an HTTP Request to...

        https://api.pwnedpasswords.com/range/<FIRST_5_CHARS_OF_PASSWORD_HASH>

    ...where <FIRST_5_CHARS_OF_PASSWORD_HASH> is [0..4] chars of the SHA-1 hash
    of your password.

        Example:
        pa$$word SHA-1 is 119E9F64E12B97293A8334CCD162C1245786336D
        and [0..4] is 119E9

    ...you will either get an HTTP response containing multiple rows with:
        [5..34] Chars of SHA-1 hash of password (and a count of occurrences)

    Or....well, I don't know what a non-hit looks like, because all random
    values between 00000..FFFFF I tried, it always returned something.

    (according to https://haveibeenpwned.com/API/v3, should never get 404,
    all 0x00000 - 0xFFFFF values are represented)


    I believe you can download the entire list, but it's many GBs and an
    exercise for those who have the bandwidth :o)

    Assuming results are returned, this script then looks for an occurrence of
    The last 35 bytes [5..34], of your passwords SHA-1 hash...

    Same Example:
        pa$$word SHA-1 is 119E9F64E12B97293A8334CCD162C1245786336D
        and [0..4] is 119E9
        [5..34] is F64E12B97293A8334CCD162C1245786336D

    ...and if it finds it, it means it was found in some dump of passwords.

    NOTE:
    If you check for things like short, N-Digit pins, ex. 12345, there will be
    massive hits.  Good reminder that by themselves, PINs are weak.


    The 3 main parameters:

    -Password:
        This is the password to check.  Use Quotes to surround any
        special characters.

        NOTE: Powershell escape char is the back tick "`". Like for passwords
        that contain "$", you'd need to escape them, ex.  "pa`$`$word"

        Also note, the back tick "`" is used as the line continuation character
        and is used throughout, as an effort to stay with 80 chars per line.

    -SHA1
        This is the SHA-1 of the password to check for.

        This is what this script does for you, when you use -Password or provide
        a list of passwords with -PasswordFile


    -PasswordFile
        File containing list of passwords.

        File is assumed to be TSV and contain columnar data (with this header):
        [Group]<TAB>[Title]<TAB>[Username]<TAB>[Password]

        This is just the format I used when I created this script, as I wanted
        to output the Group/Title/Username for hits, so I could build a list
        of those that I needed to change.

    Use Get-Help to see more details about other supported params and switches.

Credit:
    I created this after watching Mike Pound's Computerphile video:
    https://www.youtube.com/watch?v=hhUb5iknVJs

    And I think originally inspired by his script:
    https://github.com/mikepound/pwned-search/blob/master/pwned.ps1

.PARAMETER Password
    Password in Quotes.  If Password contains quotes, "$", you'll need to escape
    that value.

    Example:
        -Password "pa$$word"
        ...should be...
        -Password "pa`$`$word"

        FYI: SHA-1 of pa$$word is 119E9F64E12B97293A8334CCD162C1245786336D, so
        generating your own SHA for any tricky ones, is also an option if
        some weird case exists.

.PARAMETER SHA1
    SHA-1 of the password.

.PARAMETER PasswordFile
    Name of file containing list of passwords.

    File is assumed to be Tab Separated Values(TSV) and contains columnar data:
    [Group]<TAB>[Title]<TAB>[Username]<TAB>[Password]

    Example:
    Group	Title	Username	Password
    Work	MyWork	jdoe@foo.com	Pa$$word
    Web	SomeRandomSite.com	guest@SomeRandomSite.com	Passw0rd!
    Bank	First Intl.	jdoe@firstintl.com	P@ssword!

.PARAMETER Pretend
    This switch causes the script to do everything except actually send the
    HTTP request to HaveIBeenPwned website.  Mainly for debugging.

.PARAMETER LogLevel
    Level of logging to use.

    Verbose : Everything including debugging output
    Normal  : Everything except debugging output. (DEFAULT)
    Minimum : Just a few bits here and there including results

.PARAMETER RequestSleep
    Seconds to sleep between requests to server.
    Default is 5 seconds.

    NOTE: Please Be kind to the site, don't clobber them with requests.

.PARAMETER SaveContents
    When this switch is present, the contents of the HTTP Results body is
    saved to the current directory, unless -ContentRoot is specified.

.PARAMETER ContentRoot
    Root location used when the -SaveContents is specified.
    This parameter is ignored if -SaveContents switch is absent from command
    line.

    If script is run from "C:\foo\bar" with -ContentRoot ".\HashFiles" the
    contents will be saved to "C:\foo\bar\HashFiles\"

.EXAMPLE
    .\HaveIBeenPwned.ps1 -PasswordFile .\passwordlist.tsv
        -RequestSleep 10 -SaveContent -ContentRoot .\HashFiles

    Grab list of Password records from passwordlist.tsv
    Sleep for 10 second between requests

    Results will be stored in directory specified by the -ContentRoot location

    If script is run from "C:\foo\bar" with -ContentRoot "HashFiles" the
    contents will be saved to "C:\foo\bar\HasFiles\""

.EXAMPLE
    .\HaveIBeenPwned.ps1 -Password "pa`$`$word" -LogLevel Verbose

    Sends a request to the website for the given password.
    Hash is 119e9f64e12b97293a8334ccd162c1245786336d

    And lots of output to the console.

.EXAMPLE
    .\HaveIBeenPwned.ps1 -SHA1 "119e9f64e12b97293a8334ccd162c1245786336d"

    Sends a request to the website, based on that hash.

.NOTES
MIT License

Copyright (c) 2023 Jim Moore

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

License from :https://choosealicense.com/licenses/mit/
#>


<#
    Use of ParametersSets attempt to enforce certain param combos:
    1) If -Password present, don't want -SHA1 and/or -PasswordFile
    2) if -SHA1 present, don't want -Password and/or -PasswordFile
    3) If -PasswordFile present, don't want -Password and/or -SHA1

    Could be clever and still allow combos of all 3, and just add -Password
    and -SHA1 values as individual new records in the list (when -PasswordFile
    is specified).   Future feature :)
#>
Param(
    [Parameter(ParameterSetName='JustPassword', Mandatory=$true)]
    [Parameter(ParameterSetName='JustHash', Mandatory=$false)]
    [Parameter(ParameterSetName='PasswordFile', Mandatory=$false)]
    [string]$Password = "",

    [Parameter(ParameterSetName='JustPassword', Mandatory=$false)]
    [Parameter(ParameterSetName='JustHash', Mandatory=$true)]
    [Parameter(ParameterSetName='PasswordFile', Mandatory=$false)]
    [string]$SHA1 = "",

    [Parameter(ParameterSetName='JustPassword', Mandatory=$false)]
    [Parameter(ParameterSetName='JustHash', Mandatory=$false)]
    [Parameter(ParameterSetName='PasswordFile', Mandatory=$true)]
    [string]$PasswordFile = "",

    [Parameter(Mandatory=$false)]
    [switch]$SaveContents = $false,

    [Parameter(Mandatory=$false)]
    [string]$ContentRoot=$pwd,

    [Parameter(Mandatory=$false)]
    [switch]$Pretend = $false,

    [Parameter(Mandatory=$false)]
    [ValidateSet("Minimum","Normal","Verbose")]
    [string]$LogLevel = "Normal",

    [Parameter(Mandatory=$false)]
    [int]$RequestSleep = 5
)

$global:sha1CSP =
    New-Object System.Security.Cryptography.SHA1CryptoServiceProvider

$global:defaultStringValue ="<BLANK>" # Used when string is $null

$global:validLoggingLevels = [ordered]@{ Minimum = 0; Normal = 1; Verbose = 3}
$global:loggingLevel = $global:validLoggingLevels.Normal

<#
    .DESCRIPTION
    Simple function to output the list of parameters being used for a given
    execution.
#>
function ShowArgs() {
    Write-Out "Params:"
    Write-Out "Password     : $(($Password,'<blank>')[!($Password -ne '')])"
    Write-Out "SHA1         : $(($SHA1,'<blank>')[!($SHA1 -ne '')])"
    Write-Out "PasswordFile : $(($PasswordFile,'<blank>')[!($PasswordFile `
        -ne '')])"
    Write-Out "Pretend      : $Pretend"
    Write-Out "LogLevel     : $LogLevel"
    Write-Out "LoggingLevel : $global:loggingLevel"
    Write-Out "SaveContents : $SaveContents"
    Write-Out "ContentRoot  : $ContentRoot"
}

<#
    .DESCRIPTION
    Class PasswordDetails

    This class is meant as a representation of a given Password or Hash.

    If -Password param is used, the SHA-1 hash is created, and the other class
    properties remain $null, and will be swapped out for a generic value when
    it comes time to print.

    If -SHA1 param is used, then the Password property of this class will
    also be $null, as it really only matters what the hash is when the time
    comes to check the results.

    Constructor chain is a bit clunky, but a slight peculiarity with Powershell
    and it's inability to chain ctor's.

    https://learn.microsoft.com/en-us/powershell/module/
        microsoft.powershell.core/about/about_classes_constructors
#>
class PasswordDetails {
    [string]$GroupName
    [string]$Title
    [string]$UserName
    [string]$Password
    [string]$SHA1Hash
    [int]$HashHitCount

    # Called when -Password or -SHA1 params specified
    PasswordDetails([string]$password, [string]$hash) {
        $this.init($password, $hash)
    }

    # Expected to be used during reading from Password file
    PasswordDetails(
        [string]$group_name,
        [string]$title,
        [string]$user_name,
        [string]$password
    ) {
        $this.init($group_name, $title, $user_name, $password, $null)
    }

    # Init with 2 params that calls 5 param Init method.
    hidden init($password, $hash) {
        Write-Out "[PasswordDetails]:Init(`"$password`",`"$hash`")" `
             -level:$global:validLoggingLevels.Verbose

        # If called with a password but NULL hash, generate the hash from the
        # password.
        if (("" -eq $hash) -and ($null -ne $password)) {
            Write-Out "Password provided:$password.  Generating hash..."`
                -level:$global:validLoggingLevels.Verbose
            $hash = Get-Hash-Of-Password($password)
        }

        $this.init($null, $null, $null, $password, $hash)
    }

    # All constructor roads should lead to this 5 param Init function.
    hidden init($group_name, $title, $user_name, $password, $hash) {

        $this.GroupName = $group_name
        $this.Title     = $title
        $this.UserName  = $user_name
        $this.Password  = $password

        if (($null -eq $hash) -and  ($null -ne $password)) {
            $hash = Get-Hash-Of-Password($password)
        }

        $this.SHA1Hash = $hash

        $this.HashHitCount = 0
    }

    # Basic stringification of an instance values.
    [string] toString() {
        $group_name    = if ($this.GroupName -eq "")
                            {$global:defaultStringValue} else {$this.GroupName}
        $group_title   = if ($this.Title -eq "")
                            {$global:defaultStringValue} else {$this.Title}
        $user_name     = if ($this.UserName -eq "")
                            {$global:defaultStringValue} else {$this.UserName}
        $pword         = if ($this.Password -eq "")
                            {$global:defaultStringValue} else {$this.Password}
        $hash          = if ($this.SHA1Hash -eq "")
                            {$global:defaultStringValue} else {$this.SHA1Hash}
        $hash_hit_count = $this.HashHitCount
        $str ="$group_name, $group_title, $user_name, $pword, $hash, " +
            "$hash_hit_count"

        return $str;
    }
}

<#
    .DESCRIPTION
    This function is the main work horse and does the actual call to the
    api.pwnedpasswords.com website.

    .PARAMETER has
    Only parameter that is necessary is the hash of the password being checked.

    Much of the logging in this function was necessary during the development
    of the script as there's a lot of string swizzling going on.
#>
function Check-Website-For-Hash($hash) {
    $passwordHash = $hash.ToUpper()

    Write-Out "Password Hash: $passwordHash" `
        -level:$global:validLoggingLevels.Normal

    # These 5 chars are sent to the API endpoint.
    $firstFiveChars = $passwordHash.Substring(0,5)
    Write-Out "First 5 Chars: $firstFiveChars" `
        -level:$global:validLoggingLevels.Verbose

    # This is the last 35 chars [5..34] of the hash, and will be used to
    # look for results for our password.
    $lastPartOfHash = $passwordHash.Substring(5)
    Write-Out "Last Part of hash : $lastPartOfHash" `
        -level:$global:validLoggingLevels.Verbose

    $apiURI = "https://api.pwnedpasswords.com/range/$firstFiveChars"

    $responseContent = ""

    # If we're not using the -Pretend switch, then make the actual request.
    if ($Pretend -ne $true) {
        Write-Out "Checking api.pwnedpasswords.com:  $apiURI"

        $response = (Invoke-WebRequest -Uri $apiURI);
        $responseContent = $response.Content

        Write-Out "Received response from api.pwnedpasswords.com"

        # If -SaveContents swich is present, save the contents.
        # This was mainly useful when I was using Fiddler to feed results,
        # during script development.
        if ($SaveContents -eq $true) {
            Write-Content-To-File -content:$responseContent `
                -firstFiveSHAChars:$firstFiveChars
        }
    } else {
        Write-Out "Just pretending, or we would have made request to: $apiURI"
    }

    return $responseContent
}

<#
    .DESCRIPTION
    This function does the actual string matching of the hash, within the
    lines returned from the website.

    Example:
    for -Password "pa`$`$word", the full hash is
        119e9f64e12b97293a8334ccd162c1245786336d


    HTTP Request to site https://api.pwnedpasswords.com/range/7F2B9
        ...
        F5CA58ED8733EDAD4A64548280CEDA261B9:3
        F5EEA7D50E74D348B48159246E8FB3D027D:11
        F64E12B97293A8334CCD162C1245786336D:12110
        F6B2CF321EEAACE7865C6B81FFE73429828:3
        F7037DBCB0ED05B080B61B775860E149056:3
        ...

    And we see our last part "f64e12b97293a8334ccd162c1245786336d" has
    12110 hits.

    I think this approach is a form of https://en.wikipedia.org/wiki/K-anonymity

    .PARAMETER lines
    String array of all the lines retuned from the website.

    .PARAMETER hash
    Full hash of password

    .OUTPUTS
    The number of hits for the given hash.

#>
function Search-Results-For-Hash($lines, $hash) {
    # ToUpper not needed for actual check, but visually more consistent in
    # console output
    $lastPartOfHash = $hash.Substring(5).toUpper()

    Write-Out "Searching for: $lastPartOfHash" `
        -level:$global:validLoggingLevels.Verbose

    $HashHitCount = 0

    foreach($line in $lines) {
        # Mainly just useful for dev and debugging.
        # Uncomment the following to see all the <HASH>:<COUNT> lines returned
        # Write-Out "line: $line" -level:$global:validLoggingLevels.Verbose

        # NOTE: -eq is case insensitive
        $hashFromWebsite = $line.split(':')[0]
        if ($hashFromWebsite -eq $lastPartOfHash) {
            $HashHitCount = [int]$line.split(":")[1]
            break
        }
    }

    return $HashHitCount
}

<#
    .DESCRIPTION
    This function handles creating the SHA-1 hash for the given password

    .PARAMETER password
    Password used to generate hash.
    Example: pa$$word

    .OUTPUTS
    Full SHA-1 hash string of password.
    Example: 119e9f64e12b97293a8334ccd162c1245786336d
#>
function Get-Hash-Of-Password($password) {
    $passwordBytes = [System.Text.Encoding]::UTF8.GetBytes($password)
    $passwordBytesAsHEX = "0x" + $(($passwordBytes|ForEach-Object ToString X2) `
        -join ' 0x')

    Write-Out "Password Bytes: $passwordBytesAsHEX" `
        -level:$global:validLoggingLevels.Verbose

    $hashedPWDBytes = $global:sha1CSP.ComputeHash($passwordBytes)

    $hashedPWDBytesHEX = "0x" + $(($hashedPWDBytes|ForEach-Object ToString X2) `
        -join ' 0x')

    Write-Out "Hashed Bytes  : $hashedPWDBytesHEX" `
        -level:$global:validLoggingLevels.Verbose

    $passwordHash = ($hashedPWDBytes | ForEach-Object ToString X2) -join ''

    Write-Out "Password Hash : $passwordHash" `
        -level:$global:validLoggingLevels.Verbose

    return $passwordHash
}

<#
    .DESCRIPTION
    This function reads the file provided by the -PasswordFile parameter,
    and builds an array of PasswordDetail objects based on its contents.

    File is assumed to be TSV and contains columnar data:
    [Group]<TAB>[Title]<TAB>[Username]<TAB>[Password]

    Example:
    Group	Title	Username	Password
    Work	MyWork	jdoe@.....com	Password
    Web	SomeRandomSite.com	guest@.....com	Passw0rd!
    Bank	First Intl.	jdoe@.....com	P@ssword!

    ==========================================================================
    NOTE: Modify this routine if support for a different file format is needed
          Will also need to change PasswordDetails class.
    ==========================================================================

    .PARAMETER filename
    Filename containing the list of passwords to use.

    .OUTPUTS
    Array of PasswordDetail objects for each of the file entries.
#>
function Read-Password-File($filename) {

    if ((Test-Path -path $filename) -ne $true) {
        throw "**** [Read-Password-File] File not found: $filename"
    }

    <#
    .SYNOPSIS
        Delimiter is assumed to be TAB char, but just incase it's CSV,
        switch to "," comma delimited. Though depending on the number and
        variety of passwords in the file, this may run into one that contains a
        comma and results will likely be spoiled.
    #>
    $delim = "`t"
    if ($filename -like "*.csv") {
        $delim = ","
    }

    $passwords = Import-Csv -Delimiter $delim -Path $filename

    Write-Out ("Read {0} records from {1}" -f $passwords.Length, $filename)

    $records = @()

    <#
    .SYNOPSIS
        Iterate over all those records and add a new PasswordDetails instance
        to the records array.
    #>
    foreach($pwd in $passwords) {
        if ("" -eq $pwd.Password) {
            Write-Out "Skipping incomplete record: `n"+
                "Group    : $($pwd.Group)`n" +
                "Title    : $($pwd.Title)`n" +
                "Username : $($pwd.UserName)`n" +
                "Password : $($pwd.Password)`n"
                -level $global:validLoggingLevels.Verbose
        }
        $records += [PasswordDetails]::new($pwd.Group, $pwd.Title,
            $pwd.UserName, $pwd.Password)
    }

    if ($global:loggingLevel -eq $global:validLoggingLevels.Verbose) {
        Show-Password-Records -password_records:$records
    }

    return $records
}

<#
    .DESCRIPTION
    This function handles writing the content returned from the website, to a
    file named based on the First 5 Characters of the password hash.

    Example:
        for -Password "pa`$`$word", the full hash:
            119e9f64e12b97293a8334ccd162c1245786336d

    The resulting file will be named "119e9.txt"

    .PARAMETER content
    Full content from the website.

    .PARAMETER firstFiveSHAChars
    First 5 chars of the SHA, used as the base file name
#>
function Write-Content-To-File($content, $firstFiveSHAChars) {
    if (-not (Test-Path -Path $ContentRoot)) {
        New-item -path $ContentRoot -ItemType "directory" | Out-Null
    }

    $filename = ("{0}\{1}.txt" -f $ContentRoot, $firstFiveSHAChars)

    Write-Out ("Saving contents (length:{0} bytes) to {1}" `
        -f $content.length, $filename) -level:$global:validLoggingLevels.Verbose

    $content | Out-File -FilePath $filename -Force -Encoding UTF8

    Write-Out ("Wrote {0} bytes to {1}" `
        -f $content.length, $filename) -level:$global:validLoggingLevels.Verbose
}

<#
    .DESCRIPTION
    This function loops through all the given records, calling their toString
    function, and displaying results

    .PARAMETER password_records
    Array of PasswordDetails objects.
#>
function Show-Password-Records($password_records) {
    $recordNum = 1;
    foreach( $pwd in $password_records) {
        Write-Out "[$recordNum] $($pwd.toString())"
        $recordNum++
    }
}

function Get-Current-TimeStamp {
    return  ([datetime]::Now).ToString('yyyy/MM/dd HH:mm:ss')
}

<#
    .DESCRIPTION
    This function handles writing output to the console.
    It follows a clunky log level scheme, but it does the job.

    .PARAMETER Output
    String to send to Write-host

    .PARAMETER level
    Logging level of this output.
    If -LogLevel "Minimum" was specified on the command line, but this
    param is "Normal" or "Verbose", it will be ignored.

    .PARAMETER timestamp
    When $true, the timestamp is added to the output
    When $false, timestamp is not included.
#>
function Write-Out {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Output,

        [Parameter(Mandatory=$false)]
        [int]$level = $global:validLoggingLevels.Normal,

        [Parameter(Mandatory=$false)]
        [bool]$include_timestamp = $true
    )

    if ($level -le $global:loggingLevel) {
        if (($timestamp -eq $true) -and `
            ($level -ne $global:validLoggingLevels.Normal)){
            Write-Host ("[" + (Get-Current-TimeStamp) + "] $Output")
        } else {
            Write-Host ("$Output")
        }
    }
}

try {
    # Just for curious perf measurement.
    $timeStart = Get-Date
    Write-Out "Start Time: $timeStart"

    # Will contain a list of all the passwords checked, that have been pwnd.
    $pwndPasswords = @()

    $global:loggingLevel = $($global:validLoggingLevels.$LogLevel)

    ShowArgs

    # Will contain the list of PasswordDetail objects created that will be
    # checked.
    $listOfPasswords = @()

    # Script was run with -PasswordFile param
    if ("" -ne $PasswordFile) {
        $listOfPasswords = Read-Password-File($PasswordFile)

    # Make sure -Password or -SHA1 is not empty
    } elseif (($Password -eq "") -and ($SHA1 -eq "")) {
        throw "Must provide either -Password or -SHA1 value"

    # Either -Password or -SHA1 hash been passed in.
    } else {

        # -SHA1 was given
        if ($Password -eq "") {
            $passwordHash = $SHA1;

        # -Password was given
        } else {
            $passwordHash = Get-Hash-Of-Password($Password)
        }

        $listOfPasswords += [PasswordDetails]::new($Password, $passwordHash)
    }

    # This will contain just the body of the HTTP Response from the website
    # and will be scanned for hash occurrences.
    $content = ""

    <#
    .SYNOPSIS
        At this point, whether the script was called with an individual
        Password, Hash, or pointed to a file of passwords, we now have an array
        to cycle through, and make the request.
    #>
    foreach($entry in $listOfPasswords) {
        Write-Out "$('-'*80)" `
            -level:$global:validLoggingLevels.Normal -include_timestamp:$false

        Write-Out "Checking entry:`t$($entry.toString())" `
            -level:$global:validLoggingLevels.Normal -include_timestamp:$false

        $content = Check-Website-For-Hash($entry.SHA1Hash)

        # Haven't hit this case yet in the wild yet, but if it happens,
        # the entry will be shown with Black text on Yellow background
        # If $Pretend is specificed, it will always hit this, so factoring
        # that into this condition.
        if (($content -eq "") -and ($Pretend -ne $true)) {
            Write-Out "No results for:" `
                -level:$global:validLoggingLevels.Normal `
                -include_timestamp:$false
            Write-Host "`t$($entry.toString())" -BackgroundColor yellow `
                -ForegroundColor black
            return;
        }

        $contentLines = ($content -split "\n")

        Write-Out ("Received {0} lines" -f $contentLines.length)

        Write-Out ("Checking {0} lines of results for hash: {1} (  {2}  )" -f `
            $contentLines.length, $entry.SHA1Hash, $entry.Password)

        $HashHitCount = (Search-Results-For-Hash -lines:$contentLines `
            -hash:$entry.SHA1Hash)

        # Found a hit amongst the results, output in rude colors.
        if ($HashHitCount -gt 0) {
            $entry.HashHitCount = $HashHitCount
            Write-Out "$('+'*80)" `
                -level:$global:validLoggingLevels.Minimum `
                -include_timestamp:$false
            Write-Host "`t$($entry.toString())" -BackgroundColor red `
                -ForegroundColor black
            Write-Out "$('+'*80)" `
                -level:$global:validLoggingLevels.Minimum `
                -include_timestamp:$false
            $pwndPasswords += $entry

        # Not found, so output as green
        } else {
            Write-Host "`t$($entry.toString())" -BackgroundColor green `
                -ForegroundColor white
        }

        # Show a simple visual of time remaining in the sleep
        # The 'trick' here is to use -NoNewLine and a string that starts with `r
        $sleepCountdown = $RequestSleep
        while( ($sleepCountdown -gt 0) -and `
               ($entry -ne $listOfPasswords[$listOfPasswords.length -1])) {
            Write-host "`rSleeping $sleepCountdown seconds..." -NoNewline
            Start-Sleep -Seconds 1
            $sleepCountdown--
        }
        Write-host "`r`n"
    }

    # Show final list of any passwords that were found.
    if ($pwndPasswords.length -gt 0) {
        Write-Out "$('-'*80)"
        Write-Out ("`tList of passwords found on HaveIBeenPwned.com [{0}]" `
            -f $pwndPasswords.length)
        Write-Out "$('-'*80)"
        foreach($pwnd in $pwndPasswords) {
            Write-Host "$($pwnd.toString())" -BackgroundColor red `
                -ForegroundColor black
        }
    }

} catch [Exception] {
    Write-Out "***********************************"
    Write-Out $_.Exception.Message
    Write-Out "Line: $($_.InvocationInfo.ScriptLineNumber)"
    if ($null -ne $_.Exception.StackTrace) {
        Write-Out $_.Exception.StackTrace
    }
    Write-Out "***********************************"
} finally {
    $timeEnd = Get-Date
    write-Out "End Time: $timeEnd" `
        -level:$global:validLoggingLevels.Minimum -include_timestamp:$false
    Write-out "Elapsed time: $($timeEnd - $timeStart)" `
        -level:$global:validLoggingLevels.Minimum -include_timestamp:$false
    Write-Out "Done." `
        -level:$global:validLoggingLevels.Minimum -include_timestamp:$false
}

