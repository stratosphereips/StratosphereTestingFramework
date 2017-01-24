import persistent
import BTrees.IOBTree
from dateutil import parser
import datetime

from stf.common.out import *


# Create one of these classes for each new model constructor you want to implement
class Model_Constructor(object):
    """
    The First Model constructor. Each of this objects is unique. We are going to instantiate them only once.
    Each model constructor object is related with a unique model.
    """
    def __init__(self, id):
        self.id = id
        self.threshold_time_1 = False
        self.threshold_time_2 = False
        self.threshold_time_3 = False
        self.threshold_duration_1 = False
        self.threshold_duration_2 = False
        self.threshold_size_1 = False
        self.threshold_size_2 = False
        self.threshold_timeout = False
        self.use_multiples_timeouts = True
        self.models = {}
     
    def clean_models(self):
        self.models = {}

    def del_model(self, model_id):
        """ Delete this model from the list of models used by this constructor. This allow us to regenerate the state of a model without problems """
        try:
            self.models.pop(model_id)
        except KeyError:
            print_error('There is no such model {} in the constructor to delete.'.format(model_id))

    def set_name(self,name):
        self.name = name  
 
    def set_description(self,description):
        self.description = description

    def get_state(self, flow, model_id):
        """ Receive the flow info and the model id and get a state"""
        # Temporal TD
        TD = -1
        state = ''

        # Get what we have about this model
        newtime = parser.parse(flow.get_starttime())
        newsize = flow.get_totbytes()
        newduration = flow.get_duration()

        # This flow belongs to a known model, or is the first one?
        try:
            model = self.models[model_id]
            # We already have this model
            # Update T1. Just move T2 in there
            model['T1'] = model['T2']
            # Get the new time from the new flow
            # Compute the new T2
            model['T2'] = newtime - model['LastTime']
            # If T2 is negative, then we have an issue with the order of the file. Send an error and stop. The user should fix this, not us.
            if model['T2'].total_seconds() < 0:
                print_error('Model: {}'.format(model))
                print_error('T1 is: {}'.format(model['T1'].total_seconds()))
                print_error('T2 is: {}'.format(model['T2'].total_seconds()))
                print_error('Flow new time is: {}'.format(newtime))
                print_error('Flow last time is: {}'.format(model['LastTime']))
                print_error('The last flow is: {}'.format(flow))
                print_error('The binetflow file is not sorted. Please delete this file from the dataset, sort it (cat file.biargus |sort -n > newfile.biargus) and add it back. We can not modify a file on disk.')
                print_error('Flow: '.format(flow))
                return False
            # Update the lasttime for next time
            model['LastTime'] = newtime
        except KeyError:
            # First time we see this model. Initialize the values
            self.models[model_id]={}
            self.models[model_id]['T1'] = False
            self.models[model_id]['T2'] = False
            self.models[model_id]['LastTime'] = newtime
            model = self.models[model_id]


        # We should get inside the next if only when T2 and T1 are not False. However, since also datatime(0) matches a False, we can only check to see if it is bool or not. 
        # We are only using False when we start, so it is not necessary to check if it is False also.
        # Compute the periodicity
        if (isinstance(model['T1'], bool) and model['T1'] == False) or (isinstance(model['T2'], bool) and model['T2'] == False):
            periodic = -1
        elif not isinstance(model['T1'], bool) and not isinstance(model['T2'], bool):
            # We have some values. See which is larger
            try:
                if model['T2'] >= model['T1']:
                    TD = datetime.timedelta(seconds=(model['T2'].total_seconds() / model['T1'].total_seconds())).total_seconds()
                else:
                    TD = datetime.timedelta(seconds=(model['T1'].total_seconds() / model['T2'].total_seconds())).total_seconds()
            except ZeroDivisionError:
                #print_error('The time difference between flows was 0. Strange. We keep going anyway.')
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

        # Compute the new letters for the time of the periodicity.
        if not isinstance(model['T2'], bool):
            if model['T2'] <= datetime.timedelta(seconds=5):
                state += '.'
            elif model['T2'] <= datetime.timedelta(seconds=60):
                state += ','
            elif model['T2'] <= datetime.timedelta(seconds=300):
                state += '+'
            elif model['T2'] <= datetime.timedelta(seconds=3600):
                state += '*'
            elif model['T2'] >= self.get_tto():
                # We convert it to int because we count the amount of complete hours that timeouted. The remaining time is not a timeout... 
                t2_in_hours = model['T2'].total_seconds() / self.get_tto().total_seconds()
                # Should be int always
                for i in range(int(t2_in_hours)):
                    state += '0'

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

    def set_use_mutiples_timeouts(self, value):
        self.use_multiples_timeouts = value

    def get_use_mutiples_timeouts(self):
        try:
            return self.use_multiples_timeouts
        except AttributeError:
            # If there is no info, by default use True
            return True



#########################
#########################
#########################
class Models_Constructors(persistent.Persistent):
    def __init__(self):
        """ This class holds all the different constructors of behavioral models based on states"""
        self.default_model_constructor = 1
        self.models_constructors = BTrees.IOBTree.BTree()

        # Reapeat this for each new constructor

        # Add the first model constructor
        first_model_constructor = Model_Constructor(0)
        first_model_constructor.set_tt1(float(1.05))
        first_model_constructor.set_tt2(float(1.1))
        first_model_constructor.set_tt3(float(5))
        first_model_constructor.set_td1(float(0.1))
        first_model_constructor.set_td2(float(10))
        first_model_constructor.set_ts1(float(125))
        first_model_constructor.set_ts2(float(1100))
        first_model_constructor.set_tto(datetime.timedelta(seconds=3600))
        first_model_constructor.use_multiples_timeouts = True
        first_model_constructor.set_name('Model 0')
        first_model_constructor.set_description('To try at the thresholds.')
        self.models_constructors[first_model_constructor.get_id()] = first_model_constructor

        # Add the second model constructor
        second_model_constructor = Model_Constructor(1)
        second_model_constructor.set_tt1(float(1.05))
        second_model_constructor.set_tt2(float(1.3))
        second_model_constructor.set_tt3(float(5))
        second_model_constructor.set_td1(float(0.1))
        second_model_constructor.set_td2(float(10))
        second_model_constructor.set_ts1(float(250))
        second_model_constructor.set_ts2(float(1100))
        second_model_constructor.set_tto(datetime.timedelta(seconds=3600))
        second_model_constructor.use_multiples_timeouts = True
        second_model_constructor.set_name('Model Bundchen')
        second_model_constructor.set_description('Uses the symbols between flows to store the time. Better thresholds.')
        self.models_constructors[second_model_constructor.get_id()] = second_model_constructor

        # Add the third model constructor
        third_model_constructor = Model_Constructor(2)
        third_model_constructor.set_tt1(float(1.05))
        third_model_constructor.set_tt2(float(1.3))
        third_model_constructor.set_tt3(float(5))
        third_model_constructor.set_td1(float(0.1))
        third_model_constructor.set_td2(float(10))
        third_model_constructor.set_ts1(float(250))
        third_model_constructor.set_ts2(float(1100))
        third_model_constructor.set_tto(datetime.timedelta(seconds=3600))
        third_model_constructor.use_multiples_timeouts = False
        third_model_constructor.set_name('Model Moss')
        third_model_constructor.set_description('Uses the symbols between flows to store the time. Better thresholds.')
        self.models_constructors[third_model_constructor.get_id()] = third_model_constructor

    def has_constructor_id(self, constructor_id):
        try:
            t = self.models_constructors[constructor_id]
            return True
        except KeyError:
            return False

    def get_constructor(self, id):
        """ Return the constructors ids"""
        return self.models_constructors[id]

    def get_constructors_ids(self):
        """ Return the constructors ids"""
        return self.models_constructors.keys()

    def get_default_constructor(self):
        """ Since we return an object, all the models share the same constructor """
        return self.models_constructors[self.default_model_constructor]

    def list_constructors(self):
        print_info('List of all the models constructors available')
        rows = []
        for constructor in self.models_constructors.values():
            rows.append([constructor.get_name(), constructor.get_id(), constructor.get_description(), constructor.get_tt1(), constructor.get_tt2(), constructor.get_tt3(), constructor.get_td1(), constructor.get_td2(), constructor.get_ts1(), constructor.get_ts2(), constructor.get_tto()])
        print(table(header=['Name', 'Id', 'Description', 'Tt1', 'Tt2', 'Tt3', 'Td1', 'Td2', 'Ts1', 'Ts2', 'Tto'], rows=rows))



__modelsconstructors__ = Models_Constructors()
