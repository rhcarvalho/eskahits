# -*- coding: utf-8 -*-
#
# Find hits from EskaRock.pl
# URL example:
# http://www.eskarock.pl/index.php?page=new_hits_eska_rock&offset=10&offset=20

from datetime import datetime
import htmlentitydefs
from HTMLParser import HTMLParser
import os
import re
import sys
from threading import Thread
import urllib2

__doc__ = """Usage:

%s N

Print a list of top N hits from www.eskarock.pl.
""" % os.path.basename(sys.argv[0])


class EskaRockHitsFetcher(HTMLParser, Thread):

    """Parser to fetch top hits from EskaRock.pl."""

    base_url = "http://www.eskarock.pl/index.php?page=new_hits_eska_rock"
    hits_per_page = 10

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

        self._inside_hits_table = False
        self._hits_table_level = None
        self._table_counter = 0

    def run(self):
        f = urllib2.urlopen(self.url)
        try:
            self.feed(f.read())
        finally:
            f.close()

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            if ("class", "zajawka2") in attrs:
                self._inside_hits_table = True
                self._hits_table_level = self._table_counter
            self._table_counter += 1
        elif self._inside_hits_table and tag == "h4":
            self._inside_hit_name = True
            self._current_hit = []

    def handle_endtag(self, tag):
        if tag == "table":
            self._table_counter -= 1
            if self._table_counter == self._hits_table_level and self._inside_hits_table:
                self._inside_hits_table = False
        elif self._inside_hits_table and tag == "h4":
            self._inside_hit_name = False
            # Glue together text matched by handle_data, handle_charref and
            # handle_entityref, and strip extra whitespace.
            hit = "".join(self._current_hit).strip()
            # Replace mutiple spaces by a single space: "My  hit" -> "My hit"
            hit = re.sub("\s{1,}", " ", hit)
            self.hits.append(hit)

    def handle_data(self, data):
        if self._inside_hits_table and self._inside_hit_name:
            self._current_hit.append(data)

    def handle_charref(self, name):
        if self._inside_hits_table and self._inside_hit_name:
            if name.isdigit():
                name = int(name)
            name = htmlentitydefs.codepoint2name.get(name, "")
            char = htmlentitydefs.entitydefs.get(name, "")
            self._current_hit.append(char)

    def handle_entityref(self, name):
        if self._inside_hits_table and self._inside_hit_name:
            char = htmlentitydefs.entitydefs.get(name, "")
            self._current_hit.append(char)

# timeit results
# repeat [time in seconds]
# 23 [12.856124820919772, 10.895285955552382, 9.3024210784356]
# 50 [18.995205638917597, 17.73981352251268, 16.42225731626646]
# 320 [102.42998471273869, 107.60854448272762, 108.65786591803024]
def top_hits(count=10, max_pages=32):
    """Generate lazy sequence of top hits."""
    next_page = 0
    while count > 0:
        next_page += 1
        if next_page > max_pages:
            break
        parser = EskaRockHitsFetcher(next_page)
        parser.run()
        hits = parser.hits
        for hit in hits[:count]:
            yield hit
        count -= len(hits)

# timeit results
# repeat [time in seconds]
# 23 [4.351284881378983, 3.558788820220083, 4.224391989524346]
# 50 [4.3671874518808504, 4.418607959969794, 4.7456087619042915]
# 320 [15.237602967280825, 14.143372584187725, 15.102017524301328]
def top_hits_p(count=10, max_pages=32):
    """Generate lazy sequence of top hits.
    
    Runs parallel threads to download multiple pages at a time.
    
    """
    total_pages = ((count - 1) / EskaRockHitsFetcher.hits_per_page) + 1
    pages = []
    
    for page in xrange(1,  total_pages + 1):
        fetcher_thread = EskaRockHitsFetcher(page)
        pages.append(fetcher_thread)
        fetcher_thread.start()
    
    for page in pages:
        page.join()
        hits = page.hits
        for hit in hits[:count]:
            yield hit
        count -= len(hits)


def print_top_hits(count=10, max_pages=32):
    """Print top hits as they are fetched from EskaRock.pl."""
    print "# Top %d hits from EskaRock.pl" % count
    print "# Retrieved %s" % datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    print
    counting_width = len(str(count))
    for i, hit in enumerate(top_hits_p(count, max_pages)):
        print "%*d. %s" % (counting_width, i + 1, hit)


def main():
    if sys.argv[1:] and sys.argv[1].isdigit():
        print_top_hits(int(sys.argv[1]))
    else:
        print __doc__

if __name__ == "__main__":
    from timeit import repeat
    print repeat("main()", "from __main__ import main", repeat=3, number=1)