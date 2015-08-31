# Part of this file was taken from Viper - https://github.com/botherder/viper
# The rest is from the Stratosphere Testing Framework
# See the file 'LICENSE' for copying permission.

# This is a template module showing how to create a module that has persistence in the database. To create your own command just copy this file and start modifying it.

import persistent
import BTrees.OOBTree

from stf.common.out import *
from stf.common.abstracts import Module
from stf.core.models import  __groupofgroupofmodels__ 
from stf.core.dataset import __datasets__
from stf.core.notes import __notes__
from stf.core.connections import  __group_of_group_of_connections__
from stf.core.models_constructors import __modelsconstructors__ 
from stf.core.labels import __group_of_labels__
from stf.core.database import __database__
from modules.markov_models_1 import __group_of_markov_models__


#################
#################
#################
class Experiment(persistent.Persistent):
    """ This class is an experiment object."""
    def __init__(self, id):
        self.id = id
        # This is an example dictionary of stuff that we want to store in the DB and make persistent.
        # self.dict_of_stuff = BTrees.OOBTree.BTree()

    def get_id(self):
        return self.id

    def set_id(self, id):
        self.id = id

    def set_description(self, description):
        self.description = description

    def get_description(self):
        return self.description

    def delete(self):
        return True

    # Mandatory __repr__ module. Something you want to identify each object with. Usefull for selecting objects later
    def __repr__(self):
        return('Id:' + str(self.get_id()))



######################
######################
######################
class Group_of_Experiments(Module, persistent.Persistent):
    """ The group of Experiments """
    ### Mandatory variables ###
    cmd = 'experiments_1'
    description = 'Creates experiments with trained models on testing datasets.'
    authors = ['Sebastian Garcia']
    # Main dict of objects. The name of the attribute should be "main_dict" in this example
    main_dict = BTrees.OOBTree.BTree()
    ### End of Mandatory variables ###

    ### Mandatory Methods Don't change ###
    def __init__(self):
        # Call to our super init
        super(Group_of_Experiments, self).__init__()
        # Example of a parameter without arguments
        self.parser.add_argument('-l', '--list', action='store_true', help='List the Experiments.')
        # Example of a parameter with arguments
        self.parser.add_argument('-p', '--printstate', metavar='experiment_id', help='Print some info about the experiment.')
        self.parser.add_argument('-n', '--new', action='store_true', help='Create a new experiment. Use -m to assign the models to use for detection. Use -t to select a testing dataset.')
        self.parser.add_argument('-d', '--delete', metavar='delete', help='Delete an experiment given the id.')
        self.parser.add_argument('-m', '--models_ids', metavar='models_ids', help='Ids of the models (e.g. Markov Models) to be used when creating a new experiment with -n. Comma separated.')
        self.parser.add_argument('-t', '--testing_id', metavar='testing_id', type=int, help='Dataset id to be used as testing when creating a new experiment with -n.')

    def get_name(self):
        """ Return the name of the module"""
        return self.cmd

    # Mandatory Method! Don't change.
    def get_main_dict(self):
        """ Return the main dict where we store the info. Is going to the database"""
        return self.main_dict

    # Mandatory Method! Don't change.
    def set_main_dict(self, dict):
        """ Set the main dict where we store the info. From the database"""
        self.main_dict = dict
    ############ End of Mandatory Methods #########################


    def get_experiment(self, id):
        return self.main_dict[id]

    def get_experiments(self):
        return self.main_dict.values()

    def list_experiments(self):
        print_info('List of objects')
        rows = []
        for object in self.get_experiments():
            rows.append([ object.get_id(), object.get_description() ])
        print(table(header=['Id', 'Description'], rows=rows))

    def create_new_experiment(self, models_ids, testing_id):
        """ Create a new experiment """
        # Generate the new id
        try:
            new_id = self.main_dict[list(self.main_dict.keys())[-1]].get_id() + 1
        except (KeyError, IndexError):
            new_id = 1
        # Create the new object
        new_experiment = Experiment(new_id)
        # Set the description
        desc = raw_input("Description: ")
        new_experiment.set_description(desc)
        # Store on DB
        self.main_dict[new_id] = new_experiment
        # Methodology
        # 1. We receive the markov_models ids for the training, and the id of the dataset of the tetsing. (We may not have markov models for the testing. A binetflow file and labels are enough)
        # 2. From each training id we extract
        #   - connection-group-id
        #   - label
        #   - connection id (4-tuple)
        #   - dataset_id
        # 3. Train the thresholds of the training models between themselves
        # 4 Start the testing
        #   - Read the testing binetflow file
        #   - Create the labels_dict (IPs are key, data is another dict with time slots as key, data is label)
        #   - Create the results_dict (time slots are key, then all the errors and performance metrics in a vector)
        #   - For each flow
        #       - Extract its 4-tuple.
        #       - Extract its ground-truth label.
        #       - Extract its datetime. 
        #       - If the flow is outside the last time slot or if the netflow file finished
        #           - Compute the errors (TP, TN, FN, FP) for all the IPs in this time slot.
        #           - Compute the performance metrics in this time slot.
        #           - Compute the performance metrics so far (average?)
        #           - Store the results in the results_dict
        #           - Move to the next time slot
        #       - Compute the letter for this flow.
        #       - Get the 4-tuple object.
        #       - Store this letter in its 4-tuple.
        #       - Compute the distance of the chain of states from this 4-tuple so far, with all the training models. Don't store a new distance object.
        #       - Decide upon a winner model.
        #       - Obtain the label of the winner model.
        #       - From the labels_dict, search the IP, search the current time slot and extract the current label.
        #       - See if we should change the current label. If so, change it.
        #   - When the netflow file finishes
        #       - Select the combination of training models that had the better performance metrics for this testing dataset.
        #       - Print the winner performance metric and the winner combination of models.

        # Train the models
        print_info('Models for detection: {}'.format(models_ids))
        group_mm = __group_of_markov_models__
        group_mm.run() 
        for model_id in map(int, models_ids.split(',')):
            print_info('\tTraining model {}'.format(model_id))
            group_mm.train(model_id, "", models_ids, True)
        # Start the testing
        # Get the binetflow file
        test_dataset = __datasets__.get_dataset(testing_id)
        print test_dataset.list_files()




    def delete_experiment(self, id):
        """ Deletes an experiment """
        ans = raw_input('Are you sure you want to delete experiment {} (YES/NO)?: '.format(id))
        if ans == "YES":
            # Get the experiment
            exp = self.get_experiment(id)
            # First delete everything inside the experiment
            exp.delete()
            # Now delete it from the list of experiments
            self.main_dict.pop(id)

    # The run method runs every time that this command is used. Mandatory
    def run(self):
        ######### Mandatory part! don't delete ########################
        # Register the structure in the database, so it is stored and use in the future. 
        if not __database__.has_structure(Group_of_Experiments().get_name()):
            print_info('The structure is not registered.')
            __database__.set_new_structure(Group_of_Experiments())
        else:
            main_dict = __database__.get_new_structure(Group_of_Experiments())
            self.set_main_dict(main_dict)

        # List general help. Don't modify.
        def help():
            self.log('info', self.description)

        # Run
        super(Group_of_Experiments, self).run()
        if self.args is None:
            return
        ######### End Mandatory part! ########################
        

        # Process the command line and call the methods. Here add your own parameters
        if self.args.list:
            self.list_experiments()
        elif self.args.new:
            try:
                models_ids = self.args.models_ids
                testing_id = self.args.testing_id
            except AttributeError:
                print_error('You should provide both the ids of the models to use for detection (with -m) and the testing dataset id (with -t).')
                return False
            self.create_new_experiment(models_ids, testing_id)
        elif self.args.delete:
            self.delete_experiment(int(self.args.delete))
        else:
            print_error('At least one of the parameter is required in this module')
            self.usage()
