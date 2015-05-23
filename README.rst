=======
katutil
=======

- Script to refresh and/or edit all of a user's torrents' trackers on KickassTorrents
- More features coming soon, and requests are welcome!

Installation:
-------------

1. Go to https://www.python.org/downloads/. (Linux/Mac can probably skip this)
The latest version is recommended, but 2.x will work. Be sure to enable/check
"pip" option on install menu.

2. Run cmd on Windows as administrator (Linux/Mac just open terminal) and
type (Linux/Mac need "sudo" in front):

"pip install https://github.com/Ofekmeister/katutil/archive/master.zip"

Great, now you have the software! Here's what to do now:

3. In same cmd/terminal, type (Linux/Mac need "sudo" in front):

"katutil --install"

this will start an automatic install of PhantomJS which is needed to non-intrusively
interact with websites, otherwise this script would have to take over a firefox/chrome
window. If it should somehow fail, download it yourself at http://phantomjs.org/download.html

Now you're all set! From now on just open a normal cmd/terminal and type:

"katutil"

and simply follow the prompts. It will save all info except your password in a temp file for
easier repeat use. If you or KAT is experiencing connectivity issues and the requests keep
timing out or failing, try running it with an increased timeout per request like this:

"katutil -t 30"

The default is 20 seconds.

If you have everything set up but you need to update this script
when new features are added or bugs are fixed run cmd on Windows as administrator
(Linux/Mac just open terminal) again and do (Linux/Mac need "sudo" in front):

"katutil --save"

This attempts to save the PhantomJS executable in a temp location to avoid having to
reinstall that. Then repeat step 2 & 3.


Please tell me if this works for you or if you encounter any issues. I'll fix bugs promptly.
I'll put this in tutorials when I hear this works for most of you \(^_*)/
