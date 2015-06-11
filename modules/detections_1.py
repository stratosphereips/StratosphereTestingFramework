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





#################
#################
#################
class Detection(persistent.Persistent):
    def __init__(self, id):
        self.id = id
        self.model_training_id = ""
        self.model_testing_id = ""
        self.training_states = ""
        self.testing_states = ""
        self.training_original_prob = -1
        self.testing_final_prob = -1
        self.dict_of_distances = []
        self.distance = -1
        self.struture_training = -1
        self.struture_testing = -1
        self.training_structure_name = ""
        self.testing_structure_name = ""

    def get_id(self):
        return self.id

    def set_id(self, id):
        self.id = id

    def get_model_from_id(self, structure, model_id):
        """ From a strucure and id get the model object """
        try:
            model = structure[int(model_id)]
            return model
        except (KeyError, ValueError):
            print_error('No such id available.')
            return False

    def get_training_id(self):
        return self.model_training_id

    def get_training_structure_name(self):
        return self.training_structure_name

    def get_testing_structure_name(self):
        return self.testing_structure_name

    def get_testing_id(self):
        return self.model_testing_id

    def get_distance(self):
        return self.distance

    def detect(self, training_structure_name,  structure_training, model_training_id, testing_structure_name, structure_testing, model_testing_id):
        """ Perform the detection between the testing model and the training model"""
        self.model_training_id = model_training_id
        self.structure_training = structure_training
        self.model_testing_id = model_testing_id
        self.structure_testing = structure_testing
        self.training_structure_name = training_structure_name
        self.testing_structure_name = testing_structure_name
        # Get the models. But don't store them... they are 'heavy'
        model_training = self.get_model_from_id(self.structure_training, self.model_training_id)
        model_testing = self.get_model_from_id(self.structure_testing, self.model_testing_id)
        print_info('Detecting testing model {} with training model {}'.format(model_testing.get_id(), model_training.get_id()))
        # Get the states 
        self.training_states = model_training.get_state()
        self.testing_states = model_testing.get_state()
        # Get the original probability of detecting the training state in the training module
        self.training_original_prob = model_training.compute_probability(self.training_states)
        print_info('Probability of detecting the training model with the training model: {}'.format(self.training_original_prob))
        # Get the prob of detecting the complete testing state
        self.testing_final_prob = model_training.compute_probability(self.testing_states)
        print_info('Probability of detecting the testing model with the training model: {}'.format(self.testing_final_prob))
        # Compute distance
        if self.training_original_prob < self.testing_final_prob:
            try:
                self.distance = self.training_original_prob / self.testing_final_prob
            except ZeroDivisionError:
                self.distance = -1
        else:
            try:
                self.distance = self.testing_final_prob / self.training_original_prob
            except ZeroDivisionError:
                self.distance = -1
        print_info('Final Distance: {}'.format(self.distance))

    def detect_letter_by_letter(self, amount):
        """ 
        Try to detect letter-by-letter 
        In this model we re-create the prob matrix in the training for each letter. So the comparison is made to a matrix created with the same amount of lines that the testing sequence.
        Also the probability of detecting the training is created for the same length that the testing. We don't compare a 4 letter long testing against the prob of generating a 2000 letter long training.
        """
        # Get the models. But don't store them... they are 'heavy'
        model_training = self.get_model_from_id(self.structure_training, self.model_training_id)
        if not model_training:
            print_error('The training model was possibly deleted. We can not re-run a letter by letter comparison.')
            return False
        model_testing = self.get_model_from_id(self.structure_testing, self.model_testing_id)
        if not model_testing:
            print_error('The testing model was possibly deleted. We can not re-run a letter by letter comparison.')
            return False
        # Dont repeat the computation if we already have the data
        # Check the amount
        if amount == -1:
            amount = len(self.testing_states)
        if amount != -1 and amount > len(self.dict_of_distances):
            # Store the original matrix and prob for later
            original_matrix = model_training.get_matrix()
            original_self_prob = model_training.get_self_probability()
            if not original_self_prob:
                # Maybe it was the first time that it is generated
                training_original_prob = model_training.compute_probability(self.training_states)
                model_training.set_self_probability(training_original_prob)

            # Only generate what we dont have, not all of it
            index = len(self.dict_of_distances)
            while index < len(self.testing_states) and index < amount:
                test_sequence = self.testing_states[0:index+1]
                train_sequence = self.training_states[0:index+1]
                # First re-create the matrix only for this sequence
                model_training.create(test_sequence)
                # Get the new original prob so far...
                self.training_original_prob = model_training.compute_probability(train_sequence)
                # Now obtain the probability for testing
                temp_prob = model_training.compute_probability(test_sequence)
                if self.training_original_prob < temp_prob:
                    try:
                        self.prob_distance = self.training_original_prob / temp_prob
                    except ZeroDivisionError:
                        self.prob_distance = -1
                elif self.training_original_prob > temp_prob:
                    try:
                        self.prob_distance = temp_prob / self.training_original_prob
                    except ZeroDivisionError:
                        self.prob_distance = -1
                elif self.training_original_prob == temp_prob:
                    self.prob_distance = 1

                self.dict_of_distances.insert(index, self.prob_distance)
                #print_info('Seq: {} -> O_LogProb: {}, T_LogProb: {}, Dist: {}'.format(test_sequence, self.training_original_prob, temp_prob, self.prob_distance))
                index += 1
            final_position = index
            # Put back the original matrix and values in the model
            model_training.set_matrix(original_matrix)
            model_training.set_self_probability(original_self_prob)
        else:
            final_position = amount
        print_info('Letter by letter distance up to {} letters: {} (may differ from final distance)'.format(final_position, self.dict_of_distances[final_position-1]))
        # Ascii plot
        p = ap.AFigure()
        x = range(len(self.dict_of_distances[0:final_position]))
        y = self.dict_of_distances[0:final_position]
        # Lower all the distances more than 5
        #i = 0
        #while i < len(y):
        #    if y[i] > 5:
        #        y[i] = -1
        #    i += 1
        #print p.plot(x, y, marker='_.')
        print p.plot(x, y, marker='_of')

    def check_need_for_regeneration(self):
        """ Check if the training or testing of this detection changed since we use them """
        structures = __database__.get_structures()
        try:
            current_training_model_len = len(structures[self.training_structure_name][int(self.model_training_id)].get_state())
        except KeyError:
            print_warning('Warning! In detection id {}, the training model was deleted. However, this detection can still be used.'.format(self.get_id()))
            return False
        try:
            current_testing_model_len = len(structures[self.testing_structure_name][int(self.model_testing_id)].get_state())
        except KeyError:
            print_warning('Warning! In detection id {}, the testing model was deleted. However, this detection can still be used.'.format(self.get_id()))
            return False

        if len(self.training_states) != current_training_model_len or len(self.testing_states) != current_testing_model_len:
            return True
        else:
            return False

    def regenerate(self):
        """ Regenerate """
        print_info('Regenerating detection {}'.format(self.get_id()))
        structures = __database__.get_structures()
        structure_training = structures[self.training_structure_name]
        structure_testing = structures[self.testing_structure_name]
        self.dict_of_distances = []
        self.detect(self.training_structure_name, structure_training, self.model_training_id, self.testing_structure_name, structure_testing, self.model_testing_id)
        # Empty the dict of distances



######################
######################
######################
class Group_of_Detections(Module, persistent.Persistent):
   ### Mandatory variables ###
    cmd = 'detections_1'
    description = 'Detect a testing model using a trainig model. The distance between probabilities is made with division. The Markov Chain matrix is re-built for every letter in the sequence and the original prob of detecting the training is also re-computed for each letter in the sequence.'
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
        self.parser.add_argument('-L', '--letterbyletter', type=int, metavar='id', help='Compare and print the distances between the models letter-by-letter. Give the detection id. Optionally you can use -a to analize a fixed amount of letters. An ascii plot is generated.')
        self.parser.add_argument('-a', '--amount', type=int, default=-1, metavar='amount', help='Amount of letters to compare in the letter-by-letter comparison.')
        self.parser.add_argument('-r', '--regenerate', metavar='regenerate', type=int, help='Regenerate the detection. Used when the original training or testing models changed. Give the detection id.')
        self.parser.add_argument('-p', '--print', metavar='print', type=int, help='Print the values of the letter by letter comparison. No graph.')

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
        for detection in self.get_detections():
            regenerate = detection.check_need_for_regeneration()
            rows.append([ detection.get_id(), str(detection.get_training_id())+' in '+detection.get_training_structure_name(), str(detection.get_testing_id())+' in '+detection.get_testing_structure_name(), detection.get_distance(), regenerate])
        print(table(header=['Id', 'Training ID', 'Testing ID', 'Distance', 'Needs Regenerate'], rows=rows))

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
        # Structures to ignore
        exceptions = ['models', 'database', 'datasets', 'notes', 'connections', 'experiments', 'template_example_module', 'labels']
        # Get the training module
        # 1- List all the structures in the db, so we can pick our type of module
        structures = __database__.get_structures()
        print_info('From which structure you want to pick up the trained model?:')
        for structure in structures:
            if structure not in exceptions:
                print_info('\t'+structure)
        training_structure_name = raw_input('Name:')
        training_structure_name = training_structure_name.strip()
        # 2- Verify is there
        try:
            selected_training_structure = structures[training_structure_name]
        except KeyError:
            print_error('No such structure available.')
            return False
        # 3- Get the main dict and list the 'objects'
        print_info('Select the training module to use:')
        for object in selected_training_structure:
            print '\t',
            print_info(selected_training_structure[object])
        model_training_id = raw_input('Id:')

        print
        # Get the testing module
        # 1- List all the structures in the db, so we can pick our type of module
        structures = __database__.get_structures()
        print_info('From which structure you want to pick up the testing model?:')
        for structure in structures:
            if structure not in exceptions:
                print_info('\t'+structure)
        testing_structure_name = raw_input('Name:')
        testing_structure_name = testing_structure_name.strip()
        # 2- Verify is there
        try:
            selected_testing_structure = structures[testing_structure_name]
        except KeyError:
            print_error('No such structure available.')
            return False
        # 3- Get the main dict and list the 'objects'
        print_info('Select the testing module to use:')
        for object in selected_testing_structure:
            print '\t',
            print_info(selected_testing_structure[object])
        model_testing_id = raw_input('Id:')
        # Store on DB the new detection
        self.main_dict[new_id] = new_detection
        print_info('New detection created with id {}'.format(new_id))
        # Run the detection rutine
        new_detection.detect(training_structure_name, selected_training_structure, model_training_id, training_structure_name, selected_testing_structure, model_testing_id)

    def detect_letter_by_letter(self, detection_id, amount):
        try:
            detection = self.main_dict[detection_id]
            detection.detect_letter_by_letter(amount)
        except KeyError:
            print_error('No such detection id exists.')
            return False

    def regenerate(self, detection_id):
        """ Regenerate """
        try:
            detection = self.main_dict[detection_id]
            detection.regenerate()
        except KeyError:
            print_error('No such detection id exists.')



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
        elif self.args.letterbyletter:
            self.detect_letter_by_letter(self.args.letterbyletter, self.args.amount)
        elif self.args.regenerate:
            self.regenerate(self.args.regenerate)
        else:
            print_error('At least one of the parameter is required in this module')
            self.usage()
