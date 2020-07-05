# scdc-planning-rss
RSS feed provider for SCDC planning application site

The South Cambridgeshire District Council planning application site at
https://applications.greatercambridgeplanning.org/online-applications/search.do
is useful but doesn't provide an RSS feed of recent applications. This
CGI script fills that gap.

The script should be installed in a web server of your choice, and
called from your RSS reader with the parish of interest as a
parameter:

http://your.web.server/cgi/scdcplanningrss.cgi?parish=Pampisford

Occasionally SCDC change the site layout which breaks this script -
reports welcome.

Dave Holland <dave@biff.org.uk>
