This application is an Internet simulation via python. Routers and physics transfer medias are simulated by process.
The rest of features are pretty close to real network protocols. However, I have to revise some protocol on link layer
so that I it can run on top of the simulated virtual systems.

This simulation run on top of python2.7 and using python structs lib serialize packets and frame

**Interface:**

`````
    - Simulate an NIC and hold an IPv4 address and MAC address
    - Threads send and receive IP packets
    - Threads request and response ARP
`````

**Host:**
`````
    - Attached an chat window to represent source and destination
    - Hold an interface to simulate NIC 
    - Running a RIP to learn routing table from the network
`````

**Router:**
`````
    - Hold an interface to simulate NIC 
    - Running a RIP to learn routing table from the network
    - fowaring IP packets
`````


**library install**
``
    pip install menu: install text menu
    
    pip install netaddr : to manipulation ip and mac address
``
**Routers Simulator:**

Process will be use simulate router instance since process is similar to threads but its also offers local and remote concurrency
which is more close to our routers work.
Each router has more than one threads to run listening to receive,sending and other daemon processes such as dynamic routing 
`````
    - Internet wire - process pipe and queue
    - Interface: type , name, Mac  and IP address
    - Routing table
`````