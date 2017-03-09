This application is a model of raw internet and it implemented in python.
It is included simulator of interfaces, hosts , routers and raw  protocols such as ARP,RIP,IP, and TCP. 
Routers and physics transfer medias are simulated by process.
The rest of features are pretty close to real network protocols. However, I have to revise some protocol on link layer
so that I it can run on top of the simulated virtual systems. The principle of network has been remained.
Please refer simulators of  models and processes from readme.pptx.

Note: Many details have been ignored due to time and effort, such as I have added fresh and expire on routing table but 
not on mac table. I have wrap TCP sockets but not for UDP since here my UDP is just for send RIP packets. 
All IP addresses are set as C class addresses. 

This simulation run on top of python2.7 and using python structs lib serialize packets and frame

**Run:**
1. library install
`````
    - pip install menu  # install text menu
    - pip install netaddr # to manipulation ip and mac address
`````
2. run and command
`````
python main.py

1. Create Router
2. Config Host IP   # input IPv4 after get in  the IP address are loaded from config file but can reconfig
3. config Router IP  
4. Show Routing Table  # view routing table and dynamic learning
5. Show MAC/ARP Table  # view MAC/ARP table and dynamic learning
6. Select Servers
7. Open Chat Window
>>> 1   # eg, choose 1 to creat routers and hosts

`````
**Process of the System**
`````
It will try to build a TCP connection with target server once we click the "connect to host.x" from a client simulator.
The socket simulators will wrap a TCP segments, IP packets and put it to interfaces then it will encapsulated as frame 
to send to next hop. In order to send the frame to next hop it will check shortest path on routing table and the 
learning Mac address before send it.

Simulated RIP and ARP will run as daemon thread constantly and update the routing table and the mac/arp tables.

`````


**Interface:**

`````
    - Simulate an NIC and hold an IPv4 address and MAC address
    - Hold a send queue to serve send packets or frame
    - Threads send and receive IP packets
    - Threads request and response ARP
`````

**Host:**
`````
    - Attached an chat window to represent source and destination
    - Hold an interface to simulate NIC 
    - Running a RIP to learn routing table from the network
    - Can send and receive messages(packets) 
`````

**Router:**
`````
    - Hold an interface to simulate NIC 
    - Running a RIP to learn routing table from the network
    - Fowaring IP packets
    - Connected with a host to represent source and destination 
`````

**IP header:**

`````
0                   1                   2                   3
    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |Version|  IHL  |Type of Service|          Total Length         |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |         Identification        |Flags|      Fragment Offset    |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |  Time to Live |    Protocol   |         Header Checksum       |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                       Source Address                          |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                    Destination Address                        |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                    Options                    |    Padding    |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
`````

**TCP header:**

`````
0                   1                   2                   3   
    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |          Source Port          |       Destination Port        |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                        Sequence Number                        |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                    Acknowledgment Number                      |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |  Data |           |U|A|P|R|S|F|                               |
   | Offset| Reserved  |R|C|S|S|Y|I|            Window             |
   |       |           |G|K|H|T|N|N|                               |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |           Checksum            |         Urgent Pointer        |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                    Options                    |    Padding    |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                             data                              |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
`````

