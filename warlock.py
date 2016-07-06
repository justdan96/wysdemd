#!/usr/bin/env python

from funcs import (wyslog, check_env_file, check_for_file, check_for_service,
check_for_specifiers, clear_semicolon_comment, replace_specifiers, 
create_config, tree, dicts, tree_add, tree_set, toposort2, parse_envfile)

import ConfigParser
import sys, os
from types import StringType
import re
import pprint
import pwd
import grp
import shlex
import subprocess

try:
    from functools import reduce
except:
    pass

class bcolors:
    HEADER = '\033[1;94m'
    ENDC = '\033[0;0m'
    BOLD = '\033[0;91m'
    
global initialised
initialised = False

# -------------------------------------------
# 
# subroutine section
# 
# -------------------------------------------

# perform any start actions, whether pre, actual or post
def _start(action, config, fil):
    environc = os.environ.copy()
    
    unitname = os.path.splitext(os.path.basename(fil))[0]
    
    # create a path to a PID file, in case we need it
    pid_fname = '/var/run/{0}.pid'.format(unitname)
    ignore_errors = False
    
    # check that the option for this action exists
    if config.has_option("Service", action):
        
        # set any environment variables as per the config
        if config.has_option("Service", "Environment"):
            for setenviron in config.get("Service", "Environment"):
                environc[setenviron.split('=')[0]] = setenviron.split('=')[1]
        
        # if there is an environment file, parse any variables from it into the environment
        if config.has_option("Service", "EnvironmentFile"):
            for setenvfile in config.get("Service", "EnvironmentFile"):
                setenvfile = re.sub("^-", "", setenvfile)
                environc = parse_envfile(setenvfile, environc)
    
        for start in config.get("Service", action):
        #start = config.get("Service", action)[0]
            
            # if the action starts with a "-", we need to ignore errors
            if start.startswith("-"):
                ignore_errors = True
                start = re.sub("^-", "", start)
            
            startaction = os.path.expandvars(start)
            startaction = shlex.split(startaction, comments=True)

            try:
                proc = subprocess.Popen(startaction, env=environc, preexec_fn=set_usr_grp(config, environc))
            except:
                if ignore_errors == False:
                    wyslog(start + " encountered an error - we will bail out")
                    return False
                else:
                    wyslog(start + " encountered an error - but we will ignore it")
            
            # the actual start action may need us to set a PID file, or wait for completion
            if action == "ExecStart":
                if not config.has_option('Service', 'PidFile'):
                    with open(pid_fname, 'w') as pid_file:
                        pid_file.write(str(proc.pid))
                
                # oneshot and forking both expect the process that gets called to
                # finish before we continue. We can do that for them.
                if config.has_option("Service", "Type"):
                    if config.get("Service", "Type")[0] in ('oneshot', 'forking'):
                        proc.wait()
    else:
        wyslog("Action " + action + " does not exist for " + unitname)
        return False
    return True

# start the specified service
def start_service(fil):
    config, prog, is_service = create_config(fil)
    
    unitname = os.path.splitext(os.path.basename(fil))[0]
    
    if config == 1:
        wyslog('Error initialising target file: ' + fil)
        return [1,1]
	
    print bcolors.HEADER + "[WARLOCK]" + bcolors.BOLD + " Starting " + unitname + "..." + bcolors.ENDC
    actions = ['ExecStartPre', 'ExecStart', 'ExecStartPost']
    for action in actions:
        if config.has_option("Service", action):
            print "starting action " + action
            if _start(action, config, fil):
                print action + " completed successfully for " + unitname
            else:
                print action + " failed for " + unitname        

    print bcolors.HEADER + "[WARLOCK]" + bcolors.BOLD + " Started: " + unitname + bcolors.ENDC
    wyslog("Started: " + unitname)
    return
        
# set the environment for the process with the user and group from the unit file
def set_usr_grp(config, environ):
    def set_ids():
        if config.has_option("Service", "User"):
            user = config.get("Service", "User")[0]
            if user.isdigit():
                pwd_entry = pwd.getpwuid(user)
            else:
                pwd_entry = pwd.getpwnam(user)
            os.environ['HOME'] = pwd_entry.pw_dir
            os.environ['LOGNAME'] = pwd_entry.pw_name
            os.environ['USER'] = pwd_entry.pw_name
            os.environ['SHELL'] = pwd_entry.pw_shell
            os.setuid(pwd_entry.pw_uid)
            
        if config.has_option("Service", "Group"):
            group = config.get("Service", "Group")[0]
            if group:
                grp_entry = grp.getgrgid(int(group))
            else:
                grp_entry = grp.getgrgid(pwd_entry.pw_gid)
            os.setgid(grp_entry.gr_gid)
    
    return set_ids

# return the dependencies for a target file
def read_require_fields_from_target_file(fil):
    config, prog, is_service = create_config(fil)
    
    if config == 1:
        wyslog('Error initialising target file: ' + fil)
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
    
# read the wants from a target file, from the unit file and from the filesystem
def read_wants_from_target_file(fil):
    config, prog, is_service = create_config(fil)
    
    if config == 1:
        wyslog('Error initialising target file: ' + fil)
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

# process each service file and their require field, add each service and their dependencies to the list
def process_services(target):
    reqs, is_service = read_require_fields_from_target_file(target)
    if reqs != 1 and reqs:
            for reqser in reqs:
                # service = 'display-manager'
                # reqser = ['systemd-user-sessions.service', 'getty@tty1.service', 'plymouth-quit.service', 'livesys-late.service']
                process_services(reqser)
            if target not in boot_services:
                boot_services[target] = reqs

# recursively add required services, using different methods based on if it is a target or a service
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

# the main function, this actually starts the generation of the list of units and their dependencies
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

# initialise global variables, create the actual boot order in tbs
def init():
    global boot_targets, all_boot_targets, default_target, boot_services, tbs

    boot_targets = tree()
    all_boot_targets = set()
    default_target = 'default.target'
    all_boot_targets.add(default_target)
    boot_targets[default_target]
    boot_services = {}
    process_targets(default_target, default_target)
    tbs = toposort2(boot_services)
    initialised = True
    return

# start all the services in the generated boot order
def start_all():
    if initialised == False:
        init()
    print "========================"
    print "   WARLOCK              "
    print "========================"
    for item in ' '.join(tbs).split():
        start_service(item)
        time.sleep(15)

def main(argv=None):
    argv = argv or sys.argv
    usage = ('Run without arguments to print boot order, or use argument start or stop to start all services')
    
    init()

    if len(argv) == 1:
        print ' '.join(tbs)
        exit(0)
    
    _, action = argv
    if action == 'start':
        # print out the boot services, one on each line
        start_all()
    else:
        print >> sys.stderr, usage
        sys.exit(2)

if __name__ == '__main__':
    main()
