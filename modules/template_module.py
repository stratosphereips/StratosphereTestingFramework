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







#################
#################
#################
class Template_Object(persistent.Persistent):
    """ This class is a template of a classic object. This is usually the place you want to do something. The new 'Object' that you want to store"""
    def __init__(self, id):
        self.id = id
        # This is an example dictionary of stuff that we want to store in the DB and make persistent.
        # self.dict_of_stuff = BTrees.OOBTree.BTree()

    def get_id(self):
        return self.id

    def set_id(self, id):
        self.id = id

    def set_name(self, name):
        self.name = name

    def get_name(self):
        return self.name

    # Mandatory __repr__ module. Something you want to identify each object with. Usefull for selecting objects later
    def __repr__(self):
        return('Id:' + str(self.get_id()))



######################
######################
######################
class Group_of_Template_Objects(Module, persistent.Persistent):
    """ The group of 'Objects' is only a structure to hold them together. Usefull to add them, delete them and general management """
    ### Mandatory variables ###
    cmd = 'template_example_module'
    description = 'This module is a template to use for future modules. It stores permanently in the database the group of objects.'
    authors = ['Sebastian Garcia']
    # Main dict of objects. The name of the attribute should be "main_dict" in this example
    main_dict = BTrees.OOBTree.BTree()
    ### End of Mandatory variables ###

    ### Mandatory Methods Don't change ###
    def __init__(self):
        # Call to our super init
        super(Group_of_Template_Objects, self).__init__()
        # Example of a parameter without arguments
        self.parser.add_argument('-l', '--list', action='store_true', help='List the objects in this group.')
        # Example of a parameter with arguments
        self.parser.add_argument('-p', '--printstate', metavar='printstate', help='Print some info about a specific object. Give the object id.')
        self.parser.add_argument('-g', '--generate', metavar='generate', help='Create a new object with a name. Give name.')

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


    def get_object(self, id):
        return self.main_dict[id]

    def get_objects(self):
        return self.main_dict.values()

    def list_objects(self):
        print_info('List of objects')
        rows = []
        for object in self.get_objects():
            rows.append([ object.get_id(), object.get_name() ])
        print(table(header=['Id', 'Name'], rows=rows))

    def create_new_object(self, name):
        # Generate the new id
        try:
            new_id = self.main_dict[list(self.main_dict.keys())[-1]].get_id() + 1
        except (KeyError, IndexError):
            new_id = 1
        # Create the new object
        new_object = Template_Object(new_id)
        # Do something with it
        new_object.set_name(name)
        # Store on DB
        self.main_dict[new_id] = new_object



    # The run method runs every time that this command is used. Mandatory
    def run(self):
        ######### Mandatory part! don't delete ########################
        # Register the structure in the database, so it is stored and use in the future. 
        if not __database__.has_structure(Group_of_Template_Objects().get_name()):
            print_info('The structure is not registered.')
            __database__.set_new_structure(Group_of_Template_Objects())
        else:
            main_dict = __database__.get_new_structure(Group_of_Template_Objects())
            self.set_main_dict(main_dict)

        # List general help. Don't modify.
        def help():
            self.log('info', self.description)

        # Run
        super(Group_of_Template_Objects, self).run()
        if self.args is None:
            return
        ######### End Mandatory part! ########################
        

        # Process the command line and call the methods. Here add your own parameters
        if self.args.list:
            self.list_objects()
        elif self.args.generate:
            self.create_new_object(self.args.generate)
        else:
            print_error('At least one parameter is required in this module')
            self.usage()
