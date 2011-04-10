#!/bin/sh
cmd="/usr/local/bin/python2.7 /home/rodolfo/eskahits/eskahits.py 400"
hits="/home/rodolfo/eskahits_log/hits"
$cmd > $hits
/home/rodolfo/bin/bzr ci --unchanged -m "Hits update - $(date)" $hits
