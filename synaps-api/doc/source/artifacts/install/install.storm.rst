.. _install.storm:

Install Storm Example
=====================

This document describes basic installation guide example. For more details, see 
http://storm-project.net/

Pre-installation Requirements
-----------------------------

You can install following packages using apt tool.

.. code-block:: bash

   apt-get install openjdk-6-jdk zookeeper make build-essential
   apt-get install uuid-dev unzip pkg-config libtool automake
   
   # only for nimbus node
   apt-get install apache2 

Storm requires ZeroMQ 2.1.7 and JZMQ. 

.. code-block:: bash

   # install zeromq 
   cd ~
   wget http://download.zeromq.org/zeromq-2.1.7.tar.gz
   tar zxvf zeromq-2.1.7.tar.gz
   cd zeromq-2.1.7
   ./configure
   make
   make install
   sudo ldconfig
   
   wget http://pypi.python.org/packages/source/p/pyzmq/pyzmq-2.1.7.tar.gz#md5=aa4d7d81ad3c93dc1efd195153cb71ae
   tar xvfz pyzmq-2.1.7.tar.gz
   cd pyzmq-2.1.7
   python setup.py install
   cd ..
   
   # install JZMQ
   wget https://github.com/nathanmarz/jzmq/tarball/master
   mv master nathanmarz-jzmq-dd3327d.tar.gz
   tar zxvf nathanmarz-jzmq-dd3327d.tar.gz
   cd nathanmarz-jzmq-dd3327d
   
   # JZMQ for Ubuntu 11.04
   export JAVA_HOME='/usr/lib/jvm/java-6-openjdk'
   ./autogen.sh
   ./configure
   make
   sudo make install
   
   # JZMQ for Ubuntu 12.04
   export JAVA_HOME='/usr/lib/jvm/java-6-openjdk-amd64'
   ./autogen.sh
   ./configure
   touch src/classdist_noinst.stamp
   cd src/
   CLASSPATH=.:./.:$CLASSPATH javac -d . org/zeromq/ZMQ.java org/zeromq/App.java org/zeromq/ZMQForwarder.java org/zeromq/EmbeddedLibraryTools.java org/zeromq/ZMQQueue.java org/zeromq/ZMQStreamer.java org/zeromq/ZMQException.java
   cd ..
   make
   sudo make install


Install Storm
-------------

Install Storm as below.

.. code-block:: bash

   # install storm
   wget https://github.com/downloads/nathanmarz/storm/storm-0.8.0.zip
   mv storm-0.8.0.zip /SW
   cd /SW
   unzip storm-0.8.0
   ln -s /SW/storm-0.8.0 storm
   mkdir ~/.storm
   chmod 777 ~/.storm
   ln -s /SW/storm/bin/storm /bin/storm
   
   # set up log directory
   mkdir /var/log/storm
   rm -rf /SW/storm/logs/
   ln -s /var/log/storm /SW/storm/logs    

Configuration
-------------

First, you need to set up zookeeper cluster. The default config file is 
"/etc/zookeeper/conf/zoo.cfg". Replace HostName to real hostname.
  
.. code-block:: bash

   server.1=(HostName):2888:3888
   server.2=(HostName):2889:3889
   server.3=(HostName):2890:3890
   
   ...

And, edit zookeeper ID file, "/etc/zookeeper/conf/myid" as you set up in the 
zoo.cfg file.
  
.. code-block:: bash

   1

To config Storm, edit configuration file as below. The location of Storm 
configuration file is "/SW/storm/conf/storm.yaml". You need to replace
Storm_Nimbus_HostName, Storm_Supervisor_HostName to real hostnames. If you want 
to set up more slots for storm worker, you should assign more ports.

.. code-block:: bash

   storm.zookeeper.servers:
        - "(Storm_Nimbus_HostName)" 
        - "(Storm_Supervisor_HostName)" 
        - "(Storm_Supervisor_HostName)" 

   nimbus.host: "(Storm_Nimbus_HostName)" 

   java.library.path: "/usr/lib/jvm/java-6-openjdk-amd64:/usr/local/lib:/opt/local/lib:/usr/lib"
   
   supervisor.slots.ports:
     - 6700
     - 6701
     - 6702
     - 6703
     - 6704
     - 6705
     - 6706
     - 6707
     - 6708
     - 6709
     - 6710
     - 6711
     - 6712
     - 6713
     - 6714
     - 6715
     - 6716
     - 6717
     - 6718
     - 6719
   
   supervisor.childopts: "-Xmx1024m -Djava.net.preferIPv4Stack=true"

then copy the file to ~/.storm directory also.

.. code-block:: bash

   cp /SW/storm/conf/storm.yaml ~/.storm/
   mkdir /var/lib/dhcp3/
  
.. NOTE::
  
   Every hosts should be defined in /etc/hosts file. And for localhost, its 
   hostname should be appeared before localhost as below.
  
   .. code-block:: bash
   
      127.0.0.1		mn3 localhost
