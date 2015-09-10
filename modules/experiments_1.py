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
from modules.distances_1 import Detection # The name should be Distances, but we can not change it because if we do, we lost all the current distances in the db

from datetime import datetime
from datetime import timedelta
import time


######################
######################
######################
class Tuple(object):
    """ The class to simply handle tuples """
    def __init__(self, tuple4):
        self.id = tuple4
        self.ground_truth_label = ""
        self.datetime = ""
        self.amount_of_flows = 0
        self.src_ip = tuple4.split('-')[0]
        # The ground truth label is assigned only once, because it will not change for the same tuple
        self.ground_truth_label_id = __group_of_labels__.search_connection_in_label(tuple4)
        # It could be that the tuple does not have a ground truth label
        if self.ground_truth_label_id:
            self.ground_truth_label = __group_of_labels__.get_label_name_by_id(self.ground_truth_label_id)
        self.state_so_far = ""

    def get_tuples_with_ip(self, ip):
        """ Return all the tuples with this src ip """
        tuples = []
        for tuple in self.tuples:
            if tuple.get_src_ip() == ip:
                tuples.append(tuple)
        return tuples

    def get_state_len_so_far(self):
        return len(self.state_so_far)

    def set_state_so_far(self, state):
        self.state_so_far = state

    def get_state_so_far(self):
        return self.state_so_far

    def get_src_ip(self):
        return self.src_ip

    def add_new_flow(self, column_values):
        """ Add new stuff about the flow in this tuple """
        self.datetime = column_values['StartTime']
        self.amount_of_flows += 1
        self.predicted_label = False

    def get_ground_truth_label(self):
        """ Compute the new ground_truth_label and return it """
        return self.ground_truth_label

    def get_id(self):
        return self.id

    def get_summary(self):
        """ A summary of what happened in this tuple """
        return 'Tuple: {}, Amount of flows: {}'.format(self.id, self.amount_of_flows)
    
    def __repr__(self):
        return('Id: {}, Label:{}, Starttime: {}'.format(self.get_id(), self.ground_truth_label, self.datetime))



######################
######################
######################
class TimeSlot(persistent.Persistent):
    """ Class to work with the time slots of results from the testing """
    def __init__(self, time, width):
        self.init_time = time 
        self.finish_time = self.init_time + timedelta(seconds=width)
        # Methodology 3.2. Create the dictionary for holding the labels info (IPs are key, data is another dict with 'ground_truth_label' and 'predicted_label')
        self.ip_dict = {}
        self.time_slot_width = width
        # Initialize
        self.acc_errors = {}
        self.acc_errors['TP'] = 0.0
        self.acc_errors['TN'] = 0.0
        self.acc_errors['FN'] = 0.0
        self.acc_errors['FP'] = 0.0
        # Errors NN means that the ground truth label is unknown, so it is not Positive nor Negative and we can not report an error.
        self.acc_errors['NN'] = 0.0
        # Errors NN means that the ground truth label is unknown, so it is not Positive nor Negative and we can not report an error.
        self.performance_metrics = {}
        self.performance_metrics['TPR'] = -1
        self.performance_metrics['FPR'] = -1
        self.performance_metrics['TNR'] = -1
        self.performance_metrics['FNR'] = -1
        self.performance_metrics['ErrorRate'] = -1
        self.performance_metrics['Precision'] = -1
        self.performance_metrics['Accuracy'] = -1
        self.performance_metrics['FMeasure1'] = -1
        self.results_dict = {}

    def compute_performance_metrics(self):
        """ Compute performance metrics """
        try:
            self.performance_metrics['TPR'] = ( self.acc_errors['TP'] ) / float(self.acc_errors['TP'] + self.acc_errors['FN'])
        except ZeroDivisionError:
            self.performance_metrics['TPR'] = -1

        try:
            self.performance_metrics['TNR'] = ( self.acc_errors['TN'] ) / float( self.acc_errors['TN'] + self.acc_errors['FP'] )
        except ZeroDivisionError:
            self.performance_metrics['TNR'] = -1

        try:
            self.performance_metrics['FPR'] = ( self.acc_errors['FP'] ) / float( self.acc_errors['TN'] + self.acc_errors['FP'] )
        except ZeroDivisionError:
            self.performance_metrics['FPR'] = -1

        try:
            self.performance_metrics['FNR'] = ( self.acc_errors['FN'] ) / float(self.acc_errors['TP'] + self.acc_errors['FN'])
        except ZeroDivisionError:
            self.performance_metrics['FNR'] = -1

        try:
            self.performance_metrics['Precision'] = ( self.acc_errors['TP'] ) / float(self.acc_errors['TP'] + self.acc_errors['FP'])
        except ZeroDivisionError:
            self.performance_metrics['Precision'] = -1

        try:
            self.performance_metrics['Accuracy'] = ( self.acc_errors['TP'] + self.acc_errors['TN'] ) / float( self.acc_errors['TP'] + self.acc_errors['TN'] + self.acc_errors['FP'] + self.acc_errors['FN'] )
        except ZeroDivisionError:
            self.performance_metrics['Accuracy'] = -1

        try:
            self.performance_metrics['ErrorRate'] = ( self.acc_errors['FN'] + self.acc_errors['FP'] ) / float( self.acc_errors['TP'] + self.acc_errors['TN'] + self.acc_errors['FP'] + self.acc_errors['FN'] )
        except ZeroDivisionError:
            self.performance_metrics['ErrorRate'] = -1

        self.beta = 1.0
        # With beta=1 F-Measure is also Fscore
        try:
            self.performance_metrics['FMeasure1'] = ( ( (self.beta * self.beta) + 1 ) * self.performance_metrics['Precision'] * self.performance_metrics['TPR']  ) / float( ( self.beta * self.beta * self.performance_metrics['Precision'] ) + self.performance_metrics['TPR'])
        except ZeroDivisionError:
            self.performance_metrics['FMeasure1'] = -1

    def compute_errors(self, predicted_label, ground_truth_label):
        """ Get the predicted and ground truth labels and figure it out the errors. Both current errors for this time slot and accumulated errors in all time slots."""
        # So we can work with multiple positives and negative labels
        if 'Botnet' in predicted_label or 'Malware' in predicted_label or 'CC' in predicted_label:
            predicted_label_positive = True
        elif 'Normal' in predicted_label:
            predicted_label_positive = False
        if 'Botnet' in ground_truth_label or 'Malware' in ground_truth_label or 'CC' in ground_truth_label:
            ground_truth_label_positive = True
        elif 'Normal' in ground_truth_label:
            ground_truth_label_positive = False
        # Now catch the NN errors
        elif 'Background' in ground_truth_label or ground_truth_label == '':
            self.acc_errors['NN'] += 1
            return 'NN'
        # Compute the actual errors
        if predicted_label_positive and ground_truth_label_positive:
            self.acc_errors['TP'] += 1
            return 'TP'
        elif predicted_label_positive and not ground_truth_label_positive:
            self.acc_errors['FP'] += 1
            return 'FP'
        elif not predicted_label_positive and not ground_truth_label_positive:
            self.acc_errors['TN'] += 1
            return 'TN'
        elif not predicted_label_positive and ground_truth_label_positive:
            self.acc_errors['FN'] += 1
            return 'FN'

    def add_src_ip(self, ip):
        """ Add the src ip to the time slot """
        try:
            dict = self.ip_dict[ip]
        except KeyError:
            self.ip_dict[ip] = {}

    def set_ground_truth_label_for_ip(self, ip, ground_truth_label):
        """ The logic to select which ground_truth_label is assigned to an IP. Because we can have multiple labels because of multiple tuples for the same ip """
        try:
            current = self.ip_dict[ip]['ground_truth_label']
            # Only update if the original label is normal or background. So don't change a botnet/cc/attack/malware ground_truth_label. Also don't assign the same GTL again
            if current and 'normal' not in current.lower() and 'background' not in current.lower() and current != ground_truth_label:
                    self.ip_dict[ip]['ground_truth_label'] = ground_truth_label
                    #print '\tAssigning GTL to ip {}: {}'.format(ip, ground_truth_label)
        except KeyError:
            # First time
            self.ip_dict[ip]['ground_truth_label'] = ground_truth_label
            #print '\tAssigning first time GTL to ip {}: {}'.format(ip, ground_truth_label)

    def set_predicted_label_for_ip(self, ip, new_predicted_label):
        try:
            self.ip_dict[ip]['predicted_label'] = new_predicted_label
            #print_warning('\tAssigning predicted label {} to IP {}'.format(new_predicted_label, ip))
        except KeyError:
            # First time
            self.ip_dict[ip]['predicted_label'] = new_predicted_label
            #print_warning('\tAssigning predicted label {} to IP {}'.format(new_predicted_label, ip))

    def close(self):
        """ Close the slot """
        #  - Compute the errors (TP, TN, FN, FP) for all the IPs in this time slot.
        for ip in self.ip_dict:
            try:
                predicted_label = self.ip_dict[ip]['predicted_label']
            except KeyError:
                predicted_label = ''
            try:
                ground_truth_label = self.ip_dict[ip]['ground_truth_label']
            except KeyError:
                ground_truth_label = ''
            # Compute errors for this ip (and also accumulated)
            ip_error = self.compute_errors(predicted_label, ground_truth_label)
            print_info('IP: {:16},Ground Truth: {:30}, Predicted: {:30}. Error: {}'.format(ip, ground_truth_label, predicted_label, ip_error))
        # Compute performance metrics in this time slot
        self.compute_performance_metrics()
        print_info(cyan('\tFMeasure: {:.3f}, FPR: {:.3f}, TPR: {:.3f}, TNR: {:.3f}, FNR: {:.3f}, ErrorR: {:.3f}, Prec: {:.3f}, Accu: {:.3f}'.format(self.performance_metrics['FMeasure1'], self.performance_metrics['FPR'],self.performance_metrics['TPR'], self.performance_metrics['TNR'], self.performance_metrics['FNR'], self.performance_metrics['ErrorRate'], self.performance_metrics['Precision'], self.performance_metrics['Accuracy'])))

    def get_performance_metrics(self):
        """ return accumulated errors """
        return self.performance_metrics

    def get_errors(self):
        return self.acc_errors

    def __repr__(self):
        return ('TimeSlot start: {}, ends: {}'.format(self.init_time, self.finish_time))




######################
######################
######################
class Experiment(persistent.Persistent):
    """ An individual experiment """
    def __init__(self, id, description):
        self.id = id
        self.description = description
        # Dict of tuples in this experiment during testing
        self.tuples = {}
        # The vect of time slots
        self.time_slots = []
        self.time_slot_width = 300.0 # Now we hardcoded 300 seconds (5 mins), but it should be selected by the user
        print_info('Using the default model constructor for the testing netflow. If you need, change it.')
        self.total_errors = {}
        self.total_errors['TP'] = 0.0
        self.total_errors['TN'] = 0.0
        self.total_errors['FN'] = 0.0
        self.total_errors['FP'] = 0.0
        # NN is when the ground truth label is not determined
        self.total_errors['NN'] = 0.0
        self.total_performance_metrics = {}
        self.total_performance_metrics['TPR'] = -1
        self.total_performance_metrics['FPR'] = -1
        self.total_performance_metrics['TNR'] = -1
        self.total_performance_metrics['FNR'] = -1
        self.total_performance_metrics['ErrorRate'] = -1
        self.total_performance_metrics['Precision'] = -1
        self.total_performance_metrics['Accuracy'] = -1
        self.total_performance_metrics['FMeasure1'] = -1
        # Max amount of letters to use per tuple
        self.max_amount_to_check = 100

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

    def add_models_ids(self, models_ids):
        self.models_ids = models_ids

    def add_testing_id(self, testing_id):
        self.testing_id = testing_id

    def run(self):
        """ Run the experiment """
        # Train the models
        print_info('Models for detection: {}'.format(self.models_ids))
        group_mm = __group_of_markov_models__
        # This is necessary to get the models correctly from outside the class
        group_mm.run() 
        # Convert the str to int
        try:
            self.models_ids = map(int, self.models_ids.split(','))
        except ValueError:
            print_error('Could not split the models ids with ,')
            return False
        for model_id in self.models_ids:
            print_warning('Training model {}'.format(model_id))
            group_mm.train(model_id, "", self.models_ids, True)
        # Methodology 2. Train the thresholds of the training models between themselves
        # Methodology 3. Start the testing
        # Methodology 3.1. Get the binetflow file
        test_dataset = __datasets__.get_dataset(self.testing_id)
        self.file_obj = test_dataset.get_file(1)
        print_info('\nTesting with the netflow file: {}'.format(self.file_obj.get_name()))
        # Methodology 3.3. Process the netflow file for testing
        self.process_netflow_for_testing()

    def get_time_slot(self, column_values):
        """ Get the columns values and return the correct time slot object. Also closes the old time slot """
        starttime = datetime.strptime(column_values['StartTime'], '%Y/%m/%d %H:%M:%S.%f') 
        # Find the slot for this flow (theoretically it works with unordered flows)
        for slot in reversed(self.time_slots):
            if starttime >= slot.init_time and starttime <= slot.finish_time:
                return slot
        # Methodology 4.4. The first flow case and the case where the flow should be in a new flow because it is outside the last slot. All in one!
        new_slot = TimeSlot(starttime, self.time_slot_width)
        #print_info('New Slot Time: {}'.format(datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')))
        if self.time_slots:
            # We created a slot because the flow is outside the width, so we should close the previous time slot
            # Close the last slot
            print 'Closing slot {}. (Time: {})'.format(self.time_slots[-1], datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            self.time_slots[-1].close()
            # Store the errors in the experiment
            self.add_errors(self.time_slots[-1].get_errors())
        # Add it
        self.time_slots.append(new_slot)
        #raw_input()
        return new_slot

    def add_errors(self, errors):
        """ Get the errors of the last tuple and add them to the experiments errors """
        self.total_errors['TP'] += errors['TP']
        self.total_errors['TN'] += errors['TN']
        self.total_errors['FN'] += errors['FN']
        self.total_errors['FP'] += errors['FP']
        self.total_errors['NN'] += errors['NN']

    def get_total_errors(self):
        return self.total_errors

    def compute_total_performance_metrics(self):
        """ Compute the total performance metrics """
        try:
            self.total_performance_metrics['TPR'] = ( self.total_errors['TP'] ) / float(self.total_errors['TP'] + self.total_errors['FN'])
        except ZeroDivisionError:
            self.total_performance_metrics['TPR'] = -1
        try:
            self.total_performance_metrics['TNR'] = ( self.total_errors['TN'] ) / float( self.total_errors['TN'] + self.total_errors['FP'] )
        except ZeroDivisionError:
            self.total_performance_metrics['TNR'] = -1
        try:
            self.total_performance_metrics['FPR'] = ( self.total_errors['FP'] ) / float( self.total_errors['TN'] + self.total_errors['FP'] )
        except ZeroDivisionError:
            self.total_performance_metrics['FPR'] = -1
        try:
            self.total_performance_metrics['FNR'] = ( self.total_errors['FN'] ) / float(self.total_errors['TP'] + self.total_errors['FN'])
        except ZeroDivisionError:
            self.total_performance_metrics['FNR'] = -1
        try:
            self.total_performance_metrics['Precision'] = ( self.total_errors['TP'] ) / float(self.total_errors['TP'] + self.total_errors['FP'])
        except ZeroDivisionError:
            self.total_performance_metrics['Precision'] = -1
        try:
            self.total_performance_metrics['Accuracy'] = ( self.total_errors['TP'] + self.total_errors['TN'] ) / float( self.total_errors['TP'] + self.total_errors['TN'] + self.total_errors['FP'] + self.total_errors['FN'] )
        except ZeroDivisionError:
            self.total_performance_metrics['Accuracy'] = -1
        try:
            self.total_performance_metrics['ErrorRate'] = ( self.total_errors['FN'] + self.total_errors['FP'] ) / float( self.total_errors['TP'] + self.total_errors['TN'] + self.total_errors['FP'] + self.total_errors['FN'] )
        except ZeroDivisionError:
            self.total_performance_metrics['ErrorRate'] = -1
        self.beta = 1.0
        # With beta=1 F-Measure is also Fscore
        try:
            self.total_performance_metrics['FMeasure1'] = ( ( (self.beta * self.beta) + 1 ) * self.total_performance_metrics['Precision'] * self.total_performance_metrics['TPR']  ) / float( ( self.beta * self.beta * self.total_performance_metrics['Precision'] ) + self.total_performance_metrics['TPR'])
        except ZeroDivisionError:
            self.total_performance_metrics['FMeasure1'] = -1

    def process_netflow_for_testing(self):
        """ Get a netflow file and process it for testing """
        file = open(self.file_obj.get_name(), 'r')
        # Remove the header
        header_line = file.readline().strip()
        # Find the separation character
        self.find_separator(header_line)
        # Extract the columns names
        self.find_columns_names(header_line)
        line = file.readline().strip()
        # Methodology 4. For each flow
        start_time = datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        print_info('Start Time: {}'.format(start_time))
        group_group_of_models = __groupofgroupofmodels__ 
        # The constructor of models can change. Now we hardcode -1, but warning!
        group_id = str(self.testing_id) + '-1'
        group_of_models = group_group_of_models.get_group(group_id)
        # To store the winner train model
        new_distance = Detection(1) # The id is fake because we are not going to store the object
        winner_model_id = -1
        winner_model_distance = float('inf')
        # Get the structures
        structures = __database__.get_structures()
        training_structure_name = 'markov_models_1'
        training_structure = structures[training_structure_name]
        # Store some info about each training model, do it here and only once
        training_models = {}
        for model_training_id in self.models_ids:
            training_models[model_training_id] = {}
            training_models[model_training_id]['traininig_structure_name'] = training_structure_name
            training_models[model_training_id]['traininig_structure'] = training_structure
            try:
                training_models[model_training_id]['model_training'] = training_structure[int(model_training_id)]
            except:
                print_error('The training model id should be the id in the selected model structure. For example: markov_chains_1')
                return False
            training_models[model_training_id]['original_matrix'] = training_models[model_training_id]['model_training'].get_matrix()
            training_models[model_training_id]['original_self_prob'] = training_models[model_training_id]['model_training'].get_self_probability()
            training_models[model_training_id]['label'] = training_models[model_training_id]['model_training'].get_label().get_name()
            training_models[model_training_id]['threshold'] = training_models[model_training_id]['model_training'].get_threshold()
        while line:
            #print_warning('Netflow: {}'.format(line.split('s[')[0]))
            # Extract the column values
            column_values = self.extract_columns_values(line)
            # Methodology 4.1. Extract its 4-tuple. Find (or create) the tuple object
            tuple = self.get_tuple(column_values)
            # Methodology 4.2. Add all the relevant data to this tupple
            tuple.add_new_flow(column_values)
            # Methodology 4.3. Get the correct time slot
            time_slot = self.get_time_slot(column_values)
            # Add this src IP to the list of the time_slot
            time_slot.add_src_ip(tuple.get_src_ip())
            # Assign the ground truth label if we have one, only once for ip for time slot
            if tuple.get_ground_truth_label():
                time_slot.set_ground_truth_label_for_ip(tuple.get_src_ip(), tuple.get_ground_truth_label())
            #print 'Assigned to time slot: {}'.format(time_slot)
            # Methodology 4.4 Get the letter for this flow.
            model = group_of_models.get_model(tuple.get_id())
            test_state_so_far = model.get_state()[0:tuple.amount_of_flows]

            # IMPORTANT: Store the state so far in the tuple. Now we are cutting the max lenght, because the process is tooooo slow
            tuple.set_state_so_far(test_state_so_far[0:self.max_amount_to_check])
            # This is an issue. Right now I wont stop comparing after a max amount, but I should check this. The other idea is to only compare the states IN THIS timeslot and forget about the preivous ones...
            # If the tuple IN THIS TIME SLOT has already more than the max amount of flows to check, so ignore the new flows.
            #if len(tuple.get_state_so_far()) >= self.max_amount_to_check:
            #    line = file.readline().strip()
            #    continue

            #print '\tTuple: {}'.format(tuple)
            #print '\t\t\tStateSF: {} (0:100)'.format(test_state_so_far[0:100])
            #print_info('\t\tSetting the ground truth label for IP {}: {}'.format(tuple.get_src_ip(), tuple.get_ground_truth_label()))
            # Methodology 4.5 Compute the distance of the chain of states from this 4-tuple so far, with all the training models. Don't store a new distance object.
            # For each traininig model
            for model_training_id in self.models_ids:
                # Letters for the train model
                train_sequence = training_models[model_training_id]['model_training'].get_state()[0:tuple.get_state_len_so_far()]
                #print_info('Trai Seq: {}'.format(train_sequence))
                #print_info('Test Seq: {}'.format(test_state_so_far))
                # First re-create the matrix only for this sequence
                training_models[model_training_id]['model_training'].create(train_sequence)
                # Get the new original prob so far...
                training_original_prob = training_models[model_training_id]['model_training'].compute_probability(train_sequence)
                #print_info('\tTrain prob: {}'.format(training_original_prob))
                # Now obtain the probability for testing
                test_prob = training_models[model_training_id]['model_training'].compute_probability(tuple.get_state_so_far())
                #print_info('\tTest prob: {}'.format(test_prob))
                if training_original_prob < test_prob:
                    try:
                        prob_distance = training_original_prob / test_prob
                    except ZeroDivisionError:
                        prob_distance = -1
                elif training_original_prob > test_prob:
                    try:
                        prob_distance = test_prob / training_original_prob
                    except ZeroDivisionError:
                        prob_distance = -1
                elif training_original_prob == test_prob:
                    prob_distance = 1
                #print_info('Distance to model {} : {}'.format(model_training_id, prob_distance))
                # Methodology 4.6. Decide upon a winner model.
                # Is the probability just computed for this model lower than the threshold for that same model?
                print 'prob distance: {}, threshold of model: {}'.format(prob_distance, training_models[model_training_id]['threshold'])
                if prob_distance >= 1 and prob_distance <= training_models[model_training_id]['threshold']:
                    # The model is a candidate
                    if prob_distance < winner_model_distance:
                        # Is the winner so far
                        winner_model_distance = prob_distance
                        winner_model_id = model_training_id
            #if winner_model_id != -1:
            #    print_info('Winner model: {} ({}) with distance {}'.format(winner_model_id, training_models[winner_model_id]['label'], winner_model_distance))
            # Methodology 4.7. Extract the label and assign it
            time_slot.set_predicted_label_for_ip(tuple.get_src_ip(), training_models[model_training_id]['label'])
            #print_info('\t\tSetting the predicted label for IP {}: {}'.format(tuple.get_src_ip(), training_models[model_training_id]['label']))
            # Read next line
            line = file.readline().strip()
        # Close the file
        file.close()
        # Methodology 7 Compute the results of the last time slot
        self.time_slots[-1].close()
        print
        finish_time = datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        print_info('Finish Time: {} (Duration: {})'.format(finish_time, finish_time - start_time))
        # Print something about all the tuples
        print_info('Total amount of tuples: {}'.format(len(self.tuples)))
        print_info('Total time slots: {}'.format(len(self.time_slots)))
        # Methodology 7.1 Compute the performance metrics so far
        self.compute_total_performance_metrics()
        # Methodology 7.2 Print the total errors
        print_info('Total Errors: {}'.format(self.get_total_errors()))
        # Methodology 7.2 Print performance metric
        print_info('Total Performance Metrics:')
        print_info('\tFMeasure: {:.3f}, FPR: {:.3f}, TPR: {:.3f}, TNR: {:.3f}, FNR: {:.3f}, ErrorR: {:.3f}, Prec: {:.3f}, Accu: {:.3f}'.format(self.total_performance_metrics['FMeasure1'], self.total_performance_metrics['FPR'],self.total_performance_metrics['TPR'], self.total_performance_metrics['TNR'], self.total_performance_metrics['FNR'], self.total_performance_metrics['ErrorRate'], self.total_performance_metrics['Precision'], self.total_performance_metrics['Accuracy']))

    def get_tuple(self, column_values):
        """ Get the values and return the correct tuple for them """
        tuple4 = column_values['SrcAddr']+'-'+column_values['DstAddr']+'-'+column_values['Dport']+'-'+column_values['Proto']
        try:
            tuple = self.tuples[tuple4]
            # We already have this connection
        except KeyError:
            # First time for this connection
            tuple = Tuple(tuple4)
            self.tuples[tuple4] = tuple
        return tuple

    def find_columns_names(self, line):
        """ Usually the columns in a binetflow file are 
        StartTime,Dur,Proto,SrcAddr,Sport,Dir,DstAddr,Dport,State,sTos,dTos,TotPkts,TotBytes,SrcBytes,srcUdata,dstUdata,Label
        """
        self.columns_names = line.split(self.line_separator)
            
    def find_separator(self, line):
        count_commas = len(line.split(','))
        count_spaces = len(line.split(' '))
        if count_commas >= count_spaces:
            self.line_separator = ','
        elif count_spaces > count_commas:
            self.line_separator = ' '
        else:
            self.line_separator = ','

    def extract_columns_values(self, line):
        """ Given a line text of a flow, extract the values for each column """
        column_values = {}
        i = 0
        original_values = line.split(self.line_separator)
        temp_values = original_values
        if len(temp_values) > len(self.columns_names):
            # If there is only one occurrence of the separator char, then try to recover...
            # Find the index of srcudata
            srcudata_index_starts = 0
            for values in temp_values:
                if 's[' in values:
                    break
                else:
                    srcudata_index_starts += 1 
            # Find the index of dstudata
            dstudata_index_starts = 0
            for values in temp_values:
                if 'd[' in values:
                    break
                else:
                    dstudata_index_starts += 1 
            # Get all the src data
            srcudata_index_ends = dstudata_index_starts
            temp_srcudata = temp_values[srcudata_index_starts:srcudata_index_ends]
            srcudata = ''
            for i in temp_srcudata:
                srcudata = srcudata + i
            # Get all the dst data. The end is one before the last field. That we know is the label.
            dstudata_index_ends = len(temp_values) - 1
            temp_dstudata = temp_values[dstudata_index_starts:dstudata_index_ends]
            dstudata = ''
            for j in temp_dstudata:
                dstudata = dstudata + j
            label = temp_values[-1]
            end_of_good_data = srcudata_index_starts 
            # Rewrite temp_values
            temp_values = temp_values[0:end_of_good_data]
            temp_values.append(srcudata)
            temp_values.append(dstudata)
            temp_values.append(label)
        index = 0
        try:
            for value in temp_values:
                column_values[self.columns_names[index]] = value
                index += 1
        except IndexError:
            # Even with our fix, some data still has problems. Usually it means that there is no src data being sent, so we can not find the start of the data.
            print_error('There was some error reading the data inside a flow. Most surely it includes the field separator of the flows. We will keep the flow, but not its data.')
            # Just get the normal flow fields
            index = 0
            for value in temp_values:
                if index <= 13:
                    column_values[self.columns_names[index]] = value
                    index += 1
                else:
                    break
            column_values['srcUdata'] = 'Deleted because of inconsistencies'
            column_values['dstUdata'] = 'Deleted because of inconsistencies'
            column_values['Label'] = original_values[-1]
        return column_values

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
    description = 'Creates experiments with trained models on testing datasets. The structure of the training and testing models is fixed to markov_models_1 and the model constructor if fixed to \'-1\', so be careful.'
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
        # Set the description
        desc = raw_input("Description: ")
        # Create the new object
        new_experiment = Experiment(new_id, desc)
        # Methodology 1. We receive the markov_models ids for the training, and the id of the dataset of the tetsing. (We may not have markov models for the testing. A binetflow file and labels are enough)
        # Add info
        new_experiment.add_models_ids(models_ids)
        new_experiment.add_testing_id(testing_id)
        # Store on DB
        self.main_dict[new_id] = new_experiment
        # Run it
        new_experiment.run()



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
