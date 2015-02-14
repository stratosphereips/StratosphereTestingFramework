import persistent
import BTrees.OOBTree
from dateutil import parser
import datetime

from stf.common.out import *


# Create one of these classes for each new model constructor you want to implement
class Model_Constructor(object):
    """
    The First Model constructor. Each of this objects is unique. We are going to instantiate them only once.
    """
    def __init__(self):
        self.id = 0
        self.name = 'Model 0'
        self.description = "This behavioral type of model has thresholds ..."
        self.threshold_time_1 = False
        self.threshold_time_2 = False
        self.threshold_time_3 = False
        self.threshold_duration_1 = False
        self.threshold_duration_2 = False
        self.threshold_size_1 = False
        self.threshold_size_2 = False
        self.threshold_timeout = False

        # We store each model id with the values of T1 and T2
        self.models = {}

    def get_state(self,flow,model_id):
        """ Receive the flow info and get a state"""
        #print_info(flow)

        # Temporal TD
        TD = -1
        state = ''

        # Get what we have about this model
        newtime = parser.parse(flow.get_starttime())
        newsize = flow.get_totbytes()
        newduration = flow.get_duration()

        try:
            model = self.models[model_id]
            # Update T1. Just move T2 in there
            model['T1'] = model['T2']
            # Get the new time from the new flow
            # Compute the new T2
            model['T2'] = newtime - model['LastTime']
            # Update the lasttime for next time
            model['LastTime'] = newtime
        except KeyError:
            # First time we see this model. Initialize the values
            self.models[model_id]={}
            self.models[model_id]['T1'] = False
            self.models[model_id]['T2'] = False
            self.models[model_id]['LastTime'] = newtime
            model = self.models[model_id]



        # Compute the periodic
        if not model['T1'] or not model['T2']:
            periodic = -1
        elif model['T2'] >= self.get_tto():
            state += '0'

        if model['T1'] and model['T2']:
            # We have some values. See which is larger
            try:
                if model['T2'] >= model['T1']:
                    TD = datetime.timedelta(seconds=(model['T2'].total_seconds() / model['T1'].total_seconds()))
                else:
                    TD = datetime.timedelta(seconds=(model['T1'].total_seconds() / model['T2'].total_seconds()))
            except ZeroDivisionError:
                print_error('The time difference between flows was 0. Strange. We keep going anyway.')
                TD = 1
            # Decide the periodic based on TD and the thresholds
            if TD <= self.get_tt1():
                # Strongly periodic
                periodic = 1
            elif TD < self.get_tt2():
                # Weakly periodic
                periodic = 2
            elif TD < self.get_tt3():
                # Weakly not periodic
                periodic = 3
            else:
                periodic = 4

        # Compute the duration
        if newduration <= self.get_td1():
            duration = 1
        elif newduration > self.get_td1() and newduration <= self.get_td2():
            duration = 2
        elif newduration > self.get_td2():
            duration = 3

        # Compute the size
        if newsize <= self.get_ts1():
            size = 1
        elif newsize > self.get_ts1() and newsize <= self.get_ts2():
            size = 2
        elif newsize > self.get_ts2():
            size = 3

        # Compute the state
        if periodic == -1:
            if size == 1:
                if duration == 1:
                    state += '1'
                elif duration == 2:
                    state += '2'
                elif duration == 3:
                    state += '3'
            elif size == 2:
                if duration == 1:
                    state += '4'
                elif duration == 2:
                    state += '5'
                elif duration == 3:
                    state += '6'
            elif size == 3:
                if duration == 1:
                    state += '7'
                elif duration == 2:
                    state += '8'
                elif duration == 3:
                    state += '9'
        elif periodic == 1:
            if size == 1:
                if duration == 1:
                    state += 'a'
                elif duration == 2:
                    state += 'b'
                elif duration == 3:
                    state += 'c'
            elif size == 2:
                if duration == 1:
                    state += 'd'
                elif duration == 2:
                    state += 'e'
                elif duration == 3:
                    state += 'f'
            elif size == 3:
                if duration == 1:
                    state += 'g'
                elif duration == 2:
                    state += 'h'
                elif duration == 3:
                    state += 'i'
        elif periodic == 2:
            if size == 1:
                if duration == 1:
                    state += 'A'
                elif duration == 2:                  
                    state += 'B'          
                elif duration == 3:                  
                    state += 'C'      
            elif size == 2:                    
                if duration == 1:                    
                    state += 'D'          
                elif duration == 2:                  
                    state += 'E'          
                elif duration == 3:                  
                    state += 'F'      
            elif size == 3:                    
                if duration == 1:                    
                    state += 'G'          
                elif duration == 2:                  
                    state += 'H'          
                elif duration == 3:                  
                    state += 'I'  
        elif periodic == 3:                
            if size == 1:
                if duration == 1:                    
                    state += 'r'          
                elif duration == 2:
                    state += 's'
                elif duration == 3:
                    state += 't'
            elif size == 2:
                if duration == 1:
                    state += 'u'
                elif duration == 2:
                    state += 'v'
                elif duration == 3:
                    state += 'w'
            elif size == 3:
                if duration == 1:
                    state += 'x'
                elif duration == 2:
                    state += 'y'
                elif duration == 3:
                    state += 'z'
        elif periodic == 4:
            if size == 1:
                if duration == 1:
                    state += 'R'
                elif duration == 2:
                    state += 'S'
                elif duration == 3:
                    state += 'T'
            elif size == 2:
                if duration == 1:
                    state += 'U'
                elif duration == 2:
                    state += 'V'
                elif duration == 3:
                    state += 'W'
            elif size == 3:
                if duration == 1:
                    state += 'X'
                elif duration == 2:
                    state += 'Y'
                elif duration == 3:
                    state += 'Z'
        #print_info('Model: {}, T1: {}, T2: {}, TD:{}, Periodicity: {}, State: {}'.format(model_id, model['T1'], model['T2'], [TD.total_seconds() if not isinstance(TD,int) else -1], periodic, state))

        # We store permanently the T1, T2 and TD values on each flow, so we can later analyze it
        flow.set_t1(model['T1'])
        flow.set_t2(model['T2'])
        flow.set_td(TD)
        flow.set_state(state)

        return state


    def get_id(self):
        return self.id

    def get_name(self):
        return self.name

    def get_description(self):
        return self.description

    def get_tt1(self):
        return self.threshold_time_1

    def get_tt2(self):
        return self.threshold_time_2

    def get_tt3(self):
        return self.threshold_time_3

    def get_td1(self):
        return self.threshold_duration_1

    def get_td2(self):
        return self.threshold_duration_2

    def get_ts1(self):
        return self.threshold_size_1

    def get_ts2(self):
        return self.threshold_size_2

    def get_tto(self):
        return self.threshold_timeout

    def set_tt1(self, value):
        self.threshold_time_1 = value

    def set_tt2(self, value):
        self.threshold_time_2 = value

    def set_tt3(self, value):
        self.threshold_time_3 = value

    def set_td1(self, value):
        self.threshold_duration_1 = value

    def set_td2(self, value):
        self.threshold_duration_2 = value

    def set_ts1(self, value):
        self.threshold_size_1 = value

    def set_ts2(self, value):
        self.threshold_size_2 = value

    def set_tto(self, value):
        self.threshold_timeout = value


class Models_Constructors(persistent.Persistent):
    def __init__(self):
        """ This class holds all the different constructors of behavioral models based on states"""
        self.default_model_constructor = 0
        self.models_constructors = BTrees.OOBTree.BTree()

        # Reapeat this for each new constructor

        # Add the first model constructor
        model_constructor = Model_Constructor()
        model_constructor.set_tt1(datetime.timedelta(seconds=1.05))
        model_constructor.set_tt2(datetime.timedelta(seconds=1.1))
        model_constructor.set_tt3(datetime.timedelta(seconds=5))
        model_constructor.set_td1(float(0.1))
        model_constructor.set_td2(float(10))
        model_constructor.set_ts1(float(125))
        model_constructor.set_ts2(float(1100))
        model_constructor.set_tto(datetime.timedelta(seconds=3600))
        self.models_constructors[model_constructor.get_id()] = model_constructor

    def get_default_constructor(self):
        return self.models_constructors[self.default_model_constructor]

    def list_constructors(self):
        print_info('List of all the models constructors available')
        rows = []
        for constructor in self.models_constructors.values():
            rows.append([constructor.get_name(), constructor.get_id(), constructor.get_description(), constructor.get_tt1(), constructor.get_tt2(), constructor.get_tt3(), constructor.get_td1(), constructor.get_td2(), constructor.get_ts1(), constructor.get_ts2(), constructor.get_tto()])
        print(table(header=['Name', 'Id', 'Description', 'Tt1', 'Tt2', 'Tt3', 'Td1', 'Td2', 'Ts1', 'Ts2', 'Tto'], rows=rows))



__modelsconstructors__ = Models_Constructors()