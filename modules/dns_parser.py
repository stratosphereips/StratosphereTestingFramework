# Part of this file was taken from Viper - https://github.com/botherder/viper
# The rest is from the Stratosphere Testing Framework
# See the file 'LICENSE' for copying permission.

# Example file of how to create a module without persistence in the database. Useful for obtaining statistics or processing data.

from stf.common.out import *
from stf.common.abstracts import Module
from stf.core.models import  __groupofgroupofmodels__ 
from stf.core.dataset import __datasets__
from stf.core.notes import __notes__
from stf.core.connections import  __group_of_group_of_connections__
from stf.core.models_constructors import __modelsconstructors__ 
from stf.core.labels import __group_of_labels__
import tempfile
from subprocess import Popen
from subprocess import PIPE


import pprint
import socket
import struct


def decode_labels(message, offset):
    labels = []

    while True:
        length, = struct.unpack_from("!B", message, offset)

        if (length & 0xC0) == 0xC0:
            pointer, = struct.unpack_from("!H", message, offset)
            offset += 2

            return labels + decode_labels(message, pointer & 0x3FFF), offset

        if (length & 0xC0) != 0x00:
            raise StandardError("unknown label encoding")

        offset += 1

        if length == 0:
            return labels, offset

        labels.append(*struct.unpack_from("!%ds" % length, message, offset))
        offset += length


DNS_QUERY_SECTION_FORMAT = struct.Struct("!2H")

def decode_question_section(message, offset, qdcount):
    questions = []

    for _ in range(qdcount):
        qname, offset = decode_labels(message, offset)

        qtype, qclass = DNS_QUERY_SECTION_FORMAT.unpack_from(message, offset)
        offset += DNS_QUERY_SECTION_FORMAT.size

        question = {"domain_name": qname,
                    "query_type": qtype,
                    "query_class": qclass}

        questions.append(question)

    return questions, offset


DNS_QUERY_MESSAGE_HEADER = struct.Struct("!6H")

def decode_dns_message(message):

    id, misc, qdcount, ancount, nscount, arcount = DNS_QUERY_MESSAGE_HEADER.unpack_from(message)

    qr = (misc & 0x8000) != 0
    opcode = (misc & 0x7800) >> 11
    aa = (misc & 0x0400) != 0
    tc = (misc & 0x200) != 0
    rd = (misc & 0x100) != 0
    ra = (misc & 0x80) != 0
    z = (misc & 0x70) >> 4
    rcode = misc & 0xF

    offset = DNS_QUERY_MESSAGE_HEADER.size
    questions, offset = decode_question_section(message, offset, qdcount)

    result = {"id": id,
              "is_response": qr,
              "opcode": opcode,
              "is_authoritative": aa,
              "is_truncated": tc,
              "recursion_desired": rd,
              "recursion_available": ra,
              "reserved": z,
              "response_code": rcode,
              "question_count": qdcount,
              "answer_count": ancount,
              "authority_count": nscount,
              "additional_count": arcount,
              "questions": questions}

    return result


#s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#host = ''
#port = 53
#size = 512
#s.bind((host, port))
#while True:
#    data, addr = s.recvfrom(size)
#    pprint.pprint(decode_dns_message(data))











class DNSInfo(Module):
    cmd = 'dns_parser'
    description = 'Module to compute statistics of a DNS tuple.'
    authors = ['Harpo MAxx']

    def __init__(self):
        # Call to our super init
        super(DNSInfo, self).__init__()
        self.parser.add_argument('-i', '--info', metavar='tuple_id', help='Show DNS statistics for this 4-tuple.')

    def show_flows(self,group_of_connections,connection_id):
        all_text=''
        # Access each flow in this 4-tuple
        for flow_id in group_of_connections.connections[connection_id].flows:
#            all_text = all_text + group_of_connections.connections[connection_id].flows[flow_id].get_srcUdata() + '\n'
            dns_text = ":".join("{:02x}".format(ord(c)) for c in group_of_connections.connections[connection_id].flows[flow_id].get_srcUdata())
            all_text = all_text + dns_text + '\n\n'
        f = tempfile.NamedTemporaryFile()
        f.write(all_text)
        f.flush()
        p = Popen('less -R ' + f.name, shell=True, stdin=PIPE)
        p.communicate()
        sys.stdout = sys.__stdout__ 
        f.close()

    def dns_info(self,connection_id):
#        """ Show the flows inside a connection """
#        #__group_of_group_of_connections__.show_flows_in_connnection(arg, filter)
        if __datasets__.current:
            group_id = __datasets__.current.get_id()
            try:
                print_info('Showing the DNS information of 4tuple {}'.format(connection_id))
                self.show_flows(__group_of_group_of_connections__.group_of_connections[group_id],connection_id)
            except KeyError:
                print_error('The connection {} does not longer exists in the database.'.format(connection_id))
        else:
            print_error('There is no dataset selected.')

    def run(self):
        # List general info
        def help():
            self.log('info', self.description)
        # Run?
        super(DNSInfo, self).run()
        if self.args is None:
            return
        if self.args.info:
            self.dns_info(self.args.info)
        else:
            print_error('At least one parameter is required')
            self.usage()
