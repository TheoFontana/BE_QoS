import requests

ask_resa_1= {
    "id":"Resa_1",
    "streams" : [
        {
            "portDest" : "1234",
            "addrDest" : "192.168.1.1",
            "portSrc" : "1234",
            "addrSrc" : "192.168.2.1"
        },
        {
            "portDest" : "1234",
            "addrDest" : "192.168.2.1",
            "portSrc" : "1234",
            "addrSrc" : "192.168.1.1"
        }
    ],
    "tspec": 100
}

ask_resa_2 = {
    "id":"Resa_2",
    "streams" : [
        {
            "portDest" : "1234",
            "addrDest" : "192.168.2.1",
            "portSrc" : "1234",
            "addrSrc" : "192.168.3.1"
        },
        {
            "portDest" : "1234",
            "addrDest" : "192.168.3.1",
            "portSrc" : "1234",
            "addrSrc" : "192.168.1.1"
        }
    ],
    "tspec": 200
}

ask_resa_3 = {
    "id":"Resa_3",
    "streams" : [
        {
            "portDest" : "1234",
            "addrDest" : "192.168.3.1",
            "portSrc" :"1234",
            "addrSrc" : "192.168.1.1"
        },
        {
            "portDest" : "1234",
            "addrDest" : "192.168.1.1",
            "portSrc" :"1234",
            "addrSrc" : "192.168.3.1"
        }
    ],
    "tspec": 300
}

ask_resa_fail = {
    "id":"Resa_4",
    "streams" : [
        {
            "portDest" : "1234",
            "addrDest" : "192.168.3.1",
            "portSrc" :"1234",
            "addrSrc" : "192.168.1.1"
        },
        {
            "portDest" : "1234",
            "addrDest" : "192.168.1.1",
            "portSrc" :"1234",
            "addrSrc" : "192.168.3.1"
        }
    ],
    "tspec": 1001
}

remove_resa_1 = {
    "streams" : [
        {
            "portDest" : "1234",
            "addrDest" : "192.168.1.1",
            "portSrc" :"1234",
            "addrSrc" : "192.168.2.1"
        },
        {
            "portDest" : "1234",
            "addrDest" : "192.168.2.1",
            "portSrc" :"1234",
            "addrSrc" : "192.168.1.1"
        }
    ]
}

remove_resa_3 = {
    "streams" : [
        {
            "portDest" : "1234",
            "addrDest" : "192.168.3.1",
            "portSrc" :"1234",
            "addrSrc" : "192.168.1.1"
        },
        {
            "portDest" : "1234",
            "addrDest" : "192.168.1.1",
            "portSrc" :"1234",
            "addrSrc" : "192.168.3.1"
        }
    ]
} 


# r = requests.get('http://127.0.0.1:5001/ask-resa',json = ask_resa_fail)
r= requests.get('http://127.0.0.1:5001/remove-resa',json = remove_resa_3)

print(r.text)
#print(f"Status Code: {r.status_code}, Response: {r.json()}")
