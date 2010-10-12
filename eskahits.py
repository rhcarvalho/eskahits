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
import urllib2

__doc__ = """Usage:

%s N

Print a list of top N hits from www.eskarock.pl.
""" % os.path.basename(sys.argv[0])


class EskaRockHitsHTMLParser(HTMLParser):

    """Parser to fetch top hits from EskaRock.pl."""

    base_url = "http://www.eskarock.pl/index.php?page=new_hits_eska_rock"
    items_per_page = 10

    def __init__(self, page_index):
        """Fetch hits from the given page.

        Inspect the `hits` property which contains the hits found in that page.

        """
        HTMLParser.__init__(self)
        offset = (page_index - 1) * self.items_per_page
        self.url = "%s&offset=%d" % (self.base_url, offset)

        self._hits = []

        self._inside_hit_name = False
        self._current_hit = None

        self._inside_hits_table = False
        self._hits_table_level = None
        self._table_counter = 0

        f = urllib2.urlopen(self.url)
        self.feed(f.read())
        f.close()

    @property
    def hits(self):
        return self._hits

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
            self._hits.append(hit)

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


def top_hits(count=10, max_pages=32):
    """Generate lazy sequence of top hits."""
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
    """Print top hits as they are fetched from EskaRock.pl."""
    print "# Top %d hits from EskaRock.pl" % count
    print "# Retrieved %s" % datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    print
    counting_width = len(str(count))
    for i, hit in enumerate(top_hits(count, max_pages)):
        print "%*d. %s" % (counting_width, i + 1, hit)


if __name__ == "__main__":
    if sys.argv[1:] and sys.argv[1].isdigit():
        print_top_hits(int(sys.argv[1]))
    else:
        print __doc__
