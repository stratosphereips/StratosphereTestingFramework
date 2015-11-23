import time
import os
from subprocess import Popen,PIPE
import datetime
from dateutil import parser
import persistent

from stf.common.out import *

class File(persistent.Persistent):
    """ A Class to store all the info of different file types"""
    def __init__(self, filename, id):
        # initialize some of the attributes
        self.filename = filename
        self.id = id
        self.duration = False

        # Initialize some inner attributes
        self.capinfo = False
        self.histoinfo = False
        self.binetflowinfo = False

        # Set the modification time
        self.set_modificationtime()
        # Guess the file type to compute some of the info
        self.guess_type()

    def get_size_in_megabytes(self):
        size = self.get_size()
        if size:
            return str(size / 1024.0 / 1024.0)+' MB'
        # We can't even compute the size
        return "No data"

    def get_size(self):
        try:
            size = self.size
        except (AttributeError, TypeError):
            size = self.compute_size()
            if size:
                self.size = size
            else:
                # Could not be computed
                return False
        return self.size

    def set_duration(self,duration):
        self.duration = duration

    def get_duration(self):
        if not self.duration:
            if self.type == 'pcap':
                self.get_capinfos()
            elif self.type == 'binetflow':
                self.get_binetflowinfos()
        # To avoid returing 'False' for the duration
        if self.duration:
            return self.duration
        else:
            return ''

    def compute_size(self):
        try:
            size = os.path.getsize(self.get_name())
        except OSError:
            print_error('The file is not available in your disk.')
            return False
        return size

    def get_id(self):
        return self.id

    def set_modificationtime(self):
        ctime = time.ctime(os.path.getmtime(self.get_name()))
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
        if 'xz' in extension:
            # The file is compressed, but argus can deal with it.
            if 'biargus' in short_name.split('.')[-2]:
                extension = 'biargus'
        if 'pcap' in extension:
            self.set_type('pcap')
        elif 'netflow' in extension:
            self.set_type('binetflow')
        elif 'weblog' in extension:
            self.set_type('weblog')
        elif 'argus' in extension:
            self.set_type('biargus')
        elif 'exe' in extension:
            self.set_type('exe')
        else:
            self.set_type('Unknown')

    def set_type(self, type):
        self.type = type

    def get_type(self):
        """ Returns the type of file """
        return self.type

    def get_binetflowinfos(self):
        """ Get info about binetflow files"""
        if self.binetflowinfo == False and self.get_type() == 'binetflow':
            # Get the time in the first line, ignoring the header
            binetflow_first_flow = Popen('head -n 2 '+self.get_name()+'|tail -n 1', shell=True, stdin=PIPE, stdout=PIPE).communicate()[0]
            first_flow_date = parser.parse(binetflow_first_flow.split(',')[0])

            # Get the time in the last line
            binetflow_last_flow = Popen('tail -n 1 '+self.get_name(), shell=True, stdin=PIPE, stdout=PIPE).communicate()[0]
            last_flow_date = parser.parse(binetflow_last_flow.split(',')[0])

            # Compute the difference
            time_diff = last_flow_date - first_flow_date
            self.set_duration(time_diff)

            # Now fill the data for binetflows
            self.binetflowinfo = {}
            # Duration
            self.binetflowinfo['Duration'] = self.get_duration()

            # Amount of flows
            amount_of_flows = Popen('wc -l '+self.get_name(), shell=True, stdin=PIPE, stdout=PIPE).communicate()[0].split()[0]
            self.binetflowinfo['Amount of flows'] = amount_of_flows


        # Always return true
        return True

    def get_capinfos(self):
        """ Get info with capinfos"""
        if self.capinfo == False and self.get_type() == 'pcap':
            # I don't know how to do this better...
            capinfos_path = Popen('bash -i -c "type capinfos"', shell=True, stdin=PIPE, stdout=PIPE).communicate()[0].split()[0]

            if capinfos_path:
                (capinfos_data,capinfos_error) = Popen('tcpdump -n -s0 -r ' + self.get_name() + ' -w - | capinfos -r -', shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE).communicate()
                capinfos_info = capinfos_data.strip().split('\n')

            # Process the capinfo info
            if 'Value too large' in capinfos_error:
                print_error('There was an error with capinfos. Maybe the file is too large. See https://www.wireshark.org/lists/wireshark-users/200908/msg00008.html')
                self.capinfo = ''
                return False
            elif capinfos_info:
                self.capinfo = {}
                for line in capinfos_info:
                    header = line.split(': ')[0].strip()
                    info = line.split(': ')[1].strip()
                    if 'Number of packets' in header:
                        self.capinfo['Number of packets'] = info
                    elif 'Capture duration' in header:
                        self.capinfo['Capture duration'] = datetime.timedelta(seconds=int(info.split()[0]))
                        # The default duration of the file can be setted now also
                        self.set_duration(self.capinfo['Capture duration'])
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

    def get_bytes_histo(self):
        """ Use tshark to get the amount of bytes per 10minutes in the pcap file"""
        if self.histoinfo == False and self.get_type() == 'pcap':
            capinfos_path = Popen('bash -i -c "type tshark"', shell=True, stdin=PIPE, stdout=PIPE).communicate()[0].split()[0]

            if capinfos_path:
                (tshark_data,tshark_error) = Popen('tshark -r '+self.get_name()+' -z io,stat,300,"COUNT(frame)frame" -q|grep "<>"|head -n 24', shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE).communicate()
                tshark_info = tshark_data.strip().split('\n')
                self.histoinfo = {}
                for line in tshark_info:
                    header = line.split('|')[1].strip()
                    # Store the key as int for later sorting
                    number_in_header = float(header.split('<>')[0].strip())
                    info = line.split('|')[2].strip()
                    self.histoinfo[number_in_header] = header + '|' + info
                return True
            else:
                print_error('tshark is not installed. We can not get more information about the pcap file. apt-get install tshark')
                return False
        elif self.histoinfo and self.get_type() == 'pcap':
            return True

    def get_md5(self):
        """ Return the md5 of the file """
        try:
            return self.md5
        except AttributeError:
            self.md5 = tshark_data = Popen('md5sum '+self.get_name()+' | awk \'{print $1}\'', shell=True, stdin=PIPE, stdout=PIPE).communicate()[0]
            return self.md5

    def info(self):
        rows = []
        print_info('Information of file name {} with id {}'.format(self.get_short_name(), self.get_id()))

        rows.append(['Type', self.get_type()])
        rows.append(['Creation Time', self.get_modificationtime()])

        # Get the file size
        #if not self.get_size():
            #self.compute_size()
        size = self.get_size()
        if not size:
            return False
        rows.append(['Size', str(size/1024.0/1024)+' MB'])

        # Get more info from pcap files
        if 'pcap' in self.get_type():
            # Get capinfo data
            if self.get_capinfos():
                for infotype in self.capinfo:
                    rows.append([infotype, self.capinfo[infotype]])
            # Get the amount of bytes every 10 mins
            if self.get_bytes_histo():
                rows.append(['Time Range (secs)', 'Amount of Packets' ])
                for histo_header in sorted(self.histoinfo):
                    rows.append([self.histoinfo[histo_header].split('|')[0], self.histoinfo[histo_header].split('|')[1]])

        # Get more info from binetflow files
        elif 'binetflow' in self.get_type():
            if self.get_binetflowinfos():
                for infotype in self.binetflowinfo:
                    rows.append([infotype, self.binetflowinfo[infotype]])
        elif 'exe' in self.get_type():
            # Get exe data
            # md5
            rows.append(['MD5', self.get_md5()])

        print(table(header=['Key', 'Value'], rows=rows))

    def __repr__(self):
        return('File id: {}. Name: {}. Type: {}'.format(self.get_id(), self.get_name(), self.get_type()))
