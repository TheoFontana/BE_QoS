---
theme: gaia
_class: lead
paginate: true
backgroundColor: #fff
emoji.shortcode: true
auto-scaling: false
emoji: {
    shortcode: true,
    unicode: true,
    }
marp: true

---

<!-- _footer: 'Lauric Marthrin-John  - Théo Fontana - Vatosoa Razafiniary - Dimitrios Nixarlidris - Tomás Ubaldi - 4IR SC ' -->

<style>
img[alt="insa"] { 
  position: absolute;
  top: 2em;
  width:  10em; 
  display: block;
}
</style>

![insa](https://international.insa-toulouse.fr/wp-content/uploads/2020/07/cropped-logo_insa_toulouse-5.png)

# Bureau d'étude <br>Qualité de service dans l'internet 

---

## Sumary

1. Introduction
2. Objectives
3. Realisation
4. Demonstation
5. Discussion
6. Conclusion

---
## Introduction


---
## Objective

We need to insure :
* Connectivity between hosts on all client's sites
* QoS for VoIP applications


---
## Realisation

* Core network using MPLS 
* VPN-IP tunnel for connection client's sites
* Bandwidth Broker is Python web app
* Proxy SIP exchange with the BB via http requests

---
## Core Network

![bg bottom:100% 90%](./slide_assets/plan_adressage.drawio.svg)

---
## Proxy SIP

![SIP_screenshot](/slide_assets/SIP_screenshot.png)
<style>
img[alt="SIP_screenshot"] { 
  width:  95%; 

}
</style>
---
## Proxy SIP

```Java
process ReponseStatelessly() 
    // [...]
    if (cseqHeader.getMethod().equals("INVITE")) {
        SIPREsponse sr = (SIPREsponse) response 
    }

```

---

## Bandwith Broker

Initialisation

```Python
# Create CEs
CE1= CE('CE1', '192.168.1.2')
CE2= CE ('CE2', '193.168.2.22')
CE3= CE ('CE3', '193.168.3.33')

# Create SLAs 
SLA1 = SLA(id='SLA1', clientNetwork=IPv4Network('192.168.1.0/24'), CE=CE1, capacity=1000)
SLA2 = SLA(id='SLA2', clientNetwork=IPv4Network('192.168.2.0/24'), CE=CE2, capacity=1000)
SLA3 = SLA(id='SLA3', clientNetwork=IPv4Network('192.168.3.0/24'), CE=CE3, capacity=1000)

client_SLAs=[SLA1,SLA2,SLA3]
Active_Reservations=[]
Deleted_Reservations=[]
Failed_Reservations=[]
```
---

## Bandwith Broker

Ask for a reservation

```Python
@app.route('/ask-resa', methods=['GET'])
def ask_resa():
    request_data = request.get_json()
    # [...]
    if request_data:
        # [...]
        new_resa=Resa(id=id, streams=streams, tspec=tspec,client_SLAs=client_SLAs) # Create a reservation   
        resa_OK = new_resa.askResa() # Check if the reservation is possible
        if resa_OK :  # Respond to the request accordingly
            Active_Reservations.append(new_resa)
            return str(resa_OK)
        else :
            Failed_Reservations.append(new_resa)
            return 'Reservation failed', 40
    return 'Bad request', 400
```

---

## Bandwidth Broker

CE configuration for a new reservation
``` bash
    # Create a new queue
    tc class add dev {CE.interface} parent 1:1 classid 1:{CE.next_queue_id} htb rate {tspec}kbit ceil {tspec * 1.1}kbit
    # Association mark <-> queue
    tc filter add dev {CE.interface} parent 1:0 protocol ip prio 1 handle 11 fw flowid 1:{CE.next_queue_id}
    # Association stream <-> mark
    for stream in streams :
        iptables -A PREROUTING -t mangle -s {stream.addrSrc} -j MARK --set-mark 11
```
---

## Bandwidth Broker

Cancel a reservaion

```Python
@app.route('/remove-resa', methods=['GET'])
def remove():
    request_data = request.get_json()
    # [...]
    if request_data:
        if 'streams' in request_data:
            streams = getStreamsfromJson(request_data['streams'])  
            matching_resa = find_matching_resa(streams,Active_Reservations) #                          
        if matching_resa != None :
            matching_resa.cancelResa()
            Active_Reservations.remove(matching_resa)
            Deleted_Reservations.append(matching_resa)
            return f'{matching_resa.id} has been remove'
        else:
            return 'No reservation with matching streams', 400

    return 'Bad request', 400
```

