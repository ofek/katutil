# katutil
Script to refresh and/or edit all of a user's torrents' trackers on KickassTorrents

Until the official KickassTorrents site feature is implemented (not for a long time imo), this is
a script I wrote that allows each of us to refresh or edit all of the trackers on all of our
torrents in one go whenever we want!

Only 4 quick steps to set the script up:

1. Go to http://phantomjs.org/download.html. It's basically an invisible web browser.
  Windows & OS X users extract phantomjs executable from "bin" folder in .zip to somewhere and note its path.
  Linux users build from source.
2. Go to https://www.python.org/downloads/.
  The latest version is recommended as that's all I've tested it on, but 2.x may work.
  Be sure to enable/check "pip" option on install menu.
3. Open terminal (cmd on windows) and type "pip install selenium"
4. Download https://github.com/Ofekmeister/kat-tracker-updater/archive/master.zip.
  Extract the "tracker_updater.py" file to somewhere.

Now you're all set! There are 2 ways to run it:

1. If you are confident your newer version of Python is set up ok just double
click the .py like you would a program. The script will prompt you for your
username, etc. and save info for next time.

2. To run it in terminal/cmd type "path/to/python path/to/tracker_updater.py" (without quotes).
The script accepts an optional argument where you can specify the timeout between requests if
connectivity issues to KAT arise (default is 20) i.e. "path/to/python path/to/tracker_updater.py 32"
would set the timeout to 32. I personally have never had an issue with the default I set, but just
in case you do, you have the ability to increase it.


Mega note: I'm pretty sure in the background KAT has a process queue like Celery that
handles certain requests. If a dev says they don't, everyone should uncomment the
"time.sleep(10)" line in the refreshTrackers and editTrackers functions in the .py file to
add a 10 second delay between refresh and edit requests.


Please tell me if this works for you or if you encounter any issues. I'll fix bugs prompty.
I'll put this in tutorials when I hear this works for most of you \(^_*)/
