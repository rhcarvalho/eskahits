#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Find hits from EskaRock.pl
# URL example:
# http://www.eskarock.pl/index.php?page=new_hits_eska_rock&offset=10

from datetime import datetime
import htmlentitydefs
from HTMLParser import HTMLParser
import os
import re
from sendmail import sendmail
import sys
from threading import Thread
import time
import urllib2

__doc__ = """Usage:

%s N

Print a list of top N hits from www.eskarock.pl.
""" % os.path.basename(sys.argv[0])


class EskaRockHitsFetcher(HTMLParser, Thread):

    """Parser to fetch top hits from EskaRock.pl."""

    base_url = "http://www.eskarock.pl/index.php?page=new_hits_eska_rock"
    hits_per_page = 20

    def __init__(self, page_index):
        """Fetch hits from the given page.

        Inspect the `hits` property which contains the hits found in that page.
        """
        Thread.__init__(self)
        HTMLParser.__init__(self)

        offset = (page_index - 1) * self.hits_per_page
        self.url = "%s&offset=%d" % (self.base_url, offset)

        self.hits = []

        self._inside_hit_name = False
        self._current_hit = None

        self._inside_hits_div = False
        self._hits_div_level = None
        self._div_counter = 0

    def run(self):
        f = urllib2.urlopen(self.url)
        encoding = f.headers['content-type'].split('charset=')[-1]
        try:
            self.feed(unicode(f.read(), encoding))
        finally:
            f.close()

    def handle_starttag(self, tag, attrs):
        if tag == "div":
            if ("id", "kontener3") in attrs:
                self._inside_hits_div = True
                self._hits_div_level = self._div_counter
            self._div_counter += 1
        elif self._inside_hits_div and tag == "h4":
            self._inside_hit_name = True
            self._current_hit = []

    def handle_endtag(self, tag):
        if tag == "div":
            self._div_counter -= 1
            if self._div_counter == self._hits_div_level and self._inside_hits_div:
                self._inside_hits_div = False
        elif self._inside_hits_div and tag == "h4":
            self._inside_hit_name = False
            # Glue together text matched by handle_data, handle_charref and
            # handle_entityref, and strip extra whitespace.
            hit = "".join(self._current_hit).strip()
            # Replace mutiple spaces by a single space: "My  hit" -> "My hit"
            hit = re.sub("\s{1,}", " ", hit)
            # Encode hit into a UTF-8 bytestream
            hit = hit.encode("utf-8")
            self.hits.append(hit)

    def handle_data(self, data):
        if self._is_parsing_hit:
            self._current_hit.append(data)

    def handle_charref(self, name):
        if self._is_parsing_hit:
            if name.isdigit():
                name = int(name)
            name = htmlentitydefs.codepoint2name.get(name, "")
            char = htmlentitydefs.entitydefs.get(name, "")
            self._current_hit.append(char)

    def handle_entityref(self, name):
        if self._is_parsing_hit:
            char = htmlentitydefs.entitydefs.get(name, "")
            self._current_hit.append(char)

    @property
    def _is_parsing_hit(self):
        return self._inside_hits_div and self._inside_hit_name


def top_hits(count=10):
    """Generate lazy sequence of top hits.

    Runs parallel threads to download multiple pages at a time.
    """
    max_pages = 40 # limit the number of concurrent threads
    total_pages = ((count - 1) / EskaRockHitsFetcher.hits_per_page) + 1

    for first_page in xrange(1, total_pages + 1, max_pages):
        pages = []
        last_page = min(first_page + max_pages - 1, total_pages)
        for page in xrange(first_page, last_page + 1):
            fetcher_thread = EskaRockHitsFetcher(page)
            # Do NOT wait for thread to terminate when main thread is done
            fetcher_thread.daemon = True
            pages.append(fetcher_thread)
            fetcher_thread.start()

        for page in pages:
            page.join()
            hits = page.hits
            if not hits:
                # If this page has no hits, assume next pages won't have as well.
                # Ignore all of the next pages and terminate.
                return
            for hit in hits[:count]:
                yield hit
            count -= len(hits)


def print_top_hits(count=10):
    """Print top hits as they are fetched from EskaRock.pl."""
    print "# Top %d hits from EskaRock.pl" % count
    print "# Retrieved %s" % datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    print
    counting_width = len(str(count))
    i = 0
    for i, hit in enumerate(top_hits(count), 1):
        print "%*d. %s" % (counting_width, i, hit)
    return i


def send_alert_email(subject, text):
    from_addr = 'eskahits@rodolfocarvalho.net'
    to_addrs = (
        'rhcarvalho+eskahits@gmail.com',
    )
    sendmail(from_addr, to_addrs, subject, text)


def main():
    try:
        n = int(sys.argv[1])
        assert n > 0
        
        t0 = time.time()
        count = print_top_hits(n)
        t1 = time.time()
        
        if count == 0:
            send_alert_email("No hits found!",
                "Check for changes in "
                "http://www.eskarock.pl/index.php?page=new_hits_eska_rock")
        
        print
        print "# Fetched %d hits in %.2f seconds." % (count, t1 - t0)
    except (IndexError, ValueError, AssertionError):
        print __doc__
    except:
        import traceback
        send_alert_email("Unexpected error on Eskahits!",
                "Details:\n\n%s" % traceback.format_exc())
        raise

if __name__ == "__main__":
    main()
