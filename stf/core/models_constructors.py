import persistent
import BTrees.OOBTree

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

    def add_flow(self,info):
        print_info('I got this flow info: {}'.format(info))
        pass

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
        model_constructor.set_tt1(1)
        model_constructor.set_tt2(1)
        model_constructor.set_tt3(1)
        model_constructor.set_td1(1)
        model_constructor.set_td2(1)
        model_constructor.set_ts1(1)
        model_constructor.set_ts2(1)
        model_constructor.set_tto(3600)
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
