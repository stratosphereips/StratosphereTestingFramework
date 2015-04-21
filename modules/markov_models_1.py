# Part of this file was taken from Viper - https://github.com/botherder/viper
# The rest is from the Stratosphere Testing Framework
# See the file 'LICENSE' for copying permission.

# This module implements markov chains of first order over the letters in the chain of states of the behavioral models.
import persistent

from stf.common.out import *
from stf.common.abstracts import Module

#from stf.core.models import  __groupofgroupofmodels__ 
#from stf.core.dataset import __datasets__
#from stf.core.notes import __notes__
#from stf.core.connections import  __group_of_group_of_connections__
#from stf.core.models_constructors import __modelsconstructors__ 
#from stf.core.labels import __group_of_labels__

from stf.core.database import __database__

class Group_of_Markov_Models_1(Module, persistent.Persistent):
    cmd = 'markov_models_1'
    description = 'This module implements markov chains of first order over the letters in the chain of states of the behavioral models.'
    authors = ['Sebastian Garcia']
    # Markov Models main dictionary
    markov_models = {}

    def __init__(self):
        # Call to our super init
        super(Group_of_Markov_Models_1, self).__init__()
        self.parser.add_argument('-l', '--list', action='store_true', help='List the markov models already applied')

    # Mandatory Method!
    def get_name(self):
        """ Return the name of the module"""
        return self.cmd

    # Mandatory Method!
    def get_main_dict(self):
        """ Return the main dict where we store the info. Is going to the database"""
        return self.markov_models


    def list_markov_models(self):
        print_info('Markov Models')

    def run(self):
        # Register the structure in the database, so it is stored and use in the future
        if not __database__.has_structure(Group_of_Markov_Models_1().get_name()):
            __database__.register_new_structure(Group_of_Markov_Models_1())


        # List general help
        def help():
            self.log('info', "Markov Models")

        # Run?
        super(Group_of_Markov_Models_1, self).run()
        if self.args is None:
            return

        if self.args.list:
            self.list_markov_models()
        else:
            print_error('At least one of the parameter is required in this module')
            self.usage()

