![Stratosphere Testing Framework](http://)

The Stratosphere Testing Framework is a research framework to analyze the behavior of network connections using machine learning models and algorithms. Is the main research part of the Stratosphere IPS. Its goal is to help improving the detection models and algorithms.


# Installation and Dependencies
Before installing stf, you need to install the dependencies:

- prettytable (apt-get install python-prettytable)
- transaction (apt-get install python-transaction)
- zodb (apt-get install python-zodb)
- 

Then you are ready to use stf.py.

# How to use the stf program
The most common usage of the program is to just execute it:

> stf.py

By default the program will search for the configuration file in confs/stf.conf. From that file it will read where are the configuration files for the ZODB and the ZEO server if it is being used. Upon the first run, stf will create the folder ~/.stf/, containing the .stfhistory file (the history of commands).
The database folder is also relative to the local folder and is by default ./database 

There are two ways of using the database. Since stf is designed to be a single host program and a multi-user program, it can run with a file-based database or with a server-based database. The file-based database is suited for single user and single host environments, whereas the server-based database is suited for multi-user and remote host environments.

# How to use the stf program with a file database
By default stf is using the zodb.conf file, which is prepared to use a file-based database. This means that the default zodb.conf file already includes the file server configuration. The location of the file database is by default ./database

# How to use the stf with a database server
If you want to separate the database from the clients, probably to allow several users to use stf, you need to:

1- Copy the example conf file *confs/example_zodb_server_database.conf* to the *confs/zodb.conf* file. 
2- Make sure that the *confs/zeo.conf* file is with the same content as the *confs/example_zeo.conf* file. 
3- Start the server with the command 
    > runzeo -C confs/zeo.conf
4- Use the stf.py normally.

# Uninstall
Unfortunately distutils does not have a way to uninstall packages. So your best option is

> sudo python setup.py install --record files.txt
> sudo bash -c "cat files.txt | xargs rm -rf"



# Tips on usage
- When looking at the list of models or list of connections, stf uses 'less -R' to show you the information paginated. Whoever if you want to store the output in a file for later analysis, you can run '! cat % > /tmp/file' from inside less and store the file to disk.




# TODO
- Show more info about the constructor
- Show table for each constructor?
- Implement the constructors as modules
- Try to cluster with simhash
- Add autotext note when I delete models or connections

# Bugs
- Do not detect when the 'distribution' program is not there.
