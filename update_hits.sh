#!/bin/sh
python2.7 eskahits.py 400 > ../eskahits_log/hits
bzr ci --unchanged -m "Hits update - $(date)" ../eskahits_log/hits
