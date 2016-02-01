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
id("1")
kind("swimmingpool")
addr("Pool Way, Whitehill Road, off Newmarket Road")
price("TODO")
postcode("CB5 8NT")
phone("01223902088")
pricerange("TODO")
location("52.208789,0.154883")
openhours("TODO")
type("attraction")
name("Abbey Pool and Astroturf Pitch")


"""
typename = "attraction"
requestableslots = ["name", "pricerange","kind","area", "phone","price", "addr","postcode","openhours"]
system_requestable = ["pricerange","kind","area"]
dbase_file = "CamAttrac-dbase.txt"
ont_file = "CamAttrac-rules.json"

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
