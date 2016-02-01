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
    #print line
    temp = line.split('"')
    #print temp
    #raw_input()
    slot = temp[0][0:-1]
    val = temp[1]
    #print slot, val
    #raw_input()
    return slot,val


## Define for single run:
"""
 addr("Parkside Cambridge")
  32 location("52.2032083333333,0.130491666666667")
   33 name("Cambridge Police Station")                                                                                           
    34 phone("01223358966")
     35 postcode("CB1 1JG")
      36 shopkind("policestation")
       37 type("shop)
"""
typename = ""
requestableslots = ["name", "area","phone","postcode","shopkind","addr"]
system_requestable = ["area","shopkind"]
dbase_file = "CamShop-dbase.txt"
ont_file = "CamShop-rules.json"

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
            #print slot, val
            #raw_input()
            if val not in ont["informable"][slot]:
                ont["informable"][slot].append(val)
                #print ont
                #raw_input("asda")
db.close()
import json
with open(ont_file,"w") as f:
    json.dump(ont,f)


#END OF FILE
