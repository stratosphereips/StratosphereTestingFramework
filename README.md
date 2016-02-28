# Stratosphere Testing Framework

The [Stratosphere Testing Framework] [stf] (**stf**) is a network security research framework to analyze the behavioral patterns of network connections in the [Stratosphere Project](https://stratosphereips.org). Its goal is to aid researchers find new malware behavior, to label those behaviors, to create their traffic models and to verify the detection algorithms. Once the best malware behavioral models are created and verified, they will be used in the [Stratosphere IPS](https://stratosphereips.org) for detection. **Stf** works by using machine learning algorithms on the behavioral models.

The goal of the Stratosphere Project is to create a behavioral IPS (Intrusion Detection System) that can detect and block malicious behaviors in the network. As part of this project, the **stf** is used to generate highly confident models of malicious traffic by allowing an automated verification of the detection performance. 

The current features of the alpha release of **stf** are:

1. Management of datasets.
    - Load pcap files (including large pcap files of more than 5GB).
    - Load biargus files.
    - Load binetflow files (text flows files from argus).
    - Load PE executable files.
    - Add notes to datasets.
    - Give info about the files (md5, capinfos integration, amount of packets in time, etc).
2. Extract the network connections (4-tuples connections that ignore the source port)
3. Generate the behavioral models of each connection.
4. Assist the analyst in identifying those models by:
    - Visualizing the payload in the traffic.
    - Plotting histograms on the features of the models.
    - Visualizing the behavioral models.
    - Adding notes to the models.
5. Interactive console of commands with auto completion.
6. Option to use a local database or a remote distributed database.
7. Concurrency of several instances of **stf** simultaneously on the same database (local or remote). Which allows several researchers working on the same dataset.

## Installation and Dependencies
First clone the git repository and ```cd``` into it. Before installing stf, you need to install some dependencies. So far the stf program is designed to work on Linux environments. You can use the _pip_ program to install the dependencies:

```sudo pip install -r dependencies.txt```  

Or you can install them by hand                    

- prettytable: ```apt-get install python-prettytable```
- transaction: ```apt-get install python-transaction```
- persistent: ```apt-get install python-persistent``` 
- zodb: ```pip install zodb``` (version > 4.0)
- sparse: ```apt-get install python-sparse```

You also need to have [argus](http://http://qosient.com/argus/) (and argus clients tools) installed. This is for generating the netflows from the traffic. These tools need to be installed from its latest version (and not the ones available in the debian/ubuntu repository until April 2015). The programs can be downloaded from:

- argus ```http://qosient.com/argus/dev/argus-latest.tar.gz```
- argus-clients ```http://qosient.com/argus/dev/argus-clients-latest.tar.gz```

There are two optional tools that you can install to improve the usefulness of stf. The first one is the capinfo tool, that is available in the wireshark-common debian/ubuntu package. This tool can be installed in debian/ubuntu with `apt-get install wireshark-common`.

The second one is the tool called _distribution_, which give you awesome ascii-art histogram of the data. the distribution tool needs to be installed manually from program https://github.com/philovivero/distribution.

Then you are ready to use stf.py!


# The meaning of the Behavioral Models
The core of the Stratosphere IPS is composed of what we called **network behavioral models** and detection algorithms. The behavioral models represent what a specific connection does in the network during its life time. The behavior is constructed by analyzing the periodicity, size and duration of each flow. Based on these features each flow is assigned a letter and the group of letters characterize the behavior of the connection. The criteria to assign the letters is the following:

For example, the connection identified with the 4-tuple 192.168.0.253-166.78.144.80-80-tcp, that was assigned the label From-Botnet-V1-TCP-CC12-HTTP had the following behavioral model:

> 88\*y\*y\*i\*H\*H\*H\*y\*0yy\*H\*H\*H\*y\*y\*y\*y\*H\*h\*y\*h\*h\*H\*H\*h\*H\*y\*y\*y\*H\*

This chain of states that we call the behavioral model highlight some of the characteristics of the C&C channel. In this case it tell us that that flows are highly periodic (letters ‘h’, ‘i’), with some lost periodicity near the beginning (letters ‘y’). The flows also have a large size with a medium duration. The symbols between the letters are related with the time elapsed between flows. In this case the '*' symbol means that the flow are separated by less than one hour. Looking at the letters it can be seen that this is a rather periodic connection, and efectively checking its flows we confim that hipotesis.  Using these type of models we are able to generate the behavioral characteristics of a large number of malicious actions.

For more details on the behavioral models see [Research Publications](https://stratosphereips.org/category/publications.html).


## How to use the stf program 
To start using the program you just need to execute it:

> ./stf.py

And you should see something like 
```
    Stratosphere Testing Framework
             _    __ 
            | |  / _|
         ___| |_| |_ 
        / __| __|  _|
        \__ \ |_| |  
    ... |___/\__|_|  ...
    0.1.2alpha

    
[*] Amount of experiments in the DB so far: 0
[*] Amount of datasets in the DB so far: 0
[*] Amount of groups of connections in the DB so far: 0
[*] Amount of groups of models in the DB so far: 0
[*] Amount of notes in the DB so far: 0
stf >
```

## Usage
We will exemplify here a common session of **stf**.
- Getting help
```
test: stf > help
Commands:
+-------------+-------------------------------------------------------------+
| Command     | Description                                                 |
+-------------+-------------------------------------------------------------+
| clear       | Clear the console                                           |
| connections | Manage the connections. A dataset should be selected first. |
| database    | Manage the database.                                        |
| datasets    | Manage the datasets                                         |
| exit        | Exit                                                        |
| experiments | List or switch to existing experiments                      |
| help        | Show this help message                                      |
| info        | Show information on the opened experiment                   |
| labels      | Manage the labels.                                          |
| models      | Manage the models. A dataset should be selected first.      |
| notes       | Manage the notes.                                           |
+-------------+-------------------------------------------------------------+
test: stf >
```
- Load a pcap file
```
stf > dataset -c /tmp/test/test-1.pcap
The name of the dataset or 'Enter' to use the name of the last folder:
[*] Added file /tmp/test/test-1.pcap to dataset test
[*] Dataset test added with id 0.
test: stf >
```
- Listing of datasets (after creating a dataset, that dataset is selected by default)
```
test: stf > datasets -l
[*] Datasets Available:
+--------------+----+---------------------+----------------+--------------------------+------------+---------+-------+
| Dataset Name | Id | Added Time          | Main File Name | Main File Creation Time  | Folder     | Current | Note  |
+--------------+----+---------------------+----------------+--------------------------+------------+---------+-------+
| test         | 0  | 2015-03-06 20:20:44 | test1.pcap     | Mon May 31 00:44:43 2010 | /tmp/test/ | True    | False |
+--------------+----+---------------------+----------------+--------------------------+------------+---------+-------+
test: stf >
```
- Listing the files in the dataset
```
test: stf > datasets -f
[*] Getting information about the files... please wait
[*] Files Available in Dataset test:
+-------------+----+--------------------------+------------------+------+
| File Name   | Id | Creation Time            | Size             | Type |
+-------------+----+--------------------------+------------------+------+
| test-1.pcap | 0  | Fri Mar  6 20:25:18 2015 | 37.7940015793 MB | pcap |
+-------------+----+--------------------------+------------------+------+
test: stf >
```
- Detailed information about the pcap
```
test: stf > datasets -F 0
[*] Information of file name test-1.pcap with id 0
+-------------------+------------------------------------------+
| Key               | Value                                    |
+-------------------+------------------------------------------+
| Type              | pcap                                     |
| Creation Time     | Fri Mar  6 20:25:18 2015                 |
| Size              | 37.7940015793 MB                         |
| SHA1              | 7997d7087752ccce621b5f427960b13347d983a1 |
| Number of packets | 83 k                                     |
| Start time        | 2010-05-30 19:03:41                      |
| End time          | 2010-05-30 20:55:52                      |
| Capture duration  | 1:52:11                                  |
| MD5               | 06bbdac7b682356ecde602e5eeab8e78         |
| Time Range (secs) | Amount of Packets                        |
| 0 <>  300         | 2731                                     |
| 300 <>  600       | 8003                                     |
| 600 <>  900       | 6544                                     |
| 900 <> 1200       | 7717                                     |
| 1200 <> 1500      | 7815                                     |
| 1500 <> 1800      | 7638                                     |
| 1800 <> 2100      | 3016                                     |
| 2100 <> 2400      | 7728                                     |
| 2400 <> 2700      | 12799                                    |
| 2700 <> 3000      | 10981                                    |
| 3000 <> 3300      | 7132                                     |
| 3300 <> 3600      | 143                                      |
| 3600 <> 3900      | 185                                      |
| 3900 <> 4200      | 145                                      |
| 4200 <> 4500      | 111                                      |
| 4500 <> 4800      | 101                                      |
| 4800 <> 5100      | 155                                      |
| 5100 <> 5400      | 17                                       |
| 5400 <> 5700      | 8                                        |
| 5700 <> 6000      | 17                                       |
| 6000 <> 6300      | 0                                        |
| 6300 <> 6600      | 1                                        |
| 6600 <> Dur       | 651                                      |
+-------------------+------------------------------------------+
test: stf >
```
- Generating the biargus file and the binetflows file
```
test: stf > datasets -g
[] Generating the biargus file.
[] Added file /tmp/test/test-1.biargus to dataset test
[] Generating the binetflow file.
[] Added file /tmp/test/test-1.binetflow to dataset test
test: stf >
```
- Listing the groups of files in the dataset
```
test: stf > datasets -f
[] Getting information about the files... please wait
[] Files Available in Dataset test:
+------------------+----+--------------------------+-------------------+-----------+
| File Name        | Id | Creation Time            | Size              | Type      |
+------------------+----+--------------------------+-------------------+-----------+
| test-1.pcap      | 0  | Fri Mar  6 20:25:18 2015 | 37.7940015793 MB  | pcap      |
| test-1.biargus   | 1  | Fri Mar  6 20:49:27 2015 | 0.379196166992 MB | biargus   |
| test-1.binetflow | 2  | Fri Mar  6 20:49:27 2015 | 0.302586555481 MB | binetflow |
+------------------+----+--------------------------+-------------------+-----------+
test: stf >
```
- Adding a note to the dataset (your default editor will be open)
```
test: stf > datasets -n 0
test: stf >
```
- Generating the connections
```
test: stf > connections -g
test: stf >
```
- Listing the groups of connections
```
test: stf > connections -l
[] Groups of Connections Available:
+----------------------------+------------+----------------------------+-----------------------+
| Id of Group of Connections | Dataset Id | Filename                   | Amount of Connections |
+----------------------------+------------+----------------------------+-----------------------+
| 0                          | 0          | /tmp/test/test-1.binetflow | 446                   |
+----------------------------+------------+----------------------------+-----------------------+
test: stf >
```
- Listing the connections 
```
test: stf > connections -L 0
```
- Listing the connections with a filter (less -R will be used to show the connections. See the Tips section at the bottom)
```
test: stf > connections -L 0 -f flowamount>20
| Connection Id | Amount of flows |
192.168.0.10-200.58.116.122-80-tcp       | 93
192.168.0.10-208.13.144.35-80-tcp        | 54
192.168.0.10-69.63.176.165-80-tcp        | 21
192.168.0.10-72.246.64.83-80-tcp         | 33
Amount of connections printed: 4
test: stf > 
```
- Generating the models
```
test: stf > models -g
test: stf >
```
- Listing the groups of models
```
test: stf > models -l
[] Groups of Models
+-------------------+------------------+------------+--------------+
| Group of Model Id | Amount of Models | Dataset Id | Dataset Name |
+-------------------+------------------+------------+--------------+
| 0-1               | 446              | 0          | test         |
+-------------------+------------------+------------+--------------+
test: stf >
```
- Listing all the models (less -R will be used to show the models)
```
test: stf > models -L 0-1
test: stf >
```
- Listing the models with a filter (less -R will be used to show the models). This is a very important command, since it show the behavioral model that are the core of the **stf** program.
```
test: stf > models -L 0-1 -f name=6-80-tcp
 Note | Label | Model Id | State |
[   ] |         | 192.168.0.10-200.123.195.16-80-tcp        | 99+Z.Z.Z.
[   ] |         | 192.168.0.10-200.123.195.26-80-tcp        | 99.Z+Z.Z+Z.Z.I.I.Z.Z+
[   ] |         | 192.168.0.10-204.9.163.166-80-tcp         | 55,v,v.W+E+v+V,V+v+
[   ] |         | 192.168.0.10-65.54.85.156-80-tcp          | 8
[   ] |         | 192.168.0.10-65.54.85.206-80-tcp          | 88+
Amount of models printed: 5
test: stf >
```
- Inspecting the payload that generated a model (less -R will be used to show the models). The content of the packets is captured and stored by argus. We limit the payload to 400 bytes on each direction.
```
test: stf > connections -F 192.168.0.253-166.78.144.80-80-tcp
 State: "8" TD: -1.0 T2: False T1: False        2013/04/23 17:48:39.561383,0.567582,tcp,192.168.0.253,   ->,166.78.144.80,80,FSPA_FSPA,0,0,15,1628,1124,s[480]=GET / HTTP/1.1..Accept: */*..Accept-Language: en-US..User-Agent: Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6
.1; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0)..Host: wgylqqcqwovdztucwljbrkvcypbe.info..Connection: Close....GET / HTTP/1.1..Accept: */*..Accept-Language: en-US..User-Agent: Mozilla/4.0 (compatible; MSIE 7.0; Win
dows NT 6.1; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Medi,d[204]=HTTP/1.1 200 OK..Date: Tue 23 Apr 2013 15:49:38 GMT..Server: Apache/2.2.20 (Ubuntu)..X-Sinkhole: malware-sinkhole..Vary: Accept-Encoding..Content-Length: 0..Connectio
n: close..Content-Type: text/html....,
 State: "8*" TD: -1.0 T2: 0:25:11.313436 T1: False      2013/04/23 18:13:50.874819,2.366329,tcp,192.168.0.253,   ->,166.78.144.80,80,FSPA_FSPA,0,0,19,2964,2460,s[480]=GET / HTTP/1.1..Accept: */*..Accept-Language: en-US..User-Agent: Mozilla/4.0 (compatible; MSIE 7.0; Wind
ows NT 6.1; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0)..Host: wgylqqcqwovdztucwljbrkvcypbe.info..Connection: Close....GET / HTTP/1.1..Accept: */*..Accept-Language: en-US..User-Agent: Mozilla/4.0 (compatible; MSIE 
7.0; Windows NT 6.1; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Medi,d[204]=HTTP/1.1 200 OK..Date: Tue 23 Apr 2013 16:14:51 GMT..Server: Apache/2.2.20 (Ubuntu)..X-Sinkhole: malware-sinkhole..Vary: Accept-Encoding..Content-Length: 0..C
onnection: close..Content-Type: text/html....,
 State: "y*" TD: 2.346708 T2: 0:59:06.611929 T1: 0:25:11.313436 2013/04/23 19:12:57.486748,0.859667,tcp,192.168.0.253,   ->,166.78.144.80,80,FSPA_FSPA,0,0,15,1628,1124,s[480]=GET / HTTP/1.1..Accept: */*..Accept-Language: en-US..User-Agent: Mozilla/4.0 (compatible; MSIE 7
.0; Windows NT 6.1; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0)..Host: wgylqqcqwovdztucwljbrkvcypbe.info..Connection: Close....GET / HTTP/1.1..Accept: */*..Accept-Language: en-US..User-Agent: Mozilla/4.0 (compatibl
e; MSIE 7.0; Windows NT 6.1; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Medi,d[204]=HTTP/1.1 200 OK..Date: Tue 23 Apr 2013 17:13:56 GMT..Server: Apache/2.2.20 (Ubuntu)..X-Sinkhole: malware-sinkhole..Vary: Accept-Encoding..Content-Leng
th: 0..Connection: close..Content-Type: text/html....,
test: stf >
```
- Showing the histogram of some features (T2 is one of the features of the model representing the time difference between flows)
```
test: stf > connections -H 192.168.0.10-200.58.116.122-80-tcp
Key=T2 in secs (limited to 2 decimals)
Key|Ct (Pct)    Histogram
0.0|25 (27.17%) ----------------------------------------------------------------
0.1|21 (22.83%) -----------------------------------------------------
0.2|10 (10.87%) --------------------------
0.3|10 (10.87%) --------------------------
0.4|11 (11.96%) ----------------------------
0.5|4 (4.35%)   -----------
0.6|3 (3.26%)   --------
0.7|4 (4.35%)   -----------
0.9|1 (1.09%)   ---
1.0|1 (1.09%)   ---
1.1|1 (1.09%)   ---
3.2|1 (1.09%)   ---

Key=Size in bytes
Key |Ct (Pct)    Histogram
1628|26 (83.87%) ---------------------------------------------------------------
1736|1 (3.23%)   ---
1796|2 (6.45%)   -----
2964|1 (3.23%)   ---
3132|1 (3.23%)   ---
test: stf >
```
- Histogram of the lengths of the states of the models
```
test: stf > models -H 0-1
Key=Length of state
Key|Ct (Pct)     Histogram
1  |364 (81.61%) ---------------------------------------------------------------
2  |47 (10.54%)  ---------
3  |9 (2.02%)    --
5  |6 (1.35%)    --
7  |3 (0.67%)    -
9  |2 (0.45%)    -
13 |2 (0.45%)    -
15 |2 (0.45%)    -
19 |2 (0.45%)    -
21 |1 (0.22%)    -
23 |1 (0.22%)    -
25 |1 (0.22%)    -
37 |1 (0.22%)    -
39 |1 (0.22%)    -
41 |1 (0.22%)    -
65 |1 (0.22%)    -
107|1 (0.22%)    -
185|1 (0.22%)    -
test: stf >
```
- Using several filters simultaneously
```
captura-i78zR: stf > models -L 1-1 -f name!=-53-udp statelength>50
 Note | Model Id | State |
[   ] | 192.168.0.249-166.78.144.80-80-tcp        | 88*y*y*y*H*y*y*y*y*y*y*0yy*y*H*H*h*H*H*y*y*h*y*y*y*H*i*y*I*z*
[ 12] | 192.168.0.249-192.168.0.1--arp            | 99.0ZZ.0ZZ.0ZZ.0ZZ.0ZZ.0ZZ.0ZZ.0ZZ.0ZZ.0ZZ.0ZZ.0ZZ.0ZZ.0ZZ.0ZZ.0ZZ.0ZZ.0ZZ.0ZZ.0TW.
[   ] | 192.168.0.253-166.78.144.80-80-tcp        | 88*y*y*i*H*H*H*y*0yy*H*H*H*y*y*y*y*H*h*y*h*h*H*H*h*H*y*y*y*H*
[  5] | 192.168.0.253-192.168.0.1--arp            | 99.0ZZ.0ZZ.0ZZ.0ZZ.0ZZ.0ZZ.0ZZ.0ZZ.0ZZ.0ZZ.0ZZ.0ZZ.0ZZ.0ZZ.0ZZ.0ZZ.0ZZ.0ZZ.0ZZ.0ZZ.
[   ] | 192.168.0.254-166.78.144.80-80-tcp        | 88*y*y*y*H*y*0yy*y*H*H*H*y*y*y*H*h*H*y*y*y*y*H*y*H*h*H*y*y*y*
[   ] | 192.168.0.254-192.168.0.1--arp            | 99.0ZZ.0ZZ.0ZZ.0ZZ.0ZZ.0ZZ.0ZZ.0ZZ.0ZZ.0ZZ.0ZZ.0ZZ.0ZZ.0ZZ.0ZZ.0ZZ.0ZZ.0ZZ.0ZZ.0WW.
Amount of models printed: 6
captura-i78zR: stf >
```
- Deleting connections and models. The connections and models can be deleted by id or using the filters. It is also handy to count the amount of object to delete before actually doing it, so you can be sure of what you are deleting. Command to count the connections with a filter.
```
captura-i78zR: stf > connections -C 1 -f flowamount<3
[] Amount of connections that match the filter: 279
captura-i78zR: stf >
```
- Deleting the connections with a filter.
```
captura-i78zR: stf > connections -D 1 -f flowamount<3
[] Amount of connections deleted: 279
captura-i78zR: stf >
```
- Listing of notes
```
test: stf > notes -l
[] Note 0
# This is our first note on a dataset
test: stf >
```
- Deleting of notes
```
captura-i78zR: stf > notes -d 1
captura-i78zR: stf >
```
- Editing notes (will use your default editor)
```
captura-i78zR: stf > notes -e 1
captura-i78zR: stf >
```
- Adding a label to a specific connection
```
test: stf > labels -a -c 192.168.1.128-54.208.18.216-80-tcp -g 15-1
[!] Remember that a label should represent a unique behavioral model!
Please provide a direction. It means 'From' or 'To' the most important IP in the connection: 
From
Please provide the main decision. 'Botnet', 'Normal', 'Attack', or 'Background': 
Normal
Please provide the layer 3 proto. 'TCP', 'UDP', 'ICMP', 'IGMP', or 'ARP': 
TCP
Please provide the main proto in layer 4. 'HTTP', 'HTTPS', 'FTP', 'SSH', 'DNS', 'SMTP', 'P2P', 'Multicast', 'Unknown' or 'None': 
HTTP
Please provide optional details for this connection. Up to 30 chars (No - or spaces allowed). Example: 'Encrypted', 'PlainText', 'CustomEncryption', 'soundcound.com', 'microsoft.com', 'netbios': 
iflscience.com
[*] Connection has note id 59
```
- Adding a label to multiple connections
```
test: stf > labels -a -f connid=192.168.1.128 connid=-80-tcp -g 15-1
[!] Remember that a label should represent a unique behavioral model!
Please provide a direction. It means 'From' or 'To' the most important IP in the connection: 
From
Please provide the main decision. 'Botnet', 'Normal', 'Attack', or 'Background': 
Normal
Please provide the layer 3 proto. 'TCP', 'UDP', 'ICMP', 'IGMP', or 'ARP': 
TCP
Please provide the main proto in layer 4. 'HTTP', 'HTTPS', 'FTP', 'SSH', 'DNS', 'SMTP', 'P2P', 'Multicast', 'Unknown' or 'None': 
HTTP
Please provide optional details for this connection. Up to 30 chars (No - or spaces allowed). Example: 'Encrypted', 'PlainText', 'CustomEncryption', 'soundcound.com', 'microsoft.com', 'netbios': 
iflscience.com
[*] Connection has note id 59
[*] Connection has note id 60
[*] Connection has note id 61
```
- Looking at the labels (For more information about the labelling process see [labels](doc/labels.md)) 
```
stf > labels -l
+----+---------------------------------------+----------------+----------------------------------------+
| Id | Label Name                            | Group of Model | Connection                             |
+----+---------------------------------------+----------------+----------------------------------------+
| 1  | From-Normal-UDP-Multicast-WPAD-1      | 13-1           | ['10.0.2.15-224.0.0.252-5355-udp']     |
| 2  | From-Normal-UDP-DNS--1                | 13-1           | ['10.0.2.15-10.0.2.3-53-udp']          |
| 3  | From-Botnet-UDP-DNS-DGA-1             | 9-1            | ['10.0.2.105-8.8.8.8-53-udp']          |
| 4  | From-Botnet-UDP-DNS-DGA-2             | 9-1            | ['10.0.2.105-8.8.4.4-53-udp']          |
| 5  | From-Normal-TCP-HTTP-iflscience.com-1 | 15-1           | ['192.168.1.128-54.208.18.216-80-tcp'] |
+----+---------------------------------------+----------------+----------------------------------------+
```
- All the commands show a help menu with the parameter -h.

## Changing the Configuration
By default **stf** will search for the configuration file in confs/stf.conf. From that file it will read where are the configuration files for the ZODB and the ZEO server if it is being used. Upon the first run, **stf** will create the folder ~/.stf/, containing the .stfhistory file (the history of commands). The database folder is also relative to the local folder and is by default ./database 

There are two ways of using the database. Since **stf** is designed to be used both as single host program and as a multi-user program, it can run with a file-based database or with a server-based database. The file-based database (used by default) is suited for single user and single host environments, whereas the server-based database is suited for multi-user and remote host environments.

### How to use the stf program with a file database
By default **stf** is using the zodb.conf file, which is prepared to use a file-based database. This means that the default zodb.conf file already includes the file server configuration. The location of the file database will be by default in ./database. You don't have to don nothing to use this configuration, it is already prepared for you.

### How to use the stf with a database server
If you want to separate the database from the clients, probably to allow several users to use **stf** simultaneously, you need to:

1- Copy the example conf file *confs/example_zodb_server_database.conf* to the *confs/zodb.conf* file.  
2- Start the database server with the command 

```runzeo -C confs/zeo.conf```

4- Use the **stf** normally.   

## Why argus?
The argus suite was selected to generate the traffic flows because it is one of the most stable and resilient programs that can generate bidirectional flows. The bidirectional argus flows solve the problem of having to _match_ the pair of related flows in both directions. Also, since argus uses its own binary format, it is very easy to extract new information and process it very fast.


## Tips on Usage 
- When looking at the list of models or list of connections, **stf** uses 'less -R' to show you the information paginated. However, if you want to store the output in an external file for later analysis, you can run '! cat % > /tmp/file' from inside less and store the file to disk.
- Everytime that **stf** exits, it commits the content to the database.
- **stf** has a special command to inspect the database, that is called __database__. It can be used to commit changes to the database (```database -c```) or to revert the current program memory state to reflect the current state of the database (```database -r```). This allows for a better coordination of simultaneous researchers. Since this is an alpha release, you can have some conflicts while working simultaneously.


# Advance Usage
- **stf** uses ZODB as a database. This means that it uses an object-oriented database model. The main advantage of this model is that **stf** can be run directly on a database file (as sqlite) but also it can transparently use a remote and distributed database. Setting up a distributed database is handy for having several researchers working in the network on the same dataset. See how to set up a distributed database server above.
- The behavioral models are constructed from the models_constructors.py file. In that file you can see the details of the behavioral models. 
- Trimming the amount of flows in a connection. Since **stf** stores all the flows on each connection, it may be possible that the amount of data stored in the database for a certain connection is too large (more than 25MB per connection object). In this case it is possible to trim the amount of flows in the connections to save space. This operation should be done _after_ the creation of the models, so the behavioral state can have all the letters. An example command is:
```
test: stf > connections -t 2000
test: stf >
```

This command will trim all the connections to a maximum of 2000 flows each.
You can check that this was successful by inspecting the connections with ```connections -L```.

- There is a feature in **stf** that allows it to add text automaticaly to the notes of the dataset. This feature is used to insert notes on certain important operations that is good for the researcher to remember. For example, if you trim the amount of flows in the connections, **stf** will add a text in the dataset note with details of this operation.
- **stf** also allow you to execute bash commands by using ! as the first letter. Therefore is easy to interact with other tools, such as tcpdump, tshark or the argus clients.
- The filters can use the following keys. For connections: flowamount, flowlabel (the label in the original flow) and name. For models: name, statelength, labelname (the label assigned by stf). The operators in the filters are: <, >, = and !=
- The listings of models and datasets include a column with the id of the note that is related to that object. You can edit notes directly with ```notes -e id```
- Since the notes are stored as MarkDown text, it is nice to have some markdown support in your editor. In vi you can have nice colors and shortcuts.
- You can limit the amount of flows to show with the command _connections -F_ so large connections can be visualized better.
- You can list the notes for only the current capture, using filters.
- It assigns an auto note when putting a label.
- Show which connections have a label while listing models.
- You can filter by labelname in the models.
- You can filter by trainname, testname and distance in the detection_1 module.
- You can delete labels by range of ids.
- Only compare models when the upper most protocol matche. TCP with TCP, UDP with UDP, ICMP with ICMP.
- The experiments can be deleted by range of values.

## Modules
Now stf can import external modules that implement new functionality.
- There is a module for creating markov models of the network connections.
- There is a module to detect a testing model with a training model.
- There is a module for visualizing the model of letters.

### Bugs
- For bug reports please fill an issue on the [github page](https://github.com/stratosphereips/StratosphereTestingFramework/issues)

### TODO
- The filter of flowamount in connections does not seem to work properly when using >=
- When we leave the DB, there is an error when storing the relationship between the letters in the model and in the connections. Specifically, when using -F to see the flows in a connection, the letter is NOT shown. If we recreate the models, the letters are shown, but if we exit and enter again, they are not. This only happens in some datasets (like dataset 71)
- When creating connections, use filters to create a subset of the connections (so we don't have to delete them later)
- When we trim flows from the connections, store the original amount of flows on each connection.
- When creating a new dataset, copy the README.md file as main note for the dataset
- Change the name of a dataset
- How to change the Ground Truth label when the same machine is normal and infected???? Some tuples are infected and some are normal...
- The experiment can only be run from the machine that has the netflow file. Unless we transfer the netflow file...?
- Delete all the labels from one group-id
- Solve how to train the models globally and also for a given experiment.
- Add labels to packets
- Add labels to the binetflow files and biargus files automatically.
- When adding a binetflow and leaving, the file is not stored. (yes when creating it)
- Add "less" printing to the listing of -p of detections
- The proxy connections (like htbot) maybe be detected by the ratio of in/out bytes of argus
- argus is not detected when installed as root. Make the link
- When deleting a dataset, not all the group of models are deleted
- Put a limit when searching markov_models: amount of flows, or amount of time or maybe a specific string of letters that should be looked up.
- When deleting a label, delete its note too.
- Add notes to distances
- Fix argus timeout
- Concurrency in db?
- Copy between dbs?
- When the stf is used from several locations, it can happend that some dataset commands do not work because the pcap file is not there. Capture these issues.
- Relate the notes with the objects they reference. So after a search you can find the object again.

### CHANGELOG
- [2016/01/19]. Important change to how the letters are assigned in the models. After these date it is recommended to re-do the models. Version released 0.1.6alpha

[stf]:https://stratosphereips.org/development-of-the-stratosphere-testing-framework.html "The Stratosphere Testing Framework"
