# Part of this file was taken from Viper - https://github.com/botherder/viper
# The rest is from the Stratosphere Testing Framework
# See the file 'LICENSE' for copying permission.

# This module implements markov chains of first order over the letters in the chain of states of the behavioral models.
import persistent

from stf.common.out import *
from stf.common.abstracts import Module

from stf.core.models import  __groupofgroupofmodels__ 
#from stf.core.dataset import __datasets__
#from stf.core.notes import __notes__
#from stf.core.connections import  __group_of_group_of_connections__
#from stf.core.models_constructors import __modelsconstructors__ 
from stf.core.labels import __group_of_labels__

from stf.core.database import __database__


class Markov_Model(persistent.Persistent):
    """ This class is the actual markov model of first order to each label"""
    def __init__(self):
        pass





class Group_of_Markov_Models_1(Module, persistent.Persistent):
    cmd = 'markov_models_1'
    description = 'This module implements markov chains of first order over the letters in the chains of states in a LABEL.'
    authors = ['Sebastian Garcia']
    # Markov Models main dictionary
    markov_models = {}

    # Mandatory Method!
    def __init__(self):
        # Call to our super init
        super(Group_of_Markov_Models_1, self).__init__()
        self.parser.add_argument('-l', '--list', action='store_true', help='List the markov models already applied')
        self.parser.add_argument('-g', '--generate', metavar='generate', help='Generate the markov chain for this label. Give label id (4-tuple).')

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

    def generate_markov_chain(self, label_name):
        """ Given a label name generate its markov chain"""
        label_to_model = __group_of_labels__.get_label(label_name)
        connections = label_to_model.get_connections_complete()
        for dict in connections:
            print 'Dict: {}'.format(dict)
            for conn in connections[dict]:
                print '\tConn: {}'.format(conn)
                __groupofgroupofmodels__.get_group(dict)



    def run(self):
        # Register the structure in the database, so it is stored and use in the future
        if not __database__.has_structure(Group_of_Markov_Models_1().get_name()):
            __database__.register_new_structure(Group_of_Markov_Models_1())

        # List general help
        def help():
            self.log('info', "Markov Models of first order")

        # Run
        super(Group_of_Markov_Models_1, self).run()
        if self.args is None:
            return
        
        # Process the command line
        if self.args.list:
            self.list_markov_models()
        elif self.args.generate:
            self.generate_markov_chain(self.args.generate)
        else:
            print_error('At least one of the parameter is required in this module')
            self.usage()

