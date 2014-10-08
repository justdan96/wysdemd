#!/usr/bin/python

import wysdemd-headers.py

import ConfigParser
import sys, os
from types import StringType
import tempfile
import re

def read_require_fields_from_target_file(fil):
    config, prog
    config = ConfigParser.ConfigParser(None, newdict)

    if fil[0:20] != '/etc/systemd/system/' and fil[0:20] != '/lib/systemd/system/':
        fil = '/etc/systemd/system/' + fil
    if not os.path.isfile(fil):
        fil = fil.replace("/etc/", "/lib/")
        if not os.path.isfile(fil):
           print "Cannot find file!"
           return
    prog = (fil.split('/')[-1]).split('.')[0]
    check_for_file(fil)
    check_for_specifiers(fil, config, prog)



#boot_targets = new Tree()
#boot_targets.add(default_target)

#all_boot_targets = new Set()
#all_boot_targets.add(default_target)

#boot_services = new Set()

#process_targets(default_target)

#topological_sort(boot_services)

#def process_targets(target):
   #requires = read_require_fields_from_target_file(target)
   #for reqtar in requires:
      ## add a sub-leaf "reqtar" to leaf "target" 
      #boot_targets.add(target.reqtar)
      #if reqtar not in all_boot_targets:
         #all_boot_targets.add(reqtar)
         #process_targets(target + '.' + reqtar)
   
   #wants = read_wants_from_target(target)
   #for wantar in wants:
      #process_services(wantar)

#def process_services(service):
   #reqs = read_require_fields_from_service_file(service)
   #for reqser in reqs:
      ## service = 'display-manager'
      ## reqser = ['systemd-user-sessions.service', 'getty@tty1.service', 'plymouth-quit.service', 'livesys-late.service']
      #process_services(reqser)
   #if service not in boot_services:
      #boot_services.add(service, reqs)
   

#boot_targets.print()

