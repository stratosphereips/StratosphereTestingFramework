# This file is mostly part of Viper - https://github.com/botherder/viper
# See the file 'LICENSE' for copying permission.

from stf.common.out import *
from stf.common.abstracts import Module
from stf.core.models import  __groupofgroupofmodels__ 


class Example(Module):
    cmd = 'example'
    description = 'Example module to print some statistics about the data in stf'
    authors = ['Sebastian Garcia']

    def __init__(self):
        # Call to our super init
        super(Example, self).__init__()
        self.parser.add_argument('-i', '--info', action='store_true', help='Show info')


    def example_info(self):
        # Access the models
        # Get the groups of models
        #groups = __groupofgroupofmodels__.get_groups()
        groups_ids = list(__groupofgroupofmodels__.get_groups_ids())
        print_info('There are {} groups of models so far: {}.'.format(len(groups_ids), groups_ids))



    def run(self):
        # List general info
        def help():
            self.log('info', "Example module")
            print 'Hi'

        # Run?
        super(Example, self).run()
        if self.args is None:
            return

        if self.args.info:
            self.example_info()
        else:
            print_error('At least one of the parameter is required')
            self.usage()
