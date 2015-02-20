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
if args.config and os.path.isfile(args.config):
    config_file = args.config
elif os.path.isfile('/etc/stf.conf'):
    config_file = '/etc/stf.conf'
elif os.path.isfile('confs/stf.conf'):
    config_file = 'confs/stf.conf'
else:
    print_error('No configuration file found.')

# Load the configuration
if __configuration__.read_conf_file(os.path.expanduser(config_file)):
    # Create the console and start
    c = console.Console()
    c.start()

