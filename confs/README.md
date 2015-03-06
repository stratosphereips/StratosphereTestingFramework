# Configuration files

## Main STF configuration
The main stf configuration is stf.conf. This file contains the paths to the other configuration files needed for the databases and programs.

## Argus configuration files
The configuration files for argus and ra are the following. They will be used by the execution of argus and ra in the stf program. These configuration are special to get bidirectional flows and to store some payload data inside the flow.
- argus.conf
- ra.conf

## ZEO database server
The ZEO server is a program that listens in an ip:port and serves the object-oriented database. It is very helpful to run this program remotely. Its configuration is **zeo.conf**. The example configuration file is *example_zeo.conf*.

## ZODB configuration
Since ZODB can be used with a server or directly with a file on disk, this configuration instructs zodb on how to access it. The conf file is **zodb.conf**. There are two main types that we may use. The file type of database, with an example configuration in *example_zodb_file_database.conf*, and the server type of dataset, with an example configuration in *example_zodb_server_database.conf*.
