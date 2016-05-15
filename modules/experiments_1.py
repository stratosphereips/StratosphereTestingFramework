# Part of this file was taken from Viper - https://github.com/botherder/viper
# The rest is from the Stratosphere Testing Framework
# See the file 'LICENSE' for copying permission.

# This is a template module showing how to create a module that has persistence in the database. To create your own command just copy this file and start modifying it.

import persistent
import BTrees.OOBTree
import re

from stf.common.out import *
from stf.common.abstracts import Module
from stf.core.models import __groupofgroupofmodels__ 
from stf.core.models import Model
from stf.core.dataset import __datasets__
from stf.core.notes import __notes__
from stf.core.connections import __group_of_group_of_connections__
from stf.core.connections import Flow
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
    def __init__(self, tuple4, dataset_id):
        self.id = tuple4
        self.ground_truth_label = ""
        self.datetime = ""
        # Start of flows is a number that indicates in which flow number we should start couting the state of this 4tuple. Used to 'move' a windows of states for each time slot.
        self.amount_of_flows = 0
        self.src_ip = tuple4.split('-')[0]
        # The ground truth label is assigned only once, because it will not change for the same tuple
        self.ground_truth_label_id = __group_of_labels__.search_connection_in_label(tuple4, dataset_id)
        if self.ground_truth_label_id:
            self.ground_truth_label = __group_of_labels__.get_label_name_by_id(self.ground_truth_label_id)
        # It could be that the tuple does not have a ground truth label
        elif not self.ground_truth_label_id:
            # If the tuple4 didn't have a label, assign to it the label of its source IP, if there is one...
            srcip = tuple4.split('-')[0]
            # Get the label id of the label of the src IP
            self.ground_truth_label_id_for_ip = __group_of_labels__.search_connection_in_label(srcip, dataset_id)
            if self.ground_truth_label_id_for_ip:
                # Assign the label of the IP to the label of the tuple
                self.ground_truth_label = __group_of_labels__.get_label_name_by_id(self.ground_truth_label_id_for_ip)
        # The state of the tuple so far (because it can still grow)
        self.state_so_far = ""
        # Used to move the amount of letters considered for this tuple in the time slot
        self.min_state_len = 0
        self.winner_model_id = False
        self.winner_model_distance = float('inf')
        self.proto = ""
        # If the state was ever 'moved' by the update then store it
        self.updated = False

    def is_updated(self):
        return self.updated

    def get_state_len(self):
        return len(self.state_so_far)

    def get_proto(self):
        return self.proto

    def get_amount_of_flows(self):
        return self.amount_of_flows

    def get_max_state_len(self):
        """ The max state len is the amount of flows received """
        return self.amount_of_flows

    def update_min_state_len(self):
        """ Move the min state len to the amount of flows we have now"""
        self.min_state_len = self.amount_of_flows
        self.updated = True
        
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
        # The time stored is the time of the last netflow assigned
        self.datetime = column_values['StartTime']
        self.proto = column_values['Proto']
        self.amount_of_flows += 1

    def get_last_time(self):
        return self.datetime

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
        # Metrics for the IP detection counting all the time windows together
        self.performance_metrics = {}
        self.performance_metrics['TPR'] = -1
        self.performance_metrics['FPR'] = -1
        self.performance_metrics['TNR'] = -1
        self.performance_metrics['FNR'] = -1
        self.performance_metrics['ErrorRate'] = -1
        self.performance_metrics['Precision'] = -1
        self.performance_metrics['Accuracy'] = -1
        self.performance_metrics['FMeasure1'] = -1
        # Metrics for the IPs detection of the complete experiment as a whole
        self.performance_metrics_for_final_ips = {}
        self.performance_metrics_for_final_ips['TPR'] = -1
        self.performance_metrics_for_final_ips['FPR'] = -1
        self.performance_metrics_for_final_ips['TNR'] = -1
        self.performance_metrics_for_final_ips['FNR'] = -1
        self.performance_metrics_for_final_ips['ErrorRate'] = -1
        self.performance_metrics_for_final_ips['Precision'] = -1
        self.performance_metrics_for_final_ips['Accuracy'] = -1
        self.performance_metrics_for_final_ips['FMeasure1'] = -1
        self.results_dict = {}
        # To hold the tuples and if they matched in this time slot or not. used to move the states windows of each tuple
        self.tuples = {}
        self.verbose = 0

    def get_acc_errors(self):
        return self.acc_errors

    def set_verbose(self, verbose):
        self.verbose = verbose

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
        """ This coded is copied to the distances modules """
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
        # Add the src ip
        src_ip = tuple4.split('-')[0]
        self.add_src_ip(src_ip)
        try:
            t = self.tuples[tuple4]
            # Is already there
        except KeyError:
            # Add it for the first time
            self.tuples[tuple4] = False


    def add_src_ip(self, ip):
        """ Add the src ip to the time slot """
        try:
            dict = self.ip_dict[ip]
        except KeyError:
            self.ip_dict[ip] = {}
            # If this is the first time we see this IP in this timeslot, erase the winner model
            self.set_winner_model_id_for_ip(ip, False)
            self.set_winner_model_distance_for_ip(ip,'inf')

    def set_winner_model_distance_for_ip(self, ip, winner_model_distance):
        self.ip_dict[ip]['winner_model_distance'] = winner_model_distance

    def get_predicted_model_id_for_ip(self, ip):
        try:
            return self.ip_dict[ip]['predicted_labels'][-1][3]
        except IndexError:
            return False

    def get_predicted_model_distance_for_ip(self, ip):
        return self.ip_dict[ip]['predicted_labels'][-1][4]

    def get_winner_model_distance_for_ip(self, ip):
        return self.ip_dict[ip]['winner_model_distance']

    def set_winner_model_id_for_ip(self, ip, winner_model_id):
        """ The winner model id is always the winner model in the last flow, so it may change on each flow """
        self.ip_dict[ip]['winner_model_id'] = winner_model_id

    def get_winner_model_id_for_ip(self, ip):
        return self.ip_dict[ip]['winner_model_id']

    def set_ground_truth_label_for_ip(self, ip, ground_truth_label):
        """ The logic to select which ground_truth_label is assigned to an IP. Because we can have multiple labels because of multiple tuples for the same ip """
        # Here just store the label as one more label for this ip
        self.ip_dict[ip]['ground_truth_labels'] = []
        self.ip_dict[ip]['ground_truth_labels'].append(ground_truth_label)

    def unset_predicted_label_for_ip(self, ip, new_predicted_label, num_state, tuple_id):
        """ Get the ip, new_predicted_label num_state and tuple_id and unset it from the predictions. This is because it can happend that the model stop matching after some flows, i.e. its distance is above the threshold """
        try:
            current_predicted_tuple = self.ip_dict[ip]['predicted_labels'][-1][2]
            current_predicted_label = self.ip_dict[ip]['predicted_labels'][-1][0]
            if current_predicted_tuple == tuple_id:
                # Delete the last
                self.ip_dict[ip]['predicted_labels'] = self.ip_dict[ip]['predicted_labels'][:-1]
                if self.verbose > 2:
                    print_info('Deleting the last match for IP {}, from tuple {}, with label {}, at {} letters.'.format(ip, tuple_id, current_predicted_label, num_state))
        except (KeyError, IndexError):
            # This ip didn't have a prediction yet.
            pass

    def set_predicted_label_for_ip(self, ip, new_predicted_label, num_state, tuple_id, model_id, distance):
        """ Store the new predicted label for this ip. Also store at which len of the state latter this label was assigned. Also store the tuple that generated this match. Also store the model id that matched"""
        try:
            # Since we append, the last position has the lastest label. And from there 0 is the label and 1 the num of states
            current_label = self.ip_dict[ip]['predicted_labels'][-1][0] 
            # This if does not only avoid putting the same label again, but also avoids overwritting the first number when it happened.
            if current_label != new_predicted_label:
                self.ip_dict[ip]['predicted_labels'].append((new_predicted_label, num_state, tuple_id, model_id, distance))
        except (KeyError, IndexError):
            # First time
            self.ip_dict[ip]['predicted_labels'] = []
            self.ip_dict[ip]['predicted_labels'].append((new_predicted_label, num_state, tuple_id, model_id, distance))
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
                #####
                # Now we only get the last label assigned, BUT THIS MUST BE MORE COMPLEX!!!!!!!! This line can be a whole new project.
                #####
                return self.ip_dict[ip]['predicted_labels'][-1][0]
            except IndexError:
                # Predicted labels is empty
                return ''
        except KeyError:
            #print_error('There is no predicted label for this ip {}'.format(ip))
            return ''
    
    def get_ground_truth_label(self, ip):
        """ Return the ground truth label for this IP. That means, only Botnet, Malware or Normal... not the whole info of the tuple """
        botnet_labels = 0
        normal_labels = 0
        try:
            labels = self.ip_dict[ip]['ground_truth_labels']
        except KeyError:
            return 'Background'
        for label in labels:
            if 'Malware' in label or 'Botnet' in label:
                botnet_labels += 1
            elif 'Normal' in label:
                normal_labels += 1
        if botnet_labels:        
            return 'Botnet'
        elif normal_labels:
            return 'Normal'
        else:
            return 'Background'

    def get_tp_ips(self):
        """ Return the TP ips in this slot """
        res = []
        for ip in self.ip_dict:
            if 'TP' in self.ip_dict[ip]['error']:
                res.append(ip)
        return res

    def get_fp_ips(self):
        """ Return the FP ips in this slot """
        res = []
        for ip in self.ip_dict:
            if 'FP' in self.ip_dict[ip]['error']:
                res.append(ip)
        return res

    def get_fn_ips(self):
        """ Return the FN ips in this slot """
        res = []
        for ip in self.ip_dict:
            if 'FN' in self.ip_dict[ip]['error']:
                res.append(ip)
        return res

    def get_tn_ips(self):
        """ Return the TN ips in this slot """
        res = []
        for ip in self.ip_dict:
            if 'TN' in self.ip_dict[ip]['error']:
                res.append(ip)
        return res

    def close(self, verbose):
        """ Close the slot """
        #  - Compute the errors (TP, TN, FN, FP) for all the IPs in this time slot.
        for ip in self.ip_dict:
            predicted_label = self.get_predicted_label(ip)
            # Since we are closing the time slot, the last predicted label, is now the final one
            num_letters = self.get_num_letters_for_label(predicted_label, ip)
            ground_truth_label = self.get_ground_truth_label(ip)
            # Compute errors for this ip (and also accumulated)
            ip_error = self.compute_errors(predicted_label, ground_truth_label)
            # Store the error for this IP
            self.ip_dict[ip]['error'] = ip_error
            if verbose > 1:
                tcolor=str
                if ip_error=='FN':
                    tcolor=magenta
                elif ip_error=='TP':
                    tcolor=yellow
                elif ip_error=='TN':
                    tcolor=green
                elif ip_error=='FP':
                    tcolor=red
                print('\tIP: {:16}, Ground Truth: {:30}, Predicted: {:30} (at {} letters). Error: {}'.format(ip, tcolor(ground_truth_label), tcolor(predicted_label), num_letters, ip_error))
            if verbose > 0:
                if ip_error == 'TP':
                    print(red('\tTrue Detected IPs:'))
                    print('\t\tIP: {:16} (at {} flows)'.format(red(ip), red(str(num_letters))))
                elif ip_error == 'FP':
                    print(bold(red('\tFalse Detected IPs:')))
                    print('\t\tIP: {:16} (at {} flows)'.format(bold(red(ip)), bold(red(str(num_letters)))))
            #print 'IP dict for ip {}: {}'.format(ip, self.ip_dict[ip])
        # Compute performance metrics in this time slot
        self.compute_performance_metrics()
        if verbose > 1:
            print_info(cyan('\tFMeasure: {:.3f}, FPR: {:.3f}, TPR: {:.3f}, TNR: {:.3f}, FNR: {:.3f}, ErrorR: {:.3f}, Prec: {:.3f}, Accu: {:.3f}'.format(self.performance_metrics['FMeasure1'], self.performance_metrics['FPR'],self.performance_metrics['TPR'], self.performance_metrics['TNR'], self.performance_metrics['FNR'], self.performance_metrics['ErrorRate'], self.performance_metrics['Precision'], self.performance_metrics['Accuracy'])))
        if verbose > 9:
            # Stop after each timeslot
            raw_input()
        # Clean the tuples in this timeslot
        self.clean_tuples()

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

    def get_unmatching_tuples(self):
        """ Return the unmatching tuples in this time slot """
        unmatching = []
        for tuple in self.tuples:
            if not self.tuples[tuple]:
                unmatching.append(tuple)
        return unmatching

    def get_errors(self):
        return self.acc_errors

    def __repr__(self):
        return ('TimeSlot start: {}, ends: {}'.format(self.init_time, self.finish_time))

    def clean_tuples(self):
        """ Clean the timeslot of the info about tuples, so we don't store them """
        self.tuples = {}




######################
######################
######################
class Experiment(persistent.Persistent):
    """ An individual experiment """
    def __init__(self, id, description, timeslotwidth, filter, structure_name):
        self.filter = filter
        self.id = id
        self.description = description
        # Dict of tuples in this experiment during testing
        self.tuples = {}
        # The name of the structure where the trainings ids should be taken from
        self.structure_name = structure_name
        # The vect of time slots
        self.time_slots = []
        self.time_slot_width = timeslotwidth
        print_info('Using the default model constructor for the testing netflow. If you need, change it.')
        self.total_errors = {}
        self.total_errors['TP'] = 0.0
        self.total_errors['TN'] = 0.0
        self.total_errors['FN'] = 0.0
        self.total_errors['FP'] = 0.0
        # NN is when the ground truth label is not determined
        self.total_errors['NN'] = 0.0
        # Perf metrics for the ip detection of the total erorrs counted in all the time windows
        self.total_performance_metrics = {}
        self.total_performance_metrics['TPR'] = -1
        self.total_performance_metrics['FPR'] = -1
        self.total_performance_metrics['TNR'] = -1
        self.total_performance_metrics['FNR'] = -1
        self.total_performance_metrics['ErrorRate'] = -1
        self.total_performance_metrics['Precision'] = -1
        self.total_performance_metrics['Accuracy'] = -1
        self.total_performance_metrics['FMeasure1'] = -1
        # Perf metrics for the ip detection of the whole experiment
        self.total_performance_metrics_for_final_ips = {}
        self.total_performance_metrics_for_final_ips['TPR'] = -1
        self.total_performance_metrics_for_final_ips['FPR'] = -1
        self.total_performance_metrics_for_final_ips['TNR'] = -1
        self.total_performance_metrics_for_final_ips['FNR'] = -1
        self.total_performance_metrics_for_final_ips['ErrorRate'] = -1
        self.total_performance_metrics_for_final_ips['Precision'] = -1
        self.total_performance_metrics_for_final_ips['Accuracy'] = -1
        self.total_performance_metrics_for_final_ips['FMeasure1'] = -1
        # Max amount of letters to use per tuple
        self.max_amount_to_check = 100
        # To store the info of IPs detected. 'TP', 'FP', 'FN', 'TN'
        self.final_ips = {}
        self.final_ips['TP'] = []
        self.final_ips['TN'] = []
        self.final_ips['FP'] = []
        self.final_ips['FN'] = []
        self.training_models = {}
        # Here we store the testing models that we found but that they are not in the database.
        self.testing_models = {}

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
            if key == 'conn':
                tuple = model
                if operator == '=':
                    if value in tuple:
                        responses.append(True)
                    else:
                        responses.append(False)
                elif operator == '!=':
                    if value not in tuple:
                        responses.append(True)
                    else:
                        responses.append(False)
            else:
                return False
        for response in responses:
            if not response:
                return False
        return True

    def get_training_models(self):
        return self.training_models

    def get_time_slots(self):
        return self.time_slots

    def get_fancy_performance_metrics(self):
        text = ''
        for error in self.total_performance_metrics:
            text += '{}: {:.3f}. '.format(error, self.total_performance_metrics[error])
        return text

    def get_performance_metrics(self):
        return self.total_performance_metrics

    def get_tuples(self):
        return self.tuples

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

    def get_testing_id(self):
        return self.testing_id

    def add_testing_id(self, testing_id):
        self.testing_id = testing_id

    def run(self, verbose):
        """ Run the experiment """
        # Train the models
        self.verbose = verbose
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
        # Methodology 2. Train the thresholds of the training models between themselves
        # Methodology 3. Start the testing
        # Methodology 3.1. Get the binetflow file
        self.test_dataset = __datasets__.get_dataset(self.testing_id)
        try:
            self.file_obj = self.test_dataset.get_file_type('binetflow')
        except AttributeError:
            print_error('That testing dataset does no seem to exist.')
            return False
        try:
            print_info('\nTesting with the netflow file: {}'.format(self.file_obj.get_name()))
        except AttributeError:
            print_error('There is no binetflow file available. Did you generate it with dataset -g?')
            return False
        # Methodology 3.3. Process the netflow file for testing
        self.process_netflow_for_testing()

    def get_time_slot(self, column_values):
        """ Get the columns values and return the correct time slot object. Also closes the old time slot """
        starttime = datetime.strptime(column_values['StartTime'], '%Y/%m/%d %H:%M:%S.%f') 
        # Find the slot for this flow (theoretically it works with unordered flows). This is the check of times for getting inside a timetime slot.
        for slot in reversed(self.time_slots):
            if starttime >= slot.init_time and starttime <= slot.finish_time:
                return slot
        # Methodology 4.4. The first flow case and the case where the flow should be in a new flow because it is outside the last slot. All in one!
        new_slot = TimeSlot(starttime, self.time_slot_width)
        if self.time_slots:
            # We just created a new slot because the current flow is outside the width of the current slot, so we should close the previous time slot first
            # Close the last slot
            if self.verbose > 1:
                print 'Closing  {}. (Time: {})'.format(self.time_slots[-1], datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            self.time_slots[-1].close(self.verbose)
            # After closing the time slot, we should get some info back
            tp_ips_in_last_time_slot = self.time_slots[-1].get_tp_ips()
            fp_ips_in_last_time_slot = self.time_slots[-1].get_fp_ips()
            fn_ips_in_last_time_slot = self.time_slots[-1].get_fn_ips()
            tn_ips_in_last_time_slot = self.time_slots[-1].get_tn_ips()
            self.add_tp_ips(tp_ips_in_last_time_slot)
            self.add_fp_ips(fp_ips_in_last_time_slot)
            self.add_fn_ips(fn_ips_in_last_time_slot)
            self.add_tn_ips(tn_ips_in_last_time_slot)
            # Store the errors in the experiment
            self.add_errors(self.time_slots[-1].get_errors())
            # Move the state windows in the tuples that have more than a threshold of letters. After closing the time windoows
            self.move_windows_in_tuples()
        # Add it
        self.time_slots.append(new_slot)
        if self.verbose > 1:
            print('Starting {}'.format(new_slot))
        return new_slot

    def add_tp_ips(self, ips):
        """ Get a vector of TP ips and store them """
        for ip in ips:
            # Add the ips one by one
            try:
                self.final_ips['TP'].index(ip)
            except ValueError:
                # We dont have this ip
                self.final_ips['TP'].append(ip)
            # If this ip was added as FN, delete it from the FN list
            try:
                index = self.final_ips['FN'].index(ip)
                self.final_ips['FN'].pop(index)
            except ValueError:
                pass

    def add_fp_ips(self, ips):
        """ Get a vector of FP ips and store them """
        for ip in ips:
            # Add the ips one by one
            try:
                self.final_ips['FP'].index(ip)
            except ValueError:
                # We dont have this ip
                self.final_ips['FP'].append(ip)
            # If this IP was already detected as TN, delete it as TN
            try:
                index = self.final_ips['TN'].index(ip)
                self.final_ips['TN'].pop(index)
            except ValueError:
                pass

    def add_fn_ips(self, ips):
        """ Get a vector of FN ips and store them """
        for ip in ips:
            # Add the ips one by one
            # If this IP was already detected as TP, dont add it as FN
            try:
                self.final_ips['TP'].index(ip)
            except ValueError:
                # We dont have this ip as TP, add it as FN
                try:
                    self.final_ips['FN'].index(ip)
                except ValueError:
                    # We dont have this ip
                    self.final_ips['FN'].append(ip)

    def add_tn_ips(self, ips):
        """ Get a vector of TN ips and store them """
        for ip in ips:
            # Add the ips one by one
            try:
                self.final_ips['TN'].index(ip)
            except ValueError:
                # We dont have this ip
                self.final_ips['TN'].append(ip)
            # If this ip was added as FP before, delete it from the FP list
            try:
                index = self.final_ips['FP'].index(ip)
                self.final_ips['FP'].pop(index)
            except ValueError:
                pass

    def get_final_ips(self):
        return self.final_ips

    def add_errors(self, errors):
        """ Get the errors of the last tuple and add them to the experiments errors """
        self.total_errors['TP'] += errors['TP']
        self.total_errors['TN'] += errors['TN']
        self.total_errors['FN'] += errors['FN']
        self.total_errors['FP'] += errors['FP']
        self.total_errors['NN'] += errors['NN']

    def get_total_errors(self):
        return self.total_errors

    def compute_total_performance_metrics_for_final_ips(self):
        """ Compute the total performance metrics """
        try:
            self.total_performance_metrics_for_final_ips['TPR'] = ( len(self.final_ips['TP']) ) / float(len(self.final_ips['TP']) + len(self.final_ips['FN'] ))
        except ZeroDivisionError:
            self.total_performance_metrics_for_final_ips['TPR'] = -1
        try:
            self.total_performance_metrics_for_final_ips['TNR'] = ( len(self.final_ips['TN'] )) / float( len(self.final_ips['TN']) + len(self.final_ips['FP'] ))
        except ZeroDivisionError:
            self.total_performance_metrics_for_final_ips['TNR'] = -1
        try:
            self.total_performance_metrics_for_final_ips['FPR'] = ( len(self.final_ips['FP'] )) / float( len(self.final_ips['TN']) + len(self.final_ips['FP'] ))
        except ZeroDivisionError:
            self.total_performance_metrics_for_final_ips['FPR'] = -1
        try:
            self.total_performance_metrics_for_final_ips['FNR'] = ( len(self.final_ips['FN'] )) / float( len(self.final_ips['TP']) + len(self.final_ips['FN'] ))
        except ZeroDivisionError:
            self.total_performance_metrics_for_final_ips['FNR'] = -1
        try:
            self.total_performance_metrics_for_final_ips['Precision'] = ( len(self.final_ips['TP'] )) / float( len(self.final_ips['TP'] ) + len(self.final_ips['FP'] ))
        except ZeroDivisionError:
            self.total_performance_metrics_for_final_ips['Precision'] = -1
        try:
            self.total_performance_metrics_for_final_ips['Accuracy'] = ( len(self.final_ips['TP']) + len(self.final_ips['TN'] )) / float( len(self.final_ips['TP']) + len(self.final_ips['TN'] ) + len(self.final_ips['FP'] ) + len(self.final_ips['FN'] ))
        except ZeroDivisionError:
            self.total_performance_metrics_for_final_ips['Accuracy'] = -1
        try:
            self.total_performance_metrics_for_final_ips['ErrorRate'] = ( len(self.final_ips['FN']) + len(self.final_ips['FP']) ) / float( len(self.final_ips['TP']) + len(self.final_ips['TN']) + len(self.final_ips['FP']) + len(self.final_ips['FN'] ))
        except ZeroDivisionError:
            self.total_performance_metrics_for_final_ips['ErrorRate'] = -1
        self.beta = 1.0
        # With beta=1 F-Measure is also Fscore
        try:
            self.total_performance_metrics_for_final_ips['FMeasure1'] = ( ( (self.beta * self.beta) + 1 ) * self.total_performance_metrics_for_final_ips['Precision'] * self.total_performance_metrics_for_final_ips['TPR']  ) / float( ( self.beta * self.beta * self.total_performance_metrics_for_final_ips['Precision'] ) + self.total_performance_metrics_for_final_ips['TPR'])
        except ZeroDivisionError:
            self.total_performance_metrics_for_final_ips['FMeasure1'] = -1


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

    def get_testing_model(self, tuple4):
        """ See if we have the testing model stored for this experiment """
        try:
            model = self.testing_models[tuple4]
        except KeyError:
            model = Model(tuple4)
            self.testing_models[tuple4] = model
        return model

    def process_netflow_for_testing(self):
        """ Get a netflow file and process it for testing """
        # Clean the models in the constructor. We should do this better
        __modelsconstructors__.get_default_constructor().clean_models()
        try:
            file = open(self.file_obj.get_name(), 'r')
        except AttributeError:
            print_error('There is no binetflow file available. Did you generate it with dataset -g?')
            return False
        except IOError:
            print_error('It was not possible to open the test file. Is it on the current file system?')
            return False
        # Create the filter
        self.construct_filter(self.filter)
        # Remove the header
        header_line = file.readline().strip()
        # Find the separation character
        self.find_separator(header_line)
        # Extract the columns names
        self.find_columns_names(header_line)
        line = ','.join(file.readline().strip().split(',')[:14])
        # Methodology 4. For each flow
        start_time = datetime.now()
        print_info('Start Time: {}'.format(start_time))
        group_group_of_models = __groupofgroupofmodels__ 
        # The constructor of models can change. Now we hardcode -1, but warning!
        group_id = str(self.testing_id) + '-1'
        group_of_models = group_group_of_models.get_group(group_id)
        # If there are no model group for the testing, quit.
        if type(group_of_models) == bool:
            print_error('Inexistant group of models for this testing dataset.')
            return False
        # Get the structures
        structures = __database__.get_structures()
        try:
            training_structure = structures[self.structure_name]
        except KeyError:
            print_error('That structure name is invalid.')
            return False
        # Store some info about each training model, do it here and only once
        self.training_models = {}
        for model_training_id in self.models_ids:
            self.training_models[model_training_id] = {}
            self.training_models[model_training_id]['traininig_structure_name'] = self.structure_name
            self.training_models[model_training_id]['traininig_structure'] = training_structure
            try:
                self.training_models[model_training_id]['model_training'] = training_structure[int(model_training_id)]
            except:
                print_error('The training model id should be the id in the selected model structure. For example: markov_chains_1')
                return False
            self.training_models[model_training_id]['original_matrix'] = self.training_models[model_training_id]['model_training'].get_matrix()
            self.training_models[model_training_id]['original_self_prob'] = self.training_models[model_training_id]['model_training'].get_self_probability()
            self.training_models[model_training_id]['label'] = self.training_models[model_training_id]['model_training'].get_label()
            self.training_models[model_training_id]['labelname'] = self.training_models[model_training_id]['model_training'].get_label().get_name()
            self.training_models[model_training_id]['threshold'] = self.training_models[model_training_id]['model_training'].get_threshold()
            self.training_models[model_training_id]['proto'] = self.training_models[model_training_id]['label'].get_proto()
        while line:
            # Using our own extract_columns function makes this module more independent
            column_values = self.extract_columns_values(line)
            if self.verbose > 5:
                print_warning('Netflow: {}'.format(line))
            # Methodology 4.1. Extract its 4-tuple. Find (or create) the tuple object
            tuple4 = column_values['SrcAddr']+'-'+column_values['DstAddr']+'-'+column_values['Dport']+'-'+column_values['Proto']
            # Filter if we should analyze this tuple or not
            if self.apply_filter(tuple4):
                # Get the old tuple object for it, or get a new tuple object. 
                tuple = self.get_tuple(tuple4, group_id)
                # Methodology 4.2. Add all the relevant data to this tupple
                tuple.add_new_flow(column_values)
                # Methodology 4.3. Get the correct time slot. If the flow is outside the time slot, it will close the last time slot.
                # Here we also __close the current time slot if this tuple is in the next time slot
                time_slot = self.get_time_slot(column_values)
                # Add verbosity to time slot
                time_slot.set_verbose(self.verbose)
                # Add this 4tuple and src IP to the list on the time_slot
                time_slot.add_tuple4(tuple4)
                # Assign the ground truth label if we have one, only once for ip for time slot
                if tuple.get_ground_truth_label():
                    time_slot.set_ground_truth_label_for_ip(tuple.get_src_ip(), tuple.get_ground_truth_label())
                    if self.verbose > 3:
                        print_info('\t\tSetting the ground truth label for IP {}. The new label is {} in tuple {}. The final label is {}. (Time: {})'.format(tuple.get_src_ip(), tuple.get_ground_truth_label(), tuple.get_id(), time_slot.get_ground_truth_label(tuple.get_src_ip()), tuple.get_last_time()))
                # Methodology 4.4 Get the letter for this flow. i.e. find the model we have stored for this test tuple.
                model = group_of_models.get_model(tuple.get_id())
                if not model:
                    # It can happen that the 4tuple in the testing netflow file does not have a model in the database. In this case we should create one (not store it) and generate the letters again.
                    # Actually this is the case for real time traffic
                    #print_info('No model stored for tuple: {}. Generting one...'.format(tuple4))
                    ################
                    # Create a model
                    model = self.get_testing_model(tuple.get_id())
                    constructor_id = __modelsconstructors__.get_default_constructor().get_id()
                    # Warning, here we depend on the modelsconstrutor
                    model.set_constructor(__modelsconstructors__.get_constructor(constructor_id))
                    flow = Flow(0) # Fake flow id
                    flow.add_starttime(column_values['StartTime'])
                    flow.add_duration(column_values['Dur'])
                    flow.add_proto(column_values['Proto'])
                    flow.add_scraddr(column_values['SrcAddr'])
                    flow.add_dir(column_values['Dir'])
                    flow.add_dstaddr(column_values['DstAddr'])
                    flow.add_dport(column_values['Dport'])
                    flow.add_state(column_values['State'])
                    flow.add_stos(column_values['sTos'])
                    flow.add_dtos(column_values['dTos'])
                    flow.add_totpkts(column_values['TotPkts'])
                    flow.add_totbytes(column_values['TotBytes'])
                    try:
                        flow.add_srcbytes(column_values['SrcBytes'])
                    except KeyError:
                        # It can happen that we don't have the SrcBytes column
                        pass
                    try:
                        flow.add_srcUdata(column_values['srcUdata'])
                    except KeyError:
                        # It can happen that we don't have the srcUdata column
                        pass
                    try:
                        flow.add_dstUdata(column_values['dstUdata'])
                    except KeyError:
                        # It can happen that we don't have the dstUdata column
                        pass
                    try:
                        flow.add_label(column_values['Label'])
                    except KeyError:
                        # It can happen that we don't have the label column
                        pass
                    model.add_flow(flow)
                    ################
                # Take the letters from the test model, but not all of them, just the ones inside this time slot. This way we 'move' the letters used from time windows to time windows, but only if there was a model match.
                # Store the state so far in the tuple. Now we are cutting the original state. Min is the amount defined if this tuple had already matched before. Max is just the amount of flows recived so far.
                tuple.set_state_so_far(model.get_state()[tuple.get_min_state_len():tuple.get_max_state_len()])
                # Only compare the models when the START of the test state has more than 3 letters. So avoid mathching numbers and the first symbol. We want letters. After an update, compare all.
                if tuple.get_state_len() >= 3 or tuple.is_updated():
                    # Put these variables to default values. Used for the first time and to reset the winner variables.
                    time_slot.set_winner_model_id_for_ip(tuple.get_src_ip(), False)
                    time_slot.set_winner_model_distance_for_ip(tuple.get_src_ip(),'inf')
                    # Methodology 4.5 Compute the distance of the chain of states from this 4-tuple so far, with all the training models. Don't store a new distance object.
                    # For each traininig model
                    for model_training_id in self.models_ids:
                        # First, only continue if the protocols are the same
                        test_proto = tuple.get_proto().lower()
                        train_proto = self.training_models[model_training_id]['proto'].lower()
                        if test_proto != train_proto:
                            continue
                        # Letters for the train model. They should not be 'cut' like the test ones. Train models should be complete.
                        train_sequence = self.training_models[model_training_id]['model_training'].get_state()[tuple.get_min_state_len():tuple.get_amount_of_flows()]
                        # First re-create the matrix only for this sequence
                        self.training_models[model_training_id]['model_training'].create(train_sequence)
                        # Get the new original prob so far...
                        training_original_prob = self.training_models[model_training_id]['model_training'].compute_probability(train_sequence)
                        # Now obtain the probability for testing. The prob is computed by using the API on the train model, which knows its own matrix
                        test_prob = self.training_models[model_training_id]['model_training'].compute_probability(tuple.get_state_so_far())
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
                        if self.verbose > 4:
                            print_info('\tTraining Seq: {}'.format(train_sequence))
                            print_info('\tTesting  Seq: {}'.format(tuple.get_state_so_far()))
                            print_info('\tTrain prob: {}. Test prob: {}. Distance: {}'.format(training_original_prob, test_prob, prob_distance))
                        # Methodology 4.6. Decide upon a winner model.
                        # Is the probability just computed for this model lower than the threshold for that same model?
                        color=cyan
                        # See if the thorsold was overcomed. Also see if there are > 3 letters in the state
                        if prob_distance >= 1 and prob_distance <= self.training_models[model_training_id]['threshold']:
                            # The model is a candidate
                            if prob_distance <= time_slot.get_winner_model_distance_for_ip(tuple.get_src_ip()):
                                # The model is the winner so far. If the same model matches twice with the same distance, we reassign it. Also if two models have the same distance, we store the last one matching.
                                time_slot.set_winner_model_id_for_ip(tuple.get_src_ip(), model_training_id)
                                time_slot.set_winner_model_distance_for_ip(tuple.get_src_ip(), prob_distance)
                                color=red
                        if self.verbose > 3:
                            print_info(color('\tTuple {} ({}). Distance to model id {:6} ({:50}) (thres: {}):\t{}'.format(tuple.get_id(), tuple.get_ground_truth_label(), model_training_id, self.training_models[model_training_id]['labelname'], self.training_models[model_training_id]['threshold'], prob_distance)))
                    # End-for. After all the training models have been checked
                    # If there is a winning model, just assign it.
                    #print 'Tuple {}. Matched: {}. IP {}. Current Winner model: {}.  Current predicted: {}'.format(tuple.get_id(), time_slot.tuples[tuple.get_id()], tuple.get_src_ip(), time_slot.get_winner_model_id_for_ip(tuple.get_src_ip()), time_slot.get_predicted_label(tuple.get_src_ip()))
                    if time_slot.get_winner_model_id_for_ip(tuple.get_src_ip()):
                        # There was a winner model for this flow (tuple and ip) so store it.
                        if self.verbose > 10:
                            print_info('Winner model for IP {}: {} ({}) with distance {}'.format(tuple.get_src_ip(), time_slot.get_winner_model_id_for_ip(tuple.get_src_ip()), self.training_models[time_slot.get_winner_model_id_for_ip(tuple.get_src_ip())]['labelname'], time_slot.get_winner_model_distance_for_ip(tuple.get_src_ip())))
                        # Methodology 4.7. Extract the label and assign it together with other data
                        time_slot.set_predicted_label_for_ip(tuple.get_src_ip(), self.training_models[time_slot.get_winner_model_id_for_ip(tuple.get_src_ip())]['labelname'], tuple.get_amount_of_flows(), tuple.get_id(), time_slot.get_winner_model_id_for_ip(tuple.get_src_ip()), time_slot.get_winner_model_distance_for_ip(tuple.get_src_ip()))
                        # Methodology 4.8. Mark the 4tuple as 'matched' in the time slot. This is used later to know, from all the 4tuples, which ones we should move their states window.
                        time_slot.set_4tuple_match(tuple4)
                    # Did we have a winner model for this tuple in this time slot before?, but now the same tuple is not matching any more models? Erase its current winner label.
                    elif time_slot.get_winner_model_id_for_ip(tuple.get_src_ip()) == False and time_slot.get_predicted_label(tuple.get_src_ip()):
                        if self.verbose > 10:
                            print_info('Unset predicted label for IP {}: {}'.format(tuple.get_src_ip(), time_slot.get_predicted_label(tuple.get_src_ip())))
                        time_slot.unset_predicted_label_for_ip(tuple.get_src_ip(), False, tuple.get_amount_of_flows(), tuple.get_id())
                        time_slot.set_4tuple_unmatch(tuple.get_id())
                # Finishing working with this tuple
            # End of the if of applying the filter to this line
            # Read next line
            # Line without the src and dst data
            line = ','.join(file.readline().strip().split(',')[:14])
            if self.verbose > 12:
                # Stop after each flow
                raw_input()
        # Close the file
        file.close()
        # Methodology 7 Compute the results of the last time slot
        if self.time_slots:
            self.time_slots[-1].close(self.verbose)
            # After closing the time slot, we should get some info back
            tp_ips_in_last_time_slot = self.time_slots[-1].get_tp_ips()
            fp_ips_in_last_time_slot = self.time_slots[-1].get_fp_ips()
            fn_ips_in_last_time_slot = self.time_slots[-1].get_fn_ips()
            tn_ips_in_last_time_slot = self.time_slots[-1].get_tn_ips()
            self.add_tp_ips(tp_ips_in_last_time_slot)
            self.add_fp_ips(fp_ips_in_last_time_slot)
            self.add_fn_ips(fn_ips_in_last_time_slot)
            self.add_tn_ips(tn_ips_in_last_time_slot)
            # Store the errors in the experiment
            self.add_errors(self.time_slots[-1].get_errors())
        # Move the state windows in the tuples Before closing the time windoows!
        self.move_windows_in_tuples()
        # Update the finish time
        finish_time = datetime.now()
        print_info('Finish Time: {} (Duration: {})'.format(unicode(finish_time), unicode(finish_time - start_time)))
        self.print_final_values()
        # Erase the tuples
        self.tuples = {}
        # Before finishing we need to put back the original information in the training models
        for model_training_id in self.models_ids:
            self.training_models[model_training_id]['model_training'].set_matrix(self.training_models[model_training_id]['original_matrix']) 
            self.training_models[model_training_id]['model_training'].set_self_probability(self.training_models[model_training_id]['original_self_prob'])  

    def clean_experiment_for_storage(self):
        # After we printed everything, we should clean the experiment of all the stuff we don't want stored in the db.
        self.time_slots = []

    def print_final_values(self):
        print
        # Print something about all the tuples
        print_info('Errors based on detecting IPs on each Time Window')
        print_info('=================================================')
        print_info('Total amount of unique tuples: {}'.format(len(self.tuples)))
        print_info('Total time slots: {}'.format(len(self.time_slots)))
        # Methodology 7.1 Compute the performance metrics so far
        self.compute_total_performance_metrics()
        self.compute_total_performance_metrics_for_final_ips()
        # Methodology 7.2 Print the total errors
        print_info('Total Errors detecting IPs on all time windows: {}'.format(self.get_total_errors()))
        # Methodology 7.2 Print performance metric
        print_info('Total Performance Metrics for detcting IPs in all time windows:')
        print_info('\tFMeasure: {:.3f}, FPR: {:.3f}, TPR: {:.3f}, TNR: {:.3f}, FNR: {:.3f}, ErrorR: {:.3f}, Prec: {:.3f}, Accu: {:.3f}'.format(self.total_performance_metrics['FMeasure1'], self.total_performance_metrics['FPR'],self.total_performance_metrics['TPR'], self.total_performance_metrics['TNR'], self.total_performance_metrics['FNR'], self.total_performance_metrics['ErrorRate'], self.total_performance_metrics['Precision'], self.total_performance_metrics['Accuracy']))
        print_info('Complete experiment IPs Detections')
        for iptype in self.final_ips:
            print '\t' + str(iptype)
            for ip in self.final_ips[iptype]:
                print '\t\t' + str(ip)
        # Which positive IP did we miss?
        print_info('Not Detected IPs:')
        for ip in self.final_ips['FN']:
            # Was it TP?
            if ip not in self.final_ips['TP']:
                print('\tIP {} was never detected.'.format(red(ip)))
        print_info('Total Performance Metrics for detcting IPs in the complete experiment:')
        print_info('\tFMeasure: {:.3f}, FPR: {:.3f}, TPR: {:.3f}, TNR: {:.3f}, FNR: {:.3f}, ErrorR: {:.3f}, Prec: {:.3f}, Accu: {:.3f}'.format(self.total_performance_metrics_for_final_ips['FMeasure1'], self.total_performance_metrics_for_final_ips['FPR'],self.total_performance_metrics_for_final_ips['TPR'], self.total_performance_metrics_for_final_ips['TNR'], self.total_performance_metrics_for_final_ips['FNR'], self.total_performance_metrics_for_final_ips['ErrorRate'], self.total_performance_metrics_for_final_ips['Precision'], self.total_performance_metrics_for_final_ips['Accuracy']))

    def move_windows_in_tuples(self):
        """ Ask for all the tuples in this time slot and move their state letters windows if the state len is more than a threshold. This is run after the closing of the time slot. Be careful. If the threshold is overcome, we move the min_len to the _current_ amount of flows, that means that after each time window, the tuple forgets what happened in previous time windows and only works with what happens from now on."""
        try:
            tuples = self.time_slots[-1].tuples
        except IndexError:
            # It is possible that there are no time slots yet.
            return True
        #print_info('Tuples: {}'.format(tuples))
        for tuple4 in tuples:
            # If the amount of letters in the states is more that a threshold, update its state and forget the letters so far.
            diff = self.tuples[tuple4].get_max_state_len() - self.tuples[tuple4].get_min_state_len()
            if diff >= 100:
                self.tuples[tuple4].update_min_state_len()
                #print '\tTuple {}. The current len diff is: {}. Min len moved to {}'.format(tuple4, diff, self.tuples[tuple4].get_min_state_len())

    def get_tuple(self, tuple4, dataset_id):
        """ Get the values and return the correct tuple for them """
        try:
            tuple = self.tuples[tuple4]
            # We already have this connection
        except KeyError:
            # First time for this connection
            tuple = Tuple(tuple4, dataset_id)
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
        """ Given a line text of a flow, extract the values for each column. The main difference with this function and the one in connections.py is that we don't use the src and dst data. """
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

    def get_timeslots(self):
        return self.time_slots

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
        self.parser.add_argument('-p', '--printstate', metavar='experiment_id', type=int, help='Print some info about the experiment.')
        self.parser.add_argument('-n', '--new', action='store_true', help='Create a new experiment. Use -m to assign the models to use for detection. Use -t to select a testing dataset.')
        self.parser.add_argument('-d', '--delete', metavar='delete', help='Delete an experiment given the id. You can give a range with -. Ej: -d 10-20')
        self.parser.add_argument('-m', '--models_ids', metavar='models_ids', help='Ids of the models (e.g. Markov Models) to be used when creating a new experiment with -n. Comma separated.')
        self.parser.add_argument('-s', '--structure_of_models_ids', metavar='structure_of_models_ids', help='Name of the structure where the models id belong. For example: markov_models_1.')
        self.parser.add_argument('-t', '--testing_id', metavar='testing_id', type=int, help='Dataset id to be used as testing when creating a new experiment with -n.')
        self.parser.add_argument('-T', '--timeslotwidth', default=300, metavar='timeslotwidth', type=int, help='The width of the time slot in seconds.')
        self.parser.add_argument('-v', '--verbose', default=0, metavar='verbose', type=int, help='An integer expressing how verbose should we be while running the experiment. For example -v 1.')
        self.parser.add_argument('-r', '--reduce', metavar='experiment_id', type=str, help='Reduce the size of the given experiment. Strongly suggested to be used before storing the experiment by leaving the program. It deletes the timeslots from the experiment. Before this command you can use -p and -v > 3 to see the info of the time slots in an experiment. After this commend you can only use -v < 3.')
        self.parser.add_argument('-f', '--filter', metavar='filter', nargs = '+', default="", help='Filters for creating the experiment. They are used to select which tuples should be matched in the current testing dataset specified. Keywords: conn. Usage: conn=<text>. Also conn!=<text>. For example conn=1.1.1.1-2.2.2.2-80-tcp conn!=3.3.3.3-4.4.4.4-443-tcp. The names are partial matching. The operator for conn are = and !=.')
        self.parser.add_argument('-o', '--onebyone', action='store_true', default=False, help='Specify if the training models provided with -m should be used one by one with the testing dataset, or in group. By default it is done in groups. With this option it is done one by one.')
        self.parser.add_argument('-D', '--description', metavar='text', default="", help='An optional description of the experiment between double quotes.')


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
        try:
            return self.main_dict[id]
        except KeyError:
            return False

    def get_experiments(self):
        return self.main_dict.values()

    def list_experiments(self):
        print_info('List of objects')
        rows = []
        for experiment in self.get_experiments():
            rows.append([ experiment.get_id(), experiment.get_description(), experiment.get_fancy_performance_metrics() ])
        print(table(header=['Id', 'Description','Performance Metrics'], rows=rows))

    def create_new_experiment(self, models_ids, testing_id, timeslotwidth, verbose, filter, desc, structure_name):
        """ Create a new experiment """
        # Generate the new id
        try:
            new_id = self.main_dict[list(self.main_dict.keys())[-1]].get_id() + 1
        except (KeyError, IndexError):
            new_id = 1
        ## Set the description
        # Create the new object
        print
        print_info('Starting experiment id: {}'.format(new_id))
        new_experiment = Experiment(new_id, desc, timeslotwidth, filter, structure_name)
        # Methodology 1. We receive the markov_models ids for the training, and the id of the dataset of the tetsing. (We may not have markov models for the testing. A binetflow file and labels are enough)
        # Add info
        new_experiment.add_models_ids(models_ids)
        new_experiment.add_testing_id(testing_id)
        # Store on DB
        self.main_dict[new_id] = new_experiment
        # Run it
        new_experiment.run(verbose)

    def delete_experiment(self, id):
        """ Deletes an experiment """
        ans = raw_input('Are you sure you want to delete experiment {} (YES/NO)?: '.format(id))
        if ans == "YES":
            # Is this a range or id?
            try:
                eid = int(id)
                print_info('Deleting experiment {}.'.format(eid))
                # Get the experiment
                exp = self.get_experiment(eid)
                # First delete everything inside the experiment
                exp.delete()
                # Now delete it from the list of experiments
                self.main_dict.pop(eid)
            except ValueError:
                if '-' in id:
                    # is a range
                    try:
                        start = int(id.split('-')[0])
                        end = int(id.split('-')[1])
                        while start<=end:
                            # Get the experiment
                            exp = self.get_experiment(start)
                            if exp:
                                # First delete everything inside the experiment
                                exp.delete()
                                # Now delete it from the list of experiments
                                self.main_dict.pop(start)
                            start += 1
                    except ValueError:
                        print_error('The id of the experiment is invalid.')
                else:
                    print_error('The id of the experiment is invalid.')

    def print_experiment(self, experiment_id, verbose):
        """ Print info about the experiment """
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            print_error('No such experiment id')
            return False
        print_info('Experiment {}'.format(experiment))
        print_info('Description: ' + experiment.get_description())
        print_info('Trained models for detection: {}'.format(experiment.get_training_models().keys()))
        print_info('Test dataset: {}'.format(experiment.get_testing_id()))
        print_info('Total amount of tuples: {}'.format(len(experiment.get_tuples())))
        print_info('Total time slots: {}'.format(len(experiment.get_time_slots())))
        # Depending on the verbosity, we print more info about the experiment.
        if verbose > 1:
            # Print for each time slot, the errors
            for timeslot in experiment.get_timeslots():
                # In verbose mode 2, just print the timeslots that got some error types FN, TP, TN or FP
                if verbose < 3:
                    sum = 0
                    for error in timeslot.get_acc_errors():
                        sum += timeslot.get_acc_errors()['TP']
                        sum += timeslot.get_acc_errors()['TN']
                        sum += timeslot.get_acc_errors()['FP']
                        sum += timeslot.get_acc_errors()['FN']
                    if sum == 0:    
                        # In verbose = 2 don't print this timeslot because there is no interesting data
                        continue
                # Print this timeslot
                print timeslot
                print cyan('\tFP:{}, TP:{}, FN:{}, TN:{}, NN:{}'.format(timeslot.get_acc_errors()['FP'], timeslot.get_acc_errors()['TP'], timeslot.get_acc_errors()['FN'], timeslot.get_acc_errors()['TN'], timeslot.get_acc_errors()['NN']))
                print '\tFMeasure: {:.3f}, FPR: {:.3f}, TPR: {:.3f}, TNR: {:.3f}, FNR: {:.3f}, ErrorR: {:.3f}, Prec: {:.3f}, Accu: {:.3f}'.format(timeslot.get_performance_metrics()['FMeasure1'], timeslot.get_performance_metrics()['FPR'],timeslot.get_performance_metrics()['TPR'], timeslot.get_performance_metrics()['TNR'], timeslot.get_performance_metrics()['FNR'], timeslot.get_performance_metrics()['ErrorRate'], timeslot.get_performance_metrics()['Precision'], timeslot.get_performance_metrics()['Accuracy'])
                # Print info about each IP on each slot
                for ip in timeslot.ip_dict:
                    if timeslot.ip_dict[ip]['error'] == 'NN':
                        if verbose < 3:
                            # Dont print this IP because is unknown and detected as unknown
                            continue
                    if timeslot.ip_dict[ip]['error'] == 'TP':
                        color = yellow
                    elif timeslot.ip_dict[ip]['error'] == 'FP':
                        color = red
                    else:
                        color = str
                    print color('\t\tIP: {}'.format(ip))
                    try:
                        gtl = timeslot.get_ground_truth_label(ip)
                    except KeyError:
                        gtl = 'None'
                    try:
                        win_model_id = timeslot.get_predicted_model_id_for_ip(ip)
                    except KeyError:
                        win_model_id = False
                    try:
                        win_model_dist = timeslot.get_predicted_model_distance_for_ip(ip)
                    except KeyError:
                        win_model_dist = False
                    print color('\t\t\t Ground Truth Label: {}. Error Type: {}. Winner Model: {}, Distance: {}'.format(gtl,timeslot.ip_dict[ip]['error'], win_model_id, win_model_dist))
            if verbose > 2:
                # Print TP in the slot
                try:
                    for tp in timeslot.get_tp_ips():
                        print '\t\t IP:{}'.format(tp)
                except UnboundLocalError:
                    # The timeslot variable does not exists. Is ok.
                    pass
        if verbose > 0:
            print
            print_info('Summary of IP detections:')
            try:
                # Only one, print the IPs in each type of error: TN, TP, FN, FP
                for iptype in experiment.final_ips:
                    if experiment.final_ips[iptype]:
                        print '\t- ' + str(iptype)
                    for ip in experiment.final_ips[iptype]:
                        print '\t     ' + str(ip)
                # Print which positive IP did we miss?
                print_info('Not Detected IPs:')
                for ip in experiment.final_ips['FN']:
                    # Was it TP?
                    if ip not in experiment.final_ips['TP']:
                        print('\tIP {} was never detected.'.format(red(ip)))
            except AttributeError:
                print_error('No info about the IPs stored in this experiment.')
        print_info('Total Errors. FP:{}, TP:{}, FN:{}, TN:{}, NN:{}'.format(experiment.get_total_errors()['FP'], experiment.get_total_errors()['TP'], experiment.get_total_errors()['FN'], experiment.get_total_errors()['TN'], experiment.get_total_errors()['NN']))
        print_info('Total Performance Metrics:')
        print_info('\tFMeasure: {:.3f}, FPR: {:.3f}, TPR: {:.3f}, TNR: {:.3f}, FNR: {:.3f}, ErrorR: {:.3f}, Prec: {:.3f}, Accu: {:.3f}'.format(experiment.total_performance_metrics['FMeasure1'], experiment.total_performance_metrics['FPR'],experiment.total_performance_metrics['TPR'], experiment.total_performance_metrics['TNR'], experiment.total_performance_metrics['FNR'], experiment.total_performance_metrics['ErrorRate'], experiment.total_performance_metrics['Precision'], experiment.total_performance_metrics['Accuracy']))


    def reduce_experiment(self, experiment_id):
        """ Since an experiment can be very large, very..., it is necessary to delete some parts before storing in the db """
        experiment = self.get_experiment(experiment_id)
        experiment.clean_experiment_for_storage()

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
            # Do we have the name of the structure?
            if not self.args.structure_of_models_ids:
                print_error('The name of the structure for the trainings ids should be provided. For example: markov_models_1')
                return False
            if self.args.onebyone:
                try:
                    testing_id = self.args.testing_id
                    for models_ids in self.args.models_ids.split(','):
                        self.create_new_experiment(models_ids, testing_id, self.args.timeslotwidth, self.args.verbose, self.args.filter, self.args.description, self.args.structure_of_models_ids)
                except AttributeError:
                    print_error('You should provide both the ids of the models to use for detection (with -m) and the testing dataset id (with -t).')
                    return False
            else:
                try:
                    models_ids = self.args.models_ids
                    testing_id = self.args.testing_id
                    self.create_new_experiment(models_ids, testing_id, self.args.timeslotwidth, self.args.verbose, self.args.filter, self.args.description, self.args.structure_of_models_ids)
                #except AttributeError:
                #    print_error('You should provide both the ids of the models to use for detection (with -m) and the testing dataset id (with -t).')
                #    return False
                except Exception as e:
                    print 'Error during the experiment'
                    print e
                    return False
        elif self.args.delete:
            self.delete_experiment(self.args.delete)
        elif self.args.printstate:
            self.print_experiment(self.args.printstate, self.args.verbose)
        elif self.args.reduce:
            if '-' in self.args.reduce:
                first_id = int(self.args.reduce.split('-')[0])
                last_id = int(self.args.reduce.split('-')[1])
            else:
                first_id = int(self.args.reduce)
                last_id = int(self.args.reduce)
            for id in range(first_id, last_id):
                self.reduce_experiment(id)
        else:
            print_error('At least one parameter is required in this module')
            self.usage()
