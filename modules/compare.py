# Part of this file was taken from Viper - https://github.com/botherder/viper
# The rest is from the Stratosphere Testing Framework
# See the file 'LICENSE' for copying permission.

# Compare module. To compare models and obtain a probability of detection

import persistent
import BTrees.OOBTree

from stf.common.out import *
from stf.common.abstracts import Module

from stf.core.dataset import __datasets__
from stf.core.models import  __groupofgroupofmodels__ 
from stf.core.notes import __notes__
from stf.core.connections import  __group_of_group_of_connections__
from stf.core.models_constructors import __modelsconstructors__ 
from stf.core.labels import __group_of_labels__
from stf.core.database import __database__

#__group_of_markov_models__ = Group_of_Markov_Models_1()






#################
#################
#################
class Detection(persistent.Persistent):
    def __init__(self, id):
        self.id = id
        #self.dict_of_stuff = BTrees.OOBTree.BTree()

    def get_id(self):
        return self.id

    def set_id(self, id):
        self.id = id

    def set_training_module(self, model1):
        self.training_module_id = model1

    def set_unknown_module(self, model2):
        self.unknown_module_id = model2

    def detect(self):
        """ Perform the detection """
        print_info('Detecting...')





######################
######################
######################
class Group_of_Detections(Module, persistent.Persistent):
    ### Mandatory variables ###
    cmd = 'detections'
    description = 'Use some behavioral models to detect other models.'
    authors = ['Sebastian Garcia']
    # Main dict of objects. The name of the attribute should be "main_dict" in this example
    main_dict = BTrees.OOBTree.BTree()
    ### End of Mandatory variables ###

    ### Mandatory Methods Don't change ###
    def __init__(self):
        # Call to our super init
        super(Group_of_Detections, self).__init__()
        # Example of a parameter without arguments
        self.parser.add_argument('-l', '--list', action='store_true', help='List the detections.')
        # Example of a parameter with arguments
        self.parser.add_argument('-n', '--new', metavar='new', help='Create a new detection. Give the id of the trained model here and use -m to give the \'unknown\' model.')
        self.parser.add_argument('-m', '--model', metavar='model', help='Id of the \'unknown\' model to analyze agains the model given with -n.')
        self.parser.add_argument('-d', '--delete', metavar='delete', help='Delete the detection id.')

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

    def has_detection_id(self, id):
        try:
            return self.main_dict[id]
        except KeyError:
            return False

    def get_detection(self, id):
        return self.main_dict[id]

    def get_detections(self):
        return self.main_dict.values()

    def list_detections(self):
        print_info('List of Detections')
        rows = []
        for object in self.get_detections():
            rows.append([ object.get_id()])
        print(table(header=['Id'], rows=rows))

    def delete_detection(self, detection_id):
        """ Delete a detection """
        if self.has_detection_id(int(detection_id)):
            self.main_dict.pop(int(detection_id))

    def create_new_detection(self, model1, model2):
        # Generate the new id for this detection
        try:
            new_id = self.main_dict[list(self.main_dict.keys())[-1]].get_id() + 1
        except (KeyError, IndexError):
            new_id = 1
        # Create the new object
        new_detection = Detection(new_id)

        # Get the training module
        # 1- List all the structures in the db, so we can pick our type of module
        structures = __database__.get_structures()
        print_info('From which structure you want to pick up the trained model?:')
        for structure in structures:
            print_info(structure)
        selection = raw_input('Name:')
        selection = selection.strip()
        # 2- Verify is there
        try:
            selected_structure = structures[selection]
        except KeyError:
            print_error('No such structure available.')
            return False
        # 3- Get the main dict and list the 'objects'
        main_dict = selected_structure
        for object in  main_dict:
            print object

        
        new_detection.set_training_module(model1)
        new_detection.set_unknown_module(model2)
        # Store on DB
        self.main_dict[new_id] = new_detection
        # Run the detection rutine
        new_detection.detect()



    # The run method runs every time that this command is used. Mandatory
    def run(self):
        ######### Mandatory part! don't delete ########################
        # Register the structure in the database, so it is stored and use in the future. 
        if not __database__.has_structure(Group_of_Detections().get_name()):
            print_info('The structure is not registered.')
            __database__.set_new_structure(Group_of_Detections())
        else:
            main_dict = __database__.get_new_structure(Group_of_Detections())
            self.set_main_dict(main_dict)

        # List general help. Don't modify.
        def help():
            self.log('info', self.description)

        # Run
        super(Group_of_Detections, self).run()
        if self.args is None:
            return
        ######### End Mandatory part! ########################
        

        # Process the command line and call the methods. Here add your own parameters
        if self.args.list:
            self.list_detections()
        elif self.args.new:
            if not self.args.model:
                print_error('You should give the \'unknown\' model with -m.')
                return False
            self.create_new_detection(self.args.new, self.args.model)
        elif self.args.delete:
            self.delete_detection(self.args.delete)
        else:
            print_error('At least one of the parameter is required in this module')
            self.usage()
