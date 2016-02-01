# FIX UP WHAT I INITIALLY CLEAVED OFF into the CamAttrac bucket.
# ---------------------
import copy,json

## Utils:
def get_slot_val(line):
    temp = line.split('"')
    slot = temp[0][0:-1]
    val = temp[1]
    return slot,val

def form_line(k,v):
    return k+'("'+v+'")\n'

def print_ent(ent):
    for k,v in ent.iteritems():
        print k, " = ", v

"""
mac@cam_attractions $ grep "type(" _orig_CamAttrac-dbase.txt | sort | uniq
entstype("boat")
entstype("cinema")
entstype("concerthall")
entstype("entertainment")
entstype("nightclub")
entstype("theatre")
seetype("architecture")
seetype("college")
seetype("museum")
seetype("park")
type("entsvenue")
type("placetosee")
type("sportsvenue")
type("univenue")
unitype("college")

"""
def unique_list(seq):
    seen = set()
    seen_add = seen.add
    return [ x for x in seq if not (x in seen or seen_add(x))]

def finalise_ent(ent, typelist):
    print_ent(ent)
    out = copy.copy(ent)
    out["type"] = "attraction"
    # and importantly form the kind, description slots
    print typelist
    slots, vals = [],[]
    #slots = [s for s,v in typelist]
    #vals = [v for s,v in typelist]
    for s,v in typelist:
        if s != "type":
            slots.append(s)
            vals.append(v)
    print slots
    print vals
    if len(slots) == 1:
        out["kind"] = vals[0]
    elif "swimmingpool" in vals:
        out["kind"] = "swimmingpool"
    elif len(unique_list(vals)) == 1:
        out["kind"] = vals[0]
    elif len(vals) == 2:
        if vals[0] == "entertainment":
            out["kind"] = vals[1]
        else:
            raw_input()
    elif len(vals) > 2:
        if vals[0] == "entertainment":
            out["kind"] = "mutliple sports"
        else:
            raw_input()
    else:
        raw_input()
    return out

#------------------
slots = ["id","name","price","pricerange","type","kind","addr","phone",
            "postcode","openhours", "location"]
template = dict.fromkeys(slots)
#default values
template["price"] = "TODO"
template["pricerange"] = "TODO"
template["openhours"] = "TODO"
# removed template["description"] = "TODO"
template["type"] = "attraction"
template["kind"] = "TEMP-TO-SEE"



discardlist = ["area", "childrenallowed", "hasinternet", "hasmusic", "hastv", "rating", "reviews"] #["location"]

dbfile = open("CamAttrac-dbase.txt","w")
origfile = open("_orig_CamAttrac-dbase.txt","r")
counter = 1
start=True
for line in origfile:
    if start:
        typelist = []
        ent = copy.deepcopy(template)
        ent["id"] = str(counter)
        counter += 1
        start = False
    if line == "\n":
        # write entity
        writeent = finalise_ent(ent,typelist)
        dbfile.write(form_line("id",ent["id"]))
        for k,v in writeent.iteritems():
            if k == "id":
                continue
            writeline = form_line(k,v)
            dbfile.write(writeline)
        dbfile.write("\n")
        # setup for next entity:
        ent = copy.copy(template)
        ent["id"] = str(counter)
        typelist = []
        counter +=1
    else:
        if "id(" in line:
            pass
        else:
            s,v = get_slot_val(line)
            #print s,v
            if "type" in s or "sport(" in line:
                typelist.append((s,v))
            elif s in ent.keys():
                ent[s] = v
            elif s in discardlist:
                pass
            else:
                print line
                exit("unknown")



dbfile.close()
origfile.close()

# END OF FILE
