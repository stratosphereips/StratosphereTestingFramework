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
    def __init__(self, id):
        self.mm_id = id
        self.state = ""
        self.label_id = -1
        self.connections = {}

    def get_id(self):
        return self.mm_id

    def set_id(self, id):
        self.mm_id = id

    def get_state(self):
        return self.state

    def set_state(self, state):
        self.state = state

    def get_label_id(self):
        return self.label_id

    def set_label_id(self, label_id):
        self.label_id = label_id

    def get_connections(self):
        return self.connections
    
    def set_connections(self, connections):
        self.connections = connections




######################
######################
######################
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
        self.parser.add_argument('-g', '--generate', metavar='generate', help='Generate the markov chain for this label. Give label name.')

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

    def create_new_model(self, label_name):
        """ Given a label name create a new markov chain object"""
        # Get the label object
        label_to_model = __group_of_labels__.get_label(label_name)
        if label_to_model:
            # Create a new markov chain object
            ## Get the new id
            try:
                mm_id = self.markov_models[list(self.markov_models.keys())[-1]].get_id() + 1
            except (KeyError, IndexError):
                mm_id = 1
            markov_model = Markov_Model(mm_id)
            # Store the label id
            markov_model.set_label_id(label_to_model.get_id())
            state = ""
            # Get all the connections in the label
            connections = label_to_model.get_connections_complete()
            # Get all the group of models and connections names
            for group_of_model_id in connections:
                # Get all the connections
                for conn in connections[group_of_model_id]:
                    # Get the model group
                    group = __groupofgroupofmodels__.get_group(group_of_model_id)
                    # Get the model
                    model = group.get_model(conn)
                    # Get each state
                    state += model.get_state() + '#'
            # Store the state
            markov_model.set_state(state)
            # Store the connections
            markov_model.set_connections(connections)
            print markov_model.get_id()
            print markov_model.get_state()
            print len(markov_model.get_state())
            print markov_model.get_connections()





        else:
            print_error('No label with that name')



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
            self.create_new_model(self.args.generate)
        else:
            print_error('At least one of the parameter is required in this module')
            self.usage()

