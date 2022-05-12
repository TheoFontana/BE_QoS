#================================================================================#
#======================= Useful Functions & Module Import =======================#
#================================================================================#

from flask import Flask, request, render_template
from ipaddress import IPv4Network, ip_address
from bandwidthbroker import Stream, Resa, CE, SLA

def getStreamsfromJson(streams):
    result = []
    for stream in  streams :
        protocol = None
        if 'protocol' in stream :
            protocol = stream['protocol']     
        codec = None
        if 'codec' in stream :
            codec = stream['codec']
        params = None
        if 'protocol' in stream :
            params = stream['params']
            
        new_stream = Stream(
            portDest=stream['portDest'],
            addrDest=ip_address(stream['addrDest']),
            addrSrc=ip_address(stream['addrSrc']),
            portSrc=stream['portSrc'],
            protocol=protocol,
            codec=codec,
            params=params
        )
        result.append(new_stream)
    return result   

def find_matching_resa(streams,Active_Reservations):
    for resa in Active_Reservations:
        if resa.streams == streams :
            return resa
    return None

#================================================================================#
#============================= Create Variables =================================#
#================================================================================#

# Create CEs
CE1= CE('CE1', '192.168.1.2')
# CE2= CE ('CE2', '193.168.2.22')
# CE3= CE ('CE3', '193.168.3.33')

# Create SLAs 
SLA1 = SLA(id='SLA1', clientNetwork=IPv4Network('192.168.1.0/24'), CE=CE1, capacity=1000)
# SLA2 = SLA(id='SLA2', clientNetwork=IPv4Network('192.168.2.0/24'), CE=CE2, capacity=1000)
# SLA3 = SLA(id='SLA3', clientNetwork=IPv4Network('192.168.3.0/24'), CE=CE3, capacity=1000)

client_SLAs=[SLA1]
Active_Reservations=[]
Deleted_Reservations=[]
Failed_Reservations=[]

#================================================================================#
#============================= Create Flask App =================================#
#================================================================================#

app = Flask(__name__)

#================================= Dashboard ====================================#
@app.route('/')
def dashboard():
    global Active_Reservations
    global client_SLAs
    global Deleted_Reservations
    global Failed_Reservations

    return render_template(
        "index.html",
        client_SLAs=[SLA1],
        Active_Reservations=Active_Reservations,
        Deleted_Reservations=Deleted_Reservations,
        Failed_Reservations=Failed_Reservations,
    )

#========================= Reservation Handeler ===============================#

@app.route('/ask-resa', methods=['GET'])
def ask_resa():
    request_data = request.get_json()
    streams = None
    id = None
    tspec = None

    global Active_Reservations
    global client_SLAs

    if request_data:
        if 'id' in request_data:
            id = request_data['id']

        if 'streams' in request_data:
            streams = getStreamsfromJson(request_data['streams'])

        if 'tspec' in request_data:
            tspec = request_data['tspec']

        # Create a reservation
        new_resa=Resa(id=id, streams=streams, tspec=tspec,client_SLAs=client_SLAs)

        # Check if the reservation is possible
        resa_OK = new_resa.askResa()

        # Respond to the request accordingly
        if resa_OK:
            Active_Reservations.append(new_resa)
            return str(resa_OK)
        else :
            Failed_Reservations.append(new_resa)
            return 'Reservation failed', 400
        
    return 'Bad request', 400

@app.route('/remove-resa', methods=['GET'])
def remove():

    global Active_Reservations
    global client_SLAs
    request_data = request.get_json()
    streams = None
    if request_data:
        if 'streams' in request_data:
            streams = getStreamsfromJson(request_data['streams'])  
            matching_resa = find_matching_resa(streams,Active_Reservations)
        if matching_resa != None :
            matching_resa.cancelResa()
            Active_Reservations.remove(matching_resa)
            Deleted_Reservations.append(matching_resa)
            return f'{matching_resa.id} has been remove'
        else:
            return 'No reservation with matching streams', 400

    return 'Bad request', 400
 
if __name__ == '__main__':
    # run app in debug mode on port 5000
    app.run(host="0.0.0.0",debug=True, port=5000)
