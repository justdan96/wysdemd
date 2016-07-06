#!/usr/bin/env python

import ConfigParser
import sys, os, tempfile, re, collections
from types import StringType
import syslog

class FakeSecHead(object):
    def __init__(self, fp):
        self.fp = fp
        self.sechead = '[asection]\n'

    def readline(self):
        if self.sechead:
            try: 
                return self.sechead
            finally: 
                self.sechead = None
        else: 
            return self.fp.readline()
            return self.fp.readline()

# parse an environment file, adding the variables into the referenced environment and returning the new one
def parse_envfile(efile, environ):
    efilec = ConfigParser.RawConfigParser()
    efilec.optionxform = str
    try:
        efilec.readfp(FakeSecHead(open(efile)))
    except:
        wyslog("error reading environment file " + efile)
        return environ
    
    for option in efilec.options('asection'):
        environ[option] = efilec.get('asection', option)
    return environ

def wyslog(msg, lvl=None):
    if lvl is None:
        lvl = syslog.LOG_INFO
    elif lvl == 'err':
        lvl = syslog.LOG_ERR
    
    syslog.openlog(ident='warlock',facility=syslog.LOG_LOCAL7)
    syslog.syslog(lvl, msg)

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
            
def tree(): return collections.defaultdict(tree)

def dicts(t): return {k: dicts(t[k]) for k in t}

def tree_add(t, path):
  for node in path:
    t = t[node]

def tree_set(t, path, val):
    i = 0
    for node in path:
        i = i + 1
        if i == len(path):
            t[node] = str(val)

def toposort2(data):
    for k, v in data.items():
        v.discard(k) # Ignore self dependencies
    extra_items_in_deps = reduce(set.union, data.values()) - set(data.keys())
    data.update({item:set() for item in extra_items_in_deps})
    while True:
        ordered = set(item for item,dep in data.items() if not dep)
        if not ordered:
            break
        yield ' '.join(sorted(ordered))
        data = {item: (dep - ordered) for item,dep in data.items()
                if item not in ordered}
    assert not data, "A cyclic dependency exists amongst %r" % data
            
def create_config(fil):
    config = ConfigParser.ConfigParser(None, newdict)

    if fil[0:20] != '/etc/systemd/system/' and fil[0:20] != '/lib/systemd/system/':
        fil = '/etc/systemd/system/' + fil
    if not os.path.isfile(fil):
        fil = fil.replace("/etc/", "/lib/")
        if not os.path.isfile(fil):
           wyslog("Cannot find file! " + fil)
           return [1,1,1]
           
    prog = (fil.split('/')[-1]).split('.')[0]
    
    if check_for_file(fil) == 0:
		is_service = check_for_specifiers(fil, config, prog)
        
    return config, prog, is_service


def check_env_file(Environment_file):
    print "if test -f %s; then\n\t. %s \nfi\n" % (Environment_file,
                                                  Environment_file)

def check_for_specifiers(fil, config, prog):
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
    # template_file, instance_name, prefix_name
    conf_fd = open(fil, 'r')
    conf_list = conf_fd.readlines()
    conf_str = ''.join(conf_list)

    conf_str = clear_semicolon_comment(conf_str)

    if prog.find('@') != -1:
        template_file = 1

        if len(prog.split('@')[1]) == 0:
            wyslog("[WARNING] No instance name specified: Generated script may not be correct: " + fil)
            return 1

        else:
            # This is the value of %i/I
            instance_name = prog.split('@')[1]
            #print instance_name
            # This is the value of %p/P
            prefix_name = prog.split('@')[0]
            #print prefix_name
    else:
        template_file = 0

    conf_new_str = replace_specifiers(conf_str, template_file)
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
        wyslog("Error:%s" % (str(err)))
        return 1

    return check_for_service(config)


def replace_specifiers(exec_str, template_file):
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

def clear_semicolon_comment(file_str):
    return re.sub(' *; *', ';', file_str)

def check_for_file(fil):
    try:
        conf_fd = open(fil, 'r')

    except Exception, err:
        print err
        return err
    
    return 0

def check_for_service(config):
    # Here we check if the file is a service file.
    if config.has_section("Service") is True:
        return True
    else:
        return False
    #    print "Error: The configuration file isn't a service file"
    #    sys.exit(1)

