#================================================================================#
#======================= Useful Functions & Module Import =======================#
#================================================================================#

import paramiko

def findPath(streams, client_SLAs):
    '''
        Return the destination's SLA for every stream in `streams` 
    '''

    path =[]
    for stream in streams :
        for sla in client_SLAs:
            if stream.addrDest in sla.clientNetwork :
                path.append(sla) 

    return path

def getBookingConfig(CE,streams, tspec):
    '''
        Return the list of commands to send to the router to protect all stream based on the tspec requested
    '''
    config_commands =[]
    # Create a new queue
    config_commands.append(f'tc class add dev {CE.interface} parent 1:1 classid 1:{CE.next_queue_id} htb rate {tspec}kbit ceil {tspec * 1.5}kbit')
    # Association mark <-> queue
    config_commands.append(f'tc filter add dev {CE.interface} parent 1:0 protocol ip prio 1 handle 11 fw flowid 1:{CE.next_queue_id}')
    # Association stream <-> mark
    for stream in streams :
        # Set the MARK based on destination address
        config_commands.append(f'iptables -A PREROUTING -t mangle -d {stream.addrDest} -j MARK --set-mark 11')
        # Set TOS on post Routing
        config_commands.append(f'iptables -A POSTROUTING -t mangle -d {stream.addrDest} -j DSCP --set-DSCP EF')

    return config_commands

def getUnBookingConfig(streams):
    '''
        Return the list of commands to send to the router to cancel ressources reservation 
    '''
    config_commands =[]
    # TO DO !
    # We have to find the id of the queue corresponding to thoses streams
    return config_commands

def getInitConfig(CE,premium_br, BE_br,control_br):
    '''
        Return the list of commands to send to the router to unprotect all stream in streams  
    '''
    config_commands =[]
    config_commands.append(f'tc qdisc del dev {CE.interface} root')
    config_commands.append(f'tc qdisc add dev {CE.interface} root handle 1: htb default 20')
    config_commands.append(f'tc class add dev {CE.interface} parent 1: classid 1:1 htb rate {premium_br}kbit ceil {premium_br}kbit')
    config_commands.append(f'tc class add dev {CE.interface} parent 1: classid 1:2 htb rate {BE_br}kbit ceil{premium_br}kbit')
    config_commands.append(f'tc class add dev {CE.interface} parent 1:1 classid 1:10 htb rate {control_br}kbit ceil {premium_br}kbit')
    
    # Put packet with mark=11 if control queue
    config_commands.append(f'tc filter add dev {CE.interface} parent 1:0 protocol ip prio 1 handle 11 fw flowid 1:10')

    # Set mark = 11 for packet comming from  192.168.1.0/24 = Proxy SIP
    config_commands.append(f'iptables -A PREROUTING -t mangle -s 192.168.1.2/24 -j MARK --set-mark 11') #We must update TOP 

    # Set mark = 11 for packet adress to  192.168.1.0/24 = Proxy SIP ?
    config_commands.append(f'iptables -A PREROUTING -t mangle -d 192.168.1.2/24 -j MARK --set-mark 11') #We must update TOP 
    
    return config_commands


def sshConfig(CE,config_commands):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(hostname=CE.hostname, username=CE.username, password=CE.password)
        print('\033[92m' + f'Connected to {CE.id}' + '\033[0m')
    except:
        print('\x1b[6;30;41m' + '[!] Cannot connect to the SSH Server' + '\x1b[0m')
        exit()

    # execute the commands
    for command in config_commands:
        print('\033[1m' + command + '\033[0m')
        stdin, stdout, stderr = client.exec_command(command)
        print(stdout.read().decode())
        err = stderr.read().decode()
        if err:
            print('\x1b[6;30;41m' + err + '\x1b[0m')

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
    def __init__(self,id, ipAddress, username='root', password='7nains',premium_br='1000', BE_br='5000', interface='eth0',control_br='100'):
        self.id = id
        self.ipAddress = ipAddress
        self.username = username
        self.password = password
        self.premium_br = premium_br
        self.BE_br = BE_br
        self.interface = interface
        self.control_br = control_br
        self.next_queue_id = 20

        # Queue initialasation on the CE
        init_config_commands = getInitConfig(self, self.premium_br, self.BE_br,self.control_br)
        # sshConfig(self,init_config_commands)

        # Only for demo
        for command in init_config_commands :
            print(command)
        
        print ("="*50, 'Initialisation over', "="*50)

    def book(self, streams, tspec) :
        config_commands = getBookingConfig(self, streams,tspec)
        # sshConfig(self,config_commands)
        
        # Only for demo
        for command in config_commands :
            print(command)
        
        print('\x1b[6;30;42m' + 'Booking over!' + '\x1b[0m')
        self.next_queue_id +=1

    def unBook(self, streams) :
        config_commands = getUnBookingConfig(streams)
        # sshConfig(self,config_commands)

        # Only for demo
        for command in config_commands :
            print(command)
        
        print('\x1b[6;30;42m' + 'Unooking over!' + '\x1b[0m')
