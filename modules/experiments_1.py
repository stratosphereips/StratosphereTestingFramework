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
        # Start of flows is a number that indicates in which flow number we should start couting the state of this 4tuple. Used to 'move' a windows of states for each time slot.
        #self.start_of_flows = 0
        self.amount_of_flows = 0
        self.src_ip = tuple4.split('-')[0]
        # The ground truth label is assigned only once, because it will not change for the same tuple
        self.ground_truth_label_id = __group_of_labels__.search_connection_in_label(tuple4)
        # It could be that the tuple does not have a ground truth label
        if self.ground_truth_label_id:
            self.ground_truth_label = __group_of_labels__.get_label_name_by_id(self.ground_truth_label_id)
        self.state_so_far = ""
        # Used to move the amount of letters considered for this tuple in the time slot
        self.min_state_len = 0
        self.winner_model_id = False
        self.winner_model_distance = float('inf')

    def get_amount_of_flows(self):
        return self.amount_of_flows

    def get_max_state_len(self):
        """ The max state len is the amount of flows received """
        return self.amount_of_flows

    def update_min_state_len(self):
        """ Move the min state len to the max amount of flows we have """
        self.min_state_len = self.amount_of_flows
        
    def get_min_state_len(self):
        return self.min_state_len 

    def set_min_state_len(self, value):
        self.min_state_len = value

    def get_tuples_with_ip(self, ip):
        """ Return all the tuples with this src ip """
        tuples = []
        for tuple in self.tuples:
            if tuple.get_src_ip() == ip:
                tuples.append(tuple)
        return tuples

    def set_state_so_far(self, state):
        self.state_so_far = state

    def get_state_so_far(self):
        """ Return the state from the min state len """
        return self.state_so_far

    def get_src_ip(self):
        return self.src_ip

    def add_new_flow(self, column_values):
        """ Add new stuff about the flow in this tuple """
        self.datetime = column_values['StartTime']
        self.amount_of_flows += 1

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
        # To hold the tuples and if they matched in this time slot or not. used to move the states windows of each tuple
        self.tuples = {}

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
        # Set the predicted label
        if 'Botnet' in predicted_label or 'Malware' in predicted_label or 'CC' in predicted_label:
            predicted_label_positive = True
        elif 'Normal' in predicted_label or predicted_label == '':
            predicted_label_positive = False
        # Set the ground truth label
        if 'Botnet' in ground_truth_label or 'Malware' in ground_truth_label or 'CC' in ground_truth_label:
            ground_truth_label_positive = True
        elif 'Normal' in ground_truth_label:
            ground_truth_label_positive = False
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

    def add_tuple4(self, tuple4):
        """ add the tuple and src ip to the time slot """
        try:
            t = self.tuples[tuple4]
            # Is already there
        except KeyError:
            # Add it for the first time
            self.tuples[tuple4] = False
        # Now add the src ip
        src_ip = tuple4.split('-')[0]
        self.add_src_ip(src_ip)

    def add_src_ip(self, ip):
        """ Add the src ip to the time slot """
        try:
            dict = self.ip_dict[ip]
        except KeyError:
            self.ip_dict[ip] = {}

    def set_winner_model_distance_for_ip(self, ip, winner_model_distance):
        self.ip_dict[ip]['winner_model_distance'] = winner_model_distance

    def get_winner_model_distance_for_ip(self, ip):
        return self.ip_dict[ip]['winner_model_distance']

    def set_winner_model_id_for_ip(self, ip, winner_model_id):
        """ The winner model id is always the winner model in the last flow, so it may change on each flow """
        self.ip_dict[ip]['winner_model_id'] = winner_model_id

    def get_winner_model_id_for_ip(self, ip):
        return self.ip_dict[ip]['winner_model_id']

    def set_ground_truth_label_for_ip(self, ip, ground_truth_label):
        """ The logic to select which ground_truth_label is assigned to an IP. Because we can have multiple labels because of multiple tuples for the same ip """
        try:
            current = self.ip_dict[ip]['ground_truth_label'] 
            # We change the ground_truth_label only if it is Normal or Background. Don't change any Botnet labels.
            if current and 'normal' not in current.lower() and 'background' not in current.lower() and current != ground_truth_label:
                self.ip_dict[ip]['ground_truth_label'] = ground_truth_label
                #print '\tAssigning GTL to ip {}: {}'.format(ip, ground_truth_label)
        except KeyError:
            # First time
            self.ip_dict[ip]['ground_truth_label'] = ground_truth_label
            #print '\tAssigning first time GTL in this time slot to IP {}: {}'.format(ip, ground_truth_label)

    def unset_predicted_label_for_ip(self, ip, new_predicted_label, num_state, tuple_id):
        """ Get the ip, new_predicted_label num_state and tuple_id and unset it from the predictions. This is because it can happend that the model stop matching after some flows, i.e. its distance is above the threshold """
        try:
            current_predicted_tuple = self.ip_dict[ip]['predicted_labels'][-1][2]
            current_predicted_label = self.ip_dict[ip]['predicted_labels'][-1][0]
            if current_predicted_tuple == tuple_id:
                # Delete the last
                self.ip_dict[ip]['predicted_labels'] = self.ip_dict[ip]['predicted_labels'][:-1]
                #print_info('Deleting the last match for IP {}, from tuple {}, with label {}, at {} letters.'.format(ip, tuple_id, current_predicted_label, num_state))
        except (KeyError, IndexError):
            # This ip didn't have a prediction yet.
            pass

    def set_predicted_label_for_ip(self, ip, new_predicted_label, num_state, tuple_id):
        """ Store the new predicted label for this ip. Also store at which len of the state latter this label was assigned. Also store the tuple that generated this match."""
        try:
            # Since we append, the last position has the lastest label. And from there 0 is the label and 1 the amount
            current_label = self.ip_dict[ip]['predicted_labels'][-1][0] 
            # This if does not only avoid putting the same label again, but also avoids overwritting the first number when it happened.
            if current_label != new_predicted_label:
                self.ip_dict[ip]['predicted_labels'].append((new_predicted_label, num_state, tuple_id))
                #print '\tAssigning predicted label to ip {}: {} (after {} letters)'.format(ip, new_predicted_label, num_state)
        except (KeyError, IndexError):
            # First time
            self.ip_dict[ip]['predicted_labels'] = []
            self.ip_dict[ip]['predicted_labels'].append((new_predicted_label, num_state, tuple_id))
            #print '\tAssigning first time predicted label to ip {}: {} (after {} letters)'.format(ip, new_predicted_label, num_state)
        #print '\tAssigning predicted label to ip {}: {} (after {} letters)'.format(ip, new_predicted_label, num_state)

    def get_num_letters_for_label(self, label, ip):
        try:
            for data in self.ip_dict[ip]['predicted_labels']:
                pred_label = data[0]
                num_letters = data[1]
                if pred_label == label:
                    return num_letters
        except KeyError:
            #print_error('There is no predicted label for this ip {}'.format(ip))
            return -1

    def get_predicted_label(self, ip):
        try:
            # The last assigned label (-1) is the final one
            ip_data = self.ip_dict[ip]
            try:
                return self.ip_dict[ip]['predicted_labels'][-1][0]
            except IndexError:
                # Predicted labels is empty
                return ''
        except KeyError:
            #print_error('There is no predicted label for this ip {}'.format(ip))
            return ''

    def close(self):
        """ Close the slot """
        #  - Compute the errors (TP, TN, FN, FP) for all the IPs in this time slot.
        for ip in self.ip_dict:
            predicted_label = self.get_predicted_label(ip)
            num_letters = self.get_num_letters_for_label(predicted_label, ip)
            try:
                ground_truth_label = self.ip_dict[ip]['ground_truth_label']
            except KeyError:
                ground_truth_label = ''
            # Compute errors for this ip (and also accumulated)
            ip_error = self.compute_errors(predicted_label, ground_truth_label)
            print_info('IP: {:16},Ground Truth: {:30}, Predicted: {:30} (at {} letters). Error: {}'.format(ip, ground_truth_label, predicted_label, num_letters, ip_error))
        # Compute performance metrics in this time slot
        self.compute_performance_metrics()
        print_info(cyan('\tFMeasure: {:.3f}, FPR: {:.3f}, TPR: {:.3f}, TNR: {:.3f}, FNR: {:.3f}, ErrorR: {:.3f}, Prec: {:.3f}, Accu: {:.3f}'.format(self.performance_metrics['FMeasure1'], self.performance_metrics['FPR'],self.performance_metrics['TPR'], self.performance_metrics['TNR'], self.performance_metrics['FNR'], self.performance_metrics['ErrorRate'], self.performance_metrics['Precision'], self.performance_metrics['Accuracy'])))
        #raw_input()

    def get_performance_metrics(self):
        """ return accumulated errors """
        return self.performance_metrics

    def set_4tuple_unmatch(self, tuple4):
        """ Get a 4tuple and mark it in our dict as unMatched. When the model stop matching. """
        try:
            self.tuples[tuple4] = False
        except KeyError:
            # Tuple was never stored. This should not happen
            print_error('This tuple was never stored in the time slot. Weird.')
            return False


    def set_4tuple_match(self, tuple4):
        """ Get a 4tuple and mark it in our dict as Matched """
        try:
            self.tuples[tuple4] = True
        except KeyError:
            # Tuple was never stored. This should not happen
            print_error('This tuple was never stored in the time slot. Weird.')
            return False

    def get_matching_tuples(self):
        """ Return the matching tuples in this time slot """
        matching = []
        for tuple in self.tuples:
            if self.tuples[tuple]:
                matching.append(tuple)
        return matching

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
            group_mm.train(model_id, "", self.models_ids, False)
        # Methodology 2. Train the thresholds of the training models between themselves
        # Methodology 3. Start the testing
        # Methodology 3.1. Get the binetflow file
        test_dataset = __datasets__.get_dataset(self.testing_id)
        try:
            self.file_obj = test_dataset.get_file_type('binetflow')
        except AttributeError:
            print_error('That testing dataset does no seem to exist.')
            return False
        print_info('\nTesting with the netflow file: {}'.format(self.file_obj.get_name()))
        # Methodology 3.3. Process the netflow file for testing
        self.process_netflow_for_testing()

    def get_time_slot(self, column_values):
        """ Get the columns values and return the correct time slot object. Also closes the old time slot """
        starttime = datetime.strptime(column_values['StartTime'], '%Y/%m/%d %H:%M:%S.%f') 
        # Find the slot for this flow (theoretically it works with unordered flows). This is the check of times for getting inside a timetime  slot.
        for slot in reversed(self.time_slots):
            if starttime >= slot.init_time and starttime <= slot.finish_time:
                return slot
        # Methodology 4.4. The first flow case and the case where the flow should be in a new flow because it is outside the last slot. All in one!
        new_slot = TimeSlot(starttime, self.time_slot_width)
        if self.time_slots:
            # Move the state windows in the tuples that already matched in this time slot. Before closing the time windoows!
            self.move_windows_in_matched_tuples()
            # We created a slot because the flow is outside the width, so we should close the previous time slot
            # Close the last slot
            print 'Closing {}. (Time: {})'.format(self.time_slots[-1], datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            self.time_slots[-1].close()
            # Store the errors in the experiment
            self.add_errors(self.time_slots[-1].get_errors())
        # Add it
        self.time_slots.append(new_slot)
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
        start_time = datetime.now()
        print_info('Start Time: {}'.format(start_time))
        group_group_of_models = __groupofgroupofmodels__ 
        # The constructor of models can change. Now we hardcode -1, but warning!
        group_id = str(self.testing_id) + '-1'
        group_of_models = group_group_of_models.get_group(group_id)
        # To store the winner train model
        new_distance = Detection(1) # The id is fake because we are not going to store the object
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
            tuple4 = column_values['SrcAddr']+'-'+column_values['DstAddr']+'-'+column_values['Dport']+'-'+column_values['Proto']
            # Get the old tuple object for it, or get a new tuple object
            tuple = self.get_tuple(tuple4)
            # Methodology 4.2. Add all the relevant data to this tupple
            tuple.add_new_flow(column_values)
            # Methodology 4.3. Get the correct time slot. If the flow is outside the time slot, it will close the last time slot.
            time_slot = self.get_time_slot(column_values)
            # Add this 4tuple and src IP to the list on the time_slot
            time_slot.add_tuple4(tuple4)
            # Assign the ground truth label if we have one, only once for ip for time slot
            if tuple.get_ground_truth_label():
                time_slot.set_ground_truth_label_for_ip(tuple.get_src_ip(), tuple.get_ground_truth_label())
                #print_info('\t\tSetting the ground truth label for IP {}: {}'.format(tuple.get_src_ip(), tuple.get_ground_truth_label()))
            # Methodology 4.4 Get the letter for this flow. i.e. find the model we have stored for this test tuple.
            model = group_of_models.get_model(tuple.get_id())
            if model:
                # Take the letters from the test model, but not all of them, just the ones inside this time slot. This way we 'move' the letters used from time windows to time windows, but only if there was a model match.
                # Store the state so far in the tuple. Now we are cutting the original state. Min is the amount defined if this tuple had already matched before. Max is just the amount of flows recived so far.
                tuple.set_state_so_far(model.get_state()[tuple.get_min_state_len():tuple.get_max_state_len()])
            else:
                print_error('No model for this tuple!!!')
                return False
            #print 'Test state so far: {}'.format(tuple.get_state_so_far())
            #print '\tTuple: {}'.format(tuple)
            # Reset the winner variables.
            time_slot.set_winner_model_id_for_ip(tuple.get_src_ip(), False)
            time_slot.set_winner_model_distance_for_ip(tuple.get_src_ip(),'inf')
            # Methodology 4.5 Compute the distance of the chain of states from this 4-tuple so far, with all the training models. Don't store a new distance object.
            # For each traininig model
            for model_training_id in self.models_ids:
                # Letters for the train model. They should not be 'cut' like the test ones. Train models should be complete.
                #train_sequence = training_models[model_training_id]['model_training'].get_state()[0:tuple.get_amount_of_flows()]
                train_sequence = training_models[model_training_id]['model_training'].get_state()[tuple.get_min_state_len():tuple.get_amount_of_flows()]
                #print_info('Trai Seq: {}'.format(train_sequence))
                #print_info('Test Seq: {}'.format(tuple.get_state_so_far()))
                # First re-create the matrix only for this sequence
                training_models[model_training_id]['model_training'].create(train_sequence)
                # Get the new original prob so far...
                training_original_prob = training_models[model_training_id]['model_training'].compute_probability(train_sequence)
                #print_info('\tTrain prob: {}'.format(training_original_prob))
                # Now obtain the probability for testing
                test_prob = training_models[model_training_id]['model_training'].compute_probability(tuple.get_state_so_far())
                #print_info('\tTest prob: {}'.format(test_prob))
                # Get the distance
                prob_distance = -1
                if training_original_prob != -1 and test_prob != -1 and training_original_prob <= test_prob:
                    try:
                        prob_distance = training_original_prob / test_prob
                    except ZeroDivisionError:
                        prob_distance = -1
                elif training_original_prob != -1 and test_prob != -1 and training_original_prob > test_prob:
                    try:
                        prob_distance = test_prob / training_original_prob
                    except ZeroDivisionError:
                        prob_distance = -1
                #print_info('\tDistance to model id {:6}, {:50} (thres: {}):\t{}'.format(model_training_id, training_models[model_training_id]['label'], training_models[model_training_id]['threshold'], prob_distance))
                #print_info('\t\tDistance to model {} ({}) : {}'.format(model_training_id, training_models[model_training_id]['label'], prob_distance))
                # Methodology 4.6. Decide upon a winner model.
                # Is the probability just computed for this model lower than the threshold for that same model?
                if prob_distance >= 1 and prob_distance <= training_models[model_training_id]['threshold']:
                    # The model is a candidate
                    if prob_distance < time_slot.get_winner_model_distance_for_ip(tuple.get_src_ip()):
                        # The model is the winner so far
                        time_slot.set_winner_model_id_for_ip(tuple.get_src_ip(), model_training_id)
                        time_slot.set_winner_model_distance_for_ip(tuple.get_src_ip(), prob_distance)
            # If there is a winning model, just assign it.
            if time_slot.get_winner_model_id_for_ip(tuple.get_src_ip()):
                #print_info('Winner model for IP {}: {} ({}) with distance {}'.format(tuple.get_src_ip(), time_slot.get_winner_model_id_for_ip(tuple.get_src_ip()), training_models[time_slot.get_winner_model_id_for_ip(tuple.get_src_ip())]['label'], time_slot.get_winner_model_distance_for_ip(tuple.get_src_ip())))
                # Methodology 4.7. Extract the label and assign it
                time_slot.set_predicted_label_for_ip(tuple.get_src_ip(), training_models[time_slot.get_winner_model_id_for_ip(tuple.get_src_ip())]['label'], tuple.get_amount_of_flows(), tuple.get_id())
                #print_info('\t\tSetting the predicted label for IP {}: {}'.format(tuple.get_src_ip(), training_models[model_training_id]['label']))
                # Methodology 4.8. Mark the 4tuple as 'matched' in the time slot. This is used later to know, from all the 4tuples, which ones we should move their states window.
                time_slot.set_4tuple_match(tuple4)
            # Did we have a winner in the past, but not now anymore??? Erase its label as the current winner.
            elif time_slot.get_winner_model_id_for_ip(tuple.get_src_ip()) == False:
                #print_info('Erase the winner model for IP {}'.format(tuple.get_src_ip()))
                time_slot.unset_predicted_label_for_ip(tuple.get_src_ip(), False, tuple.get_amount_of_flows(), tuple.get_id())
                time_slot.set_4tuple_unmatch(tuple.get_id())
            # Read next line
            line = file.readline().strip()
            #raw_input()
        # Close the file
        file.close()
        # Move the state windows in the tuples that already matched in this time slot. Before closing the time windoows!
        self.move_windows_in_matched_tuples()
        # Methodology 7 Compute the results of the last time slot
        self.time_slots[-1].close()
        print
        finish_time = datetime.now()
        print_info('Finish Time: {} (Duration: {})'.format(unicode(finish_time), unicode(finish_time - start_time)))
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

    def move_windows_in_matched_tuples(self):
        """ Ask for all the tuples that had matches in this time slot and move their state letters windows. This is run after the closing of the time slot. Be careful """
        matching_tuples = self.time_slots[-1].get_matching_tuples()
        for tuple4 in matching_tuples:
            # First get how far the state has gone in the current time slot. Not the state number when it was detected first, but the state number when the time slot finished.
            # 'move' the start of the letters to where it finished in the last time slot that matched.
            self.tuples[tuple4].update_min_state_len()
            #print '\tMatched tuple {}. Min len moved to {}'.format(tuple4, self.tuples[tuple4].get_min_state_len())

    def get_tuple(self, tuple4):
        """ Get the values and return the correct tuple for them """
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
