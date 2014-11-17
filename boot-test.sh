#!/bin/bash

for dmn in `python /opt/wysdemd/bootorder.py`; do
   logger -s -p local7.notice "I am starting $dmn now!"
   /usr/bin/python /opt/wysdemd/dshimv /lib/systemd/system/$dmn status
   read
   /usr/bin/python /opt/wysdemd/dshimv /lib/systemd/system/$dmn start
done
