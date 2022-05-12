#================================================================================#
#======================= Useful Functions & Module Import =======================#
#================================================================================#

import paramiko

def findPath(streams, client_SLAs):
    '''Return the destination's SLA for every stream in `streams` '''

    path =[]
    for stream in streams :
        for sla in client_SLAs:
            if stream.addrDest in sla.clientNetwork :
                path.append(sla) 

    return path

def getBookingConfig(streams, tspec,queue_id,interface):
    '''Return the list of commands to send to the router to protect all stream in streams acording to tspec'''
    config_commands =[]
    # Create a new queue
    config_commands.append(f'tc class add dev {interface} parent 1:1 classid 1:{queue_id} htb rate {tspec}kbit ceil {tspec * 1.1}kbit')
    # Put packet with TOS=11 if control queue
    config_commands.append(f'tc filter add dev {interface} parent 1:0 protocol ip prio 1 handle 11 fw flowid 1:10')
    # set mark = 11 for packet comming from  192.168.1.0/24 = Proxy SIP
    config_commands.append(f'iptables -A PREROUTING -t mangle -s 192.168.1.2/24 -j MARK --set-mark 11')
    return config_commands

def getUnBookingConfig(streams):
    '''Return the list of commands to send to the router to unprotect all stream in streams  '''
    config_commands =[]
    # TO DO !
    return config_commands

def getInitConfig(premium_Br, Be_Br,interface,control_br):
    '''
        Return the list of commands to send to the router to unprotect all stream in streams  
        By default config on eth0
    '''
    config_commands =[]
    config_commands.append(f'tc qdisc del dev {interface} root')
    config_commands.append(f'tc qdisc add dev {interface} root handle 1: htb default 20')
    config_commands.append(f'tc class add dev {interface} parent 1: classid 1:1 htb rate {premium_Br}kbit ceil {premium_Br}kbit')
    config_commands.append(f'tc class add dev {interface} parent 1: classid 1:2 htb rate {Be_Br}kbit ceil{Be_Br}kbit')
    config_commands.append(f'tc class add dev {interface} parent 1:1 classid 1:10 htb rate {control_br}kbit ceil {premium_Br}kbit')
    
    # Put packet with TOS=11 if control queue
    config_commands.append(f'tc filter add dev {interface} parent 1:0 protocol ip prio 1 handle 11 fw flowid 1:10')
    # set mark = 11 for packet comming from  192.168.1.0/24 = Proxy SIP
    config_commands.append(f'iptables -A PREROUTING -t mangle -s 192.168.1.2/24 -j MARK --set-mark 11') #We miust update TOP 
    
    return config_commands

#================================================================================#
#==================================== Resa ======================================#
#================================================================================#

class Resa :
    def __init__(self, id , streams, tspec, client_SLAs):
        self.id = id
        self.streams = streams
        self.status = 'Unactive'
        self.path = findPath(streams,client_SLAs)
        self.tspec = tspec

    def askResa(self,):
        '''Check if all SLAs in path have the capacity, and if possible, book the require capacity'''
        resaOK = True

        # Check if all SLA in path have the capacity
        for SLA in self.path :
            if not SLA.checkCapacity(self.tspec) :
                resaOK = False 
                break
    
        # Book require capacity on evry SLA in path
        if resaOK :
            for SLA in self.path :
                SLA.book(self.streams, self.tspec)
            self.status = 'Active'
            return resaOK

        return False
    
    def cancelResa(self):
        '''Ask all SLAs in path to unbook the resources allocated to this reservation'''
        for SLA in self.path :
            SLA.unBook(self.streams, self.tspec)
            self.tspec = 0
        self.status = 'Unactive'

#================================================================================#
#=================================== Stream =====================================#
#================================================================================#

class Stream :
    def __init__(self,portDest, addrDest, portSrc, addrSrc,protocol='UDP',codec='Default', params=None):
        self.portDest = portDest
        self.addrDest = addrDest
        self.portSrc = portSrc
        self.addrSrc = addrSrc
        if protocol == None :
            self.protocol = 'UDP'
        else :
            self.protocol = protocol
        self.codec = codec
        self.params = params

    def __eq__(self, other) : 
        return self.__dict__ == other.__dict__

#================================================================================#
#==================================== SLA =======================================#
#================================================================================#

class SLA :
    def __init__(self,id, CE, clientNetwork, capacity): 
        self.id = id
        self.CE = CE
        self.clientNetwork = clientNetwork
        self.capacity = capacity
        self.usage = 0

    def checkCapacity(self ,tspec) :
        '''Check if the SLA have the capacity to book `tspec`'''
        result = False
        if self.capacity > (self.usage + tspec):
            result = True
        return result

    def book(self,streams, tspec):
        '''Upadte SLA's usage and book require `tspec` on the CE '''
        self.usage += tspec
        self.CE.book(streams, tspec)

    def unBook(self, streams, tspec):
        '''Check if the SLA have the capacity to book `tspec`'''
        self.usage -= tspec
        self.CE.unBook(streams)
    
#================================================================================#
#==================================== CE ========================================#
#================================================================================#

class CE :
    def __init__(self,id, ipAddress, username='root', password='7nains',premium_Br='700', Be_Br='57900', interface='eth0',control_br='600'):
        self.id = id
        self.ipAddress = ipAddress
        self.username = username
        self.password = password
        self.premium_Br = premium_Br
        self.Be_Br = Be_Br
        self.interface = interface
        self.control_br = control_br
        self.next_queue_id = 20

        # Init comande for setting up queue 
        client = paramiko.SSHClient()

        init_config_commands = getInitConfig(self.premium_Br, self.Be_Br,self.interface,self.control_br)

        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(hostname=self.ipAddress, username=self.username, password=self.password)
        except:
            print("[!] Cannot connect to the SSH Server")
            exit()

        # execute the commands
        for command in init_config_commands:
            print("="*50, command, "="*50)
            stdin, stdout, stderr = client.exec_command(command)
            print(stdout.read().decode())
            err = stderr.read().decode()
            if err:
                print(err)
        print ("="*50, 'Initialisation over', "="*50)


    def book(self, streams, tspec) :
        config_commands = getBookingConfig(streams,tspec)
        
        # initialize the SSH client
        client = paramiko.SSHClient()
        # add to known hosts
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(hostname=self.hostname, username=self.username, password=self.password)
        except:
            print("[!] Cannot connect to the SSH Server")
            exit()

        # execute the commands
        for command in config_commands:
            print("="*50, command, "="*50)
            stdin, stdout, stderr = client.exec_command(command)
            print(stdout.read().decode())
            err = stderr.read().decode()
            if err:
                print(err)
        print ("="*50, 'booking over', "="*50)
        self.next_queue_id +=1

    def unBook(self, streams) :
        config_commands = getUnBookingConfig(streams)
        # We have to find the id of the queue corresponding to thoses streams
        return
        # initialize the SSH client
        client = paramiko.SSHClient()
        # add to known hosts
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(hostname=self.hostname, username=self.username, password=self.password)
        except:
            print("[!] Cannot connect to the SSH Server")
            exit()

        # execute the commands
        for command in config_commands:
            print("="*50, command, "="*50)
            stdin, stdout, stderr = client.exec_command(command)
            print(stdout.read().decode())
            err = stderr.read().decode()
            if err:
                print(err)
        print ("="*50, 'unbooking over', "="*50)