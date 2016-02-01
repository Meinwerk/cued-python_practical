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
typename = ""
requestableslots = ["name"]
system_requestable = []
dbase_file = ""
ont_file = ""

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
