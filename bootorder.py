#!/usr/bin/env python

from funcs import (check_env_file, check_for_file, check_for_service,
check_for_specifiers, clear_semicolon_comment, replace_specifiers, 
create_config, tree, dicts, tree_add, tree_set, toposort2)

import ConfigParser
import sys, os
from types import StringType
import tempfile
import re
import pprint

try:
    from functools import reduce
except:
    pass

# -------------------------------------------
# 
# subroutine section
# 
# -------------------------------------------

def read_require_fields_from_target_file(fil):
    config, prog, is_service = create_config(fil)
    
    if config == 1:
        # print 'Error initialising target file: ' + fil
        return [1,1]
	
    options = ['After', 'Requires']
    
    requires = set()
    
    for option in options:
        if config.has_option("Unit", option):
            after_services_str = config.get("Unit", option)[0]
            
            for unit in after_services_str.split(" "):
                if unit != "rescue.target" and unit != "rescue.service" and unit != "emergency.target" and unit != "emergency.service":
                   requires.add(unit)
                   # required_str += unit + " "
                
    # print prog + ": "
    return requires, is_service
    
def read_wants_from_target_file(fil):
    config, prog, is_service = create_config(fil)
    
    if config == 1:
        # print 'Error initialising target file: ' + fil
        return 1
    
    wants_path = '/etc/systemd/system/' + prog + '.target.wants/'

    options = ['Wants']
    
    wants = set()

    for option in options:
        if config.has_option("Unit", option):
            after_services_str = config.get("Unit", option)[0]

            for unit in after_services_str.split(" "):
                # ignore any references to rescue or emergency
                if unit != "rescue.target" and unit != "rescue.service" and unit != "emergency.target" and unit != "emergency.service":
                    wants.add(unit)
        else:
            break
    
    if not is_service and os.path.isdir(wants_path):
       wantsfiles = [ f for f in os.listdir(wants_path) if os.path.isfile(os.path.join(wants_path,f)) ]
       # add list to set
       wants |= set(wantsfiles)
    
    # special case for "default.target"
    if not is_service and prog == "default":
       # get the real name of the target, i.e. graphical
       real_target = os.path.basename(os.readlink('/etc/systemd/system/default.target')).replace(".target", "")
       
       # create the wants path for the real target, create the list of files and append them to the wants set
       real_wants_path = '/etc/systemd/system/' + real_target + '.target.wants/'
       
       if os.path.isdir(real_wants_path):
           real_wantsfiles = [ f for f in os.listdir(real_wants_path) if os.path.isfile(os.path.join(real_wants_path,f)) ]
           wants |= set(real_wantsfiles)
    
    return wants

def process_services(target):
    reqs, is_service = read_require_fields_from_target_file(target)
    if reqs != 1 and reqs:
            for reqser in reqs:
                # service = 'display-manager'
                # reqser = ['systemd-user-sessions.service', 'getty@tty1.service', 'plymouth-quit.service', 'livesys-late.service']
                process_services(reqser)
            if target not in boot_services:
                boot_services[target] = reqs

def recurse_required_services(requires, required_services):
    # print 'requires: ',
    # print requires
    if requires != 1:
        for req in requires:
            if req.split('.')[1] == 'target':
                nreqs, is_service = read_require_fields_from_target_file(req)
                recurse_required_services(nreqs, required_services)
            if req.split('.')[1] == 'service':
                required_services.add(req)

def process_targets(target, target_str):
    requires, is_service = read_require_fields_from_target_file(target)
    
    # print 'THIS TARGET IS = ' + target
    
    # if there are actually some requires
    if requires != 1:
        # add this particular target 
            
        # print requires
        for reqtar in requires:
            # add the requirements to the tree
            target_path = target_str + '>' + reqtar
            tree_add(boot_targets, target_path.split('>'))
            
            # if the target isn't in our set of all targets
            # parse the target as well
            if reqtar not in all_boot_targets:
                all_boot_targets.add(reqtar)
                process_targets(reqtar, target_path)
        
        # find the wants and process those targets too
        wants = read_wants_from_target_file(target)
        if wants and wants != 1:
            for wantar in wants:
                # print 'wantar: ' + wantar
                wantar_path = target_str + '>' + wantar
                process_targets(wantar, wantar_path)
            # tree_set(boot_targets, target_str.split('>'), wants)
        
        # if this current target is a service, add it to the list of boot services
        # making sure we add all the service requirements as dependencies 
        if is_service == True:
            if target not in boot_services:
                boot_reqservs = set()
                recurse_required_services(requires, boot_reqservs)
                boot_services[target] = boot_reqservs

# -------------------------------------------
# 
# main section
# 
# -------------------------------------------

global boot_targets, all_boot_targets, default_target, boot_services

boot_targets = tree()

all_boot_targets = set()

default_target = 'default.target'

all_boot_targets.add(default_target)

boot_targets[default_target]
boot_targets_str = default_target

boot_services = {}

process_targets(default_target, default_target)

#pprint.pprint(dicts(boot_targets))

#print "BOOT TARGETS:"
#pprint.pprint(dicts(boot_targets))
# print boot_targets

#print "ALL BOOT TARGETS:"
#print all_boot_targets

#print "BOOT SERVICES:"
#pprint.pprint(boot_services)

#print "SORTED BOOT SERVICES:"
print (' '.join( toposort2(boot_services) ))

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

