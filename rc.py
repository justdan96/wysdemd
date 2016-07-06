#!/bin/python
# coding=utf8

import os
#rename to warlock
import warlock
import time

class bcolors:
    HEADER = '\033[1;94m'
    ENDC = '\033[0;0m'
    BOLD = '\033[0;91m'

# Python replacement for the heavily-edited minirc RC script

print " wysdemd     ____       "
print "            /_ _\`¬     "
print "  /\        |^L^| /     "
print "=(++)=      | 0 | L,    "
print "  ||      ,-'\ /'-, \,  "
print "  ||     /    '    \ |  "
print "---"
print "========================"
print "   DRUID                "
print "========================"

print bcolors.HEADER + "[DRUID]" + bcolors.BOLD + " mounting API filesystem..." + bcolors.ENDC
os.system("mountpoint -q /proc|| mount -t proc proc /proc -o nosuid,noexec,nodev")
os.system("mountpoint -q /sys || mount -t sysfs sys /sys -o nosuid,noexec,nodev")
os.system("mountpoint -q /run || mount -t tmpfs run /run -o mode=0755,nosuid,nodev")
os.system("mountpoint -q /dev || mount -t devtmpfs dev /dev -o mode=0755,nosuid")
os.system("mkdir -p /dev/pts /dev/shm")
os.system("mountpoint -q /dev/pts || mount -t devpts devpts /dev/pts -o mode=0620,gid=5,nosuid,noexec")
os.system("mountpoint -q /dev/shm || mount -t tmpfs shm /dev/shm -o mode=1777,nosuid,nodev")

print bcolors.HEADER + "[DRUID]" + bcolors.BOLD + " setting up loopback device..." + bcolors.ENDC
os.system("/usr/sbin/ip link set up dev lo")

print bcolors.HEADER + "[DRUID]" + bcolors.BOLD + " initializing udev..." + bcolors.ENDC
os.system("/usr/lib/systemd/systemd-udevd --daemon")
os.system("/usr/bin/udevadm trigger --action=add --type=subsystems")
os.system("/usr/bin/udevadm trigger --action=add --type=devices")

print bcolors.HEADER + "[DRUID]" + bcolors.BOLD + " setting hostname..." + bcolors.ENDC
os.system("cat /etc/hostname >| /proc/sys/kernel/hostname")

print bcolors.HEADER + "[DRUID]" + bcolors.BOLD + " mounting..." + bcolors.ENDC
os.system("mount -a")
os.system("mount -o remount,rw /")

print bcolors.HEADER + "[DRUID]" + bcolors.BOLD + " start the syslog daemon" + bcolors.ENDC
os.system("python /opt/wysdemd/dshimv /lib/systemd/system/rsyslog.service start")

print bcolors.HEADER + "[DRUID]" + bcolors.BOLD + " start the dbus daemon" + bcolors.ENDC
os.system("mkdir -p /run/dbus")
os.system("/usr/bin/dbus-uuidgen --ensure")
os.system("/usr/bin/dbus-daemon --system")

print bcolors.HEADER + "[DRUID]" + bcolors.BOLD + " starting network..." + bcolors.ENDC
os.system("/etc/init.d/network start")

time.sleep(15)
    
print bcolors.HEADER + "[DRUID]" + bcolors.BOLD + " starting daemons..." + bcolors.ENDC
warlock.start_all()
