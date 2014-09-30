#!/bin/sh

default=`readlink /etc/systemd/system/default.target`

echo "Default Target: $default"

cat $default

exit

