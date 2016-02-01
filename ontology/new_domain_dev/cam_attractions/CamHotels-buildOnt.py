ont = {
    "type":"",
    "requestable": [
        ], 
    "discourseAct": [
        "ack", 
        "hello", 
        "none", 
        "repeat", 
        "silence", 
        "thankyou"
    ], 
    "method": [
        "none", 
        "byconstraints", 
        "byname", 
        "finished", 
        "byalternatives", 
        "restart"
    ],
    "system_requestable": [ 
    ],
    "informable": {} 
}

## Utils:
def get_slot_val(line):
    temp = line.split('"')
    slot = temp[0][0:-1]
    val = temp[1]
    return slot,val

## Define for single run:
"""
id("0")
addr("124 Tenison Road")
area("cherryhinton")
hasinternet("true")
hasparking("true")
hastv("true")
location("52.1963733,0.1987426")
name("A and B Guest House")
phone("01223315702")
postcode("CB1 2DP")
price("a cheapest single room is 50 pounds and a cheapest double room is 70 pounds and a cheapest family room is 90 pounds")
pricerange("moderate")
stars("4")
staytype("guesthouse")
type("placetostay")

"""
typename = "placetostay"
requestableslots = ["name", "pricerange","kind","area", "phone","price", "addr","postcode","stars","hasinternet"
    ,"hasparking","hastv"]
system_requestable = ["pricerange","kind","area","stars","hasparking"]
dbase_file = "CamHotels-dbase.txt"
ont_file = "_ugly_CamHotels-rules.json"

## Code:
ont["informable"] = dict.fromkeys(system_requestable+["name"])
for k in ont["informable"].keys():
    ont["informable"][k] = []

ont["system_requestable"] = system_requestable
ont["requestable"] = requestableslots
db = open(dbase_file,"r")
for line in db:
    if line != "\n":
        slot, val = get_slot_val(line)
        if slot in ont["informable"].keys():
            if val not in ont["informable"][slot]:
                ont["informable"][slot].append(val)
db.close()
import json
with open(ont_file,"w") as f:
    json.dump(ont,f)


#END OF FILE
