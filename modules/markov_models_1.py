# Part of this file was taken from Viper - https://github.com/botherder/viper
# The rest is from the Stratosphere Testing Framework
# See the file 'LICENSE' for copying permission.

# This module implements markov chains of first order over the letters in the chain of states of the behavioral models.
import persistent
import pykov
import BTrees.OOBTree
from subprocess import Popen, PIPE
import copy

from stf.common.out import *
from stf.common.abstracts import Module
from stf.core.models import  __groupofgroupofmodels__ 
#from stf.core.dataset import __datasets__
#from stf.core.notes import __notes__
#from stf.core.connections import  __group_of_group_of_connections__
#from stf.core.models_constructors import __modelsconstructors__ 
from stf.core.labels import __group_of_labels__
from stf.core.database import __database__








#################
#################
#################
class Markov_Model(persistent.Persistent):
    """ This class is the actual markov model of first order to each label"""
    def __init__(self, id):
        self.mm_id = id
        self.state = ""
        self.label_id = -1
        self.connections = BTrees.OOBTree.BTree()

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
        # Use deepcopy so we store a copy of the connections and not the connections themselves. This is needed because more connections can be added to the label, however the state in this markov chain will miss them
        self.connections = copy.deepcopy(connections)

    def count_connections(self):
        """ Return the amount of connections in the markov model """
        count = 0
        for id in self.connections:
            for conn in self.connections[id]:
                count += 1
        return count

    def get_init_vector(self):
        return self.init_vector

    def get_matrix(self):
        return self.matrix

    def create(self):
        """ Create the Markov chain itself """
        # Separete the letters considering the letter and the symbol as a unique state:
        # So from "88,a,b," we get: '8' '8,' 'a,' 'b,'
        try:
            # This is a first order markov model. Each individual object (letter, number, etc.) is a state
            separated_letters = list(self.state)
        except AttributeError:
            print_error('There is no state yet')
            return False
        # Generate the MC
        self.init_vector, self.matrix = pykov.maximum_likelihood_probabilities(separated_letters, lag_time=1, separator='#')

    def print_matrix(self):
        print_info('Matrix of the Markov Model {}'.format(self.get_id()))
        for first in self.matrix:
            print first, self.matrix[first]

    def simulate(self, amount):
        print type(self.matrix.walk(5))
        """ Generate a simulated chain using this markov chain """
        chain = ''
        chain += self.state[0]
        chain += self.state[1]
        chain += self.state[2]
        chain += ''.join(self.matrix.walk(amount))
        print chain
        return True

    def compute_probability(self, state):
        """ Given a chain of letters, return the probability that it was generated by this MC """
        # Our computation is different of the normal one in:
        # - If a transition of states is not in the MC, we just ignore the transition and continue.
        i = 0
        probability = 0
        ignored = 0
        # We should have more than 2 states at least
        while i < len(state) and len(state) > 1:
            try:
                #vector = [state[i], state[i+1]]
                vector = state[i] + state[i+1]
                growing_v = state[0:i+2]
                # The transitions that include the # char will be automatically excluded
                log_temp_prob = self.matrix.walk_probability(vector)
                temp_prob = log_temp_prob
                i += 1
                if temp_prob != float('-inf'):                
                    probability = probability + temp_prob # logs should be +
                    #print_info('Transition [{}:{}]: {} -> Prob:{:.10f}. Our so far: {}. Real so far: {}'.format(i-1, i,vector, temp_prob, probability, self.matrix.walk_probability(growing_v)))
                else:
                    # Here is our trick. If two letters are not in the matrix... ignore the transition.
                    if '#' not in vector:
                        ignored += 1
                    continue
            except IndexError:             
                # We are out of letters        
                break
        if ignored:
            print_warning('Ignored transitions: {}'.format(ignored))
        return probability       

    def __repr__(self):
        try:
            label = __group_of_labels__.get_label_by_id(self.get_label_id())
            label_name = label.get_name()
        except KeyError:
            label_name = 'Deleted'
        current_connections = label.get_connections_complete()
        response = "Id:"+str(self.get_id())+", Label:"+label_name+", Len State:"+str(len(self.get_state()))+", #Conns:"+str(self.count_connections())
        return(response)



######################
######################
######################
class Group_of_Markov_Models_1(Module, persistent.Persistent):
    cmd = 'markov_models_1'
    description = 'This module implements markov chains of first order over the letters in the chains of states in a LABEL.'
    authors = ['Sebastian Garcia']
    # Markov Models main dictionary
    markov_models = BTrees.OOBTree.BTree()

    # Mandatory Method!
    def __init__(self):
        # Call to our super init
        super(Group_of_Markov_Models_1, self).__init__()
        self.parser.add_argument('-l', '--list', action='store_true', help='List the markov models already applied')
        self.parser.add_argument('-g', '--generate', metavar='generate', help='Generate the markov chain for this label. Give label name.')
        self.parser.add_argument('-m', '--printmatrix', metavar='printmatrix', help='Print the markov chains matrix of the given markov model id.')
        self.parser.add_argument('-s', '--simulate', metavar='simulate', help='Use this markov chain to generate a new simulated chain of states. Give the markov chain id. The length is now fixed in 100 states.')
        self.parser.add_argument('-d', '--delete', metavar='delete', help='Delete this markov chain. Give the markov chain id.')
        self.parser.add_argument('-p', '--printstate', metavar='printstate', help='Print the chain of states of all the models included in this markov chain. Give the markov chain id.')
        self.parser.add_argument('-r', '--regenerate', metavar='regenerate', help='Regenerate the markov chain. Usually because more connections were added to the label. Give the markov chain id.')

    # Mandatory Method!
    def get_name(self):
        """ Return the name of the module"""
        return self.cmd

    # Mandatory Method!
    def get_main_dict(self):
        """ Return the main dict where we store the info. Is going to the database"""
        return self.markov_models

    # Mandatory Method!
    def set_main_dict(self, dict):
        """ Set the main dict where we store the info. From the database"""
        self.markov_models = dict

    def get_markov_model(self, id):
        return self.markov_models[id]

    def get_markov_models(self):
        return self.markov_models.values()

    def print_matrix(self, markov_model_id):
        try:
            self.markov_models[int(markov_model_id)].print_matrix()
        except KeyError:
            print_error('That markov model id does not exists.')

    def list_markov_models(self):
        print_info('First Order Markov Models')
        rows = []
        for markov_model in self.get_markov_models():
            try:
                label = __group_of_labels__.get_label_by_id(markov_model.get_label_id())
                label_name = label.get_name()
            except KeyError:
                print_error('The label used in the markov model {} does not exist anymore. You should delete the markov chain (It will not appear in the list).'.format(markov_model.get_id()))
                continue
            current_connections = label.get_connections_complete()
            needs_regenerate = True
            # Do we need to regenerate this mc?
            if current_connections == markov_model.get_connections():
                needs_regenerate = False
            rows.append([ markov_model.get_id(), len(markov_model.get_state()), markov_model.count_connections(), label_name, needs_regenerate ])
        print(table(header=['Id', 'State Len', '# Connections', 'Label', 'Needs Regenerate'], rows=rows))


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
            # Delete the last #
            state = state[:-1]
            # Store the state
            markov_model.set_state(state)
            # Store the connections
            markov_model.set_connections(connections)
            # Create the MM itself
            markov_model.create()
            # Store
            self.markov_models[mm_id] = markov_model
        else:
            print_error('No label with that name')

    def simulate(self, markov_model_id):
        """ Generate a new simulated chain of states for this markov chain """
        try:
            markov_model = self.get_markov_model(int(markov_model_id))
            markov_model.simulate(100)
        except KeyError:
            print_error('No such markov model id')

    def delete(self, markov_model_id):
        """ Delete the markvov chain """
        try:
            self.markov_models.pop(int(markov_model_id))
        except KeyError:
            print_error('No such markov model id')

    def printstate(self, markov_model_id):
        """ Print all the info about the markov chain """
        try:
            markov_model = self.get_markov_model(int(markov_model_id))
        except KeyError:
            print_error('No such markov model id')
            return False
        print_info('Markov Chain ID {}'.format(markov_model_id))
        print_info('Label')
        label_name = __group_of_labels__.get_label_name_by_id(markov_model.get_label_id())
        print '\t', 
        print_info(label_name)
        state = markov_model.get_state()
        print_info('Len of State: {} (Max chars printed: 2000)'.format(len(state)))
        print '\t', 
        print_info(state[0:2000])
        print_info('Connections in the Markov Chain')
        connections = markov_model.get_connections()
        print '\t', 
        print_info(connections)
        # Plot the histogram of letters
        print_info('Histogram of Amount of Letters')
        dist_path,error = Popen('bash -i -c "type distribution"', shell=True, stderr=PIPE, stdin=PIPE, stdout=PIPE).communicate()
        if not error:
            distribution_path = dist_path.split()[0]
            list_of_letters = ''.join([i+'\n' for i in list(state)])
            print 'Key=Amount of letters'
            Popen('echo \"' + list_of_letters + '\" |distribution --height=50 | sort -nk1', shell=True).communicate()
        else:
            print_error('For ploting the histogram we use the tool https://github.com/philovivero/distribution. Please install it in the system to enable this command.')
        #print_info('Test Probability: {}'.format(markov_model.compute_probability("r*R*")))
        log_self_prob = markov_model.compute_probability(markov_model.get_state())
        print_info('Log Probability of detecting itself: {}'.format(log_self_prob))

    def regenerate(self, markov_model_id):
        """ Regenerate the markvov chain """
        try:
            markov_model = self.get_markov_model(int(markov_model_id))
        except KeyError:
            print_error('No such markov model id')
            return False
        label = __group_of_labels__.get_label_by_id(markov_model.get_label_id())
        connections = label.get_connections_complete()
        # Get all the group of models and connections names
        state = ""
        for group_of_model_id in connections:
            # Get all the connections
            for conn in connections[group_of_model_id]:
                # Get the model group
                group = __groupofgroupofmodels__.get_group(group_of_model_id)
                # Get the model
                model = group.get_model(conn)
                # Get each state
                state += model.get_state() + '#'
        # Delete the last #
        state = state[:-1]
        # Store the state
        markov_model.set_state(state)
        # Store the connections
        markov_model.set_connections(connections)
        # Create the MM itself
        markov_model.create()
        print_info('Markov model {} regenerated.'.format(markov_model_id))




    # The run method runs every time that this command is used
    def run(self):
        # Register the structure in the database, so it is stored and use in the future. 
        if not __database__.has_structure(Group_of_Markov_Models_1().get_name()):
            print_info('The structure is not registered.')
            __database__.set_new_structure(Group_of_Markov_Models_1())
        else:
            main_dict = __database__.get_new_structure(Group_of_Markov_Models_1())
            self.set_main_dict(main_dict)

        # List general help. Don't modify.
        def help():
            self.log('info', self.description)

        # Run
        super(Group_of_Markov_Models_1, self).run()
        if self.args is None:
            return
        
        # Process the command line
        if self.args.list:
            self.list_markov_models()
        elif self.args.generate:
            self.create_new_model(self.args.generate)
        elif self.args.printmatrix:
            self.print_matrix(self.args.printmatrix)
        elif self.args.simulate:
            self.simulate(self.args.simulate)
        elif self.args.delete:
            self.delete(self.args.delete)
        elif self.args.printstate:
            self.printstate(self.args.printstate)
        elif self.args.regenerate:
            self.regenerate(self.args.regenerate)
        else:
            print_error('At least one of the parameter is required in this module')
            self.usage()

__group_of_markov_models__ = Group_of_Markov_Models_1()
