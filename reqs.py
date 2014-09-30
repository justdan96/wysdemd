#!/usr/bin/python

'''
@author: Akhil Vij
'''

import ConfigParser
import sys, os
from types import StringType
import tempfile
import re

class newdict(dict):
    def __setitem__(self, key, value):
        if key in self:
            if type(value) is not StringType:
                dict.__setitem__(self, key, self[key] + value)
        else:
            if type(value) is StringType:
                temp_list = []
                temp_list.append(value)
                value = temp_list
            dict.__setitem__(self, key, value)

# Function to initiate the parser, returns with error code 2 if the incorrect
# arguments are provided to the script

def parser_init():
    global config, prog, fil
    config = ConfigParser.ConfigParser(None, newdict)

    if len(sys.argv) == 2:
        fil = sys.argv[1]
        if fil[0:20] != '/etc/systemd/system/' and fil[0:20] != '/lib/systemd/system/':
            fil = '/etc/systemd/system/' + fil
        if not os.path.isfile(fil):
            fil = fil.replace("/etc/", "/lib/")
            if not os.path.isfile(fil):
               print "Cannot find file!"
               sys.exit(1)
        prog = (fil.split('/')[-1]).split('.')[0]
        check_for_file()
        check_for_specifiers()

    else:
        print "Usage: python code.py /location/of/systemd/conf_file"
        sys.exit(2)

def check_for_file():
    try:
        conf_fd = open(fil, 'r')

    except Exception, err:
        print err
        sys.exit(1)

def clear_semicolon_comment(file_str):
    return re.sub(' *; *', ';', file_str)

def check_for_specifiers():
    '''
    Function: check_for_specifiers()
    --------------------------------
    It checks for the specifiers mentioned in the systemd.unit man page.
    throws a warning to the user. Else replaces the specifiers with
    Checks the file name and if the name contains "@" but no instance it
    appropriate values.

    @return: No return value.

    '''

    # Extract the whole file content in a single string
    global template_file, instance_name, prefix_name
    conf_fd = open(fil, 'r')
    conf_list = conf_fd.readlines()
    conf_str = ''.join(conf_list)

    conf_str = clear_semicolon_comment(conf_str)

    if prog.find('@') != -1:
        template_file = 1

        if len(prog.split('@')[1]) == 0:
            print "[WARNING] No instance name specified: Generated script may not be correct"
            sys.exit(1)

        else:
            # This is the value of %i/I
            instance_name = prog.split('@')[1]
            print instance_name
            # This is the value of %p/P
            prefix_name = prog.split('@')[0]
            print prefix_name
    else:
        template_file = 0

    conf_new_str = replace_specifiers(conf_str)
    conf_new_fd = tempfile.NamedTemporaryFile(delete=False)
    tempname = conf_new_fd.name
    conf_new_fd.write(conf_new_str)
    conf_new_fd.flush()
    os.fsync(conf_new_fd)
    conf_new_fd.close()

    conf_new_fd = open(tempname, 'r')

    try:
        config.readfp(conf_new_fd)

    except Exception, err:
        print "Error:%s" % (str(err))
        sys.exit(1)

    check_for_service()

def check_for_service():
    # Here we check if the file is a service file.
    #if config.has_section("Service") is False:
    #    print "Error: The configuration file isn't a service file"
    #    sys.exit(1)
    return

def add_required_service():
    required_str = "# Requires: "

    options = ['After', 'Requires']
    
    requires = set()

    for option in options:
        if config.has_option("Unit", option):
            after_services_str = config.get("Unit", option)[0]

            for unit in after_services_str.split(" "):
                if unit != "rescue.target" and unit != "rescue.service" and unit != "emergency.target" and unit != "emergency.service":
                   requires.add(unit)
                   # required_str += unit + " "
                
    print required_str
    print requires

def check_env_file(Environment_file):
    print "if test -f %s; then\n\t. %s \nfi\n" % (Environment_file,
                                                  Environment_file)

def build_LSB_header(): #add more arguments here
# Call functions here for Provides, Required-Start, Required-Stop,
# Default-Start, Default-Stop, Short-Description and Description. Don't know
# whether we can get all the info for this from the "Unit" Section alone.
    add_required_service()


def replace_specifiers(exec_str):
    '''
    Function: replace_specifiers(exec_str)
    --------------------------------------
    Checks for the occurence of common specifiers in the string and replaces
    them with appropriate values.

    @param exec_str: string which needs to be checked for specifiers
    @return: The modified string with specifiers replaced or the same one if
    none found.
    '''

    if template_file == 1:
        # Check for %i/I specifiers and replace them with instance_name
        if (exec_str.find('%i') != -1) or (exec_str.find('%I') != -1):
            exec_str = exec_str.replace('%i', instance_name)
            exec_str = exec_str.replace('%I', instance_name)

        # Check for %p/P specifiers and replace them with prefix_name
        elif (exec_str.find('%p') != -1) or (exec_str.find('%P') != -1):
            exec_str.replace('%p', prefix_name)
            exec_str.replace('%P', prefix_name)

        elif exec_str.find('%f') != -1:
            exec_str.replace('%p', '/' + instance_name)

    # Check for %u/U and replace them with full unit name.
    # Should mean 'prog'(doubtful)
    if (exec_str.find('%u') != -1) or (exec_str.find('%U') != -1):
        exec_str.replace('%u', prog)
        exec_str.replace('%U', prog)

    return exec_str

# The build_{start,stop,reload} functions will be called irrespective of the
# existence of Exec{Start,Stop,Reload} options. This is to ensure that all the
# basic call exists(even if they have no operation).

if __name__ == '__main__':
    parser_init()
    # print "#!/bin/sh"
    build_LSB_header()
    # build_default_params()
    # build_start()
    # build_stop()
    # build_reload()
    # build_force_reload()
    # build_call_arguments()

