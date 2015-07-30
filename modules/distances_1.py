# Part of this file was taken from Viper - https://github.com/botherder/viper
# The rest is from the Stratosphere Testing Framework
# See the file 'LICENSE' for copying permission.

# Compare module. To compare models and obtain a distance

import persistent
import BTrees.OOBTree
import re
import tempfile
from subprocess import Popen, PIPE

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
        # The distances between the models for EACH letter. The index in the dict is the index letter in the testing chain of state
        self.dict_of_distances = []
        self.distance = -1
        self.struture_training = -1
        self.struture_testing = -1
        self.training_structure_name = ""
        self.testing_structure_name = ""
        # The vector of probabilities for each letter of the training model
        self.train_prob_vector = []
        # The vector of probabilities for each letter of the testing model
        self.test_prob_vector = []
        self.amount = -1

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

    def get_train_prob_vector(self):
        return self.train_prob_vector

    def get_test_prob_vector(self):
        return self.test_prob_vector

    def get_model_training_id(self):
        return self.model_training_id

    def get_model_testing_id(self):
        return self.model_testing_id

    def set_model_training_id(self, model_training_id):
        self.model_training_id = model_training_id

    def set_model_testing_id(self, model_testing_id):
        self.model_testing_id = model_testing_id

    def get_training_structure_name(self):
        return self.training_structure_name

    def get_testing_structure_name(self):
        return self.testing_structure_name

    def set_testing_structure_name(self, testing_structure_name):
        self.testing_structure_name = testing_structure_name

    def set_training_structure_name(self, training_structure_name):
        self.training_structure_name = training_structure_name

    def get_model_testing_id(self):
        return self.model_testing_id

    def get_distance(self):
        return self.distance

    def get_structure_testing(self):
        return self.structure_testing

    def get_structure_training(self):
        return self.structure_training

    def set_structure_training(self, structure_training):
        self.structure_training = structure_training

    def set_structure_testing(self, structure_testing):
        self.structure_testing = structure_testing

    def set_amount(self,amount):
        self.amount = amount

    def get_amount(self):
        try:
            return self.amount
        except AttributeError:
            return -1

    def detect(self, training_structure_name,  structure_training, model_training_id, testing_structure_name, structure_testing, model_testing_id, amount):
        """ Perform the distance between the testing model and the training model"""
        self.set_model_training_id(model_training_id)
        self.set_model_testing_id(model_testing_id)
        self.set_structure_training(structure_training)
        self.set_structure_testing(structure_testing)
        self.set_training_structure_name(training_structure_name)
        self.set_testing_structure_name(testing_structure_name)
        # Check if we can make the distance based on the protocols.
        train_label = self.get_training_label()
        test_label = self.get_testing_label()
        try:
            train_protocol = train_label.split('-')[2]
        except IndexError:
            # The label is not complete, maybe because now is "Deleted". Ignore
            return False
        try:
            test_protocol = test_label.split('-')[2]
        except IndexError:
            # The label is not complete, maybe because now is "Deleted". Ignore
            return False
        # Only compare if the protocols are the same
        if not train_protocol == test_protocol:
            return False
        # Get the models. But don't store them... they are too 'heavy'
        model_training = self.get_model_from_id(self.structure_training, self.model_training_id)
        model_testing = self.get_model_from_id(self.structure_testing, self.model_testing_id)
        if not model_testing or not model_training:
            print_error('Id is incorrect.')
            return False
        print_info('Detecting testing model {} with training model {}'.format(model_testing.get_id(), model_training.get_id()))
        # Get the states 
        self.training_states = model_training.get_state()
        self.testing_states = model_testing.get_state()
        # Get the original probability of detecting the training state in the training module
        #self.training_original_prob = model_training.compute_probability(self.training_states)
        #print_info('Probability of detecting the training model with the training model: {}'.format(self.training_original_prob))
        # Compute the distance with the cut training chain of states
        len_testing_chain = len(self.testing_states)
        self.distance = self.detect_letter_by_letter(amount)
        print_info(red('Final Distance: {}'.format(self.distance)))
        return True

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
                # IS THIS EVER USED???? IF NOT WE SHOULD DELETE IT
                # Maybe it was the first time that it is generated
                training_original_prob = model_training.compute_probability(self.training_states)
                model_training.set_self_probability(training_original_prob)

            # Only generate what we dont have, not all of it
            index = len(self.dict_of_distances)
            while index < len(self.testing_states) and index < amount:
                test_sequence = self.testing_states[0:index+1]
                train_sequence = self.training_states[0:index+1]
                #print_info('Trai Seq: {}'.format(train_sequence))
                #print_info('Test Seq: {}'.format(test_sequence))
                # First re-create the matrix only for this sequence
                model_training.create(train_sequence)
                #print_info('\tNew Matrix:')
                #for item in model_training.get_matrix():
                    #print '\t', item, model_training.get_matrix()[item]
                # Get the new original prob so far...
                self.training_original_prob = model_training.compute_probability(train_sequence)
                #print_info('\tTrain prob: {}'.format(self.training_original_prob))
                # Store the prob for future verification
                self.train_prob_vector.insert(index, self.training_original_prob)
                # Now obtain the probability for testing
                test_prob = model_training.compute_probability(test_sequence)
                #print_info('\tTest prob: {}'.format(test_prob))
                # Store the prob for future verification
                self.test_prob_vector.insert(index, test_prob)
                if self.training_original_prob < test_prob:
                    try:
                        self.prob_distance = self.training_original_prob / test_prob
                    except ZeroDivisionError:
                        self.prob_distance = -1
                elif self.training_original_prob > test_prob:
                    try:
                        self.prob_distance = test_prob / self.training_original_prob
                    except ZeroDivisionError:
                        self.prob_distance = -1
                elif self.training_original_prob == test_prob:
                    self.prob_distance = 1
                self.dict_of_distances.insert(index, self.prob_distance)
                #print_info('\tDistance: {}'.format(self.prob_distance))
                index += 1
            final_position = index
            # Put back the original matrix and values in the model
            model_training.set_matrix(original_matrix)
            model_training.set_self_probability(original_self_prob)
        else:
            final_position = amount
        # Store the amount used if it is larger than the previous one stored
        if self.get_amount() < final_position:
            self.set_amount(final_position)
            # Update the final distance of this comparison because we compute more letters
            self.distance = self.dict_of_distances[final_position-1]
        print_info('Letter by letter distance up to {} letters: {}'.format(final_position, red(self.dict_of_distances[final_position-1])))
        # Return the final distance.
        # Ascii plot
        p = ap.AFigure()
        x = range(len(self.dict_of_distances[0:final_position]))
        y = self.dict_of_distances[0:final_position]
        print p.plot(x, y, marker='_of')
        return self.dict_of_distances[final_position-1]

    def check_need_for_regeneration(self):
        """ Check if the training or testing of this comparison changed since we use them """
        structures = __database__.get_structures()
        try:
            current_training_model_len = len(structures[self.training_structure_name][int(self.model_training_id)].get_state())
        except KeyError:
            print_warning('Warning! In distance id {}, the training model was deleted. However, this distance can still be used.'.format(self.get_id()))
            return False
        try:
            current_testing_model_len = len(structures[self.testing_structure_name][int(self.model_testing_id)].get_state())
        except KeyError:
            print_warning('Warning! In distance id {}, the testing model was deleted. However, this distance can still be used.'.format(self.get_id()))
            return False

        if len(self.training_states) != current_training_model_len or len(self.testing_states) != current_testing_model_len:
            return True
        else:
            return False

    def regenerate(self):
        """ Regenerate """
        print_info('Regenerating distance {}'.format(self.get_id()))
        structures = __database__.get_structures()
        structure_training = structures[self.training_structure_name]
        structure_testing = structures[self.testing_structure_name]
        self.dict_of_distances = []
        self.detect(self.training_structure_name, structure_training, self.model_training_id, self.testing_structure_name, structure_testing, self.model_testing_id, self.get_amount())
        # Empty the dict of distances

    def print_comparison(self):
        """ Print the letter by letter values of the comparison """
        if not self.dict_of_distances:
            print_warning('Please first run -L to compute the letter by letter distances.')
            return False
        all_text='\tLetter Index | Training Letter | Testing Letter | Train Prob | Test Prob | Distance Value\n'
        index = 0
        while index < len(self.dict_of_distances):
            try:
                test_state = self.testing_states[index]
                test_prob = self.test_prob_vector[index]
            except IndexError:
                test_state = ""
            try:
                train_state = self.training_states[index]
                train_prob = self.train_prob_vector[index]
            except IndexError:
                train_state = ""
            all_text += '\t\t{}|\t\t{}|\t\t{}|\t\t{} |\t\t{} |\t\t{}\n'.format(index, train_state, test_state, train_prob, test_prob, self.dict_of_distances[index])
            index += 1
        all_text += "\n"
        # Print the matrix
        all_text += 'Train Markov Chain matrix\n'
        model_training = self.get_model_from_id(self.structure_training, self.model_training_id)
        try:
            train_matrix = model_training.get_matrix()
            for line in train_matrix:
                all_text += str(line) + str(train_matrix[line]) + "\n"
            all_text += "\n"
        except AttributeError:
            # No matrix
            print_error('No matrix available. Perhaps the model was deleted.')
        all_text += 'Test Markov Chain matrix\n'
        model_testing = self.get_model_from_id(self.structure_testing, self.model_testing_id)
        try:
            test_matrix = model_testing.get_matrix()
        except AttributeError:
            # No matrix
            print_error('No matrix available. Perhaps the model was deleted.')
        for line in test_matrix:
            all_text += str(line) + str(test_matrix[line]) + "\n"
        # Print with less
        f = tempfile.NamedTemporaryFile()
        f.write(all_text)
        f.flush()
        p = Popen('less -R ' + f.name, shell=True, stdin=PIPE)
        p.communicate()
        sys.stdout = sys.__stdout__ 
        f.close()


    def get_training_label(self):
        """ Get the training label of the training model """
        try:
            model_training = self.get_model_from_id(self.get_structure_training(), self.get_model_training_id())
        except AttributeError:
            labelname = 'Deleted'
            return labelname
        try:
            label = __group_of_labels__.get_label_by_id(model_training.get_label_id())
        except AttributeError:
            labelname = 'Deleted'
            return labelname
        if label:
            labelname = label.get_name()
        else:
            labelname = 'Deleted'
        return labelname

    def get_testing_label(self):
        """ Get the testing label of the training model """
        try:
            model_testing = self.get_model_from_id(self.get_structure_testing(), self.get_model_testing_id())
        except AttributeError:
            labelname = 'Deleted'
            return labelname
        try:
            label = __group_of_labels__.get_label_by_id(model_testing.get_label_id())
        except AttributeError:
            labelname = 'Deleted'
            return labelname
        if label:
            labelname = label.get_name()
        else:
            labelname = 'Deleted'
        return labelname



######################
######################
######################
class Group_of_Detections(Module, persistent.Persistent):
   ### Mandatory variables ###
    cmd = 'distance_1'
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
        self.parser.add_argument('-l', '--list', action='store_true', help='List the distances.')
        # Example of a parameter with arguments
        self.parser.add_argument('-n', '--new', action='store_true', help='Create a new distance. You will be prompted to select the trained model and the \'unknown\' model.')
        self.parser.add_argument('-d', '--delete', metavar='id', help='Delete the distance object with the given id.')
        self.parser.add_argument('-L', '--letterbyletter', type=int, metavar='id', help='Compare and print the distances between the models letter-by-letter. Give the distance id. Optionally you can use -a to analize a fixed amount of letters. An ascii plot is generated.')
        self.parser.add_argument('-a', '--amount', type=int, default=-1, metavar='amount', help='Amount of letters to compare in the letter-by-letter comparison.')
        self.parser.add_argument('-r', '--regenerate', metavar='regenerate', type=int, help='Regenerate the distance. Used when the original training or testing models changed. Give the distance id.')
        self.parser.add_argument('-p', '--print_comparison', metavar='id', type=int, help='Print the values of the letter by letter comparison. No graph.')
        self.parser.add_argument('-c', '--compareall', metavar='structure', help='Compare all the models between themselves in the structure specified. The comparisons are not repeted if the already exists. For example: -a markov_models_1. You can force a maximun amount of letters to compare with -a.')
        self.parser.add_argument('-f', '--filter', metavar='filter', nargs = '+', default="", help='Filter the distance. For example for listing. Keywords: testname, trainname, distance, id. Usage: testname=<text> distance<2. The names are partial matching. The operator for distances are <, >, = and !=. The operator for id is = and !=')
        self.parser.add_argument('-D', '--deleteall', action='store_true', help='Delete all the distance object that matches the -f filter. Must provide a -f filter.')

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

    def construct_filter(self, filter):
        """ Get the filter string and decode all the operations """
        # If the filter string is empty, delete the filter variable
        if not filter:
            try:
                del self.filter 
            except:
                pass
            return True
        self.filter = []
        # Get the individual parts. We only support and's now.
        for part in filter:
            # Get the key
            try:
                key = re.split('\!=|>=|<=|=|<|>', part)[0]
                value = re.split('\!=|>=|<=|=|<|>', part)[1]
            except IndexError:
                # No < or > or = or != in the string. Just stop.
                break
            # We should search for <= before <
            try:
                part.index('<=')
                operator = '<='
                self.filter.append((key, operator, value))
                continue
            except ValueError:
                # Now we search for <
                try:
                    part.index('<')
                    operator = '<'
                    self.filter.append((key, operator, value))
                    continue
                except ValueError:
                    pass
            # We should search for >= before >
            try:
                part.index('>=')
                operator = '>='
                self.filter.append((key, operator, value))
                continue
            except ValueError:
                # Now we search for >
                try:
                    part.index('>')
                    operator = '>'
                    self.filter.append((key, operator, value))
                    continue
                except ValueError:
                    pass
            # We should search for != before =
            try:
                part.index('!=')
                operator = '!='
                self.filter.append((key, operator, value))
                continue
            except ValueError:
                # Now we search for =
                try:
                    part.index('=')
                    operator = '='
                    self.filter.append((key, operator, value))
                    continue
                except ValueError:
                    pass

    def apply_filter(self, model):
        """ Use the stored filter to know what we should match"""
        responses = []
        try:
            self.filter
        except AttributeError:
            # If we don't have any filter string, just return true and show everything
            return True
        # Check each filter
        for filter in self.filter:
            key = filter[0]
            operator = filter[1]
            value = filter[2]
            if key == 'testname':
                labelname = model.get_testing_label()
                if operator == '=':
                    if value in labelname:
                        responses.append(True)
                    else:
                        responses.append(False)
                elif operator == '!=':
                    if value not in labelname:
                        responses.append(True)
                    else:
                        responses.append(False)
            elif key == 'trainname':
                labelname = model.get_training_label()
                if operator == '=':
                    if value in labelname:
                        responses.append(True)
                    else:
                        responses.append(False)
                elif operator == '!=':
                    if value not in labelname:
                        responses.append(True)
                    else:
                        responses.append(False)
            elif key == 'distance':
                distance = float(model.get_distance())
                try:
                    value = float(value)
                except ValueError:
                    print_error('Value was not float or int')
                    responses.append(False)
                    continue
                if operator == '=':
                    if distance == value:
                        responses.append(True)
                    else:
                        responses.append(False)
                elif operator == '!=':
                    if distance != value:
                        responses.append(True)
                    else:
                        responses.append(False)
                elif operator == '<':
                    if distance < value:
                        responses.append(True)
                    else:
                        responses.append(False)
                elif operator == '<=':
                    if distance <= value:
                        responses.append(True)
                    else:
                        responses.append(False)
                elif operator == '>':
                    if distance > value:
                        responses.append(True)
                    else:
                        responses.append(False)
                elif operator == '>=':
                    if distance >= value:
                        responses.append(True)
                    else:
                        responses.append(False)
            elif key == 'id':
                id = float(model.get_id())
                value = float(value)
                if operator == '=':
                    if id == value:
                        responses.append(True)
                    else:
                        responses.append(False)
                elif operator == '!=':
                    if id != value:
                        responses.append(True)
                    else:
                        responses.append(False)
            else:
                return False

        for response in responses:
            if not response:
                return False
        return True

    def has_distance_id(self, id):
        try:
            return self.main_dict[id]
        except KeyError:
            return False

    def get_distance(self, id):
        return self.main_dict[id]

    def get_distances(self):
        return self.main_dict.values()

    def list_distances(self, filter):
        self.construct_filter(filter)
        all_text=' Id | Training | Testing | Distance (amount of letters)| Needs Regenerate \n'
        for distance in self.get_distances():
            if self.apply_filter(distance):
                regenerate = distance.check_need_for_regeneration()
                training_label = distance.get_training_label()
                testing_label = distance.get_testing_label()
                all_text += ' {:<4} | {:75} | {:75} | {:8.3f} ({:>5}) | {}\n'.format(distance.get_id(), distance.get_training_structure_name() + ': ' + str(distance.get_model_training_id()) + ' (' + training_label + ')', distance.get_testing_structure_name() + ': ' + str(distance.get_model_testing_id()) + ' (' + testing_label + ')', distance.get_distance(), distance.get_amount(), regenerate)
        f = tempfile.NamedTemporaryFile()
        f.write(all_text)
        f.flush()
        p = Popen('less -R ' + f.name, shell=True, stdin=PIPE)
        p.communicate()
        sys.stdout = sys.__stdout__ 
        f.close()

    def delete_distance(self, distance_id):
        """ Delete a distance """
        if self.has_distance_id(int(distance_id)):
            self.main_dict.pop(int(distance_id))
        else:
            print_error('No such distance available.')

    def delete_all(self, filter):
        """ Delete all the objects that match the filter """
        ids=[]
        self.construct_filter(filter)
        for distance in self.get_distances():
            if self.apply_filter(distance):
                ids.append(int(distance.get_id()))
        # Must first store them and then delete them
        for id in ids:
            self.main_dict.pop(id)
        print_info('Amount of objects deleted: {}'.format(len(ids)))

    def create_new_distance(self, amount):
        """ Create a new distance. We must select the trained model and the unknown model. The amount is the max amount of letters to compare. """
        # Generate the new id for this distance
        try:
            new_id = self.main_dict[list(self.main_dict.keys())[-1]].get_id() + 1
        except (KeyError, IndexError):
            new_id = 1
        # Create the new object
        new_distance = Detection(new_id)
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
        # Run the distance rutine
        if new_distance.detect(training_structure_name, selected_training_structure, model_training_id, training_structure_name, selected_testing_structure, model_testing_id, amount):
            # Store on DB the new distance only if the comparison was successful.
            self.main_dict[new_id] = new_distance
            print_info('New distance created with id {}'.format(new_id))


    def detect_letter_by_letter(self, distance_id, amount):
        try:
            distance = self.main_dict[distance_id]
            distance.detect_letter_by_letter(amount)
        except KeyError:
            print_error('No such distance id exists.')
            return False

    def regenerate(self, distance_id, filter):
        """ Regenerate """
        try:
            distance = self.main_dict[distance_id]
            distance.regenerate()
        except KeyError:
            print_error('No such distance id exists.')

    def print_comparison(self, distance_id):
        """ Print the comparison letter by letter using the actual values """
        try:
            distance = self.main_dict[distance_id]
            distance.print_comparison()
        except KeyError:
            print_error('No such distance id exists.')

    def has_distance(self, train_id, test_id, train_structure, test_structure):
        """ Given a model train id and test id, return if the distance was previously done or not """
        response = False
        for distance in self.get_distances():
            stored_train_model_id = int(distance.get_model_training_id())
            stored_test_model_id = int(distance.get_model_testing_id())
            if stored_train_model_id == train_id and stored_test_model_id == test_id:
                response = True
                break
        return response

    def compare_all(self, structure_name, amount):
        """ Compare all the models between themselves in the specified structure. Do not repeat the comparison if it already exists """
        structures = __database__.get_structures()
        try:
            structure = structures[structure_name]
        except KeyError:
            print_error('No such structure available.')
            return False
        for train_object in structure:
            train_model_id = int(structure[train_object].get_id())
            # Run this model against the rest
            for test_object in structure:
                test_model_id = int(structure[test_object].get_id())
                if not self.has_distance(train_model_id, test_model_id, structure_name, structure_name):
                    print
                    print('Training model:'),
                    print_info(structure[train_object])
                    print('\tTesting model: '),
                    print_info(structure[test_object])
                    # Generate the new id for this distance
                    try:
                        new_id = self.main_dict[list(self.main_dict.keys())[-1]].get_id() + 1
                    except (KeyError, IndexError):
                        new_id = 1
                    # Create the new object
                    new_distance = Detection(new_id)
                    # Run the distance rutine
                    if new_distance.detect(structure_name, structure, train_model_id, structure_name, structure, test_model_id, amount):
                        # Store on DB the new distance only if the comparison was successful
                        self.main_dict[new_id] = new_distance
                        print_info('\tNew distance created with id {}'.format(new_id))

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
            self.list_distances(self.args.filter)
        elif self.args.new:
            self.create_new_distance(self.args.amount)
        elif self.args.delete:
            self.delete_distance(self.args.delete)
        elif self.args.letterbyletter:
            self.detect_letter_by_letter(self.args.letterbyletter, self.args.amount)
        elif self.args.regenerate:
            self.regenerate(self.args.regenerate, self.args.filter)
        elif self.args.print_comparison:
            self.print_comparison(self.args.print_comparison)
        elif self.args.compareall:
            self.compare_all(self.args.compareall, self.args.amount)
        elif self.args.deleteall:
            if self.args.filter:
                self.delete_all(self.args.filter)
            else: 
                print_error('Must provide a filter with -f')
        else:
            print_error('At least one of the parameter is required in this module')
            self.usage()
