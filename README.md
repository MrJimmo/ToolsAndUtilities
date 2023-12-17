# Tools And Utilities
Various tools and utilities.

## [Mortgage Payments](https://mrjimmo.com/ToolsAndUtilities/MortgagePayments/MortgagePayments.html)
A No-frills page born from wanting to generate the entire payment schedule for a loan, and produce details that matched up with the statements I get from my bank.

## [Generate Calendar](https://mrjimmo.com/ToolsAndUtilities/GenerateCalendar/GenerateCalendar.html)
I used to get those handy little small calendars from places like Les Schwab.

I whipped this page together to generate a year in the format I like the most.  I then use a paper cutter to cut them out and then staple them to some thicker cardboard, so I end up with the current year including the holidays highlighted accurately.

Supported Keyboard shortcuts:

|Key|Action|
|-|-|
|R|Reset to current year|
|O|Toggle Horizontal/Vertical orientation|
|H|Set to Horizontal orientation|
|V|Set to Vertical orientation|
|[Left/Right]Arrow|Back/Forward 1 year|
|Control+[Left/Right]Arrow|Back/Forward by 5 years at a time|
|Shift+[Left/Right]Arrow|Back/Forward by 10 years at a time|

Supports "year" and "horizontal" URL params.

Example: [GenerateCalendar.html?year=2020&horizontal](https://mrjimmo.com/ToolsAndUtilities/GenerateCalendar/GenerateCalendar.html?year=2020&horizontal)


## [HaveIBeenPwned Utility](https://github.com/MrJimmo/ToolsAndUtilities/tree/main/HaveIBeenPwned)
This Powershell script handles calling the [HaveIBeenPwned](https://haveibeenpwned.com/) api to check for password occurrences in security breaches.

Handles simple Password (or Hash) query, or processes an file input.

See more info in the [Readme.md](https://github.com/MrJimmo/ToolsAndUtilities/tree/main/HaveIBeenPwned/Readme.md)

Example:

` .\HaveIBeenPwned.ps1 -Password "pa$$word" -LogLevel Verbose`
