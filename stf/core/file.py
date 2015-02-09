import time
import os
from subprocess import Popen,PIPE
import datetime
from dateutil import parser

from stf.common.out import *

class File(object):
    """ A Class to store all the info of different file types"""
    def __init__(self, filename, id):
        self.filename = filename
        self.id = id
        # Set the modification time
        self.set_modificationtime()
        # Guess the file type
        self.guess_type()

    def get_size_in_megabytes(self):
        try:
            size = self.size
        except (AttributeError, TypeError):
            self.compute_size()

        return str(self.size / 1024.0 / 1024.0)+' MB'

    def get_size(self):
        try:
            size = self.size
        except (AttributeError, TypeError):
            self.compute_size()
        return self.size

    def get_duration(self):
        self.get_capinfos()
        return self.capinfo['Capture duration'] 

    def compute_size(self):
        size = os.path.getsize(self.get_name())
        self.size = size

    def get_id(self):
        return self.id

    def set_modificationtime(self):
        ctime = time.ctime(os.path.getmtime(self.get_name()))
        print_info(ctime)
        self.ctime = ctime

    def get_modificationtime(self):
        return self.ctime

    def get_name(self):
        return self.filename

    def get_short_name(self):
        """ Only the name of the file without the path"""
        return os.path.split(self.filename)[1]

    def set_name(self, filename):
        self.filename = filename

    def guess_type(self):
        short_name = os.path.split(self.filename)[1]
        extension = short_name.split('.')[-1]
        if 'pcap' in extension:
            self.set_type('pcap')
        elif 'netflow' in extension:
            self.set_type('binetflow')
        elif 'weblog' in extension:
            self.set_type('weblog')
        elif 'argus' in extension:
            self.set_type('biargus')
        else:
            self.set_type('Unknown')

    def set_type(self, type):
        self.type = type

    def get_type(self):
        return self.type

    def get_capinfos(self):
        """ Get info with capinfos"""
        try :
            ci = self.capinfo
            return True
        except AttributeError:
            # I don't know how to do this better...
            capinfos_path = Popen('bash -i -c "type capinfos"', shell=True, stdin=PIPE, stdout=PIPE).communicate()[0].split()[0]
            if capinfos_path:
                capinfos_info = Popen('capinfos '+self.get_name(), shell=True, stdin=PIPE, stdout=PIPE).communicate()[0].strip().split('\n')

            # Process the capinfo info
            if capinfos_info:
                self.capinfo = {}
                for line in capinfos_info:
                    header = line.split(': ')[0].strip()
                    info = line.split(': ')[1].strip()
                    if 'Number of packets' in header:
                        self.capinfo['Number of packets'] = info
                    elif 'Capture duration' in header:
                        self.capinfo['Capture duration'] = datetime.timedelta(seconds=int(info.split()[0]))
                    elif 'Start time' in header:
                        self.capinfo['Start time'] = parser.parse(info)
                    elif 'End time' in header:
                        self.capinfo['End time'] = parser.parse(info)
                    elif 'MD5' in header:
                        self.capinfo['MD5'] = info
                    elif 'SHA1' in header:
                        self.capinfo['SHA1'] = info
                return True
            else:
                print_error('capinfos is not installed. We can not get more information about the pcap file. apt-get install wireshark-common')
                return False


    def info(self):
        rows = []
        print_info('Information of file name {} with id {}'.format(self.get_short_name(), self.get_id()))

        rows.append(['Type', self.get_type()])
        rows.append(['Creation Time', self.get_modificationtime()])


        # Get the file size
        if not self.get_size():
            self.compute_size()
        rows.append(['Size', str(self.get_size()/1024.0/1024)+' MB'])

        # Get more info from pcap files
        if 'pcap' in self.get_type():
            if self.get_capinfos():
                for infotype in self.capinfo:
                    rows.append([infotype, self.capinfo[infotype]])

        print(table(header=['Key', 'Value'], rows=rows))

