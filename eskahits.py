# -*- coding: utf-8 -*-
#
# Find hints from EskaRock.pl
# URL example:
# http://www.eskarock.pl/index.php?page=new_hits_eska_rock&offset=10&offset=20

from datetime import datetime
from HTMLParser import HTMLParser
import os
import sys
import urllib2

__doc__ = """Usage:

%s N

Print a list of top N hits from www.eskarock.pl.
""" % os.path.basename(sys.argv[0])


class EskaRockHitsHTMLParser(HTMLParser):
    base_url = "http://www.eskarock.pl/index.php?page=new_hits_eska_rock"

    def __init__(self, page_index):
        HTMLParser.__init__(self)
        if page_index == 1:
            self.url = "%s&offset=60&offset=0" % self.base_url
        else:
            offset = (page_index-1)*10
            self.url = "%s&offset=0&offset=%d" % (self.base_url, offset)
        self._hits = []
        self._inside_hits_table = False
        self._table_counter = 0
        self._hits_table_level = None
        self._inside_hit_name = False

        f = urllib2.urlopen(self.url)
        self.feed(f.read())
        f.close()

    def handle_starttag(self, tag, attrs):
        if tag == "h4":
            self._inside_hit_name = True
        if tag == "table":
            if ("class", "zajawka2") in attrs:
                self._inside_hits_table = True
                self._hits_table_level = self._table_counter
            self._table_counter += 1

    def handle_endtag(self, tag):
        if tag == "h4":
            self._inside_hit_name = False
        if tag == "table":
            self._table_counter -= 1
            if self._table_counter == self._hits_table_level and self._inside_hits_table:
                self._inside_hits_table = False

    def handle_data(self, data):
        if self._inside_hits_table and self._inside_hit_name:
            self._hits.append(data)

    @property
    def hits(self):
        return [" ".join(item.strip() for item in self._hits[i:i+3]) for i in xrange(0, len(self._hits), 3)]


def top_hits(count=10, max_pages=32):
    next_page = 0
    while count > 0:
        next_page += 1
        if next_page > max_pages:
            break
        parser = EskaRockHitsHTMLParser(next_page)
        hits = parser.hits
        for hit in hits[:count]:
            yield hit
        count -= len(hits)


def print_top_hits(count=10, max_pages=32):
    counting_width = len(str(count))
    print "# Top %d hits from EskaRock.pl" % count
    print "# Retrieved %s" % datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    print
    for i, hit in enumerate(top_hits(count, max_pages)):
        print "%*d. %s" % (counting_width, i + 1, hit)


if __name__ == "__main__":
    if sys.argv[1:] and sys.argv[1].isdigit():
        print_top_hits(int(sys.argv[1]))
    else:
        print __doc__
