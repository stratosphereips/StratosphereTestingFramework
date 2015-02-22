#!/usr/bin/env python
# This file is part of the Stratosphere Testing Framework 
# See the file 'LICENSE' for copying permission.

import argparse
import os

from stf.core.ui import console
from stf.core.configuration import __configuration__

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--config', help='Configuration file.', action='store', required=False, type=str)
args = parser.parse_args()

# Read the conf file.
# If we were given a conf file, use it
if args.config and os.path.isfile(args.config):
    config_file = args.config
# If not, search for the conf file in our local folder
elif os.path.isfile('./confs/stf.conf'):
    config_file = './confs/stf.conf'
else:
    print 'No configuration file found. Either give one with -c or put one in the local confs folder.'
    exit(-1)

# Load the configuration
if __configuration__.read_conf_file(os.path.expanduser(config_file)):
    # Create the console and start
    c = console.Console()
    c.start()

