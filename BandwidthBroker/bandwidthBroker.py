from tkinter.messagebox import NO


def findPath (stream_1,stream_2):
    pass


class SLA :
    id = None
    CE = None
    PE = None
    capacity = None
    usage = None

    def __init__(self,id, CE, PE, capacity): 
        self.id = id
        self.CE = CE
        self.PE = PE
        self.capacity = capacity

    def checkCapacity(self ,tspec) :
        result = False
        if self.capacity < (self.usage + tspec):
            result = True
        return result

    def book(self, stream_1, stream_2, tspec):
        self.usage += tspec
        self.CE.book(stream_1,stream_2, tspec)

    def unBook(self, stream_1, stream_2, tspec):
        self.usage -= tspec
        self.CE.unBook(stream_1,stream_2, tspec)


class Resa :
    id = None
    stream_1 = None
    stream_2 = None
    status = None
    path = None

    def __init__(self, id , steam1, stream2):
        self.id = id
        self.stream_1 = steam1
        self.stream_2 = stream2
        self.status = 'Unactive'
        self.path = findPath(self.stream_1,self.stream_2)

    def askResa(self, tspec):
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
        return resaOK
    def cancelResa(self, tspec):
        # Unbook require capacity on evry SLA in path
        for SLA in self.path :
            SLA.unBook(self.stream_1,self.stream_2, tspec)
        self.status = 'Unactive'

class Steam :
    portDest = None
    addrDest = None
    portSrc = None
    addrSrc = None
    protocol = 'UDP'
    codec = 'Defaul'
    params = None

    def __init__(self,portDest, addrDest, portSrc, addrSrc,protocol='UDP',codec='Default', params=None):
        self.portDest = portDest
        self.addrDest = addrDest
        self.portSrc = portSrc
        self.addrSrc = addrSrc
        self.protocol = protocol
        self.codec = codec
        self.params = params