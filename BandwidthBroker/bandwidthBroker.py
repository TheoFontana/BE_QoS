from ipaddress import IPv4Network
from netmiko import ConnectHandler

def findPath(stream_1,stream_2):
    '''Return stream 1 & stream 2 destination's SLA'''
    path =[]
    for SLA in client_SLAs :
        if stream_1.addrDest in SLA.clientNetwok :
            path.append(SLA) 
        if stream_2.addrDest in SLA.clientNetwok :
            path.append(SLA) 
    return path

def getBookingConfig(stream_1,stream_2,tspec):
    config_commands =[]
    # TO DO !
    return config_commands

def getUnBookingConfig(stream_1,stream_2,tspec):
    config_commands =[]
    # TO DO !
    return config_commands


#---------------------------------------------------------------------------
#------------------------------ RESA ---------------------------------------
#---------------------------------------------------------------------------

class Resa :
    def __init__(self, id , steam1, stream2):
        self.id = id
        self.stream_1 = steam1
        self.stream_2 = stream2
        self.status = 'Unactive'
        self.path = findPath(self.stream_1,self.stream_2)
        self.capacity = 0

    def askResa(self, tspec):
        '''Check if all SLAs in path have the capacity, and if possible, book the require capacity'''
        resaOK = True

        # Check if all SLA in path have the capacity
        for SLA in self.path :
            if not SLA.checkCapacity(tspec) :
                resaOK = False 
                break
        # Book require capacity on evry SLA in path
        if resaOK :
            for SLA in self.path :
                SLA.book(self.stream_1,self.stream_2, tspec)
        self.status = 'Active'
        self.capacity += tspec
        return resaOK
    
    def cancelResa(self):
        '''Ask all SLAs in path to unbook the resources allocated to this reservation'''
        for SLA in self.path :
            SLA.unBook(self.stream_1,self.stream_2, self.capacity)
            self.capacity = 0
        self.status = 'Unactive'

#---------------------------------------------------------------------------
#----------------------------- Stream --------------------------------------
#---------------------------------------------------------------------------

class Steam :
    def __init__(self,portDest, addrDest, portSrc, addrSrc,protocol='UDP',codec='Default', params=None):
        self.portDest = portDest
        self.addrDest = addrDest
        self.portSrc = portSrc
        self.addrSrc = addrSrc
        self.protocol = protocol
        self.codec = codec
        self.params = params


#---------------------------------------------------------------------------
#------------------------------ SLA ----------------------------------------
#---------------------------------------------------------------------------

class SLA :
    def __init__(self,id, CE, clientNetwork, capacity): 
        self.id = id
        self.CE = CE
        self.clientNetwork = clientNetwork
        self.capacity = capacity
        self.usage = 0

    def checkCapacity(self ,tspec) :
        result = False
        if self.capacity > (self.usage + tspec):
            result = True
        return result

    def book(self, stream_1, stream_2, tspec):
        self.usage += tspec
        self.CE.book(stream_1,stream_2, tspec)

    def unBook(self, stream_1, stream_2, tspec):
        self.usage -= tspec
        self.CE.unBook(stream_1,stream_2, tspec)


#---------------------------------------------------------------------------
#------------------------------- CE ----------------------------------------
#---------------------------------------------------------------------------

class CE :
    def __init__(self,id, device):
        self.id = id
        self.device = device

    def book(self, stream_1,stream_2,tspec) :
        ssh = ConnectHandler(**self.device)
        config_commands = getBookingConfig(stream_1,stream_2,tspec)
        ssh.send_config_set(config_commands)

    def unBook(self, stream_1,stream_2,tspec) :
        ssh = ConnectHandler(**self.device)
        config_commands = getUnBookingConfig(stream_1,stream_2,tspec)
        ssh.send_config_set(config_commands)
        

#---------------------------------------------------------------------------
#------------------------------ Main ---------------------------------------
#---------------------------------------------------------------------------

# Create CEs
CE1= CE (
    id='CE1',
    device ={
        'device_type': 'cisco_ios',
        'host':   '193.168.1.11',
        'username': 'test',
        'password': 'password',
        'port' : 8022,
        'secret': 'secret',
    }
)
CE2= CE (
    id='CE2',
    device ={
        'device_type': 'cisco_ios',
        'host':   '193.168.2.22',
        'username': 'test',
        'password': 'password',
        'port' : 8022,
        'secret': 'secret',
    }
)
CE3= CE (
    id='CE3',
    device ={
        'device_type': 'cisco_ios',
        'host':   '193.168.3.33',
        'username': 'test',
        'password': 'password',
        'port' : 8022,
        'secret': 'secret',
    }
)

# Create SLAs 
SLA1 = SLA(id='SLA1', clientNetwork=IPv4Network('192.168.1.0/24'), CE=CE1, capacity=1000)
SLA2 = SLA(id='SLA2', clientNetwork=IPv4Network('192.168.2.0/24'), CE=CE2, capacity=1000)
SLA3 = SLA(id='SLA3', clientNetwork=IPv4Network('192.168.3.0/24'), CE=CE3, capacity=1000)

client_SLAs=[SLA1,SLA2,SLA3]