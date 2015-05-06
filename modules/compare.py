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
from stf.common import ap

#__group_of_markov_models__ = Group_of_Markov_Models_1()






#################
#################
#################
class Detection(persistent.Persistent):
    def __init__(self, id):
        self.id = id
        self.training_states = ""
        self.testing_states = ""
        self.training_original_prob = -1
        self.testing_final_prob = -1
        self.dict_of_distances = []

    def get_id(self):
        return self.id

    def set_id(self, id):
        self.id = id

    def detect(self, model_training, model_testing):
        """ Perform the detection between the testing model and the training model"""
        print_info('Detecting testing model {} with {}'.format(model_training.get_id(), model_testing.get_id()))
        # Get the states 
        self.training_states = model_training.get_state()[0:1000]
        self.testing_states = model_testing.get_state()[0:1000]
        # Get the original probability of detecting the training state in the training module
        self.training_original_prob = model_training.compute_probability(self.training_states)
        print_info('Original probability for detecting the training: {}'.format(self.training_original_prob))
        sequence = ""
        # Get the prob of detecting the complete testing state
        self.testing_final_prob = model_training.compute_probability(self.testing_states)
        print_info('Final probability of detecting the testing: {}'.format(self.testing_final_prob))

        # Compute distance
        if self.training_original_prob < self.testing_final_prob:
            try:
                self.prob_distance = self.training_original_prob / self.testing_final_prob
            except ZeroDivisionError:
                self.prob_distance = -1
        else:
            try:
                self.prob_distance = self.testing_final_prob / self.training_original_prob
            except ZeroDivisionError:
                self.prob_distance = -1
        print_info('Final Distance: {}'.format(self.prob_distance))


        # Get the probs letter by letter
        print
        for letter in self.testing_states:
            sequence += letter
            temp_prob = model_training.compute_probability(sequence)
            #print_info('Seq: {} -> Prob: {}'.format(sequence, temp_prob))
            if self.training_original_prob < temp_prob:
                try:
                    self.prob_distance = self.training_original_prob / temp_prob
                except ZeroDivisionError:
                    self.prob_distance = -1
            else:
                try:
                    self.prob_distance = temp_prob / self.training_original_prob
                except ZeroDivisionError:
                    self.prob_distance = -1
            self.dict_of_distances.append(self.prob_distance)
            #print_info('Distance: {}'.format(self.prob_distance))

        
        p = ap.AFigure()
        x = range(len(self.dict_of_distances))
        y = self.dict_of_distances
        # Lower all the distances more than 5
        i = 0
        while i < len(y):
            if y[i] > 5:
                y[i] = -1
            i += 1
        #print p.plot(x, y, marker='_.')
        print p.plot(x, y, marker='_of')

        #print x[0:100]
        #print y[0:100]

        #print 'Training'
        #for letter in training_states:
        #    sequence += letter
        #    temp_prob = model_training.compute_probability(sequence)
        #    print_info('Seq: {} -> Prob: {}'.format(sequence, temp_prob))




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
        self.parser.add_argument('-n', '--new', action='store_true', help='Create a new detection. You will be prompted to select the trained model and the \'unknown\' model.')
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
        else:
            print_error('No such detection available.')

    def create_new_detection(self):
        """ Create a new detection. We must select the trained model and the unknown model """
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
            print_info('\t'+structure)
        selection = raw_input('Name:')
        selection = selection.strip()
        # 2- Verify is there
        try:
            selected_structure = structures[selection]
        except KeyError:
            print_error('No such structure available.')
            return False
        # 3- Get the main dict and list the 'objects'
        print_info('Select the training module to use:')
        for object in selected_structure:
            print '\t',
            print_info(selected_structure[object])
        model_training_id = raw_input('Id:')
        # 4- Verify is there
        try:
            model_training = selected_structure[int(model_training_id)]
        except (KeyError, ValueError):
            print_error('No such id available.')
            return False

        print
        # Get the testing module
        # 1- List all the structures in the db, so we can pick our type of module
        structures = __database__.get_structures()
        print_info('From which structure you want to pick up the testing model?:')
        for structure in structures:
            print_info('\t'+structure)
        selection = raw_input('Name:')
        selection = selection.strip()
        # 2- Verify is there
        try:
            selected_structure = structures[selection]
        except KeyError:
            print_error('No such structure available.')
            return False
        # 3- Get the main dict and list the 'objects'
        print_info('Select the testing module to use:')
        for object in selected_structure:
            print '\t',
            print_info(selected_structure[object])
        model_testing_id = raw_input('Id:')
        # 4- Verify is there
        try:
            model_testing = selected_structure[int(model_testing_id)]
        except (KeyError, ValueError):
            print_error('No such id available.')
            return False
        # Store on DB the new detection
        self.main_dict[new_id] = new_detection
        print_info('New detection created with id {}'.format(new_id))
        # Run the detection rutine
        new_detection.detect(model_training, model_testing)



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
            self.create_new_detection()
        elif self.args.delete:
            self.delete_detection(self.args.delete)
        else:
            print_error('At least one of the parameter is required in this module')
            self.usage()
