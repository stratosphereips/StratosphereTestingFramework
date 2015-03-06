import ConfigParser
import os

from stf.common.out import *


class Configuration(object):
    """
    The class to deal with the configuration. Every other class that wants to read the configuration just instantiate this one.
    """
    def __init__(self):
        self.config = ConfigParser.ConfigParser()
        self.zeoconffile = None
        self.zodbconffile = None

    def read_conf_file(self, conf_file):
        """ Read the conf file"""
        # Read the sections
        self.config.read(conf_file)
        stf_section = self.ConfigSectionMap('stf')
        try:
            self.zeoconffile = stf_section['zeoconfigurationfile']
            self.zodbconffile = stf_section['zodbconfigurationfile']
        except:
            print_error('Errors in the configuration files.')
            return False
        return True

    def get_zeoconf_file(self):
        return self.zeoconffile

    def get_zodbconf_file(self):
        return self.zodbconffile

    def ConfigSectionMap(self,section):
        """ Taken from the python site"""
        dict1 = {}
        options = self.config.options(section)
        for option in options:
            try:
                dict1[option] = self.config.get(section, option)
                if dict1[option] == -1:
                    print_info("Skip: %s" % option)
            except:
                print_error("Exception on %s!" % option)
                dict1[option] = None
        return dict1


__configuration__ = Configuration()
