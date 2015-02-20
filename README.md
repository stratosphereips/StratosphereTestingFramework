![Stratosphere Testing Framework](http://)

The Stratosphere Testing Framework is a research framework to analyze the behavior of network connections using machine learning models and algorithms. Is the main research part of the Stratosphere IPS. Its goal is to help improving the detection models and algorithms.


## How to run the server
runzeo -f database/stf.zodb -a 127.0.0.1:9002

## How to use the stf without a server
There is an example configuration in the _confs_ folder that has an example of a local storage without the server. Just make a backup of the example_zeo_server_database.conf file and move the example_zeo_file_database.conf to zeo.conf

### Not connecting to the zeo server.
It can happen that the program hangs while trying to connect to the zeo database server the first time. We should fix this, but for now you should first execute the program with the file storage database conf (example_zeo_file_database.conf copied to zeo.conf)

# TODO

- Make a nice instalation
    - put configs in /etc or in ~/.stf/
    - create the database folder
