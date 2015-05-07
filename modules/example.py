# Part of this file was taken from Viper - https://github.com/botherder/viper
# The rest is from the Stratosphere Testing Framework
# See the file 'LICENSE' for copying permission.

# Example file of how to create a module without persistence in the database. Useful for obtaining statistics or processing data.

from stf.common.out import *
from stf.common.abstracts import Module
from stf.core.models import  __groupofgroupofmodels__ 
from stf.core.dataset import __datasets__
from stf.core.notes import __notes__
from stf.core.connections import  __group_of_group_of_connections__
from stf.core.models_constructors import __modelsconstructors__ 
from stf.core.labels import __group_of_labels__


class Example(Module):
    cmd = 'example'
    description = 'Example module to print some statistics about the data in stf'
    authors = ['Sebastian Garcia']

    def __init__(self):
        # Call to our super init
        super(Example, self).__init__()
        self.parser.add_argument('-i', '--info', action='store_true', help='Show info')


    def example_info(self):
        # Example to read datasets
        datasets_ids = list(__datasets__.get_datasets_ids())
        print_info('There are {} datasets: {}.'.format(len(datasets_ids), datasets_ids))

        # Example to get connnections
        connections_groups_ids = list(__group_of_group_of_connections__.get_groups_ids())
        print_info('There are {} groups of connections: {}.'.format(len(connections_groups_ids), connections_groups_ids))

        # Example to read models
        models_groups_ids = list(__groupofgroupofmodels__.get_groups_ids())
        print_info('There are {} groups of models: {}.'.format(len(models_groups_ids), models_groups_ids))

        # Example to get notes
        notes_ids = list(__notes__.get_notes_ids())
        print_info('There are {} notes: {}.'.format(len(notes_ids), notes_ids))

        # Example to get labels
        labels_ids = list(__group_of_labels__.get_labels_ids())
        print_info('There are {} labels: {}.'.format(len(labels_ids), labels_ids))

        # Example to get the labels constructors
        constructors_ids = list(__modelsconstructors__.get_constructors_ids())
        print_info('There are {} model constructors: {}.'.format(len(constructors_ids), constructors_ids))




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
